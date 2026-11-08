from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class IncidentBase(BaseModel):
    trip_id: int
    incident_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="e.g. ROUTE_DEVIATION, UNEXPECTED_STOP, DURESS_PIN, MISSED_CHECKIN, GPS_MISMATCH",
    )
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(default="MEDIUM")
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    status: Optional[Literal["OPEN", "ACKNOWLEDGED", "RESOLVED", "FALSE_ALARM"]] = None
    severity: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None
    description: Optional[str] = None


class IncidentResponse(IncidentBase):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
