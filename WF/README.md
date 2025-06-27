# Wells Fargo Payment Processing Module

## Overview
This module processes Wells Fargo Excel payment files and inserts them into the `spider_sync_DEV.wf_payments_split` table.

## Setup
1. Activate virtual environment: `source wf_venv/bin/activate`
2. Dependencies are already installed via requirements.txt

## Usage

### Process latest Excel file:
```bash
python wf_excel_importer.py
```

### Process specific file:
```bash
python wf_excel_importer.py --file /path/to/file.xlsx
```

### Process all Excel files in PaymentFiles/WF/:
```bash
python wf_excel_importer.py --all
```

## File Location
- Input files: `../PaymentFiles/WF/*.xlsx`
- Log files: Created in current directory with timestamp

## Database
- Database: spider_sync_DEV
- Table: wf_payments_split
- Connection uses environment variables from ../.env

## Author
Lil Claudy Flossy