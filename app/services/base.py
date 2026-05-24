"""Base service class with common functionality."""
from abc import ABC
from typing import Optional, Generic, TypeVar, Dict, Any
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseService(ABC):
    """Base service class providing common functionality."""

    def __init__(self):
        """Initialize base service."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def log_info(self, message: str, **kwargs) -> None:
        """Log info level message."""
        self.logger.info(message, extra=kwargs)

    def log_error(self, message: str, **kwargs) -> None:
        """Log error level message."""
        self.logger.error(message, extra=kwargs)

    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug level message."""
        self.logger.debug(message, extra=kwargs)
