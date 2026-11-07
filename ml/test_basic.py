"""
Rakshaq Commute Safety Prototype - Basic Test Suite
===================================================
Simple unit tests using plain assert statements to verify:
1. Normal commute produces no flags and trust score >= 100.
2. Route deviation produces 'ROUTE_DEVIATION' flag and score penalty.
3. Unexpected stop produces 'UNEXPECTED_STOP' flag and score penalty.
4. GPS mismatch produces 'GPS_MISMATCH' flag and score penalty.
5. Empty driver_points produces gps_status 'UNAVAILABLE' without false alarm.
6. Malformed and empty inputs never crash analyzer.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ml.detectors import haversine_m
    from ml.analyzer import analyze_trip
    from ml.simulator import (
        normal_trip,
        deviation_trip,
        stop_trip,
        gps_mismatch_trip,
        CHENNAI_PLANNED_ROUTE,
    )
except ImportError:
    from detectors import haversine_m
    from analyzer import analyze_trip
    from simulator import (
        normal_trip,
        deviation_trip,
        stop_trip,
        gps_mismatch_trip,
        CHENNAI_PLANNED_ROUTE,
    )


def test_haversine():
    """Verify great-circle distance calculation."""
    # Distance between same points should be 0
    assert haversine_m(12.9680, 80.1500, 12.9680, 80.1500) == 0.0

    # Distance between Pallavaram (12.9680, 80.1500) and Chromepet (12.9602, 80.1618) is ~1.5 km
    dist = haversine_m(12.9680, 80.1500, 12.9602, 80.1618)
    assert 1300 < dist < 1700, f"Expected ~1.5km, got {dist}m"
    print("✓ test_haversine passed")


def test_normal_trip():
    """Verify normal commute produces no flags, clean trip bonus, and score >= 100."""
    trip = normal_trip()
    result = analyze_trip(trip)

    assert result["trip_id"] == "TRIP_NORMAL_CHENNAI"
    assert result["flags"] == [], f"Expected no flags, got {result['flags']}"
    assert result["trust_score"] >= 100, f"Expected score >= 100, got {result['trust_score']}"
    assert result["gps_status"] == "OK"
    assert len(result["reasons"]) > 0
    print("✓ test_normal_trip passed (no flags, score >= 100)")


def test_deviation_trip():
    """Verify route deviation is flagged and penalizes trust score."""
    trip = deviation_trip()
    result = analyze_trip(trip)

    assert "ROUTE_DEVIATION" in result["flags"], f"Expected ROUTE_DEVIATION, got {result['flags']}"
    assert result["trust_score"] < 100, f"Expected score < 100, got {result['trust_score']}"
    assert any("Deviated" in r for r in result["reasons"])
    print("✓ test_deviation_trip passed (flags ROUTE_DEVIATION)")


def test_stop_trip():
    """Verify unexpected stop mid-route is flagged."""
    trip = stop_trip()
    result = analyze_trip(trip)

    assert "UNEXPECTED_STOP" in result["flags"], f"Expected UNEXPECTED_STOP, got {result['flags']}"
    assert result["trust_score"] < 100, f"Expected score < 100, got {result['trust_score']}"
    assert any("Unexpected stop" in r for r in result["reasons"])
    print("✓ test_stop_trip passed (flags UNEXPECTED_STOP)")


def test_gps_mismatch_trip():
    """Verify separation between rider and driver devices is flagged."""
    trip = gps_mismatch_trip()
    result = analyze_trip(trip)

    assert "GPS_MISMATCH" in result["flags"], f"Expected GPS_MISMATCH, got {result['flags']}"
    assert result["trust_score"] < 100, f"Expected score < 100, got {result['trust_score']}"
    assert result["gps_status"] == "OK"
    assert any("mismatch" in r.lower() for r in result["reasons"])
    print("✓ test_gps_mismatch_trip passed (flags GPS_MISMATCH)")


def test_empty_driver_points():
    """Verify missing driver GPS data gives UNAVAILABLE status without false danger."""
    trip = normal_trip()
    trip["driver_points"] = []
    result = analyze_trip(trip)

    assert result["gps_status"] == "UNAVAILABLE"
    assert "GPS_MISMATCH" not in result["flags"]
    assert result["trust_score"] >= 100
    print("✓ test_empty_driver_points passed (gps_status UNAVAILABLE, no false alarm)")


def test_robustness_empty_and_none_input():
    """Verify analyze_trip handles empty or None input gracefully without crashing."""
    res_empty = analyze_trip({})
    assert isinstance(res_empty, dict)
    assert res_empty["trip_id"] == "UNKNOWN_TRIP"
    assert res_empty["flags"] == []
    assert res_empty["gps_status"] == "UNAVAILABLE"

    res_none = analyze_trip(None)
    assert isinstance(res_none, dict)
    assert res_none["trip_id"] == "UNKNOWN_TRIP"
    assert res_none["flags"] == []
    assert res_none["gps_status"] == "UNAVAILABLE"
    print("✓ test_robustness_empty_and_none_input passed (no crashes)")


def test_bad_rider_feedback():
    """Verify negative rider feedback is penalized."""
    trip = normal_trip()
    trip["rider_feedback"] = {"rating": 1, "comment": "Unsafe driving"}
    result = analyze_trip(trip)

    assert result["trust_score"] < 100
    assert any("Unsafe driving" in r or "rating" in r.lower() for r in result["reasons"])
    print("✓ test_bad_rider_feedback passed (penalizes low rating)")


def run_all_tests():
    print("=" * 60)
    print(" RUNNING RAKSHAQ BASIC TEST SUITE")
    print("=" * 60)
    test_haversine()
    test_normal_trip()
    test_deviation_trip()
    test_stop_trip()
    test_gps_mismatch_trip()
    test_empty_driver_points()
    test_robustness_empty_and_none_input()
    test_bad_rider_feedback()
    print("=" * 60)
    print(" ALL TESTS PASSED SUCCESSFULLY! ")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
