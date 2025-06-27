"""
Order-based matching service for the WF payment processing system.

This service is responsible for matching WF payments to order records
using account numbers and historical payment patterns.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from WF.repositories.payment_repository import payment_repository
from WF.repositories.account_repository import account_repository
from WF.utilities.logging_config import get_logger

logger = get_logger(__name__)


class OrderMatchingService:
    """
    Service for matching WF payments to order records.
    
    This service provides methods to match WF payments using account numbers
    from order records and historical payment patterns with payment_type=5.
    """
    
    def __init__(self):
        """Initialize the order matching service."""
        self.payment_repository = payment_repository
        self.account_repository = account_repository
        self.account_ids = set()
    
    def _load_account_ids(self):
        """
        Load account IDs from the order_payment table for matching.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.account_ids = self.account_repository.get_distinct_account_ids()
            logger.info(f"Loaded {len(self.account_ids)} account IDs for matching")
            return True
        except Exception as e:
            logger.error(f"Error loading account IDs: {str(e)}")
            return False
    
    def _check_exact_match(self, account_id: Optional[float]) -> bool:
        """
        Check if an account ID exactly matches an account ID from order_payment.
        
        Args:
            account_id: Account ID to check
            
        Returns:
            bool: True if the account ID is an exact match, False otherwise
        """
        if not account_id:
            return False
            
        # Ensure account IDs are loaded
        if not self.account_ids:
            self._load_account_ids()
            
        return account_id in self.account_ids
    
    def match_payment_by_account(self, wf_payment_id: int, account_id: Optional[float] = None,
                               customer_name: Optional[str] = None, amount: float = 0.0,
                               payment_date: Optional[datetime] = None,
                               reference: Optional[str] = None) -> Tuple[bool, str, float]:
        """
        Match a WF payment to an order record using account ID or customer name with payment history.
        
        Args:
            wf_payment_id: ID of the WF payment to match
            account_id: Account ID to match against (if available)
            customer_name: Customer name for matching (if available)
            amount: Payment amount
            payment_date: Date of the payment
            reference: Payment reference or description
            
        Returns:
            Tuple of (success, match_type, confidence)
        """
        try:
            # Ensure account IDs are loaded
            if not self.account_ids:
                self._load_account_ids()
            
            # Check if we have enough information to attempt a match
            if not account_id and not customer_name:
                logger.warning(f"Not enough information to match payment {wf_payment_id}")
                return False, "unknown", 0.0
                
            payment_reference = reference or f"WF-{wf_payment_id}"
            
            # Try to find a match based on account ID or customer name
            if account_id and self._check_exact_match(account_id):
                logger.info(f"Found exact account match for payment {wf_payment_id}: {account_id}")
                
                # Attempt to match to an order record
                success, payment_az_id = self.payment_repository.match_to_order_payment(
                    wf_payment_id=wf_payment_id,
                    account_id=account_id,
                    amount=amount,
                    payment_date=payment_date,
                    payment_reference=payment_reference,
                    customer_name=customer_name
                )
                
                if success:
                    return True, "order_account", 0.95
                else:
                    logger.warning(f"Failed to match payment {wf_payment_id} despite account ID match")
            
            # If we have a customer name but no account match, try matching by customer name
            # with clients who have payment history
            if customer_name:
                logger.info(f"Attempting to match payment {wf_payment_id} using customer name and payment history")
                
                # Even with no account ID, we can pass None to trigger the payment history matching logic
                success, payment_az_id = self.payment_repository.match_to_order_payment(
                    wf_payment_id=wf_payment_id,
                    account_id=None,  # No account ID for this path
                    amount=amount,
                    payment_date=payment_date,
                    payment_reference=payment_reference,
                    customer_name=customer_name
                )
                
                if success:
                    return True, "payment_history", 0.75
            
            # If we get here, no match was found
            logger.warning(f"No match found for payment {wf_payment_id}")
            return False, "unknown", 0.0
                
        except Exception as e:
            logger.error(f"Error matching payment {wf_payment_id}: {str(e)}")
            return False, "error", 0.0
    
    def process_unmatched_payments(self, limit: int = 100) -> Tuple[int, int]:
        """
        Process unmatched WF payments and attempt to match them using account IDs
        and customer names with payment history.
        
        Args:
            limit: Maximum number of payments to process
            
        Returns:
            Tuple of (processed_count, matched_count)
        """
        try:
            # Ensure account IDs are loaded
            if not self.account_ids:
                self._load_account_ids()
                
            # Get unmatched payments
            payments = self.payment_repository.get_unapplied_wf_payments(limit=limit)
            
            if not payments:
                logger.info("No unmatched payments found")
                return 0, 0
                
            logger.info(f"Processing {len(payments)} unmatched payments")
            
            processed_count = 0
            matched_count = 0
            
            for payment in payments:
                wf_payment_id = payment.get('ID')
                account_id = payment.get('AccountNumber')
                customer_name = payment.get('CustomerName')
                amount = payment.get('Amount', 0.0)
                
                # Convert account ID to float if it's a string
                if account_id and isinstance(account_id, str):
                    try:
                        account_id = float(account_id)
                    except ValueError:
                        account_id = None
                
                # Convert payment date to datetime if it's a string
                payment_date = payment.get('PaymentDate')
                if payment_date and isinstance(payment_date, str):
                    try:
                        payment_date = datetime.strptime(payment_date, '%Y-%m-%d')
                    except ValueError:
                        payment_date = datetime.now()
                
                # Get payment reference
                reference = payment.get('Reference') or f"WF-{wf_payment_id}"
                
                # Attempt to match the payment
                success, match_type, confidence = self.match_payment_by_account(
                    wf_payment_id=wf_payment_id,
                    account_id=account_id,
                    customer_name=customer_name,
                    amount=amount,
                    payment_date=payment_date,
                    reference=reference
                )
                
                processed_count += 1
                
                if success:
                    matched_count += 1
                    
                    # Update payment status
                    self.payment_repository.update_wf_payment_applied_status(
                        payment_id=wf_payment_id,
                        applied=True
                    )
            
            logger.info(f"Processed {processed_count} payments, matched {matched_count}")
            return processed_count, matched_count
                
        except Exception as e:
            logger.error(f"Error processing unmatched payments: {str(e)}")
            return 0, 0


# Create a singleton instance
order_matching_service = OrderMatchingService()
