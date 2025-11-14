from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError
from app.config import settings
from app.logging_config import logger
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import asyncio


# Global connection pool for resource management
_redis_pool: Optional[ConnectionPool] = None


def get_redis_pool() -> ConnectionPool:
    """
    Redis connection pool with singleton pattern.
    Optimal connection reuse across the application.
    """
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                **settings.redis_connection_kwargs
            )
            logger.info("Redis connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create Redis connection pool: {e}")
            raise
    return _redis_pool


async def wait_for_redis(max_retries: int = 10, retry_delay: int = 2) -> bool:
    """
    Redis connection waiter.
    Ensures Redis is fully ready before application startup.
    """
    redis_pool = get_redis_pool()
    
    for attempt in range(max_retries):
        try:
            async with Redis(connection_pool=redis_pool) as redis:
                if await redis.ping():
                    logger.info("Redis connection established and responsive")
                    return True
        except (RedisError, ConnectionError) as e:
            logger.warning(
                f"🔄 Redis not ready (attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Redis connection failed after {max_retries} attempts")
                return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            return False
    
    return False


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    Redis client provider with error handling and health checks.
    Provides async context manager for automatic connection management.
    """
    redis_pool = get_redis_pool()
    redis_client = None
    
    try:
        redis_client = Redis(connection_pool=redis_pool)
        
        # Health check before yielding client
        if not await redis_client.ping():
            raise RedisError("Redis ping failed")
            
        logger.debug("✅ Redis client provided successfully")
        yield redis_client
        
    except RedisError as e:
        logger.error(f"Redis client error: {e}")
        raise RuntimeError(f"Redis connection error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Redis error: {e}")
        raise
    finally:
        if redis_client:
            await redis_client.aclose()

@asynccontextmanager
async def get_redis_for_subscriber() -> AsyncGenerator[Redis, None]:
    redis_client = Redis(connection_pool=get_redis_pool())
    try:
        if not await redis_client.ping():
            raise RedisError("Redis ping failed")
        yield redis_client
    finally:
        await redis_client.aclose()


async def close_redis_pool():
    """
    Close Redis connection pool during application shutdown.
    """
    global _redis_pool
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")


def get_sync_redis_client():
    """
    Get sync Redis client for Celery and other sync operations.
    """
    import redis
    try:
        sync_client = redis.from_url(
            settings.REDIS_URL,
            **settings.redis_connection_kwargs
        )
        # Test connection
        sync_client.ping()
        logger.debug("Sync Redis client created successfully")
        return sync_client
    except Exception as e:
        logger.error(f"Failed to create sync Redis client: {e}")
        raise