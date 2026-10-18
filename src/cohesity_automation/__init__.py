"""Unofficial example automation toolkit for a data-protection REST API."""

from .client import ApiClient
from .config import Settings
from .errors import ApiError, AuthError, ConfigError, RateLimitError, TransportError

__all__ = [
    "ApiClient",
    "ApiError",
    "AuthError",
    "ConfigError",
    "RateLimitError",
    "Settings",
    "TransportError",
]
__version__ = "0.1.0"
