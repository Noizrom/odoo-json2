"""
Unit tests for QWeb Theme Manager.
"""

import pytest
import requests_mock

from odoo_json2 import JSON2Client, apply_login_theme


def test_apply_login_theme_create(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="key123")
    
    # Mock search_read for web.login_layout
    requests_mock.post(
        "https://demo.odoo.com/json/2/ir.ui.view/search_read",
        [
            {"json": [{"id": 100, "name": "web.login_layout"}]},  # parent search
            {"json": []}  # existing theme search
        ]
    )
    
    # Mock create for ir.ui.view
    requests_mock.post(
        "https://demo.odoo.com/json/2/ir.ui.view/create",
        json=[200],
        status_code=200
    )
    
    res = apply_login_theme(client, theme_name="glassmorphism")
    assert res["status"] == "created"
    assert res["view_id"] == 200


def test_apply_login_theme_update(requests_mock):
    client = JSON2Client(host="demo.odoo.com", api_key="key123")
    
    # Mock search_read for web.login_layout and existing theme
    requests_mock.post(
        "https://demo.odoo.com/json/2/ir.ui.view/search_read",
        [
            {"json": [{"id": 100, "name": "web.login_layout"}]},
            {"json": [{"id": 200, "name": "Modern Login Theme [glassmorphism] (odoo-json2)"}]}
        ]
    )
    
    # Mock write for ir.ui.view
    requests_mock.post(
        "https://demo.odoo.com/json/2/ir.ui.view/write",
        json=True,
        status_code=200
    )
    
    res = apply_login_theme(client, theme_name="glassmorphism")
    assert res["status"] == "updated"
    assert res["view_id"] == 200
