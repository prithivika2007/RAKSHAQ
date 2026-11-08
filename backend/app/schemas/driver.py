from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DriverBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=5, max_length=20)
    trust_score: float = Field(default=100.0, ge=0.0, le=100.0, description="Trust score (0–100 scale)")
    night_duty_eligible: bool = Field(default=True, description="Night shift clearance flag")


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=5, max_length=20)
    trust_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    night_duty_eligible: Optional[bool] = None


class DriverResponse(DriverBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
