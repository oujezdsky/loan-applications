from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.logging_config import setup_logging, logger
from app.database import init_db, run_migrations
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting Loan Approval System API")

    # Initialize database
    try:
        init_db()
        run_migrations()
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    # Initialize Redis client for Pub/Sub
    redis_client = None
    try:
        async for redis in get_redis_client():  # Použij tvůj generator pro client
            redis_client = redis
            break  # Získej první (a jediný) client
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {e}")
        raise

    # Initialize DB session for subscriber (pokud potřebuješ persistentní session; jinak vytvoř novou uvnitř tasku)
    db_session = next(get_db())  # Nebo použij scoped_session pokud máš

    # Spusť Pub/Sub subscriber v background tasku
    subscriber_task = asyncio.create_task(enum_changes_subscriber(redis_client, db_session))
    logger.info("Enum changes Pub/Sub subscriber started")

    yield

    # Shutdown
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        logger.info("Pub/Sub subscriber task cancelled")
    
    await redis_client.aclose()
    logger.info("Redis client closed")
    
    # Zavři DB session pokud potřeba
    await db_session.close()
    
    logger.info("Shutting down Loan Approval System API")


# Create FastAPI application
app = FastAPI(
    title="Loan Approval System API",
    description="Enterprise loan application processing system",
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
    return {"message": "Loan Approval System API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"path": request.url.path, "method": request.method, "error": str(exc)},
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
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
