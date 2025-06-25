"""
Logging configuration for NLM tool
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    verbose: bool = False
) -> logging.Logger:
    """
    Setup logging configuration for the NLM tool
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        verbose: Enable verbose logging (DEBUG level)
    
    Returns:
        Configured logger instance
    """
    
    # Set log level
    if verbose:
        level = "DEBUG"
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("nlm")
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = "nlm") -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class TestLogger:
    """Specialized logger for test execution"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.logger = get_logger(f"nlm.test.{test_name}")
        self.metrics = []
    
    def log_request(self, method: str, url: str, status_code: int, 
                   response_time: float, timestamp: float):
        """Log individual request details"""
        self.logger.debug(
            f"Request: {method} {url} - Status: {status_code} - "
            f"Time: {response_time:.3f}s"
        )
        
        self.metrics.append({
            "timestamp": timestamp,
            "method": method,
            "url": url,
            "status_code": status_code,
            "response_time": response_time
        })
    
    def log_error(self, error: str, context: str = ""):
        """Log test errors"""
        self.logger.error(f"Test Error [{context}]: {error}")
    
    def log_summary(self, total_requests: int, successful_requests: int,
                   failed_requests: int, avg_response_time: float):
        """Log test summary"""
        self.logger.info(
            f"Test Summary: {total_requests} total, "
            f"{successful_requests} successful, {failed_requests} failed, "
            f"avg response time: {avg_response_time:.3f}s"
        )
    
    def get_metrics(self):
        """Get collected metrics"""
        return self.metrics.copy() 