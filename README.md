# RAKSHAQ

RAKSHAQ connects an employee commute portal, a FastAPI/SQLite service, an ML
trip analyzer, and a live security dashboard.

## Local integration

The local demo requires three terminals. Run the backend and seed before
starting either frontend.

### 1. Backend (port 8000)

From the repository root in PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts\seed_chennai.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The seed script prints the employee's database ID. The demo phone is
`+919840001234`; the normal check-in PIN is `2810` and the silent duress PIN is
`9999`. Use the printed ID and phone to verify in the employee portal.

### 2. Security dashboard (port 5173)

```powershell
cd dashboard
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

[dashboard/.env](./dashboard/.env) is configured for the live backend. Live mode
does not substitute mock responses when a backend request fails.

### 3. Employee portal (port 5174)

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

The demo portal sends its route-based GPS samples to the backend every five
seconds. For a live browser/device GPS provider, integrate the platform
geolocation source in place of this explicitly simulated route stream.

## Verify the employee-to-dashboard flow

1. Verify the seeded employee in the portal and start the scheduled trip.
2. Confirm its numeric trip ID is shown in SQLite-backed API data at
   `http://127.0.0.1:8000/trips/active`.
3. Keep the trip active for GPS samples to appear on the map at
   `http://127.0.0.1:5173`.
4. Submit PIN `2810` for an ordinary check-in. Submitting `9999` raises a
   CRITICAL `DURESS_PIN` incident but returns the same confirmation to the
   employee.
5. Use Emergency SOS to create a CRITICAL incident. Route-deviation analysis
   runs against stored telemetry and updates the assigned driver's trust score.
6. Complete the trip; its database status becomes `COMPLETED`.

The login flow verifies the employee ID and registered phone against SQLite.
No SMS/OTP delivery provider is configured in this repository.

## Tests and builds

Backend tests use isolated SQLite databases:

```powershell
cd backend
python tests\test_phase4.py
python tests\test_phase5.py
python -X utf8 tests\test_phase6.py
```

Build both existing frontends from their directories:

```powershell
cd dashboard
npm run build
cd ..\frontend
npm run build
```
