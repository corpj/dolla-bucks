#!/usr/bin/env python3
"""Verify PNC import results."""

import os
import pymysql
from dotenv import load_dotenv
from datetime import datetime, date

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('SPIDERSYNC_DEV_HOST'),
    'user': os.getenv('SPIDERSYNC_DEV_USER'),
    'password': os.getenv('SPIDERSYNC_DEV_PASSWORD'),
    'database': os.getenv('SPIDERSYNC_DEV_DATABASE', 'spider_sync_DEV'),
    'charset': 'utf8mb4',
    'port': int(os.getenv('SPIDERSYNC_DEV_PORT', '10033'))
}

try:
    conn = pymysql.connect(**db_config)
    with conn.cursor() as cursor:
        # Check recent imports
        query = """
        SELECT 
            DATE(AsOfDate) as ImportDate,
            COUNT(*) as RecordCount,
            SUM(Amount) as TotalAmount,
            COUNT(DISTINCT CompName) as UniqueCompanies,
            COUNT(DISTINCT CustName) as UniqueCustomers
        FROM pnc_currentday_split
        WHERE AsOfDate >= '2025-06-23'
        GROUP BY DATE(AsOfDate)
        ORDER BY ImportDate DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print("=== Recent PNC Imports ===")
        print(f"{'Date':<12} {'Records':<10} {'Total Amount':<15} {'Companies':<12} {'Customers':<12}")
        print("-" * 65)
        
        for row in results:
            print(f"{str(row[0]):<12} {row[1]:<10} ${row[2]:>13,.2f} {row[3]:<12} {row[4]:<12}")
        
        # Get sample of today's imports
        cursor.execute("""
            SELECT Reference, Amount, CompName, CustName
            FROM pnc_currentday_split
            WHERE DATE(AsOfDate) = '2025-06-27'
            LIMIT 5
        """)
        
        print("\n=== Sample Records from 2025-06-27 ===")
        samples = cursor.fetchall()
        for sample in samples:
            print(f"Ref: {sample[0]}, Amount: ${sample[1]:.2f}, Company: {sample[2]}, Customer: {sample[3]}")
        
        # Check total records in table
        cursor.execute("SELECT COUNT(*) FROM pnc_currentday_split")
        total = cursor.fetchone()[0]
        print(f"\n✓ Total records in pnc_currentday_split: {total:,}")
        
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}")