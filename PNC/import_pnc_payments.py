#!/usr/bin/env python3
"""
PNC Payments Import Script - Refactored for WSL Ubuntu
Imports PNC payment CSV files into the pnc_currentday_split table.

Usage:
    python import_pnc_payments.py
    python import_pnc_payments.py --test

Author: Lil Claudy Flossy
Modified: 2025-06-27
"""

import os
import glob
import shutil
import logging
import pandas as pd
import re
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'pnc_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants - Updated for WSL Ubuntu environment
INPUT_DIR = Path(__file__).parent.parent / 'PaymentFiles' / 'PNC'
ARCHIVE_DIR = INPUT_DIR / 'archive'
MAX_BATCH_SIZE = 100

class DescriptionParser:
    """Simple PNC transaction description parser."""
    
    def __init__(self):
        self.fields = [
            'Cust ID:', 'Desc:', 'Comp Name:', 'Comp ID:', 
            'Batch Discr:', 'SEC:', 'Cust Name:', 'Date:', 
            'Time:', 'Addenda:'
        ]
    
    def parse(self, description: str) -> Dict[str, Any]:
        """Parse transaction description."""
        if not description:
            return {}
        
        # Remove ACH prefix if present
        desc = description.strip()
        if desc.startswith('ACH CREDIT RECEIVED - '):
            desc = desc[22:]
        elif desc.startswith('ACH DEBIT RECEIVED - '):
            desc = desc[21:]
        
        result = {}
        
        # Parse each field
        for field in self.fields:
            field_lower = field[:-1].lower().replace(' ', '_')
            
            # Find field position
            start_pos = desc.find(field)
            if start_pos == -1:
                continue
            
            # Extract value
            value_start = start_pos + len(field)
            
            # Find next field
            next_positions = []
            for next_field in self.fields:
                if next_field != field:
                    pos = desc.find(next_field, value_start)
                    if pos > -1:
                        next_positions.append(pos)
            
            if next_positions:
                value_end = min(next_positions)
                value = desc[value_start:value_end].strip()
            else:
                value = desc[value_start:].strip()
            
            if value:
                result[field_lower] = value
        
        return result

