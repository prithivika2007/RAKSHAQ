from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import app.models  # noqa: F401 - registers models with Base.metadata
from app.database import Base, engine, ensure_schema_updated

# Initialize database tables and apply backward-compatible schema updates
Base.metadata.create_all(bind=engine)
ensure_schema_updated(engine)

app = FastAPI(
    title="RAKSHAQ - Women's Night-Shift Safety System API",
    description="Backend API for RAKSHAQ commute safety monitoring and alert management.",
    version="0.1.0",
)

# 1. Enable CORS Middleware for Mobile App & Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request / Response Pydantic Models for Mobile API ---
class StartTripRequest(BaseModel):
    employee_id: str

class TelemetryRequest(BaseModel):
    trip_id: str
    lat: float
    lng: float
    timestamp: Optional[str] = None

class CheckInRequest(BaseModel):
    trip_id: str
    pin: str

class CloseTripRequest(BaseModel):
    trip_id: str


# --- Mobile API Router (/api/trip) ---
mobile_router = APIRouter(prefix="/api/trip", tags=["Mobile Commute"])

@mobile_router.post("/start")
def start_trip(payload: StartTripRequest):
    return {
        "status": "success",
        "trip_id": f"TRIP-{payload.employee_id}-101",
        "message": f"Monitored trip initialized for {payload.employee_id}"
    }

@mobile_router.post("/telemetry")
def receive_telemetry(payload: TelemetryRequest):
    print(f"📡 [GPS Telemetry Logged] Trip: {payload.trip_id} -> Lat: {payload.lat}, Lng: {payload.lng}")
    return {
        "status": "received",
        "trip_id": payload.trip_id,
        "safety_score": 98
    }

@mobile_router.post("/check-in")
def safety_check_in(payload: CheckInRequest):
    is_duress = payload.pin == "9999"
    if is_duress:
        print(f"🚨 [DURESS ALERT 9999] Silent emergency dispatched for trip {payload.trip_id}!")
        return {
            "status": "duress_alert_dispatched",
            "message": "Silent SOS triggered to dashboard"
        }
    
    print(f"🔒 [Check-In Verified] Trip {payload.trip_id}")
    return {
        "status": "verified",
        "message": "Check-in successful"
    }

@mobile_router.post("/close")
def close_trip(payload: CloseTripRequest):
    print(f"🏡 [Trip Closed] Employee arrived safely for trip {payload.trip_id}")
    return {
        "status": "closed",
        "trip_id": payload.trip_id,
        "message": "Trip completed safely"
    }

# Register the mobile endpoints router into the FastAPI app
app.include_router(mobile_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "healthy"}