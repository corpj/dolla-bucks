#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Check today's Corporate Jewelers import"""

import sys
sys.path.append('..')

from utils.MySQLConnectionManager import MySQLConnectionManager
from datetime import date

db_manager = MySQLConnectionManager()
connection = db_manager.connect_to_spidersync('dev')

if connection:
    cursor = connection.cursor()
    
    # Check today's Corporate Jewelers imports
    cursor.execute('''
        SELECT payment_id, name, ssn, amount, company, clientID, 
               CASE WHEN clientID IS NOT NULL THEN 'Matched' ELSE 'Unmatched' END as match_status
        FROM eaa_payments 
        WHERE company = 'CORPORATE JEWELERS' 
        AND report_date = '2025-06-20'
        ORDER BY id DESC
        LIMIT 20
    ''')
    
    print("Corporate Jewelers 06/20/2025 Import Results:")
    print("=" * 80)
    
    records = cursor.fetchall()
    for row in records:
        print(f"Payment ID: {row[0]}")
        print(f"  Name: {row[1]}")
        print(f"  SSN: {row[2]}")
        print(f"  Amount: ${row[3]}")
        print(f"  ClientID: {row[5]} ({row[6]})")
        print("-" * 40)
    
    # Get summary
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN clientID IS NOT NULL THEN 1 ELSE 0 END) as matched,
            SUM(amount) as total_amount
        FROM eaa_payments 
        WHERE company = 'CORPORATE JEWELERS' 
        AND report_date = '2025-06-20'
    ''')
    
    summary = cursor.fetchone()
    print(f"\nSummary:")
    print(f"Total Records: {summary[0]}")
    print(f"Matched Records: {summary[1]}")
    print(f"Unmatched Records: {summary[0] - summary[1]}")
    print(f"Match Rate: {(summary[1]/summary[0]*100):.2f}%")
    print(f"Total Amount: ${summary[2]}")
    
    cursor.close()
    db_manager.close_connection(connection)