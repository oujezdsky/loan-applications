from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextvars import ContextVar, Token
from typing import Generator
from typing import cast

from app.config import settings
from app.logging_config import logger

# Database URL
POSTGRES_DB_URL = str(settings.POSTGRES_DB_URL)

# Engine and Session
engine = create_engine(
    POSTGRES_DB_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.is_development,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Context var for async session management
db_session: ContextVar[Session] = ContextVar("db_session")


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    session = SessionLocal()
    token: Token[Session] | None = None
    try:
        token = db_session.set(session)
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()
        if token:
            db_session.reset(token)


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
