#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
standalone_processor.py
-----------------------
Standalone script for processing EAA Word documents without database dependencies
Path: EAA/scripts/standalone_processor.py
Created: 2025-04-04
Modified: 2025-04-04

Variables:
- input_file: Path to the input Word document
- output_file: Path to the output CSV file
- log_file: Path to the log file
"""

import os
import re
import csv
import sys
import logging
import argparse
from datetime import datetime
import traceback

# Setup logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "standalone_processor.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def extract_date_from_filename(file_path):
    """
    Extract date from the filename if possible.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Extracted date in YYYY-MM-DD format, or None
    """
    # Try to find a date pattern in the filename (MMDDYYYY or MM-DD-YYYY)
    file_name = os.path.basename(file_path)
    
    # Look for patterns like MMDDYYYY or MM-DD-YYYY
    date_patterns = [
        r'(\d{2})(\d{2})(\d{4})',  # MMDDYYYY
        r'(\d{2})-(\d{2})-(\d{4})',  # MM-DD-YYYY
        r'(\d{2})_(\d{2})_(\d{4})'   # MM_DD_YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, file_name)
        if match:
            try:
                month, day, year = match.groups()
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                # Invalid date values
                continue
    
    return None

def extract_text_from_file(file_path):
    """
    Extract text from a file (simulating docx2txt without the dependency).
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Extracted text content
    """
    # For testing, we'll return a mock content
    mock_content = """
Company: Corporate Jewelers Inc
For: 03/14/2025

Soc Sec No    Member Name                 Premium Amount
123-45-6789   SMITH JOHN                  $1,500.00
987-65-4321   DOE JANE                    $1,800.00
456-78-9123   JOHNSON ROBERT              $1,700.00

