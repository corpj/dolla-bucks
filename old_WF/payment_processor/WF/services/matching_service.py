"""
Matching service for the WF payment processing system.

This module provides algorithms for matching strings such as customer names,
company names, and account numbers with various similarity metrics.
"""

import re
import logging
from typing import List, Tuple, Optional
from difflib import SequenceMatcher

from WF.utilities.logging_config import get_logger

logger = get_logger(__name__)


class MatchingService:
    """
    Service for string similarity and pattern matching.
    
    This class provides methods to compare strings using various algorithms
    and determine the similarity between payment data and customer/client records.
    """
    
    def __init__(self):
        """Initialize the matching service with default thresholds."""
        # Thresholds for different confidence levels
        self.high_confidence_threshold = 0.9
        self.medium_confidence_threshold = 0.7
        self.low_confidence_threshold = 0.5
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names.
        
        This function uses multiple methods to calculate similarity and returns
        the best match score.
        
        Args:
            name1 (str): First name to compare
            name2 (str): Second name to compare
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        if not name1 or not name2:
            return 0.0
            
        # Normalize names
        name1 = self._normalize_string(name1)
        name2 = self._normalize_string(name2)
        
        # Exact match
        if name1 == name2:
            return 1.0
        
        # Calculate similarity using different methods and take the best score
        exact_match_score = self._check_exact_match(name1, name2)
        contains_score = self._check_contains(name1, name2)
        token_match_score = self._check_token_match(name1, name2)
        sequence_match_score = self._check_sequence_match(name1, name2)
        
        # Return the highest score
        similarity = max(
            exact_match_score, 
            contains_score, 
            token_match_score, 
            sequence_match_score
        )
        
        return similarity
    
    def calculate_account_similarity(self, account1: str, account2: str) -> float:
        """
        Calculate similarity between two account numbers.
        
        This method is stricter than name similarity because account numbers
        should match more precisely.
        
        Args:
            account1 (str): First account number
            account2 (str): Second account number
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        if not account1 or not account2:
            return 0.0
            
        # Normalize account numbers (remove non-alphanumeric characters)
        account1 = self._normalize_account(account1)
        account2 = self._normalize_account(account2)
        
        # Exact match
        if account1 == account2:
            return 1.0
        
        # Check if one is contained in the other (for partial account numbers)
        if account1 in account2 or account2 in account1:
            # Calculate the length ratio to determine confidence
            max_len = max(len(account1), len(account2))
            min_len = min(len(account1), len(account2))
            if max_len > 0:
                length_ratio = min_len / max_len
                # Adjust score based on length ratio (longer matches are better)
                return 0.8 * length_ratio
            
        # For account numbers, we use a stricter sequence matcher
        return self._check_sequence_match(account1, account2) * 0.8
    
    def is_high_confidence_match(self, similarity: float) -> bool:
        """
        Determine if a similarity score represents a high confidence match.
        
        Args:
            similarity (float): Similarity score to check
            
        Returns:
            bool: True if high confidence, False otherwise
        """
        return similarity >= self.high_confidence_threshold
    
    def is_medium_confidence_match(self, similarity: float) -> bool:
        """
        Determine if a similarity score represents a medium confidence match.
        
        Args:
            similarity (float): Similarity score to check
            
        Returns:
            bool: True if medium confidence, False otherwise
        """
        return (
            similarity >= self.medium_confidence_threshold and 
            similarity < self.high_confidence_threshold
        )
    
    def is_low_confidence_match(self, similarity: float) -> bool:
        """
        Determine if a similarity score represents a low confidence match.
        
        Args:
            similarity (float): Similarity score to check
            
        Returns:
            bool: True if low confidence, False otherwise
        """
        return (
            similarity >= self.low_confidence_threshold and 
            similarity < self.medium_confidence_threshold
        )
    
    def _normalize_string(self, text: str) -> str:
        """
        Normalize a string for comparison.
        
        Args:
            text (str): String to normalize
            
        Returns:
            str: Normalized string
        """
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove common prefixes and suffixes
        prefixes = ["mr", "mrs", "ms", "dr", "prof"]
        for prefix in prefixes:
            if text.startswith(prefix + " "):
                text = text[len(prefix) + 1:]
                break
        
        # Remove punctuation and extra whitespace
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _normalize_account(self, account: str) -> str:
        """
        Normalize an account number for comparison.
        
        Args:
            account (str): Account number to normalize
            
        Returns:
            str: Normalized account number
        """
        if not account:
            return ""
            
        # Remove all non-alphanumeric characters
        account = re.sub(r'[^a-zA-Z0-9]', '', account)
        
        return account
    
    def _check_exact_match(self, text1: str, text2: str) -> float:
        """
        Check if two strings match exactly.
        
        Args:
            text1 (str): First string
            text2 (str): Second string
            
        Returns:
            float: 1.0 if exact match, 0.0 otherwise
        """
        return 1.0 if text1 == text2 else 0.0
    
    def _check_contains(self, text1: str, text2: str) -> float:
        """
        Check if one string contains the other.
        
        Args:
            text1 (str): First string
            text2 (str): Second string
            
        Returns:
            float: Confidence score between 0.0 and 0.9
        """
        if text1 in text2:
            # text1 is contained in text2
            return 0.8 * (len(text1) / len(text2))
        elif text2 in text1:
            # text2 is contained in text1
            return 0.8 * (len(text2) / len(text1))
        else:
            return 0.0
    
    def _check_token_match(self, text1: str, text2: str) -> float:
        """
        Check token-based similarity between two strings.
        
        This splits each string into tokens (words) and compares the token sets.
        
        Args:
            text1 (str): First string
            text2 (str): Second string
            
        Returns:
            float: Similarity score between 0.0 and 0.9
        """
        # Split into tokens
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())
        
        # Empty sets edge case
        if not tokens1 or not tokens2:
            return 0.0
        
        # Calculate intersection and union
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        # Jaccard similarity
        if union:
            jaccard = len(intersection) / len(union)
            return 0.85 * jaccard
        else:
            return 0.0
    
    def _check_sequence_match(self, text1: str, text2: str) -> float:
        """
        Check sequence-based similarity between two strings.
        
        This uses the SequenceMatcher algorithm to calculate similarity.
        
        Args:
            text1 (str): First string
            text2 (str): Second string
            
        Returns:
            float: Similarity score between 0.0 and 0.9
        """
        if not text1 or not text2:
            return 0.0
            
        # Use SequenceMatcher for more complex similarity
        matcher = SequenceMatcher(None, text1, text2)
        similarity = matcher.ratio()
        
        # Scale to a maximum of 0.9
        return 0.9 * similarity


# Create a singleton instance
matching_service = MatchingService()
