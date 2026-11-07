"""
Rakshaq Commute Safety Prototype - Anomaly Detectors
=====================================================
Rule-based detection modules for:
1. Route Deviation: Sustained lateral drift from planned polyline segments.
2. Unexpected Stop: Extended stationary periods outside designated pickup/dropoff zones.
3. GPS Mismatch: Divergence between employee phone and cab/driver GPS streams.

Clean, explainable, and testable standalone functions.
"""

import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ml.config import (
        DEVIATION_DISTANCE_M,
        DEVIATION_MIN_CONSECUTIVE_POINTS,
        STOP_SPEED_KMH,
        STOP_DURATION_MIN,
        STOP_IGNORE_RADIUS_M,
        GPS_MISMATCH_DISTANCE_M,
        GPS_MISMATCH_MIN_CONSECUTIVE_POINTS,
    )
except ImportError:
    from config import (
        DEVIATION_DISTANCE_M,
        DEVIATION_MIN_CONSECUTIVE_POINTS,
        STOP_SPEED_KMH,
        STOP_DURATION_MIN,
        STOP_IGNORE_RADIUS_M,
        GPS_MISMATCH_DISTANCE_M,
        GPS_MISMATCH_MIN_CONSECUTIVE_POINTS,
    )


def format_ts(ts: Any) -> str:
    """
    Format a timestamp (epoch seconds, float, or ISO string) to readable 'HH:MM:SS'.
    Falls back gracefully to str(ts).
    """
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S")
        except Exception:
            return ts
    return str(ts)


def to_epoch_sec(ts: Any) -> float:
    """Convert timestamp (int, float, or ISO string) to epoch seconds."""
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            pass
    return 0.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth in meters.
    Uses the Haversine formula with mean Earth radius R = 6,371,000 meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return R * c


def point_to_segment_distance_m(p_lat: float, p_lng: float,
                                a_lat: float, a_lng: float,
                                b_lat: float, b_lng: float) -> float:
    """
    Compute shortest distance in meters from point P to line segment AB.
    Projects P orthogonally onto AB in local equirectangular meter space.
    Clamps projection factor t to [0, 1] to stay within the segment.
    """
    # Degenerate segment: start and end are identical
    if abs(a_lat - b_lat) < 1e-7 and abs(a_lng - b_lng) < 1e-7:
        return haversine_m(p_lat, p_lng, a_lat, a_lng)

    # Local meter scaling factors around segment midpoint
    mean_lat_rad = math.radians((a_lat + b_lat + p_lat) / 3.0)
    kx = 111320.0 * math.cos(mean_lat_rad)
    ky = 110574.0

    # Local coordinates relative to point A (0, 0)
    bx = (b_lng - a_lng) * kx
    by = (b_lat - a_lat) * ky
    px = (p_lng - a_lng) * kx
    py = (p_lat - a_lat) * ky

    # Projection parameter t = (P . B) / |B|^2
    b_len_sq = bx * bx + by * by
    if b_len_sq <= 0:
        return math.hypot(px, py)

    t = (px * bx + py * by) / b_len_sq
    t_clamped = max(0.0, min(1.0, t))

    # Closest point on segment
    proj_x = t_clamped * bx
    proj_y = t_clamped * by

    return math.hypot(px - proj_x, py - proj_y)


def min_distance_to_route_m(p_lat: float, p_lng: float, planned_route: List[List[float]]) -> float:
    """
    Compute minimum distance from point P to any segment along planned route polyline.
    """
    if not planned_route:
        return 0.0
    if len(planned_route) == 1:
        return haversine_m(p_lat, p_lng, planned_route[0][0], planned_route[0][1])

    min_dist = float("inf")
    for i in range(len(planned_route) - 1):
        a_lat, a_lng = planned_route[i]
        b_lat, b_lng = planned_route[i + 1]
        dist = point_to_segment_distance_m(p_lat, p_lng, a_lat, a_lng, b_lat, b_lng)
        if dist < min_dist:
            min_dist = dist
    return min_dist


