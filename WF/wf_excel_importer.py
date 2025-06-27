#!/usr/bin/env python3
"""
Wells Fargo Excel Payment Importer
Processes Excel files from PaymentFiles/WF/ and inserts into wf_payments_split table
Author: Lil Claudy Flossy
"""

import os
import sys
import pandas as pd
import pymysql
from datetime import datetime
import logging
import argparse
from pathlib import Path
from db_connection import get_db_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'wf_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Column mapping from Excel to database
COLUMN_MAPPING = {
    'As-Of Date': 'AsOfDate',
    'As-Of-Time': 'AsOfTime',
    'Bank ID': 'BankID',
    'Bank Name': 'BankName',
    'State': 'State',
    'Acct No': 'AccountNumber',
    'Acct Type': 'AccountType',
    'Acct Name': 'AccountName',
    'Currency': 'Currency',
    'BAI Type Code': 'BAITypeCode',
    'Tran Desc': 'TransactionDesc',
    'Debit Amt': 'DebitAmount',
    'Credit Amt': 'CreditAmount',
    'Customer Ref No': 'CustomerRefNo',
    'Value Date': 'ValueDate',
    'Location': 'Location',
    'Bank Reference': 'BankReference',
    'Tran Status': 'TransactionStatus',
    'Descriptive Text 1': 'DescriptiveText1',
    'Descriptive Text 2': 'DescriptiveText2',
    'Description': 'Description',
    'Unique ID': 'UniqueID'
}

# Transaction types to process - removed filter for now
# Will process all transaction types in the Excel file

def process_excel_file(file_path):
    """Read and process Excel file."""
    logger.info(f"Processing file: {file_path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        logger.info(f"Read {len(df)} rows from Excel file")
        
        # Rename columns to match database
        df.rename(columns=COLUMN_MAPPING, inplace=True)
        
        # No filtering for now - process all records
        
        # Convert date columns
        date_columns = ['AsOfDate', 'ValueDate', 'PostingDate']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].dt.strftime('%Y-%m-%d')
        
        # Convert amount columns
        amount_columns = ['DebitAmount', 'CreditAmount']
        for col in amount_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Replace NaN values with None for MySQL compatibility
        df = df.where(pd.notnull(df), None)
        
        # Add metadata
        df['Import_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['File_Name'] = os.path.basename(file_path)
        
        return df
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise

def insert_to_database(df, connection):
    """Insert DataFrame records into wf_payments_split table."""
    cursor = connection.cursor()
    
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    for _, row in df.iterrows():
        try:
            # Check if record exists based on BankReference
            check_sql = "SELECT ID FROM wf_payments_split WHERE BankReference = %s"
            cursor.execute(check_sql, (row.get('BankReference'),))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                update_sql = """
                    UPDATE wf_payments_split 
                    SET AsOfDate = %s, AsOfTime = %s, BankID = %s, BankName = %s,
                        State = %s, AccountNumber = %s, AccountType = %s, AccountName = %s,
                        Currency = %s, BAITypeCode = %s, TransactionDesc = %s,
                        DebitAmount = %s, CreditAmount = %s, CustomerRefNo = %s,
                        ValueDate = %s, Location = %s, TransactionStatus = %s,
                        DescriptiveText1 = %s, DescriptiveText2 = %s, Description = %s,
                        UniqueID = %s
                    WHERE BankReference = %s
                """
                cursor.execute(update_sql, (
                    row.get('AsOfDate'), row.get('AsOfTime'), row.get('BankID'),
                    row.get('BankName'), row.get('State'), row.get('AccountNumber'),
                    row.get('AccountType'), row.get('AccountName'), row.get('Currency'),
                    row.get('BAITypeCode'), row.get('TransactionDesc'), row.get('DebitAmount'),
                    row.get('CreditAmount'), row.get('CustomerRefNo'), row.get('ValueDate'),
                    row.get('Location'), row.get('TransactionStatus'), row.get('DescriptiveText1'),
                    row.get('DescriptiveText2'), row.get('Description'), row.get('UniqueID'),
                    row.get('BankReference')
                ))
                updated_count += 1
                logger.debug(f"Updated record with BankReference: {row.get('BankReference')}")
            else:
                # Insert new record
                insert_sql = """
                    INSERT INTO wf_payments_split 
                    (AsOfDate, AsOfTime, BankID, BankName, State, AccountNumber,
                     AccountType, AccountName, Currency, BAITypeCode, TransactionDesc,
                     DebitAmount, CreditAmount, CustomerRefNo, ValueDate, Location,
                     BankReference, TransactionStatus, DescriptiveText1, DescriptiveText2,
                     Description, UniqueID)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (
                    row.get('AsOfDate'), row.get('AsOfTime'), row.get('BankID'),
                    row.get('BankName'), row.get('State'), row.get('AccountNumber'),
                    row.get('AccountType'), row.get('AccountName'), row.get('Currency'),
                    row.get('BAITypeCode'), row.get('TransactionDesc'), row.get('DebitAmount'),
                    row.get('CreditAmount'), row.get('CustomerRefNo'), row.get('ValueDate'),
                    row.get('Location'), row.get('BankReference'), row.get('TransactionStatus'),
                    row.get('DescriptiveText1'), row.get('DescriptiveText2'), row.get('Description'),
                    row.get('UniqueID')
                ))
                inserted_count += 1
                logger.debug(f"Inserted record with BankReference: {row.get('BankReference')}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing record {row.get('BankReference')}: {str(e)}")
            continue
    
    connection.commit()
    logger.info(f"Database operation complete - Inserted: {inserted_count}, Updated: {updated_count}, Errors: {error_count}")
    
    return inserted_count, updated_count, error_count

def main():
    """Main function to process WF Excel files."""
    parser = argparse.ArgumentParser(description='Import Wells Fargo Excel payments')
    parser.add_argument('--file', help='Specific Excel file to import')
    parser.add_argument('--all', action='store_true', help='Process all Excel files in PaymentFiles/WF/')
    args = parser.parse_args()
    
    # Determine base path
    base_path = Path(__file__).parent.parent / 'PaymentFiles' / 'WF'
    
    # Get files to process
    if args.file:
        files_to_process = [args.file]
    elif args.all:
        files_to_process = [str(f) for f in base_path.glob('*.xlsx') if not f.name.startswith('~')]
    else:
        # Default: get latest file
        excel_files = [f for f in base_path.glob('*.xlsx') if not f.name.startswith('~')]
        if not excel_files:
            logger.error("No Excel files found in PaymentFiles/WF/")
            return
        files_to_process = [str(max(excel_files, key=os.path.getmtime))]
    
    # Process each file
    total_inserted = 0
    total_updated = 0
    total_errors = 0
    
    connection = None
    try:
        connection = get_db_connection()
        logger.info("Connected to database successfully")
        
        for file_path in files_to_process:
            try:
                logger.info(f"Processing file: {file_path}")
                df = process_excel_file(file_path)
                
                if df.empty:
                    logger.warning(f"No valid records found in {file_path}")
                    continue
                
                inserted, updated, errors = insert_to_database(df, connection)
                total_inserted += inserted
                total_updated += updated
                total_errors += errors
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                continue
        
        logger.info(f"\nFinal Summary:")
        logger.info(f"Total files processed: {len(files_to_process)}")
        logger.info(f"Total records inserted: {total_inserted}")
        logger.info(f"Total records updated: {total_updated}")
        logger.info(f"Total errors: {total_errors}")
        
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        sys.exit(1)
    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()