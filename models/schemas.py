"""
Pydantic models for request validation and response serialisation.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------- Request Models ----------

class EmployeeCreate(BaseModel):
    """Payload for creating a new employee."""
    first_name: str = Field(..., min_length=1, max_length=50, alias="firstName")
    last_name: str = Field(..., min_length=1, max_length=50, alias="lastName")
    department_id: int = Field(..., gt=0, alias="departmentId")
    salary: Decimal = Field(..., gt=0, alias="salary")
    bonus: Optional[Decimal] = Field(None, ge=0, alias="bonus")
    hire_date: datetime.date = Field(..., alias="hireDate")

    model_config = {"populate_by_name": True}

    @field_validator("hire_date", mode="before")
    @classmethod
    def parse_date(cls, value):
        if isinstance(value, str):
            return datetime.date.fromisoformat(value)
        return value


class EmployeeUpdate(BaseModel):
    """Payload for updating an existing employee.  All fields optional."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, alias="firstName")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, alias="lastName")
    department_id: Optional[int] = Field(None, gt=0, alias="departmentId")
    salary: Optional[Decimal] = Field(None, gt=0, alias="salary")
    bonus: Optional[Decimal] = Field(None, ge=0, alias="bonus")
    hire_date: Optional[datetime.date] = Field(None, alias="hireDate")
    # Explicit flag: set to true to clear the bonus (set to NULL)
    clear_bonus: bool = Field(False, alias="clearBonus")

    model_config = {"populate_by_name": True}

    @field_validator("hire_date", mode="before")
    @classmethod
    def parse_date(cls, value):
        if isinstance(value, str):
            return datetime.date.fromisoformat(value)
        return value


# ---------- Response Models ----------

class EmployeeResponse(BaseModel):
    """Serialisable employee representation."""
    employee_id: int = Field(alias="employeeId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    department_id: int = Field(alias="departmentId")
    salary: Decimal = Field(alias="salary")
    bonus: Optional[Decimal] = Field(alias="bonus")
    hire_date: datetime.date = Field(alias="hireDate")
    department_name: Optional[str] = Field(None, alias="departmentName")

    model_config = {"populate_by_name": True, "from_attributes": True}


class DepartmentResponse(BaseModel):
    """Serialisable department representation."""
    department_id: int = Field(alias="departmentId")
    department_name: str = Field(alias="departmentName")
    location: Optional[str] = Field(alias="location")

    model_config = {"populate_by_name": True, "from_attributes": True}
