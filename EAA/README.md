# EAA Payment Data Processor

This set of scripts processes Federal Employees Activities Association (EAA) payment data from Word documents, converts it to CSV format, and imports it into the SPIDERSYNC database.

## Features

- Extracts employee payment data from Word documents
- Preserves SSNs with leading zeros
- Converts data to CSV format
- Imports data into the SPIDERSYNC database
- Automatic file archiving after successful processing
- Handles Windows Zone.Identifier metadata files
- Command-line interface with flexible options
- Comprehensive logging and error handling
- Matches customer records based on SSN and employer ID

## Files

### Core Processing Scripts
- `eaa_data_processor.py` - Extracts data from Word documents and converts to CSV
- `eaa_db_importer.py` - Enhanced CSV importer with file archiving and CLI support
- `process_eaa_payments.py` - Comprehensive workflow script (DOCX → CSV → Database → Archive)
- `payments_module_menu.py` - Interactive menu-driven interface for payment processing

### Utility Scripts
- `apply_payments.py` - Applies imported payments to customer accounts
- `check_db.py` - Utility script to verify database records
- `check_import_status.py` - Checks import status for specific dates
- `archive_completed_files.py` - Archives successfully imported files
- `test_db_connection.py` - Tests database connectivity and table structure

### Configuration
- `requirements.txt` - Python package dependencies
- `models.py` - SQLAlchemy models for database tables
- `eaa_sqlalchemy_importer.py` - Alternative SQLAlchemy-based importer

## Database Schema

The data is stored in the `eaa_payments` table with the following structure:

- `id` - Auto-incrementing primary key
- `ssn` - Social Security Number (CHAR(9), preserves leading zeros)
- `name` - Employee name
- `amount` - Premium amount
- `company` - Company name
- `report_date` - Report date
- `import_date` - Date and time the record was imported
- `clientID` - Client ID from the customers table (matched by SSN)
- `payment_id` - Unique identifier in format XXXX_MMDDYYYY (last 4 of SSN + date)
- `payment_applied` - Flag indicating if payment has been applied (0=no, 1=yes)
- `date_applied` - Date and time when payment was applied

### Indexes

- `ssn` - Normal index for efficient lookups
- `name` - Fulltext index for name searches
- `payment_id` - Unique index to ensure payment ID uniqueness

### Customer Matching

The system automatically attempts to match EAA payment records to customer records in the database:

1. First, it searches for matches where SSN matches `customers.socsec` AND `customers.employerid` is in (160, 199, 225)
2. If no match is found, it expands the search to any employer
3. Special handling for SSNs with leading zeros (tries with and without leading zero)
4. When a match is found, it updates the `clientID` field with the customer's `primaryclientID`

## Installation

1. Create and activate the virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   .\venv\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Complete Workflow (Recommended)
Process DOCX files from PaymentFiles/EAA directory through the entire workflow:
```bash
# Process all DOCX files, convert to CSV, import to database, and archive
python process_eaa_payments.py

# Process a specific file
python process_eaa_payments.py "Corporate Jewelers062025.docx"

# Convert to CSV only (no database import)
python process_eaa_payments.py --csv-only

# Process without archiving
python process_eaa_payments.py --no-archive
```

### Individual Steps

1. Extract data from Word document to CSV:
   ```bash
   python eaa_data_processor.py
   ```

2. Import CSV data to database:
   ```bash
   # Import all CSV files from PaymentFiles/EAA
   python eaa_db_importer.py
   
   # Import specific file
   python eaa_db_importer.py /path/to/file.csv
   
   # Import without archiving
   python eaa_db_importer.py --no-archive
   ```

3. Apply payments to customer accounts:
   ```bash
   python apply_payments.py
   ```

4. Interactive menu interface:
   ```bash
   python payments_module_menu.py
   ```

### Utility Commands

Check database connection:
```bash
python test_db_connection.py
```

Check import status:
```bash
python check_import_status.py
```

Archive completed files:
```bash
python archive_completed_files.py
```

## File Organization

- **Input Directory**: `/PaymentFiles/EAA/` - Place DOCX files here for processing
- **Archive Directory**: `/PaymentFiles/EAA/archive/` - Processed files are moved here
- **Log Directory**: `/EAA/logs/` - Processing logs are stored here

## Dependencies

- **docx2txt** (0.8) - For extracting text from Word documents
- **pandas** (2.2.0) - For data manipulation
- **mysql-connector-python** (8.3.0) - For database connectivity
- **python-dotenv** (1.0.1) - For environment variable management
- **sqlalchemy** (2.0.25) - For ORM functionality
- **pymysql** (1.1.0) - MySQL driver for SQLAlchemy

## Notes

- SSNs are stored as CHAR(9) to preserve leading zeros
- All dates are stored in YYYY-MM-DD format
- The script automatically extracts company name and report date from the document
- Windows Zone.Identifier metadata files are automatically handled during archiving
- Duplicate imports are prevented by unique payment_id constraint
- All operations are logged with timestamps for audit trails

## Recent Updates (June 2025)

- Added command-line interface to `eaa_db_importer.py` with flexible file/directory options
- Implemented automatic file archiving after successful processing
- Created `process_eaa_payments.py` for complete workflow automation
- Enhanced logging with dedicated log directory and timestamped log files
- Added support for processing files from `/PaymentFiles/EAA/` directory
- Created utility scripts for checking import status and archiving completed files
- Updated to handle Windows Zone.Identifier metadata files
