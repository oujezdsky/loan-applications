from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.models import Application, ApplicationStatus, AuditLog
from app.schemas import ApplicationCreate
from app.services import VerificationService
from app.logging_config import logger
from app.config import settings


class LoanApplicationService:
    def __init__(self, db: Session):
        self.db = db
        self.verification_service = VerificationService(db)

    def create_loan_application(
        self, application_data: ApplicationCreate, client_ip: str, user_agent: str
    ) -> Dict[str, Any]:
        """Create new loan application with initial validation"""

        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())

            # Calculate expiration date
            expires_at = datetime.utcnow() + timedelta(
                hours=settings.VERIFICATION_TIMEOUT_HOURS
            )

            # Create application record
            application = Application(
                request_id=request_id,
                email=application_data.email,
                phone=application_data.phone,
                full_name=application_data.full_name,
                date_of_birth=application_data.date_of_birth,
                citizenship=application_data.citizenship,
                housing_type=application_data.housing_type.value,
                address=application_data.address,
                education_level=application_data.education_level.value,
                employment_status=application_data.employment_status,
                monthly_income=application_data.monthly_income,
                income_sources=[
                    source.value for source in application_data.income_sources
                ],
                marital_status=application_data.marital_status.value,
                children_count=application_data.children_count,
                requested_amount=application_data.requested_amount,
                loan_purpose=application_data.loan_purpose,
                status=ApplicationStatus.SUBMITTED,
                expires_at=expires_at,
            )

            self.db.add(application)
            self.db.commit()
            self.db.refresh(application)

            # Create audit log
            self._create_audit_log(
                application.id, "APPLICATION_SUBMITTED", client_ip, user_agent
            )

            # Initialize verification process
            verification_init = self.verification_service.initiate_verification(
                application
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
                "verification_methods": verification_init["methods"],
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
            self.db.query(Application)
            .filter(Application.request_id == request_id)
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

    def _create_audit_log(
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
        self.db.commit()
