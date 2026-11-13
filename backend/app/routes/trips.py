"""Trip lifecycle and telemetry routes.

Covers both dashboard (read) and mobile/simulator (write) endpoints.
Route order is intentional: static paths (/active) must precede dynamic
path parameters (/{trip_id}) to avoid integer-parse failures.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.adapter import evaluate_trip_safety
from app.models.driver import Driver
from app.models.employee import Employee
from app.models.trip import Trip
from app.models.trip_location import TripLocation
from app.models.vehicle import Vehicle
from app.schemas.checkin import CheckInRequest, CheckInResponse, HeartbeatPing
from app.schemas.ml import MLTripAnalysisOutput
from app.schemas.trip import TripCreate, TripResponse
from app.schemas.trip_location import TripLocationCreate, TripLocationResponse
from app.services.checkin_service import process_heartbeat_ping, verify_and_process_checkin
from app.services.trip_service import (
    complete_trip,
    create_trip,
    get_trip,
    list_active_trips,
    list_scheduled_trips,
    record_location,
    start_trip,
)

router = APIRouter(prefix="/trips", tags=["Trips"])
_VALID_TRIP_STATUSES = {"SCHEDULED", "ACTIVE", "ALERT", "COMPLETED", "CANCELLED"}

# ── Dashboard read endpoints ──────────────────────────────────────────────────


@router.get("/active", response_model=List[TripResponse], summary="List active trips")
def get_active_trips(db: Session = Depends(get_db)):
    """Return all trips with status ACTIVE or ALERT for real-time dashboard monitoring."""
    return list_active_trips(db)


@router.get("", response_model=List[TripResponse], summary="List trips")
def get_trips(
    trip_status: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return recent trip records, optionally filtered by lifecycle status."""
    query = db.query(Trip)
    if trip_status is not None:
        normalized_status = trip_status.upper()
        if normalized_status not in _VALID_TRIP_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid trip status '{trip_status}'. Must be one of: {sorted(_VALID_TRIP_STATUSES)}.",
            )
        query = query.filter(Trip.status == normalized_status)
    return query.order_by(Trip.id.desc()).limit(limit).all()


@router.get("/scheduled", response_model=List[TripResponse], summary="List scheduled employee trips")
def get_scheduled_trips(
    employee_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    """Return scheduled trips, optionally restricted to one employee."""
    if employee_id is not None and not db.query(Employee.id).filter(Employee.id == employee_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found.",
        )
    return list_scheduled_trips(db, employee_id)


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED, summary="Schedule a trip")
def schedule_trip(payload: TripCreate, db: Session = Depends(get_db)):
    """Create a database-backed scheduled trip using the shared trip service."""
    if not db.query(Employee.id).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {payload.employee_id} not found.",
        )
    if payload.driver_id is not None and not db.query(Driver.id).filter(Driver.id == payload.driver_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {payload.driver_id} not found.",
        )
    if payload.vehicle_id is not None and not db.query(Vehicle.id).filter(Vehicle.id == payload.vehicle_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {payload.vehicle_id} not found.",
        )
    return create_trip(db, payload)


@router.get("/{trip_id}", response_model=TripResponse, summary="Get trip by ID")
def get_trip_by_id(trip_id: int, db: Session = Depends(get_db)):
    """Fetch a trip record including heartbeat timestamps and current status."""
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found.",
        )
    return trip


@router.get(
    "/{trip_id}/locations",
    response_model=List[TripLocationResponse],
    summary="Trip telemetry history",
)
def get_trip_locations(trip_id: int, db: Session = Depends(get_db)):
    """Return chronological GPS telemetry for route-replay on the dashboard map."""
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found.",
        )
    return (
        db.query(TripLocation)
        .filter(TripLocation.trip_id == trip_id)
        .order_by(TripLocation.recorded_at.asc())
        .all()
    )


