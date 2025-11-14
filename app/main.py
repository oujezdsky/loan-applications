import asyncio
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime

from app.config import settings
from app.utils.caching import (
    get_redis_client,
    wait_for_redis,
    close_redis_pool,
    get_redis_pool,
)
from app.utils.enums import enum_changes_subscriber
from app.database import get_db
from app.logging_config import setup_logging, logger
from app.api.v1.endpoints.router import api_router


async def initialize_services():
    """
    Service initialization.
    """
    logger.info("Starting Loan Application System API")

    # 1. Wait for Redis retry logic
    logger.info("Checking Redis availability...")
    redis_ready = await wait_for_redis()
    if not redis_ready:
        logger.error("Redis initialization failed - continuing without Pub/Sub")
        return None, None, None

    # 2. Initialize Redis client
    redis_client = None
    try:
        async for redis in get_redis_client():
            redis_client = redis
            break
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {e}")
        redis_client = None

    # 3. Initialize database session for Pub/Sub
    db_session = None
    subscriber_task = None

    if redis_client:
        try:
            db_session = next(get_db())

            # 4. Start Pub/Sub subscriber with error handling
            subscriber_task = asyncio.create_task(
                enum_changes_subscriber(redis_client, db_session)
            )
            logger.info("Enum changes Pub/Sub subscriber started")

        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub subscriber: {e}")
            if db_session:
                db_session.close()
            subscriber_task = None
            redis_client = None

    return redis_client, db_session, subscriber_task


async def shutdown_services(redis_client, db_session, subscriber_task):
    """
    Graceful shutdown of all services.
    """
    logger.info("Starting graceful shutdown...")

    # Cancel Pub/Sub subscriber
    if subscriber_task:
        subscriber_task.cancel()
        try:
            await subscriber_task
            logger.info("Pub/Sub subscriber task cancelled gracefully")
        except asyncio.CancelledError:
            logger.info("Pub/Sub subscriber task cancelled")
        except Exception as e:
            logger.error(f"Error cancelling subscriber task: {e}")

    # Close database session
    if db_session:
        db_session.close()
        logger.info("Database session closed")

    # Close Redis connection pool
    await close_redis_pool()
    logger.info("All services shut down successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan management.
    """
    redis_client, db_session, subscriber_task = None, None, None

    try:
        # Startup sequence
        setup_logging()
        redis_client, db_session, subscriber_task = await initialize_services()
        yield

    except Exception as e:
        logger.error(f"Startup sequence failed: {e}")
        raise
    finally:
        # Shutdown sequence - always runs
        await shutdown_services(redis_client, db_session, subscriber_task)


# Create FastAPI application
app = FastAPI(
    title="Loan Application System API",
    description="Loan Application Processing System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Loan Application System API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with service status.
    """
    from redis.asyncio import Redis
    from sqlalchemy import select
    from app.models.enums import EnumType

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "enums_data": {},
    }

    # Check Redis
    try:
        redis_pool = get_redis_pool()
        async with Redis(connection_pool=redis_pool) as redis:
            if await redis.ping():
                health_status["services"]["redis"] = "healthy"
            else:
                health_status["services"]["redis"] = "unhealthy"
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Database
    try:
        db_session = next(get_db())
        db_session.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
        db_session.close()
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check enum data
    try:
        db_session = next(get_db())
        enum_count = db_session.scalar(select(EnumType))
        health_status["enums_data"]["enum_types"] = enum_count
        health_status["enums_data"]["enums_ready"] = enum_count > 0
        db_session.close()
    except Exception as e:
        health_status["enums_data"]["enum_types"] = f"error: {str(e)}"
        health_status["enums_data"]["enums_ready"] = False

    return health_status


@app.get("/ready")
async def readiness_probe():
    """
    Kubernetes-style readiness probe for deployments.
    """
    health_data = await health_check()

    if health_data["status"] == "healthy":
        return JSONResponse(content=health_data, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(
            content=health_data, status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler with structured logging.
    """
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "client_ip": request.client.host if request.client else "unknown",
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": str(hash(str(exc) + str(datetime.utcnow())))[-8:],
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


def main():
    """Main entry point for the application"""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_config=None,
    )


if __name__ == "__main__":
    main()
