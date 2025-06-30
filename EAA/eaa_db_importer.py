#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EAA Database Importer
--------------------
This script imports EAA payment data from CSV files into the SPIDERSYNC database.
"""

import os
import sys
import csv
import pandas as pd
from datetime import datetime
import logging
import mysql.connector
import argparse
import shutil
import glob

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f'eaa_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)


def create_table_if_not_exists(connection):
    """
    Create the EAA payments table if it doesn't exist.
    
    Args:
        connection: MySQL database connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor = connection.cursor()
        
        # Create table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS eaa_payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ssn CHAR(9) NOT NULL,
            name VARCHAR(255) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            company VARCHAR(255) NOT NULL,
            report_date DATE NOT NULL,
            import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            clientID INT NULL,
            payment_id VARCHAR(15) NOT NULL,
            payment_applied INT DEFAULT 0,
            date_applied DATETIME NULL,
            INDEX idx_ssn (ssn),
            FULLTEXT INDEX idx_name (name),
            UNIQUE INDEX idx_payment_id (payment_id)
        )
        """
        
        cursor.execute(create_table_query)
        connection.commit()
        cursor.close()
        
        return True
    
    except Exception as e:
        print(f"Error creating table: {e}")
        return False


def import_csv_to_database(csv_file, connection):
    """
    Import data from a CSV file into the database.
    
    Args:
        csv_file (str): Path to the CSV file
        connection: MySQL database connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        # Ensure SSNs are properly formatted with leading zeros
        df['ssn'] = df['ssn'].astype(str).str.zfill(9)
        
        # Generate payment_id from last 4 of SSN and date (XXXX_MMDDYYYY)
        df['payment_id'] = df.apply(
            lambda row: f"{row['ssn'][-4:]}_{pd.to_datetime(row['report_date']).strftime('%m%d%Y')}", 
            axis=1
        )
        
        # Ensure the table exists
        if not create_table_if_not_exists(connection):
            return False
        
        # Insert data into the database
        cursor = connection.cursor()
        
        # Prepare insert query
        insert_query = """
        INSERT INTO eaa_payments (ssn, name, amount, company, report_date, payment_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Insert each row from the CSV
        records_inserted = 0
        for _, row in df.iterrows():
            data = (
                row['ssn'],
                row['name'],
                float(row['amount']),
                row['company'],
                row['report_date'],
                row['payment_id']
            )
            
            cursor.execute(insert_query, data)
            records_inserted += 1
        
        # Commit the transaction
        connection.commit()
        cursor.close()
        
        print(f"Successfully imported {records_inserted} records into the database.")
        return True
    
    except Exception as e:
        print(f"Error importing data to database: {e}")
        return False


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


def archive_file(file_path, archive_dir):
    """
    Archive a file to the specified directory.
    
    Args:
        file_path (str): Path to the file to archive
        archive_dir (str): Directory to move the file to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(archive_dir, exist_ok=True)
        filename = os.path.basename(file_path)
        archive_path = os.path.join(archive_dir, filename)
        
        # If file already exists in archive, add timestamp
        if os.path.exists(archive_path):
            base, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base}_{timestamp}{ext}"
            archive_path = os.path.join(archive_dir, filename)
        
        shutil.move(file_path, archive_path)
        logging.info(f"Archived {file_path} to {archive_path}")
        
        # Check for Zone.Identifier file
        zone_file = f"{file_path}:Zone.Identifier"
        if os.path.exists(zone_file):
            zone_archive_path = f"{archive_path}:Zone.Identifier"
            try:
                shutil.move(zone_file, zone_archive_path)
                logging.info(f"Archived Zone.Identifier file")
            except Exception as e:
                logging.warning(f"Could not archive Zone.Identifier file: {e}")
        
        return True
    except Exception as e:
        logging.error(f"Error archiving file: {e}")
        return False


def get_csv_files(directory):
    """
    Get all CSV files from the specified directory.
    
    Args:
        directory (str): Directory to search for CSV files
    
    Returns:
        list: List of CSV file paths
    """
    csv_pattern = os.path.join(directory, "*.csv")
    return glob.glob(csv_pattern)


def main():
    """Main function to import CSV data into the database."""
    parser = argparse.ArgumentParser(description="Import EAA payment data from CSV files")
    parser.add_argument(
        "file", 
        nargs="?", 
        help="Specific CSV file to import (optional)"
    )
    parser.add_argument(
        "--directory", "-d",
        default="../PaymentFiles/EAA",
        help="Directory to search for CSV files (default: ../PaymentFiles/EAA)"
    )
    parser.add_argument(
        "--archive", "-a",
        default="../PaymentFiles/EAA/archive",
        help="Archive directory for processed files (default: ../PaymentFiles/EAA/archive)"
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Do not archive files after processing"
    )
    
    args = parser.parse_args()
    
    # Get the base directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine files to process
    files_to_process = []
    
    if args.file:
        # Specific file provided
        if os.path.exists(args.file):
            files_to_process = [args.file]
        else:
            # Check in the default directory
            file_path = os.path.join(script_dir, args.directory, args.file)
            if os.path.exists(file_path):
                files_to_process = [file_path]
            else:
                logging.error(f"File not found: {args.file}")
                return
    else:
        # Get all CSV files from directory
        search_dir = os.path.join(script_dir, args.directory)
        if os.path.exists(search_dir):
            files_to_process = get_csv_files(search_dir)
            if not files_to_process:
                logging.info(f"No CSV files found in {search_dir}")
                return
        else:
            logging.error(f"Directory not found: {search_dir}")
            return
    
    logging.info(f"Found {len(files_to_process)} file(s) to process")
    
    # Connect to the SPIDERSYNC database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        logging.error("Failed to connect to the SPIDERSYNC database.")
        return
    
    # Process each file
    successful_imports = []
    failed_imports = []
    
    for csv_file in files_to_process:
        logging.info(f"\nProcessing: {csv_file}")
        
        try:
            # Import data from CSV to database
            if import_csv_to_database(csv_file, connection):
                # Update client IDs
                logging.info("Updating client IDs...")
                updated_count = update_client_ids(connection)
                logging.info(f"Updated {updated_count} client IDs")
                
                successful_imports.append(csv_file)
                
                # Archive the file if requested
                if not args.no_archive:
                    archive_dir = os.path.join(script_dir, args.archive)
                    if archive_file(csv_file, archive_dir):
                        logging.info(f"Successfully archived {csv_file}")
                    else:
                        logging.warning(f"Failed to archive {csv_file}")
            else:
                failed_imports.append(csv_file)
                
        except Exception as e:
            logging.error(f"Error processing {csv_file}: {e}")
            failed_imports.append(csv_file)
    
    # Close the database connection
    if connection.is_connected():
        connection.close()
        logging.info("Database connection closed.")
    
    # Summary
    logging.info("\n" + "=" * 50)
    logging.info("IMPORT SUMMARY")
    logging.info("=" * 50)
    logging.info(f"Total files processed: {len(files_to_process)}")
    logging.info(f"Successful imports: {len(successful_imports)}")
    logging.info(f"Failed imports: {len(failed_imports)}")
    
    if successful_imports:
        logging.info("\nSuccessfully imported:")
        for f in successful_imports:
            logging.info(f"  - {os.path.basename(f)}")
    
    if failed_imports:
        logging.info("\nFailed to import:")
        for f in failed_imports:
            logging.info(f"  - {os.path.basename(f)}")


if __name__ == "__main__":
    main()
