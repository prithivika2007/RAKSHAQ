"""Phase 6 — Route Integration Tests

Tests all Phase 6 HTTP endpoints using an isolated in-memory SQLite database.
Production rakshaq.db is never touched.

Coverage:
  GET  /health
  GET  /trips/active
  GET  /trips/{id}
  GET  /trips/{id}/locations
  GET  /trips/{id}/analysis
  GET  /incidents
  GET  /employees
  GET  /drivers
  GET  /trips
  GET  /drivers/{id}
  POST /trips/{id}/start
  POST /trips/{id}/locations
  POST /trips/{id}/heartbeat
  POST /trips/{id}/check-in
  POST /trips/{id}/complete
  PATCH /incidents/{id}
  PATCH /drivers/{id}
"""

import sys
from pathlib import Path

# Resolve project paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_pin
from app.database import Base, ensure_schema_updated, get_db
from app.main import app

# ── In-memory test database ───────────────────────────────────────────────────
# StaticPool keeps a single SQLite :memory: connection for the entire test run.
# All sessions and the engine share the exact same connection, so table DDL
# and DML are always visible to each other without filesystem writes.

from sqlalchemy.pool import StaticPool

TEST_DB_URL = "sqlite://"  # Pure in-memory, no file

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create tables once — they persist for the whole process via StaticPool
Base.metadata.create_all(bind=test_engine)

client = TestClient(app, raise_server_exceptions=False)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _seed_db():
    """Seed a minimal dataset: employee, driver, vehicle, trip."""
    from app.models.driver import Driver
    from app.models.employee import Employee
    from app.models.trip import Trip
    from app.models.vehicle import Vehicle

    db = TestingSession()
    try:
        employee = Employee(
            name="Priya Test",
            phone="+919800000001",
            email="priya@test.local",
            normal_pin_hash=hash_pin("1234"),
            duress_pin_hash=hash_pin("9999"),
            failed_pin_attempts=0,
        )
        db.add(employee)
        db.flush()

        driver = Driver(
            name="Ravi Test",
            phone="+919800000002",
            trust_score=90.0,
            night_duty_eligible=True,
        )
        db.add(driver)
        db.flush()

        vehicle = Vehicle(
            registration_number="TN01AA0001",
            vehicle_model="Honda City",
        )
        db.add(vehicle)
        db.flush()

        trip = Trip(
            employee_id=employee.id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            pickup_location="Anna Nagar, Chennai",
            destination="T. Nagar, Chennai",
            planned_route=[[13.085, 80.210], [13.040, 80.233]],
            status="SCHEDULED",
        )
        db.add(trip)
        db.commit()

        ids = {
            "employee_id": employee.id,
            "driver_id": driver.id,
            "vehicle_id": vehicle.id,
            "trip_id": trip.id,
        }
    finally:
        db.close()
    return ids


def _clear_db():
    """Delete all rows from every table for test isolation (preserves schema)."""
    from app.models.incident import Incident
    from app.models.trip_location import TripLocation
    from app.models.trip import Trip
    from app.models.vehicle import Vehicle
    from app.models.driver import Driver
    from app.models.employee import Employee

    db = TestingSession()
    try:
        # Delete in dependency order (FK children first)
        db.query(Incident).delete()
        db.query(TripLocation).delete()
        db.query(Trip).delete()
        db.query(Vehicle).delete()
        db.query(Driver).delete()
        db.query(Employee).delete()
        db.commit()
    finally:
        db.close()


# ── Test: Health ──────────────────────────────────────────────────────────────

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# ── Test: GET /trips/active ───────────────────────────────────────────────────

def test_get_active_trips_empty():
    _clear_db()
    resp = client.get("/trips/active")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_active_trips_returns_active():
    _clear_db()
    ids = _seed_db()
    # Start the trip so it becomes ACTIVE
    client.post(f"/trips/{ids['trip_id']}/start")
    resp = client.get("/trips/active")
    assert resp.status_code == 200
    trips = resp.json()
    assert len(trips) == 1
    assert trips[0]["status"] == "ACTIVE"


# ── Test: Dashboard read endpoints ────────────────────────────────────────────

