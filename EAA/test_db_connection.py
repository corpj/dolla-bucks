#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Database Connection for EAA
--------------------------------
This script tests the database connection and verifies the eaa_payments table structure.
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager


def test_connection():
    """Test the database connection."""
    print("Testing database connection...")
    
    # Create connection manager
    db_manager = MySQLConnectionManager()
    connection = db_manager.connect_to_spidersync()
    
    if not connection:
        print("❌ Failed to connect to the database.")
        return False
    
    print("✅ Successfully connected to the database!")
    
    try:
        cursor = connection.cursor()
        
        # Check if eaa_payments table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'eaa_payments'
        """)
        
        table_exists = cursor.fetchone()[0] > 0
        
        if table_exists:
            print("✅ eaa_payments table exists!")
            
            # Get table structure
            cursor.execute("DESCRIBE eaa_payments")
            columns = cursor.fetchall()
            
            print("\nTable structure:")
            print("-" * 50)
            for col in columns:
                print(f"{col[0]:<20} {col[1]:<20} {col[2]}")
            
            # Get record count
            cursor.execute("SELECT COUNT(*) FROM eaa_payments")
            count = cursor.fetchone()[0]
            print(f"\nTotal records: {count}")
            
        else:
            print("⚠️  eaa_payments table does not exist. It will be created on first import.")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False
        
    finally:
        db_manager.close_connection(connection)


if __name__ == "__main__":
    test_connection()