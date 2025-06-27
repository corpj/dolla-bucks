# PNC Payment Import Script

This is a minimal, refactored version of the PNC payment import script designed for Windows WSL Ubuntu.

## Setup

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Required packages (already installed in venv):
   - pandas
   - pymysql
   - python-dotenv

## Configuration

The script uses environment variables from the `.env` file in the parent directory:
- `DB_HOST` - MySQL host (defaults to localhost)
- `DB_USER` - MySQL username
- `DB_PASSWORD` - MySQL password

The database name is hardcoded as `spider_sync_DEV`.

## Usage

### Test Mode (no database changes):
```bash
python import_pnc_payments.py --test
```

### Production Mode:
```bash
python import_pnc_payments.py
```

## File Locations

- **Input Directory**: `/PaymentFiles/PNC/`
- **Archive Directory**: `/PaymentFiles/PNC/archive/`
- **Log Directory**: `/PNC/logs/`

## Features

- Processes CSV files from the PaymentFiles/PNC directory
- Parses PNC transaction descriptions to extract:
  - Customer ID
  - Description
  - Company Name
  - Company ID
  - Batch Discriminator
  - SEC Code
  - Customer Name
  - Time
  - Addenda
- Archives processed files with timestamp
- Prevents duplicate imports by checking reference numbers
- Comprehensive logging

## Minimum Files Required

This is a standalone script that only requires:
1. `import_pnc_payments.py` - The main script
2. Python virtual environment with required packages
3. Access to the `.env` file for database credentials

## Author
Lil Claudy Flossy

## Modified
2025-06-27