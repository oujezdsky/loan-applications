from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    JSON,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base


class LoanApplicationStatus(enum.Enum):
    SUBMITTED = "submitted"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    PREPROCESSING = "preprocessing"
    DATA_ENRICHMENT = "data_enrichment"
    SCORING = "scoring"
    MANUAL_REVIEW = "manual_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), unique=True, index=True, nullable=False)

    # Personal Information
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    citizenship = Column(String(3), nullable=False)  # ISO code

    # Housing Information
    housing_type = Column(String(50), nullable=False)  # References enum_values
    address = Column(Text, nullable=False)

    # Education and Employment
    education_level = Column(String(50), nullable=False)
    employment_status = Column(String(50), nullable=False)
    monthly_income = Column(Float, nullable=False)
    income_sources = Column(JSON, nullable=False)  # Array of income sources

    # Family Information
    marital_status = Column(String(50), nullable=False)
    children_count = Column(Integer, default=0)

    # Loan Information
    requested_amount = Column(Float, nullable=False)
    loan_purpose = Column(Text, nullable=False)

    # Document Information
    identity_document_front = Column(String(500))  # File path or URL
    identity_document_back = Column(String(500))

    # Processing Information
    status = Column(
        SQLEnum(LoanApplicationStatus), default=LoanApplicationStatus.SUBMITTED
    )
    risk_score = Column(Float)
    decision_reason = Column(Text)

    # Metadata
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    contact_verifications = relationship("ContactVerification", back_populates="loan_application")
    identity_verifications = relationship("IdentityVerification", back_populates="loan_application")
    audit_logs = relationship("AuditLog", back_populates="loan_application")

    def __repr__(self):
        return f"<Application(request_id='{self.request_id}', status='{self.status.value}')>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON)
    user_agent = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    loan_application = relationship("LoanApplication", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(application_id={self.application_id}, event='{self.event_type}')>"
