"""Comprehensive verification suite for Phase 4: Pydantic Schemas, Security & Database Integrity."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from pydantic import ValidationError

import app.models
from app.core.security import (
    calculate_lockout_expiry,
    hash_pin,
    is_pin_locked,
    verify_pin,
)
from app.database import Base, ensure_schema_updated
from app.models import Driver, Employee, Incident, Trip, TripLocation, Vehicle
from app.schemas import (
    CheckInRequest,
    CheckInResponse,
    DriverCreate,
    DriverResponse,
    DriverUpdate,
    EmployeeCreate,
    EmployeePINSetup,
    EmployeeResponse,
    HeartbeatPing,
    IncidentCreate,
    IncidentResponse,
    MLDriverPoint,
    MLTelemetryPoint,
    MLTripAnalysisInput,
    MLTripAnalysisOutput,
    TripCreate,
    TripLocationCreate,
    TripLocationResponse,
    TripResponse,
    VehicleCreate,
    VehicleResponse,
)


def test_schema_employee():
    """Verify Employee schemas."""
    # Valid
    emp_in = EmployeeCreate(name="Ananya Sharma", phone="+919876543210", email="ananya@rakshaq.org")
    assert emp_in.name == "Ananya Sharma"

    # PIN Setup - different PINs (valid)
    pin_setup = EmployeePINSetup(normal_pin="1234", duress_pin="9999")
    assert pin_setup.normal_pin != pin_setup.duress_pin

    # PIN Setup - identical PINs (must raise ValidationError)
    try:
        EmployeePINSetup(normal_pin="1234", duress_pin="1234")
        assert False, "Should have failed with identical PINs"
    except ValidationError:
        pass


def test_schema_driver_trust_score():
    """Verify Driver trust score validation (0 - 100)."""
    # Valid
    driver = DriverCreate(name="Rajesh Kumar", phone="+919876543211", trust_score=85.0)
    assert driver.trust_score == 85.0

    # Invalid > 100
    try:
        DriverCreate(name="Rajesh Kumar", phone="+919876543211", trust_score=105.0)
        assert False, "Should have failed with trust_score > 100"
    except ValidationError:
        pass

    # Invalid < 0
    try:
        DriverCreate(name="Rajesh Kumar", phone="+919876543211", trust_score=-5.0)
        assert False, "Should have failed with trust_score < 0"
    except ValidationError:
        pass


def test_schema_planned_route_validation():
    """Verify planned route coordinate validation."""
    # Valid route
    valid_route = [[12.9680, 80.1500], [12.9602, 80.1618]]
    trip = TripCreate(
        employee_id=1,
        pickup_location="Tidel Park",
        destination="Pallavaram",
        planned_route=valid_route,
    )
    assert len(trip.planned_route) == 2

    # Invalid - coordinate with 3 elements
    try:
        TripCreate(
            employee_id=1,
            pickup_location="Tidel Park",
            destination="Pallavaram",
            planned_route=[[12.9680, 80.1500, 50.0]],
        )
        assert False, "Should have rejected 3-element coordinate"
    except ValidationError:
        pass

    # Invalid latitude > 90
    try:
        TripCreate(
            employee_id=1,
            pickup_location="Tidel Park",
            destination="Pallavaram",
            planned_route=[[95.0, 80.1500]],
        )
        assert False, "Should have rejected latitude > 90"
    except ValidationError:
        pass

    # Invalid longitude < -180
    try:
        TripCreate(
            employee_id=1,
            pickup_location="Tidel Park",
            destination="Pallavaram",
            planned_route=[[12.9680, -185.0]],
        )
        assert False, "Should have rejected longitude < -180"
    except ValidationError:
        pass


def test_schema_trip_location_bounds():
    """Verify TripLocation coordinates and multi-source streaming."""
    loc = TripLocationCreate(
        trip_id=1,
        source="EMPLOYEE",
        latitude=12.9716,
        longitude=80.1472,
        speed=25.5,
    )
    assert loc.source == "EMPLOYEE"
    assert loc.latitude == 12.9716

    driver_loc = TripLocationCreate(
        trip_id=1,
        source="DRIVER",
        latitude=12.9715,
        longitude=80.1470,
        speed=26.0,
    )
    assert driver_loc.source == "DRIVER"

    # Out of bounds lat
    try:
        TripLocationCreate(trip_id=1, source="EMPLOYEE", latitude=91.0, longitude=80.0)
        assert False, "Should have rejected latitude > 90"
    except ValidationError:
        pass


def test_schema_checkin_and_heartbeat():
    """Verify check-in schema accepts raw PIN and returns uniform response."""
    chk = CheckInRequest(trip_id=1, pin="1234", latitude=12.9680, longitude=80.1500)
    assert chk.pin == "1234"

    res = CheckInResponse(
        trip_id=1,
        status="ACKNOWLEDGED",
        message="Check-in verified successfully",
        timestamp=datetime.now(timezone.utc),
    )
    assert res.status == "ACKNOWLEDGED"

    hb = HeartbeatPing(trip_id=1, source="EMPLOYEE")
    assert hb.source == "EMPLOYEE"


def test_schema_ml_compatibility():
    """Verify exact match with ml.analyzer.analyze_trip contract."""
    ml_input = MLTripAnalysisInput(
        trip_id="TRIP_101",
        planned_route=[[12.9680, 80.1500], [12.9602, 80.1618]],
        points=[MLTelemetryPoint(lat=12.9680, lng=80.1500, speed=30.0, ts=1710000000)],
        driver_points=[MLDriverPoint(lat=12.9680, lng=80.1500, ts=1710000000)],
    )
    assert ml_input.trip_id == "TRIP_101"

    ml_output = MLTripAnalysisOutput(
        trip_id="TRIP_101",
        flags=["ROUTE_DEVIATION"],
        trust_score=85,
        reasons=["Deviated 350m from planned route"],
        gps_status="OK",
    )
    assert ml_output.trust_score == 85
    assert ml_output.gps_status == "OK"


def test_database_migration_and_relationships():
    """Verify database auto-migration and all 6 tables and relationships."""
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with test_engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE employees ("
            "id INTEGER NOT NULL PRIMARY KEY, "
            "name VARCHAR(100) NOT NULL, "
            "phone VARCHAR(20) NOT NULL, "
            "email VARCHAR(100) NOT NULL)"
        ))
    ensure_schema_updated(test_engine)
    Base.metadata.create_all(bind=test_engine)
    employee_columns = {
        column["name"] for column in inspect(test_engine).get_columns("employees")
    }
    assert {
        "normal_pin_hash",
        "duress_pin_hash",
        "failed_pin_attempts",
        "pin_locked_until",
    } <= employee_columns
    db = sessionmaker(bind=test_engine)()
    try:
        # 2. Create test employee with PIN hashes & rate limiting fields
        normal_h = hash_pin("1234")
        duress_h = hash_pin("9999")
        assert verify_pin("1234", normal_h) is True
        assert verify_pin("9999", duress_h) is True
        assert verify_pin("0000", normal_h) is False

        # Clean existing test records if any
        db.query(TripLocation).delete()
        db.query(Incident).delete()
        db.query(Trip).delete()
        db.query(Vehicle).delete()
        db.query(Driver).delete()
        db.query(Employee).delete()
        db.commit()

        emp = Employee(
            name="Priya Raman",
            phone="+919876543299",
            email="priya@rakshaq.org",
            normal_pin_hash=normal_h,
            duress_pin_hash=duress_h,
            failed_pin_attempts=0,
            pin_locked_until=None,
        )
        db.add(emp)

        driver = Driver(
            name="Murugan S",
            phone="+919876543288",
            trust_score=95.0,
            night_duty_eligible=True,
        )
        db.add(driver)

        vehicle = Vehicle(
            registration_number="TN09CA1234",
            vehicle_model="Toyota Innova",
        )
        db.add(vehicle)
        db.commit()

        # 3. Create Trip linking Employee, Driver, Vehicle
        trip = Trip(
            employee_id=emp.id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            pickup_location="Tidel Park, Tharamani",
            destination="Chromepet, Chennai",
            planned_route=[[12.9890, 80.2450], [12.9516, 80.1462]],
            status="ACTIVE",
            started_at=datetime.now(timezone.utc),
            last_employee_heartbeat_at=datetime.now(timezone.utc),
            last_driver_heartbeat_at=datetime.now(timezone.utc),
        )
        db.add(trip)
        db.commit()

        # 4. Create Incident & TripLocation
        inc = Incident(
            trip_id=trip.id,
            incident_type="ROUTE_DEVIATION",
            severity="HIGH",
            description="Vehicle deviated 400m from OMR corridor",
            latitude=12.9700,
            longitude=80.2100,
            status="OPEN",
        )
        db.add(inc)

        loc_emp = TripLocation(
            trip_id=trip.id,
            source="EMPLOYEE",
            latitude=12.9700,
            longitude=80.2100,
            speed=35.0,
        )
        loc_drv = TripLocation(
            trip_id=trip.id,
            source="DRIVER",
            latitude=12.9701,
            longitude=80.2101,
            speed=35.5,
        )
        db.add_all([loc_emp, loc_drv])
        db.commit()

        # 5. Verify all relationships bidirectional mapping
        db.refresh(emp)
        db.refresh(driver)
        db.refresh(vehicle)
        db.refresh(trip)

        assert len(emp.trips) == 1
        assert emp.trips[0].id == trip.id
        assert trip.employee.name == "Priya Raman"

        assert len(driver.trips) == 1
        assert trip.driver.name == "Murugan S"

        assert len(vehicle.trips) == 1
        assert trip.vehicle.registration_number == "TN09CA1234"

        assert len(trip.incidents) == 1
        assert trip.incidents[0].incident_type == "ROUTE_DEVIATION"
        assert inc.trip.id == trip.id

        assert len(trip.locations) == 2
        sources = {l.source for l in trip.locations}
        assert sources == {"EMPLOYEE", "DRIVER"}

        # 6. Verify Rate Limiting Helper
        assert is_pin_locked(None) is False
        expiry = calculate_lockout_expiry()
        assert is_pin_locked(expiry) is True

    finally:
        db.close()
        test_engine.dispose()


if __name__ == "__main__":
    print("Running test_schema_employee...")
    test_schema_employee()
    print("Running test_schema_driver_trust_score...")
    test_schema_driver_trust_score()
    print("Running test_schema_planned_route_validation...")
    test_schema_planned_route_validation()
    print("Running test_schema_trip_location_bounds...")
    test_schema_trip_location_bounds()
    print("Running test_schema_checkin_and_heartbeat...")
    test_schema_checkin_and_heartbeat()
    print("Running test_schema_ml_compatibility...")
    test_schema_ml_compatibility()
    print("Running test_database_migration_and_relationships...")
    test_database_migration_and_relationships()
    print("\nALL PHASE 4 TESTS PASSED SUCCESSFULLY!")
