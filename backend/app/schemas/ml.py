from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class MLTelemetryPoint(BaseModel):
    """Employee GPS telemetry ping matching ml/analyzer.py detectors."""
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    speed: Optional[float] = Field(default=0.0, ge=0.0)
    ts: Union[float, int, str]


class MLDriverPoint(BaseModel):
    """Driver/cab GPS telemetry ping for dual-stream comparison."""
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    ts: Union[float, int, str]


class MLTripAnalysisInput(BaseModel):
    """Input payload expected by ml.analyzer.analyze_trip."""
    trip_id: str
    planned_route: List[List[float]]
    points: List[MLTelemetryPoint] = Field(default_factory=list)
    driver_points: List[MLDriverPoint] = Field(default_factory=list)
    rider_feedback: Optional[Union[int, float, Dict[str, Any], str]] = None


class MLTripAnalysisOutput(BaseModel):
    """Guaranteed output payload returned by ml.analyzer.analyze_trip."""
    trip_id: str
    flags: List[str]  # e.g., ["ROUTE_DEVIATION", "UNEXPECTED_STOP", "GPS_MISMATCH"]
    trust_score: int = Field(..., ge=0, le=100)
    reasons: List[str]
    gps_status: Literal["OK", "UNAVAILABLE"]

