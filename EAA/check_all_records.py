#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check All Records Script
---------------------
This script checks all records in the eaa_payments table and shows their clientID status.
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

def main():
    """Check all records in the eaa_payments table and show their clientID status."""
    # Connect to the SPIDERSYNC database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        print("Failed to connect to the SPIDERSYNC database.")
        return
    
    try:
        cursor = connection.cursor()
        
        # Get all records from eaa_payments
        cursor.execute("SELECT id, ssn, name, amount, payment_id, clientID FROM eaa_payments ORDER BY id")
        all_records = cursor.fetchall()
        
        # Count records with and without clientID
        with_client_id = [r for r in all_records if r[5] is not None]
        without_client_id = [r for r in all_records if r[5] is None]
        
        print(f"Total records: {len(all_records)}")
        print(f"Records with clientID: {len(with_client_id)}")
        print(f"Records without clientID: {len(without_client_id)}")
        
        # Display all records
        print("\n=== ALL RECORDS ===")
        print("{:<5} {:<15} {:<25} {:<10} {:<15} {:<10}".format(
            "ID", "SSN", "Name", "Amount", "Payment ID", "ClientID"
        ))
        print("-" * 85)
        
        for record in all_records:
            client_id = str(record[5]) if record[5] is not None else "NULL"
            print("{:<5} {:<15} {:<25} {:<10} {:<15} {:<10}".format(
                record[0], 
                record[1], 
                record[2][:25], 
                f"${float(record[3]):.2f}", 
                record[4],
                client_id
            ))
        
        # If there are records without clientID, check why
        if without_client_id:
            print("\n=== RECORDS WITHOUT CLIENT ID ===")
            for record in without_client_id:
                ssn = record[1]
                cursor.execute("SELECT COUNT(*) FROM customers WHERE SocSec = %s", (ssn,))
                count = cursor.fetchone()[0]
                
                print(f"ID: {record[0]}, SSN: {ssn}, Name: {record[2]}")
                if count > 0:
                    cursor.execute("SELECT CustomerID, PrimaryClientID, FirstName, LastName, EmployerID FROM customers WHERE SocSec = %s", (ssn,))
                    matches = cursor.fetchall()
                    print(f"  Found {count} matching customer records:")
                    for match in matches:
                        print(f"  - CustomerID: {match[0]}, PrimaryClientID: {match[1]}, Name: {match[2]} {match[3]}, EmployerID: {match[4]}")
                else:
                    print("  No matching customer records found.")
    
    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
