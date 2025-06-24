#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_db_connection.py
---------------------
Script to test database connection using MySQLConnectionManager
Path: EAA/scripts/test_db_connection.py
Created: 2025-04-04
Modified: 2025-04-04

Variables:
- env_file: Path to the .env file
- environment: Database environment (dev, prod, backup)
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directories to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
payments_dir = os.path.dirname(parent_dir)
sys.path.append(payments_dir)

from utils.MySQLConnectionManager import MySQLConnectionManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(script_dir, "test_db_connection.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_eaa_payments_table(connection):
    """
    Check if the eaa_payments table exists and get record count.
    
    Args:
        connection: MySQL database connection
        
    Returns:
        tuple: (table_exists, record_count)
    """
    try:
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'eaa_payments'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Get record count
            cursor.execute("SELECT COUNT(*) FROM eaa_payments")
            record_count = cursor.fetchone()[0]
            
            logger.info(f"eaa_payments table exists with {record_count} records")
            print(f"eaa_payments table exists with {record_count} records")
        else:
            logger.warning("eaa_payments table does not exist")
            print("eaa_payments table does not exist")
            record_count = 0
        
        cursor.close()
        return table_exists, record_count
    
    except Exception as e:
        logger.error(f"Error checking eaa_payments table: {e}")
        print(f"Error checking eaa_payments table: {e}")
        return False, 0

def main():
    """Main function to test database connection."""
    # Look for .env file in different locations
    env_file = None
    possible_paths = [
        # payment_processor directory
        Path(payments_dir) / "payment_processor" / ".env",
        # Root project directory
        Path(payments_dir) / ".env",
        # EAA directory
        Path(parent_dir) / ".env"
    ]
    
    for path in possible_paths:
        if path.exists():
            env_file = str(path)
            logger.info(f"Found .env file at {env_file}")
            print(f"Found .env file at {env_file}")
            break
    
    if not env_file:
        logger.warning("No .env file found in common locations")
        print("No .env file found in common locations")
    
    # Create connection manager
    db_manager = MySQLConnectionManager(env_file)
    
    # Try different environments
    environments = ["dev", "prod"]
    connection = None
    
    for environment in environments:
        logger.info(f"Trying to connect to {environment} environment")
        print(f"Trying to connect to {environment} environment")
        
        connection = db_manager.connect_to_spidersync(environment)
        
        if connection and connection.is_connected():
            logger.info(f"Successfully connected to {environment} environment")
            print(f"Successfully connected to {environment} environment")
            
            # Test a simple query
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION() as version")
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                logger.info(f"MySQL Version: {result[0]}")
                print(f"MySQL Version: {result[0]}")
            
            # Check eaa_payments table
            check_eaa_payments_table(connection)
            
            # Close connection
            db_manager.close_connection(connection)
            
            return True
    
    if not connection or not connection.is_connected():
        logger.error("Failed to connect to any database environment")
        print("Failed to connect to any database environment")
        print("\nPlease make sure your .env file contains valid database credentials:")
        print("SPIDERSYNC_DEV_HOST=<hostname>")
        print("SPIDERSYNC_DEV_DATABASE=spider_sync_DEV")
        print("SPIDERSYNC_DEV_USER=<username>")
        print("SPIDERSYNC_DEV_PASSWORD=<password>")
        print("SPIDERSYNC_DEV_PORT=3306")
        
        return False

if __name__ == "__main__":
    main()
