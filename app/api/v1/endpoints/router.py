from fastapi import APIRouter
from app.api.v1.endpoints import applications, verification

api_router = APIRouter()

api_router.include_router(
    applications.router, prefix="/applications", tags=["applications"]
)
api_router.include_router(verification.router, prefix="/verify", tags=["verification"])
