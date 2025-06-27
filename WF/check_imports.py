#!/usr/bin/env python3
"""Check imported WF payment records"""

from db_connection import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_imports():
    """Check recent imports in wf_payments_split table."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Count total records
        cursor.execute("SELECT COUNT(*) as total FROM wf_payments_split")
        total = cursor.fetchone()['total']
        logger.info(f"Total records in wf_payments_split: {total}")
        
        # Get recent records
        cursor.execute("""
            SELECT ID, AsOfDate, BankReference, CustomerRefNo, 
                   DebitAmount, CreditAmount, TransactionDesc
            FROM wf_payments_split 
            ORDER BY ID DESC 
            LIMIT 10
        """)
        records = cursor.fetchall()
        
        logger.info("\nRecent records:")
        for record in records:
            logger.info(f"ID: {record['ID']}, Date: {record['AsOfDate']}, "
                       f"BankRef: {record['BankReference']}, "
                       f"Debit: ${record['DebitAmount']}, Credit: ${record['CreditAmount']}")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"Error checking records: {str(e)}")

if __name__ == "__main__":
    check_imports()