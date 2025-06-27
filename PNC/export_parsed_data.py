#!/usr/bin/env python3
"""Export parsed PNC data to CSV for review."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from import_pnc_payments import PNCImporter
import pandas as pd
from datetime import datetime

def main():
    """Export parsed data to CSV."""
    print("Exporting parsed PNC payment data...")
    
    # Create importer in test mode
    importer = PNCImporter(test_mode=True)
    
    # Get CSV files
    csv_files = importer.get_csv_files()
    
    all_records = []
    for file_path in csv_files:
        print(f"\nProcessing: {file_path.name}")
        records = importer.process_csv_file(file_path)
        
        if records is not None:
            print(f"  - Parsed {len(records)} records")
            # Add source file column
            records['SourceFile'] = file_path.name
            all_records.append(records)
    
    if all_records:
        # Combine all records
        master_df = pd.concat(all_records, ignore_index=True)
        
        # Save to CSV
        output_file = f"pnc_parsed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        master_df.to_csv(output_file, index=False)
        
        print(f"\n✓ Exported {len(master_df)} records to {output_file}")
        
        # Show sample data
        print("\nSample parsed data (first 5 records):")
        print(master_df[['AsOfDate', 'Reference', 'Amount', 'CustID', 'CustName', 'CompName']].head())
        
        # Show parsing statistics
        print(f"\nParsing statistics:")
        print(f"  - Records with CustID: {master_df['CustID'].notna().sum()}")
        print(f"  - Records with CompName: {master_df['CompName'].notna().sum()}")
        print(f"  - Records with CustName: {master_df['CustName'].notna().sum()}")
        print(f"  - Total amount: ${master_df['Amount'].sum():,.2f}")
        
        # Create SQL insert statements
        sql_file = f"pnc_insert_statements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(sql_file, 'w') as f:
            f.write("-- PNC Payment Import SQL Statements\n")
            f.write(f"-- Generated: {datetime.now()}\n")
            f.write(f"-- Total records: {len(master_df)}\n\n")
            
            for idx, row in master_df.head(10).iterrows():
                f.write(f"-- Record {idx + 1} from {row['SourceFile']}\n")
                f.write("INSERT INTO pnc_currentday_split (\n")
                f.write("    AsOfDate, BankId, AccountNumber, AccountName, BaiControl,\n")
                f.write("    Currency, Transaction, Amount, CR_DR, ZeroDayFloat,\n")
                f.write("    OneDayFloat, TwoDayFloat, Reference, Description,\n")
                f.write("    CompName, CompID, CustID, CustName, BatchDiscr,\n")
                f.write("    SEC, desc_name, Time, Addenda, applied\n")
                f.write(") VALUES (\n")
                f.write(f"    '{row.get('AsOfDate')}', '{row.get('BankId', '')}', ")
                f.write(f"'{row.get('AccountNumber', '')}', '{row.get('AccountName', '')}', ")
                f.write(f"'{row.get('BaiControl', '')}',\n")
                f.write(f"    '{row.get('Currency', 'USD')}', '{row.get('Transaction', '')}', ")
                f.write(f"{row.get('Amount', 0.0)}, '{row.get('CR_DR', '')}', ")
                f.write(f"{row.get('ZeroDayFloat', 0.0)},\n")
                f.write(f"    {row.get('OneDayFloat', 0.0)}, {row.get('TwoDayFloat', 0.0)}, ")
                desc = str(row.get('Description', '')).replace("'", "''")
                f.write(f"'{row.get('Reference', '')}', '{desc}',\n")
                f.write(f"    '{row.get('CompName', '')}', '{row.get('CompID', '')}', ")
                f.write(f"'{row.get('CustID', '')}', '{row.get('CustName', '')}', ")
                f.write(f"'{row.get('BatchDiscr', '')}',\n")
                f.write(f"    '{row.get('SEC', '')}', '{row.get('desc_name', '')}', ")
                f.write(f"'{row.get('Time', '')}', '{row.get('Addenda', 'NoAddenda')}', 0\n")
                f.write(");\n\n")
        
        print(f"\n✓ Created sample SQL insert statements in {sql_file}")
        
    else:
        print("\n✗ No records found to export")

if __name__ == '__main__':
    main()