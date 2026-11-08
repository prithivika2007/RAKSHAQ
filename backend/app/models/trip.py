from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    pickup_location = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    planned_route = Column(JSON, nullable=True)  # Stores coordinate arrays/GeoJSON
    status = Column(String(50), default="SCHEDULED", nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Device heartbeat tracking for missed check-in and connectivity monitoring
    last_employee_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    last_driver_heartbeat_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")
    vehicle = relationship("Vehicle", back_populates="trips")
    incidents = relationship("Incident", back_populates="trip", cascade="all, delete-orphan")
    locations = relationship("TripLocation", back_populates="trip", cascade="all, delete-orphan")
