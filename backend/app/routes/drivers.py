"""Driver profile and trust score routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.driver import Driver
from app.schemas.driver import DriverResponse, DriverUpdate

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=List[DriverResponse], summary="List driver profiles")
def list_drivers(db: Session = Depends(get_db)):
    """Return driver profiles including their current trust and night-duty status."""
    return db.query(Driver).order_by(Driver.id.asc()).all()


@router.get("/{driver_id}", response_model=DriverResponse, summary="Get driver profile")
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Fetch driver profile including current ML-updated trust score."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found.",
        )
    return driver


@router.patch("/{driver_id}", response_model=DriverResponse, summary="Update driver")
def update_driver(
    driver_id: int,
    payload: DriverUpdate,
    db: Session = Depends(get_db),
):
    """Update driver fields: name, phone, trust_score (0–100), night_duty_eligible.

    Only provided (non-null) fields are updated. trust_score is validated
    to [0.0, 100.0] by the DriverUpdate schema.
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found.",
        )

    if payload.name is not None:
        driver.name = payload.name
    if payload.phone is not None:
        driver.phone = payload.phone
    if payload.trust_score is not None:
        driver.trust_score = payload.trust_score
    if payload.night_duty_eligible is not None:
        driver.night_duty_eligible = payload.night_duty_eligible

    db.commit()
    db.refresh(driver)
    return driver
