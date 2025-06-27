"""
Payment service for the WF payment processing system.

This module provides the core business logic for mapping WF payments
to customers and clients, updating payment records, and tracking
payment status.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set

from WF.repositories.account_repository import account_repository
from WF.repositories.customer_repository import customer_repository
from WF.repositories.client_repository import client_repository
from WF.repositories.payment_repository import payment_repository
from WF.services.matching_service import matching_service
from WF.services.confidence_service import confidence_service
from WF.utilities.logging_config import get_logger

logger = get_logger(__name__)


class PaymentMapperService:
    """
    Service for mapping WF payments to customers and clients.
    
    This class implements the core business logic for finding the best matches
    for WF payments, updating payment records, and tracking payment status.
    """
    
    def __init__(self):
        """Initialize the payment mapper service."""
        # Initialize statistics counters
        self.stats = {
            'total_processed': 0,
            'customer_matches': 0,
            'client_matches': 0,
            'no_matches': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0
        }
    
    def initialize(self):
        """
        Initialize the service by loading necessary data.
        
        This method should be called before processing payments to ensure
        all necessary data is loaded and ready to use.
        """
        # Fetch account IDs to help with matching
        self.account_ids = account_repository.get_distinct_account_ids()
        logger.info(f"Loaded {len(self.account_ids)} account IDs for matching")
        
        # Reset statistics
        for key in self.stats:
            self.stats[key] = 0
    
    def process_payment(self, wf_payment: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Process a single WF payment record.
        
        This method attempts to match the payment to a customer or client,
        updates the payment_az table, and marks the WF payment as applied.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record to process
            
        Returns:
            Tuple[bool, str, float]: Success status, match type, and confidence score
            
        Raises:
            Exception: If there's an error processing the payment
        """
        payment_id = wf_payment.get('ID')
        
        if not payment_id:
            logger.error("Payment record missing ID field")
            return False, "error", 0.0
            
        logger.info(f"Processing WF payment {payment_id}")
        
        try:
            # Increment total processed counter
            self.stats['total_processed'] += 1
            
            # Try to match to a customer first
            customer_match, customer_confidence = self._find_customer_match(wf_payment)
            
            if customer_match and confidence_service.is_high_confidence(customer_confidence):
                # We found a good customer match
                logger.info(
                    f"Found high confidence customer match for payment {payment_id}: "
                    f"Customer {customer_match['customer_id']} with score {customer_confidence:.2f}"
                )
                
                # Update statistics
                self.stats['customer_matches'] += 1
                self.stats['high_confidence'] += 1
                
                # Apply the payment
                self._apply_customer_payment(wf_payment, customer_match, customer_confidence)
                
                return True, "customer_match", customer_confidence
                
            # Try client match if customer match wasn't good enough
            client_match, client_confidence = self._find_client_match(wf_payment)
            
            if client_match and confidence_service.is_medium_confidence(client_confidence):
                # We found a good client match
                logger.info(
                    f"Found medium+ confidence client match for payment {payment_id}: "
                    f"Client {client_match['client_id']} with score {client_confidence:.2f}"
                )
                
                # Update statistics
                self.stats['client_matches'] += 1
                
                if confidence_service.is_high_confidence(client_confidence):
                    self.stats['high_confidence'] += 1
                else:
                    self.stats['medium_confidence'] += 1
                
                # Apply the payment
                self._apply_client_payment(wf_payment, client_match, client_confidence)
                
                return True, "client_match", client_confidence
                
            # If we get here, we couldn't find a good match
            logger.warning(
                f"No good match found for payment {payment_id}. "
                f"Best customer score: {customer_confidence:.2f}, "
                f"Best client score: {client_confidence:.2f}"
            )
            
            # Update statistics
            self.stats['no_matches'] += 1
            
            return False, "no_match", max(customer_confidence, client_confidence)
                
        except Exception as e:
            logger.error(f"Error processing payment {payment_id}: {str(e)}")
            raise
    
    def process_batch(self, limit: int = 100) -> Dict[str, Any]:
        """
        Process a batch of unapplied WF payments.
        
        Args:
            limit (int): Maximum number of payments to process, defaults to 100
            
        Returns:
            Dict[str, Any]: Statistics about the processed batch
            
        Raises:
            Exception: If there's an error processing the batch
        """
        try:
            # Initialize the service
            self.initialize()
            
            # Get unapplied payments
            unapplied_payments = payment_repository.get_unapplied_wf_payments(limit)
            
            logger.info(f"Processing batch of {len(unapplied_payments)} unapplied payments")
            
            # Process each payment
            for payment in unapplied_payments:
                self.process_payment(payment)
            
            # Log statistics
            logger.info(f"Batch processing complete. Statistics: {self.stats}")
            
            return self.stats
                
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            raise
    
    def _find_customer_match(self, wf_payment: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Find the best customer match for a WF payment.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            
        Returns:
            Tuple[Optional[Dict[str, Any]], float]: Best customer match and confidence score
        """
        best_match = None
        best_confidence = 0.0
        
        # Try direct customer ID match if available
        if wf_payment.get('CustID') and wf_payment['CustID'].isdigit():
            try:
                customer_id = int(wf_payment['CustID'])
                customer = customer_repository.get_customer_by_id(customer_id)
                
                if customer:
                    confidence = confidence_service.calculate_customer_match_confidence(
                        wf_payment, customer
                    )
                    
                    if confidence > best_confidence:
                        best_match = customer
                        best_confidence = confidence
                        
                        # If we have a high confidence match, return immediately
                        if confidence_service.is_high_confidence(confidence):
                            return best_match, best_confidence
            except:
                # Continue with other matching methods if this fails
                pass
        
        # Try matching by account number
        for account_field in ['AccountNumber', 'FullSubAccount', 'ACCT', 'AcctNo']:
            if wf_payment.get(account_field) and str(wf_payment[account_field]).isdigit():
                try:
                    account_id = float(wf_payment[account_field])
                    # Check if this account ID is in our list of known account IDs
                    if account_id in self.account_ids:
                        customers = customer_repository.get_customers_by_primary_client_ids([account_id])
                        
                        for customer_id, customer in customers.items():
                            confidence = confidence_service.calculate_customer_match_confidence(
                                wf_payment, customer
                            )
                            
                            if confidence > best_confidence:
                                best_match = customer
                                best_confidence = confidence
                                
                                # If we have a high confidence match, return immediately
                                if confidence_service.is_high_confidence(confidence):
                                    return best_match, best_confidence
                except:
                    # Continue with other matching methods if this fails
                    pass
        
        # Try matching by customer name
        if wf_payment.get('CustName'):
            customers = customer_repository.get_customers_by_name(wf_payment['CustName'])
            
            for customer in customers:
                confidence = confidence_service.calculate_customer_match_confidence(
                    wf_payment, customer
                )
                
                if confidence > best_confidence:
                    best_match = customer
                    best_confidence = confidence
                    
                    # If we have a high confidence match, return immediately
                    if confidence_service.is_high_confidence(confidence):
                        return best_match, best_confidence
        
        # Try matching by company name
        if wf_payment.get('CompName'):
            customers = customer_repository.get_customers_by_company(wf_payment['CompName'])
            
            for customer in customers:
                confidence = confidence_service.calculate_customer_match_confidence(
                    wf_payment, customer
                )
                
                if confidence > best_confidence:
                    best_match = customer
                    best_confidence = confidence
                    
                    # If we have a high confidence match, return immediately
                    if confidence_service.is_high_confidence(confidence):
                        return best_match, best_confidence
        
        return best_match, best_confidence
    
    def _find_client_match(self, wf_payment: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Find the best client match for a WF payment.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            
        Returns:
            Tuple[Optional[Dict[str, Any]], float]: Best client match and confidence score
        """
        best_match = None
        best_confidence = 0.0
        
        # Try direct account number match
        for account_field in ['AccountNumber', 'FullSubAccount', 'ACCT', 'AcctNo']:
            if wf_payment.get(account_field):
                client = client_repository.get_client_by_account_number(str(wf_payment[account_field]))
                
                if client:
                    confidence = confidence_service.calculate_client_match_confidence(
                        wf_payment, client
                    )
                    
                    if confidence > best_confidence:
                        best_match = client
                        best_confidence = confidence
                        
                        # If we have a high confidence match, return immediately
                        if confidence_service.is_high_confidence(confidence):
                            return best_match, best_confidence
        
        # Try matching by name
        if wf_payment.get('CustName'):
            clients = client_repository.get_clients_by_name(wf_payment['CustName'])
            
            for client in clients:
                confidence = confidence_service.calculate_client_match_confidence(
                    wf_payment, client
                )
                
                if confidence > best_confidence:
                    best_match = client
                    best_confidence = confidence
                    
                    # If we have a high confidence match, return immediately
                    if confidence_service.is_high_confidence(confidence):
                        return best_match, best_confidence
        
        # Try matching by company name
        if wf_payment.get('CompName'):
            clients = client_repository.get_clients_by_company(wf_payment['CompName'])
            
            for client in clients:
                confidence = confidence_service.calculate_client_match_confidence(
                    wf_payment, client
                )
                
                if confidence > best_confidence:
                    best_match = client
                    best_confidence = confidence
                    
                    # If we have a high confidence match, return immediately
                    if confidence_service.is_high_confidence(confidence):
                        return best_match, best_confidence
        
        return best_match, best_confidence
    
    def _apply_customer_payment(
        self, 
        wf_payment: Dict[str, Any], 
        customer: Dict[str, Any], 
        confidence: float
    ) -> int:
        """
        Apply a WF payment to a customer.
        
        This method creates or updates a record in the payments_az table
        and marks the WF payment as applied.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            customer (Dict[str, Any]): Customer record
            confidence (float): Match confidence score
            
        Returns:
            int: Payment ID in the payments_az table
            
        Raises:
            Exception: If there's an error applying the payment
        """
        try:
            # Get client ID for the customer
            client_ids = customer_repository.get_client_ids_for_customer(customer['customer_id'])
            
            if not client_ids:
                logger.warning(
                    f"Customer {customer['customer_id']} has no associated client IDs"
                )
                return 0
            
            # Use the first client ID associated with the customer
            client_id = client_ids[0]
            
            # Create payment notes
            notes = (
                f"Wells Fargo payment matched to customer {customer['customer_id']} "
                f"({customer['name']}) with confidence {confidence:.2f}. "
                f"Original bank reference: {wf_payment.get('BankReference', 'N/A')}"
            )
            
            # Create or update payment record
            payment_date = wf_payment.get('AsOfDate')
            if not payment_date:
                payment_date = datetime.now().date()
                
            amount = wf_payment.get('CreditAmount', 0.0)
            
            payment_id, is_new = payment_repository.create_or_update_payment_az(
                client_id=client_id,
                amount=amount,
                payment_date=payment_date,
                notes=notes,
                payment_reference=str(wf_payment.get('BankReference', wf_payment.get('ID')))
            )
            
            # Mark WF payment as applied
            payment_repository.update_wf_payment_applied_status(wf_payment['ID'], True)
            
            action = "Created" if is_new else "Updated"
            logger.info(
                f"{action} payment_az record {payment_id} for WF payment {wf_payment['ID']} "
                f"mapped to customer {customer['customer_id']}"
            )
            
            return payment_id
                
        except Exception as e:
            logger.error(
                f"Error applying WF payment {wf_payment['ID']} to customer "
                f"{customer['customer_id']}: {str(e)}"
            )
            raise
    
    def _apply_client_payment(
        self, 
        wf_payment: Dict[str, Any], 
        client: Dict[str, Any], 
        confidence: float
    ) -> int:
        """
        Apply a WF payment to a client.
        
        This method creates or updates a record in the payments_az table
        and marks the WF payment as applied.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            client (Dict[str, Any]): Client record
            confidence (float): Match confidence score
            
        Returns:
            int: Payment ID in the payments_az table
            
        Raises:
            Exception: If there's an error applying the payment
        """
        try:
            # Create payment notes
            notes = (
                f"Wells Fargo payment matched to client {client['client_id']} "
                f"({client['name']}) with confidence {confidence:.2f}. "
                f"Original bank reference: {wf_payment.get('BankReference', 'N/A')}"
            )
            
            # Create or update payment record
            payment_date = wf_payment.get('AsOfDate')
            if not payment_date:
                payment_date = datetime.now().date()
                
            amount = wf_payment.get('CreditAmount', 0.0)
            
            payment_id, is_new = payment_repository.create_or_update_payment_az(
                client_id=client['client_id'],
                amount=amount,
                payment_date=payment_date,
                notes=notes,
                payment_reference=str(wf_payment.get('BankReference', wf_payment.get('ID')))
            )
            
            # Mark WF payment as applied
            payment_repository.update_wf_payment_applied_status(wf_payment['ID'], True)
            
            action = "Created" if is_new else "Updated"
            logger.info(
                f"{action} payment_az record {payment_id} for WF payment {wf_payment['ID']} "
                f"mapped to client {client['client_id']}"
            )
            
            return payment_id
                
        except Exception as e:
            logger.error(
                f"Error applying WF payment {wf_payment['ID']} to client "
                f"{client['client_id']}: {str(e)}"
            )
            raise


# Create a singleton instance
payment_mapper_service = PaymentMapperService()
