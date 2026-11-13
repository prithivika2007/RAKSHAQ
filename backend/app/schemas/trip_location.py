from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    @field_validator("recorded_at", mode="before")
    @classmethod
    def normalize_sqlite_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    model_config = ConfigDict(from_attributes=True)
