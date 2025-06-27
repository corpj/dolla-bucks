#!/usr/bin/env python3
"""Delete recently imported records to reimport with all columns"""

from db_connection import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_recent_imports():
    """Delete records imported today."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Delete records from today's import (the ones with missing columns)
        delete_sql = """
            DELETE FROM wf_payments_split 
            WHERE BankReference IN (
                'IA000010139848', 'IA000010142712', 'IA000015941197',
                'IA000010143144', 'IA000017848051', 'IA000010140419'
            )
        """
        cursor.execute(delete_sql)
        deleted_count = cursor.rowcount
        
        connection.commit()
        logger.info(f"Deleted {deleted_count} records")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"Error deleting records: {str(e)}")

if __name__ == "__main__":
    delete_recent_imports()