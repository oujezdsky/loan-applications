from fastapi import APIRouter
from app.api.v1.endpoints import loan_applications, client_verification

api_router = APIRouter()

api_router.include_router(
    loan_applications.router, prefix="/applications", tags=["applications"]
)
api_router.include_router(client_verification.router, prefix="/verify", tags=["verification"])
