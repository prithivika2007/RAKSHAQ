"""Chennai Demo Seed Script — RAKSHAQ

Creates one idempotent demo dataset:
  • 1 Employee  — Meera Subramaniam
  • 1 Driver    — Rajan Pillai (trust_score=92.0)
  • 1 Vehicle   — TN 09 BV 4321
  • 1 Trip      — OMR → Sholinganallur (SCHEDULED)

Run from the backend/ directory:
    python scripts/seed_chennai.py

The script is IDEMPOTENT — re-running it will not create duplicate records.
It never touches existing production data beyond the demo records it owns.
"""

import sys
from pathlib import Path

# Ensure 'app' package is importable when run from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_pin
from app.database import SessionLocal, engine, ensure_schema_updated
from app.database import Base
from app.models import Employee, Driver, Vehicle, Trip  # noqa: F401

# Seed constants (Chennai demo data)
EMPLOYEE_EMAIL = "meera.subramaniam@rakshaq.demo"
EMPLOYEE_PHONE = "+919840001234"
DRIVER_PHONE   = "+919500005678"
VEHICLE_REG    = "TN09BV4321"

NORMAL_PIN = "2810"   # Meera's regular check-in PIN
DURESS_PIN = "9999"   # Meera's silent duress PIN (must differ from normal)

# Planned route: OMR → Sholinganallur (Chennai)
PLANNED_ROUTE = [
    [12.9279, 80.2080],   # Old Mahabalipuram Road near Perungudi
    [12.9220, 80.2130],
    [12.9120, 80.2200],
    [12.9004, 80.2275],   # Sholinganallur signal
]


def seed():
    # Apply any pending schema migrations
    ensure_schema_updated(engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── Employee ──────────────────────────────────────────────────────────
        employee = db.query(Employee).filter(Employee.email == EMPLOYEE_EMAIL).first()
        if not employee:
            employee = Employee(
                name="Meera Subramaniam",
                phone=EMPLOYEE_PHONE,
                email=EMPLOYEE_EMAIL,
                normal_pin_hash=hash_pin(NORMAL_PIN),
                duress_pin_hash=hash_pin(DURESS_PIN),
                failed_pin_attempts=0,
            )
            db.add(employee)
            db.flush()
            print(f"[seed] Created employee: {employee.name} (id={employee.id})")
        else:
            print(f"[seed] Employee already exists: {employee.name} (id={employee.id})")

        # ── Driver ────────────────────────────────────────────────────────────
        driver = db.query(Driver).filter(Driver.phone == DRIVER_PHONE).first()
        if not driver:
            driver = Driver(
                name="Rajan Pillai",
                phone=DRIVER_PHONE,
                trust_score=92.0,
                night_duty_eligible=True,
            )
            db.add(driver)
            db.flush()
            print(f"[seed] Created driver: {driver.name} (id={driver.id})")
        else:
            print(f"[seed] Driver already exists: {driver.name} (id={driver.id})")

        # ── Vehicle ───────────────────────────────────────────────────────────
        vehicle = db.query(Vehicle).filter(Vehicle.registration_number == VEHICLE_REG).first()
        if not vehicle:
            vehicle = Vehicle(
                registration_number=VEHICLE_REG,
                vehicle_model="Maruti Suzuki Swift Dzire",
            )
            db.add(vehicle)
            db.flush()
            print(f"[seed] Created vehicle: {vehicle.registration_number} (id={vehicle.id})")
        else:
            print(f"[seed] Vehicle already exists: {vehicle.registration_number} (id={vehicle.id})")

        # ── Trip ──────────────────────────────────────────────────────────────
        # Idempotency: reuse the demo trip regardless of its current status
        trip = (
            db.query(Trip)
            .filter(
                Trip.employee_id == employee.id,
                Trip.driver_id == driver.id,
                Trip.vehicle_id == vehicle.id,
                Trip.pickup_location == "Old Mahabalipuram Road, Perungudi, Chennai",
                Trip.destination == "Sholinganallur, Chennai",
            )
            .first()
        )
        if not trip:
            trip = Trip(
                employee_id=employee.id,
                driver_id=driver.id,
                vehicle_id=vehicle.id,
                pickup_location="Old Mahabalipuram Road, Perungudi, Chennai",
                destination="Sholinganallur, Chennai",
                planned_route=PLANNED_ROUTE,
                status="SCHEDULED",
            )
            db.add(trip)
            db.flush()
            print(f"[seed] Created trip: {trip.pickup_location} -> {trip.destination} (id={trip.id})")
        else:
            print(f"[seed] Trip already exists (id={trip.id}, status={trip.status})")

        db.commit()
        print("\n[seed] Chennai demo seed complete.")
        print(f"       employee_id={employee.id}  driver_id={driver.id}"
              f"  vehicle_id={vehicle.id}  trip_id={trip.id}")
        print(f"       Normal PIN : {NORMAL_PIN}")
        print(f"       Duress PIN : {DURESS_PIN}")

    except Exception as exc:
        db.rollback()
        print(f"[seed] Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
