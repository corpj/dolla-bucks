"""
File: payment_processor/scripts/enhanced_wf_importer_v2.py
Created: 2025-05-08
Modified: 2025-05-08
Variables: csv_file_path, import_date, batch_size, verify_import, test_mode

Script to import Wells Fargo payment data from CSV or Excel files into the database.
Uses the enhanced parsing logic to extract structured data from payment descriptions.
Automatically processes files from X:\\toadd directory.
Only processes transactions with TransactionDesc IN ('MISCELLANEOUS ACH CREDIT', 'POSTING ERROR CORRECTION DEBIT')

### THIS IS THE MOST RECENT VERSION OF THE ENHANCED WF IMPORTER ###

# Navigate to the main payments directory
cd C:/Users/CorporateJewelers/pythonapps/pj-app/payments

# Activate the virtual environment if it exists
# For Windows:
venv/Scripts/activate

# Run the script as a module within the package
python -m payment_processor.scripts.enhanced_wf_importer_v2 --test
# or for production:
python -m payment_processor.scripts.enhanced_wf_importer_v2
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
import re
from typing import Dict, List, Any, Optional, Tuple
import argparse
import glob
import shutil
import uuid
import traceback

# Add parent directory to path to import from app
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Configure logging with both file and console handlers
log_dir = os.path.join(parent_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'enhanced_wf_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Create logger
logger = logging.getLogger('enhanced_wf_import')
logger.setLevel(logging.INFO)

# Prevent propagation to root logger to avoid duplicate messages
logger.propagate = False

# Create file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(file_format)
logger.addHandler(console_handler)

# Try to import necessary modules
try:
    from sqlalchemy import text, create_engine
    from app.utils.db_engine import get_engine
    logger.info("Successfully imported SQLAlchemy and database modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


class EnhancedDescriptionParser:
    """Enhanced description parser that uses the improved pattern-based extraction logic"""
    
    def __init__(self):
        """Initialize with patterns from the database"""
        self.patterns = None
        self.engine = get_engine('dev')
        self.load_patterns()
    
    def load_patterns(self):
        """Load company name patterns from the database"""
        try:
            with self.engine.connect() as connection:
                query = text("""
                SELECT CompName, CompName_Pattern, PaymentType_Pattern, 
                       FormatDate_Pattern, CustID_Pattern, employerID 
                FROM wf_compnames
                """)
                result = connection.execute(query)
                
                # Create a dictionary using integer indices instead of column names
                self.patterns = {}
                for row in result:
                    try:
                        self.patterns[row[0]] = {
                            'CompName_Pattern': row[1],
                            'PaymentType_Pattern': row[2],
                            'FormatDate_Pattern': row[3],
                            'CustID_Pattern': row[4],
                            'employerID': row[5]
                        }
                    except Exception as e:
                        logger.warning(f"Error processing pattern for {row[0] if len(row) > 0 else 'unknown'}: {e}")
                
                logger.info(f"Loaded {len(self.patterns)} company name patterns from database")
        except Exception as e:
            logger.error(f"Error loading company name patterns: {e}")
            self.patterns = {}
    
    def detect_company_name(self, description: str) -> str:
        """Extract company name using the same logic as the view"""
        if not description or not isinstance(description, str):
            return None
            
        # Use the same complex logic as in the view
        try:
            parts = description.split(' ')
            if len(parts) >= 2:
                second_word = parts[1]
                
                if second_word in ('LOS', 'OF', '&'):
                    return ' '.join(parts[:3])
                elif second_word in ('&', 'WATER'):
                    return ' '.join(parts[:4])
                elif second_word in ('ACH', 'ALLOTMENT', 'REG.SALARY', 'ASSOCPAYRL', 
                                    'PMT/REFUND', 'PAYROLL', 'EXL02', 'RET', 'DIRECT', 'REG'):
                    return parts[0]
                else:
                    return ' '.join(parts[:2])
            elif len(parts) == 1:
                return parts[0]
            return None
        except Exception as e:
            logger.warning(f"Error detecting company name from '{description[:30]}...': {e}")
            return None
    
    def get_before_fr(self, description: str) -> str:
        """Extract the part before ' FR ' from the description"""
        if not description or ' FR ' not in description:
            return description
        return description.split(' FR ')[0].strip()
    
    def extract_pattern_value(self, before_fr: str, start_pattern: int, end_pattern: int = None) -> str:
        """Extract a value based on word patterns"""
        if not before_fr:
            return None
            
        parts = before_fr.split()
        if len(parts) <= start_pattern:
            return None
            
        if end_pattern is None:
            # Extract a single word
            return parts[start_pattern]
        else:
            # Extract a range of words
            return ' '.join(parts[start_pattern:end_pattern])
    
    def parse(self, description: str, transaction_desc: str) -> Dict[str, Any]:
        """
        Parse the payment description to extract structured data
        
        Args:
            description: The payment description string to parse
            transaction_desc: The transaction description
            
        Returns:
            Dict with extracted fields
        """
        if not description or not isinstance(description, str):
            return {}
            
        # Only process specific transaction types
        if transaction_desc not in ('MISCELLANEOUS ACH CREDIT', 'POSTING ERROR CORRECTION DEBIT'):
            return {}
            
        result = {}
        
        try:
            # Get the part before 'FR'
            before_fr = self.get_before_fr(description)
            result['before_FR'] = before_fr
            
            # Detect company name
            detected_company = self.detect_company_name(description)
            result['CompName'] = detected_company  # Store directly as CompName
            
            # Default behavior - extract AcctNo as last 10 digits
            if description:
                # Try to get the last 10 digits
                acct_match = re.search(r'\d{10}$', description)
                if acct_match:
                    result['AcctNo'] = acct_match.group(0)
                
                # Extract FR and related fields
                if ' FR ' in description:
                    try:
                        fr_parts = description.split(' FR ')
                        if len(fr_parts) > 1:
                            # Get the FR value (typically a number after 'FR ')
                            fr_value = fr_parts[1].split()[0].strip()
                            result['FR'] = fr_value
                            
                            # Look for customer name between date and FR
                            if 'Date' in result and result['Date']:
                                date_str = result['Date']
                                if date_str in fr_parts[0]:
                                    name_part = fr_parts[0].split(date_str, 1)[1].strip()
                                    # Extract customer name (words after XXXXX)
                                    if 'XXXXX' in name_part:
                                        cust_parts = name_part.split('XXXXX', 1)
                                        if len(cust_parts) > 1 and cust_parts[1].strip():
                                            result['CustName'] = cust_parts[1].strip()
                    except Exception as e:
                        logger.warning(f"Error extracting FR data: {e}")
                        
                # Extract SUB ACCT info
                if ' SUB ACCT ' in description:
                    try:
                        sub_parts = description.split(' SUB ACCT ')
                        if len(sub_parts) > 1:
                            acct_value = sub_parts[1].strip()
                            result['SubAccount'] = acct_value
                    except Exception as e:
                        logger.warning(f"Error extracting SUB ACCT data: {e}")
        except Exception as e:
            logger.error(f"Error parsing description: {e}")
            return {}
        
        return result


def map_csv_to_db(df_raw: pd.DataFrame, parser: EnhancedDescriptionParser) -> pd.DataFrame:
    """
    Maps CSV column names to database column names and parses descriptions
    
    Args:
        df_raw: The raw dataframe directly from CSV
        parser: The description parser instance
        
    Returns:
        DataFrame with columns renamed to match database schema
    """
    # Define the mapping from CSV field names to database field names
    field_mapping = {
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
    
    # Create a copy to avoid modifying the original
    df_mapped = df_raw.copy()
    
    # Filter for the transaction types we care about
    filter_condition = df_mapped['Tran Desc'].isin(['MISCELLANEOUS ACH CREDIT', 'POSTING ERROR CORRECTION DEBIT'])
    df_mapped = df_mapped[filter_condition]
    
    if len(df_mapped) == 0:
        logger.warning("No records with the required transaction types were found")
        return df_mapped
    
    # Convert dates to proper format
    for date_field in ['As-Of Date', 'Value Date']:
        if date_field in df_mapped.columns:
            try:
                df_mapped[date_field] = pd.to_datetime(df_mapped[date_field]).dt.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Could not convert {date_field} to date format: {e}")
    
    # Rename columns according to mapping
    df_mapped = df_mapped.rename(columns=field_mapping)
    
    # Process AccountNumber to extract only digits
    if 'AccountNumber' in df_mapped.columns:
        df_mapped['AccountNumber'] = df_mapped['AccountNumber'].apply(
            lambda x: ''.join(filter(str.isdigit, str(x))) if x else None
        )
    
    # Add default applied field
    df_mapped['applied'] = 0
    
    # Track companies needing parser improvements
    unparsed_companies = {}
    
    # Parse description to extract additional fields
    if 'Description' in df_mapped.columns and 'TransactionDesc' in df_mapped.columns:
        # Apply the description parser and create a series of dictionaries
        logger.info("Parsing payment descriptions...")
        
        # Process rows in batches to show progress
        total_rows = len(df_mapped)
        batch_size = 50
        parsed_descriptions = []
        
        for i in range(0, total_rows, batch_size):
            end_idx = min(i + batch_size, total_rows)
            batch = df_mapped.iloc[i:end_idx]
            
            batch_results = []
            for _, row in batch.iterrows():
                parsed = parser.parse(row['Description'], row['TransactionDesc'])
                batch_results.append(parsed)
            
            parsed_descriptions.extend(batch_results)
            
            # Log progress
            logger.info(f"Parsed {end_idx}/{total_rows} descriptions ({end_idx/total_rows*100:.1f}%)")
        
        # Create a Series from the results
        parsed_series = pd.Series(parsed_descriptions, index=df_mapped.index)
        
        # For each field we want to extract, create a new column
        for field in ['CompName', 'desc_name', 'Date', 'CustID', 'CustName', 'FR', 
                     'FullSubAccount', 'SubAccount', 'SUB', 'ACCT', 'AcctNo', 'wf_payID', 'employerID']:
            df_mapped[field] = parsed_series.apply(lambda x: x.get(field, None))
        
        # Generate wf_payid by concatenating CompName and CustName where not already generated
        df_mapped['wf_payID'] = df_mapped.apply(
            lambda row: f"{row['CompName']}_{row['CustName']}" 
            if row['CompName'] and row['CustName'] and not row.get('wf_payID') 
            else row.get('wf_payID'),
            axis=1
        )
        
        # Track companies with unparsed fields
        for idx, row in df_mapped.iterrows():
            comp_name = row.get('CompName')
            if comp_name and not (row.get('CustID') and row.get('CustName') and row.get('AcctNo')):
                unparsed_companies[comp_name] = unparsed_companies.get(comp_name, 0) + 1
        
        # Report candidates for new parser development
        if unparsed_companies:
            logger.info("Companies needing parser improvements:")
            for company, count in sorted(unparsed_companies.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {company}: {count} records")
    
    return df_mapped


def get_table_schema(connection, table_name: str) -> Dict[str, str]:
    """
    Get the database schema for the specified table.
    
    Args:
        connection: SQLAlchemy connection
        table_name: Name of the table to get schema for
        
    Returns:
        Dictionary mapping column names to their data types
    """
    try:
        query = text("""
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = :table_name
        """)
        
        result = connection.execute(query, {"table_name": table_name})
        schema = {row[0]: row[1] for row in result}
        return schema
    except Exception as e:
        logger.error(f"Error getting schema for table {table_name}: {e}")
        return {}


def convert_types_for_db(data: Dict[str, Any], schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert data types to match database schema.
    
    Args:
        data: Dictionary of data to convert
        schema: Database schema with column types
        
    Returns:
        Dictionary with converted values
    """
    converted = {}
    
    for key, value in data.items():
        try:
            # Skip problematic column names and empty values
            if key.isdigit() or key.startswith('0') or not key or value is None or value == '':
                continue
                
            if key in schema:
                data_type = schema[key].lower()
                
                # Handle special numeric ID fields as strings
                if key in ['BankID', 'CustID', 'FR', 'FullSubAccount', 'SubAccount']:
                    converted[key] = str(value) if value is not None else None
                # Handle numeric types
                elif 'int' in data_type:
                    try:
                        converted[key] = int(float(value)) if value is not None and value != '' else None
                    except (ValueError, TypeError):
                        converted[key] = None
                elif 'decimal' in data_type or 'float' in data_type or 'double' in data_type:
                    try:
                        converted[key] = float(value) if value is not None and value != '' else None
                    except (ValueError, TypeError):
                        converted[key] = None
                # Handle date types
                elif 'date' in data_type:
                    if value:
                        try:
                            converted[key] = str(pd.to_datetime(value).strftime('%Y-%m-%d'))
                        except:
                            converted[key] = None
                    else:
                        converted[key] = None
                # Handle varchar fields - enforce length limits
                elif 'varchar' in data_type and '(' in data_type:
                    # Extract the length limit from the data type
                    length_match = re.search(r'varchar\((\d+)\)', data_type)
                    if length_match and value is not None:
                        length_limit = int(length_match.group(1))
                        converted[key] = str(value)[:length_limit]
                    else:
                        converted[key] = str(value) if value is not None else None
                # Default to string
                else:
                    converted[key] = str(value) if value is not None else None
            else:
                # Skip fields not in schema
                pass
        except Exception as e:
            logger.warning(f"Error converting {key}: {e}")
    
    return converted


