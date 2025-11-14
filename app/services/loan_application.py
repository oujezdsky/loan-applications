from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from redis.asyncio import Redis
from datetime import datetime, timedelta
import uuid

from app.models import LoanApplication, LoanApplicationStatus, AuditLog
from app.schemas import LoanApplicationCreate
from app.logging_config import logger
from app.config import settings
from app.utils.enums import get_valid_enum_values


class LoanApplicationService:
    def __init__(self, db: Session, redis: Redis):
        from app.services import VerificationService

        self.db = db
        self.redis = redis
        self.verification_service = VerificationService(db)

    async def _validate_dynamic_enums(self, application_data: LoanApplicationCreate):
        """Helper method for dynamic enums validation."""

        housing_info = await get_valid_enum_values(
            "housing_type", db=self.db, redis=self.redis
        )
        if application_data.housing_type not in housing_info["valid_values"]:
            raise ValueError(f"Invalid housing_type: {application_data.housing_type}")

        education_info = await get_valid_enum_values(
            "education_level", db=self.db, redis=self.redis
        )
        if application_data.education_level not in education_info["valid_values"]:
            raise ValueError(
                f"Invalid education_level: {application_data.education_level}"
            )
        marital_status_info = await get_valid_enum_values(
            "martial_status", db=self.db, redis=self.redis
        )
        if application_data.marital_status not in marital_status_info["valid_values"]:
            raise ValueError(
                f"Invalid martial_status: {application_data.marital_status}"
            )
        income_type_info = await get_valid_enum_values(
            "income_type", db=self.db, redis=self.redis
        )
        for income_type in application_data.income_type:
            if income_type not in income_type_info["valid_values"]:
                raise ValueError(f"Invalid income_type: {income_type}")

    async def create_loan_application(
        self, application_data: LoanApplicationCreate, client_ip: str, user_agent: str
    ) -> Dict[str, Any]:
        """Create new loan application with initial validation"""

        await self._validate_dynamic_enums(application_data)
        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())

            # Calculate expiration date
            expires_at = datetime.utcnow() + timedelta(
                hours=settings.VERIFICATION_TIMEOUT_HOURS
            )

            # Create application record
            application = LoanApplication(
                request_id=request_id,
                email=application_data.email,
                phone=application_data.phone,
                full_name=application_data.full_name,
                date_of_birth=application_data.date_of_birth,
                citizenship=application_data.citizenship,
                housing_type=application_data.housing_type,
                address=application_data.address,
                education_level=application_data.education_level,
                employment_status=application_data.employment_status,
                monthly_income=application_data.monthly_income,
                income_sources=[source for source in application_data.income_sources],
                marital_status=application_data.marital_status,
                children_count=application_data.children_count,
                requested_amount=application_data.requested_amount,
                loan_purpose=application_data.loan_purpose,
                status=LoanApplicationStatus.SUBMITTED,
                expires_at=expires_at,
            )

            self.db.add(application)
            await self.db.commit()
            await self.db.refresh(application)

            # Create audit log
            await self._create_audit_log(
                application.id, "APPLICATION_SUBMITTED", client_ip, user_agent
            )

            logger.info(
                f"Application created successfully: {request_id}",
                extra={
                    "request_id": request_id,
                    "email": application_data.email,
                    "client_ip": client_ip,
                },
            )

            return {
                "request_id": request_id,
                "status": "submitted",
                "verification_required": True,
                "expires_at": expires_at.isoformat(),
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to create application: {str(e)}",
                extra={"error": str(e), "client_ip": client_ip},
            )
            raise

    def get_loan_application_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an application"""

        application = (
            self.db.query(LoanApplication)
            .filter(LoanApplication.request_id == request_id)
            .first()
        )

        if not application:
            return None

        # Get verification status
        verification_status = self.verification_service.get_verification_status(
            application.id
        )

        return {
            "request_id": application.request_id,
            "status": application.status.value,
            "submitted_at": application.submitted_at,
            "verification_status": verification_status,
            "last_updated": application.updated_at or application.submitted_at,
        }

    async def _create_audit_log(
        self, application_id: int, event_type: str, ip_address: str, user_agent: str
    ) -> None:
        """Create audit log entry"""

        audit_log = AuditLog(
            application_id=application_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
