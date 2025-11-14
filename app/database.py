from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextvars import ContextVar, Token
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.config import settings
from app.logging_config import logger

# Database URL
POSTGRES_DB_URL = str(settings.POSTGRES_DB_URL)


# Engine and Session
async_engine = create_async_engine(
    POSTGRES_DB_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.is_development,
)

# Async sessionmaker
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Context var for async session management
async_db_session: ContextVar[AsyncSession] = ContextVar("async_db_session")

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async dependency for FastAPI to get database session"""
    session = AsyncSessionLocal()
    token: Token[AsyncSession] | None = None
    try:
        token = async_db_session.set(session)
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f"Async database session error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()
        if token:
            async_db_session.reset(token)


def run_migrations() -> None:
    """
    Run database migrations using Alembic,
    can be used in CI/CD or in emergency cases.
    """
    from alembic.config import Config
    from alembic import command

    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise
