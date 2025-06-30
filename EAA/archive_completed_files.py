#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Archive Completed EAA Files
---------------------------
This script archives CSV files that have been successfully imported to the database.
"""

import os
import sys
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

def check_if_imported(csv_file, connection):
    """Check if a CSV file's data has been imported to the database."""
    # Extract date from filename
    filename = os.path.basename(csv_file)
    
    # Map filenames to dates
    date_mapping = {
        'CorporateJewelers050925.csv': '2025-05-09',
        'CorporateJewelers060625.csv': '2025-06-06',
        'CorporateJewelers062025.csv': '2025-06-20'
    }
    
    if filename not in date_mapping:
        print(f"Unknown file: {filename}")
        return False
    
    report_date = date_mapping[filename]
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM eaa_payments 
        WHERE report_date = %s
    """, (report_date,))
    
    count = cursor.fetchone()[0]
    cursor.close()
    
    return count > 0

def archive_file(file_path, archive_dir):
    """Archive a file to the specified directory."""
    try:
        os.makedirs(archive_dir, exist_ok=True)
        filename = os.path.basename(file_path)
        archive_path = os.path.join(archive_dir, filename)
        
        # If file already exists in archive, add timestamp
        if os.path.exists(archive_path):
            base, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base}_{timestamp}{ext}"
            archive_path = os.path.join(archive_dir, filename)
        
        shutil.move(file_path, archive_path)
        print(f"✅ Archived: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error archiving {file_path}: {e}")
        return False

def main():
    """Main function to archive completed files."""
    # Paths
    payment_dir = "/home/corpj/projects/dolla-bucks/PaymentFiles/EAA"
    archive_dir = os.path.join(payment_dir, "archive")
    
    # Connect to database
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        print("Failed to connect to database")
        return
    
    print("Checking for completed imports to archive...")
    print("-" * 50)
    
    # Get all CSV files
    csv_files = [f for f in os.listdir(payment_dir) if f.endswith('.csv')]
    
    archived_count = 0
    for csv_file in csv_files:
        file_path = os.path.join(payment_dir, csv_file)
        
        # Check if imported
        if check_if_imported(file_path, connection):
            print(f"\n{csv_file}: Imported ✓")
            if archive_file(file_path, archive_dir):
                archived_count += 1
        else:
            print(f"\n{csv_file}: Not imported yet ⚠️")
    
    # Close connection
    connection.close()
    
    print("\n" + "-" * 50)
    print(f"Total files archived: {archived_count}")
    
    # Show current state
    print("\nRemaining files in PaymentFiles/EAA:")
    remaining = [f for f in os.listdir(payment_dir) 
                 if os.path.isfile(os.path.join(payment_dir, f))]
    if remaining:
        for f in remaining:
            print(f"  - {f}")
    else:
        print("  (directory is clean)")

if __name__ == "__main__":
    main()