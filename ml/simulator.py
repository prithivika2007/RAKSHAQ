"""
Rakshaq Commute Safety Prototype - Telemetry Simulator
======================================================
Simulates realistic night-shift commute trips in Chennai (Pallavaram to Sholinganallur).
Generates telemetry streams (lat, lng, speed, ts) sampled every 30 seconds.

Provides 4 test scenarios:
1. normal_trip(): Commute strictly on planned route.
2. deviation_trip(): Vehicle deviates ~800 m off-route for ~5.5 minutes.
3. stop_trip(): Vehicle stops mid-route for ~7 minutes outside pickup/dropoff zones.
4. gps_mismatch_trip(): Divergence between rider phone and driver device (~450 m).
"""

import math
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ml.config import SAMPLE_INTERVAL_SEC
    from ml.detectors import haversine_m
except ImportError:
    from config import SAMPLE_INTERVAL_SEC
    from detectors import haversine_m

# ---------------------------------------------------------------------------
# Planned Route: Pallavaram GST Road to Sholinganallur ELCOT SEZ (17 Waypoints)
# ---------------------------------------------------------------------------
CHENNAI_PLANNED_ROUTE = [
    [12.9680, 80.1500],  # 0: Pallavaram Railway Station / GST Rd (Pickup)
    [12.9602, 80.1618],  # 1: Chromepet Radial Rd Flyover
    [12.9568, 80.1735],  # 2: 200 Feet Radial Rd (near Vels)
    [12.9541, 80.1852],  # 3: Keelkattalai Signal
    [12.9469, 80.1973],  # 4: Kovilambakkam Radial Rd
    [12.9418, 80.2064],  # 5: Eachangadu Junction
    [12.9372, 80.2138],  # 6: Dr. Kamakshi Memorial Hospital
    [12.9331, 80.2209],  # 7: Narayanapuram Lake
    [12.9298, 80.2276],  # 8: Pallikaranai Junction
    [12.9234, 80.2268],  # 9: Pallikaranai Marshland View
    [12.9152, 80.2251],  # 10: Perumbakkam Junction
    [12.9085, 80.2294],  # 11: Medavakkam-Sholinganallur Link Rd
    [12.9038, 80.2335],  # 12: Global Health City (Hospital)
    [12.9018, 80.2405],  # 13: Perumbakkam Main Rd
    [12.9002, 80.2462],  # 14: Sholinganallur West
    [12.9010, 80.2520],  # 15: Sholinganallur OMR Junction
    [12.9060, 80.2510],  # 16: ELCOT SEZ Sholinganallur (Drop-off)
]


def _build_cumulative_distances(route: List[List[float]]) -> List[float]:
    """Calculate cumulative distance along planned route polyline in meters."""
    cum_dist = [0.0]
    for i in range(len(route) - 1):
        d = haversine_m(route[i][0], route[i][1], route[i + 1][0], route[i + 1][1])
        cum_dist.append(cum_dist[-1] + d)
    return cum_dist


def _interpolate_along_route(route: List[List[float]],
                            cum_dist: List[float],
                            target_dist: float) -> Tuple[float, float]:
    """Interpolate (lat, lng) at a given distance along the route polyline."""
    if target_dist <= 0.0:
        return route[0][0], route[0][1]
    if target_dist >= cum_dist[-1]:
        return route[-1][0], route[-1][1]

    for i in range(len(cum_dist) - 1):
        if cum_dist[i] <= target_dist <= cum_dist[i + 1]:
            seg_len = cum_dist[i + 1] - cum_dist[i]
            if seg_len <= 0:
                return route[i][0], route[i][1]
            frac = (target_dist - cum_dist[i]) / seg_len
            lat = route[i][0] + frac * (route[i + 1][0] - route[i][0])
            lng = route[i][1] + frac * (route[i + 1][1] - route[i][1])
            return lat, lng
    return route[-1][0], route[-1][1]


