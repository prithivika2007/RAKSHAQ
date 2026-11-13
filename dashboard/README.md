# RAKSHAQ &bull; Women's Night-Shift Commute Safety Dashboard

**RAKSHAQ** is an intelligent commute-monitoring and threat-detection dashboard designed for corporate 24/7 security dispatchers overseeing women's night-shift cab trips in Chennai (Pallavaram &rarr; Radial Road &rarr; Sholinganallur ELCOT SEZ).

Built with **React**, **Vite**, **react-leaflet**, and **plain CSS**.

---

## Key Features

1. **Live Corridor Map (`react-leaflet`)**:
   - **Planned Route (Blue)**: Polyline representing the scheduled corridor from Pallavaram Railway Station along 200 Feet Radial Road to ELCOT SEZ Sholinganallur.
   - **Employee Trail (Green)**: Real-time telemetry streamed from the employee's mobile device.
   - **Driver Trail (Orange)**: Hardware cab GPS telemetry for dual-stream discrepancy verification.
   - **Last Known Position**: Pulsing radar marker with speed and coordinates only when stored GPS telemetry exists.
   - **Incident Markers (Red)**: Beacons for active threats with one-click map popups to inspect and resolve.
   - Centered on Chennai corridor with custom dark-palette tiles.

2. **Trip Monitor**:
   - Selectable active, alerting, scheduled, completed, and cancelled trip details.
   - Commute status, pickup and destination points, and the associated employee and driver records.
   - Live heartbeat age counters for both employee and driver streams.
   - Last successful safety check-in timestamp; normal and duress PINs remain indistinguishable in dashboard status.
   - **60-Second Stale Heartbeat Detection**: When telemetry is lost or delayed for &ge; 60 seconds, the card dynamically transitions to a high-visibility crimson alert state with pulsing warnings.

3. **Operations Summary & Roster**:
   - Live counts for employees, drivers, active trips, scheduled trips, recent completed trips, and open incidents.
   - Expandable employee and driver records with PIN setup readiness, trust scores, and night-duty eligibility.
   - Employee verification is performed during login and is not stored as a persistent status; the dashboard does not claim that a user is currently authenticated.

4. **Driver Trust & Integrity Card**:
   - **Circular Trust Score Gauge (0–100)**: Visual dial reflecting rule-based ML deductions.
   - **Threat Flags**: Visual chips for `ROUTE_DEVIATION`, `UNEXPECTED_STOP`, `GPS_MISMATCH`.
   - **Evidence & Explainability**: Point-by-point reasons logged by the ML analyzer (e.g. detour distance, stop duration).
   - **GPS Stream Status**: Displays `"GPS stream unavailable"` in **neutral grey** (not red) when `gps_status` is `UNAVAILABLE`, avoiding false panic.
   - **Restrict Night Duty Button**: Saves night-shift eligibility changes through the backend.

5. **Alert List & Incident Timeline**:
   - Chronological incident feed, ordered **newest first**.
   - Color-coded severity badges (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
   - Status indicators (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `FALSE_ALARM`).
   - One-click **Acknowledge** and **Resolve** triage buttons calling `PATCH /incidents/{id}`.

6. **Telemetry Auto-Refresh**:
   - Automatic polling every **3 seconds** (`setInterval`).
   - Pause/Resume controls and manual refresh button.

7. **Scenario Switcher & Interactive Simulation**:
   - Header dropdown switcher (`Navbar`) to instantly swap commute scenarios:
     - **Normal**: Compliant commute along 200 Feet Radial Road (`locations_normal.json`, trust score: 100, no threat flags).
     - **Deviation**: ~884 m off-route detour into unlit bypass corridor (`locations_deviation.json`, score: 85, `ROUTE_DEVIATION` alert).
     - **Stop**: Stationary 6.5 min mid-route halt at Narayanapuram Lake (`locations_stop.json`, score: 90, `UNEXPECTED_STOP` alert).
     - **Duress**: Silent duress emergency triggered on employee device (`analysis_duress.json`, score: 45, `DURESS_PIN` critical alert).
     - **Missed check-in**: Scheduled 15-minute check-in unanswered (`analysis_missed_checkin.json`, score: 80, `MISSED_CHECKIN` alert).
     - **Phone shutdown**: Telemetry stream halts and stops advancing heartbeats, causing the Active Trip Card to turn alarming red when age exceeds 60s.
   - Replays 1 GPS point per poll (every 3 seconds).
   - Test toggle for missing cab hardware GPS stream (`analysis_unavailable.json`, `gps_status: "UNAVAILABLE"` in neutral grey).

---

## Directory Structure

```
dashboard/
├── index.html               # HTML entry point with Leaflet & typography
├── package.json             # React, Vite, react-leaflet dependencies
├── vite.config.js           # Vite dev and build configuration
├── .env                     # Environment variables (VITE_USE_MOCK=false)
├── .env.example             # Template for environment configuration
├── src/
│   ├── main.jsx             # React entry point & Leaflet CSS
│   ├── App.jsx              # Main dashboard view with 3s polling
│   ├── App.css              # Plain CSS styling (dark operations theme)
│   ├── api.js               # Data layer for all REST endpoints and replay
│   ├── components/
│   │   ├── Navbar.jsx           # Header with live indicator & poll controls
│   │   ├── OperationsOverview.jsx # Live summary, trip selection, and roster
│   │   ├── ReplayControlBar.jsx # Interactive scenario bar
│   │   ├── ActiveTripCard.jsx   # Trip details & 60s stale heartbeat alert
│   │   ├── DriverTrustCard.jsx  # Trust score gauge, ML flags, grey GPS badge
│   │   ├── LiveMap.jsx          # Leaflet map with multi-stream polylines
│   │   └── AlertsTimeline.jsx   # Incident list with Acknowledge/Resolve
│   ├── mock/
│   │   ├── trip.json                   # Active trip schema (id: 1, Pallavaram -> ELCOT)
│   │   ├── locations_normal.json       # Normal route telemetry
│   │   ├── locations_deviation.json    # Route detour telemetry
│   │   ├── locations_stop.json         # Mid-route halt telemetry
│   │   ├── locations_unavailable.json  # Telemetry without driver GPS stream
│   │   ├── analysis_normal.json        # ML output (score: 100, clean)
│   │   ├── analysis_deviation.json     # ML output (score: 85, ROUTE_DEVIATION)
│   │   ├── analysis_stop.json          # ML output (score: 90, UNEXPECTED_STOP)
│   │   ├── analysis_duress.json        # ML output (score: 45, DURESS_PIN)
│   │   ├── analysis_missed_checkin.json# ML output (score: 80, MISSED_CHECKIN)
│   │   ├── analysis_unavailable.json   # ML output (gps_status: "UNAVAILABLE")
│   │   └── incidents.json              # OPEN incidents (DEVIATION, STOP, DURESS, MISSED)
│   └── utils/
│       ├── formatters.js        # Relative time & severity styling
│       └── mapIcons.js          # Crisp SVG DivIcons for Leaflet
└── README.md
```

---

## Quickstart & Run Instructions

### 1. Install Dependencies
From the repository root:
```bash
cd dashboard
npm install
```

### 2. Run in Live Mode (Default)
The dashboard is preconfigured with `VITE_USE_MOCK=false` in `.env` and
connects to the FastAPI backend at `http://localhost:8000`:
```bash
npm run dev
```
Open your browser at `http://localhost:5173`.

The employee portal's **Preview Dashboard** button opens
`http://127.0.0.1:5173/index.html?mode=preview`. The `mode=preview` query
forces local demo/replay data even when `.env` is configured with
`VITE_USE_MOCK=false`; preview controls only update in-memory demo state and do
not send requests to the FastAPI backend. Start this dashboard server before
clicking the portal button.

### 3. Start the live FastAPI backend
1. Start the FastAPI backend from the `backend/` directory:
   ```bash
   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
2. Start/restart the dashboard:
   ```bash
   npm run dev -- --host 127.0.0.1 --port 5173
   ```
3. In LIVE mode:
   - The header displays a green `LIVE` badge.
   - The scenario dropdown and mock replay bar are automatically hidden.
   - API errors are shown in a banner; failed requests are not replaced with mock responses.
   - The summary, employee/driver roster, trip lifecycle, incidents, and telemetry are loaded from backend records.

Set `VITE_USE_MOCK=true` in `.env` only when intentionally using the isolated
replay/demo fixtures.

### 4. Build for Production
To generate an optimized production bundle:
```bash
npm run build
```
To preview the production build locally:
```bash
npm run preview
```

### 5. Backend integration tests
From the repository root, install the backend and test dependencies and run the route suite:
```bash
cd backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pytest tests -q
```

---

## Data Layer API Reference (`src/api.js`)

| Function | Endpoint | Description |
|---|---|---|
| `getTrips()` | `GET /trips?limit=500` | Retrieves recent trips across lifecycle states for summary and detail selection |
| `getEmployees()` | `GET /employees` | Retrieves registered employee records and whether both safety PINs are configured |
| `getDrivers()` | `GET /drivers` | Retrieves driver profiles, trust scores, and night-duty eligibility |
| `getTripLocations(tripId)` | `GET /trips/{id}/locations` | Fetches chronological GPS breadcrumbs for rider and cab streams |
| `getIncidents()` | `GET /incidents` | Fetches incidents, newest first |
| `getTripAnalysis(tripId)` | `GET /trips/{id}/analysis` | Fetches ML safety output: `{flags, trust_score, reasons, gps_status}` |
| `updateIncident(id, data)` | `PATCH /incidents/{id}` | Updates incident status (`ACKNOWLEDGED`, `RESOLVED`, `FALSE_ALARM`) |
| `updateDriver(id, data)` | `PATCH /drivers/{id}` | Updates night-duty eligibility or driver profile fields |

---

## Demo Walkthrough Guide

1. **Initial State (Steps 0–15)**:
   - Vehicle proceeds along 200 Feet Radial Road.
   - Dual GPS streams (green employee and orange driver trails) stay tightly aligned.
   - Trust score remains at **98–100** ("Verified Safe").
2. **Route Deviation Trigger (Step 16)**:
   - Click **"2. Route Deviation"** on the replay bar.
   - Vehicle diverges ~884 m off the blue planned corridor towards unlit marshland.
   - ML flags `ROUTE_DEVIATION`, trust score drops to **74**, and a **HIGH severity** incident appears on the timeline and map.
3. **Duress Alert Trigger (Step 22)**:
   - Click **"3. Duress Alert (SOS)"**.
   - An emergency `DURESS_PIN` **CRITICAL** incident is raised.
   - Trust score drops to **42** ("Critical Risk").
4. **Heartbeat Timeout Test**:
   - Click **"Test: 60s Heartbeat Timeout"**.
   - The Active Trip Card immediately turns alarming crimson with an emergency banner warning of signal disconnection.
5. **GPS Unavailable Test**:
   - Click **"Test: GPS Unavailable"**.
   - Observe the Driver Trust Card displaying **"GPS stream unavailable"** in neutral **grey** (not red).
6. **Incident Resolution**:
   - Click **"Acknowledge"** on an incident to claim ownership, then click **"Resolve"** to mark the threat closed.
