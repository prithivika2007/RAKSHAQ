# Rakshaq — Commute Safety AI/ML Module

> **Hackathon Prototype**: Transparent, rule-based, and explainable safety intelligence for women's night-shift commutes.

---

## 📌 Overview

**Rakshaq** safeguards late-night commutes by monitoring real-time telemetry against planned routes. Rather than relying on opaque black-box machine learning models that can hallucinate or fail unpredictably, this module uses **deterministic, explainable physics- and geometry-based rules**.

Every anomaly detected produces human-readable, auditable evidence and feeds into a **Driver Trust Score**.

---

## 📁 File Structure

```text
ml/
├── config.py          # Centralized thresholds and scoring weights
├── detectors.py       # Rule-based anomaly detectors (deviation, stop, GPS mismatch)
├── scoring.py         # Driver Trust Score calculation & explanation engine
├── analyzer.py        # Main API wrapper (analyze_trip) with strict schema output
├── simulator.py       # Realistic Chennai night-shift commute generator (Pallavaram to Sholinganallur)
├── demo.py            # Runs 4 simulated trips + edge cases and prints pretty JSON
├── test_basic.py      # Standalone unit tests with plain assert statements
├── requirements.txt   # Dependencies (numpy, pandas)
└── README.md          # Usage guide and architecture documentation
```

---

## ⚙️ How It Works

### 1. Route Deviation (`detect_route_deviation`)
- Calculates the orthogonal distance in meters from each GPS ping to the nearest segment of the planned polyline using local equirectangular projection and Haversine distance.
- **Threshold**: Exceeds `DEVIATION_DISTANCE_M` (300 m).
- **Debounce**: Flags an event only after **3 consecutive pings** beyond threshold to avoid false alarms from transient GPS multipath reflection or antenna jitter.

### 2. Unexpected Stops (`detect_unexpected_stop`)
- Monitors vehicle speed. A speed $\le$ `STOP_SPEED_KMH` (3 km/h) indicates a stationary vehicle.
- **Exclusion Zone**: Stops within `STOP_IGNORE_RADIUS_M` (150 m) of the pickup point (start) or drop-off point (destination) are expected waiting periods and are ignored.
- **Threshold**: Flags an event if stationary mid-route for $\ge$ `STOP_DURATION_MIN` (5 minutes).

### 3. Dual-Stream GPS Mismatch (`detect_gps_mismatch`)
- Compares timestamp-aligned telemetry from the **employee's phone** and the **driver/cab device**.
- If driver device stream is empty, returns `gps_status: "UNAVAILABLE"` without raising an alarm (*missing data is never treated as danger*).
- If driver stream is active, flags sustained separation $> 200\text{ m}$ for $\ge 3$ consecutive pings.

### 4. Driver Trust Score & Explainability (`compute_trust_score`)
- Starts at a baseline of **100**.
- **Weights**:
  - `ROUTE_DEVIATION`: **-15 pts**
  - `UNEXPECTED_STOP`: **-10 pts**
  - `GPS_MISMATCH`: **-20 pts**
  - `BAD_RIDER_FEEDBACK`: **-10 pts**
  - `CLEAN_TRIP_BONUS`: **+2 pts**
- **Score Protection**: Repeated penalties of the same type within a single commute are capped (maximum 2 per event type) so noisy data streams cannot zero out a driver's score.
- **Capped**: Final score is clamped strictly between **0 and 100**.
- **Evidence**: Generates human-readable explanations with exact distance and time stamps (e.g., `"Deviated 884 m from planned route at 23:08:00 (-15 pts)"`).

---

## 🚀 Getting Started

### 1. Installation

Ensure you have Python 3.9+ installed. Activate your virtual environment and install the dependencies:

```bash
# From the RAKSHAQ directory
pip install -r ml/requirements.txt
```

### 2. Run the Demo

Executes 4 simulated Chennai commute trips (Normal, Deviation, Stop, GPS Mismatch) plus the missing driver telemetry edge case:

```bash
python -m ml.demo
```

### 3. Run the Tests

Runs the validation test suite using plain assertions:

```bash
python -m ml.test_basic
```

---

## 🔌 API Contract: `analyze_trip(data)`

### Input Format
```json
{
  "trip_id": "TRIP_001",
  "planned_route": [
    [12.9680, 80.1500],
    [12.9602, 80.1618]
  ],
  "points": [
    {
      "lat": 12.9680,
      "lng": 80.1500,
      "speed": 35.0,
      "ts": 1710025200
    }
  ],
  "driver_points": [
    {
      "lat": 12.9680,
      "lng": 80.1500,
      "ts": 1710025200
    }
  ],
  "rider_feedback": null
}
```

### Output Format (Guaranteed)
```json
{
  "trip_id": "TRIP_001",
  "flags": [
    "ROUTE_DEVIATION"
  ],
  "trust_score": 85,
  "reasons": [
    "Deviated 884 m from planned route at 23:08:00 (-15 pts)"
  ],
  "gps_status": "OK"
}
```

*Note: `analyze_trip` is completely defensive and will never crash on `None`, empty dictionaries, or missing keys.*

