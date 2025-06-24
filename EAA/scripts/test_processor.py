#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_processor.py
----------------
Simplified test script for extracting data from EAA Word documents
Path: EAA/scripts/test_processor.py
Created: 2025-04-04
Modified: 2025-04-04

Variables:
- log_file: Path to the log file
- input_file: Path to the input Word document
- output_file: Path to the output CSV file
"""

import os
import re
import csv
import logging
from datetime import datetime
import traceback

# Setup logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_processor.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def mock_extract_data(file_path):
    """
    Mock function to simulate extracting data from a Word document.
    
    Args:
        file_path (str): Path to the Word document
        
    Returns:
        dict: Dictionary containing extracted data
    """
    logging.info(f"Simulating data extraction from {file_path}")
    
    # Sample mock data
    mock_data = {
        'company': 'Corporate Jewelers Inc',
        'report_date': '2025-03-14',
        'total_amount': '5000.00',
        'employee_data': [
            {
                'ssn': '123456789',
                'name': 'John Smith',
                'amount': '1500.00',
                'company': 'Corporate Jewelers Inc',
                'report_date': '2025-03-14'
            },
            {
                'ssn': '987654321',
                'name': 'Jane Doe',
                'amount': '1800.00',
                'company': 'Corporate Jewelers Inc',
                'report_date': '2025-03-14'
            },
            {
                'ssn': '456789123',
                'name': 'Robert Johnson',
                'amount': '1700.00',
                'company': 'Corporate Jewelers Inc',
                'report_date': '2025-03-14'
            }
        ]
    }
    
    return mock_data

def save_to_csv(data, output_file):
    """
    Save extracted data to a CSV file.
    
    Args:
        data (dict): Dictionary containing extracted data
        output_file (str): Path to the output CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not data or 'employee_data' not in data or not data['employee_data']:
            logging.error("No data to save.")
            return False
        
        # Write data to CSV
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['ssn', 'name', 'amount', 'company', 'report_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for employee in data['employee_data']:
                writer.writerow(employee)
        
        logging.info(f"Data saved to {output_file}")
        return True
    
    except Exception as e:
        error_msg = str(e)
        trace = traceback.format_exc()
        logging.error(f"Error saving data to CSV: {error_msg}\n{trace}")
        return False

def main():
    """Main function to process Word documents and convert to CSV."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output files
    input_file = os.path.join(os.path.dirname(script_dir), 'CorporateJewelers031425.docx')
    output_file = os.path.join(os.path.dirname(script_dir), 'test_output.csv')
    
    logging.info(f"Processing {input_file} -> {output_file}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        print(f"Input file not found: {input_file}")
        return False
    
    # Extract data from Word document (mock function for now)
    data = mock_extract_data(input_file)
    
    if data:
        # Save data to CSV
        if save_to_csv(data, output_file):
            logging.info(f"Successfully processed {input_file}")
            print(f"Successfully processed {input_file}")
            print(f"Output saved to {output_file}")
            
            # Display summary
            print("\nSummary of extracted data:")
            print(f"Company: {data['company']}")
            print(f"Report Date: {data['report_date']}")
            print(f"Total Amount: ${data['total_amount']}")
            print(f"Employee Records: {len(data['employee_data'])}")
            
            return True
        else:
            logging.error(f"Failed to save data to CSV")
            print(f"Failed to save data to CSV")
            return False
    else:
        logging.error("Failed to extract data from the Word document")
        print("Failed to extract data from the Word document")
        return False

if __name__ == "__main__":
    main()