def test_dashboard_employee_and_driver_lists():
    _clear_db()
    ids = _seed_db()

    employees = client.get("/employees")
    assert employees.status_code == 200
    assert employees.json() == [{
        "id": ids["employee_id"],
        "name": "Priya Test",
        "phone": "+919800000001",
        "email": "priya@test.local",
        "pin_configured": True,
    }]
    assert "normal_pin_hash" not in employees.text
    assert "duress_pin_hash" not in employees.text

    drivers = client.get("/drivers")
    assert drivers.status_code == 200
    assert drivers.json() == [{
        "id": ids["driver_id"],
        "name": "Ravi Test",
        "phone": "+919800000002",
        "trust_score": 90.0,
        "night_duty_eligible": True,
    }]


def test_dashboard_trip_lists_include_scheduled_and_completed():
    _clear_db()
    ids = _seed_db()

    scheduled = client.get("/trips/scheduled")
    assert scheduled.status_code == 200
    assert [trip["id"] for trip in scheduled.json()] == [ids["trip_id"]]

    all_trips = client.get("/trips")
    assert all_trips.status_code == 200
    assert [(trip["id"], trip["status"]) for trip in all_trips.json()] == [
        (ids["trip_id"], "SCHEDULED")
    ]

    client.post(f"/trips/{ids['trip_id']}/start")
    completed = client.post(f"/trips/{ids['trip_id']}/complete")
    assert completed.status_code == 200
    completed_trips = client.get("/trips?status=completed")
    assert completed_trips.status_code == 200
    assert [(trip["id"], trip["status"]) for trip in completed_trips.json()] == [
        (ids["trip_id"], "COMPLETED")
    ]


def test_dashboard_trip_list_rejects_unknown_status():
    _clear_db()
    response = client.get("/trips?status=UNKNOWN")
    assert response.status_code == 422


def test_trip_migration_adds_last_checkin_timestamp():
    legacy_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with legacy_engine.begin() as connection:
        connection.execute(text("CREATE TABLE trips (id INTEGER NOT NULL PRIMARY KEY)"))

    ensure_schema_updated(legacy_engine)
    trip_columns = {column["name"] for column in inspect(legacy_engine).get_columns("trips")}
    assert "last_checkin_at" in trip_columns
    legacy_engine.dispose()


# ── Test: GET /trips/{id} ─────────────────────────────────────────────────────

