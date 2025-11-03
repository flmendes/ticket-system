"""Logging configuration."""
import logging
import sys


def setup_logging(service_name: str, level: str = "INFO", json_logs: bool = False) -> logging.Logger:
    """
    Setup standardized logging.

    Args:
        service_name: Name of the service
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Whether to use JSON format (for production)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    if json_logs:
        # In production, you might want to use python-json-logger
        # For now, use structured format
        formatter = logging.Formatter(
            '{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}'
        )
    else:
        # Development-friendly format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
