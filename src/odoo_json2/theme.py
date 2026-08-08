"""
Theme manager for applying modern QWeb login themes over JSON-2 API.
"""

import logging
from typing import Any, Dict, Optional

from .client import JSON2Client

logger = logging.getLogger("odoo_json2.theme")

GLASSMORPHISM_CSS = """
<style>
    body {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        min-height: 100vh !important;
    }
    div.o_database_list, .card.single-card {
        background: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 24px !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4) !important;
        padding: 32px !important;
    }
    .card-body, label, .text-muted {
        color: #f8fafc !important;
    }
    .form-control {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
    }
    .form-control:focus {
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: #818cf8 !important;
        box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.25) !important;
        color: #ffffff !important;
    }
    .btn-primary {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s ease !important;
    }
    .btn-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4) !important;
    }
</style>
"""


def apply_login_theme(
    client: JSON2Client,
    theme_name: str = "glassmorphism",
    custom_css: Optional[str] = None
) -> Dict[str, Any]:
    """
    Injects or updates a modern QWeb view extension targeting web.login_layout.
    """
    View = client.env["ir.ui.view"]
    
    # 1. Search for web.login_layout parent view
    parent_views = View.search_read([("key", "=", "web.login_layout")], fields=["id", "name"])
    if not parent_views:
        raise RuntimeError("Parent view 'web.login_layout' not found in database.")
    
    parent_id = parent_views[0]["id"]
    css_content = custom_css or GLASSMORPHISM_CSS
    
    view_arch = f"""
    <xpath expr="//div[contains(@class, 'o_database_list')]" position="before">
        {css_content}
    </xpath>
    """
    
    view_name = f"Modern Login Theme [{theme_name}] (odoo-json2)"
    existing = View.search_read([("name", "=", view_name)], fields=["id"])
    
    if existing:
        view_id = existing[0]["id"]
        View.write([view_id], {"arch": view_arch, "active": True})
        logger.info("Updated existing login theme view ID: %d", view_id)
        return {"status": "updated", "view_id": view_id, "name": view_name}
    else:
        created_ids = View.create([{
            "name": view_name,
            "type": "qweb",
            "mode": "extension",
            "inherit_id": parent_id,
            "arch": view_arch,
            "priority": 99
        }])
        view_id = created_ids[0]
        logger.info("Created new login theme view ID: %d", view_id)
        return {"status": "created", "view_id": view_id, "name": view_name}
