from pydantic import BaseModel, ConfigDict, Field, model_validator


class EmployeeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name of employee")
    phone: str = Field(..., min_length=5, max_length=20, description="Contact phone number")
    email: str = Field(..., min_length=3, max_length=100, description="Company email address")


class EmployeeCreate(EmployeeBase):
    pass


class EmployeePINSetup(BaseModel):
    """Schema for setting up or updating employee safety PINs (hashed upon storage with Argon2id)."""
    normal_pin: str = Field(..., min_length=4, max_length=10, description="Routine check-in PIN (4-10 digits)")
    duress_pin: str = Field(..., min_length=4, max_length=10, description="Duress emergency PIN (4-10 digits)")

    @model_validator(mode="after")
    def validate_pins_differ(self):
        if self.normal_pin == self.duress_pin:
            raise ValueError("Normal PIN and Duress PIN must be different for security reasons.")
        return self


class EmployeeResponse(EmployeeBase):
    id: int

    # Plaintext and hashed PINs are never exposed in responses
    model_config = ConfigDict(from_attributes=True)
