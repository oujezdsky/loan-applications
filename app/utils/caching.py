from redis.asyncio import Redis
from app.config import Settings
from app.logging_config import logger
from typing import AsyncGenerator
from redis.exceptions import RedisError
from fastapi import Depends


async def get_redis_client(
    settings: Settings = Depends(lambda: Settings()),  # type: ignore
) -> AsyncGenerator[Redis, None]:
    """Provide Redis client with automatic connection management."""
    redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        encoding="utf-8",
        socket_timeout=5,
    )
    try:
        await redis.ping()
        logger.debug("Redis connection established", redis_url=settings.REDIS_URL)
        yield redis
    except RedisError as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise RuntimeError(f"Redis connection error: {str(e)}")
    finally:
        await redis.aclose()
        logger.debug("Redis connection closed")
