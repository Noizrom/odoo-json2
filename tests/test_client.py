"""
Unit tests for JSON2Client core methods and exception handling.
"""

import pytest
import requests_mock

from odoo_json2 import (
    JSON2Client,
    OdooAuthError,
    OdooJSON2Error,
    OdooNotFoundError,
    OdooServerException,
    OdooValidationError,
)


def test_client_init_headers():
    client = JSON2Client(host="mycompany.odoo.com", api_key="test_api_key", database="mycompany", protocol="https")
    assert client.host == "mycompany.odoo.com"
    assert client.base_url == "https://mycompany.odoo.com/json/2"
    assert client.session.headers["Authorization"] == "bearer test_api_key"
    assert client.session.headers["X-Odoo-Database"] == "mycompany"


def test_client_call_success(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="secret_key", database="demo")
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/search_read",
        json=[{"id": 1, "name": "Test Partner"}],
        status_code=200
    )
    
    res = client.call("res.partner", "search_read", domain=[], fields=["name"])
    assert res == [{"id": 1, "name": "Test Partner"}]
    
    last_req = requests_mock.last_request
    assert last_req.headers["Authorization"] == "bearer secret_key"
    assert last_req.json() == {"domain": [], "fields": ["name"]}


def test_client_auth_error(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="invalid_key")
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/search_read",
        json={"name": "werkzeug.exceptions.Unauthorized", "message": "Invalid apikey"},
        status_code=401
    )
    
    with pytest.raises(OdooAuthError) as exc_info:
        client.call("res.partner", "search_read")
    
    assert exc_info.value.status_code == 401
    assert "Invalid apikey" in str(exc_info.value)


def test_client_not_found_error(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="test_key")
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/invalid.model/search_read",
        json={"message": "Model not found"},
        status_code=404
    )
    
    with pytest.raises(OdooNotFoundError):
        client.call("invalid.model", "search_read")


def test_client_validation_error(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="test_key")
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/create",
        json={"message": "Missing required field 'name'"},
        status_code=422
    )
    
    with pytest.raises(OdooValidationError):
        client.create("res.partner", {})


def test_client_server_error(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="test_key")
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/search_read",
        json={"message": "Internal Server Error", "debug": "Traceback (most recent call last)..."},
        status_code=500
    )
    
    with pytest.raises(OdooServerException) as exc_info:
        client.call("res.partner", "search_read")
    
    assert exc_info.value.traceback == "Traceback (most recent call last)..."


def test_version_fetch(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="test_key")
    requests_mock.get("https://demo.odoo.com/web/version", json={"server_version": "19.0"})
    
    v = client.version()
    assert v["server_version"] == "19.0"
