#!/usr/bin/env python3
"""Verify complete import with all columns"""

from db_connection import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_import():
    """Check that all columns were properly imported."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check a specific record with all important columns
        cursor.execute("""
            SELECT ID, AsOfDate, BankReference, BAITypeCode, TransactionDesc,
                   BankID, BankName, AccountNumber, AccountType, State,
                   DebitAmount, CreditAmount, CustomerRefNo, Description
            FROM wf_payments_split 
            WHERE BankReference = 'IA000010139848'
        """)
        record = cursor.fetchone()
        
        if record:
            logger.info("✓ Record found with BankReference: IA000010139848")
            logger.info(f"  - ID: {record['ID']}")
            logger.info(f"  - AsOfDate: {record['AsOfDate']}")
            logger.info(f"  - BAITypeCode: {record['BAITypeCode']} (This was missing before!)")
            logger.info(f"  - TransactionDesc: {record['TransactionDesc']}")
            logger.info(f"  - BankID: {record['BankID']}")
            logger.info(f"  - BankName: {record['BankName']}")
            logger.info(f"  - AccountNumber: {record['AccountNumber']}")
            logger.info(f"  - AccountType: {record['AccountType']}")
            logger.info(f"  - State: {record['State']}")
            logger.info(f"  - CreditAmount: ${record['CreditAmount']}")
            logger.info(f"  - Description: {record['Description'][:50]}...")
        else:
            logger.error("Record not found!")
        
        # Test the query from the user
        logger.info("\nTesting user's query with BAITypeCode filter:")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM wf_payments_split
            WHERE AsOfDate = '2025-06-26' OR (
                AsOfDate >= '2025-06-01' AND 
                BAITypeCode IN (169, 554)
            )
        """)
        result = cursor.fetchone()
        logger.info(f"Records matching query: {result['count']}")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    verify_import()