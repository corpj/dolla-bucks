#!/usr/bin/env python3
"""Test database connection for PNC import."""

import os
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('SPIDERSYNC_DEV_HOST', 'localhost'),
    'user': os.getenv('SPIDERSYNC_DEV_USER'),
    'password': os.getenv('SPIDERSYNC_DEV_PASSWORD'),
    'database': os.getenv('SPIDERSYNC_DEV_DATABASE', 'spider_sync_DEV'),
    'charset': 'utf8mb4',
    'port': int(os.getenv('SPIDERSYNC_DEV_PORT', '10033'))
}

print("Attempting to connect to database...")
print(f"Host: {db_config['host']}")
print(f"Port: {db_config['port']}")
print(f"User: {db_config['user']}")
print(f"Database: {db_config['database']}")

try:
    conn = pymysql.connect(**db_config)
    print("\n✓ Connection successful!")
    
    with conn.cursor() as cursor:
        # Test query
        cursor.execute("SELECT COUNT(*) FROM pnc_currentday_split")
        count = cursor.fetchone()[0]
        print(f"✓ Found {count} existing records in pnc_currentday_split table")
        
        # Check table structure
        cursor.execute("DESCRIBE pnc_currentday_split")
        columns = cursor.fetchall()
        print("\n✓ Table structure verified. Columns:")
        for col in columns[:5]:  # Show first 5 columns
            print(f"  - {col[0]} ({col[1]})")
        print(f"  ... and {len(columns)-5} more columns")
    
    conn.close()
    print("\n✓ Database connection test completed successfully!")
    
except Exception as e:
    print(f"\n✗ Connection failed: {str(e)}")
    print("\nPossible issues:")
    print("1. Network connectivity to CloudClusters")
    print("2. Firewall blocking port 10166")
    print("3. Database credentials in .env file")
    print("4. VPN or proxy requirements")