"""Comprehensive Phase 5 Test Suite: Business Services & ML Integration.

Uses an isolated in-memory SQLite database to preserve existing rakshaq.db records.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Employee, Driver, Vehicle, Trip, TripLocation, Incident
from app.core.security import hash_pin
from app.schemas.trip import TripCreate
from app.services import (
    verify_and_process_checkin,
    process_heartbeat_ping,
    create_incident,
    check_missed_heartbeats,
    acknowledge_incident,
    resolve_incident,
    get_open_incidents,
    create_trip,
    start_trip,
    record_location,
    complete_trip,
    get_trip,
    list_active_trips,
)
from app.ml import evaluate_trip_safety


def get_test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_normal_checkin():
    """Verify normal PIN check-in updates heartbeat and resets failed attempts."""
    db = get_test_db()
    try:
        emp = Employee(
            name="Ananya S",
            phone="+919876543101",
            email="ananya@example.com",
            normal_pin_hash=hash_pin("1234"),
            duress_pin_hash=hash_pin("9999"),
        )
        db.add(emp)
        db.commit()

        trip = Trip(
            employee_id=emp.id,
            pickup_location="Tidel Park",
            destination="Adyar",
            status="ACTIVE",
            started_at=datetime.now(timezone.utc),
        )
        db.add(trip)
        db.commit()

        res = verify_and_process_checkin(db, trip.id, "1234", 12.9800, 80.2500)
        assert res.status == "ACKNOWLEDGED"
        assert res.message == "Check-in verified successfully"

        db.refresh(emp)
        db.refresh(trip)
        assert emp.failed_pin_attempts == 0
        assert trip.last_employee_heartbeat_at is not None
        assert trip.status == "ACTIVE"
    finally:
        db.close()


def test_duress_checkin_silent_alarm():
    """Verify duress PIN creates silent CRITICAL incident with identical outward response."""
    db = get_test_db()
    try:
        emp = Employee(
            name="Bhavani K",
            phone="+919876543102",
            email="bhavani@example.com",
            normal_pin_hash=hash_pin("1234"),
            duress_pin_hash=hash_pin("9999"),
        )
        db.add(emp)
        db.commit()

        trip = Trip(
            employee_id=emp.id,
            pickup_location="Tidel Park",
            destination="Velachery",
            status="ACTIVE",
            started_at=datetime.now(timezone.utc),
        )
        db.add(trip)
        db.commit()

        # Submit duress PIN
        res = verify_and_process_checkin(db, trip.id, "9999", 12.9810, 80.2450)
        # Outward response MUST be identical to normal check-in
        assert res.status == "ACKNOWLEDGED"
        assert res.message == "Check-in verified successfully"

        db.refresh(trip)
        assert trip.status == "ALERT"

        incidents = db.query(Incident).filter(Incident.trip_id == trip.id).all()
        assert len(incidents) == 1
        assert incidents[0].incident_type == "DURESS_PIN"
        assert incidents[0].severity == "CRITICAL"
        assert incidents[0].status == "OPEN"
    finally:
        db.close()


def test_pin_brute_force_lockout():
    """Verify 5 failed attempts trigger a 15-minute lockout."""
    db = get_test_db()
    try:
        emp = Employee(
            name="Chitra N",
            phone="+919876543103",
            email="chitra@example.com",
            normal_pin_hash=hash_pin("1234"),
            duress_pin_hash=hash_pin("9999"),
        )
        db.add(emp)
        db.commit()

        trip = Trip(
            employee_id=emp.id,
            pickup_location="Office",
            destination="Home",
            status="ACTIVE",
            started_at=datetime.now(timezone.utc),
        )
        db.add(trip)
        db.commit()

        for attempt in range(1, 5):
            try:
                verify_and_process_checkin(db, trip.id, "0000")
                assert False, "Should have failed on invalid PIN"
            except ValueError:
                db.refresh(emp)
                assert emp.failed_pin_attempts == attempt
                assert emp.pin_locked_until is None

        # 5th attempt triggers lockout
        try:
            verify_and_process_checkin(db, trip.id, "0000")
            assert False, "Should have failed on 5th attempt"
        except ValueError:
            db.refresh(emp)
            assert emp.failed_pin_attempts == 5
            assert emp.pin_locked_until is not None

        # Locked account rejects even valid PIN
        try:
            verify_and_process_checkin(db, trip.id, "1234")
            assert False, "Should have rejected due to lockout"
        except PermissionError as e:
            assert "temporarily locked" in str(e)
    finally:
        db.close()


def test_independent_heartbeats_and_deduplication():
    """Verify independent monitoring of employee and driver heartbeats."""
    db = get_test_db()
    try:
        emp = Employee(name="Divya P", phone="+919876543104", email="divya@example.com")
        db.add(emp)
        db.commit()

        trip = Trip(
            employee_id=emp.id,
            pickup_location="Office",
            destination="Home",
            status="ACTIVE",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            last_employee_heartbeat_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            last_driver_heartbeat_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        )
        db.add(trip)
        db.commit()

        # Employee check
        emp_alerts = check_missed_heartbeats(db, threshold_minutes=5, source="EMPLOYEE")
        assert len(emp_alerts) == 1
        assert emp_alerts[0].incident_type == "MISSED_CHECKIN"
        assert emp_alerts[0].severity == "HIGH"

        # Deduplication check
        emp_alerts_dup = check_missed_heartbeats(db, threshold_minutes=5, source="EMPLOYEE")
        assert len(emp_alerts_dup) == 0

        # Driver check
        drv_alerts = check_missed_heartbeats(db, threshold_minutes=5, source="DRIVER")
        assert len(drv_alerts) == 1
        assert drv_alerts[0].incident_type == "DRIVER_CONNECTIVITY_LOST"
        assert drv_alerts[0].severity == "MEDIUM"

        # Heartbeat ping resets
        process_heartbeat_ping(db, trip.id, "EMPLOYEE")
        db.refresh(trip)
        assert (datetime.now(timezone.utc) - trip.last_employee_heartbeat_at.replace(tzinfo=timezone.utc)).total_seconds() < 5
    finally:
        db.close()


def test_incident_lifecycle_and_state_guard():
    """Verify incident lifecycle and guard preventing COMPLETED trip revert."""
    db = get_test_db()
    try:
        emp = Employee(name="Ezhil R", phone="+919876543105", email="ezhil@example.com")
        db.add(emp)
        db.commit()

        trip = Trip(
            employee_id=emp.id,
            pickup_location="Office",
            destination="Home",
            status="ACTIVE",
            started_at=datetime.now(timezone.utc),
        )
        db.add(trip)
        db.commit()

        # Create incident -> transitions trip to ALERT
        inc = create_incident(db, trip.id, "ROUTE_DEVIATION", "HIGH", "Route deviation 500m")
        db.refresh(trip)
        assert trip.status == "ALERT"

        # Acknowledge
        acknowledge_incident(db, inc.id)
        assert inc.status == "ACKNOWLEDGED"

        # Resolve -> restores to ACTIVE because trip is ongoing
        resolve_incident(db, inc.id, "Returned to route")
        db.refresh(trip)
        assert trip.status == "ACTIVE"

        # Mark trip COMPLETED
        trip.status = "COMPLETED"
        trip.ended_at = datetime.now(timezone.utc)
        db.commit()

        # Add late incident on completed trip
        inc_late = Incident(trip_id=trip.id, incident_type="DOORSTEP_SOS", severity="HIGH", status="OPEN")
        db.add(inc_late)
        trip.status = "ALERT"
        db.commit()

        # Resolve late incident -> MUST NOT change COMPLETED trip back to ACTIVE!
        resolve_incident(db, inc_late.id)
        db.refresh(trip)
        assert trip.status != "ACTIVE"
    finally:
        db.close()


def test_trip_lifecycle_and_locations():
    """Verify trip scheduling, activation, dual telemetry, and doorstep completion."""
    db = get_test_db()
    try:
        emp = Employee(name="Farhana A", phone="+919876543106", email="farhana@example.com")
        driver = Driver(name="Ganesh T", phone="+919876543107", trust_score=100.0)
        vehicle = Vehicle(registration_number="TN04AA1111", vehicle_model="Honda Amaze")
        db.add_all([emp, driver, vehicle])
        db.commit()

        # Create
        trip_in = TripCreate(
            employee_id=emp.id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            pickup_location="DLF Cybercity",
            destination="Nanganallur",
            planned_route=[[12.9850, 80.2000], [12.9800, 80.1900]],
        )
        trip = create_trip(db, trip_in)
        assert trip.status == "SCHEDULED"

        # Start
        trip = start_trip(db, trip.id)
        assert trip.status == "ACTIVE"
        assert trip.started_at is not None

        # Dual telemetry
        loc_e = record_location(db, trip.id, "EMPLOYEE", 12.9840, 80.1990, speed=25.0)
        loc_d = record_location(db, trip.id, "DRIVER", 12.9841, 80.1989, speed=25.2)
        assert loc_e.source == "EMPLOYEE"
        assert loc_d.source == "DRIVER"

        # Active list
        assert len(list_active_trips(db)) == 1

        # Complete
        trip = complete_trip(db, trip.id)
        assert trip.status == "COMPLETED"
        assert trip.ended_at is not None
        assert len(list_active_trips(db)) == 0
    finally:
        db.close()


def test_ml_adapter_integration():
    """Verify ML adapter calls ml.analyzer.analyze_trip, updates trust score & deduplicates incidents."""
    db = get_test_db()
    try:
        emp = Employee(name="Geetha N", phone="+919876543108", email="geetha@example.com")
        driver = Driver(name="Hari M", phone="+919876543109", trust_score=100.0)
        vehicle = Vehicle(registration_number="TN05BB2222", vehicle_model="Tata Tigor")
        db.add_all([emp, driver, vehicle])
        db.commit()

        # Planned radial road route
        route = [
            [12.9680, 80.1500],
            [12.9602, 80.1618],
            [12.9550, 80.1750],
        ]
        trip = Trip(
            employee_id=emp.id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            pickup_location="Pallavaram",
            destination="Medavakkam",
            planned_route=route,
            status="ACTIVE",
            started_at=datetime.now(timezone.utc),
        )
        db.add(trip)
        db.commit()

        # 3 points deviating > 300m
        base_ts = 1710025200.0
        for i in range(3):
            loc = TripLocation(
                trip_id=trip.id,
                source="EMPLOYEE",
                latitude=12.9850 + (i * 0.001),
                longitude=80.1500,
                speed=35.0,
                recorded_at=datetime.fromtimestamp(base_ts + (i * 10), tz=timezone.utc),
            )
            db.add(loc)
        db.commit()

        # 1. Evaluate
        output = evaluate_trip_safety(db, trip.id)
        assert "ROUTE_DEVIATION" in output.flags
        assert output.trust_score < 100

        # 2. Check Driver trust score updated in DB
        db.refresh(driver)
        assert driver.trust_score == float(output.trust_score)

        # 3. Check Incident logged in DB
        db.refresh(trip)
        assert trip.status == "ALERT"
        incidents = db.query(Incident).filter(Incident.trip_id == trip.id).all()
        assert len(incidents) == 1
        assert incidents[0].incident_type == "ROUTE_DEVIATION"

        # 4. Deduplication: running again does not spam duplicate incident rows
        output2 = evaluate_trip_safety(db, trip.id)
        assert output2.flags == output.flags
        incidents_after = db.query(Incident).filter(Incident.trip_id == trip.id).all()
        assert len(incidents_after) == 1
    finally:
        db.close()


if __name__ == "__main__":
    print("Running test_normal_checkin...")
    test_normal_checkin()
    print("Running test_duress_checkin_silent_alarm...")
    test_duress_checkin_silent_alarm()
    print("Running test_pin_brute_force_lockout...")
    test_pin_brute_force_lockout()
    print("Running test_independent_heartbeats_and_deduplication...")
    test_independent_heartbeats_and_deduplication()
    print("Running test_incident_lifecycle_and_state_guard...")
    test_incident_lifecycle_and_state_guard()
    print("Running test_trip_lifecycle_and_locations...")
    test_trip_lifecycle_and_locations()
    print("Running test_ml_adapter_integration...")
    test_ml_adapter_integration()
    print("\nALL PHASE 5 TESTS PASSED SUCCESSFULLY!")

