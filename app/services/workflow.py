from sqlalchemy.orm import Session
from datetime import datetime

from app.models import LoanApplication, LoanApplicationStatus, AuditLog
from app.workers.tasks import (
    preprocess_application,
    enrich_application_data,
    calculate_risk_score,
)
from app.logging_config import logger

# TODO, outdated!
class WorkflowService:
    def __init__(self, db: Session):
        self.db = db

    def execute_workflow(self, request_id: str) -> None:
        """Execute the complete workflow for an application"""

        application = (
            self.db.query(LoanApplication)
            .filter(LoanApplication.request_id == request_id)
            .first()
        )

        if not application:
            logger.error(f"Application not found: {request_id}")
            return

        try:
            # Wait for verification (this would be triggered by verification completion)
            self._wait_for_verification(application)

            # Preprocessing
            self._update_status(application, LoanApplicationStatus.PREPROCESSING)
            preprocessing_result = preprocess_application.delay(request_id).get()

            # Data Enrichment
            self._update_status(application, LoanApplicationStatus.DATA_ENRICHMENT)
            enrichment_result = enrich_application_data.delay(request_id).get()

            # Check if we should proceed to scoring
            if enrichment_result.get("external_data_verified", False):
                # Scoring
                self._update_status(application, LoanApplicationStatus.SCORING)
                scoring_result = calculate_risk_score.delay(request_id).get()

                # Decision making based on score
                if scoring_result.get("auto_approve", False):
                    self._update_status(
                        application,
                        LoanApplicationStatus.APPROVED,
                        "Auto-approved based on risk score",
                    )
                elif scoring_result.get("auto_reject", False):
                    self._update_status(
                        application,
                        LoanApplicationStatus.REJECTED,
                        "Auto-rejected based on risk score",
                    )
                else:
                    self._update_status(
                        application,
                        LoanApplicationStatus.MANUAL_REVIEW,
                        "Requires manual review",
                    )
            else:
                # Data enrichment failed or requires review
                self._update_status(
                    application,
                    LoanApplicationStatus.MANUAL_REVIEW,
                    "Data verification required",
                )

            logger.info(f"Workflow completed for {request_id}")

        except Exception as e:
            self._update_status(application, LoanApplicationStatus.ERROR, str(e))
            logger.error(f"Workflow failed for {request_id}: {str(e)}")
            raise

    def _wait_for_verification(self, application: LoanApplication) -> None:
        """Wait for email/SMS verification to complete"""

        # In production, this would listen for verification events
        # For now, we'll simulate waiting by checking status
        from app.services import VerificationService

        verification_service = VerificationService(self.db)
        status = verification_service.get_verification_status(application.id)

        # Check if all required verifications are complete
        required_verifications = ["email", "sms"]
        completed = all(
            status.get(vtype) == "verified" for vtype in required_verifications
        )

        if not completed:
            # In real implementation, this would use Celery's waiting mechanisms
            # or event-driven architecture
            self._update_status(application, LoanApplicationStatus.AWAITING_VERIFICATION)
            # For now, we'll assume verification is complete for demo purposes
            pass

        self._update_status(application, LoanApplicationStatus.VERIFIED)

    def _update_status(
        self, application: LoanApplication, status: LoanApplicationStatus, reason: str = None
    ) -> None:
        """Update application status and create audit log"""

        application.status = status
        if reason:
            application.decision_reason = reason
        application.updated_at = datetime.utcnow()

        self.db.commit()

        # Create audit log
        audit_log = AuditLog(
            application_id=application.id,
            event_type=f"STATUS_CHANGED_{status.value.upper()}",
            event_data={"reason": reason} if reason else None,
        )

        self.db.add(audit_log)
        self.db.commit()

        logger.info(
            f"Application {application.request_id} status updated to {status.value}",
            extra={
                "request_id": application.request_id,
                "new_status": status.value,
                "reason": reason,
            },
        )
