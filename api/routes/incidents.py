"""
Incident management API routes for RansomWatch.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from evidence.database import db
from evidence.models import Incident

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=List[dict])
def list_incidents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    severity: Optional[str] = Query(default=None),
):
    """Retrieve security incidents ordered from newest to oldest."""
    incidents = db.list_incidents(limit=limit, offset=offset, severity=severity)
    return [inc.to_dict() for inc in incidents]


@router.get("/{incident_id}")
def get_incident(incident_id: str):
    """Retrieve complete evidence and telemetry for a specific incident."""
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident.to_dict()


@router.delete("/{incident_id}")
def delete_incident(incident_id: str):
    """Remove an incident record."""
    session = db.get_session()
    try:
        incident = session.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        session.delete(incident)
        session.commit()
        return {"status": "success", "message": f"Incident {incident_id} deleted"}
    finally:
        session.close()


@router.post("/clear-all")
def clear_all_incidents():
    """Clear all recorded incidents for demo convenience."""
    session = db.get_session()
    try:
        count = session.query(Incident).delete()
        session.commit()
        return {"status": "success", "deleted_count": count}
    finally:
        session.close()
