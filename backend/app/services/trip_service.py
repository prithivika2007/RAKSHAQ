"""Trip management service for RAKSHAQ.

Handles trip scheduling, state transitions (SCHEDULED -> ACTIVE -> COMPLETED),
telemetry ingestion, and doorstep arrival verification.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.trip_location import TripLocation
from app.schemas.trip import TripCreate


def create_trip(db: Session, trip_in: TripCreate) -> Trip:
    """Schedule a new commute trip."""
    trip = Trip(
        employee_id=trip_in.employee_id,
        driver_id=trip_in.driver_id,
        vehicle_id=trip_in.vehicle_id,
        pickup_location=trip_in.pickup_location,
        destination=trip_in.destination,
        planned_route=trip_in.planned_route,
        status="SCHEDULED",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def start_trip(db: Session, trip_id: int) -> Trip:
    """Transition a scheduled trip to ACTIVE state and initialize heartbeats."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise ValueError(f"Trip with ID {trip_id} not found.")

    now = datetime.now(timezone.utc)
    trip.status = "ACTIVE"
    trip.started_at = now
    trip.last_employee_heartbeat_at = now
    trip.last_driver_heartbeat_at = now

    db.commit()
    db.refresh(trip)
    return trip


def record_location(
    db: Session,
    trip_id: int,
    source: str,
    latitude: float,
    longitude: float,
    speed: float = 0.0,
) -> TripLocation:
    """Record telemetry ping and refresh the corresponding device heartbeat."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise ValueError(f"Trip with ID {trip_id} not found.")

    normalized_source = source.upper()
    if normalized_source not in ("EMPLOYEE", "DRIVER"):
        raise ValueError(f"Invalid source: {source}. Must be 'EMPLOYEE' or 'DRIVER'.")

    location = TripLocation(
        trip_id=trip_id,
        source=normalized_source,
        latitude=latitude,
        longitude=longitude,
        speed=speed,
    )
    db.add(location)

    now = datetime.now(timezone.utc)
    if normalized_source == "EMPLOYEE":
        trip.last_employee_heartbeat_at = now
    else:
        trip.last_driver_heartbeat_at = now

    db.commit()
    db.refresh(location)
    return location


def complete_trip(db: Session, trip_id: int) -> Trip:
    """Mark a trip as COMPLETED upon safe arrival at destination doorstep."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise ValueError(f"Trip with ID {trip_id} not found.")

    now = datetime.now(timezone.utc)
    trip.status = "COMPLETED"
    trip.ended_at = now

    db.commit()
    db.refresh(trip)
    return trip


def get_trip(db: Session, trip_id: int) -> Optional[Trip]:
    """Retrieve trip by ID."""
    return db.query(Trip).filter(Trip.id == trip_id).first()


def list_active_trips(db: Session) -> List[Trip]:
    """List all currently active or alerting trips."""
    return db.query(Trip).filter(Trip.status.in_(["ACTIVE", "ALERT"])).all()


def list_scheduled_trips(db: Session, employee_id: Optional[int] = None) -> List[Trip]:
    """List scheduled trips, optionally restricted to one employee."""
    query = db.query(Trip).filter(Trip.status == "SCHEDULED")
    if employee_id is not None:
        query = query.filter(Trip.employee_id == employee_id)
    return query.order_by(Trip.id.asc()).all()
