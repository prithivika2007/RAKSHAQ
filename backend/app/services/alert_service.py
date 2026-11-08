"""Alert and incident management service for RAKSHAQ.

Handles incident creation, lifecycle (open -> acknowledged -> resolved),
independent employee and driver missed heartbeat detection, and safety escalations.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.trip import Trip


def create_incident(
    db: Session,
    trip_id: int,
    incident_type: str,
    severity: str = "MEDIUM",
    description: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Incident:
    """Create and persist a new safety incident.

    Transitions trip status to ALERT if it is currently ACTIVE.
    Does not modify trips that are already COMPLETED or CANCELLED.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise ValueError(f"Trip with ID {trip_id} does not exist.")

    incident = Incident(
        trip_id=trip_id,
        incident_type=incident_type,
        severity=severity,
        description=description,
        latitude=latitude,
        longitude=longitude,
        status="OPEN",
    )
    db.add(incident)

    # Transition to ALERT only if trip is in ACTIVE state
    if trip.status == "ACTIVE":
        trip.status = "ALERT"

    db.commit()
    db.refresh(incident)
    return incident


def check_missed_heartbeats(
    db: Session,
    threshold_minutes: int = 5,
    source: Literal["EMPLOYEE", "DRIVER"] = "EMPLOYEE",
) -> List[Incident]:
    """Inspect all active trips for lost heartbeats, monitoring streams independently.

    - source="EMPLOYEE": Checks last_employee_heartbeat_at -> flags MISSED_CHECKIN (HIGH).
    - source="DRIVER": Checks last_driver_heartbeat_at -> flags DRIVER_CONNECTIVITY_LOST (MEDIUM).

    Includes deduplication to prevent alert spamming during an ongoing outage.
    """
    now = datetime.now(timezone.utc)
    threshold = timedelta(minutes=threshold_minutes)

    active_trips = db.query(Trip).filter(Trip.status.in_(["ACTIVE", "ALERT"])).all()
    created_incidents: List[Incident] = []

    normalized_source = source.upper()

    for trip in active_trips:
        if normalized_source == "EMPLOYEE":
            last_seen = trip.last_employee_heartbeat_at or trip.started_at
            alert_type = "MISSED_CHECKIN"
            severity = "HIGH"
            label = "Employee device"
        elif normalized_source == "DRIVER":
            last_seen = trip.last_driver_heartbeat_at or trip.started_at
            alert_type = "DRIVER_CONNECTIVITY_LOST"
            severity = "MEDIUM"
            label = "Driver device"
        else:
            raise ValueError(f"Unknown heartbeat source: {source}. Must be 'EMPLOYEE' or 'DRIVER'.")

        if not last_seen:
            continue

        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        time_elapsed = now - last_seen
        if time_elapsed > threshold:
            # Check if an OPEN or ACKNOWLEDGED incident of this type already exists for this trip
            recent_alert = (
                db.query(Incident)
                .filter(
                    Incident.trip_id == trip.id,
                    Incident.incident_type == alert_type,
                    Incident.status.in_(["OPEN", "ACKNOWLEDGED"]),
                )
                .first()
            )

            if not recent_alert:
                elapsed_min = int(time_elapsed.total_seconds() // 60)
                inc = create_incident(
                    db=db,
                    trip_id=trip.id,
                    incident_type=alert_type,
                    severity=severity,
                    description=(
                        f"{label} heartbeat overdue by {elapsed_min} minutes "
                        f"(threshold: {threshold_minutes} min). Auto-escalation triggered."
                    ),
                )
                created_incidents.append(inc)

    return created_incidents


def acknowledge_incident(db: Session, incident_id: int) -> Incident:
    """Transition an incident status to ACKNOWLEDGED."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Incident with ID {incident_id} not found.")

    incident.status = "ACKNOWLEDGED"
    db.commit()
    db.refresh(incident)
    return incident


def resolve_incident(
    db: Session,
    incident_id: int,
    description_update: Optional[str] = None,
) -> Incident:
    """Resolve an incident.

    Restores trip status to ACTIVE only if:
    1. Trip status was ALERT.
    2. No other OPEN or ACKNOWLEDGED incidents remain for the trip.
    3. The trip has NOT ended and is not in COMPLETED or CANCELLED state.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Incident with ID {incident_id} not found.")

    incident.status = "RESOLVED"
    if description_update:
        incident.description = f"{incident.description} | Resolution: {description_update}"

    trip = db.query(Trip).filter(Trip.id == incident.trip_id).first()
    if trip and trip.status == "ALERT":
        open_count = (
            db.query(Incident)
            .filter(
                Incident.trip_id == trip.id,
                Incident.status.in_(["OPEN", "ACKNOWLEDGED"]),
                Incident.id != incident_id,
            )
            .count()
        )
        if open_count == 0:
            # Strictly protect lifecycle state: never revert COMPLETED or CANCELLED trips
            if trip.ended_at is None and trip.status not in ("COMPLETED", "CANCELLED"):
                trip.status = "ACTIVE"

    db.commit()
    db.refresh(incident)
    return incident


def get_open_incidents(db: Session, trip_id: Optional[int] = None) -> List[Incident]:
    """Retrieve all OPEN or ACKNOWLEDGED incidents, optionally filtered by trip."""
    query = db.query(Incident).filter(Incident.status.in_(["OPEN", "ACKNOWLEDGED"]))
    if trip_id is not None:
        query = query.filter(Incident.trip_id == trip_id)
    return query.order_by(Incident.created_at.desc()).all()
