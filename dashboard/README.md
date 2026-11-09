# RAKSHAQ &bull; Women's Night-Shift Commute Safety Dashboard

**RAKSHAQ** is an intelligent commute-monitoring and threat-detection dashboard designed for corporate 24/7 security dispatchers overseeing women's night-shift cab trips in Chennai (Pallavaram &rarr; Radial Road &rarr; Sholinganallur ELCOT SEZ).

Built with **React**, **Vite**, **react-leaflet**, and **plain CSS**.

---

## Key Features

1. **Live Corridor Map (`react-leaflet`)**:
   - **Planned Route (Blue)**: Polyline representing the scheduled corridor from Pallavaram Railway Station along 200 Feet Radial Road to ELCOT SEZ Sholinganallur.
   - **Employee Trail (Green)**: Real-time telemetry streamed from the employee's mobile device.
   - **Driver Trail (Orange)**: Hardware cab GPS telemetry for dual-stream discrepancy verification.
   - **Last Known Position**: Pulsing radar marker with live vehicle speed and coordinates.
   - **Incident Markers (Red)**: Beacons for active threats with one-click map popups to inspect and resolve.
   - Centered on Chennai corridor with custom dark-palette tiles.

2. **Active Trip Monitor**:
   - Commute status (`ACTIVE`, `ALERT`, `COMPLETED`), pickup and destination points.
   - Live heartbeat age counters for both employee and driver streams.
   - **60-Second Stale Heartbeat Detection**: When telemetry is lost or delayed for &ge; 60 seconds, the card dynamically transitions to a high-visibility crimson alert state with pulsing warnings.

3. **Driver Trust & Integrity Card**:
   - **Circular Trust Score Gauge (0–100)**: Visual dial reflecting rule-based ML deductions.
   - **Threat Flags**: Visual chips for `ROUTE_DEVIATION`, `UNEXPECTED_STOP`, `GPS_MISMATCH`.
   - **Evidence & Explainability**: Point-by-point reasons logged by the ML analyzer (e.g. detour distance, stop duration).
   - **GPS Stream Status**: Displays `"GPS stream unavailable"` in **neutral grey** (not red) when `gps_status` is `UNAVAILABLE`, avoiding false panic.
   - **Restrict Night Duty Button**: Local operator toggle to restrict or restore night shift clearance.

4. **Alert List & Incident Timeline**:
   - Chronological incident feed, ordered **newest first**.
   - Color-coded severity badges (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
   - Status indicators (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `FALSE_ALARM`).
   - One-click **Acknowledge** and **Resolve** triage buttons calling `PATCH /incidents/{id}`.

5. **Telemetry Auto-Refresh**:
   - Automatic polling every **3 seconds** (`setInterval`).
   - Pause/Resume controls and manual refresh button.

6. **Scenario Switcher & Interactive Simulation**:
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
├── .env                     # Environment variables (VITE_USE_MOCK=true)
├── .env.example             # Template for environment configuration
├── src/
│   ├── main.jsx             # React entry point & Leaflet CSS
│   ├── App.jsx              # Main dashboard view with 3s polling
│   ├── App.css              # Plain CSS styling (dark operations theme)
│   ├── api.js               # Data layer for all REST endpoints and replay
│   ├── components/
│   │   ├── Navbar.jsx           # Header with live indicator & poll controls
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

### 2. Run in Standalone Demo Mode (Default)
The dashboard is preconfigured with `VITE_USE_MOCK=true` in `.env`:
```bash
npm run dev
```
Open your browser at `http://localhost:5173`.
The simulated replay will immediately start streaming telemetry and advancing GPS pings every 3 seconds.

### 3. Connect to Live FastAPI Backend
To connect the dashboard to a live FastAPI instance running at `http://localhost:8000`:
1. Edit `dashboard/.env`:
   ```ini
   VITE_USE_MOCK=false
   VITE_API_URL=http://localhost:8000
   ```
2. Start the FastAPI backend from the `backend/` directory:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
3. Restart or reload Vite:
   ```bash
   npm run dev
   ```
4. In LIVE mode:
   - The header displays a green `LIVE` badge.
   - The scenario dropdown and mock replay bar are automatically hidden.
   - If the backend is unreachable or temporarily drops off, a non-intrusive `Backend offline` banner is shown while the dashboard preserves the last known telemetry without crashing.
   - If no active trips are running, a clean `No active trip` empty state is displayed until a trip is started.

### 4. Build for Production
To generate an optimized production bundle:
```bash
npm run build
```
To preview the production build locally:
```bash
npm run preview
```

---

## Data Layer API Reference (`src/api.js`)

| Function | Endpoint | Description |
|---|---|---|
| `getActiveTrip()` | `GET /trips/active` | Retrieves current active commute details, planned route, and heartbeats |
| `getTripLocations(tripId)` | `GET /trips/{id}/locations` | Fetches chronological GPS breadcrumbs for rider and cab streams |
| `getIncidents()` | `GET /incidents` | Fetches all open/acknowledged/resolved incidents, newest first |
| `getTripAnalysis(tripId)` | `GET /trips/{id}/analysis` | Fetches ML safety output: `{flags, trust_score, reasons, gps_status}` |
| `updateIncident(id, data)` | `PATCH /incidents/{id}` | Updates incident status (`ACKNOWLEDGED`, `RESOLVED`, `FALSE_ALARM`) |

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

