from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional, Dict, Union
from datetime import datetime, date
from app.utils.enums import get_valid_enum_values
import asyncio

'''
class HousingType(str, Enum):
    OWN = "vlastní"
    RENT = "nájem"
    WITH_PARENTS = "u rodičů"
    WITH_PARTNER = "u partnera"
    COOPERATIVE = "družstevní"


class EducationLevel(str, Enum):
    BASIC = "základní"
    SECONDARY = "střední"
    HIGHER = "vysokoškolské"


class MaritalStatus(str, Enum):
    MARRIED = "vdaná/ženatý"
    SINGLE = "svobodný"
    DIVORCED = "rozvedený"
    WIDOWED = "ovdovělý"


class IncomeSource(str, Enum):
    EMPLOYMENT = "zaměstnání"
    BUSINESS = "podnikání"
    PENSION = "důchod"
    RENT = "nájem"
    OTHER = "jiné"
'''

class LoanApplicationCreate(BaseModel):
    # Personal Information
    email: EmailStr
    phone: str = Field(..., regex=r"^\+?[1-9]\d{1,14}$")  # E.164 format
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

    @validator("date_of_birth")
    def validate_age(cls, v):
        min_age = 18
        max_age = 100
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))

        if age < min_age:
            raise ValueError(f"Applicant must be at least {min_age} years old")
        if age > max_age:
            raise ValueError(f"Applicant must be younger than {max_age} years")

        return v

    @validator("income_sources")
    def validate_income_sources(cls, v):
        if not v:
            raise ValueError("At least one income source must be specified")
        return v

    @validator("housing_type", "income_type", "education_level", "marital_status",  pre=True, each_item=False)
    def validate_enum(cls, v, field):
        enum_name = field.name.replace("_", "").capitalize() + "Enum"  # Automatický mapping, uprav pokud potřeba
        try:
            info = asyncio.run(get_valid_enum_values(enum_name))
        except Exception as e:
            raise ValueError(f"Failed to fetch enum info for {field.name}: {e}")
        
        valid_values = set(info["valid_values"])
        is_multi = info["is_multi_select"]
        max_selections = info.get("max_selections")
        
        if is_multi:
            if not isinstance(v, list):
                raise ValueError(f"{field.name} must be a list for multi-select enums")
            if len(v) == 0:
                raise ValueError(f"{field.name} cannot be empty for this enum")  # Pokud required; jinak uprav
            v = list(set(v))  # Odstraň duplicity automaticky
            if max_selections and len(v) > max_selections:
                raise ValueError(f"{field.name} exceeds max selections ({max_selections})")
            invalid = set(v) - valid_values
            if invalid:
                raise ValueError(f"Invalid values in {field.name}: {invalid}. Valid: {', '.join(valid_values)}")
        else:
            if not isinstance(v, str):
                raise ValueError(f"{field.name} must be a single string for single-select enums")
            if v not in valid_values:
                raise ValueError(f"Invalid {field.name}: '{v}'. Valid: {', '.join(valid_values)}")
        
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