def test_get_trip_by_id_found():
    _clear_db()
    ids = _seed_db()
    resp = client.get(f"/trips/{ids['trip_id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == ids["trip_id"]
    assert data["status"] == "SCHEDULED"


def test_get_trip_not_found():
    _clear_db()
    resp = client.get("/trips/9999")
    assert resp.status_code == 404


# ── Test: POST /trips/{id}/start ──────────────────────────────────────────────

def test_start_trip_success():
    _clear_db()
    ids = _seed_db()
    resp = client.post(f"/trips/{ids['trip_id']}/start")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"


def test_start_trip_already_active():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/start")
    resp = client.post(f"/trips/{ids['trip_id']}/start")
    assert resp.status_code == 409


def test_start_trip_not_found():
    _clear_db()
    resp = client.post("/trips/9999/start")
    assert resp.status_code == 404


# ── Test: POST /trips/{id}/locations ─────────────────────────────────────────

def test_post_location_success():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/start")
    payload = {
        "trip_id": ids["trip_id"],
        "source": "EMPLOYEE",
        "latitude": 13.085,
        "longitude": 80.210,
        "speed": 25.5,
    }
    resp = client.post(f"/trips/{ids['trip_id']}/locations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["source"] == "EMPLOYEE"
    assert data["latitude"] == 13.085


def test_post_location_trip_not_active():
    _clear_db()
    ids = _seed_db()
    # Trip is SCHEDULED — should be rejected
    payload = {
        "trip_id": ids["trip_id"],
        "source": "EMPLOYEE",
        "latitude": 13.085,
        "longitude": 80.210,
    }
    resp = client.post(f"/trips/{ids['trip_id']}/locations", json=payload)
    assert resp.status_code == 409


def test_post_location_mismatched_trip_id():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/start")
    payload = {
        "trip_id": 9999,  # Mismatch
        "source": "DRIVER",
        "latitude": 13.040,
        "longitude": 80.233,
    }
    resp = client.post(f"/trips/{ids['trip_id']}/locations", json=payload)
    assert resp.status_code == 422


def test_post_location_invalid_coords():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/start")
    payload = {
        "trip_id": ids["trip_id"],
        "source": "EMPLOYEE",
        "latitude": 999.0,   # Out of bounds
        "longitude": 80.210,
    }
    resp = client.post(f"/trips/{ids['trip_id']}/locations", json=payload)
    assert resp.status_code == 422


# ── Test: GET /trips/{id}/locations ──────────────────────────────────────────

def test_get_locations_returns_history():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/start")
    for i in range(3):
        client.post(f"/trips/{ids['trip_id']}/locations", json={
            "trip_id": ids["trip_id"],
            "source": "EMPLOYEE",
            "latitude": 13.085 - i * 0.01,
            "longitude": 80.210 + i * 0.01,
        })
    resp = client.get(f"/trips/{ids['trip_id']}/locations")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_get_locations_trip_not_found():
    _clear_db()
    resp = client.get("/trips/9999/locations")
    assert resp.status_code == 404


# ── Test: POST /trips/{id}/heartbeat ─────────────────────────────────────────

def test_heartbeat_success():
    _clear_db()
    ids = _seed_db()
    resp = client.post(f"/trips/{ids['trip_id']}/heartbeat", json={
        "trip_id": ids["trip_id"],
        "source": "EMPLOYEE",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_heartbeat_driver_source():
    _clear_db()
    ids = _seed_db()
    resp = client.post(f"/trips/{ids['trip_id']}/heartbeat", json={
        "trip_id": ids["trip_id"],
        "source": "DRIVER",
    })
    assert resp.status_code == 200
    assert resp.json()["source"] == "DRIVER"


def test_heartbeat_mismatched_trip_id():
    _clear_db()
    ids = _seed_db()
    resp = client.post(f"/trips/{ids['trip_id']}/heartbeat", json={
        "trip_id": 9999,
        "source": "EMPLOYEE",
    })
    assert resp.status_code == 422


# ── Test: POST /trips/{id}/check-in ──────────────────────────────────────────

def test_checkin_normal_pin():
    _clear_db()
    ids = _seed_db()
    resp = client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "1234",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACKNOWLEDGED"
    assert data["trip_id"] == ids["trip_id"]
    trip = client.get(f"/trips/{ids['trip_id']}").json()
    assert trip["last_checkin_at"] == data["timestamp"]


def test_checkin_duress_pin_identical_response():
    """Duress PIN must return the same outward response as normal PIN."""
    _clear_db()
    ids = _seed_db()
    resp = client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "9999",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACKNOWLEDGED"  # Identical — attacker cannot distinguish
    assert data["message"] == "Check-in verified successfully"
    trip = client.get(f"/trips/{ids['trip_id']}").json()
    assert trip["last_checkin_at"] == data["timestamp"]

    # Verify DURESS_PIN incident was raised silently
    from app.models.incident import Incident
    db = TestingSession()
    try:
        duress = db.query(Incident).filter(
            Incident.trip_id == ids["trip_id"],
            Incident.incident_type == "DURESS_PIN",
        ).first()
        assert duress is not None
        assert duress.severity == "CRITICAL"
    finally:
        db.close()


def test_checkin_wrong_pin_returns_401():
    _clear_db()
    ids = _seed_db()
    resp = client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "0000",
    })
    assert resp.status_code == 401


def test_checkin_brute_force_lockout():
    """Five wrong PINs should lock the account (423 Locked)."""
    _clear_db()
    ids = _seed_db()
    for _ in range(5):
        client.post(f"/trips/{ids['trip_id']}/check-in", json={
            "trip_id": ids["trip_id"],
            "pin": "wrong",
        })
    resp = client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "1234",
    })
    assert resp.status_code == 423


# ── Test: POST /trips/{id}/complete ──────────────────────────────────────────

def test_complete_trip_success():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/start")
    resp = client.post(f"/trips/{ids['trip_id']}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"


def test_complete_scheduled_trip_rejected():
    _clear_db()
    ids = _seed_db()
    resp = client.post(f"/trips/{ids['trip_id']}/complete")
    assert resp.status_code == 409


def test_complete_already_completed_rejected():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/start")
    client.post(f"/trips/{ids['trip_id']}/complete")
    resp = client.post(f"/trips/{ids['trip_id']}/complete")
    assert resp.status_code == 409


# ── Test: GET /incidents ──────────────────────────────────────────────────────

def test_list_incidents_empty():
    _clear_db()
    resp = client.get("/incidents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_incidents_by_trip_id():
    _clear_db()
    ids = _seed_db()
    # Create an incident via duress check-in
    client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "9999",
    })
    resp = client.get(f"/incidents?trip_id={ids['trip_id']}")
    assert resp.status_code == 200
    incidents = resp.json()
    assert len(incidents) >= 1
    assert all(i["trip_id"] == ids["trip_id"] for i in incidents)


