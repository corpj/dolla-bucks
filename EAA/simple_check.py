#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Check Script
----------------
This script performs a simple check of the customers table and matching records.
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

def main():
    """Perform a simple check of the customers table and matching records."""
    # Connect to the SPIDERSYNC database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        print("Failed to connect to the SPIDERSYNC database.")
        return
    
    try:
        cursor = connection.cursor()
        
        # Check column names in customers table
        cursor.execute("SHOW COLUMNS FROM customers")
        columns = [column[0].lower() for column in cursor.fetchall()]
        print("Columns in customers table:")
        for column in columns:
            print(f"  - {column}")
        
        # Check if required columns exist
        required_columns = ['socsec', 'primaryclientid', 'employerid']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"\nWARNING: The following required columns are missing: {', '.join(missing_columns)}")
            return
        
        # Check for case sensitivity in column names
        print("\nChecking case sensitivity in column names:")
        cursor.execute("SHOW COLUMNS FROM customers WHERE Field LIKE 'SocSec' OR Field LIKE 'PrimaryClientID' OR Field LIKE 'EmployerID'")
        case_sensitive_columns = cursor.fetchall()
        for column in case_sensitive_columns:
            print(f"  - {column[0]}")
        
        # Get SSNs from eaa_payments
        cursor.execute("SELECT ssn FROM eaa_payments LIMIT 5")
        ssns = [row[0] for row in cursor.fetchall()]
        
        if not ssns:
            print("\nNo SSNs found in eaa_payments table.")
            return
        
        print(f"\nSample SSNs from eaa_payments table:")
        for ssn in ssns:
            print(f"  - {ssn}")
        
        # Check for matching records with specific SSNs
        for ssn in ssns:
            print(f"\nChecking for matches with SSN: {ssn}")
            cursor.execute("SELECT CustomerID, PrimaryClientID, FirstName, LastName, EmployerID, SocSec FROM customers WHERE SocSec = %s LIMIT 5", (ssn,))
            matches = cursor.fetchall()
            
            if matches:
                print(f"  Found {len(matches)} matches:")
                for match in matches:
                    print(f"  - CustomerID: {match[0]}, PrimaryClientID: {match[1]}, Name: {match[2]} {match[3]}, EmployerID: {match[4]}, SocSec: {match[5]}")
            else:
                print("  No matches found.")
        
        # Test the update query
        print("\nTesting update query:")
        update_query = """
        UPDATE eaa_payments ep
        JOIN customers c ON ep.ssn = c.SocSec AND c.EmployerID = 160
        SET ep.clientID = c.PrimaryClientID
        WHERE ep.clientID IS NULL
        """
        
        # Execute the update query
        cursor.execute(update_query)
        connection.commit()
        rows_affected = cursor.rowcount
        
        print(f"Update query affected {rows_affected} rows.")
        
        # Check if any records were updated
        cursor.execute("SELECT id, ssn, clientID FROM eaa_payments WHERE clientID IS NOT NULL")
        updated_records = cursor.fetchall()
        
        if updated_records:
            print(f"\nUpdated records ({len(updated_records)}):")
            for record in updated_records:
                print(f"  - ID: {record[0]}, SSN: {record[1]}, ClientID: {record[2]}")
        else:
            print("\nNo records were updated.")
    
    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
