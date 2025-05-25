"""Logging configuration and utilities."""

import sys
from pathlib import Path
from loguru import logger
from src.config.settings import settings


def setup_logger():
    """Configure the logger with proper format and handlers."""
    
    # Remove default logger
    logger.remove()
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format=settings.log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # File handler if configured
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.log_file,
            format=settings.log_format,
            level=settings.log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )
    
    return logger


# Initialize logger
logger = setup_logger()


class LoggerMixin:
    """Mixin class to provide logging capabilities to other classes."""
    
    @property
    def logger(self):
        """Get a logger instance with the class name."""
        return logger.bind(classname=self.__class__.__name__)


def log_execution_time(func):
    """Decorator to log function execution time."""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.debug(
            f"{func.__name__} executed in {execution_time:.2f} seconds"
        )
        return result
    
    return wrapper


def log_errors(func):
    """Decorator to log exceptions."""
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                exc_info=True
            )
            raise
    
    return wrapper