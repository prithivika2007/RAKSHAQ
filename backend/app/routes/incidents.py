"""Incident / alert management routes.

Supports dashboard listing with flexible status filtering and
lifecycle transitions (acknowledge, resolve, false_alarm).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate
from app.services.alert_service import acknowledge_incident, create_incident, resolve_incident
from app.services.trip_service import get_trip

router = APIRouter(prefix="/incidents", tags=["Incidents"])

# Valid status values accepted from query params
_VALID_STATUSES = {"OPEN", "ACKNOWLEDGED", "RESOLVED", "FALSE_ALARM"}


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED, summary="Create SOS incident")
def post_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Persist an employee SOS against a currently monitored trip."""
    trip = get_trip(db, payload.trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {payload.trip_id} not found.",
        )
    if trip.status not in ("ACTIVE", "ALERT"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Trip {payload.trip_id} is not active (status: '{trip.status}').",
        )
    return create_incident(
        db,
        trip_id=payload.trip_id,
        incident_type=payload.incident_type,
        severity=payload.severity,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )


@router.get("", response_model=List[IncidentResponse], summary="List incidents")
def list_incidents(
    trip_id: Optional[int] = Query(default=None),
    incident_status: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    """Return incidents with optional filters.

    - `trip_id`: restrict to a specific trip.
    - `status`: one of OPEN | ACKNOWLEDGED | RESOLVED | FALSE_ALARM.
      Defaults to OPEN and ACKNOWLEDGED when omitted (dashboard view).
    """
    if incident_status is not None and incident_status.upper() not in _VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{incident_status}'. Must be one of: {sorted(_VALID_STATUSES)}.",
        )

    query = db.query(Incident)

    if trip_id is not None:
        query = query.filter(Incident.trip_id == trip_id)

    if incident_status is not None:
        query = query.filter(Incident.status == incident_status.upper())

    return query.order_by(Incident.created_at.desc()).all()


@router.patch("/{incident_id}", response_model=IncidentResponse, summary="Update incident")
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
):
    """Update incident status or severity.

    Status transitions:
    - ACKNOWLEDGED → calls alert_service.acknowledge_incident (no trip side-effect)
    - RESOLVED     → calls alert_service.resolve_incident (may restore trip to ACTIVE)
    - FALSE_ALARM  → direct status update (no trip status change)

    Severity and description can be updated independently of status.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found.",
        )

    # ── Status lifecycle transitions ──────────────────────────────────────────
    if payload.status == "ACKNOWLEDGED":
        incident = acknowledge_incident(db, incident_id)

    elif payload.status == "RESOLVED":
        # Pass description as a resolution note (appended to existing description)
        incident = resolve_incident(db, incident_id, description_update=payload.description)

    elif payload.status == "FALSE_ALARM":
        incident.status = "FALSE_ALARM"
        db.commit()
        db.refresh(incident)

    # ── Field-level updates (applied independently of status) ─────────────────
    field_changed = False

    if payload.severity is not None and incident.severity != payload.severity:
        incident.severity = payload.severity
        field_changed = True

    # Update description only when status is not RESOLVED
    # (resolve_incident already handles the description_update)
    if payload.description is not None and payload.status != "RESOLVED":
        incident.description = payload.description
        field_changed = True

    if field_changed:
        db.commit()
        db.refresh(incident)

    return incident