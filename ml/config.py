"""
Rakshaq Commute Safety Prototype - Configuration & Thresholds
==============================================================
Central configuration for rule-based commute anomaly detection
and Driver Trust Score calculation.

Designed for a hackathon prototype: clean, explainable, and tunable.
"""

# ==========================================
# 1. Route Deviation Thresholds
# ==========================================
# Maximum allowable distance (in meters) from planned route segment
DEVIATION_DISTANCE_M = 300

# Minimum consecutive points exceeding DEVIATION_DISTANCE_M to confirm a deviation
# (Filters out transient GPS jitter or multi-path reflections)
DEVIATION_MIN_CONSECUTIVE_POINTS = 3


# ==========================================
# 2. Unexpected Stop Thresholds
# ==========================================
# Maximum speed (in km/h) below which the vehicle is considered stationary
STOP_SPEED_KMH = 3

# Duration (in minutes) of stationary state required to trigger an unexpected stop alert
STOP_DURATION_MIN = 5

# Radius (in meters) around planned pickup and drop-off points where stops are expected
# (e.g. waiting for employee at pickup or finishing commute at destination)
STOP_IGNORE_RADIUS_M = 150


# ==========================================
# 3. GPS Mismatch (Rider vs Driver) Thresholds
# ==========================================
# Maximum allowable separation (in meters) between employee phone and driver device
GPS_MISMATCH_DISTANCE_M = 200

# Minimum consecutive points exceeding GPS_MISMATCH_DISTANCE_M to flag mismatch
GPS_MISMATCH_MIN_CONSECUTIVE_POINTS = 3


# ==========================================
# 4. Sampling & Simulation Parameters
# ==========================================
# Expected interval (in seconds) between successive GPS pings
SAMPLE_INTERVAL_SEC = 30


# ==========================================
# 5. Driver Trust Score Weights & Limits
# ==========================================
INITIAL_TRUST_SCORE = 100
MIN_TRUST_SCORE = 0
MAX_TRUST_SCORE = 100

# Penalty and bonus point adjustments
WEIGHTS = {
    "ROUTE_DEVIATION": -15,
    "UNEXPECTED_STOP": -10,
    "GPS_MISMATCH": -20,
    "BAD_RIDER_FEEDBACK": -10,
    "CLEAN_TRIP_BONUS": 2,
}

# Maximum penalty occurrences applied per event type per trip
# Prevents a single extended noisy incident from completely zeroing the score
MAX_PENALTIES_PER_EVENT_TYPE = 2

