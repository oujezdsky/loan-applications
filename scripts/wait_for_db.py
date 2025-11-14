#!/usr/bin/env python3
"""
Database wait script with retry logic
"""
import os
import sys
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_database(max_retries=30, retry_interval=2):
    """Wait for database to be ready with exponential backoff"""
    db_url = os.getenv('POSTGRES_DB_URL')
    if not db_url:
        logger.error("POSTGRES_DB_URL environment variable is not set")
        sys.exit(1)
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(db_url, connect_args={'connect_timeout': 5})
            with engine.connect() as conn:
                logger.info("✅ Database connection successful")
                return True
        except OperationalError as e:
            logger.warning(f"⚠️ Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                logger.error("❌ Database connection failed after all retries")
                sys.exit(1)
    
    return False

if __name__ == "__main__":
    wait_for_database()