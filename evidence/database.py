"""
Database interface for RansomWatch using SQLite and SQLAlchemy.
Handles automatic schema creation and incident evidence operations.
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, scoped_session

from config.settings import settings
from evidence.models import Base, Incident, TelemetrySnapshot

logger = logging.getLogger("RansomWatch.Database")


class Database:
    """SQLite database management for incident records and metrics."""

    def __init__(self, db_path=None):
        self.db_path = db_path or settings.DB_PATH
        # SQLite connect_args to support multi-threaded access safely
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
            echo=False,
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        self.init_db()

    def init_db(self) -> None:
        """Create database tables if they do not exist."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info(f"Database initialized at: {self.db_path}")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")

    def get_session(self):
        """Get a thread-local scoped session."""
        return self.Session()

    def create_incident(self, data: Dict[str, Any]) -> Incident:
        """Persist a newly detected incident."""
        session = self.get_session()
        try:
            incident_id = data.get("id") or f"INC-{int(time.time()*1000)}"

            incident = Incident(
                id=incident_id,
                timestamp=data.get("timestamp", time.time()),
                prediction=data.get("prediction", 1),
                label=data.get("label", "RANSOMWARE_LIKE"),
                confidence=float(data.get("confidence", 0.0)),
                ransomware_probability=float(data.get("ransomware_probability", 0.0)),
                risk_score=int(data.get("risk_score", 0)),
                severity=data.get("severity", "LOW"),
                reasons_json=json.dumps(data.get("reasons", [])),
                process_name=data.get("process_name", "unknown"),
                pid=int(data.get("pid", 0)),
                affected_path=data.get("affected_path", str(settings.TEST_DATA_DIR)),
                features_json=json.dumps(data.get("features", {})),
                rag_context_json=json.dumps(data.get("rag_context", [])) if data.get("rag_context") else None,
                ai_analysis_json=json.dumps(data.get("ai_analysis", {})) if data.get("ai_analysis") else None,
                status=data.get("status", "DETECTED"),
            )
            session.add(incident)
            session.commit()
            session.refresh(incident)
            logger.info(f"Recorded incident {incident.id} [Severity: {incident.severity}, Score: {incident.risk_score}]")
            return incident
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create incident: {e}")
            raise
        finally:
            session.close()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Fetch an incident by its unique ID."""
        session = self.get_session()
        try:
            return session.query(Incident).filter(Incident.id == incident_id).first()
        finally:
            session.close()

    def list_incidents(
        self,
        limit: int = 50,
        offset: int = 0,
        severity: Optional[str] = None,
    ) -> List[Incident]:
        """List incidents with optional filtering and pagination."""
        session = self.get_session()
        try:
            query = session.query(Incident)
            if severity:
                query = query.filter(Incident.severity == severity.upper())
            incidents = query.order_by(desc(Incident.timestamp)).offset(offset).limit(limit).all()
            return incidents
        finally:
            session.close()

    def update_incident_analysis(
        self,
        incident_id: str,
        rag_context: Optional[List[Dict]] = None,
        ai_analysis: Optional[Dict] = None,
        status: str = "ANALYZED",
    ) -> bool:
        """Update an incident with retrieved RAG context and Gemini AI analysis."""
        session = self.get_session()
        try:
            incident = session.query(Incident).filter(Incident.id == incident_id).first()
            if not incident:
                return False

            if rag_context is not None:
                incident.rag_context_json = json.dumps(rag_context)
            if ai_analysis is not None:
                incident.ai_analysis_json = json.dumps(ai_analysis)
            incident.status = status

            session.commit()
            logger.info(f"Updated AI analysis for incident {incident_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating incident analysis: {e}")
            return False
        finally:
            session.close()

    def record_telemetry(self, features: Dict[str, Any], risk_score: int) -> TelemetrySnapshot:
        """Record periodic rolling metrics for dashboard charts."""
        session = self.get_session()
        try:
            snapshot = TelemetrySnapshot(
                timestamp=time.time(),
                create_rate=features.get("create_rate", 0.0),
                modified_rate=features.get("modified_rate", 0.0),
                rename_rate=features.get("rename_rate", 0.0),
                delete_rate=features.get("delete_rate", 0.0),
                operations_rate=features.get("operations_rate", 0.0),
                directories_affected=int(features.get("directories_affected", 0)),
                activity_burst=features.get("activity_burst", 0.0),
                current_risk_score=risk_score,
            )
            session.add(snapshot)
            session.commit()
            return snapshot
        except Exception as e:
            session.rollback()
            logger.debug(f"Telemetry record error: {e}")
            return None
        finally:
            session.close()

    def get_recent_telemetry(self, limit: int = 30) -> List[TelemetrySnapshot]:
        """Fetch the latest telemetry snapshots in chronological order."""
        session = self.get_session()
        try:
            items = (
                session.query(TelemetrySnapshot)
                .order_by(desc(TelemetrySnapshot.timestamp))
                .limit(limit)
                .all()
            )
            items.reverse()
            return items
        finally:
            session.close()

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate statistical summary for SOC dashboard cards."""
        session = self.get_session()
        try:
            total_incidents = session.query(func.count(Incident.id)).scalar() or 0
            critical = session.query(func.count(Incident.id)).filter(Incident.severity == "CRITICAL").scalar() or 0
            high = session.query(func.count(Incident.id)).filter(Incident.severity == "HIGH").scalar() or 0
            medium = session.query(func.count(Incident.id)).filter(Incident.severity == "MEDIUM").scalar() or 0
            low = session.query(func.count(Incident.id)).filter(Incident.severity == "LOW").scalar() or 0

            latest_incident = session.query(Incident).order_by(desc(Incident.timestamp)).first()
            latest_telemetry = session.query(TelemetrySnapshot).order_by(desc(TelemetrySnapshot.timestamp)).first()

            return {
                "total_incidents": total_incidents,
                "critical_incidents": critical,
                "high_incidents": high,
                "medium_incidents": medium,
                "low_incidents": low,
                "latest_risk_score": latest_telemetry.current_risk_score if latest_telemetry else 0,
                "latest_ops_rate": latest_telemetry.operations_rate if latest_telemetry else 0.0,
                "latest_incident_time": latest_incident.timestamp if latest_incident else None,
                "latest_incident_severity": latest_incident.severity if latest_incident else None,
            }
        finally:
            session.close()


db = Database()