def _generate_base_trajectory(base_speed_kmh: float = 38.0,
                              start_time: int = 1710025200) -> List[Dict[str, Any]]:
    """
    Generate baseline telemetry points along CHENNAI_PLANNED_ROUTE.
    Points are produced every SAMPLE_INTERVAL_SEC (30s).
    """
    cum_dist = _build_cumulative_distances(CHENNAI_PLANNED_ROUTE)
    total_len = cum_dist[-1]

    # Speed in meters per second
    speed_mps = (base_speed_kmh * 1000.0) / 3600.0
    dist_per_step = speed_mps * SAMPLE_INTERVAL_SEC

    points = []
    current_dist = 0.0
    step = 0

    # Deterministic pseudo-random seed for repeatable hackathon demos
    rng = random.Random(42)

    while current_dist <= total_len:
        lat, lng = _interpolate_along_route(CHENNAI_PLANNED_ROUTE, cum_dist, current_dist)

        # Realistic small GPS jitter (~3-6 meters)
        jitter_lat = rng.gauss(0, 0.00003)
        jitter_lng = rng.gauss(0, 0.00003)

        speed_variation = base_speed_kmh + rng.uniform(-3.0, 3.0)

        points.append({
            "lat": round(lat + jitter_lat, 6),
            "lng": round(lng + jitter_lng, 6),
            "speed": round(max(10.0, speed_variation), 1),
            "ts": start_time + step * SAMPLE_INTERVAL_SEC,
        })

        if current_dist >= total_len:
            break

        current_dist += dist_per_step
        step += 1

    # Ensure last point arrives at destination
    last_lat, last_lng = CHENNAI_PLANNED_ROUTE[-1]
    points.append({
        "lat": round(last_lat, 6),
        "lng": round(last_lng, 6),
        "speed": 0.0,
        "ts": start_time + (step + 1) * SAMPLE_INTERVAL_SEC,
    })

    return points


def normal_trip() -> Dict[str, Any]:
    """
    Scenario 1: Normal commute.
    Vehicle stays on planned route from Pallavaram to ELCOT SEZ Sholinganallur.
    Driver and employee GPS streams remain closely aligned (< 15 m).
    """
    base_points = _generate_base_trajectory(base_speed_kmh=40.0)

    # Driver stream matches with independent small GPS noise
    rng = random.Random(101)
    driver_points = []
    for pt in base_points:
        driver_points.append({
            "lat": round(pt["lat"] + rng.gauss(0, 0.00003), 6),
            "lng": round(pt["lng"] + rng.gauss(0, 0.00003), 6),
            "speed": pt["speed"],
            "ts": pt["ts"],
        })

    return {
        "trip_id": "TRIP_NORMAL_CHENNAI",
        "planned_route": CHENNAI_PLANNED_ROUTE,
        "points": base_points,
        "driver_points": driver_points,
        "rider_feedback": None,
    }


def deviation_trip() -> Dict[str, Any]:
    """
    Scenario 2: Route Deviation commute.
    Mid-route (between points 16 and 26), the vehicle drifts ~800 m off-route
    into an unauthorized detour for ~5.5 minutes before returning to route.
    Driver is with the vehicle, so driver_points also deviates.
    """
    base_points = _generate_base_trajectory(base_speed_kmh=40.0)
    deviated_points = []
    driver_points = []
    rng = random.Random(202)

    # Lateral offset of ~800m (0.0072 deg latitude ≈ 800m)
    deviation_offset_lat = 0.0072
    deviation_offset_lng = 0.0035

    for i, pt in enumerate(base_points):
        lat = pt["lat"]
        lng = pt["lng"]
        speed = pt["speed"]
        ts = pt["ts"]

        # Deviate for 11 points (indices 16 to 26 inclusive = 330s = 5.5 min)
        if 16 <= i <= 26:
            # Smooth ramp in and out of detour
            factor = 1.0 if (18 <= i <= 24) else 0.75
            lat += deviation_offset_lat * factor
            lng += deviation_offset_lng * factor

        deviated_points.append({
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "speed": speed,
            "ts": ts,
        })

        # Driver is in same car, subject to slight GPS receiver noise
        driver_points.append({
            "lat": round(lat + rng.gauss(0, 0.00003), 6),
            "lng": round(lng + rng.gauss(0, 0.00003), 6),
            "speed": speed,
            "ts": ts,
        })

    return {
        "trip_id": "TRIP_DEVIATION_CHENNAI",
        "planned_route": CHENNAI_PLANNED_ROUTE,
        "points": deviated_points,
        "driver_points": driver_points,
        "rider_feedback": None,
    }