def detect_route_deviation(points: List[Dict[str, Any]],
                           planned_route: List[List[float]]) -> List[Dict[str, Any]]:
    """
    Detect route deviation incidents.
    Measures shortest distance from each point to the planned route polyline.
    Flags an event only after N consecutive points exceed DEVIATION_DISTANCE_M
    to avoid false alarms from transient GPS spikes.

    Returns:
        List of event dicts: {"type": "ROUTE_DEVIATION", "ts": ..., "detail": "..."}
    """
    events: List[Dict[str, Any]] = []
    if not points or not planned_route:
        return events

    consecutive_deviant_points = 0
    max_distance_in_episode = 0.0
    episode_start_ts = None
    event_flagged = False

    for pt in points:
        lat = pt.get("lat")
        lng = pt.get("lng")
        ts = pt.get("ts")
        if lat is None or lng is None:
            continue

        dist = min_distance_to_route_m(lat, lng, planned_route)

        if dist > DEVIATION_DISTANCE_M:
            consecutive_deviant_points += 1
            if consecutive_deviant_points == 1:
                episode_start_ts = ts
                max_distance_in_episode = dist
            else:
                max_distance_in_episode = max(max_distance_in_episode, dist)

            # Trigger event when consecutive threshold is reached
            if consecutive_deviant_points == DEVIATION_MIN_CONSECUTIVE_POINTS and not event_flagged:
                event_flagged = True
                event = {
                    "type": "ROUTE_DEVIATION",
                    "ts": episode_start_ts,
                    "distance_m": round(max_distance_in_episode, 1),
                    "detail": f"Deviated {int(round(max_distance_in_episode))} m from planned route at {format_ts(episode_start_ts)}",
                }
                events.append(event)
            elif consecutive_deviant_points > DEVIATION_MIN_CONSECUTIVE_POINTS and event_flagged:
                # Update peak distance in active event detail
                events[-1]["distance_m"] = round(max_distance_in_episode, 1)
                events[-1]["detail"] = f"Deviated {int(round(max_distance_in_episode))} m from planned route at {format_ts(episode_start_ts)}"
        else:
            # Rejoined route - reset episode tracker
            consecutive_deviant_points = 0
            max_distance_in_episode = 0.0
            episode_start_ts = None
            event_flagged = False

    return events


def detect_unexpected_stop(points: List[Dict[str, Any]],
                           planned_route: List[List[float]]) -> List[Dict[str, Any]]:
    """
    Detect unexpected stationary stops along the commute.
    Flags an event if vehicle speed stays below STOP_SPEED_KMH for longer than
    STOP_DURATION_MIN, ignoring stops within STOP_IGNORE_RADIUS_M of planned
    pickup (start) or drop-off (destination) points.

    Returns:
        List of event dicts: {"type": "UNEXPECTED_STOP", "ts": ..., "detail": "..."}
    """
    events: List[Dict[str, Any]] = []
    if not points or not planned_route:
        return events

    pickup = planned_route[0]
    dropoff = planned_route[-1]
    stop_duration_sec_threshold = STOP_DURATION_MIN * 60.0

    in_stop_state = False
    stop_start_ts = None
    stop_start_epoch = 0.0
    event_flagged = False

    for pt in points:
        lat = pt.get("lat")
        lng = pt.get("lng")
        speed = pt.get("speed", 0.0)
        ts = pt.get("ts")
        if lat is None or lng is None:
            continue

        epoch_sec = to_epoch_sec(ts)

        # Check if point is in legitimate pickup or dropoff zone
        d_pickup = haversine_m(lat, lng, pickup[0], pickup[1])
        d_dropoff = haversine_m(lat, lng, dropoff[0], dropoff[1])
        near_pickup_or_drop = (d_pickup <= STOP_IGNORE_RADIUS_M or d_dropoff <= STOP_IGNORE_RADIUS_M)

        if speed <= STOP_SPEED_KMH and not near_pickup_or_drop:
            if not in_stop_state:
                in_stop_state = True
                stop_start_ts = ts
                stop_start_epoch = epoch_sec
                event_flagged = False
            else:
                elapsed_sec = epoch_sec - stop_start_epoch
                if elapsed_sec >= stop_duration_sec_threshold and not event_flagged:
                    event_flagged = True
                    duration_min = round(elapsed_sec / 60.0, 1)
                    event = {
                        "type": "UNEXPECTED_STOP",
                        "ts": stop_start_ts,
                        "duration_min": duration_min,
                        "detail": f"Unexpected stop of {duration_min} min mid-route at {format_ts(stop_start_ts)}",
                    }
                    events.append(event)
                elif event_flagged:
                    # Update active event duration
                    duration_min = round(elapsed_sec / 60.0, 1)
                    events[-1]["duration_min"] = duration_min
                    events[-1]["detail"] = f"Unexpected stop of {duration_min} min mid-route at {format_ts(stop_start_ts)}"
        else:
            # Vehicle moving or within legitimate pickup/drop zone
            in_stop_state = False
            stop_start_ts = None
            stop_start_epoch = 0.0
            event_flagged = False

    return events