def execute_sql(engine, sql, params=None, fetchall=False):
    """
    Execute SQL with proper connection and cursor management
    to avoid "Commands out of sync" errors
    
    Args:
        engine: SQLAlchemy engine
        sql: SQL query to execute
        params: Parameters for the query
        fetchall: Whether to fetch all results
        
    Returns:
        Query results if fetchall is True, otherwise rowcount
    """
    if params is None:
        params = {}
        
    try:
        # Get a new connection for each query
        with engine.connect() as conn:
            with conn.begin():
                # Execute the query
                result = conn.execute(text(sql), params)
                
                # Fetch results if needed
                if fetchall:
                    return result.fetchall()
                else:
                    return result.rowcount
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        logger.error(traceback.format_exc())
        return None


def process_wf_payment_records(
    df: pd.DataFrame,
    engine,
    test_mode: bool = False,
    update_existing: bool = True,
    insert_customer_payid: bool = True,
    run_parse_proc: bool = False
) -> Tuple[int, int, int]:
    """
    Process Wells Fargo payment records from a DataFrame
    
    Args:
        df: DataFrame containing the records to process
        engine: SQLAlchemy engine
        test_mode: If True, no changes will be made to the database
        update_existing: If True, update existing records
        insert_customer_payid: If True, insert into wf_customer_payid table
        
    Returns:
        Tuple of (inserted_count, updated_count, error_count)
    """
    if len(df) == 0:
        logger.warning("No records to process")
        return 0, 0, 0
    
    inserted = 0
    updated = 0
    errors = 0
    
    # Get table schema with a fresh connection
    with engine.connect() as conn:
        try:
            schema = get_table_schema(conn, 'wf_payments_split')
            if not schema:
                logger.error("Failed to retrieve database schema")
                return 0, 0, 0
        except Exception as e:
            logger.error(f"Error retrieving schema: {e}")
            return 0, 0, 0
    
    # Process records
    records = df.to_dict(orient='records')
    logger.info(f"Processing {len(records)} records...")
    
    # Process records in batches
    batch_size = 10
    for batch_start in range(0, len(records), batch_size):
        batch_end = min(batch_start + batch_size, len(records))
        batch = records[batch_start:batch_end]
        
        batch_errors = 0
        
        for i, record in enumerate(batch):
            record_index = batch_start + i
            try:
                # Convert data types
                converted_record = convert_types_for_db(record, schema)
                
                # Check if record already exists
                bank_ref = record.get('BankReference', '')
                if not bank_ref:
                    logger.warning(f"Record {record_index+1} has no BankReference, skipping")
                    continue
                
                # Use separate connection for each operation
                check_result = execute_sql(
                    engine, 
                    "SELECT ID FROM wf_payments_split WHERE BankReference = :ref", 
                    {"ref": bank_ref}, 
                    fetchall=True
                )
                
                if check_result and len(check_result) > 0 and update_existing:
                    existing_id = check_result[0][0]
                    
                    # Record exists, update it
                    if not test_mode:
                        try:
                            # Build parameterized update query
                            update_fields = []
                            update_params = {"id": existing_id}
                            
                            for k, v in converted_record.items():
                                if k != 'ID' and not k.isdigit():  # Skip ID and numeric column names
                                    update_fields.append(f"`{k}` = :{k}")
                                    update_params[k] = v
                            
                            if update_fields:
                                update_sql = f"UPDATE wf_payments_split SET {', '.join(update_fields)} WHERE ID = :id"
                                execute_sql(engine, update_sql, update_params)
                            else:
                                logger.warning(f"No valid fields to update for record with ID {existing_id}")
                        except Exception as e:
                            logger.error(f"Update error for record ID {existing_id}: {e}")
                            batch_errors += 1
                            continue
                    
                    updated += 1
                    if (record_index+1) % 5 == 0 or record_index+1 == len(records):
                        mode_prefix = "TEST MODE: Would update" if test_mode else "Updated"
                        logger.info(f"{mode_prefix} record {record_index+1}/{len(records)}")
                
                elif not check_result or len(check_result) == 0:
                    # New record, insert it
                    if not test_mode:
                        try:
                            # Build parameterized insert query
                            insert_fields = []
                            insert_values = []
                            insert_params = {}
                            
                            for k, v in converted_record.items():
                                if not k.isdigit() and not k.startswith('0'):
                                    insert_fields.append(f"`{k}`")
                                    insert_values.append(f":{k}")
                                    insert_params[k] = v
                            
                            if insert_fields:
                                insert_sql = f"INSERT INTO wf_payments_split ({', '.join(insert_fields)}) VALUES ({', '.join(insert_values)})"
                                execute_sql(engine, insert_sql, insert_params)
                            else:
                                logger.warning("No valid columns for insert")
                                batch_errors += 1
                        except Exception as e:
                            logger.error(f"Insert error: {e}")
                            batch_errors += 1
                            continue
                    
                    inserted += 1
                    if (record_index+1) % 5 == 0 or record_index+1 == len(records):
                        mode_prefix = "TEST MODE: Would insert" if test_mode else "Inserted"
                        logger.info(f"{mode_prefix} record {record_index+1}/{len(records)}")
            
            except Exception as e:
                batch_errors += 1
                logger.error(f"Error processing record {record_index+1}: {e}")
                logger.error(traceback.format_exc())
        
        # Report batch status
        errors += batch_errors
        
        if not test_mode:
            logger.info(f"Batch {batch_start//batch_size + 1} completed with {batch_errors} errors")
    
    # After all batches, run additional operations
    if not test_mode and (inserted + updated > 0):
        # Insert into wf_customer_payid table
        if insert_customer_payid:
            try:
                # Insert only unique payid records that don't already exist
                payid_query = """
                INSERT IGNORE INTO wf_customer_payid (CompName, CustName, wf_payID, AcctNo)
                SELECT DISTINCT
                    CompName,
                    CustName,
                    wf_payID,
                    AcctNo
                FROM wf_payments_split
                WHERE wf_payID IS NOT NULL
                AND wf_payID NOT IN (SELECT wf_payID FROM wf_customer_payid WHERE wf_payID IS NOT NULL)
                """
                
                rows_inserted = execute_sql(engine, payid_query)
                logger.info(f"Inserted {rows_inserted} records into wf_customer_payid table")
            except Exception as e:
                logger.error(f"Error inserting into wf_customer_payid table: {e}")
        
        # Run the enhanced parse procedure separately (optional)
        try:
            logger.info("Running enhanced parse procedure to process unmapped records...")
            
            # Instead of calling the procedure from Python, we'll make it optional
            # and provide a message to run it manually if needed
            
            # Option 1: Skip the procedure call entirely
            logger.info("Skipping automatic enhanced parse procedure call due to potential connection issues.")
            logger.info("If needed, please run this procedure manually with: CALL enhanced_parse_wf_payments_v2(NULL);")
            
            # Option 2: If you still want to try running it, uncomment this code and comment out Option 1
            # This creates a completely separate connection to run just the stored procedure
            """
            import subprocess
            import tempfile
            
            # Create a temporary SQL file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as sql_file:
                sql_file.write("CALL enhanced_parse_wf_payments_v2(NULL);")
                sql_file_path = sql_file.name
            
            # Run MySQL client directly (assumes mysql client is installed)
            # Get connection info from engine URL
            url = engine.url
            cmd = [
                'mysql', 
                f'--host={url.host}',
                f'--port={url.port}',
                f'--user={url.username}',
                f'--password={url.password}',
                url.database,
                f'--execute=CALL enhanced_parse_wf_payments_v2(NULL);'
            ]
            
            # Run the command
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("Enhanced parse procedure completed successfully via external command")
                else:
                    logger.error(f"Error running enhanced parse procedure via external command: {result.stderr}")
            except Exception as e:
                logger.error(f"Error running external MySQL command: {e}")
                logger.error(traceback.format_exc())
            else:
                # Clean up temp file
                try:
                    os.remove(sql_file_path)
                except:
                    pass
            """
        except Exception as e:
            logger.error(f"Error with enhanced parse procedure handling: {e}")
            logger.error(traceback.format_exc())
        else:
            logger.info("Skipping enhanced parse procedure call due to potential connection issues.")
            logger.info("If needed, please run this procedure manually with: CALL enhanced_parse_wf_payments_v2(NULL);")
    
    return inserted, updated, errors


