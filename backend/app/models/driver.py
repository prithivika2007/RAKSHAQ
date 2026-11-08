from sqlalchemy import Boolean, Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    trust_score = Column(Float, default=100.0, nullable=False)  # Scale: 0.0 - 100.0 (compatible with ML module)
    night_duty_eligible = Column(Boolean, default=True, nullable=False)

    # Relationships
    trips = relationship("Trip", back_populates="driver")
