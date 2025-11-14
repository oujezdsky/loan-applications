import random
import string
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import (
    Verification,
    VerificationType,
    VerificationCategory,
    VerificationStatus,
)
from app.logging_config import logger


class VerificationService:
    def __init__(self, db: Session):
        self.db = db

    def initiate_verification(
        self,
        application,
        verification_type: VerificationType,
        category: Optional[VerificationCategory] = VerificationCategory.CONTACT,
    ) -> Dict[str, Any]:
        """
        Start verification for a specific type (email, sms, identity).
        Can be called multiple times independently.
        """

        # Check whether an active verification of the given type already exists
        existing = (
            self.db.query(Verification)
            .filter(
                Verification.application_id == application.id,
                Verification.verification_type == verification_type.value,
                Verification.status.in_(
                    [
                        VerificationStatus.PENDING.value,
                        VerificationStatus.EXPIRED.value,
                    ]
                ),
            )
            .first()
        )

        # If it exists — invalidate it (e.g., the user requests a new code)
        if existing:
            existing.status = VerificationStatus.EXPIRED.value
            self.db.commit()

        verification = self._create_verification(
            application.id,
            category,
            verification_type,
        )

        if verification_type == VerificationType.IDENTITY_DOCUMENT:
            logger.info(
                f"Identity verification initiated for application {application.request_id}",
                extra={"request_id": application.request_id},
            )
            return {
                "type": verification_type.value,
                "status": verification.status,
                "expires_at": verification.expires_at,
                "message": "Manual identity verification initiated. Awaiting admin review.",
            }

        target = (
            application.email
            if verification_type == VerificationType.EMAIL
            else application.phone
        )
        self._send_verification_code(verification, target)

        logger.info(
            f"{verification_type.value} verification initiated for {application.request_id}",
            extra={
                "request_id": application.request_id,
                "verification_type": verification_type.value,
            },
        )

        return {
            "type": verification_type.value,
            "status": verification.status,
            "expires_at": verification.expires_at,
        }

    # Helper method - generating and creating verification DB record
    def _create_verification(
        self,
        application_id: int,
        verification_category: VerificationCategory,
        verification_type: VerificationType,
    ) -> Verification:
        """Create a new verification entry"""

        verification_code = (
            self._generate_verification_code()
            if verification_type != VerificationType.IDENTITY_DOCUMENT
            else None
        )
        expires_at = datetime.utcnow() + timedelta(hours=24)

        verification = Verification(
            application_id=application_id,
            category=verification_category.value,
            verification_type=verification_type.value,
            verification_code=verification_code,
            expires_at=expires_at,
            status=VerificationStatus.PENDING.value,
        )

        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)

        return verification

    # Dummy verification code generator
    def _generate_verification_code(self, length: int = 6) -> str:
        return "".join(random.choices(string.digits, k=length))

    # Dummy sender (SMS / Email)
    def _send_verification_code(self, verification: Verification, target: str) -> None:
        logger.info(
            f"Verification code {verification.verification_code} "
            f"sent to {target} via {verification.verification_type}",
            extra={
                "verification_id": verification.id,
                "target": target,
                "method": verification.verification_type,
            },
        )

    # Verification code validation (SMS/Email)
    def verify_code(
        self, request_id: str, verification_code: str, verification_type: str
    ) -> Dict[str, Any]:
        """Verify a code received by the user"""

        from app.models import LoanApplication

        application = (
            self.db.query(LoanApplication)
            .filter(LoanApplication.request_id == request_id)
            .first()
        )
        if not application:
            return {"success": False, "message": "Application not found"}

        verification = (
            self.db.query(Verification)
            .filter(
                Verification.application_id == application.id,
                Verification.verification_type == verification_type,
                Verification.status == VerificationStatus.PENDING.value,
            )
            .first()
        )

        if not verification:
            return {
                "success": False,
                "message": "Verification not found or already completed",
            }

        if datetime.utcnow() > verification.expires_at:
            verification.status = VerificationStatus.EXPIRED.value
            self.db.commit()
            return {"success": False, "message": "Verification code expired"}

        if verification.attempts >= verification.max_attempts:
            verification.status = VerificationStatus.FAILED.value
            self.db.commit()
            return {"success": False, "message": "Maximum attempts exceeded"}

        verification.attempts += 1

        if verification.verification_code == verification_code:
            verification.status = VerificationStatus.VERIFIED.value
            verification.verified_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                f"Verification successful for {request_id}",
                extra={
                    "request_id": request_id,
                    "verification_type": verification_type,
                },
            )
            return {"success": True, "message": "Verification successful"}

        self.db.commit()
        return {"success": False, "message": "Invalid verification code"}

    # External update for manual identity check (via admin interface)
    def update_identity_verification_status(
        self,
        application_id: int,
        new_status: VerificationStatus,
    ) -> Dict[str, Any]:
        """
        Called from an admin system or webhook when manual ID verification is completed.
        new_status can be: 'approved', 'rejected', 'canceled'
        """

        verification = (
            self.db.query(Verification)
            .filter(
                Verification.application_id == application_id,
                Verification.verification_type
                == VerificationType.IDENTITY_DOCUMENT.value,
            )
            .first()
        )

        if not verification:
            return {"success": False, "message": "Identity verification not found"}

        verification.status = new_status.value
        if new_status == VerificationStatus.VERIFIED:
            verification.verified_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(verification)

        logger.info(
            f"Identity verification status updated for application {application_id} -> {new_status.value}",
            extra={
                "application_id": application_id,
                "status": new_status.value,
            },
        )

        return {
            "success": True,
            "message": f"Identity verification updated to {new_status.value}",
            "verified_at": verification.verified_at,
        }

    # Status of all verifications for a given request
    def get_verification_status(self, application_id: int) -> Dict[str, str]:
        verifications = (
            self.db.query(Verification)
            .filter(Verification.application_id == application_id)
            .all()
        )
        return {v.verification_type: v.status for v in verifications}