def test_list_incidents_by_status():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "9999",
    })
    resp = client.get("/incidents?status=OPEN")
    assert resp.status_code == 200
    for inc in resp.json():
        assert inc["status"] == "OPEN"

def test_list_incidents_returns_all_statuses():
    _clear_db()
    ids = _seed_db()

    client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "9999",
    })

    incidents = client.get("/incidents").json()
    assert incidents

    incident_id = incidents[0]["id"]

    client.patch(
        f"/incidents/{incident_id}",
        json={"status": "RESOLVED"}
    )

    resp = client.get("/incidents")
    assert resp.status_code == 200
    assert any(i["status"] == "RESOLVED" for i in resp.json())


# ── Test: PATCH /incidents/{id} ───────────────────────────────────────────────

def test_acknowledge_incident():
    _clear_db()
    ids = _seed_db()
    # Trigger a duress incident
    client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "9999",
    })
    incidents = client.get("/incidents").json()
    assert incidents, "Expected at least one incident"
    inc_id = incidents[0]["id"]

    resp = client.patch(f"/incidents/{inc_id}", json={"status": "ACKNOWLEDGED"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACKNOWLEDGED"


def test_resolve_incident():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "9999",
    })
    incidents = client.get("/incidents").json()
    inc_id = incidents[0]["id"]

    resp = client.patch(f"/incidents/{inc_id}", json={
        "status": "RESOLVED",
        "description": "Confirmed safe by supervisor",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESOLVED"


def test_patch_incident_not_found():
    _clear_db()
    resp = client.patch("/incidents/9999", json={"status": "ACKNOWLEDGED"})
    assert resp.status_code == 404


def test_patch_incident_severity_only():
    _clear_db()
    ids = _seed_db()
    client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "9999",
    })
    incidents = client.get("/incidents").json()
    inc_id = incidents[0]["id"]

    resp = client.patch(f"/incidents/{inc_id}", json={"severity": "LOW"})
    assert resp.status_code == 200
    assert resp.json()["severity"] == "LOW"


# ── Test: GET /drivers/{id} ───────────────────────────────────────────────────

