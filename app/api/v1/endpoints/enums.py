from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.utils.caching import get_redis_client
from app.utils.enums import get_enum_full_info
from app.database import get_db
from app.schemas.enums import EnumResponseSchema

enums_router = APIRouter(prefix="/enums", tags=["enums"])


@enums_router.get("/{enum_name}", response_model=EnumResponseSchema)
async def get_enum(
    enum_name: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """
    Retrieve enum details by name.

    Fetches the enum type and values from the database or Redis cache.
    Returns 404 if the enum does not exist, or 500 on internal errors.
    """
    try:
        info = await get_enum_full_info(enum_name, db=db, redis=redis)
        return EnumResponseSchema(enum_type=info["enum_type"], values=info["values"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
