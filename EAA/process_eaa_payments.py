#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Process EAA Payments
--------------------
This script processes EAA Word documents from PaymentFiles/EAA directory,
converts them to CSV, imports to database, and archives processed files.
Author: Lil Claudy Flossy
"""

import os
import sys
import argparse
import logging
import shutil
from datetime import datetime
import glob

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the processor and importer modules
from eaa_data_processor import extract_data_from_docx, save_to_csv
from eaa_db_importer import import_csv_to_database, update_client_ids, archive_file
from utils.MySQLConnectionManager import MySQLConnectionManager

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f'process_eaa_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)


def get_docx_files(directory):
    """
    Get all DOCX files from the specified directory.
    
    Args:
        directory (str): Directory to search for DOCX files
    
    Returns:
        list: List of DOCX file paths
    """
    docx_pattern = os.path.join(directory, "*.docx")
    return glob.glob(docx_pattern)


def process_docx_to_csv(docx_file, output_dir=None):
    """
    Process a DOCX file and convert it to CSV.
    
    Args:
        docx_file (str): Path to the DOCX file
        output_dir (str): Directory to save CSV file (optional)
    
    Returns:
        str: Path to the created CSV file, or None if failed
    """
    try:
        # Extract data from Word document
        logging.info(f"Extracting data from {docx_file}")
        data = extract_data_from_docx(docx_file)
        
        if not data:
            logging.error(f"Failed to extract data from {docx_file}")
            return None
        
        # Generate CSV filename based on DOCX filename
        base_name = os.path.splitext(os.path.basename(docx_file))[0]
        # Clean up the filename - remove spaces and standardize format
        base_name = base_name.replace(" ", "")
        
        # Determine output directory
        if output_dir:
            csv_dir = output_dir
        else:
            csv_dir = os.path.dirname(docx_file)
        
        csv_file = os.path.join(csv_dir, f"{base_name}.csv")
        
        # Save data to CSV
        save_to_csv(data, csv_file)
        logging.info(f"Created CSV file: {csv_file}")
        
        return csv_file
        
    except Exception as e:
        logging.error(f"Error processing {docx_file}: {e}")
        return None


def main():
    """Main function to process EAA payments workflow."""
    parser = argparse.ArgumentParser(
        description="Process EAA payment documents: DOCX → CSV → Database"
    )
    parser.add_argument(
        "file", 
        nargs="?", 
        help="Specific DOCX or CSV file to process (optional)"
    )
    parser.add_argument(
        "--directory", "-d",
        default="../PaymentFiles/EAA",
        help="Directory to search for files (default: ../PaymentFiles/EAA)"
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
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Only convert DOCX to CSV, do not import to database"
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
        # Get all DOCX files from directory
        search_dir = os.path.join(script_dir, args.directory)
        if os.path.exists(search_dir):
            files_to_process = get_docx_files(search_dir)
            if not files_to_process:
                logging.info(f"No DOCX files found in {search_dir}")
                return
        else:
            logging.error(f"Directory not found: {search_dir}")
            return
    
    logging.info(f"Found {len(files_to_process)} file(s) to process")
    
    # Process workflow
    successful_conversions = []
    successful_imports = []
    failed_files = []
    
    # Connect to database if needed
    connection = None
    if not args.csv_only:
        db_manager = MySQLConnectionManager()
        connection = db_manager.connect_to_spidersync()
        
        if not connection:
            logging.error("Failed to connect to the SPIDERSYNC database.")
            return
    
    for docx_file in files_to_process:
        logging.info(f"\nProcessing: {docx_file}")
        
        try:
            # Convert DOCX to CSV
            csv_file = process_docx_to_csv(docx_file)
            
            if csv_file:
                successful_conversions.append((docx_file, csv_file))
                
                # Import to database if requested
                if not args.csv_only and connection:
                    if import_csv_to_database(csv_file, connection):
                        # Update client IDs
                        logging.info("Updating client IDs...")
                        updated_count = update_client_ids(connection)
                        logging.info(f"Updated {updated_count} client IDs")
                        
                        successful_imports.append(csv_file)
                        
                        # Archive files if requested
                        if not args.no_archive:
                            archive_dir = os.path.join(script_dir, args.archive)
                            
                            # Archive DOCX file
                            if archive_file(docx_file, archive_dir):
                                logging.info(f"Archived DOCX: {docx_file}")
                            
                            # Archive CSV file
                            if archive_file(csv_file, archive_dir):
                                logging.info(f"Archived CSV: {csv_file}")
                    else:
                        logging.error(f"Failed to import {csv_file} to database")
                        failed_files.append(csv_file)
                        
                # Archive DOCX file if only converting to CSV
                elif args.csv_only and not args.no_archive:
                    archive_dir = os.path.join(script_dir, args.archive)
                    if archive_file(docx_file, archive_dir):
                        logging.info(f"Archived DOCX: {docx_file}")
            else:
                failed_files.append(docx_file)
                
        except Exception as e:
            logging.error(f"Error processing {docx_file}: {e}")
            failed_files.append(docx_file)
    
    # Close database connection
    if connection and connection.is_connected():
        connection.close()
        logging.info("Database connection closed.")
    
    # Summary
    logging.info("\n" + "=" * 50)
    logging.info("PROCESSING SUMMARY")
    logging.info("=" * 50)
    logging.info(f"Total files processed: {len(files_to_process)}")
    logging.info(f"Successful conversions: {len(successful_conversions)}")
    if not args.csv_only:
        logging.info(f"Successful imports: {len(successful_imports)}")
    logging.info(f"Failed files: {len(failed_files)}")
    
    if successful_conversions:
        logging.info("\nSuccessfully converted:")
        for docx, csv in successful_conversions:
            logging.info(f"  - {os.path.basename(docx)} → {os.path.basename(csv)}")
    
    if failed_files:
        logging.info("\nFailed to process:")
        for f in failed_files:
            logging.info(f"  - {os.path.basename(f)}")


if __name__ == "__main__":
    main()