def import_wf_payments(
    csv_file_path: str,
    engine,
    parser: EnhancedDescriptionParser,
    import_date: Optional[str] = None,
    test_mode: bool = False,
    verify_import: bool = True,
    run_parse_proc: bool = False
) -> bool:
    """
    Import Wells Fargo payment records from CSV file.
    
    Args:
        csv_file_path: Path to the CSV file
        engine: SQLAlchemy engine
        parser: Description parser instance
        import_date: Date to filter records (YYYY-MM-DD format)
        test_mode: If True, no changes will be made to the database
        verify_import: If True, verify import results
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 80)
    logger.info(f"Starting import of Wells Fargo payment records from {csv_file_path}")
    if import_date:
        logger.info(f"Filtering for date: {import_date}")
    if test_mode:
        logger.info("RUNNING IN TEST MODE - NO DATA WILL BE COMMITTED")
    logger.info("=" * 80)
    
    try:
        # Read CSV file
        logger.info(f"Reading CSV file: {csv_file_path}")
        df_raw = pd.read_csv(csv_file_path, encoding='utf-8', low_memory=False)
        df_raw = df_raw.fillna('')  # Replace NaN values with empty strings
        logger.info(f"CSV file loaded with {len(df_raw)} records")
        
        # Filter by transaction type
        orig_count = len(df_raw)
        df_raw = df_raw[df_raw['Tran Desc'].isin(['MISCELLANEOUS ACH CREDIT', 'POSTING ERROR CORRECTION DEBIT'])]
        filt_count = len(df_raw)
        logger.info(f"Filtered to {filt_count} relevant records (removed {orig_count - filt_count} non-matching records)")
        
        if filt_count == 0:
            logger.warning("No records with the required transaction types found")
            return True  # Not a failure, just no relevant records
        
        # Map CSV columns to database columns
        df_mapped = map_csv_to_db(df_raw, parser)
        logger.info("Successfully mapped CSV columns to database schema")
        
        # Apply filtering based on date
        if import_date:
            # Filter by specific date
            date_filter = pd.to_datetime(import_date).strftime('%Y-%m-%d')
            df_filtered = df_mapped[df_mapped['AsOfDate'] == date_filter].copy()
            logger.info(f"Filtered to {len(df_filtered)} records for date {import_date}")
        else:
            # No filtering
            df_filtered = df_mapped.copy()
        
        if len(df_filtered) == 0:
            logger.warning("No records to import after filtering")
            return True
        
        # Process the records
        inserted, updated, errors = process_wf_payment_records(
            df=df_filtered,
            engine=engine,
            test_mode=test_mode,
            update_existing=True,
            insert_customer_payid=True,
            run_parse_proc=run_parse_proc
        )
        
        if test_mode:
            logger.info(f"TEST MODE: Would insert {inserted} records and update {updated} records")
        else:
            logger.info(f"Inserted {inserted} records and updated {updated} records")
        
        # Verify import if requested
        if verify_import and not test_mode:
            try:
                if import_date:
                    # Use a separate connection for verification
                    with engine.connect() as conn:
                        verify_sql = "SELECT COUNT(*) FROM wf_payments_split WHERE AsOfDate = :date"
                        result = conn.execute(text(verify_sql), {"date": import_date})
                        count = result.scalar()
                        logger.info(f"Verified {count} records in database for date {import_date}")
                else:
                    # Check bank references individually to avoid IN clause
                    verified_count = 0
                    bank_refs = df_filtered['BankReference'].dropna().tolist()
                    
                    if bank_refs:
                        for ref in bank_refs:
                            with engine.connect() as conn:
                                check_sql = "SELECT COUNT(*) FROM wf_payments_split WHERE BankReference = :ref"
                                result = conn.execute(text(check_sql), {"ref": ref})
                                if result.scalar() > 0:
                                    verified_count += 1
                                
                        logger.info(f"Verified {verified_count}/{len(bank_refs)} imported bank references in database")
            except Exception as e:
                logger.error(f"Error verifying import: {e}")
                logger.error(traceback.format_exc())
        
        # Print summary
        logger.info("=" * 80)
        logger.info("Import summary")
        logger.info("=" * 80)
        logger.info(f"Total records processed: {len(df_filtered)}")
        logger.info(f"Records inserted: {inserted}")
        logger.info(f"Records updated: {updated}")
        logger.info(f"Records with errors: {errors}")
        if len(df_filtered) > 0:
            logger.info(f"Success rate: {((inserted + updated) / len(df_filtered)) * 100:.2f}%")
        
        return errors == 0
    
    except Exception as e:
        logger.error(f"Unexpected error during import process: {e}")
        logger.error(traceback.format_exc())
        return False


def process_excel_file(
    file_path: str,
    engine,
    parser: EnhancedDescriptionParser,
    import_date: Optional[str] = None,
    test_mode: bool = False,
    verify_import: bool = True,
    run_parse_proc: bool = False
) -> bool:
    """
    Process a single Excel file
    
    Args:
        file_path: Path to the Excel file
        engine: SQLAlchemy engine
        parser: Description parser instance
        import_date: Date to filter records (YYYY-MM-DD format)
        test_mode: If True, no changes will be made to the database
        verify_import: If True, verify import results
        
    Returns:
        True if successful, False otherwise
    """
    file_name = os.path.basename(file_path)
    logger.info(f"Processing Excel file: {file_name}")
    
    try:
        # Create a temporary CSV file
        temp_csv_path = os.path.join(os.path.dirname(file_path), f"temp_{uuid.uuid4().hex}.csv")
        
        # Convert Excel to CSV
        logger.info(f"Converting {file_name} to CSV...")
        df = pd.read_excel(file_path)
        df.to_csv(temp_csv_path, index=False, encoding='utf-8')
        logger.info(f"Conversion successful, saved to {temp_csv_path}")
        
        # Process the CSV file
        success = import_wf_payments(
            csv_file_path=temp_csv_path,
            engine=engine,
            parser=parser,
            import_date=import_date,
            test_mode=test_mode,
            verify_import=verify_import,
            run_parse_proc=run_parse_proc
        )
        
        # Clean up the temporary CSV file
        try:
            os.remove(temp_csv_path)
            logger.info(f"Temporary CSV file removed")
        except Exception as e:
            logger.warning(f"Could not remove temporary CSV file: {e}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing Excel file {file_name}: {e}")
        logger.error(traceback.format_exc())
        return False


def scan_and_process_directory(
    directory_path: str,
    engine,
    parser: EnhancedDescriptionParser,
    import_date: Optional[str] = None,
    test_mode: bool = False,
    verify_import: bool = True,
    move_processed: bool = True,
    run_parse_proc: bool = False
) -> Tuple[int, int]:
    """
    Scan a directory for CSV and Excel files and process them
    
    Args:
        directory_path: Path to scan for files
        engine: SQLAlchemy engine
        parser: Description parser instance
        import_date: Date to filter records (YYYY-MM-DD format)
        test_mode: If True, no changes will be made to the database
        verify_import: If True, verify import results
        move_processed: If True, move processed files to a 'processed' subdirectory
        
    Returns:
        Tuple of (files_processed, files_with_errors)
    """
    logger.info(f"Scanning directory {directory_path} for CSV and Excel files...")
    
    # Create processed directory if needed and if moving files is enabled
    processed_dir = os.path.join(directory_path, 'processed')
    if move_processed and not test_mode:
        os.makedirs(processed_dir, exist_ok=True)
    
    # Scan for files
    csv_files = glob.glob(os.path.join(directory_path, '*.csv'))
    excel_files = glob.glob(os.path.join(directory_path, '*.xlsx'))
    excel_files.extend(glob.glob(os.path.join(directory_path, '*.xls')))
    excel_files.extend(glob.glob(os.path.join(directory_path, '*.xlsm')))
    
    # Combine all files, starting with Excel files
    all_files = excel_files + csv_files
    
    if not all_files:
        logger.info(f"No files found in {directory_path}")
        return 0, 0
    
    logger.info(f"Found {len(all_files)} files to process ({len(excel_files)} Excel, {len(csv_files)} CSV)")
    
    files_processed = 0
    files_with_errors = 0
    
    # Process each file
    for file_path in all_files:
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        try:
            # Process based on file type
            if file_ext in ['.xlsx', '.xls', '.xlsm']:
                success = process_excel_file(
                    file_path=file_path,
                    engine=engine,
                    parser=parser,
                    import_date=import_date,
                    test_mode=test_mode,
                    verify_import=verify_import,
                    run_parse_proc=run_parse_proc
                )
            else:  # CSV files
                success = import_wf_payments(
                    csv_file_path=file_path,
                    engine=engine,
                    parser=parser,
                    import_date=import_date,
                    test_mode=test_mode,
                    verify_import=verify_import
                )
            
            # Move the processed file if needed
            if success and move_processed and not test_mode:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    processed_file_path = os.path.join(
                        processed_dir, 
                        f"{os.path.splitext(file_name)[0]}_{timestamp}{os.path.splitext(file_name)[1]}"
                    )
                    shutil.move(file_path, processed_file_path)
                    logger.info(f"Moved processed file to {processed_file_path}")
                except Exception as e:
                    logger.error(f"Could not move processed file: {e}")
            
            if success:
                files_processed += 1
                logger.info(f"Successfully processed file {file_name}")
            else:
                files_with_errors += 1
                logger.error(f"Error processing file {file_name}")
                
        except Exception as e:
            files_with_errors += 1
            logger.error(f"Error processing file {file_name}: {e}")
            logger.error(traceback.format_exc())
    
    logger.info(f"File processing complete. Processed: {files_processed}, Errors: {files_with_errors}")
    return files_processed, files_with_errors


def main():
    """
    Main entry point for the script.
    Parse command line arguments and run the import process.
    """
    parser = argparse.ArgumentParser(description='Enhanced importer for Wells Fargo payment data')
    parser.add_argument('--csv', type=str, help='Path to a specific CSV file to import')
    parser.add_argument('--date', type=str, help='Date to filter records (YYYY-MM-DD format)')
    parser.add_argument('--directory', type=str, default='X:\\toadd', help='Directory to scan for files')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no database changes)')
    parser.add_argument('--keep-files', action='store_true', help='Do not move processed files')
    parser.add_argument('--run-parse-proc', action='store_true', help='Try to run enhanced_parse_wf_payments_v2 procedure afterward (may cause errors)')
    
    args = parser.parse_args()
    
    try:
        # Initialize database engine and parser
        engine = get_engine('dev')
        parser = EnhancedDescriptionParser()
        
        # Process a specific CSV file if provided
        if args.csv:
            if not os.path.isfile(args.csv):
                logger.error(f"CSV file not found: {args.csv}")
                sys.exit(1)
                
            success = import_wf_payments(
                csv_file_path=args.csv,
                engine=engine,
                parser=parser,
                import_date=args.date,
                test_mode=args.test,
                verify_import=True
            )
            
            if success:
                logger.info("CSV import completed successfully")
                sys.exit(0)
            else:
                logger.error("CSV import failed")
                sys.exit(1)
        
        # Otherwise, scan the directory for files
        directory_path = args.directory
        if not os.path.isdir(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            sys.exit(1)
            
        files_processed, files_with_errors = scan_and_process_directory(
            directory_path=directory_path,
            engine=engine,
            parser=parser,
            import_date=args.date,
            test_mode=args.test,
            verify_import=True,
            move_processed=not args.keep_files,
            run_parse_proc=args.run_parse_proc
        )
        
        # Print a summary
        logger.info("=" * 80)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Files processed: {files_processed}")
        logger.info(f"Files with errors: {files_with_errors}")
        logger.info("=" * 80)
        
        # Exit with appropriate code
        if files_processed > 0 or files_with_errors == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()