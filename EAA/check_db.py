#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Check Script
-------------------
This script checks the records in the eaa_payments table.
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

def main():
    """Check the records in the eaa_payments table."""
    # Connect to the SPIDERSYNC database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        print("Failed to connect to the SPIDERSYNC database.")
        return
    
    try:
        cursor = connection.cursor()
        
        # Check if the table exists
        cursor.execute("SHOW TABLES LIKE 'eaa_payments'")
        if not cursor.fetchone():
            print("The eaa_payments table does not exist.")
            return
        
        # Get the table structure
        cursor.execute("DESCRIBE eaa_payments")
        print("=== TABLE STRUCTURE ===")
        print("{:<15} {:<15} {:<10} {:<10} {:<15}".format("Column", "Type", "Null", "Key", "Default"))
        print("-" * 65)
        for column in cursor.fetchall():
            print("{:<15} {:<15} {:<10} {:<10} {:<15}".format(
                column[0], column[1], column[2], column[3] or 'None', str(column[4] or 'None')
            ))
        
        print("\n")
        
        # Get the count of records
        cursor.execute("SELECT COUNT(*) FROM eaa_payments")
        count = cursor.fetchone()[0]
        print(f"Total records: {count}")
        
        # Get the first 5 records
        cursor.execute("SELECT id, ssn, name, amount, payment_id, clientID, payment_applied, date_applied FROM eaa_payments LIMIT 5")
        print("\n=== FIRST 5 RECORDS ===")
        records = cursor.fetchall()
        for row in records:
            print("\nRecord ID: {}".format(row[0]))
            print("  SSN:            '{}'".format(row[1]))
            print("  Name:           {}".format(row[2]))
            print("  Amount:         ${:.2f}".format(float(row[3])))
            print("  Payment ID:     {}".format(row[4]))
            print("  ClientID:       {}".format(row[5] if row[5] is not None else 'NULL'))
            print("  Payment Applied: {}".format(row[6]))
            print("  Date Applied:   {}".format(row[7] if row[7] is not None else 'NULL'))
        
        # Display all payment IDs
        cursor.execute("SELECT id, payment_id FROM eaa_payments")
        print("\n=== ALL PAYMENT IDs ===")
        payment_ids = cursor.fetchall()
        for i, (id, payment_id) in enumerate(payment_ids):
            print("  ID: {:<3} Payment ID: {}".format(id, payment_id))
    
    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
