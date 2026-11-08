"""Non-invasive adapter bridging backend telemetry to the root ML module.

Directly consumes the exact contract of ml.analyzer.analyze_trip without
modifying any code or files in the root ml/ directory.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

# Ensure project root is in sys.path so ml package can be imported cleanly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.analyzer import analyze_trip

from app.models.driver import Driver
from app.models.incident import Incident
from app.models.trip import Trip
from app.models.trip_location import TripLocation
from app.schemas.ml import MLTripAnalysisOutput


def evaluate_trip_safety(
    db: Session,
    trip_id: int,
    rider_feedback: Optional[Any] = None,
) -> MLTripAnalysisOutput:
    """Analyze a trip using the teammate's rule-based ML analyzer.

    1. Extracts chronological telemetry points from TripLocation.
    2. Maps points into employee telemetry and driver telemetry arrays.
    3. Invokes ml.analyzer.analyze_trip(data).
    4. Updates Driver.trust_score in SQLite.
    5. Automatically logs Incident rows for any returned anomaly flags
       (ROUTE_DEVIATION, UNEXPECTED_STOP, GPS_MISMATCH) with deduplication.
    6. Transitions trip.status to ALERT if safety anomalies were detected.
    7. Returns an MLTripAnalysisOutput object matching the exact ML contract.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise ValueError(f"Trip with ID {trip_id} not found.")

    locations = (
        db.query(TripLocation)
        .filter(TripLocation.trip_id == trip_id)
        .order_by(TripLocation.recorded_at.asc())
        .all()
    )

    # Format telemetry points matching ml.analyzer input schema
    points: List[Dict[str, Any]] = []
    driver_points: List[Dict[str, Any]] = []

    for loc in locations:
        ts = loc.recorded_at.timestamp() if loc.recorded_at else 0.0
        if loc.source == "EMPLOYEE":
            points.append({
                "lat": loc.latitude,
                "lng": loc.longitude,
                "speed": loc.speed if loc.speed is not None else 0.0,
                "ts": ts,
            })
        elif loc.source == "DRIVER":
            driver_points.append({
                "lat": loc.latitude,
                "lng": loc.longitude,
                "ts": ts,
            })

    ml_payload: Dict[str, Any] = {
        "trip_id": str(trip.id),
        "planned_route": trip.planned_route if isinstance(trip.planned_route, list) else [],
        "points": points,
        "driver_points": driver_points,
        "rider_feedback": rider_feedback,
    }

    # Execute ML anomaly detection and driver trust scoring
    raw_result = analyze_trip(ml_payload)

    flags: List[str] = raw_result.get("flags", [])
    trust_score: int = int(raw_result.get("trust_score", 100))
    reasons: List[str] = raw_result.get("reasons", [])
    gps_status: str = raw_result.get("gps_status", "UNAVAILABLE" if not driver_points else "OK")

    # Update Driver trust score if assigned
    if trip.driver_id:
        driver = db.query(Driver).filter(Driver.id == trip.driver_id).first()
        if driver:
            driver.trust_score = float(trust_score)

    # Automatically create Incident records for detected flags (with deduplication)
    if flags:
        if trip.status == "ACTIVE":
            trip.status = "ALERT"

        for flag in flags:
            existing_open = (
                db.query(Incident)
                .filter(
                    Incident.trip_id == trip.id,
                    Incident.incident_type == flag,
                    Incident.status.in_(["OPEN", "ACKNOWLEDGED"]),
                )
                .first()
            )

            if not existing_open:
                # Find corresponding explanation description from reasons
                desc = "; ".join(reasons) if reasons else f"ML detector flagged {flag}"
                severity = "HIGH" if flag in ("ROUTE_DEVIATION", "GPS_MISMATCH") else "MEDIUM"
                incident = Incident(
                    trip_id=trip.id,
                    incident_type=flag,
                    severity=severity,
                    description=desc,
                    status="OPEN",
                )
                db.add(incident)

    db.commit()

    return MLTripAnalysisOutput(
        trip_id=str(raw_result.get("trip_id", trip.id)),
        flags=flags,
        trust_score=trust_score,
        reasons=reasons,
        gps_status="OK" if gps_status == "OK" else "UNAVAILABLE",
    )

