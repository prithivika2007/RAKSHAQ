from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TripBase(BaseModel):
    employee_id: int
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    pickup_location: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    planned_route: Optional[List[List[float]]] = Field(
        default=None,
        description="Planned polyline as array of [latitude, longitude] coordinate pairs",
    )

    @field_validator("planned_route")
    @classmethod
    def validate_planned_route(cls, v: Optional[List[List[float]]]) -> Optional[List[List[float]]]:
        if v is None:
            return v
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError("planned_route must be a non-empty list of [latitude, longitude] coordinate pairs")
        for idx, coord in enumerate(v):
            if not isinstance(coord, (list, tuple)) or len(coord) != 2:
                raise ValueError(f"Coordinate at index {idx} must contain exactly two values: [latitude, longitude]")
            lat, lng = coord
            if not isinstance(lat, (int, float)) or not (-90.0 <= lat <= 90.0):
                raise ValueError(f"Latitude at index {idx} must be a number between -90 and 90, got {lat}")
            if not isinstance(lng, (int, float)) or not (-180.0 <= lng <= 180.0):
                raise ValueError(f"Longitude at index {idx} must be a number between -180 and 180, got {lng}")
        return v


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    status: Optional[str] = Field(default=None, description="SCHEDULED, ACTIVE, COMPLETED, ALERT, CANCELLED")
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class TripResponse(TripBase):
    id: int
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    last_employee_heartbeat_at: Optional[datetime] = None
    last_driver_heartbeat_at: Optional[datetime] = None
    last_checkin_at: Optional[datetime] = None

    @field_validator(
        "started_at",
        "ended_at",
        "last_employee_heartbeat_at",
        "last_driver_heartbeat_at",
        "last_checkin_at",
        mode="before",
    )
    @classmethod
    def normalize_sqlite_datetime(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    model_config = ConfigDict(from_attributes=True)
