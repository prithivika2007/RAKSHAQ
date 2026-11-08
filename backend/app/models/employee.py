from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)

    # Secure Hashed PIN storage - never store plaintext PINs (Argon2id)
    normal_pin_hash = Column(String(255), nullable=True)
    duress_pin_hash = Column(String(255), nullable=True)

    # Brute-force protection & rate limiting
    failed_pin_attempts = Column(Integer, default=0, nullable=False)
    pin_locked_until = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    trips = relationship("Trip", back_populates="employee", cascade="all, delete-orphan")
