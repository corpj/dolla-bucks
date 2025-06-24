#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check Customers Table Script
--------------------------
This script checks the structure of the customers table and looks for matching records.
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

def main():
    """Check the structure of the customers table and look for matching records."""
    # Connect to the SPIDERSYNC database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        print("Failed to connect to the SPIDERSYNC database.")
        return
    
    try:
        cursor = connection.cursor()
        
        # Check if the customers table exists
        cursor.execute("SHOW TABLES LIKE 'customers'")
        if not cursor.fetchone():
            print("The customers table does not exist.")
            return
        
        # Get the table structure
        cursor.execute("DESCRIBE customers")
        print("=== CUSTOMERS TABLE STRUCTURE ===")
        
        # Store column names and details
        columns = []
        column_details = []
        for column in cursor.fetchall():
            columns.append(column[0])
            column_details.append({
                'name': column[0],
                'type': column[1],
                'null': column[2],
                'key': column[3] or 'None'
            })
        
        # Print column details in a more controlled way
        print("{:<20} {:<15} {:<10} {:<10}".format("Column", "Type", "Null", "Key"))
        print("-" * 60)
        for col in column_details:
            print("{:<20} {:<15} {:<10} {:<10}".format(
                col['name'], col['type'], col['null'], col['key']
            ))
        
        # Check if the required columns exist
        required_columns = ['socsec', 'primaryclientID', 'employerid']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"\nWARNING: The following required columns are missing: {', '.join(missing_columns)}")
            return
        
        # Get SSNs from eaa_payments
        cursor.execute("SELECT ssn FROM eaa_payments")
        ssns = [row[0] for row in cursor.fetchall()]
        
        if not ssns:
            print("\nNo SSNs found in eaa_payments table.")
            return
        
        print(f"\nFound {len(ssns)} SSNs in eaa_payments table.")
        
        # Check for matching records with employerid = 160
        ssn_placeholders = ', '.join(['%s'] * len(ssns))
        query = f"""
        SELECT 
            socsec, 
            primaryclientID, 
            firstname, 
            lastname, 
            employerid 
        FROM 
            customers 
        WHERE 
            socsec IN ({ssn_placeholders}) 
            AND employerid = 160
        """
        
        cursor.execute(query, ssns)
        specific_matches = cursor.fetchall()
        
        print(f"\nFound {len(specific_matches)} matches with employerid = 160:")
        if specific_matches:
            print("{:<15} {:<15} {:<15} {:<15} {:<10}".format(
                "SSN", "ClientID", "First Name", "Last Name", "EmployerID"
            ))
            print("-" * 70)
            for match in specific_matches:
                print("{:<15} {:<15} {:<15} {:<15} {:<10}".format(
                    match[0], str(match[1]), match[2], match[3], str(match[4])
                ))
        else:
            print("No matches found with employerid = 160.")
        
        # Check for matching records with any employerid
        query = f"""
        SELECT 
            socsec, 
            primaryclientID, 
            firstname, 
            lastname, 
            employerid 
        FROM 
            customers 
        WHERE 
            socsec IN ({ssn_placeholders})
        """
        
        cursor.execute(query, ssns)
        all_matches = cursor.fetchall()
        
        print(f"\nFound {len(all_matches)} matches with any employerid:")
        if all_matches:
            print("{:<15} {:<15} {:<15} {:<15} {:<10}".format(
                "SSN", "ClientID", "First Name", "Last Name", "EmployerID"
            ))
            print("-" * 70)
            for match in all_matches:
                print("{:<15} {:<15} {:<15} {:<15} {:<10}".format(
                    match[0], str(match[1]), match[2], match[3], str(match[4])
                ))
        else:
            print("No matches found with any employerid.")
        
        # Check if the update query would work
        print("\nTesting update query:")
        test_query = """
        SELECT 
            ep.id, 
            ep.ssn, 
            c.primaryclientID 
        FROM 
            eaa_payments ep
        JOIN 
            customers c ON ep.ssn = c.socsec AND c.employerid = 160
        LIMIT 5
        """
        
        cursor.execute(test_query)
        test_results = cursor.fetchall()
        
        if test_results:
            print("Update query would work. Sample results:")
            for result in test_results:
                print(f"  ID: {result[0]}, SSN: {result[1]}, ClientID: {result[2]}")
        else:
            print("Update query would not work. No matching records found.")
    
    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
