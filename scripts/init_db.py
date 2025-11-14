#!/usr/bin/env python3
"""
Database initialization script for Loan Approval System.
This script runs Alembic migrations and can seed initial data.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import run_migrations, init_db
from app.logging_config import setup_logging, logger


def main():
    """Initialize the database with migrations and optional seed data"""
    setup_logging()
    
    try:
        logger.info("Starting database initialization...")
        
        # Initialize database (sets up connection)
        init_db()
        
        # Run migrations
        run_migrations()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()