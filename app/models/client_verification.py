import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class VerificationCategory(enum.Enum):
    CONTACT = "contact"
    IDENTITY = "identity"


class VerificationType(enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    IDENTITY_DOCUMENT = "identity_document"


class VerificationStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    verification_category = Column(Enum(VerificationCategory), nullable=False)
    verification_type = Column(Enum(VerificationType), nullable=False)
    verification_code = Column(String(10))
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    loan_application = relationship("LoanApplication", back_populates="verifications")

    def __repr__(self):
        return f"<Verification(category='{self.category}', type='{self.verification_type}', status='{self.status}')>"


"""
class ContactVerificationType(enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    IDENTITY_DOCUMENT = "identity_document"


class ContactVerificationStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


class IdentityVerificationType(enum.Enum):
    IDENTITY_DOCUMENT = "identity_document"


class IdentityVerificationStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


class ContactVerification(Base):
    __tablename__ = "contact_verifications"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    verification_type = Column(String(50), nullable=False)
    verification_code = Column(String(10))
    status = Column(String(20), default=ContactVerificationStatus.PENDING.value)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    loan_application = relationship("LoanApplication", back_populates="contact_verifications")

    def __repr__(self):
        return (
            f"<ContactVerification(type='{self.verification_type}', status='{self.status}')>"
        )


class IdentityVerification(Base):
    __tablename__ = "identity_verifications"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    verification_type = Column(String(50), nullable=False)
    verification_code = Column(String(10))
    status = Column(String(20), default=IdentityVerificationStatus.PENDING.value)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    loan_application = relationship("LoanApplication", back_populates="identity_verifications")

    def __repr__(self):
        return (
            f"<IdentityVerification(type='{self.verification_type}', status='{self.status}')>"
        )
"""
