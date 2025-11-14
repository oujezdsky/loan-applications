import logging
import structlog
import sys
from app.config import settings


def setup_logging() -> None:
    """Configure structlog and logging for JSON-structured output."""
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get logger
    logger = structlog.get_logger()
    logger.info("Logging initialized", environment=settings.ENVIRONMENT)


# Initialize logger
logger: structlog.stdlib.BoundLogger = structlog.get_logger()
setup_logging()
