"""
Confidence service for the WF payment processing system.

This module provides methods to calculate confidence scores for matches
between payment records and customer/client records.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from WF.services.matching_service import matching_service
from WF.utilities.logging_config import get_logger

logger = get_logger(__name__)


class ConfidenceService:
    """
    Service for calculating match confidence scores.
    
    This class combines multiple similarity scores with different weights
    to calculate an overall confidence score for a potential match.
    """
    
    def __init__(self):
        """Initialize the confidence service with default weights."""
        # Weights for different match components
        self.weights = {
            'name': 0.35,
            'company': 0.25,
            'account': 0.40
        }
        
        # Thresholds for different confidence levels (adjusted for testing)
        self.high_confidence_threshold = 0.60  # Lowered from 0.85
        self.medium_confidence_threshold = 0.50  # Lowered from 0.65
        self.low_confidence_threshold = 0.40  # Lowered from 0.45
    
    def calculate_customer_match_confidence(
        self, 
        wf_payment: Dict[str, Any], 
        customer: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for a customer match.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            customer (Dict[str, Any]): Customer record
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        # Direct ID match provides highest confidence
        if self._has_direct_id_match(wf_payment, customer):
            return 1.0
        
        # Calculate individual similarity scores
        name_similarity = self._calculate_name_similarity(wf_payment, customer)
        company_similarity = self._calculate_company_similarity(wf_payment, customer)
        account_similarity = self._calculate_account_similarity(wf_payment, customer)
        
        # Calculate weighted average
        confidence = (
            self.weights['name'] * name_similarity +
            self.weights['company'] * company_similarity + 
            self.weights['account'] * account_similarity
        )
        
        logger.debug(
            f"Customer match confidence: {confidence:.2f} "
            f"(name: {name_similarity:.2f}, company: {company_similarity:.2f}, "
            f"account: {account_similarity:.2f})"
        )
        
        return confidence
    
    def calculate_client_match_confidence(
        self, 
        wf_payment: Dict[str, Any], 
        client: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for a client match.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            client (Dict[str, Any]): Client record
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        # Direct account match provides high confidence for clients
        if self._has_direct_account_match(wf_payment, client):
            return 0.95
        
        # Calculate individual similarity scores
        name_similarity = self._calculate_name_similarity(wf_payment, client)
        company_similarity = self._calculate_company_similarity(wf_payment, client)
        account_similarity = self._calculate_account_similarity(wf_payment, client)
        
        # Calculate weighted average
        confidence = (
            self.weights['name'] * name_similarity +
            self.weights['company'] * company_similarity + 
            self.weights['account'] * account_similarity
        )
        
        logger.debug(
            f"Client match confidence: {confidence:.2f} "
            f"(name: {name_similarity:.2f}, company: {company_similarity:.2f}, "
            f"account: {account_similarity:.2f})"
        )
        
        return confidence
    
    def is_high_confidence(self, confidence: float) -> bool:
        """
        Determine if a confidence score is high confidence.
        
        Args:
            confidence (float): Confidence score to check
            
        Returns:
            bool: True if high confidence, False otherwise
        """
        return confidence >= self.high_confidence_threshold
    
    def is_medium_confidence(self, confidence: float) -> bool:
        """
        Determine if a confidence score is medium confidence.
        
        Args:
            confidence (float): Confidence score to check
            
        Returns:
            bool: True if medium confidence, False otherwise
        """
        return (
            confidence >= self.medium_confidence_threshold and 
            confidence < self.high_confidence_threshold
        )
    
    def is_low_confidence(self, confidence: float) -> bool:
        """
        Determine if a confidence score is low confidence.
        
        Args:
            confidence (float): Confidence score to check
            
        Returns:
            bool: True if low confidence, False otherwise
        """
        return (
            confidence >= self.low_confidence_threshold and 
            confidence < self.medium_confidence_threshold
        )
    
    def _has_direct_id_match(self, wf_payment: Dict[str, Any], customer: Dict[str, Any]) -> bool:
        """
        Check if there's a direct ID match between payment and customer.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            customer (Dict[str, Any]): Customer record
            
        Returns:
            bool: True if there's a direct ID match, False otherwise
        """
        # Check for customer ID match
        if (
            wf_payment.get('CustID') and 
            customer.get('customer_id') and 
            str(wf_payment['CustID']) == str(customer['customer_id'])
        ):
            return True
        
        # Check for primary client ID match with account number
        if (
            customer.get('primary_client_id') and 
            wf_payment.get('AccountNumber') and 
            str(customer['primary_client_id']) == str(wf_payment['AccountNumber'])
        ):
            return True
        
        return False
    
    def _has_direct_account_match(self, wf_payment: Dict[str, Any], client: Dict[str, Any]) -> bool:
        """
        Check if there's a direct account match between payment and client.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            client (Dict[str, Any]): Client record
            
        Returns:
            bool: True if there's a direct account match, False otherwise
        """
        # Check different account number fields
        if client.get('account_number'):
            client_account = str(client['account_number'])
            
            # Check against various WF payment account fields
            account_fields = [
                'AccountNumber', 'FullSubAccount', 'ACCT', 'AcctNo', 'SubAccount'
            ]
            
            for field in account_fields:
                if (
                    wf_payment.get(field) and 
                    str(wf_payment[field]) == client_account
                ):
                    return True
        
        return False
    
    def _calculate_name_similarity(
        self, 
        wf_payment: Dict[str, Any], 
        entity: Dict[str, Any]
    ) -> float:
        """
        Calculate name similarity between payment and entity.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            entity (Dict[str, Any]): Customer or client record
            
        Returns:
            float: Name similarity score between 0.0 and 1.0
        """
        if not wf_payment.get('CustName') or not entity.get('name'):
            return 0.0
        
        return matching_service.calculate_name_similarity(
            wf_payment['CustName'], 
            entity['name']
        )
    
    def _calculate_company_similarity(
        self, 
        wf_payment: Dict[str, Any], 
        entity: Dict[str, Any]
    ) -> float:
        """
        Calculate company name similarity between payment and entity.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            entity (Dict[str, Any]): Customer or client record
            
        Returns:
            float: Company similarity score between 0.0 and 1.0
        """
        if not wf_payment.get('CompName') or not entity.get('company'):
            return 0.0
        
        return matching_service.calculate_name_similarity(
            wf_payment['CompName'], 
            entity['company']
        )
    
    def _calculate_account_similarity(
        self, 
        wf_payment: Dict[str, Any], 
        entity: Dict[str, Any]
    ) -> float:
        """
        Calculate account number similarity between payment and entity.
        
        Args:
            wf_payment (Dict[str, Any]): WF payment record
            entity (Dict[str, Any]): Customer or client record
            
        Returns:
            float: Account similarity score between 0.0 and 1.0
        """
        # For customers, check primary client ID against account numbers
        if entity.get('primary_client_id'):
            entity_account = str(entity['primary_client_id'])
        # For clients, check account number
        elif entity.get('account_number'):
            entity_account = str(entity['account_number'])
        else:
            return 0.0
        
        # Check against various WF payment account fields
        account_fields = [
            'AccountNumber', 'FullSubAccount', 'ACCT', 'AcctNo', 'SubAccount'
        ]
        
        max_similarity = 0.0
        for field in account_fields:
            if wf_payment.get(field):
                similarity = matching_service.calculate_account_similarity(
                    str(wf_payment[field]), 
                    entity_account
                )
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity


# Create a singleton instance
confidence_service = ConfidenceService()
