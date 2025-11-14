from pydantic import BaseModel, EmailStr, field_validator, Field, ValidationInfo
from typing import List, Optional, Dict, Union
from datetime import datetime, date
from app.utils.enums import get_valid_enum_values
import asyncio


class LoanApplicationCreate(BaseModel):
    # Personal Information
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")  # E.164 format
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: date
    citizenship: str = Field(..., min_length=2, max_length=3)

    # Housing Information
    housing_type: Union[str, List[str]]
    address: str = Field(..., min_length=5, max_length=500)

    # Education and Employment
    education_level: Union[str, List[str]]
    employment_status: str = Field(..., min_length=2, max_length=100)
    monthly_income: float = Field(..., gt=0)
    income_sources: Union[str, List[str]]

    # Family Information
    marital_status: Union[str, List[str]]
    children_count: int = Field(0, ge=0)

    # Loan Information
    requested_amount: float = Field(..., gt=0)
    loan_purpose: str = Field(..., min_length=10, max_length=1000)

    @field_validator("date_of_birth")
    def validate_age(cls, v):
        if not v:
            raise ValueError("Date of birth must be specified")
        min_age = 18
        max_age = 100
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))

        if age < min_age:
            raise ValueError(f"Applicant must be at least {min_age} years old")
        if age > max_age:
            raise ValueError(f"Applicant must be younger than {max_age} years")

        return v

    @field_validator("income_sources")
    def validate_income_sources(cls, v):
        if not v:
            raise ValueError("At least one income source must be specified")
        return v

    @field_validator(
        "housing_type",
        "income_sources",
        "education_level",
        "marital_status",
        mode="before",
    )
    def validate_enum(cls, v, info: ValidationInfo):
        field_name = info.field_name

        enum_name = field_name.replace("_", "").capitalize() + "Enum"
        try:
            enum_info = asyncio.run(get_valid_enum_values(enum_name))
        except Exception as e:
            raise ValueError(f"Failed to fetch enum info for {field_name}: {e}")

        valid_values = set(enum_info["valid_values"])
        is_multi = enum_info["is_multi_select"]
        max_selections = enum_info.get("max_selections")

        if is_multi:
            if not isinstance(v, list):
                raise ValueError(f"{field_name} must be a list for multi-select enums")
            if len(v) == 0:
                raise ValueError(f"{field_name} cannot be empty for this enum")
            v = list(set(v))  # remove possible duplicity
            if max_selections and len(v) > max_selections:
                raise ValueError(
                    f"{field_name} exceeds max selections ({max_selections})"
                )
            invalid = set(v) - valid_values
            if invalid:
                raise ValueError(
                    f"Invalid values in {field_name}: {invalid}. Valid: {', '.join(valid_values)}"
                )
        else:
            if not isinstance(v, str):
                raise ValueError(
                    f"{field_name} must be a single string for single-select enums"
                )
            if v not in valid_values:
                raise ValueError(
                    f"Invalid {field_name}: '{v}'. Valid: {', '.join(valid_values)}"
                )

        return v


class LoanApplicationResponse(BaseModel):
    request_id: str
    status: str
    submitted_at: datetime
    verification_required: bool

    class Config:
        from_attributes = True


class LoanApplicationDetail(LoanApplicationResponse):
    email: str
    phone: str
    full_name: str
    # ... other fields as needed

    class Config:
        from_attributes = True


class LoanApplicationStatusResponse(BaseModel):
    request_id: str
    status: str
    last_updated: datetime
    verification_status: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True
