import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

from app.config import settings


class ElasticsearchHandler(logging.Handler):
    """Handler for sending logs to Elasticsearch"""
    
    def emit(self, record: logging.LogRecord) -> None:
        # This would be implemented to send logs to Elasticsearch
        # For now, it's a placeholder.
        log_entry = self.format(record)
        pass


def setup_logging() -> None:
    """Setup comprehensive logging configuration"""
    
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    LOGGING_CONFIG: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(module)s %(funcName)s"
            }
        },
        "handlers": {
            "default": {
                "level": settings.LOG_LEVEL,
                "formatter": "standard",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "celery": {
                "level": settings.LOG_LEVEL,
                "formatter": "standard",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "celery.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "encoding": "utf8",
            },
            "elasticsearch": {
                "level": "INFO",
                "formatter": "json",
                "()": ElasticsearchHandler,
            },
            "console": {
                "level": "DEBUG" if settings.is_development else "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "app": {
                "handlers": ["default", "console", "elasticsearch"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "celery": {
                "handlers": ["celery", "console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["default", "console"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"] if settings.is_development else ["default"],
            "level": "WARNING",
        },
    }
    
    logging.config.dictConfig(LOGGING_CONFIG)


# Global logger instance
logger = logging.getLogger("app")