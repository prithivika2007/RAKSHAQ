"""Pydantic schemas for request and response validation."""

from app.schemas.checkin import CheckInRequest, CheckInResponse, HeartbeatPing
from app.schemas.driver import DriverBase, DriverCreate, DriverResponse, DriverUpdate
from app.schemas.employee import (
    EmployeeBase,
    EmployeeCreate,
    EmployeeDashboardResponse,
    EmployeePINSetup,
    EmployeeResponse,
    EmployeeVerifyRequest,
)
from app.schemas.incident import IncidentBase, IncidentCreate, IncidentResponse, IncidentUpdate
from app.schemas.ml import MLDriverPoint, MLTelemetryPoint, MLTripAnalysisInput, MLTripAnalysisOutput
from app.schemas.trip import TripBase, TripCreate, TripResponse, TripUpdate
from app.schemas.trip_location import TripLocationBase, TripLocationCreate, TripLocationResponse
from app.schemas.vehicle import VehicleBase, VehicleCreate, VehicleResponse, VehicleUpdate

__all__ = [
    # Employee
    "EmployeeBase",
    "EmployeeCreate",
    "EmployeePINSetup",
    "EmployeeVerifyRequest",
    "EmployeeResponse",
    "EmployeeDashboardResponse",
    # Driver
    "DriverBase",
    "DriverCreate",
    "DriverUpdate",
    "DriverResponse",
    # Vehicle
    "VehicleBase",
    "VehicleCreate",
    "VehicleUpdate",
    "VehicleResponse",
    # Trip
    "TripBase",
    "TripCreate",
    "TripUpdate",
    "TripResponse",
    # Check-in & Heartbeat
    "CheckInRequest",
    "CheckInResponse",
    "HeartbeatPing",
    # Incident
    "IncidentBase",
    "IncidentCreate",
    "IncidentUpdate",
    "IncidentResponse",
    # TripLocation
    "TripLocationBase",
    "TripLocationCreate",
    "TripLocationResponse",
    # ML Compatibility
    "MLTelemetryPoint",
    "MLDriverPoint",
    "MLTripAnalysisInput",
    "MLTripAnalysisOutput",
]