@router.get(
    "/{trip_id}/analysis",
    response_model=MLTripAnalysisOutput,
    summary="Run ML safety analysis",
)
def analyze_trip_safety(trip_id: int, db: Session = Depends(get_db)):
    """Invoke the ML safety analyser on current telemetry.

    Updates driver trust score and creates deduped Incident rows for detected flags.
    Safe to call multiple times — incidents are deduplicated inside the adapter.
    """
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found.",
        )
    try:
        return evaluate_trip_safety(db, trip_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML analysis failed: {exc}",
        )


# ── Mobile / simulator write endpoints ───────────────────────────────────────


@router.post("/{trip_id}/start", response_model=TripResponse, summary="Start trip")
def start_trip_route(trip_id: int, db: Session = Depends(get_db)):
    """Transition a SCHEDULED trip to ACTIVE and initialise both device heartbeats."""
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found.",
        )
    if trip.status != "SCHEDULED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Trip {trip_id} cannot be started: "
                f"current status is '{trip.status}'. Expected 'SCHEDULED'."
            ),
        )
    return start_trip(db, trip_id)


@router.post(
    "/{trip_id}/locations",
    response_model=TripLocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest GPS telemetry ping",
)
def post_location(
    trip_id: int,
    payload: TripLocationCreate,
    db: Session = Depends(get_db),
):
    """Record a GPS telemetry ping from an employee or driver device.

    The trip must be ACTIVE or ALERT. The body `trip_id` must match the URL path.
    Also refreshes the corresponding device heartbeat timestamp.
    """
    if payload.trip_id != trip_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Body trip_id ({payload.trip_id}) must match URL trip_id ({trip_id}).",
        )
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found.",
        )
    if trip.status not in ("ACTIVE", "ALERT"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Trip {trip_id} is not active (status: '{trip.status}'). "
                "Cannot record location for a non-running trip."
            ),
        )
    try:
        return record_location(
            db,
            trip_id,
            payload.source,
            payload.latitude,
            payload.longitude,
            payload.speed if payload.speed is not None else 0.0,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.post("/{trip_id}/heartbeat", summary="Device heartbeat ping")
def post_heartbeat(
    trip_id: int,
    payload: HeartbeatPing,
    db: Session = Depends(get_db),
):
    """Record a lightweight device-connectivity ping (no GPS required).

    Source must be EMPLOYEE or DRIVER. Used by the missed-heartbeat monitor.
    The body `trip_id` must match the URL path.
    """
    if payload.trip_id != trip_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Body trip_id ({payload.trip_id}) must match URL trip_id ({trip_id}).",
        )
    try:
        process_heartbeat_ping(db, trip_id, payload.source)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    return {"status": "ok", "trip_id": trip_id, "source": payload.source}


@router.post(
    "/{trip_id}/check-in",
    response_model=CheckInResponse,
    summary="Employee check-in (PIN verification)",
)
def post_checkin(
    trip_id: int,
    payload: CheckInRequest,
    db: Session = Depends(get_db),
):
    """Submit raw PIN for Argon2id verification.

    Normal PIN: records safe check-in.
    Duress PIN: silently raises CRITICAL DURESS_PIN incident while returning an
    identical outward response — attacker cannot distinguish safe from duress check-in.
    The body `trip_id` must match the URL path.
    """
    if payload.trip_id != trip_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Body trip_id ({payload.trip_id}) must match URL trip_id ({trip_id}).",
        )
    try:
        return verify_and_process_checkin(
            db,
            trip_id,
            payload.pin,
            payload.latitude,
            payload.longitude,
        )
    except PermissionError as exc:
        # 423 Locked — account is rate-limited due to brute-force attempts
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post(
    "/{trip_id}/complete",
    response_model=TripResponse,
    summary="Complete trip (doorstep arrival)",
)
def complete_trip_route(trip_id: int, db: Session = Depends(get_db)):
    """Mark a trip COMPLETED on confirmed doorstep arrival.

    Valid source statuses: ACTIVE, ALERT.
    SCHEDULED, COMPLETED and CANCELLED trips are rejected.
    """
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found.",
        )
    if trip.status == "SCHEDULED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Trip {trip_id} has not started yet (status: 'SCHEDULED').",
        )
    if trip.status in ("COMPLETED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Trip {trip_id} is already '{trip.status}'.",
        )
    return complete_trip(db, trip_id)
