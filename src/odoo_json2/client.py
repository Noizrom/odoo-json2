"""
Core JSON2Client implementation for Odoo 19+ External JSON-2 API (/json/2).
"""

import logging
import os
import time
import requests
from typing import Any, Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv

from rich.console import Console
from rich.logging import RichHandler

from .exceptions import (
    OdooAuthError,
    OdooJSON2Error,
    OdooNotFoundError,
    OdooServerException,
    OdooValidationError,
)
from .env import Environment
from . import __version__

logger = logging.getLogger("odoo_json2")
console = Console()


class JSON2Client:
    """
    Modern HTTP Client for Odoo 19+ External JSON-2 API (`/json/2`).
    
    Provides an `odoorpc`-compatible `env['model_name']` dynamic interface.
    API Key authentication via `Authorization: bearer <API_KEY>`.
    Each API call executes in a single SQL transaction.
    """

    def __init__(
        self,
        host: str,
        api_key: str,
        database: Optional[str] = None,
        protocol: str = "https",
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        self.raw_host = host
        clean_host = host.rstrip("/").replace("http://", "").replace("https://", "")
        
        # Normalize protocol (converting legacy jsonrpc/jsonrpc+ssl to http/https)
        if host.startswith("http://"):
            self.protocol = "http"
        elif host.startswith("https://"):
            self.protocol = "https"
        else:
            proto = (protocol or "https").lower().replace("jsonrpc+ssl", "https").replace("jsonrpc", "https").replace("+ssl", "")
            self.protocol = proto if proto in ("http", "https") else "https"
        self.host = clean_host
        self.api_key = api_key
        self.database = database or os.getenv("ODOO_DATABASE")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.base_url = f"{self.protocol}://{self.host}/json/2"
        
        self.session = requests.Session()
        self.session.verify = self.verify_ssl
        self.session.headers.update({
            "Authorization": f"bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": f"odoo-json2/{__version__} Python-Requests"
        })
        if self.database:
            self.session.headers["X-Odoo-Database"] = self.database

        # Initialize dynamic environment accessor (env['res.partner'])
        self.env = Environment(self)

    @classmethod
    def from_env(cls, **kwargs) -> "JSON2Client":
        """Instantiate client from environment variables (ODOO_HOST, ODOO_API_KEY, ODOO_DATABASE)."""
        load_dotenv(override=True)
        host = os.getenv("ODOO_HOST", "localhost")
        api_key = os.getenv("ODOO_API_KEY", "")
        database = os.getenv("ODOO_DATABASE")
        protocol = os.getenv("ODOO_PROTOCOL", "https").replace("+ssl", "")
        if not api_key:
            raise OdooAuthError("ODOO_API_KEY environment variable is required for JSON2Client.")
        return cls(host=host, api_key=api_key, database=database, protocol=protocol, **kwargs)

    def version(self) -> Dict[str, Any]:
        """Fetch Odoo server version from /web/version endpoint."""
        url = f"{self.protocol}://{self.host}/web/version"
        try:
            res = self.session.get(url, timeout=self.timeout)
            if res.ok:
                return res.json()
        except Exception as e:
            logger.debug("Failed to fetch version from /web/version: %s", e)
        return {"version": "19.0", "server_version": "19.0"}

    def call(
        self,
        model: str,
        method: str,
        ids: Optional[List[int]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        Execute an ORM method via POST /json/2/<model>/<method>.
        
        :param model: Technical model name (e.g. 'res.partner', 'ir.ui.view')
        :param method: ORM method name (e.g. 'search_read', 'create', 'write')
        :param ids: Optional list of record IDs for recordset methods
        :param context: Optional context dict (e.g. {'lang': 'en_US'})
        :param kwargs: Named parameters passed to the ORM method
        """
        url = f"{self.base_url}/{model}/{method}"
        payload: Dict[str, Any] = {}
        if ids is not None:
            payload["ids"] = ids
        if context is not None:
            payload["context"] = context
        payload.update(kwargs)

        start_time = time.perf_counter()
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.error("Connection error to %s: %s", url, exc)
            raise OdooJSON2Error(f"Network error connecting to Odoo host '{self.host}': {exc}") from exc
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if response.status_code == 200:
            logger.debug("JSON-2 %s.%s OK (%.2fms)", model, method, elapsed_ms)
            return response.json()

        # Handle non-200 Error Responses
        err_data: Dict[str, Any] = {}
        try:
            err_data = response.json()
            msg = err_data.get("message") or err_data.get("name") or response.text
        except Exception:
            msg = response.text or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise OdooAuthError(f"Unauthorized: {msg}", status_code=401, raw_error=err_data)
        elif response.status_code == 404:
            raise OdooNotFoundError(f"Endpoint or model not found: {msg}", status_code=404, raw_error=err_data)
        elif response.status_code in (400, 422):
            raise OdooValidationError(f"Validation / Request error: {msg}", status_code=response.status_code, raw_error=err_data)
        else:
            raise OdooServerException(f"Odoo Server Error [{response.status_code}]: {msg}", status_code=response.status_code, raw_error=err_data)

    def search_read(
        self,
        model: str,
        domain: List[Any],
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.env[model].search_read(domain=domain, fields=fields, limit=limit, order=order)

    def create(self, model: str, vals_list: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[int]:
        return self.env[model].create(vals_list)

    def write(self, model: str, ids: List[int], vals: Dict[str, Any]) -> bool:
        return self.env[model].write(ids, vals)

    def unlink(self, model: str, ids: List[int]) -> bool:
        return self.env[model].unlink(ids)

    def __repr__(self) -> str:
        db_info = f", db='{self.database}'" if self.database else ""
        return f"<JSON2Client host='{self.host}'{db_info} protocol='{self.protocol}'>"


# Alias for backward compatibility / explicit naming
OdooJSON2 = JSON2Client
