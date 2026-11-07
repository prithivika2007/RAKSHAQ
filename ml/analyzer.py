"""
Rakshaq Commute Safety Prototype - Trip Analyzer
=================================================
Top-level entry point that processes trip telemetry data, executes
all anomaly detectors, computes the Driver Trust Score, and returns
a standardized, production-ready assessment.

Designed for robust fault tolerance: never crashes on missing or malformed inputs.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ml.detectors import (
        detect_route_deviation,
        detect_unexpected_stop,
        detect_gps_mismatch,
    )
    from ml.scoring import compute_trust_score
except ImportError:
    from detectors import (
        detect_route_deviation,
        detect_unexpected_stop,
        detect_gps_mismatch,
    )
    from scoring import compute_trust_score


def analyze_trip(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a commute trip for safety anomalies.

    Input format:
    {
        "trip_id": "T1",
        "planned_route": [[lat, lng], ...],
        "points": [{"lat": float, "lng": float, "speed": float, "ts": ...}],
        "driver_points": [{"lat": ..., "lng": ..., "ts": ...}],  # optional/empty
        "rider_feedback": null / int / dict / str                 # optional
    }

    Output format (EXACT):
    {
        "trip_id": "T1",
        "flags": ["ROUTE_DEVIATION"],
        "trust_score": 72,
        "reasons": ["..."],
        "gps_status": "OK"  # or "UNAVAILABLE"
    }

    Guaranteed not to crash on empty or missing fields.
    """
    if not isinstance(data, dict):
        data = {}

    trip_id = data.get("trip_id")
    if not trip_id:
        trip_id = "UNKNOWN_TRIP"

    planned_route = data.get("planned_route")
    if not isinstance(planned_route, list):
        planned_route = []

    points = data.get("points")
    if not isinstance(points, list):
        points = []

    driver_points = data.get("driver_points")
    if not isinstance(driver_points, list):
        driver_points = []

    rider_feedback = data.get("rider_feedback")

    # 1. Detect Route Deviation
    deviation_events = detect_route_deviation(points, planned_route)

    # 2. Detect Unexpected Stops
    stop_events = detect_unexpected_stop(points, planned_route)

    # 3. Detect GPS Mismatch between Employee and Driver devices
    mismatch_events, gps_status = detect_gps_mismatch(points, driver_points)

    # Aggregate all detected events
    all_events: List[Dict[str, Any]] = []
    all_events.extend(deviation_events)
    all_events.extend(stop_events)
    all_events.extend(mismatch_events)

    # Extract unique flags in order of occurrence
    flags: List[str] = []
    seen = set()
    for ev in all_events:
        ev_type = ev.get("type")
        if ev_type and ev_type not in seen:
            seen.add(ev_type)
            flags.append(ev_type)

    # Compute Driver Trust Score & generate human-readable explanations
    trust_score, reasons = compute_trust_score(all_events, rider_feedback=rider_feedback)

    # Exact expected response format
    return {
        "trip_id": str(trip_id),
        "flags": flags,
        "trust_score": trust_score,
        "reasons": reasons,
        "gps_status": gps_status,
    }
