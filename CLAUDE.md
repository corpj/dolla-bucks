# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dolla-bucks is a Python-based payment processing system for Federal Employees Activities Association (EAA) data. It extracts payment data from Word documents, processes it through CSV files, and imports it into a MySQL database for customer matching and payment application.

## Development Commands

### Running Core Scripts
```bash
# Main orchestrator for complete workflow
python EAA/eaa_main.py

# Process Word document to CSV
python EAA/eaa_data_processor.py <docx_file>

# Import CSV to database
python EAA/eaa_db_importer.py <csv_file>

# Menu-driven interface (recommended for most operations)
python EAA/payments_module_menu.py

# Apply payments
python EAA/apply_payments.py
```

### Database Verification
```bash
# Check database records
python EAA/check_db.py

# Check specific payment batch
python EAA/check_payment_batch.py <payment_id>

# Verify customer mappings
python EAA/check_customers.py
```

## Architecture

### Data Flow
1. **Input**: Word documents (.docx) containing payment data
2. **Processing**: Extract data preserving SSN formatting (with leading zeros)
3. **Storage**: CSV files organized by year (format: eaa_XXXX_MMDDYYYY.csv)
4. **Database**: MySQL SPIDERSYNC database with tables:
   - `eaa_payments`: Raw payment records
   - `customers`: Customer master data
   - `payments_az`: Applied payments

### Key Components
- **eaa_data_processor.py**: Extracts data from Word docs, creates formatted CSV
- **eaa_db_importer.py**: Imports CSV to database, matches customers by SSN
- **payments_module_menu.py**: Interactive menu system for workflow management
- **MySQLConnectionManager**: Utility class for database operations

### Customer Matching Logic
- Matches on SSN with employer IDs: 160, 199, or 225
- Preserves SSN leading zeros throughout process
- Updates client_id and client_name upon successful match

## Project Standards (from RULES.md)

### Author Attribution
- All commits and documentation must use "Lil Claudy Flossy" as author name

### Database Operations
- Use MySQLConnectionManager for all database connections
- Never hardcode credentials
- Always use parameterized queries
- Log all database operations

### Error Handling
- All database operations must be wrapped in try-except blocks
- Log errors with timestamp and operation context
- Maintain separate log files for different operations

### File Organization
- Payment files automatically organized into year folders (e.g., 2024/)
- CSV naming convention: eaa_XXXX_MMDDYYYY.csv
- Log files: operation_YYYYMMDD_HHMMSS.log

## Workflow Process

1. **Import Phase**: Process Word document → Generate CSV
2. **Mapping Phase**: Import CSV to database → Match customers
3. **Application Phase**: Apply payments to customer accounts
4. **Verification**: Check imported records and payment status

## Important Notes

- SSN formatting is critical - always preserve leading zeros
- Payment IDs follow format: XXXX_MMDDYYYY (4-digit sequence + date)
- Customer matching requires exact SSN match with specific employer IDs
- All file paths should be relative to the EAA/ directory
- Comprehensive logging is required for audit trails