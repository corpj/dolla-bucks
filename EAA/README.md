# EAA Payment Data Processor

This set of scripts processes Federal Employees Activities Association (EAA) payment data from Word documents, converts it to CSV format, and imports it into the SPIDERSYNC database.

## Features

- Extracts employee payment data from Word documents
- Preserves SSNs with leading zeros
- Converts data to CSV format
- Imports data into the SPIDERSYNC database
- Provides logging and error handling
- Matches customer records based on SSN and employer ID

## Files

- `eaa_data_processor.py` - Extracts data from Word documents and converts to CSV
- `eaa_db_importer.py` - Imports CSV data into the SPIDERSYNC database
- `eaa_main.py` - Main script that orchestrates the entire process
- `check_db.py` - Utility script to verify database records

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

1. First, it searches for matches where SSN matches `customers.socsec` AND `customers.employerid = 160`
2. If no match is found, it expands the search to any employer
3. When a match is found, it updates the `clientID` field with the customer's `primaryclientID`

## Usage

1. Activate the virtual environment:
   ```powershell
.\venv\Scripts\activate
```
2. Run the data processor to extract data from the Word document:
   ```powershell
python eaa_data_processor.py path/to/document.docx
```
3. Run the database importer to import the extracted data:
   ```powershell
python eaa_db_importer.py path/to/csv_file.csv
```
4. Check the database to verify the imported data:
   ```powershell
python check_db.py
```

## Dependencies

- docx2txt - For extracting text from Word documents
- pandas - For data manipulation
- mysql-connector-python - For database connectivity

## Notes

- SSNs are stored as CHAR(9) to preserve leading zeros
- All dates are stored in YYYY-MM-DD format
- The script automatically extracts company name and report date from the document
