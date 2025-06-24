#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Process and Import EAA Payment Data
-----------------------------------
This script processes Word documents and imports them to the database.
Author: Lil Claudy Flossy
"""

import os
import sys
import argparse
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eaa_data_processor import extract_data_from_docx, save_to_csv
from eaa_db_importer import import_csv_to_database, update_client_ids, create_table_if_not_exists
from utils.MySQLConnectionManager import MySQLConnectionManager


def setup_logging(log_file=None):
    """Set up logging configuration."""
    if not log_file:
        log_file = f"process_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def process_docx_to_csv(docx_file):
    """
    Process a Word document to CSV.
    
    Args:
        docx_file (str): Path to the Word document
        
    Returns:
        str: Path to the generated CSV file or None if failed
    """
    logger = logging.getLogger(__name__)
    
    # Generate output CSV filename
    base_name = os.path.splitext(os.path.basename(docx_file))[0]
    csv_file = os.path.join(os.path.dirname(docx_file), f"{base_name}.csv")
    
    logger.info(f"Processing {docx_file}")
    
    # Extract data from Word document
    data = extract_data_from_docx(docx_file)
    
    if data:
        logger.info(f"Extracted {len(data['employee_data'])} records")
        logger.info(f"Company: {data['company']}")
        logger.info(f"Report Date: {data['report_date']}")
        logger.info(f"Total Amount: ${data['total_amount']}")
        
        # Save to CSV
        if save_to_csv(data, csv_file):
            logger.info(f"CSV file created: {csv_file}")
            return csv_file
        else:
            logger.error("Failed to save CSV file")
            return None
    else:
        logger.error("Failed to extract data from Word document")
        return None


def import_to_database(csv_file, environment='dev'):
    """
    Import CSV file to the database.
    
    Args:
        csv_file (str): Path to the CSV file
        environment (str): Database environment to use
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Connect to database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync(environment)
    
    if not connection:
        logger.error(f"Failed to connect to {environment} database")
        return False
    
    try:
        # Ensure table exists
        if not create_table_if_not_exists(connection):
            logger.error("Failed to create/verify eaa_payments table")
            return False
        
        # Import CSV to database
        logger.info(f"Importing {csv_file} to database")
        if import_csv_to_database(csv_file, connection):
            logger.info("Import successful")
            
            # Update client IDs
            logger.info("Updating client IDs...")
            updated_count = update_client_ids(connection)
            logger.info(f"Updated {updated_count} client IDs")
            
            return True
        else:
            logger.error("Import failed")
            return False
            
    finally:
        db_manager.close_connection(connection)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Process and import EAA payment data')
    parser.add_argument('input_file', help='Word document (.docx) or CSV file to process')
    parser.add_argument('--env', default='dev', choices=['dev', 'prod'], 
                       help='Database environment (default: dev)')
    parser.add_argument('--skip-process', action='store_true',
                       help='Skip processing, import existing CSV directly')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    # Determine file type and process accordingly
    if args.input_file.endswith('.csv') or args.skip_process:
        # Direct CSV import
        csv_file = args.input_file
        logger.info(f"Importing CSV file directly: {csv_file}")
    elif args.input_file.endswith('.docx'):
        # Process Word document first
        csv_file = process_docx_to_csv(args.input_file)
        if not csv_file:
            logger.error("Failed to process Word document")
            return 1
    else:
        logger.error("Input file must be .docx or .csv")
        return 1
    
    # Import to database
    if import_to_database(csv_file, args.env):
        logger.info("Process completed successfully")
        return 0
    else:
        logger.error("Process failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())