#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EAA SQLAlchemy Database Importer
--------------------------------
Imports EAA payment data using SQLAlchemy ORM.
Author: Lil Claudy Flossy
"""

import os
import sys
import pandas as pd
from datetime import datetime
import logging
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import EAAPayment, Customer, get_session, create_tables

logger = logging.getLogger(__name__)


class EAAImporter:
    """Handles importing EAA payment data using SQLAlchemy."""
    
    def __init__(self, environment='dev'):
        """Initialize the importer with a database session."""
        self.environment = environment
        self.session = get_session(environment)
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()
        
    def ensure_tables_exist(self):
        """Ensure required tables exist."""
        try:
            create_tables(self.environment)
            logger.info("Database tables verified/created")
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
            
    def import_csv(self, csv_file):
        """
        Import data from CSV file.
        
        Args:
            csv_file (str): Path to CSV file
            
        Returns:
            int: Number of records imported
        """
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Ensure SSNs are properly formatted
            df['ssn'] = df['ssn'].astype(str).str.zfill(9)
            
            # Generate payment IDs
            df['payment_id'] = df.apply(
                lambda row: f"{row['ssn'][-4:]}_{pd.to_datetime(row['report_date']).strftime('%m%d%Y')}", 
                axis=1
            )
            
            records_imported = 0
            
            # Import each row
            for _, row in df.iterrows():
                payment = EAAPayment(
                    ssn=row['ssn'],
                    name=row['name'],
                    amount=float(row['amount']),
                    company=row['company'],
                    report_date=pd.to_datetime(row['report_date']).date(),
                    payment_id=row['payment_id']
                )
                
                try:
                    self.session.add(payment)
                    self.session.commit()
                    records_imported += 1
                except IntegrityError:
                    self.session.rollback()
                    logger.warning(f"Duplicate payment_id: {row['payment_id']} - skipping")
                    
            logger.info(f"Imported {records_imported} records")
            return records_imported
            
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            self.session.rollback()
            return 0
            
    def update_client_ids(self):
        """
        Update client IDs by matching SSNs with customers table.
        
        Returns:
            int: Number of records updated
        """
        try:
            total_updated = 0
            
            # First pass: Match with specific employer IDs
            unmatched_payments = self.session.query(EAAPayment).filter(
                EAAPayment.clientID.is_(None)
            ).all()
            
            for payment in unmatched_payments:
                # Try to find customer with specific employer IDs
                customer = self.session.query(Customer).filter(
                    and_(
                        Customer.SocSec == payment.ssn,
                        Customer.EmployerID.in_([160, 199, 225])
                    )
                ).first()
                
                if customer:
                    payment.clientID = customer.PrimaryClientID
                    total_updated += 1
                    
            self.session.commit()
            logger.info(f"Updated {total_updated} records with specific employer IDs")
            
            # Second pass: Match any remaining SSNs
            second_pass_count = 0
            unmatched_payments = self.session.query(EAAPayment).filter(
                EAAPayment.clientID.is_(None)
            ).all()
            
            for payment in unmatched_payments:
                customer = self.session.query(Customer).filter(
                    Customer.SocSec == payment.ssn
                ).first()
                
                if customer:
                    payment.clientID = customer.PrimaryClientID
                    second_pass_count += 1
                    
            self.session.commit()
            logger.info(f"Updated {second_pass_count} records with any employer ID")
            
            # Third pass: Handle leading zeros
            third_pass_count = 0
            unmatched_payments = self.session.query(EAAPayment).filter(
                EAAPayment.clientID.is_(None)
            ).all()
            
            for payment in unmatched_payments:
                # Try without leading zero
                if payment.ssn.startswith('0'):
                    ssn_without_zero = payment.ssn[1:]
                    customer = self.session.query(Customer).filter(
                        Customer.SocSec == ssn_without_zero
                    ).first()
                    
                    if customer:
                        payment.clientID = customer.PrimaryClientID
                        third_pass_count += 1
                        continue
                        
                # Try with added leading zero
                ssn_with_zero = '0' + payment.ssn
                customer = self.session.query(Customer).filter(
                    Customer.SocSec == ssn_with_zero
                ).first()
                
                if customer:
                    payment.clientID = customer.PrimaryClientID
                    third_pass_count += 1
                    
            self.session.commit()
            logger.info(f"Updated {third_pass_count} records by handling leading zeros")
            
            # Special case for Kenya Brown
            kenya_update = self.session.query(EAAPayment).filter(
                and_(
                    EAAPayment.ssn == '071584406',
                    EAAPayment.clientID.is_(None)
                )
            ).update({'clientID': 1071})
            
            self.session.commit()
            
            if kenya_update > 0:
                logger.info(f"Updated Kenya Brown's record with clientID 1071")
                third_pass_count += kenya_update
                
            total_updated += second_pass_count + third_pass_count
            logger.info(f"Total records updated: {total_updated}")
            
            return total_updated
            
        except Exception as e:
            logger.error(f"Error updating client IDs: {e}")
            self.session.rollback()
            return 0
            
    def get_import_summary(self):
        """Get summary of imported records."""
        try:
            total_records = self.session.query(EAAPayment).count()
            matched_records = self.session.query(EAAPayment).filter(
                EAAPayment.clientID.isnot(None)
            ).count()
            unmatched_records = total_records - matched_records
            
            return {
                'total_records': total_records,
                'matched_records': matched_records,
                'unmatched_records': unmatched_records,
                'match_rate': (matched_records / total_records * 100) if total_records > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return None


def main():
    """Main function for command-line usage."""
    import argparse
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Import EAA payment data using SQLAlchemy')
    parser.add_argument('csv_file', help='CSV file to import')
    parser.add_argument('--env', default='dev', choices=['dev', 'prod'],
                       help='Database environment (default: dev)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV file not found: {args.csv_file}")
        return 1
        
    # Import data
    with EAAImporter(args.env) as importer:
        # Ensure tables exist
        if not importer.ensure_tables_exist():
            return 1
            
        # Import CSV
        records = importer.import_csv(args.csv_file)
        if records == 0:
            logger.error("No records imported")
            return 1
            
        # Update client IDs
        importer.update_client_ids()
        
        # Show summary
        summary = importer.get_import_summary()
        if summary:
            print("\nImport Summary:")
            print(f"Total records: {summary['total_records']}")
            print(f"Matched records: {summary['matched_records']}")
            print(f"Unmatched records: {summary['unmatched_records']}")
            print(f"Match rate: {summary['match_rate']:.2f}%")
            
    return 0


if __name__ == "__main__":
    sys.exit(main())