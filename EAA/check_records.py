#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check Records Script
-----------------
This script checks records in the eaa_payments and customers tables before updating.
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

def main():
    """Check records in the eaa_payments and customers tables before updating."""
    # Connect to the SPIDERSYNC database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        print("Failed to connect to the SPIDERSYNC database.")
        return
    
    try:
        cursor = connection.cursor()
        
        # Get all records from eaa_payments
        cursor.execute("SELECT id, ssn, name, amount, payment_id FROM eaa_payments")
        eaa_records = cursor.fetchall()
        
        print("=== EAA PAYMENTS RECORDS ===")
        print("{:<5} {:<15} {:<25} {:<10} {:<15}".format("ID", "SSN", "Name", "Amount", "Payment ID"))
        print("-" * 70)
        for record in eaa_records:
            print("{:<5} {:<15} {:<25} {:<10} {:<15}".format(
                record[0], record[1], record[2][:25], f"${float(record[3]):.2f}", record[4]
            ))
        
        # Check for matching records in customers table
        print("\n=== CHECKING FOR MATCHING RECORDS IN CUSTOMERS TABLE ===")
        
        for record in eaa_records:
            ssn = record[1]
            cursor.execute("SELECT CustomerID, PrimaryClientID, FirstName, LastName, EmployerID FROM customers WHERE SocSec = %s", (ssn,))
            matches = cursor.fetchall()
            
            print(f"\nEAA Record: ID={record[0]}, SSN={ssn}, Name={record[2]}")
            
            if matches:
                print(f"  Found {len(matches)} matching customer records:")
                print("  {:<10} {:<10} {:<15} {:<15} {:<10}".format(
                    "CustID", "ClientID", "FirstName", "LastName", "EmployerID"
                ))
                print("  " + "-" * 60)
                for match in matches:
                    print("  {:<10} {:<10} {:<15} {:<15} {:<10}".format(
                        match[0], match[1], match[2][:15], match[3][:15], match[4]
                    ))
            else:
                print("  No matching customer records found.")
        
        # Check for records with employerid = 160
        cursor.execute("SELECT COUNT(*) FROM customers WHERE EmployerID = 160")
        employer_count = cursor.fetchone()[0]
        print(f"\nTotal records in customers table with EmployerID = 160: {employer_count}")
        
        if employer_count > 0:
            cursor.execute("SELECT CustomerID, PrimaryClientID, FirstName, LastName, SocSec FROM customers WHERE EmployerID = 160 LIMIT 5")
            sample_records = cursor.fetchall()
            
            print("\nSample records with EmployerID = 160:")
            print("{:<10} {:<10} {:<15} {:<15} {:<15}".format(
                "CustID", "ClientID", "FirstName", "LastName", "SSN"
            ))
            print("-" * 65)
            for record in sample_records:
                print("{:<10} {:<10} {:<15} {:<15} {:<15}".format(
                    record[0], record[1], record[2][:15], record[3][:15], record[4]
                ))
    
    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
