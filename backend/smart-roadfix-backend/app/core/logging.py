"""Logging configuration for the application."""

import logging
import sys
from typing import Any

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)


class Logger:
    """Custom logger wrapper."""
    
    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        self._logger.critical(message, extra=kwargs)


# Create application logger
logger = Logger("smart_roadfix")