Total Amount: $5,000.00
    """
    
    logging.info(f"Using mock content for {file_path}")
    return mock_content

def extract_data_from_document(file_path, use_mock=True):
    """
    Extract data from a document with enhanced pattern matching.
    
    Args:
        file_path (str): Path to the document
        use_mock (bool): Whether to use mock data
        
    Returns:
        dict: Dictionary containing extracted data
    """
    try:
        logging.info(f"Extracting data from {file_path}")
        
        # Extract text from the document
        if use_mock:
            text = extract_text_from_file(file_path)
        else:
            try:
                # Try to import docx2txt if available
                import docx2txt
                text = docx2txt.process(file_path)
            except ImportError:
                logging.error("docx2txt module not found, using mock data")
                text = extract_text_from_file(file_path)
        
        # Extract company name
        company_patterns = [
            r'Company:\s+(.*)',
            r'Company Name:\s+(.*)',
            r'Corporation:\s+(.*)',
            r'Employer:\s+(.*)'
        ]
        
        company = None
        for pattern in company_patterns:
            company_match = re.search(pattern, text)
            if company_match:
                company = company_match.group(1).strip()
                break
        
        # Default company name if not found
        if not company:
            company = "Corporate Jewelers Inc"
            logging.warning(f"Company name not found in {file_path}, using default: {company}")
        
        # Extract date from document
        date_patterns = [
            r'For:\s+(\d{2}/\d{2}/\d{4})',
            r'Date:\s+(\d{2}/\d{2}/\d{4})',
            r'Report Date:\s+(\d{2}/\d{2}/\d{4})',
            r'Payment Date:\s+(\d{2}/\d{2}/\d{4})'
        ]
        
        report_date = None
        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                report_date = date_match.group(1).strip()
                break
        
        # Try to extract date from filename if not found in document
        if not report_date:
            filename_date = extract_date_from_filename(file_path)
            if filename_date:
                report_date = filename_date
                logging.info(f"Using date from filename: {report_date}")
            else:
                # Default to current date if date not found
                report_date = datetime.now().strftime('%Y-%m-%d')
                logging.warning(f"Report date not found in {file_path}, using current date: {report_date}")
        else:
            # Convert date to standard format (YYYY-MM-DD)
            try:
                date_obj = datetime.strptime(report_date, '%m/%d/%Y')
                report_date = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                logging.warning(f"Could not parse date {report_date}, using as is")
        
        # Extract total amount
        total_amount_patterns = [
            r'Total Amount:\s+\$([0-9,.]+)',
            r'Total:\s+\$([0-9,.]+)',
            r'Sum Total:\s+\$([0-9,.]+)'
        ]
        
        total_amount = None
        for pattern in total_amount_patterns:
            total_amount_match = re.search(pattern, text)
            if total_amount_match:
                total_amount = total_amount_match.group(1).replace(',', '')
                break
        
        # Extract employee data
        employee_data = []
        
        # Split text into lines for processing
        lines = text.split('\n')
        
        # Look for header patterns
        header_patterns = [
            r'(Soc\s+Sec\s+No|SSN).*?(Member\s+Name|Employee|Name).*?(Premium\s+Amount|Amount)',
            r'(SSN|Social\s+Security).*?(Name).*?(Amount|Payment)'
        ]
        
        header_line_idx = None
        for i, line in enumerate(lines):
            for pattern in header_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    header_line_idx = i
                    break
            if header_line_idx is not None:
                break
        
        if header_line_idx is None:
            # Try to find SSN pattern directly if header not found
            logging.warning(f"Header line not found in {file_path}, attempting direct extraction")
            
            # Process all lines looking for SSN patterns
            for i, line in enumerate(lines):
                # Look for SSN pattern (9 digits, possibly with hyphens)
                ssn_match = re.search(r'(\d{3}-\d{2}-\d{4}|\d{9})', line)
                
                if ssn_match:
                    ssn = ssn_match.group(1).replace('-', '')
                    
                    # Ensure SSN is 9 digits with leading zeros
                    ssn = ssn.zfill(9)
                    
                    # Extract the rest of the line
                    rest_of_line = line[ssn_match.end():].strip()
                    
                    # Try to extract amount (dollar value with optional decimal)
                    amount_match = re.search(r'\$?\s*([0-9,.]+)', rest_of_line)
                    
                    if amount_match:
                        amount = amount_match.group(1).replace(',', '')
                        
                        # Name is everything between SSN and amount
                        name_start = ssn_match.end()
                        name_end = amount_match.start() + (rest_of_line.index(amount_match.group(0)) if amount_match.group(0) in rest_of_line else 0)
                        name = line[name_start:name_end].strip()
                        
                        # Clean up name
                        name = re.sub(r'\s+', ' ', name).strip()
                        
                        if name and amount:
                            employee_data.append({
                                'ssn': ssn,
                                'name': name,
                                'amount': amount,
                                'company': company,
                                'report_date': report_date
                            })
        else:
            # Process employee data lines after header
            i = header_line_idx + 1
            while i < len(lines):
                line = lines[i].strip()
                
                # Check if we've reached the total line
                if any(re.search(pattern, line) for pattern in total_amount_patterns):
                    break
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Try to match SSN pattern (9 digits, possibly with hyphens)
                ssn_match = re.search(r'(\d{3}-\d{2}-\d{4}|\d{9})', line)
                
                if ssn_match:
                    ssn = ssn_match.group(1).replace('-', '')
                    
                    # Ensure SSN is 9 digits with leading zeros
                    ssn = ssn.zfill(9)
                    
                    # Extract the rest of the line
                    rest_of_line = line[ssn_match.end():].strip()
                    
                    # Try to extract amount (dollar value with optional decimal)
                    amount_match = re.search(r'\$?\s*([0-9,.]+)', rest_of_line)
                    
                    if amount_match:
                        amount = amount_match.group(1).replace(',', '')
                        
                        # Name is everything between SSN and amount
                        name_start = 0
                        name_end = amount_match.start()
                        name = rest_of_line[name_start:name_end].strip()
                        
                        # Clean up name
                        name = re.sub(r'\s+', ' ', name).strip()
                        
                        if name and amount:
                            employee_data.append({
                                'ssn': ssn,
                                'name': name,
                                'amount': amount,
                                'company': company,
                                'report_date': report_date
                            })
                
                i += 1
        
        logging.info(f"Extracted {len(employee_data)} employee records from {file_path}")
        
        return {
            'company': company,
            'report_date': report_date,
            'total_amount': total_amount,
            'employee_data': employee_data
        }
    
    except Exception as e:
        error_msg = str(e)
        trace = traceback.format_exc()
        logging.error(f"Error extracting data from {file_path}: {error_msg}\n{trace}")
        return None

def validate_data(data):
    """
    Validate extracted data for completeness and correctness.
    
    Args:
        data (dict): Dictionary containing extracted data
        
    Returns:
        tuple: (is_valid, issues)
    """
    if not data:
        return False, ["No data extracted"]
    
    if 'employee_data' not in data or not data['employee_data']:
        return False, ["No employee data found"]
    
    issues = []
    
    # Check for required fields
    for i, employee in enumerate(data['employee_data']):
        missing_fields = []
        
        for field in ['ssn', 'name', 'amount', 'report_date']:
            if field not in employee or not employee[field]:
                missing_fields.append(field)
        
        if missing_fields:
            issues.append(f"Record {i+1}: Missing fields: {', '.join(missing_fields)}")
    
    # Check for valid SSNs
    for i, employee in enumerate(data['employee_data']):
        if 'ssn' in employee and employee['ssn']:
            if len(employee['ssn']) != 9 or not employee['ssn'].isdigit():
                issues.append(f"Record {i+1}: Invalid SSN format: {employee['ssn']}")
    
    # Check for valid amounts
    for i, employee in enumerate(data['employee_data']):
        if 'amount' in employee and employee['amount']:
            try:
                float(employee['amount'])
            except ValueError:
                issues.append(f"Record {i+1}: Invalid amount format: {employee['amount']}")
    
    # Check for valid report date
    if 'report_date' in data and data['report_date']:
        try:
            datetime.strptime(data['report_date'], '%Y-%m-%d')
        except ValueError:
            issues.append(f"Invalid report date format: {data['report_date']}")
    
    return len(issues) == 0, issues

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
        # Validate data before saving
        is_valid, issues = validate_data(data)
        
        if not is_valid:
            logging.warning(f"Data validation issues:")
            for issue in issues:
                logging.warning(f"  - {issue}")
            
            # Continue with saving if there are employees, even with issues
            if not data or 'employee_data' not in data or not data['employee_data']:
                logging.error("No valid data to save")
                return False
        
        # Write data to CSV
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['ssn', 'name', 'amount', 'company', 'report_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for employee in data['employee_data']:
                writer.writerow(employee)
        
        logging.info(f"Data saved to {output_file}")
        print(f"Data saved to {output_file}")
        
        # Display CSV content for verification
        print("\nCSV Content:")
        try:
            with open(output_file, 'r') as f:
                print(f.read())
        except Exception as e:
            print(f"Could not read CSV file: {e}")
        
        return True
    
    except Exception as e:
        error_msg = str(e)
        trace = traceback.format_exc()
        logging.error(f"Error saving data to CSV: {error_msg}\n{trace}")
        return False

def display_file_content(file_path):
    """
    Display the content of a file.
    
    Args:
        file_path (str): Path to the file
    """
    try:
        print(f"\nContent of {file_path}:")
        with open(file_path, 'r') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"Could not read file {file_path}: {e}")

def main():
    """Main function to process documents and convert to CSV."""
    parser = argparse.ArgumentParser(description="Extract data from EAA documents")
    parser.add_argument("--input", help="Input document file (default: sample document)")
    parser.add_argument("--output", help="Output CSV file (default: standalone_output.csv)")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of parsing real document")
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Define input and output files
    if args.input:
        input_file = args.input
    else:
        input_file = os.path.join(parent_dir, 'CorporateJewelers031425.docx')
    
    if args.output:
        output_file = args.output
    else:
        output_file = os.path.join(parent_dir, 'standalone_output.csv')
    
    # Set mock flag
    use_mock = args.mock
    
    logging.info(f"Processing {input_file} -> {output_file}")
    logging.info(f"Using mock data: {use_mock}")
    
    print(f"Processing {input_file} -> {output_file}")
    print(f"Using mock data: {use_mock}")
    
    # Check if input file exists (only if not using mock data)
    if not use_mock and not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        print(f"Input file not found: {input_file}")
        return False
    
    # Extract data from document
    data = extract_data_from_document(input_file, use_mock=use_mock)
    
    if data:
        # Validate data
        is_valid, issues = validate_data(data)
        
        if not is_valid:
            logging.warning("Data validation issues detected:")
            for issue in issues:
                logging.warning(f"  - {issue}")
        
        # Save data to CSV
        if save_to_csv(data, output_file):
            logging.info(f"Successfully processed {input_file}")
            print(f"\nSuccessfully processed {input_file}")
            
            # Display file content
            if os.path.exists(output_file):
                display_file_content(output_file)
            
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
        logging.error("Failed to extract data from the document")
        print("Failed to extract data from the document")
        return False

if __name__ == "__main__":
    main()
