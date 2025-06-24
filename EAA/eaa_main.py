#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EAA Main Processor
-----------------
This script orchestrates the entire process of extracting data from EAA Word documents,
converting to CSV, and importing into the SPIDERSYNC database.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'eaa_process.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import local modules
from eaa_data_processor import extract_data_from_docx, save_to_csv
from eaa_db_importer import import_csv_to_database

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager


def process_eaa_document(docx_file):
    """
    Process an EAA Word document: extract data, save to CSV, and import to database.
    
    Args:
        docx_file (str): Path to the Word document
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the directory and filename
        file_dir = os.path.dirname(docx_file)
        file_name = os.path.basename(docx_file)
        file_base = os.path.splitext(file_name)[0]
        
        # Define output CSV file
        csv_file = os.path.join(file_dir, f"{file_base}.csv")
        
        logger.info(f"Processing document: {docx_file}")
        
        # Step 1: Extract data from Word document
        logger.info("Step 1: Extracting data from Word document")
        data = extract_data_from_docx(docx_file)
        
        if not data:
            logger.error("Failed to extract data from the Word document.")
            return False
        
        # Step 2: Save data to CSV
        logger.info("Step 2: Saving data to CSV")
        if not save_to_csv(data, csv_file):
            logger.error("Failed to save data to CSV.")
            return False
        
        # Step 3: Import data to database
        logger.info("Step 3: Importing data to database")
        
        # Connect to the SPIDERSYNC database
        db_manager = MySQLConnectionManager()
        connection = db_manager.connect_to_spidersync()
        
        if not connection:
            logger.error("Failed to connect to the SPIDERSYNC database.")
            return False
        
        try:
            # Import data from CSV to database
            if not import_csv_to_database(csv_file, connection):
                logger.error("Failed to import data to database.")
                return False
        
        finally:
            # Close the database connection
            if connection.is_connected():
                connection.close()
                logger.info("Database connection closed.")
        
        logger.info(f"Successfully processed document: {docx_file}")
        return True
    
    except Exception as e:
        logger.exception(f"Error processing document {docx_file}: {e}")
        return False


def main():
    """Main function to process all EAA Word documents in the directory."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input file
    input_file = os.path.join(script_dir, 'CorporateJewelers031425.docx')
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    
    # Process the document
    if process_eaa_document(input_file):
        logger.info("Document processing completed successfully.")
    else:
        logger.error("Document processing failed.")


if __name__ == "__main__":
    main()