def test_get_driver_found():
    _clear_db()
    ids = _seed_db()
    resp = client.get(f"/drivers/{ids['driver_id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == ids["driver_id"]
    assert data["trust_score"] == 90.0


def test_get_driver_not_found():
    _clear_db()
    resp = client.get("/drivers/9999")
    assert resp.status_code == 404


# ── Test: PATCH /drivers/{id} ─────────────────────────────────────────────────

def test_patch_driver_trust_score():
    _clear_db()
    ids = _seed_db()
    resp = client.patch(f"/drivers/{ids['driver_id']}", json={"trust_score": 75.0})
    assert resp.status_code == 200
    assert resp.json()["trust_score"] == 75.0


def test_patch_driver_trust_score_out_of_bounds():
    _clear_db()
    ids = _seed_db()
    resp = client.patch(f"/drivers/{ids['driver_id']}", json={"trust_score": 150.0})
    assert resp.status_code == 422


def test_patch_driver_not_found():
    _clear_db()
    resp = client.patch("/drivers/9999", json={"trust_score": 80.0})
    assert resp.status_code == 404


def test_patch_driver_night_duty_eligible():
    _clear_db()
    ids = _seed_db()
    resp = client.patch(f"/drivers/{ids['driver_id']}", json={"night_duty_eligible": False})
    assert resp.status_code == 200
    assert resp.json()["night_duty_eligible"] is False


# ── Test: Status transition guard (COMPLETED trip stays COMPLETED) ────────────

def test_completed_trip_not_reverted_to_active():
    """Resolving an incident on a COMPLETED trip must not revert it to ACTIVE."""
    _clear_db()
    ids = _seed_db()
    # Start → duress check-in (creates incident + sets ALERT) → complete trip
    client.post(f"/trips/{ids['trip_id']}/start")
    client.post(f"/trips/{ids['trip_id']}/check-in", json={
        "trip_id": ids["trip_id"],
        "pin": "9999",
    })
    client.post(f"/trips/{ids['trip_id']}/complete")

    # Verify trip is COMPLETED
    trip_resp = client.get(f"/trips/{ids['trip_id']}").json()
    assert trip_resp["status"] == "COMPLETED"

    # Resolve the incident
    incidents = client.get(f"/incidents?trip_id={ids['trip_id']}&status=OPEN").json()
    if incidents:
        client.patch(f"/incidents/{incidents[0]['id']}", json={"status": "RESOLVED"})

    # Trip must remain COMPLETED
    trip_resp = client.get(f"/trips/{ids['trip_id']}").json()
    assert trip_resp["status"] == "COMPLETED"


# ── Test: GET /trips/{id}/analysis ────────────────────────────────────────────

def test_analysis_no_locations():
    """ML analysis should succeed even with zero telemetry points."""
    _clear_db()
    ids = _seed_db()
    resp = client.get(f"/trips/{ids['trip_id']}/analysis")
    assert resp.status_code == 200


def test_analysis_trip_not_found():
    _clear_db()
    resp = client.get("/trips/9999/analysis")
    assert resp.status_code == 404


def test_employee_to_dashboard_end_to_end():
    """Verify employee actions persist and are visible through dashboard routes."""
    _clear_db()
    ids = _seed_db()

    verification = client.post("/employees/verify", json={
        "employee_id": ids["employee_id"],
        "phone": "+919800000001",
    })
    assert verification.status_code == 200
    assert verification.json()["id"] == ids["employee_id"]

    scheduled = client.get(f"/trips/scheduled?employee_id={ids['employee_id']}")
    assert scheduled.status_code == 200
    assert len(scheduled.json()) == 1

    trip_id = ids["trip_id"]
    started = client.post(f"/trips/{trip_id}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "ACTIVE"
    assert started.json()["last_employee_heartbeat_at"].endswith(("Z", "+00:00"))

    normal_checkin = client.post(f"/trips/{trip_id}/check-in", json={
        "trip_id": trip_id,
        "pin": "1234",
    })
    assert normal_checkin.status_code == 200
    assert normal_checkin.json()["message"] == "Check-in verified successfully"

    gps_ping = client.post(f"/trips/{trip_id}/locations", json={
        "trip_id": trip_id,
        "source": "EMPLOYEE",
        "latitude": 13.085,
        "longitude": 80.210,
        "speed": 30,
    })
    assert gps_ping.status_code == 201
    assert gps_ping.json()["source"] == "EMPLOYEE"
    assert gps_ping.json()["recorded_at"].endswith(("Z", "+00:00"))

    duress_checkin = client.post(f"/trips/{trip_id}/check-in", json={
        "trip_id": trip_id,
        "pin": "9999",
        "latitude": 13.085,
        "longitude": 80.210,
    })
    assert duress_checkin.status_code == 200
    assert duress_checkin.json()["message"] == normal_checkin.json()["message"]
    assert duress_checkin.json()["status"] == normal_checkin.json()["status"]

    sos = client.post("/incidents", json={
        "trip_id": trip_id,
        "incident_type": "SOS",
        "severity": "CRITICAL",
        "description": "Employee initiated an emergency SOS.",
        "latitude": 13.085,
        "longitude": 80.210,
    })
    assert sos.status_code == 201
    assert sos.json()["created_at"].endswith(("Z", "+00:00"))

    # Three consecutive off-route samples exercise the real ML adapter.
    for offset in (0.0, 0.001, 0.002):
        response = client.post(f"/trips/{trip_id}/locations", json={
            "trip_id": trip_id,
            "source": "EMPLOYEE",
            "latitude": 13.085 + offset,
            "longitude": 80.230,
            "speed": 30,
        })
        assert response.status_code == 201

    analysis = client.get(f"/trips/{trip_id}/analysis")
    assert analysis.status_code == 200
    assert "ROUTE_DEVIATION" in analysis.json()["flags"]
    assert analysis.json()["trust_score"] < 100

    # These are the same live read endpoints used by the dashboard.
    active_trips = client.get("/trips/active")
    assert active_trips.status_code == 200
    assert active_trips.json()[0]["id"] == trip_id
    locations = client.get(f"/trips/{trip_id}/locations")
    assert locations.status_code == 200
    assert len(locations.json()) == 4
    incidents = client.get("/incidents")
    assert incidents.status_code == 200
    incident_types = {incident["incident_type"] for incident in incidents.json()}
    assert {"DURESS_PIN", "SOS", "ROUTE_DEVIATION"} <= incident_types

    driver = client.get(f"/drivers/{ids['driver_id']}")
    assert driver.status_code == 200
    assert driver.json()["trust_score"] == float(analysis.json()["trust_score"])

    completed = client.post(f"/trips/{trip_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"
    stored_trip = client.get(f"/trips/{trip_id}")
    assert stored_trip.status_code == 200
    assert stored_trip.json()["status"] == "COMPLETED"


def test_chennai_seed_script_creates_idempotent_demo_records():
    """Run the actual seed function against an isolated in-memory database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.core.security import verify_pin
    from app.models import Driver, Employee, Trip, Vehicle
    from scripts import seed_chennai

    seed_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=seed_engine)
    original_engine = seed_chennai.engine
    original_session_local = seed_chennai.SessionLocal
    seed_session = sessionmaker(autocommit=False, autoflush=False, bind=seed_engine)
    seed_chennai.engine = seed_engine
    seed_chennai.SessionLocal = seed_session

    try:
        seed_chennai.seed()
        seed_chennai.seed()

        db = seed_session()
        try:
            employee = db.query(Employee).filter_by(email=seed_chennai.EMPLOYEE_EMAIL).one()
            driver = db.query(Driver).filter_by(phone=seed_chennai.DRIVER_PHONE).one()
            vehicle = db.query(Vehicle).filter_by(
                registration_number=seed_chennai.VEHICLE_REG
            ).one()
            trip = db.query(Trip).filter_by(
                employee_id=employee.id,
                driver_id=driver.id,
                vehicle_id=vehicle.id,
            ).one()
            assert verify_pin(seed_chennai.NORMAL_PIN, employee.normal_pin_hash)
            assert verify_pin(seed_chennai.DURESS_PIN, employee.duress_pin_hash)
            assert trip.status == "SCHEDULED"
            assert db.query(Employee).count() == 1
            assert db.query(Driver).count() == 1
            assert db.query(Vehicle).count() == 1
            assert db.query(Trip).count() == 1
        finally:
            db.close()
    finally:
        seed_chennai.engine = original_engine
        seed_chennai.SessionLocal = original_session_local
        seed_engine.dispose()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_health,
        test_get_active_trips_empty,
        test_get_active_trips_returns_active,
        test_get_trip_by_id_found,
        test_get_trip_not_found,
        test_start_trip_success,
        test_start_trip_already_active,
        test_start_trip_not_found,
        test_post_location_success,
        test_post_location_trip_not_active,
        test_post_location_mismatched_trip_id,
        test_post_location_invalid_coords,
        test_get_locations_returns_history,
        test_get_locations_trip_not_found,
        test_heartbeat_success,
        test_heartbeat_driver_source,
        test_heartbeat_mismatched_trip_id,
        test_checkin_normal_pin,
        test_checkin_duress_pin_identical_response,
        test_checkin_wrong_pin_returns_401,
        test_checkin_brute_force_lockout,
        test_complete_trip_success,
        test_complete_scheduled_trip_rejected,
        test_complete_already_completed_rejected,
        test_list_incidents_empty,
        test_list_incidents_by_trip_id,
        test_list_incidents_by_status,
        test_list_incidents_returns_all_statuses,
        test_acknowledge_incident,
        test_resolve_incident,
        test_patch_incident_not_found,
        test_patch_incident_severity_only,
        test_get_driver_found,
        test_get_driver_not_found,
        test_patch_driver_trust_score,
        test_patch_driver_trust_score_out_of_bounds,
        test_patch_driver_not_found,
        test_patch_driver_night_duty_eligible,
        test_completed_trip_not_reverted_to_active,
        test_analysis_no_locations,
        test_analysis_trip_not_found,
        test_employee_to_dashboard_end_to_end,
        test_chennai_seed_script_creates_idempotent_demo_records,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  ❌ {t.__name__}: {exc}")
            failed += 1

    print(f"\nPhase 6: {passed} passed, {failed} failed out of {len(tests)} tests.")
    sys.exit(0 if failed == 0 else 1)