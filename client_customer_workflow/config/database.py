"""
Database configuration module for client_customer_workflow.

This module provides SQLAlchemy database engine creation and session management
utilities for connecting to the spider_sync_DEV database.
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


def create_db_engine(database: str = "spider_sync_DEV") -> Engine:
    """
    Create a SQLAlchemy database engine for the specified database.
    
    Args:
        database: Database name (default: spider_sync_DEV)
        
    Returns:
        SQLAlchemy Engine instance
    """
    # Get database credentials from environment variables
    host = os.getenv('SPIDERSYNC_DEV_HOST')
    db_name = os.getenv('SPIDERSYNC_DEV_DATABASE')
    user = os.getenv('SPIDERSYNC_DEV_USER')
    password = os.getenv('SPIDERSYNC_DEV_PASSWORD')
    port = os.getenv('SPIDERSYNC_DEV_PORT', '3306')
    
    # Override database name if provided
    if database and database != "spider_sync_DEV":
        db_name = database
    
    # Validate required environment variables
    if not all([host, db_name, user, password]):
        raise ValueError(
            "Missing required database environment variables. "
            "Please ensure SPIDERSYNC_DEV_HOST, SPIDERSYNC_DEV_DATABASE, "
            "SPIDERSYNC_DEV_USER, and SPIDERSYNC_DEV_PASSWORD are set."
        )
    
    # Create connection URL
    connection_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    
    # Create engine with connection pooling
    engine = create_engine(
        connection_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False  # Set to True for SQL debugging
    )
    
    logger.info(f"Created database engine for {db_name}@{host}:{port}")
    
    return engine


def get_session_factory(engine: Engine) -> sessionmaker:
    """
    Create a session factory bound to the given engine.
    
    Args:
        engine: SQLAlchemy Engine instance
        
    Returns:
        sessionmaker instance
    """
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(Session: sessionmaker):
    """
    Provide a transactional scope for database operations.
    
    This context manager ensures that database sessions are properly
    closed and transactions are rolled back on error.
    
    Args:
        Session: sessionmaker instance
        
    Yields:
        SQLAlchemy Session instance
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Convenience function to get a session directly
def get_db_session(database: str = "spider_sync_DEV") -> Session:
    """
    Get a database session for immediate use.
    
    Note: The caller is responsible for closing this session.
    
    Args:
        database: Database name (default: spider_sync_DEV)
        
    Returns:
        SQLAlchemy Session instance
    """
    engine = create_db_engine(database)
    Session = get_session_factory(engine)
    return Session()