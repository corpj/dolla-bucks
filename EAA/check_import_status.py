#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Check import status for EAA payments"""

import sys
sys.path.append('..')
from utils.MySQLConnectionManager import MySQLConnectionManager

manager = MySQLConnectionManager()
conn = manager.connect_to_spidersync()

if conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            report_date,
            COUNT(*) as record_count,
            SUM(amount) as total_amount
        FROM eaa_payments 
        WHERE report_date IN ('2025-05-09', '2025-06-06', '2025-06-20')
        GROUP BY report_date
        ORDER BY report_date
    """)
    results = cursor.fetchall()
    print('Import Status Summary:')
    print('-' * 50)
    for row in results:
        print(f'Date: {row[0]} | Records: {row[1]} | Total: ${float(row[2]):.2f}')
    print('-' * 50)
    
    # Check if 06/06/2025 is missing
    cursor.execute("""
        SELECT COUNT(*) 
        FROM eaa_payments 
        WHERE report_date = '2025-06-06'
    """)
    june6_count = cursor.fetchone()[0]
    
    if june6_count == 0:
        print('\n✅ Data from 06/06/2025 has NOT been imported yet')
        print('   File: CorporateJewelers060625.csv can be imported')
    
    cursor.close()
    conn.close()