"""Secure check-in and heartbeat processing service for RAKSHAQ.

Handles Argon2id PIN verification, silent duress escalation,
and brute-force rate-limiting lockout.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import (
    MAX_PIN_ATTEMPTS,
    calculate_lockout_expiry,
    is_pin_locked,
    verify_pin,
)
from app.models.employee import Employee
from app.models.incident import Incident
from app.models.trip import Trip
from app.schemas.checkin import CheckInResponse


def verify_and_process_checkin(
    db: Session,
    trip_id: int,
    pin: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> CheckInResponse:
    """Verify an employee check-in PIN securely.

    1. Enforces rate limiting against brute-force attacks (5 attempts / 15-min lockout).
    2. Compares against normal_pin_hash using Argon2id (resets failures, records safe progress).
    3. Compares against duress_pin_hash using Argon2id (SILENTLY generates a CRITICAL DURESS_PIN incident).
    4. For BOTH normal and duress check-ins, returns an IDENTICAL outward response to protect user safety.
    5. Invalid PIN increments failure count, commits failure state, and locks account after MAX_PIN_ATTEMPTS.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise ValueError(f"Trip with ID {trip_id} does not exist.")

    employee = db.query(Employee).filter(Employee.id == trip.employee_id).first()
    if not employee:
        raise ValueError(f"Employee for Trip {trip_id} not found.")

    # 1. Check if account is currently locked out
    if is_pin_locked(employee.pin_locked_until):
        raise PermissionError(
            "Account is temporarily locked due to multiple failed PIN attempts. Please wait before retrying."
        )

    now = datetime.now(timezone.utc)

    # 2. Check for Normal PIN Match
    if verify_pin(pin, employee.normal_pin_hash):
        employee.failed_pin_attempts = 0
        employee.pin_locked_until = None
        trip.last_employee_heartbeat_at = now
        trip.last_checkin_at = now
        db.commit()

        return CheckInResponse(
            trip_id=trip_id,
            status="ACKNOWLEDGED",
            message="Check-in verified successfully",
            timestamp=now,
        )

    # 3. Check for Duress PIN Match (Silent Emergency Alarm)
    if verify_pin(pin, employee.duress_pin_hash):
        employee.failed_pin_attempts = 0
        employee.pin_locked_until = None
        trip.last_employee_heartbeat_at = now
        trip.last_checkin_at = now
        trip.status = "ALERT"

        # Covertly raise CRITICAL incident - attacker sees standard confirmation on phone screen
        incident = Incident(
            trip_id=trip_id,
            incident_type="DURESS_PIN",
            severity="CRITICAL",
            description="Duress PIN entered by employee - silent distress escalation triggered",
            latitude=latitude,
            longitude=longitude,
            status="OPEN",
        )
        db.add(incident)
        db.commit()

        # Identical outward response to preserve employee safety
        return CheckInResponse(
            trip_id=trip_id,
            status="ACKNOWLEDGED",
            message="Check-in verified successfully",
            timestamp=now,
        )

    # 4. Neither PIN matched: increment failed attempts & check for lockout
    employee.failed_pin_attempts += 1
    if employee.failed_pin_attempts >= MAX_PIN_ATTEMPTS:
        employee.pin_locked_until = calculate_lockout_expiry()

    # Commit failure count before raising exception so brute-force protection persists
    db.commit()
    raise ValueError("Invalid check-in PIN.")


def process_heartbeat_ping(db: Session, trip_id: int, source: str) -> Trip:
    """Record a device connectivity heartbeat from employee or driver."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise ValueError(f"Trip with ID {trip_id} does not exist.")

    now = datetime.now(timezone.utc)
    if source.upper() == "EMPLOYEE":
        trip.last_employee_heartbeat_at = now
    elif source.upper() == "DRIVER":
        trip.last_driver_heartbeat_at = now
    else:
        raise ValueError(f"Unknown heartbeat source: {source}. Must be 'EMPLOYEE' or 'DRIVER'.")

    db.commit()
    db.refresh(trip)
    return trip