class PNCImporter:
    """PNC transaction file importer for new payment files."""
    
    def __init__(self, test_mode: bool = False):
        """Initialize the PNC Importer."""
        self.test_mode = test_mode
        self.description_parser = DescriptionParser()
        self.setup_directories()
        self.db_config = self.get_db_config()
    
    def get_db_config(self) -> dict:
        """Get database configuration from environment."""
        return {
            'host': os.getenv('SPIDERSYNC_DEV_HOST', 'localhost'),
            'user': os.getenv('SPIDERSYNC_DEV_USER'),
            'password': os.getenv('SPIDERSYNC_DEV_PASSWORD'),
            'database': os.getenv('SPIDERSYNC_DEV_DATABASE', 'spider_sync_DEV'),
            'charset': 'utf8mb4',
            'port': int(os.getenv('SPIDERSYNC_DEV_PORT', '10033'))
        }
    
    def get_connection(self):
        """Get database connection."""
        return pymysql.connect(**self.db_config)
    
    def setup_directories(self):
        """Set up required directories for processing."""
        ARCHIVE_DIR.mkdir(exist_ok=True)
        logger.info(f"Using input directory: {INPUT_DIR}")
        logger.info(f"Using archive directory: {ARCHIVE_DIR}")
    
    def get_csv_files(self) -> List[Path]:
        """Get list of CSV files to process."""
        csv_files = list(INPUT_DIR.glob('*.csv'))
        logger.info(f"Found {len(csv_files)} CSV files in input directory")
        return csv_files
    
    def get_existing_references(self) -> set:
        """Get set of existing reference numbers from database."""
        if self.test_mode:
            logger.info("Test mode: Skipping database reference check")
            return set()
        
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT Reference FROM pnc_currentday_split")
                return {row[0] for row in cursor.fetchall()}
        finally:
            conn.close()
    
    def parse_description(self, description: str) -> Dict[str, Any]:
        """Parse the transaction description field."""
        if not description or pd.isna(description):
            return {}
        
        # Parse using the description parser
        parsed_fields = self.description_parser.parse(str(description).strip())
        
        # Map field names to database columns
        field_mapping = {
            'cust_id': 'CustID',
            'desc_name': 'desc_name',
            'comp_name': 'CompName',
            'comp_id': 'CompID',
            'batch_discr': 'BatchDiscr',
            'sec': 'SEC',
            'cust_name': 'CustName',
            'time': 'Time',
            'addenda': 'Addenda'
        }
        
        # Create result with mapped names
        result = {}
        for parser_field, db_field in field_mapping.items():
            if parser_field in parsed_fields:
                result[db_field] = parsed_fields[parser_field]
        
        # Apply field length limits
        field_limits = {
            'CompName': 50, 'CompID': 50, 'CustID': 50,
            'CustName': 50, 'BatchDiscr': 50, 'SEC': 50,
            'desc_name': 50, 'Time': 10, 'Addenda': 50
        }
        
        for field, limit in field_limits.items():
            if field in result and result[field] and len(result[field]) > limit:
                logger.warning(f"Truncating {field} from {len(result[field])} to {limit} characters")
                result[field] = result[field][:limit]
        
        return result
    
    def process_csv_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Process a single CSV file."""
        try:
            logger.info(f"Processing file: {file_path.name}")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            if df.empty:
                logger.warning(f"File {file_path.name} is empty")
                return None
            
            # Remove duplicate headers if present
            if 'AsOfDate' in df.columns:
                df = df[~df['AsOfDate'].astype(str).str.contains('AsOfDate')]
            
            # Clean column names
            column_mapping = {
                'CR/DR': 'CR_DR',
                'ZerDayFloat': 'ZeroDayFloat',
                'Desc': 'desc_name'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and new_col not in df.columns:
                    df[new_col] = df[old_col]
            
            # Verify required columns
            required_columns = ['AsOfDate', 'Description', 'Reference']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Required column '{col}' missing from {file_path.name}")
                    return None
            
            # Parse descriptions
            logger.info(f"Parsing descriptions for {len(df)} records")
            parsed_descriptions = []
            
            for idx, row in df.iterrows():
                if 'Description' in df.columns and not pd.isna(row['Description']):
                    parsed = self.parse_description(row['Description'])
                    parsed_descriptions.append(parsed)
                else:
                    parsed_descriptions.append({})
            
            # Add parsed fields to dataframe
            for i, parsed in enumerate(parsed_descriptions):
                for field, value in parsed.items():
                    if field not in df.columns:
                        df[field] = None
                    df.at[i, field] = value
            
            # Format date field
            try:
                # First try simple MM/DD/YYYY format (most common)
                df['AsOfDate'] = pd.to_datetime(df['AsOfDate'], 
                                                format='%m/%d/%Y', 
                                                errors='coerce')
                # If that doesn't work, try with time and timezone
                mask = df['AsOfDate'].isna()
                if mask.any():
                    df.loc[mask, 'AsOfDate'] = pd.to_datetime(
                        df.loc[mask, 'AsOfDate'], 
                        format='%m/%d/%Y %I:%M:%S %p CDT', 
                        errors='coerce'
                    )
                
                # Convert to date only (no time)
                df['AsOfDate'] = df['AsOfDate'].dt.date
                
                nat_count = df['AsOfDate'].isna().sum()
                if nat_count > 0:
                    logger.warning(f"Found {nat_count} records with invalid dates")
            except Exception as e:
                logger.error(f"Error parsing date fields: {str(e)}")
            
            # Clean Reference field
            if 'Reference' in df.columns:
                df['Reference'] = df['Reference'].astype(str).str.replace("'", "", regex=False)
            
            # Convert numeric fields
            numeric_fields = ['Amount', 'ZeroDayFloat', 'OneDayFloat', 'TwoDayFloat']
            for field in numeric_fields:
                if field in df.columns:
                    df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0.0)
            
            logger.info(f"Successfully processed {len(df)} records from {file_path.name}")
            return df
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")
            return None
    
    def insert_records(self, records: pd.DataFrame) -> int:
        """Insert records into the pnc_currentday_split table."""
        # Validate dates
        valid_records = records.dropna(subset=['AsOfDate'])
        invalid_count = len(records) - len(valid_records)
        
        if invalid_count > 0:
            logger.warning(f"Dropping {invalid_count} records with invalid dates")
            records = valid_records
        
        if records.empty:
            logger.warning("No valid records to insert")
            return 0
        
        # Check for duplicates
        existing_references = self.get_existing_references()
        new_records = records[~records['Reference'].isin(existing_references)]
        skipped_count = len(records) - len(new_records)
        
        if skipped_count > 0:
            logger.info(f"Skipping {skipped_count} records with existing references")
        
        if new_records.empty:
            logger.info("No new records to insert")
            return 0
        
        # Process in batches
        success_count = 0
        batch_size = min(MAX_BATCH_SIZE, len(new_records))
        batches = [new_records[i:i+batch_size] for i in range(0, len(new_records), batch_size)]
        
        logger.info(f"Inserting {len(new_records)} records in {len(batches)} batches")
        
        if self.test_mode:
            # In test mode, just log what would be inserted
            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"Test mode: would insert {len(batch)} records in batch {batch_num}/{len(batches)}")
            return len(new_records)
        
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                for batch_num, batch in enumerate(batches, 1):
                    try:
                        # Convert to list of tuples for bulk insert
                        values = []
                        for _, record in batch.iterrows():
                            # Helper function to handle NaN values
                            def clean_value(value, default=''):
                                if pd.isna(value):
                                    return default
                                return value
                            
                            # Handle date formatting for MySQL
                            as_of_date = record.get('AsOfDate')
                            if pd.notna(as_of_date):
                                # Convert to date object if it's a Timestamp
                                if hasattr(as_of_date, 'date'):
                                    as_of_date = as_of_date.date()
                                # Format as MySQL date string
                                as_of_date = str(as_of_date)
                            else:
                                as_of_date = None
                            
                            values.append((
                                as_of_date,
                                clean_value(record.get('BankId', '')),
                                clean_value(record.get('AccountNumber', '')),
                                clean_value(record.get('AccountName', '')),
                                clean_value(record.get('BaiControl', '')),
                                clean_value(record.get('Currency', 'USD'), 'USD'),
                                clean_value(record.get('Transaction', '')),
                                float(clean_value(record.get('Amount', 0.0), 0.0)),
                                clean_value(record.get('CR_DR', '')),
                                float(clean_value(record.get('ZeroDayFloat', 0.0), 0.0)),
                                float(clean_value(record.get('OneDayFloat', 0.0), 0.0)),
                                float(clean_value(record.get('TwoDayFloat', 0.0), 0.0)),
                                clean_value(record.get('Reference', '')),
                                clean_value(record.get('Description', '')),
                                clean_value(record.get('CompName', '')),
                                clean_value(record.get('CompID', '')),
                                clean_value(record.get('CustID', '')),
                                clean_value(record.get('CustName', '')),
                                clean_value(record.get('BatchDiscr', '')),
                                clean_value(record.get('SEC', '')),
                                clean_value(record.get('desc_name', '')),
                                clean_value(record.get('Time', '')),
                                clean_value(record.get('Addenda', 'NoAddenda'), 'NoAddenda'),
                                0  # applied field
                            ))
                        
                        if not self.test_mode:
                            insert_query = """
                                INSERT INTO pnc_currentday_split (
                                    AsOfDate, BankId, AccountNumber, AccountName, BaiControl,
                                    Currency, Transaction, Amount, CR_DR, ZeroDayFloat,
                                    OneDayFloat, TwoDayFloat, Reference, Description,
                                    CompName, CompID, CustID, CustName, BatchDiscr,
                                    SEC, desc_name, Time, Addenda, applied
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s
                                )
                            """
                            cursor.executemany(insert_query, values)
                            conn.commit()
                            success_count += len(batch)
                            logger.info(f"Inserted batch {batch_num}/{len(batches)} with {len(batch)} records")
                        else:
                            logger.info(f"Test mode: would insert {len(batch)} records in batch {batch_num}")
                    
                    except Exception as e:
                        logger.error(f"Error inserting batch {batch_num}: {str(e)}")
                        conn.rollback()
                        continue
        finally:
            conn.close()
        
        return success_count
    
    def archive_file(self, file_path: Path) -> bool:
        """Archive a processed file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_path = ARCHIVE_DIR / f"{timestamp}_{file_path.name}"
            
            shutil.copy2(file_path, archive_path)
            
            if not self.test_mode:
                file_path.unlink()
                logger.info(f"Archived and removed: {file_path.name} -> {archive_path.name}")
            else:
                logger.info(f"Test mode: would archive: {file_path.name} -> {archive_path.name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error archiving {file_path.name}: {str(e)}")
            return False
    
    def run(self) -> Dict[str, Any]:
        """Run the complete import process."""
        logger.info(f"Starting PNC import process (test_mode={self.test_mode})")
        
        stats = {
            'files_found': 0,
            'files_processed': 0,
            'records_found': 0,
            'records_inserted': 0,
            'files_archived': 0
        }
        
        # Get CSV files
        csv_files = self.get_csv_files()
        stats['files_found'] = len(csv_files)
        
        if not csv_files:
            logger.info("No CSV files found to process")
            return stats
        
        # Process each file
        all_records = []
        for file_path in csv_files:
            records = self.process_csv_file(file_path)
            
            if records is not None:
                stats['files_processed'] += 1
                stats['records_found'] += len(records)
                all_records.append(records)
                
                # Archive the file
                if self.archive_file(file_path):
                    stats['files_archived'] += 1
        
        # Combine and insert records
        if all_records:
            master_df = pd.concat(all_records, ignore_index=True)
            stats['records_inserted'] = self.insert_records(master_df)
        
        # Log summary
        logger.info("=== Import Summary ===")
        logger.info(f"Files found: {stats['files_found']}")
        logger.info(f"Files processed: {stats['files_processed']}")
        logger.info(f"Files archived: {stats['files_archived']}")
        logger.info(f"Records found: {stats['records_found']}")
        logger.info(f"Records inserted: {stats['records_inserted']}")
        
        if self.test_mode:
            logger.info("Note: Ran in TEST MODE - no actual database changes made")
        
        return stats

def main():
    """Main function to run the import process."""
    import argparse
    parser = argparse.ArgumentParser(description='Import PNC payment files')
    parser.add_argument('--test', action='store_true', 
                      help='Run in test mode without making changes')
    parser.add_argument('--dry-run', action='store_true',
                      help='Process files and show what would be inserted without DB connection')
    args = parser.parse_args()
    
    # Use test mode for dry-run as well
    test_mode = args.test or args.dry_run
    
    # Run the importer
    importer = PNCImporter(test_mode=test_mode)
    stats = importer.run()
    
    # Return exit code
    if stats['files_processed'] > 0:
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())