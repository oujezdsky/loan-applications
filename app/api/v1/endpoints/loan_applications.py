from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    LoanApplicationCreate,
    LoanApplicationResponse,
    LoanApplicationStatusResponse,
)
from app.services.application import LoanApplicationService
from app.api.dependencies import get_user_agent, get_client_ip
from app.workers.tasks import process_application_workflow
from app.logging_config import logger

router = APIRouter()


@router.post(
    "/applications",
    response_model=LoanApplicationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit new loan application",
    description="Submit a new loan application with all required information",
)
async def create_application(
    application_data: LoanApplicationCreate,
    db: Session = Depends(get_db),
    client_ip: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
):
    """
    Create a new loan application.

    - **email**: Applicant's email address
    - **phone**: Applicant's phone number
    - **full_name**: Applicant's full name
    - **date_of_birth**: Applicant's date of birth (must be 18+)
    - **citizenship**: ISO country code
    - **housing_type**: Type of housing
    - **address**: Full residential address
    - **education_level**: Highest education level
    - **employment_status**: Current employment status
    - **monthly_income**: Average monthly income
    - **income_sources**: Sources of income
    - **marital_status**: Marital status
    - **children_count**: Number of children
    - **requested_amount**: Requested loan amount
    - **loan_purpose**: Purpose of the loan
    """

    try:
        application_service = LoanApplicationService(db)
        result = application_service.create_application(
            application_data, client_ip, user_agent
        )

        # Start async workflow
        process_application_workflow.delay(result["request_id"])

        return LoanApplicationResponse(
            request_id=result["request_id"],
            status="submitted",
            submitted_at=result.get("submitted_at"),
            verification_required=result["verification_required"],
        )

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}", extra={"client_ip": client_ip})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Application creation error: {str(e)}", extra={"client_ip": client_ip}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/applications/{request_id}/status",
    response_model=LoanApplicationStatusResponse,
    summary="Get application status",
    description="Check the current status of a loan application",
)
async def get_application_status(request_id: str, db: Session = Depends(get_db)):
    """
    Get the current status of a loan application by its request ID.
    """

    application_service = LoanApplicationService(db)
    status_info = application_service.get_application_status(request_id)

    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )

    return LoanApplicationStatusResponse(**status_info)
