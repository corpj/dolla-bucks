#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EAA Data Processor
-----------------
This script extracts data from EAA Word documents, processes it, and converts it to CSV format.
"""

import os
import re
import csv
import pandas as pd
from datetime import datetime
import docx2txt
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager


def extract_data_from_docx(file_path):
    """
    Extract data from a Word document.
    
    Args:
        file_path (str): Path to the Word document
        
    Returns:
        dict: Dictionary containing extracted data
    """
    try:
        # Extract text from the Word document
        text = docx2txt.process(file_path)
        
        # Extract company name
        company_match = re.search(r'Company:\s+(.*)', text)
        company = company_match.group(1).strip() if company_match else None
        
        # Extract date
        date_match = re.search(r'For:\s+(\d{2}/\d{2}/\d{4})', text)
        report_date = date_match.group(1).strip() if date_match else None
        
        # Convert date to standard format (YYYY-MM-DD)
        if report_date:
            try:
                date_obj = datetime.strptime(report_date, '%m/%d/%Y')
                report_date = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                print(f"Warning: Could not parse date {report_date}")
        
        # Extract total amount
        total_amount_match = re.search(r'Total Amount:\s+\$([0-9,.]+)', text)
        total_amount = total_amount_match.group(1).replace(',', '') if total_amount_match else None
        
        # Extract employee data
        # Look for patterns of SSN, Name, and Amount
        employee_data = []
        
        # Split text into lines for processing
        lines = text.split('\n')
        
        # Find the line with headers
        header_line_idx = None
        for i, line in enumerate(lines):
            if 'Soc Sec No' in line and 'Member Name' in line and 'Premium Amount' in line:
                header_line_idx = i
                break
        
        if header_line_idx is not None:
            # Process employee data lines
            i = header_line_idx + 1
            while i < len(lines):
                line = lines[i].strip()
                
                # Check if we've reached the total line
                if 'Total Amount:' in line:
                    break
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Try to match SSN pattern (9 digits, possibly with hyphens)
                ssn_match = re.match(r'^\s*(\d{9}|\d{3}-\d{2}-\d{4})', line)
                
                if ssn_match:
                    ssn = ssn_match.group(1).replace('-', '')
                    
                    # Ensure SSN is 9 digits with leading zeros
                    ssn = ssn.zfill(9)
                    
                    # Extract the rest of the line
                    rest_of_line = line[ssn_match.end():].strip()
                    
                    # Try to extract name and amount
                    # This assumes the format is: SSN Name $Amount
                    amount_match = re.search(r'\$([0-9,.]+)$', rest_of_line)
                    
                    if amount_match:
                        amount = amount_match.group(1).replace(',', '')
                        
                        # Name is everything between SSN and amount
                        name = rest_of_line[:amount_match.start()].strip()
                        
                        employee_data.append({
                            'ssn': ssn,
                            'name': name,
                            'amount': amount,
                            'company': company,
                            'report_date': report_date
                        })
                
                i += 1
        
        return {
            'company': company,
            'report_date': report_date,
            'total_amount': total_amount,
            'employee_data': employee_data
        }
    
    except Exception as e:
        print(f"Error extracting data from {file_path}: {e}")
        return None


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
            print("No data to save.")
            return False
        
        # Write data to CSV
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['ssn', 'name', 'amount', 'company', 'report_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for employee in data['employee_data']:
                writer.writerow(employee)
        
        print(f"Data saved to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error saving data to CSV: {e}")
        return False


def main():
    """Main function to process Word documents and convert to CSV."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output files
    input_file = os.path.join(script_dir, 'CorporateJewelers031425.docx')
    output_file = os.path.join(script_dir, 'CorporateJewelers031425.csv')
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return
    
    # Extract data from Word document
    data = extract_data_from_docx(input_file)
    
    if data:
        # Save data to CSV
        save_to_csv(data, output_file)
    else:
        print("Failed to extract data from the Word document.")


if __name__ == "__main__":
    main()
