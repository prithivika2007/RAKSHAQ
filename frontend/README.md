# RAKSHAQ Employee Portal

The portal runs on port `5174` and uses the FastAPI backend at
`http://127.0.0.1:8000`.

Start the backend and seed the Chennai demo data from `backend/` first:

```powershell
python scripts\seed_chennai.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then start the portal:

```powershell
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

To use **Preview Dashboard**, start its separate Vite app in another terminal
from the repository root:

```powershell
cd dashboard
npm run dev
```

The portal's Preview Dashboard button opens
`http://127.0.0.1:5173/index.html?mode=preview`. Preview mode uses only the
dashboard's local demo/replay fixtures; dashboard edits affect only in-memory
demo state and do not call the backend. The portal remains on port `5174`.

The seed script prints the employee's database ID. The demo phone number is
`+919840001234`; use both to verify the registered employee. A scheduled trip
for that employee is started when available, otherwise a real scheduled SQLite
trip is created before starting. The demo portal submits route-based GPS samples
to the trip telemetry API every five seconds.

Check-in PINs in the Chennai seed are `2810` (normal) and `9999` (silent duress).
Both return the same check-in confirmation; duress creates a CRITICAL incident
visible to the dashboard. The Emergency SOS control creates a CRITICAL SOS
incident. Completing a commute updates the trip status to `COMPLETED`.
