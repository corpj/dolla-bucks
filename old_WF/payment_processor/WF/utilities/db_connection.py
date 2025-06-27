"""
Database connection management for the WF payment processing system.

This module provides a centralized way to manage database connections using SQLAlchemy.
It ensures proper connection handling, pooling, and session management.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

# Configure logger
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and sessions.
    
    This class is responsible for creating and managing database connections and sessions
    with appropriate connection pooling and error handling.
    """
    
    _instance = None
    
    def __new__(cls):
        """Implements singleton pattern to ensure only one database manager exists."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the database manager if not already initialized."""
        if self._initialized:
            return
            
        # Load database configuration
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '3306')
        db_name = os.environ.get('DB_NAME', 'spider_sync_DEV')
        db_user = os.environ.get('DB_USER', 'glama')
        db_password = os.environ.get('DB_PASSWORD', '')
        
        # Create connection URL
        connection_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Create engine with appropriate pooling configuration
        try:
            self.engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True
            )
            logger.info("Database engine created successfully")
            
            # Create session factory
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            
            self._initialized = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise
    
    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db_manager.session_scope() as session:
                session.query(...)
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()


# Create a global instance
db_manager = DatabaseManager()


def get_session():
    """Get a database session."""
    return db_manager.Session()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    return db_manager.session_scope()
