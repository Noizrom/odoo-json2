"""
Unit tests for CLI commands.
"""

import pytest
import requests_mock

from odoo_json2.cli import main


def test_cli_test_connection(requests_mock, monkeypatch):
    monkeypatch.setattr("sys.argv", ["odoo-json2", "--host", "demo.odoo.com", "--protocol", "https", "--key", "test_key", "test-connection"])
    
    requests_mock.get("https://demo.odoo.com/web/version", json={"server_version": "19.0"})
    requests_mock.post("https://demo.odoo.com/json/2/res.users/search_read", json=[{"name": "Admin", "login": "admin"}])
    
    # Should run without error/exit
    main()


def test_cli_search(requests_mock, monkeypatch):
    monkeypatch.setattr("sys.argv", ["odoo-json2", "--host", "demo.odoo.com", "--protocol", "https", "--key", "test_key", "search", "res.partner", "--json"])
    
    requests_mock.post("https://demo.odoo.com/json/2/res.partner/search_read", json=[{"id": 1, "name": "Acme"}])
    
    main()
