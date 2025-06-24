#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQLConnectionManager
----------------------
Manages MySQL database connections for the SPIDERSYNC database.
Author: Lil Claudy Flossy
"""

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class MySQLConnectionManager:
    """Manages MySQL database connections with environment-based configuration."""
    
    def __init__(self, env_file=None):
        """
        Initialize the connection manager.
        
        Args:
            env_file (str): Path to .env file. If None, searches common locations.
        """
        self.env_file = env_file or self._find_env_file()
        if self.env_file:
            load_dotenv(self.env_file)
        else:
            load_dotenv()  # Try to load from current directory
        
        self.connections = {}
        
    def _find_env_file(self):
        """Search for .env file in common locations."""
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),
            os.path.join(os.path.dirname(__file__), '.env'),
            '.env'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found .env file at {path}")
                return path
        
        logger.warning("No .env file found in common locations")
        return None
    
    def connect_to_spidersync(self, environment='dev'):
        """
        Connect to the SPIDERSYNC database.
        
        Args:
            environment (str): Database environment ('dev', 'prod', 'backup')
            
        Returns:
            mysql.connector.connection: Database connection or None if failed
        """
        try:
            # Get environment-specific variables
            env_prefix = f"SPIDERSYNC_{environment.upper()}_"
            
            config = {
                'host': os.getenv(f"{env_prefix}HOST", 'localhost'),
                'database': os.getenv(f"{env_prefix}DATABASE", 'spider_sync_DEV'),
                'user': os.getenv(f"{env_prefix}USER"),
                'password': os.getenv(f"{env_prefix}PASSWORD"),
                'port': int(os.getenv(f"{env_prefix}PORT", 3306)),
                'autocommit': False
            }
            
            # Check if credentials are available
            if not config['user'] or not config['password']:
                logger.error(f"Database credentials not found for {environment} environment")
                logger.error(f"Please ensure {env_prefix}USER and {env_prefix}PASSWORD are set in .env file")
                return None
            
            # Create connection
            connection = mysql.connector.connect(**config)
            
            if connection.is_connected():
                db_info = connection.get_server_info()
                logger.info(f"Connected to MySQL Server version {db_info}")
                logger.info(f"Connected to database: {config['database']}")
                
                # Store connection for later reference
                self.connections[environment] = connection
                
                return connection
                
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return None
    
    def close_connection(self, connection):
        """
        Close a database connection.
        
        Args:
            connection: The database connection to close
        """
        try:
            if connection and connection.is_connected():
                connection.close()
                logger.info("Database connection closed")
        except Error as e:
            logger.error(f"Error closing connection: {e}")
    
    def close_all_connections(self):
        """Close all stored connections."""
        for env, conn in self.connections.items():
            self.close_connection(conn)
        self.connections.clear()
    
    def execute_query(self, connection, query, params=None, fetch=True):
        """
        Execute a query on the given connection.
        
        Args:
            connection: Database connection
            query (str): SQL query to execute
            params (tuple): Query parameters
            fetch (bool): Whether to fetch results
            
        Returns:
            List of results if fetch=True, otherwise None
        """
        try:
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                results = cursor.fetchall()
                cursor.close()
                return results
            else:
                connection.commit()
                cursor.close()
                return None
                
        except Error as e:
            logger.error(f"Error executing query: {e}")
            connection.rollback()
            return None


# For backward compatibility
def get_connection(environment='dev'):
    """
    Get a database connection (backward compatibility function).
    
    Args:
        environment (str): Database environment
        
    Returns:
        Database connection
    """
    manager = MySQLConnectionManager()
    return manager.connect_to_spidersync(environment)