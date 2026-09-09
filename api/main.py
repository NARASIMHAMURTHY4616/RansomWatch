"""
FastAPI Backend and Real-Time Detection Pipeline Orchestrator for RansomWatch.
"""

import os
import time
import threading
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from config.settings import settings
from monitor.file_monitor import FileMonitor
from monitor.process_monitor import ProcessMonitor
from features.feature_extractor import BehavioralFeatureExtractor
from detection.detector import BehavioralDetector
from risk_engine.risk_scorer import RiskScorer
from evidence.database import db
from rag.retriever import RAGRetriever
from ai.gemini_analyzer import GeminiAnalyzer
from attack_simulator.simulator import SafeAttackSimulator
from api.routes.incidents import router as incidents_router
from api.routes.analysis import router as analysis_router

logger = settings.setup_logging()

# Global pipeline instances
file_monitor = FileMonitor()
process_monitor = ProcessMonitor()
feature_extractor = BehavioralFeatureExtractor(window_seconds=settings.MONITOR_WINDOW_SECONDS)
detector = BehavioralDetector()
risk_scorer = RiskScorer()
rag_retriever = RAGRetriever()
gemini_analyzer = GeminiAnalyzer()

# Shared live state
_pipeline_running = False
_pipeline_thread: Optional[threading.Thread] = None
_latest_features: Dict[str, Any] = {
    "create_rate": 0.0,
    "modified_rate": 0.0,
    "rename_rate": 0.0,
    "delete_rate": 0.0,
    "operations_rate": 0.0,
    "directories_affected": 0,
    "activity_burst": 0.0,
}
_latest_risk: Dict[str, Any] = {
    "risk_score": 0,
    "severity": "LOW",
    "reasons": ["System idle. No active filesystem anomalies."],
}
_last_incident_time = 0.0
_cooldown_seconds = 4.0  # Cooldown between creating new incidents during the same ongoing burst


def _process_auto_analysis(incident_dict: Dict[str, Any]):
    """Background task to enrich an incident with RAG and Gemini AI analysis without blocking."""
    try:
        rag_chunks = rag_retriever.retrieve_for_incident(incident_dict, top_k=3)
        ai_res = gemini_analyzer.analyze_incident(incident_dict, rag_chunks=rag_chunks)
        db.update_incident_analysis(
            incident_id=incident_dict["id"],
            rag_context=rag_chunks,
            ai_analysis=ai_res,
            status="AI_ANALYZED" if ai_res.get("available") else "ANALYZED",
        )
    except Exception as e:
        logger.error(f"Error in automatic incident enrichment: {e}")


