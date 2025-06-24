#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Update Client IDs Script
----------------------
This script updates the clientID field in the eaa_payments table by matching SSNs with the customers table.
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
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'eaa_update.log')),
        logging.StreamHandler()
    ]
)

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

def update_client_ids(connection):
    """
    Update the clientID in the eaa_payments table by matching SSNs with the customers table.
    
    Args:
        connection: MySQL database connection
    
    Returns:
        int: Number of records updated
    """
    cursor = connection.cursor()
    
    try:
        # First update: Match SSNs with customers where EmployerID is one of the specified values
        update_query = """
        UPDATE eaa_payments ep
        JOIN customers c ON ep.ssn = c.SocSec AND c.EmployerID IN (160, 199, 225)
        SET ep.clientID = c.PrimaryClientID
        WHERE ep.clientID IS NULL
        """
        cursor.execute(update_query)
        connection.commit()
        
        first_update_count = cursor.rowcount
        logging.info(f"Updated {first_update_count} records with EmployerID in (160, 199, 225)")
        
        # Second update: Match any remaining SSNs with customers regardless of EmployerID
        second_update_query = """
        UPDATE eaa_payments ep
        JOIN customers c ON ep.ssn = c.SocSec
        SET ep.clientID = c.PrimaryClientID
        WHERE ep.clientID IS NULL
        """
        cursor.execute(second_update_query)
        connection.commit()
        
        second_update_count = cursor.rowcount
        logging.info(f"Updated {second_update_count} records with any EmployerID")
        
        # Third update: Handle SSNs that might be stored without a leading zero
        # Get remaining unmatched records
        cursor.execute("SELECT id, ssn FROM eaa_payments WHERE clientID IS NULL")
        unmatched_records = cursor.fetchall()
        
        third_update_count = 0
        for record_id, ssn in unmatched_records:
            # If SSN starts with a zero, try matching without the leading zero
            if ssn.startswith('0'):
                ssn_without_leading_zero = ssn[1:]
                cursor.execute(
                    "SELECT PrimaryClientID FROM customers WHERE SocSec = %s LIMIT 1", 
                    (ssn_without_leading_zero,)
                )
                result = cursor.fetchone()
                
                if result:
                    client_id = result[0]
                    cursor.execute(
                        "UPDATE eaa_payments SET clientID = %s WHERE id = %s",
                        (client_id, record_id)
                    )
                    connection.commit()
                    third_update_count += 1
                    logging.info(f"Updated record ID {record_id} with SSN {ssn} to match SSN without leading zero {ssn_without_leading_zero}, ClientID: {client_id}")
            
            # Also try the reverse - if the SSN in customers might be stored with an extra leading zero
            cursor.execute(
                "SELECT PrimaryClientID FROM customers WHERE SocSec = %s LIMIT 1", 
                ('0' + ssn,)
            )
            result = cursor.fetchone()
            
            if result:
                client_id = result[0]
                cursor.execute(
                    "UPDATE eaa_payments SET clientID = %s WHERE id = %s",
                    (client_id, record_id)
                )
                connection.commit()
                third_update_count += 1
                logging.info(f"Updated record ID {record_id} with SSN {ssn} to match SSN with added leading zero {'0' + ssn}, ClientID: {client_id}")
        
        logging.info(f"Updated {third_update_count} records by handling leading zeros")
        
        # Special case for Kenya Brown (clientID: 1071)
        cursor.execute(
            "UPDATE eaa_payments SET clientID = 1071 WHERE ssn = '071584406' AND clientID IS NULL"
        )
        connection.commit()
        
        kenya_brown_update = cursor.rowcount
        if kenya_brown_update > 0:
            logging.info(f"Updated Kenya Brown's record with clientID 1071")
            third_update_count += kenya_brown_update
        
        total_updated = first_update_count + second_update_count + third_update_count
        logging.info(f"Total records updated: {total_updated}")
        
        return total_updated
    
    except mysql.connector.Error as err:
        logging.error(f"Error updating client IDs: {err}")
        connection.rollback()
        return 0
    
    finally:
        cursor.close()

def main():
    """Main function to update client IDs."""
    logging.info("Starting client ID update process")
    
    # Connect to the SPIDERSYNC database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        logging.error("Failed to connect to the SPIDERSYNC database")
        return
    
    try:
        # Update client IDs
        updated_count = update_client_ids(connection)
        
        # Check the updated records
        cursor = connection.cursor()
        cursor.execute("SELECT id, ssn, name, clientID FROM eaa_payments WHERE clientID IS NOT NULL")
        updated_records = cursor.fetchall()
        
        logging.info(f"Successfully updated {updated_count} records")
        logging.info(f"Records with clientID: {len(updated_records)}")
        
        # Display the first 5 updated records
        if updated_records:
            logging.info("First 5 updated records:")
            for i, record in enumerate(updated_records[:5]):
                logging.info(f"  ID: {record[0]}, SSN: {record[1]}, Name: {record[2]}, ClientID: {record[3]}")
    
    finally:
        # Close the database connection
        if connection.is_connected():
            connection.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    main()
