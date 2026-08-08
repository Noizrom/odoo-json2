"""
Unit tests for Environment dict accessor and ModelProxy ORM operations.
"""

import pytest
import requests_mock

from odoo_json2 import JSON2Client


def test_model_proxy_search(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="key123")
    Partner = client.env["res.partner"]
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/search",
        json=[1, 2, 3],
        status_code=200
    )
    
    ids = Partner.search([("is_company", "=", True)], limit=3)
    assert ids == [1, 2, 3]
    assert requests_mock.last_request.json() == {
        "domain": [["is_company", "=", True]],
        "offset": 0,
        "limit": 3
    }


def test_model_proxy_read(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="key123")
    Partner = client.env["res.partner"]
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/read",
        json=[{"id": 1, "name": "Acme"}],
        status_code=200
    )
    
    records = Partner.read([1], fields=["name"])
    assert records == [{"id": 1, "name": "Acme"}]
    assert requests_mock.last_request.json() == {
        "ids": [1],
        "fields": ["name"]
    }


def test_model_proxy_create_dict_or_list(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="key123")
    Partner = client.env["res.partner"]
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/create",
        json=[42],
        status_code=200
    )
    
    # Test passing single dict
    created_id = Partner.create({"name": "New Corp"})
    assert created_id == [42]
    assert requests_mock.last_request.json() == {
        "vals_list": [{"name": "New Corp"}]
    }


def test_model_proxy_write_and_unlink(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="key123")
    Partner = client.env["res.partner"]
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/write",
        json=True,
        status_code=200
    )
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/unlink",
        json=True,
        status_code=200
    )
    
    assert Partner.write([42], {"phone": "12345"}) is True
    assert Partner.unlink([42]) is True


def test_model_proxy_dynamic_method(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="key123")
    Partner = client.env["res.partner"]
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/custom_action_method",
        json={"result": "ok"},
        status_code=200
    )
    
    res = Partner.custom_action_method(ids=[10], extra_param="hello")
    assert res == {"result": "ok"}
    assert requests_mock.last_request.json() == {
        "ids": [10],
        "extra_param": "hello"
    }


def test_model_proxy_fields_get(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="key123")
    Partner = client.env["res.partner"]
    
    requests_mock.post(
        "https://demo.odoo.com/json/2/res.partner/fields_get",
        json={"name": {"type": "char", "string": "Name"}},
        status_code=200
    )
    
    fg = Partner.fields_get(allfields=["name"])
    assert "name" in fg
    assert fg["name"]["type"] == "char"