def stop_trip() -> Dict[str, Any]:
    """
    Scenario 3: Unexpected Stop commute.
    Vehicle halts mid-route (Narayanapuram / Pallikaranai area, away from pickup/dropoff)
    for 14 points (420 seconds = 7.0 minutes, > 5 min threshold).
    """
    base_points = _generate_base_trajectory(base_speed_kmh=40.0)
    stopped_points = []
    driver_points = []
    rng = random.Random(303)

    # Point index 16 is around Narayanapuram lake, > 6 km from start and > 7 km from end
    halt_index = 16
    halt_lat = base_points[halt_index]["lat"]
    halt_lng = base_points[halt_index]["lng"]
    halt_start_ts = base_points[halt_index]["ts"]

    # First segment: drive normally up to halt_index
    for i in range(halt_index):
        pt = base_points[i]
        stopped_points.append(pt)
        driver_points.append({
            "lat": round(pt["lat"] + rng.gauss(0, 0.00002), 6),
            "lng": round(pt["lng"] + rng.gauss(0, 0.00002), 6),
            "speed": pt["speed"],
            "ts": pt["ts"],
        })

    # Stationary segment: 14 points (7.0 minutes) at the same coordinates with speed = 0
    num_stop_points = 14
    for k in range(num_stop_points):
        stop_ts = halt_start_ts + k * SAMPLE_INTERVAL_SEC
        # Micro-jitter of stationary GPS
        s_lat = round(halt_lat + rng.gauss(0, 0.00001), 6)
        s_lng = round(halt_lng + rng.gauss(0, 0.00001), 6)

        stopped_points.append({
            "lat": s_lat,
            "lng": s_lng,
            "speed": 0.0,
            "ts": stop_ts,
        })
        driver_points.append({
            "lat": round(s_lat + rng.gauss(0, 0.00001), 6),
            "lng": round(s_lng + rng.gauss(0, 0.00001), 6),
            "speed": 0.0,
            "ts": stop_ts,
        })

    # Remaining segment: resume driving along route
    time_shift = (num_stop_points - 1) * SAMPLE_INTERVAL_SEC
    for i in range(halt_index + 1, len(base_points)):
        pt = base_points[i]
        new_ts = pt["ts"] + time_shift
        stopped_points.append({
            "lat": pt["lat"],
            "lng": pt["lng"],
            "speed": pt["speed"],
            "ts": new_ts,
        })
        driver_points.append({
            "lat": round(pt["lat"] + rng.gauss(0, 0.00002), 6),
            "lng": round(pt["lng"] + rng.gauss(0, 0.00002), 6),
            "speed": pt["speed"],
            "ts": new_ts,
        })

    return {
        "trip_id": "TRIP_STOP_CHENNAI",
        "planned_route": CHENNAI_PLANNED_ROUTE,
        "points": stopped_points,
        "driver_points": driver_points,
        "rider_feedback": None,
    }


def gps_mismatch_trip() -> Dict[str, Any]:
    """
    Scenario 4: GPS Mismatch commute.
    Employee phone moves along normal route, but driver device drifts ~450 m away
    for 10 consecutive points (5.0 minutes) due to phone separation / spoofing.
    """
    base_points = _generate_base_trajectory(base_speed_kmh=40.0)
    driver_points = []
    rng = random.Random(404)

    # 450 m offset in longitude (0.0042 deg ≈ 460 m)
    mismatch_offset_lng = 0.0042

    for i, pt in enumerate(base_points):
        ts = pt["ts"]
        d_lat = pt["lat"] + rng.gauss(0, 0.00002)
        d_lng = pt["lng"] + rng.gauss(0, 0.00002)

        # Mismatch between index 15 and 24 (10 points = 300 seconds)
        if 15 <= i <= 24:
            d_lng += mismatch_offset_lng

        driver_points.append({
            "lat": round(d_lat, 6),
            "lng": round(d_lng, 6),
            "speed": pt["speed"],
            "ts": ts,
        })

    return {
        "trip_id": "TRIP_GPS_MISMATCH_CHENNAI",
        "planned_route": CHENNAI_PLANNED_ROUTE,
        "points": base_points,
        "driver_points": driver_points,
        "rider_feedback": None,
    }
