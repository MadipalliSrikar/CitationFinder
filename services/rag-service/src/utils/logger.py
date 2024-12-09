import logging
import sys
from typing import Optional

def setup_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """Setup logger with consistent formatting and level"""
    
    logger = logging.getLogger(name)
    
    # Set log level (default to INFO if not specified)
    log_level = log_level if log_level is not None else logging.INFO
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Add handler if not already added
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger