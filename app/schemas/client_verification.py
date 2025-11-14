from pydantic import BaseModel, Field
from typing import Literal, Optional, Union
from datetime import datetime
from app.models import VerificationStatus


#   Společné základy pro všechny typy verifikace
class BaseVerificationRequest(BaseModel):
    request_id: str = Field(..., min_length=36, max_length=36)


#   Contact (email nebo SMS) verifikace
class ContactVerificationRequest(BaseVerificationRequest):
    verification_type: Literal["email", "sms"]
    verification_code: str = Field(..., min_length=4, max_length=10)


#   Identity verifikace (manuální, bez kódu)
class IdentityVerificationRequest(BaseVerificationRequest):
    verification_type: Literal["identity_document"]
    verification_status: VerificationStatus = Field(..., description="Manual verification status.")
    verification_code: None = Field(
        default=None, description="No code for manual verification"
    )


#   Discriminated union
VerificationRequest = Union[
    ContactVerificationRequest,
    IdentityVerificationRequest,
]

"""
class EmailVerificationRequest(BaseModel):
    request_id: str = Field(..., min_length=36, max_length=36)
    verification_code: str = Field(..., min_length=4, max_length=10)


class SmsVerificationRequest(BaseModel):
    request_id: str = Field(..., min_length=36, max_length=36)
    verification_code: str = Field(..., min_length=4, max_length=10)


class IdentityVerificationRequest(BaseModel):
    request_id: str = Field(..., min_length=36, max_length=36)
"""

# class VerificationRequest(BaseModel):
#     request_id: str = Field(..., min_length=36, max_length=36)
#     verification_code: str = Field(..., min_length=4, max_length=10)
#     verification_type: str = Field(
#         ..., enum=["email", "sms", "identity_document"]
#     )


class VerificationResponse(BaseModel):
    success: bool
    message: str
    next_step: Optional[str] = None  # U identity bude krok typu "manual_verification"
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VerificationInitResponse(BaseModel):
    success: bool
    message: str
    verification_method: str  # e-mail, SMS, identity_document
    expires_in_minutes: int

    class Config:
        from_attributes = True
