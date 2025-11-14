from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    ContactVerificationRequest,
    VerificationResponse,
    VerificationInitResponse,
)
from app.services import VerificationService

router = APIRouter()


@router.post(
    "/initiate/verification",
    response_model=VerificationInitResponse,
    summary="Initiate verification for a specific method",
    description="Start verification for a specific method (email, SMS, identity)",
)
async def initiate_verification(
    verification_data: ContactVerificationRequest, db: Session = Depends(get_db)
):
    """
    Initiate verification for email, SMS, or identity.

    - **request_id**: The application request ID
    """

    verification_service = VerificationService(db)
    result = verification_service.initiate_verification(
        application=verification_data,
        verification_type=verification_data.verification_type,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
        )

    return VerificationInitResponse(**result)


@router.post(
    "/verify",
    response_model=VerificationResponse,
    summary="Verify contact or identity",
    description="Verify email, SMS, or identity based on verification_type.",
)
async def verify(
    verification_data: ContactVerificationRequest,
    db: Session = Depends(get_db),
):
    service = VerificationService(db)

    if verification_data.verification_type in ("email", "sms"):
        result = service.verify_code(
            verification_data.request_id,
            verification_data.verification_code,
            verification_data.verification_type,
        )
    elif verification_data.verification_type == "identity_document":
        result = service.update_identity_verification_status(
            application_id=verification_data.request_id,
            new_status=verification_data.status,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported verification type")

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return VerificationResponse(**result)


'''
@router.post(
    "/verify/email",
    response_model=VerificationResponse,
    summary="Verify email address",
    description="Verify email address using the received verification code",
)
async def verify_email(
    verification_data: ContactVerificationRequest, db: Session = Depends(get_db)
):
    """
    Verify email address with the provided verification code.

    - **request_id**: The application request ID
    - **verification_code**: The code received via email
    """

    verification_service = VerificationService(db)
    result = verification_service.verify_code(
        verification_data.request_id, verification_data.verification_code, "email"
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
        )

    return VerificationResponse(**result)


@router.post(
    "/verify/sms",
    response_model=VerificationResponse,
    summary="Verify phone number",
    description="Verify phone number using the received SMS code",
)
async def verify_sms(
    verification_data: ContactVerificationRequest, db: Session = Depends(get_db)
):
    """
    Verify phone number with the provided SMS verification code.

    - **request_id**: The application request ID
    - **verification_code**: The code received via SMS
    """

    verification_service = VerificationService(db)
    result = verification_service.verify_code(
        verification_data.request_id, verification_data.verification_code, "sms"
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
        )

    return VerificationResponse(**result)


@router.post(
    "/verify/identity",
    response_model=VerificationResponse,
    summary="Verify identity",
    description="Verify identity by manual decision",
)
async def verify_identity(
    verification_data: ContactVerificationRequest, db: Session = Depends(get_db)
):
    """
    Verify identity by manual decision.

    - **request_id**: The application request ID
    - **verification_code**: placeholder, nn for identity verification
    """

    verification_service = VerificationService(db)
    result = verification_service.verify_code(
        verification_data.request_id, verification_data.verification_code, "identity_document"
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
        )

    return VerificationResponse(**result)
'''
