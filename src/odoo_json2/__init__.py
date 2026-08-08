"""
odoo-json2: Modern Python Client & CLI for Odoo 19+ External JSON-2 API (/json/2).
"""

from .client import JSON2Client, OdooJSON2
from .env import Environment, ModelProxy
from .exceptions import (
    OdooAuthError,
    OdooJSON2Error,
    OdooNotFoundError,
    OdooServerException,
    OdooValidationError,
)
from .theme import apply_login_theme

__version__ = "0.2.0"
__all__ = [
    "JSON2Client",
    "OdooJSON2",
    "Environment",
    "ModelProxy",
    "OdooJSON2Error",
    "OdooAuthError",
    "OdooNotFoundError",
    "OdooValidationError",
    "OdooServerException",
    "apply_login_theme",
    "__version__",
]
