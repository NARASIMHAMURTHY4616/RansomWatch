"""
SQLAlchemy ORM models for RansomWatch evidence storage and telemetry.
"""

import json
import time
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Incident(Base):
    """Stores security incidents detected by the ML and Risk engines."""

    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(Float, default=time.time, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ML Detection fields
    prediction = Column(Integer, nullable=False)  # 0 or 1
    label = Column(String(32), nullable=False)    # BENIGN or RANSOMWARE_LIKE
    confidence = Column(Float, nullable=False)
    ransomware_probability = Column(Float, nullable=False, default=0.0)

    # Risk Engine fields
    risk_score = Column(Integer, nullable=False)  # 0 to 100
    severity = Column(String(16), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    reasons_json = Column(Text, nullable=False, default="[]")

    # Process and Target fields
    process_name = Column(String(128), default="unknown")
    pid = Column(Integer, default=0)
    affected_path = Column(String(512), default="")

    # Behavioral Telemetry Features
    features_json = Column(Text, nullable=False, default="{}")

    # RAG Context & Gemini AI Analysis
    rag_context_json = Column(Text, nullable=True)
    ai_analysis_json = Column(Text, nullable=True)
    status = Column(String(32), default="DETECTED")  # DETECTED, ANALYZED, MITIGATED

    def get_features(self) -> dict:
        try:
            return json.loads(self.features_json) if self.features_json else {}
        except Exception:
            return {}

    def get_reasons(self) -> list:
        try:
            return json.loads(self.reasons_json) if self.reasons_json else []
        except Exception:
            return []

    def get_rag_context(self) -> list:
        try:
            return json.loads(self.rag_context_json) if self.rag_context_json else []
        except Exception:
            return []

    def get_ai_analysis(self) -> dict:
        try:
            return json.loads(self.ai_analysis_json) if self.ai_analysis_json else {}
        except Exception:
            return {}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "prediction": self.prediction,
            "label": self.label,
            "confidence": self.confidence,
            "ransomware_probability": self.ransomware_probability,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "reasons": self.get_reasons(),
            "process_name": self.process_name,
            "pid": self.pid,
            "affected_path": self.affected_path,
            "features": self.get_features(),
            "rag_context": self.get_rag_context(),
            "ai_analysis": self.get_ai_analysis(),
            "status": self.status,
        }


class TelemetrySnapshot(Base):
    """Stores rolling behavioral metrics for SOC dashboard visualization."""

    __tablename__ = "telemetry_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Float, default=time.time, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    create_rate = Column(Float, default=0.0)
    modified_rate = Column(Float, default=0.0)
    rename_rate = Column(Float, default=0.0)
    delete_rate = Column(Float, default=0.0)
    operations_rate = Column(Float, default=0.0)
    directories_affected = Column(Integer, default=0)
    activity_burst = Column(Float, default=0.0)
    current_risk_score = Column(Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "create_rate": self.create_rate,
            "modified_rate": self.modified_rate,
            "rename_rate": self.rename_rate,
            "delete_rate": self.delete_rate,
            "operations_rate": self.operations_rate,
            "directories_affected": self.directories_affected,
            "activity_burst": self.activity_burst,
            "current_risk_score": self.current_risk_score,
        }
