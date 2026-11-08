from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class VehicleBase(BaseModel):
    registration_number: str = Field(..., min_length=2, max_length=50)
    vehicle_model: str = Field(..., min_length=1, max_length=100)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    registration_number: Optional[str] = Field(None, min_length=2, max_length=50)
    vehicle_model: Optional[str] = Field(None, min_length=1, max_length=100)


class VehicleResponse(VehicleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
