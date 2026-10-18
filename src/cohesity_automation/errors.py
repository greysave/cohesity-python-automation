"""Exception hierarchy."""

from __future__ import annotations


class AutomationError(Exception):
    """Base class for all errors raised by this package."""


class ConfigError(AutomationError):
    """Missing or invalid configuration."""


class TransportError(AutomationError):
    """Network-level failure (connection, timeout, TLS)."""


class ApiError(AutomationError):
    """The server returned a non-success HTTP status."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message


class AuthError(ApiError):
    """401/403 responses."""


class RateLimitError(ApiError):
    """429 response; ``retry_after`` is seconds, if the server provided it."""

    def __init__(self, status: int, message: str, retry_after: float | None = None) -> None:
        super().__init__(status, message)
        self.retry_after = retry_after
