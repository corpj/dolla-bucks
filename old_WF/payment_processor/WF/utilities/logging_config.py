"""
Logging configuration for the WF payment processing system.

This module centralizes logging configuration with appropriate levels, formats,
and handlers following best practices for structured logging.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path


def setup_logging(name, level=logging.INFO, log_to_console=True, log_to_file=True):
    """
    Set up a logger with appropriate configuration.
    
    Args:
        name (str): Name of the logger, typically __name__
        level (int): Logging level, default is INFO
        log_to_console (bool): Whether to log to console
        log_to_file (bool): Whether to log to file
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # If handlers are already configured, return the logger
    if logger.handlers:
        return logger
    
    # Create formatter with contextual information
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Ensure log directory exists
        log_dir = Path('logs/wf')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp and module name
        module_name = name.split('.')[-1] if '.' in name else name
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f"{timestamp}_{module_name}.log"
        
        # Create file handler with daily rotation
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when='midnight',
            backupCount=30  # Keep logs for 30 days
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name, level=logging.INFO):
    """
    Get a logger with the specified name and level.
    
    This is a convenience function to create a standardized logger.
    
    Args:
        name (str): Name of the logger, typically __name__
        level (int): Logging level, default is INFO
        
    Returns:
        logging.Logger: Configured logger
    """
    return setup_logging(name, level)
