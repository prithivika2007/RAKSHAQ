"""
Rakshaq Commute Safety Prototype - Demonstration Script
========================================================
Runs 4 simulated night-shift commute scenarios through analyze_trip()
and prints the resulting safety assessments as formatted JSON.

Scenarios:
1. Normal Trip (On-route, verified GPS stream)
2. Route Deviation Trip (~800 m detour into unauthorized area)
3. Unexpected Stop Trip (~7 min stationary mid-route)
4. GPS Mismatch Trip (Rider phone & driver device diverge by ~450 m)
5. Bonus Edge Case: Trip with missing driver GPS (UNAVAILABLE status)
"""

import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ml.analyzer import analyze_trip
    from ml.simulator import (
        normal_trip,
        deviation_trip,
        stop_trip,
        gps_mismatch_trip,
    )
except ImportError:
    from analyzer import analyze_trip
    from simulator import (
        normal_trip,
        deviation_trip,
        stop_trip,
        gps_mismatch_trip,
    )


def run_demo():
    print("=" * 70)
    print(" RAKSHAQ - NIGHT-SHIFT COMMUTE SAFETY PROTOTYPE (ML MODULE DEMO)")
    print(" Rule-based, explainable AI for women's commute verification")
    print("=" * 70)

    trips = [
        ("SCENARIO 1: NORMAL COMMUTE (Follows Planned Route)", normal_trip()),
        ("SCENARIO 2: ROUTE DEVIATION (Unauthorized Detour ~800m)", deviation_trip()),
        ("SCENARIO 3: UNEXPECTED STOP (~7 Min Mid-route Halt)", stop_trip()),
        ("SCENARIO 4: GPS MISMATCH (Rider and Driver Devices Separate)", gps_mismatch_trip()),
    ]

    for title, trip_data in trips:
        print("\n" + "-" * 70)
        print(f" {title}")
        print("-" * 70)
        result = analyze_trip(trip_data)
        print(json.dumps(result, indent=2))

    # Edge Case Demonstration: Missing Driver Telemetry
    print("\n" + "-" * 70)
    print(" BONUS CASE: MISSING DRIVER GPS (Status UNAVAILABLE, No False Alert)")
    print("-" * 70)
    missing_gps_trip = normal_trip()
    missing_gps_trip["trip_id"] = "TRIP_MISSING_DRIVER_GPS"
    missing_gps_trip["driver_points"] = []
    result_missing = analyze_trip(missing_gps_trip)
    print(json.dumps(result_missing, indent=2))

    print("\n" + "=" * 70)
    print(" DEMO COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