def detect_gps_mismatch(points: List[Dict[str, Any]],
                        driver_points: Optional[List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Detect divergence between employee phone GPS and driver/vehicle GPS.
    If driver_points is empty or None, returns status 'UNAVAILABLE' without raising an alarm
    (never treat missing data as danger).
    Otherwise compares timestamp-aligned points and flags sustained separation gaps.

    Returns:
        (events, status) where status is 'OK' or 'UNAVAILABLE'
        events: List of event dicts: {"type": "GPS_MISMATCH", "ts": ..., "detail": "..."}
    """
    if not driver_points or len(driver_points) == 0:
        return [], "UNAVAILABLE"

    events: List[Dict[str, Any]] = []

    # Build fast timestamp index for driver points
    # Index by integer/epoch timestamp or string key
    driver_by_ts = {dp.get("ts"): dp for dp in driver_points if "ts" in dp}

    consecutive_mismatches = 0
    max_mismatch_dist = 0.0
    episode_start_ts = None
    event_flagged = False

    for pt in points:
        pt_ts = pt.get("ts")
        dp = driver_by_ts.get(pt_ts)

        # If exact match not found, check closest timestamp within 30s
        if dp is None and isinstance(pt_ts, (int, float)):
            for d in driver_points:
                d_ts = d.get("ts")
                if isinstance(d_ts, (int, float)) and abs(d_ts - pt_ts) <= 15:
                    dp = d
                    break

        if dp is None or pt.get("lat") is None or dp.get("lat") is None:
            continue

        dist = haversine_m(pt["lat"], pt["lng"], dp["lat"], dp["lng"])

        if dist > GPS_MISMATCH_DISTANCE_M:
            consecutive_mismatches += 1
            if consecutive_mismatches == 1:
                episode_start_ts = pt_ts
                max_mismatch_dist = dist
            else:
                max_mismatch_dist = max(max_mismatch_dist, dist)

            if consecutive_mismatches == GPS_MISMATCH_MIN_CONSECUTIVE_POINTS and not event_flagged:
                event_flagged = True
                event = {
                    "type": "GPS_MISMATCH",
                    "ts": episode_start_ts,
                    "distance_m": round(max_mismatch_dist, 1),
                    "detail": f"GPS mismatch of {int(round(max_mismatch_dist))} m between rider and driver at {format_ts(episode_start_ts)}",
                }
                events.append(event)
            elif consecutive_mismatches > GPS_MISMATCH_MIN_CONSECUTIVE_POINTS and event_flagged:
                events[-1]["distance_m"] = round(max_mismatch_dist, 1)
                events[-1]["detail"] = f"GPS mismatch of {int(round(max_mismatch_dist))} m between rider and driver at {format_ts(episode_start_ts)}"
        else:
            consecutive_mismatches = 0
            max_mismatch_dist = 0.0
            episode_start_ts = None
            event_flagged = False

    return events, "OK"
