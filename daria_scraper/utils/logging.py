"""
Logging utilities for the Daria scraper.
"""

import logging
from pathlib import Path

def setup_logging(log_config):
    """
    Set up logging configuration.

    Args:
        log_config: Dictionary with logging configuration

    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    log_file = Path(log_config["LOG_FILE"])
    log_file.parent.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_config["LEVEL"]),
        format=log_config["LOG_FORMAT"],
        handlers=[
            logging.FileHandler(log_config["LOG_FILE"]),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger("daria_scraper")

    # Log startup message
    logger.info("Logging initialized at level %s", log_config["LEVEL"])

    return logger

def get_logger(name=None):
    """
    Get a logger instance.

    Args:
        name: Logger name (optional)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"daria_scraper.{name}")
    return logging.getLogger("daria_scraper")
