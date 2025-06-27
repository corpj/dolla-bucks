#!/usr/bin/env python3
"""Inspect Excel file structure to understand columns"""

import pandas as pd
import sys

def inspect_excel(file_path):
    """Read Excel file and show column information."""
    df = pd.read_excel(file_path)
    
    print(f"File: {file_path}")
    print(f"Total rows: {len(df)}")
    print(f"\nColumns in Excel file:")
    for i, col in enumerate(df.columns):
        print(f"{i+1}. '{col}'")
    
    print("\nFirst row of data:")
    if len(df) > 0:
        for col in df.columns:
            print(f"{col}: {df.iloc[0][col]}")

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "../PaymentFiles/WF/20250627.xlsx"
    inspect_excel(file_path)