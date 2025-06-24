#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EAA Payments Module Menu
------------------------
This script provides a menu-driven interface for the EAA payment processing workflow.
"""

import os
import sys
import logging
import mysql.connector
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'eaa_menu.log')),
        logging.StreamHandler()
    ]
)

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.MySQLConnectionManager import MySQLConnectionManager

class EAAPaymentsMenu:
    def __init__(self):
        """Initialize the EAA Payments Menu."""
        self.db_manager = MySQLConnectionManager()
        self.connection = None
        self.unmatched_records = []
        self.total_records = 0
        self.total_amount = 0
        self.matched_records = 0
        self.manually_matched_records = 0
        self.inserted_records = 0
        
    def connect_to_database(self):
        """Connect to the SPIDERSYNC database."""
        self.connection = self.db_manager.connect_to_spidersync()
        if not self.connection:
            logging.error("Failed to connect to the SPIDERSYNC database")
            print("Failed to connect to the database. Please check your connection settings.")
            return False
        return True
    
    def disconnect_from_database(self):
        """Disconnect from the database."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Database connection closed")
    
    def display_menu(self):
        """Display the main menu options."""
        print("\n" + "=" * 50)
        print("EAA PAYMENTS MODULE MENU")
        print("=" * 50)
        print("1. Import Payments from Word Document")
        print("2. Map Customers to Payments")
        print("3. View Unmatched Records")
        print("4. View Matched Records")
        print("5. Search for Customer by Name")
        print("6. Update Customer ID Manually")
        print("7. Insert Payments into payments_az Table")
        print("8. View Summary Report")
        print("9. Exit")
        print("=" * 50)
        
        choice = input("Enter your choice (1-9): ")
        return choice
    
    def import_payments_from_word(self):
        """Import payments from a Word document."""
        print("\n" + "=" * 50)
        print("IMPORT PAYMENTS FROM WORD DOCUMENT")
        print("=" * 50)
        
        # Use default directory
        default_dir = r"R:\Payments\NewPayments"
        print(f"Using default directory: {default_dir}")
        
        # List available Word documents in the default directory
        word_docs = []
        if os.path.exists(default_dir):
            for file in os.listdir(default_dir):
                if file.endswith(".docx"):
                    word_docs.append(file)
            
            if word_docs:
                print("\nAvailable Word documents:")
                for i, doc in enumerate(word_docs, 1):
                    print(f"{i}. {doc}")
                
                choice = input("\nSelect a document number or enter a custom path: ")
                if choice.isdigit() and 1 <= int(choice) <= len(word_docs):
                    word_doc_path = os.path.join(default_dir, word_docs[int(choice)-1])
                else:
                    word_doc_path = choice
            else:
                print(f"No Word documents found in {default_dir}")
                word_doc_path = input("Enter the path to the Word document: ")
        else:
            print(f"Default directory {default_dir} not found")
            word_doc_path = input("Enter the path to the Word document: ")
        
        if not os.path.exists(word_doc_path):
            print(f"Error: File '{word_doc_path}' does not exist.")
            return
        
        # Extract the year from the document name (assuming format like CorporateJewelers031425.docx)
        filename = os.path.basename(word_doc_path)
        try:
            # Extract year from the last 4 digits before the extension (e.g., 031425 -> 2025)
            year_str = filename[-10:-6]
            if year_str.isdigit():
                year = "20" + year_str
            else:
                # If we can't extract the year, use the current year
                year = str(datetime.now().year)
        except:
            # Default to current year if there's any issue
            year = str(datetime.now().year)
        
        # Call the eaa_data_processor.py script
        cmd = f"python {os.path.join(os.path.dirname(__file__), 'eaa_data_processor.py')} \"{word_doc_path}\""
        print(f"Running command: {cmd}")
        os.system(cmd)
        
        # Get the CSV file path (assuming it's in the same directory with a similar name)
        csv_file = word_doc_path.replace('.docx', '.csv')
        if not os.path.exists(csv_file):
            csv_file = input("Enter the path to the generated CSV file: ")
            if not os.path.exists(csv_file):
                print(f"Error: CSV file '{csv_file}' does not exist.")
                return
        
        # Call the eaa_db_importer.py script
        cmd = f"python {os.path.join(os.path.dirname(__file__), 'eaa_db_importer.py')} \"{csv_file}\""
        print(f"Running command: {cmd}")
        os.system(cmd)
        
        # Auto-map clientIDs based on existing SSN matches
        if self.connect_to_database():
            try:
                cursor = self.connection.cursor()
                
                # Find records with the same SSN in eaa_payments that already have a clientID
                auto_map_query = """
                UPDATE ep1
                JOIN (
                    SELECT ssn, clientID FROM eaa_payments 
                    WHERE clientID IS NOT NULL
                    GROUP BY ssn, clientID
                ) ep2 ON ep1.ssn = ep2.ssn
                SET ep1.clientID = ep2.clientID
                WHERE ep1.clientID IS NULL
                """
                cursor.execute(auto_map_query)
                self.connection.commit()
                
                auto_mapped_count = cursor.rowcount
                if auto_mapped_count > 0:
                    print(f"\nAuto-mapped {auto_mapped_count} records based on existing SSN matches")
                
            except mysql.connector.Error as err:
                print(f"Error during auto-mapping: {err}")
            
            finally:
                self.disconnect_from_database()
        
        # Move the processed files to the appropriate year folder
        year_folder = os.path.join(r"R:\Payments", year)
        
        # Create the year folder if it doesn't exist
        if not os.path.exists(year_folder):
            try:
                os.makedirs(year_folder)
                print(f"Created year folder: {year_folder}")
            except Exception as e:
                print(f"Error creating year folder: {e}")
                return
        
        # Move the Word document
        try:
            target_word_path = os.path.join(year_folder, os.path.basename(word_doc_path))
            if os.path.exists(word_doc_path):
                import shutil
                shutil.copy2(word_doc_path, target_word_path)
                os.remove(word_doc_path)
                print(f"Moved Word document to: {target_word_path}")
        except Exception as e:
            print(f"Error moving Word document: {e}")
        
        # Move the CSV file
        try:
            target_csv_path = os.path.join(year_folder, os.path.basename(csv_file))
            if os.path.exists(csv_file):
                import shutil
                shutil.copy2(csv_file, target_csv_path)
                os.remove(csv_file)
                print(f"Moved CSV file to: {target_csv_path}")
        except Exception as e:
            print(f"Error moving CSV file: {e}")
        
        print("Import completed successfully.")
    
    def map_customers_to_payments(self):
        """Map customers to payments using SSN matching."""
        print("\n" + "=" * 50)
        print("MAP CUSTOMERS TO PAYMENTS")
        print("=" * 50)
        
        if not self.connect_to_database():
            return
        
        try:
            cursor = self.connection.cursor()
            
            # First update: Match SSNs with customers where EmployerID is one of the specified values
            update_query = """
            UPDATE eaa_payments ep
            JOIN customers c ON ep.ssn = c.SocSec AND c.EmployerID IN (160, 199, 225)
            SET ep.clientID = c.PrimaryClientID
            WHERE ep.clientID IS NULL
            """
            cursor.execute(update_query)
            self.connection.commit()
            
            first_update_count = cursor.rowcount
            print(f"Updated {first_update_count} records with EmployerID in (160, 199, 225)")
            
            # Second update: Match any remaining SSNs with customers regardless of EmployerID
            second_update_query = """
            UPDATE eaa_payments ep
            JOIN customers c ON ep.ssn = c.SocSec
            SET ep.clientID = c.PrimaryClientID
            WHERE ep.clientID IS NULL
            """
            cursor.execute(second_update_query)
            self.connection.commit()
            
            second_update_count = cursor.rowcount
            print(f"Updated {second_update_count} records with any EmployerID")
            
            # Third update: Handle SSNs that might be stored without a leading zero
            # Get remaining unmatched records
            cursor.execute("SELECT id, ssn FROM eaa_payments WHERE clientID IS NULL")
            unmatched_records = cursor.fetchall()
            
            third_update_count = 0
            for record_id, ssn in unmatched_records:
                # If SSN starts with a zero, try matching without the leading zero
                if ssn.startswith('0'):
                    ssn_without_leading_zero = ssn[1:]
                    cursor.execute(
                        "SELECT PrimaryClientID FROM customers WHERE SocSec = %s LIMIT 1", 
                        (ssn_without_leading_zero,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        client_id = result[0]
                        cursor.execute(
                            "UPDATE eaa_payments SET clientID = %s WHERE id = %s",
                            (client_id, record_id)
                        )
                        self.connection.commit()
                        third_update_count += 1
                        print(f"Updated record ID {record_id} with SSN {ssn} to match SSN without leading zero {ssn_without_leading_zero}, ClientID: {client_id}")
                
                # Also try the reverse - if the SSN in customers might be stored with an extra leading zero
                cursor.execute(
                    "SELECT PrimaryClientID FROM customers WHERE SocSec = %s LIMIT 1", 
                    ('0' + ssn,)
                )
                result = cursor.fetchone()
                
                if result:
                    client_id = result[0]
                    cursor.execute(
                        "UPDATE eaa_payments SET clientID = %s WHERE id = %s",
                        (client_id, record_id)
                    )
                    self.connection.commit()
                    third_update_count += 1
                    print(f"Updated record ID {record_id} with SSN {ssn} to match SSN with added leading zero {'0' + ssn}, ClientID: {client_id}")
            
            print(f"Updated {third_update_count} records by handling leading zeros")
            
            total_updated = first_update_count + second_update_count + third_update_count
            print(f"Total records updated: {total_updated}")
            
            # Get the remaining unmatched records
            self.refresh_unmatched_records()
            
            if self.unmatched_records:
                print(f"\nThere are {len(self.unmatched_records)} unmatched records.")
                print("Use option 3 to view these records and options 5 and 6 to match them manually.")
            else:
                print("\nAll records have been matched successfully!")
            
            # Prompt user to view matches
            view_matches = input("\nWould you like to view the matched records? (y/n): ")
            if view_matches.lower() == 'y':
                self.view_matched_records()
            
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            logging.error(f"Error mapping customers to payments: {err}")
        
        finally:
            self.disconnect_from_database()
    
    def refresh_unmatched_records(self):
        """Refresh the list of unmatched records."""
        if not self.connection or not self.connection.is_connected():
            if not self.connect_to_database():
                return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, ssn, name, amount, payment_id
                FROM eaa_payments
                WHERE clientID IS NULL
                ORDER BY id
            """)
            self.unmatched_records = cursor.fetchall()
            
            # Get total records and amount
            cursor.execute("SELECT COUNT(*), SUM(amount) FROM eaa_payments")
            result = cursor.fetchone()
            self.total_records = result[0] if result and result[0] is not None else 0
            self.total_amount = float(result[1]) if result and result[1] is not None else 0
            
            # Get matched records count
            cursor.execute("SELECT COUNT(*) FROM eaa_payments WHERE clientID IS NOT NULL")
            result = cursor.fetchone()
            self.matched_records = result[0] if result and result[0] is not None else 0
            
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            logging.error(f"Error refreshing unmatched records: {err}")
    
    def view_unmatched_records(self):
        """View records without a clientID."""
        print("\n" + "=" * 50)
        print("VIEW UNMATCHED RECORDS")
        print("=" * 50)
        
        self.refresh_unmatched_records()
        
        if not self.unmatched_records:
            print("All records have been matched successfully!")
            return
        
        print(f"Found {len(self.unmatched_records)} unmatched records:")
        print("\n{:<5} {:<15} {:<25} {:<10} {:<15}".format(
            "ID", "SSN", "Name", "Amount", "Payment ID"
        ))
        print("-" * 70)
        
        for record in self.unmatched_records:
            print("{:<5} {:<15} {:<25} {:<10} {:<15}".format(
                record[0], 
                record[1], 
                record[2][:25], 
                f"${float(record[3]):.2f}", 
                record[4]
            ))
    
    def view_matched_records(self):
        """View records with a clientID."""
        print("\n" + "=" * 50)
        print("VIEW MATCHED RECORDS")
        print("=" * 50)
        
        if not self.connect_to_database():
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, ssn, name, amount, payment_id, clientID
                FROM eaa_payments
                WHERE clientID IS NOT NULL
                ORDER BY id
            """)
            matched_records = cursor.fetchall()
            
            if not matched_records:
                print("No matched records found.")
                return
            
            print(f"Found {len(matched_records)} matched records:")
            print("\n{:<5} {:<15} {:<25} {:<10} {:<15} {:<10}".format(
                "ID", "SSN", "Name", "Amount", "Payment ID", "ClientID"
            ))
            print("-" * 85)
            
            for record in matched_records:
                print("{:<5} {:<15} {:<25} {:<10} {:<15} {:<10}".format(
                    record[0], 
                    record[1], 
                    record[2][:25], 
                    f"${float(record[3]):.2f}", 
                    record[4],
                    record[5]
                ))
            
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            logging.error(f"Error viewing matched records: {err}")
        
        finally:
            self.disconnect_from_database()
    
    def search_customer_by_name(self):
        """Search for a customer by first and last name."""
        print("\n" + "=" * 50)
        print("SEARCH CUSTOMER BY NAME")
        print("=" * 50)
        
        if not self.connect_to_database():
            return
        
        try:
            first_name = input("Enter first name: ")
            last_name = input("Enter last name: ")
            
            cursor = self.connection.cursor()
            query = """
            SELECT PrimaryClientID, FirstName, LastName, SocSec, EmployerID
            FROM customers
            WHERE FirstName LIKE %s AND LastName LIKE %s
            AND EmployerID IN (160, 199, 225)
            ORDER BY LastName, FirstName
            """
            cursor.execute(query, (f"%{first_name}%", f"%{last_name}%"))
            results = cursor.fetchall()
            
            if not results:
                print("No matching customers found.")
                return
            
            print(f"\nFound {len(results)} matching customers:")
            print("\n{:<10} {:<15} {:<15} {:<15} {:<10}".format(
                "ClientID", "First Name", "Last Name", "SSN", "EmployerID"
            ))
            print("-" * 70)
            
            for result in results:
                print("{:<10} {:<15} {:<15} {:<15} {:<10}".format(
                    result[0], result[1], result[2], result[3], result[4]
                ))
            
            client_id = input("\nEnter the ClientID to use (or press Enter to cancel): ")
            if client_id:
                record_id = input("Enter the payment record ID to update: ")
                if record_id:
                    cursor.execute(
                        "UPDATE eaa_payments SET clientID = %s WHERE id = %s",
                        (client_id, record_id)
                    )
                    self.connection.commit()
                    
                    if cursor.rowcount > 0:
                        print(f"Successfully updated record ID {record_id} with ClientID {client_id}")
                        self.manually_matched_records += 1
                    else:
                        print(f"Failed to update record ID {record_id}")
            
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            logging.error(f"Error searching for customer: {err}")
        
        finally:
            self.disconnect_from_database()
    
    def update_customer_id_manually(self):
        """Update customer ID manually for unmatched records."""
        print("\n" + "=" * 50)
        print("UPDATE CUSTOMER ID MANUALLY")
        print("=" * 50)
        
        if not self.connect_to_database():
            return
        
        try:
            # Refresh the list of unmatched records
            self.refresh_unmatched_records()
            
            if not self.unmatched_records:
                print("No unmatched records found.")
                return
            
            # Display unmatched records for selection
            print(f"Found {len(self.unmatched_records)} unmatched records:")
            print("\n{:<5} {:<15} {:<25} {:<10} {:<15}".format(
                "ID", "SSN", "Name", "Amount", "Payment ID"
            ))
            print("-" * 75)
            
            for record in self.unmatched_records:
                print("{:<5} {:<15} {:<25} {:<10} {:<15}".format(
                    record[0], 
                    record[1], 
                    record[2][:25], 
                    f"${float(record[3]):.2f}", 
                    record[4]
                ))
            
            # Prompt user to select a record
            record_id = input("\nEnter the ID of the record to update (or 'q' to quit): ")
            if record_id.lower() == 'q':
                return
            
            # Validate the record ID
            selected_record = None
            for record in self.unmatched_records:
                if str(record[0]) == record_id:
                    selected_record = record
                    break
            
            if not selected_record:
                print(f"Record with ID {record_id} not found in unmatched records.")
                return
            
            # Display the selected record
            print("\nSelected Record:")
            print(f"ID: {selected_record[0]}")
            print(f"SSN: {selected_record[1]}")
            print(f"Name: {selected_record[2]}")
            print(f"Amount: ${float(selected_record[3]):.2f}")
            print(f"Payment ID: {selected_record[4]}")
            
            # Search for customer or enter client ID directly
            search_option = input("\nWould you like to search for a customer (s) or enter a client ID directly (d)? (s/d): ")
            
            if search_option.lower() == 's':
                # Search for customer
                self.search_customer_by_name()
                client_id = input("\nEnter the client ID for this record: ")
            else:
                # Enter client ID directly
                client_id = input("\nEnter the client ID for this record: ")
            
            # Validate client ID
            if not client_id.strip():
                print("Client ID cannot be empty.")
                return
            
            # Update the record
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE eaa_payments SET clientID = %s WHERE id = %s",
                (client_id, selected_record[0])
            )
            self.connection.commit()
            
            print(f"\nUpdated record ID {selected_record[0]} with client ID {client_id}")
            
            # Check if there are more unmatched records
            self.refresh_unmatched_records()
            if self.unmatched_records:
                update_more = input(f"\nThere are {len(self.unmatched_records)} more unmatched records. Would you like to update another? (y/n): ")
                if update_more.lower() == 'y':
                    self.update_customer_id_manually()
            else:
                print("\nAll records have been matched successfully!")
            
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            logging.error(f"Error updating customer ID manually: {err}")
        
        finally:
            self.disconnect_from_database()
    
    def insert_payments_into_payments_az(self):
        """Insert payments into the payments_az table."""
        print("\n" + "=" * 50)
        print("INSERT PAYMENTS INTO PAYMENTS_AZ TABLE")
        print("=" * 50)
        
        if not self.connect_to_database():
            return
        
        try:
            cursor = self.connection.cursor()
            
            # Get all matched records that haven't been applied yet
            cursor.execute("""
                SELECT ep.id, ep.ssn, ep.name, ep.amount, ep.payment_id, ep.clientID, 
                       c.FirstName, c.LastName, c.SocSec
                FROM eaa_payments ep
                JOIN customers c ON ep.clientID = c.PrimaryClientID
                WHERE ep.clientID IS NOT NULL AND ep.payment_applied = 0
                ORDER BY ep.id
            """)
            
            matched_records = cursor.fetchall()
            
            if not matched_records:
                print("No matched records found that haven't been applied yet.")
                return
            
            # Display the records that will be inserted
            print(f"Found {len(matched_records)} matched records to insert:")
            print("\n{:<5} {:<15} {:<25} {:<10} {:<15} {:<10} {:<15} {:<15}".format(
                "ID", "SSN", "EAA Name", "Amount", "Payment ID", "ClientID", "First Name", "Last Name"
            ))
            print("-" * 120)
            
            total_amount = 0
            for record in matched_records:
                print("{:<5} {:<15} {:<25} {:<10} {:<15} {:<10} {:<15} {:<15}".format(
                    record[0], 
                    record[1], 
                    record[2][:25], 
                    f"${float(record[3]):.2f}", 
                    record[4],
                    record[5],
                    record[6][:15],
                    record[7][:15]
                ))
                total_amount += float(record[3])
            
            print(f"\nTotal Amount to Insert: ${total_amount:.2f}")
            
            # Confirm before proceeding
            confirm = input("\nDo you want to insert these payments into the payments_az table? (y/n): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return
            
            # Get today's date for the notes field
            today = datetime.now().strftime("%m/%d/%Y")
            
            # Insert each record into the payments_az table
            inserted_count = 0
            for record in matched_records:
                payment_id = record[4]
                client_id = record[5]
                amount = float(record[3])
                notes = f"EAA Payment Applied for {today}"
                
                cursor.execute("""
                    INSERT INTO payments_az (clientID, payment_type, amount, notes, payment_id)
                    VALUES (%s, 14, %s, %s, %s)
                """, (client_id, amount, notes, payment_id))
                
                # Mark the record as applied in the eaa_payments table
                cursor.execute("""
                    UPDATE eaa_payments
                    SET payment_applied = 1
                    WHERE payment_id = %s
                """, (payment_id,))
                
                inserted_count += 1
            
            self.connection.commit()
            
            print(f"\nSuccessfully inserted {inserted_count} payments into the payments_az table.")
            print(f"Total amount inserted: ${total_amount:.2f}")
            
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            logging.error(f"Error inserting payments into payments_az table: {err}")
        
        finally:
            self.disconnect_from_database()
    
    def view_summary_report(self):
        """View a summary report of the payment processing."""
        print("\n" + "=" * 50)
        print("SUMMARY REPORT")
        print("=" * 50)
        
        if not self.connect_to_database():
            return
        
        try:
            cursor = self.connection.cursor()
            
            # Get total records and amount
            cursor.execute("SELECT COUNT(*), SUM(amount) FROM eaa_payments")
            result = cursor.fetchone()
            total_records = result[0] if result and result[0] is not None else 0
            total_amount = float(result[1]) if result and result[1] is not None else 0
            
            # Get matched records
            cursor.execute("SELECT COUNT(*) FROM eaa_payments WHERE clientID IS NOT NULL")
            matched_records = cursor.fetchone()[0]
            
            # Get applied records
            cursor.execute("SELECT COUNT(*), SUM(amount) FROM eaa_payments WHERE payment_applied = 1")
            result = cursor.fetchone()
            applied_records = result[0] if result and result[0] is not None else 0
            applied_amount = float(result[1]) if result and result[1] is not None else 0
            
            # Get records in payments_az
            cursor.execute("""
                SELECT COUNT(*), SUM(amount)
                FROM payments_az
                WHERE payment_type = 14
                AND payment_id IN (SELECT payment_id FROM eaa_payments)
            """)
            result = cursor.fetchone()
            payments_az_records = result[0] if result and result[0] is not None else 0
            payments_az_amount = float(result[1]) if result and result[1] is not None else 0
            
            print(f"Total Records in eaa_payments: {total_records}")
            print(f"Total Amount: ${total_amount:.2f}")
            print(f"Matched Records: {matched_records} ({matched_records/total_records*100:.1f}%)")
            print(f"Applied Records: {applied_records} ({applied_records/total_records*100:.1f}%)")
            print(f"Records in payments_az: {payments_az_records} ({payments_az_records/total_records*100:.1f}%)")
            print(f"Amount in payments_az: ${payments_az_amount:.2f} ({payments_az_amount/total_amount*100:.1f}%)")
            
            if payments_az_amount != applied_amount:
                print("\nWARNING: The amount in payments_az does not match the applied amount in eaa_payments!")
                print(f"Difference: ${payments_az_amount - applied_amount:.2f}")
            
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            logging.error(f"Error generating summary report: {err}")
        
        finally:
            self.disconnect_from_database()
    
    def run(self):
        """Run the menu-driven interface."""
        while True:
            choice = self.display_menu()
            
            if choice == '1':
                self.import_payments_from_word()
            elif choice == '2':
                self.map_customers_to_payments()
            elif choice == '3':
                self.view_unmatched_records()
            elif choice == '4':
                self.view_matched_records()
            elif choice == '5':
                self.search_customer_by_name()
            elif choice == '6':
                self.update_customer_id_manually()
            elif choice == '7':
                self.insert_payments_into_payments_az()
            elif choice == '8':
                self.view_summary_report()
            elif choice == '9':
                print("\nExiting EAA Payments Module. Goodbye!")
                break
            else:
                print("\nInvalid choice. Please try again.")
            
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    menu = EAAPaymentsMenu()
    menu.run()