def detection_worker():
    """Background loop processing filesystem events, extracting features, and scoring risk."""
    global _pipeline_running, _latest_features, _latest_risk, _last_incident_time
    logger.info("Real-time detection pipeline loop started.")

    while _pipeline_running:
        try:
            # 1. Drain new events from file monitor
            events = file_monitor.get_events()
            if events:
                feature_extractor.add_events(events)

            # 2. Extract current window features
            features = feature_extractor.extract_features()
            _latest_features = features

            # 3. Perform ML inference
            ml_result = detector.detect(features)

            # 4. Compute risk score
            risk_result = risk_scorer.calculate_risk(ml_result, features)
            _latest_risk = risk_result

            # 5. Record periodic telemetry snapshot
            db.record_telemetry(features=features, risk_score=risk_result["risk_score"])

            # 6. Check if suspicious behavior warrants raising an incident
            is_ransomware_ml = (ml_result.get("prediction") == 1)
            is_high_risk = (risk_result["risk_score"] >= settings.RISK_THRESHOLD_MEDIUM)
            now = time.time()

            if (is_ransomware_ml or is_high_risk) and (now - _last_incident_time > _cooldown_seconds):
                _last_incident_time = now

                # Gather active process information
                proc_info = process_monitor.find_active_file_accessor()
                proc_name = proc_info.name if proc_info else "attack_simulator"
                proc_pid = proc_info.pid if proc_info else os.getpid()

                incident_id = f"INC-{int(now * 1000) % 10000000}"
                incident_data = {
                    "id": incident_id,
                    "timestamp": now,
                    "prediction": ml_result.get("prediction", 1),
                    "label": ml_result.get("label", "RANSOMWARE_LIKE"),
                    "confidence": ml_result.get("confidence", 0.0),
                    "ransomware_probability": ml_result.get("ransomware_probability", 0.0),
                    "risk_score": risk_result["risk_score"],
                    "severity": risk_result["severity"],
                    "reasons": risk_result["reasons"],
                    "process_name": proc_name,
                    "pid": proc_pid,
                    "affected_path": str(settings.TEST_DATA_DIR),
                    "features": features,
                    "status": "DETECTED",
                }

                # Save base evidence to SQLite
                db.create_incident(incident_data)
                logger.warning(
                    f"[ALERT] New Incident Created: {incident_id} | "
                    f"Score: {risk_result['risk_score']} | Severity: {risk_result['severity']}"
                )

                # Trigger async RAG + Gemini enrichment thread
                threading.Thread(
                    target=_process_auto_analysis,
                    args=(incident_data,),
                    daemon=True,
                ).start()

        except Exception as e:
            logger.error(f"Error in detection worker loop: {e}", exc_info=True)

        time.sleep(0.8)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown management."""
    global _pipeline_running, _pipeline_thread

    settings.ensure_directories()
    db.init_db()

    # Start filesystem watcher
    file_monitor.start()

    # Start detection background thread
    _pipeline_running = True
    _pipeline_thread = threading.Thread(target=detection_worker, daemon=True)
    _pipeline_thread.start()
    logger.info("RansomWatch backend initialized and active.")

    yield

    # Shutdown
    _pipeline_running = False
    file_monitor.stop()
    if _pipeline_thread:
        _pipeline_thread.join(timeout=2.0)
    logger.info("RansomWatch backend shut down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
)

# Enable CORS for dashboard and local clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(incidents_router)
app.include_router(analysis_router)


# Request schemas
class SimulatorRequest(BaseModel):
    mode: str = "benign"  # benign or ransomware
    duration: int = 8
    intensity: str = "high"


@app.get("/api/status")
def get_system_status():
    """Retrieve operational health of all monitoring and detection subcomponents."""
    return {
        "status": "ONLINE",
        "timestamp": time.time(),
        "monitoring": {
            "active": file_monitor.is_running(),
            "target_dir": str(settings.TEST_DATA_DIR),
            "events_recorded": file_monitor.total_events_recorded,
            "window_seconds": settings.MONITOR_WINDOW_SECONDS,
        },
        "ml_engine": {
            "loaded": detector.is_loaded(),
            "model_path": str(settings.MODEL_PATH),
            "feature_count": len(settings.FEATURE_NAMES),
        },
        "risk_engine": {
            "current_score": _latest_risk["risk_score"],
            "current_severity": _latest_risk["severity"],
        },
        "rag_retriever": {
            "ready": rag_retriever.is_ready(),
            "indexed_chunks": len(rag_retriever.chunks),
        },
        "ai_engine": {
            "configured": gemini_analyzer.is_configured(),
            "model": settings.GEMINI_MODEL,
        },
    }


@app.get("/api/stats")
def get_statistics():
    """Summary metrics for the SOC overview cards."""
    stats = db.get_stats()
    stats["current_risk_score"] = _latest_risk["risk_score"]
    stats["current_severity"] = _latest_risk["severity"]
    return stats


@app.get("/api/live-metrics")
def get_live_metrics():
    """Real-time rates and rolling telemetry for Chart.js."""
    history = db.get_recent_telemetry(limit=30)
    return {
        "current_features": _latest_features,
        "current_risk": _latest_risk,
        "history": [s.to_dict() for s in history],
    }


@app.post("/api/simulator/run")
def trigger_simulation(req: SimulatorRequest, background_tasks: BackgroundTasks):
    """Run benign or ransomware simulation inside test_data/ in a background task."""
    simulator = SafeAttackSimulator()

    def run_sim():
        if req.mode == "benign":
            simulator.run_benign(duration_seconds=req.duration)
        elif req.mode == "ransomware":
            simulator.run_ransomware(duration_seconds=req.duration, intensity=req.intensity)

    background_tasks.add_task(run_sim)
    return {
        "status": "started",
        "mode": req.mode,
        "duration": req.duration,
        "message": f"Simulation [{req.mode}] launched in background inside test_data/",
    }


@app.post("/api/simulator/cleanup")
def cleanup_sandbox():
    """Safely clear test_data/."""
    simulator = SafeAttackSimulator()
    simulator.cleanup()
    feature_extractor.clear()
    return {"status": "success", "message": "Sandbox test_data/ wiped clean."}


# Mount Dashboard static assets
if settings.DASHBOARD_DIR.exists():
    app.mount(
        "/dashboard",
        StaticFiles(directory=str(settings.DASHBOARD_DIR), html=True),
        name="dashboard",
    )


@app.get("/")
@app.head("/")
def root():
    """Redirect home to the SOC dashboard."""
    return RedirectResponse(url="/dashboard/index.html")
