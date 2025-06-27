#!/usr/bin/env python3
"""Test database connection and table structure"""

from db_connection import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test database connection and check wf_payments_split table."""
    try:
        connection = get_db_connection()
        logger.info("✓ Successfully connected to database")
        
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'wf_payments_split'")
        if cursor.fetchone():
            logger.info("✓ Table 'wf_payments_split' exists")
            
            # Get table structure
            cursor.execute("DESCRIBE wf_payments_split")
            columns = cursor.fetchall()
            logger.info("\nTable structure:")
            for col in columns:
                logger.info(f"  - {col['Field']} ({col['Type']})")
        else:
            logger.error("✗ Table 'wf_payments_split' not found")
            
        connection.close()
        
    except Exception as e:
        logger.error(f"✗ Connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection()