from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    """Client check-in request. Raw PIN is hashed on backend to verify normal vs duress."""
    trip_id: int
    pin: str = Field(..., min_length=4, max_length=10, description="PIN entered by employee")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Current latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Current longitude")


class CheckInResponse(BaseModel):
    """Uniform check-in response to preserve user safety during duress."""
    trip_id: int
    status: str = "ACKNOWLEDGED"
    message: str = "Check-in verified successfully"
    timestamp: datetime


class HeartbeatPing(BaseModel):
    """Device heartbeat ping for connectivity monitoring."""
    trip_id: int
    source: Literal["EMPLOYEE", "DRIVER"]
