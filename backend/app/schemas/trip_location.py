from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class TripLocationBase(BaseModel):
    trip_id: int
    source: Literal["EMPLOYEE", "DRIVER"] = Field(..., description="GPS telemetry origin")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude degrees (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude degrees (-180 to +180)")
    speed: Optional[float] = Field(default=0.0, ge=0.0, description="Speed in km/h")


class TripLocationCreate(TripLocationBase):
    pass


class TripLocationResponse(TripLocationBase):
    id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
