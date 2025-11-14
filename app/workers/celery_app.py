from celery import Celery
from app.config import settings
from app.logging_config import setup_logging

# Setup logging
setup_logging()

# Create Celery app
celery_app = Celery(
    "loan_approval",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Prague",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.process_application_workflow": {"queue": "workflow"},
        "app.workers.tasks.preprocess_application": {"queue": "processing"},
        "app.workers.tasks.enrich_application_data": {"queue": "enrichment"},
        "app.workers.tasks.calculate_risk_score": {"queue": "scoring"},
        "app.workers.tasks.send_verification_code": {"queue": "notifications"},
    },
    task_always_eager=settings.is_development,  # Sync execution in development
)


def start_worker():
    """Start Celery worker - used by Poetry script"""
    celery_app.start()


if __name__ == "__main__":
    start_worker()
