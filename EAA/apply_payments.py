#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Apply Payments Script
------------------
This script marks payments as applied and updates the date_applied field.
"""

import os
import sys
import logging
import mysql.connector
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'eaa_apply_payments.log')),
        logging.StreamHandler()
    ]
)

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

def apply_payments(connection, payment_ids=None):
    """
    Mark payments as applied and update the date_applied field.
    
    Args:
        connection: MySQL database connection
        payment_ids: List of payment_ids to apply. If None, apply all payments with clientID.
    
    Returns:
        int: Number of payments applied
    """
    cursor = connection.cursor()
    
    try:
        if payment_ids:
            # Apply specific payments
            placeholders = ', '.join(['%s'] * len(payment_ids))
            update_query = f"""
            UPDATE eaa_payments
            SET payment_applied = 1, date_applied = NOW()
            WHERE payment_id IN ({placeholders}) AND clientID IS NOT NULL
            """
            cursor.execute(update_query, payment_ids)
        else:
            # Apply all payments with clientID
            update_query = """
            UPDATE eaa_payments
            SET payment_applied = 1, date_applied = NOW()
            WHERE clientID IS NOT NULL AND payment_applied = 0
            """
            cursor.execute(update_query)
        
        connection.commit()
        applied_count = cursor.rowcount
        logging.info(f"Applied {applied_count} payments")
        
        return applied_count
    
    except mysql.connector.Error as err:
        logging.error(f"Error applying payments: {err}")
        connection.rollback()
        return 0
    
    finally:
        cursor.close()

def get_applied_payments(connection):
    """
    Get all applied payments.
    
    Args:
        connection: MySQL database connection
    
    Returns:
        list: List of applied payment records
    """
    cursor = connection.cursor()
    
    try:
        query = """
        SELECT 
            id, 
            ssn, 
            name, 
            amount, 
            payment_id, 
            clientID, 
            payment_applied, 
            date_applied 
        FROM 
            eaa_payments 
        WHERE 
            payment_applied = 1
        ORDER BY 
            id
        """
        cursor.execute(query)
        applied_payments = cursor.fetchall()
        
        return applied_payments
    
    except mysql.connector.Error as err:
        logging.error(f"Error getting applied payments: {err}")
        return []
    
    finally:
        cursor.close()

def main():
    """Main function to apply payments."""
    logging.info("Starting payment application process")
    
    # Connect to the SPIDERSYNC database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        logging.error("Failed to connect to the SPIDERSYNC database")
        return
    
    try:
        # Apply payments
        applied_count = apply_payments(connection)
        
        # Get applied payments
        applied_payments = get_applied_payments(connection)
        
        logging.info(f"Successfully applied {applied_count} payments")
        logging.info(f"Total applied payments: {len(applied_payments)}")
        
        # Display the applied payments
        if applied_payments:
            print("\n=== APPLIED PAYMENTS ===")
            print("{:<5} {:<15} {:<25} {:<10} {:<15} {:<10} {:<20}".format(
                "ID", "SSN", "Name", "Amount", "Payment ID", "ClientID", "Date Applied"
            ))
            print("-" * 100)
            
            for payment in applied_payments:
                print("{:<5} {:<15} {:<25} {:<10} {:<15} {:<10} {:<20}".format(
                    payment[0],
                    payment[1],
                    payment[2][:25],
                    f"${float(payment[3]):.2f}",
                    payment[4],
                    str(payment[5]),
                    payment[7].strftime("%Y-%m-%d %H:%M:%S") if payment[7] else "NULL"
                ))
    
    finally:
        # Close the database connection
        if connection.is_connected():
            connection.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    main()
