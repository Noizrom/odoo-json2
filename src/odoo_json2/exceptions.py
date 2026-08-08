"""
Custom exception hierarchy for odoo-json2 library.
"""

from typing import Any, Dict, Optional


class OdooJSON2Error(Exception):
    """Base exception for all Odoo JSON-2 API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, raw_error: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_error = raw_error or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class OdooAuthError(OdooJSON2Error):
    """Raised when authentication fails (HTTP 401 / Invalid API key)."""
    pass


class OdooNotFoundError(OdooJSON2Error):
    """Raised when a model, method, or endpoint is not found (HTTP 404)."""
    pass


class OdooValidationError(OdooJSON2Error):
    """Raised on invalid request body or ORM domain/data validation errors (HTTP 400/422)."""
    pass


class OdooServerException(OdooJSON2Error):
    """Raised when Odoo backend raises a Python exception (HTTP 500). Includes debug traceback if available."""

    @property
    def traceback(self) -> Optional[str]:
        return self.raw_error.get("debug")
