"""Employee verification routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeeDashboardResponse,
    EmployeeResponse,
    EmployeeVerifyRequest,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=List[EmployeeDashboardResponse], summary="List employee records")
def list_employees(db: Session = Depends(get_db)):
    """Return registered employee records and whether both safety PINs are configured."""
    employees = db.query(Employee).order_by(Employee.id.asc()).all()
    return [
        {
            "id": employee.id,
            "name": employee.name,
            "phone": employee.phone,
            "email": employee.email,
            "pin_configured": bool(employee.normal_pin_hash and employee.duress_pin_hash),
        }
        for employee in employees
    ]


@router.post("/verify", response_model=EmployeeResponse, summary="Verify employee record")
def verify_employee(payload: EmployeeVerifyRequest, db: Session = Depends(get_db)):
    """Verify a registered employee ID and phone number for the local portal."""
    employee = (
        db.query(Employee)
        .filter(
            Employee.id == payload.employee_id,
            Employee.phone == payload.phone.strip(),
        )
        .first()
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Employee verification failed.",
        )
    return employee
