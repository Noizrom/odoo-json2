"""
Common utilities for OdooRPC connections with proxy support.

This module provides a reusable OdooClient class that handles:
- SOCKS5 proxy configuration
- Connection initialization
- Environment variable configuration
- Rich console logging
"""

import logging
import os
import socket
from typing import Any, Optional

try:
    import odoorpc
except ImportError:
    odoorpc = None
try:
    import socks
except ImportError:
    socks = None
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from .json2_client import JSON2OdooClient

# Load environment variables
load_dotenv()

# Setup Rich console
console = Console()


def setup_logging(name: str = "odoo-client", level: str = None) -> logging.Logger:
    """
    Setup Rich logging for the application.
    
    Args:
        name: Logger name
        level: Log level (defaults to LOG_LEVEL env var or INFO)
    
    Returns:
        Configured logger instance
    """
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console)],
    )
    return logging.getLogger(name)


def setup_proxy(
    proxy_host: str = None,
    proxy_port: int = None,
    proxy_type: Any = None
) -> bool:
    """
    Configure SOCKS proxy for all socket connections.
    
    Args:
        proxy_host: Proxy hostname (defaults to PROXY_HOST env var or 'localhost')
        proxy_port: Proxy port (defaults to PROXY_PORT env var or 1080)
        proxy_type: Proxy type (SOCKS4, SOCKS5, HTTP)
    
    Returns:
        True if proxy was configured successfully, False otherwise
    """
    try:
        host = proxy_host or os.getenv("PROXY_HOST", "localhost")
        port = proxy_port or int(os.getenv("PROXY_PORT", "1080"))
        
        socks.set_default_proxy(proxy_type, host, port, rdns=True)
        socket.socket = socks.socksocket
        
        # Monkeypatch getaddrinfo to return the hostname directly
        # This helps with DNS resolution through the proxy
        def getaddrinfo_mock(host, port, family=0, type=0, proto=0, flags=0):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (host, port))]
        
        socket.getaddrinfo = getaddrinfo_mock
        
        console.print(f"[yellow]✓ Using SOCKS5 proxy at {host}:{port}[/yellow]")
        return True
        
    except ImportError:
        console.print("[red]✗ PySocks not installed! Install with: pip install PySocks[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Failed to setup proxy: {e}[/red]")
        return False


class OdooClient:
    """
    Reusable Odoo client with proxy support and environment-based configuration.
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        protocol: str = None,
        use_proxy: bool = None,
        logger: logging.Logger = None
    ):
        """
        Initialize Odoo client.
        
        Args:
            host: Odoo server hostname (defaults to ODOO_HOST env var)
            port: Odoo server port (defaults to ODOO_PORT env var or 8069)
            protocol: Connection protocol (defaults to ODOO_PROTOCOL env var or 'jsonrpc')
                - "jsonrpc" for HTTP
                - "jsonrpc+ssl" for HTTPS
            use_proxy: Enable proxy (defaults to USE_PROXY env var or False)
            logger: Logger instance (creates one if not provided)
        """
        self.host = host or os.getenv("ODOO_HOST", "localhost")
        self.port = port or int(os.getenv("ODOO_PORT", "8069"))
        self.protocol = protocol or os.getenv("ODOO_PROTOCOL", "jsonrpc")
        self.use_proxy = use_proxy if use_proxy is not None else os.getenv("USE_PROXY", "false").lower() == "true"
        self.log = logger or setup_logging()
        
        # Setup proxy if enabled
        if self.use_proxy:
            if not setup_proxy():
                self.log.warning("Proxy setup failed, continuing without proxy")
        
        # Initialize OdooRPC connection
        self.odoo = odoorpc.ODOO(self.host, port=self.port, protocol=self.protocol)
        self.db = None
        self.username = None
    
    def login(
        self,
        database: str = None,
        username: str = None,
        password: str = None
    ) -> None:
        """
        Authenticate with the Odoo server.
        
        Args:
            database: Database name (defaults to ODOO_DATABASE env var)
            username: Username (defaults to ODOO_USER env var)
            password: Password (defaults to ODOO_PASSWORD env var)
        """
        self.db = database or os.getenv("ODOO_DATABASE", "odoo")
        self.username = username or os.getenv("ODOO_USER", "admin")
        pwd = password or os.getenv("ODOO_PASSWORD", "admin")
        
        self.odoo.login(self.db, self.username, pwd)
        self.log.info(f"✓ Connected to {self.host} as {self.username}")
    
    def get_env(self, model: str):
        """
        Get Odoo environment for a specific model.
        
        Args:
            model: Model name (e.g., 'hr.employee', 'res.users')
        
        Returns:
            Odoo model environment
        """
        return self.odoo.env[model]
    
    @classmethod
    def from_env(cls, use_proxy: bool = None, logger: logging.Logger = None) -> 'OdooClient':
        """
        Create an OdooClient instance using only environment variables.
        
        Args:
            use_proxy: Override USE_PROXY env var
            logger: Logger instance
        
        Returns:
            Configured OdooClient instance
        """
        return cls(use_proxy=use_proxy, logger=logger)
