"""Customize Odoo's login screen through the JSON-2 API.

The example creates or updates an inherited QWeb view for ``web.login_layout``
with a modern dark theme.
"""

import logging
import os

from dotenv import load_dotenv

from odoo_json2 import JSON2Client, OdooJSON2Error

load_dotenv(override=True)

HOST = os.getenv("ODOO_HOST") or "mycompany.odoo.com"
API_KEY = os.getenv("ODOO_API_KEY") or "your_bearer_api_key"
DATABASE = os.getenv("ODOO_DATABASE") or "mycompany"
PROTOCOL = os.getenv("ODOO_PROTOCOL") or "https"

DARK_THEME_CSS = """<style><![CDATA[
    /* 1. Root & Page Dark Background */
    html, body, body.o_home_menu_background {
        background-color: #0b0f19 !important;
        background-image: linear-gradient(
            135deg, #0b0f19 0%, #111827 50%, #1e1b4b 100%
        ) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont,
            "Segoe UI", Roboto, sans-serif !important;
        color: #f8fafc !important;
        min-height: 100vh !important;
        margin: 0 !important;
    }

    #wrapwrap {
        display: flex !important;
        flex-direction: column !important;
        min-height: 100vh !important;
        background: transparent !important;
    }

    main {
        flex: 1 0 auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 2rem 1rem !important;
        width: 100% !important;
    }

    /* 2. Main Centered Dark Card Container */
    .container.py-5 {
        padding: 0 !important;
        margin: auto !important;
        width: 100% !important;
        max-width: 420px !important;
    }

    div.o_database_list, div.o_database_list.card, .card, .bg-white, .bg-100 {
        background-color: #1e293b !important;
        background: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6) !important;
        max-width: 420px !important;
        width: 100% !important;
        margin: 0 auto !important;
        color: #f8fafc !important;
    }

    .card {
        padding: 32px !important;
    }

    .card-body {
        padding: 0 !important;
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #f8fafc !important;
    }

    /* 3. Logo & Dividers */
    .card-body .text-center.pb-3.border-bottom {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin-bottom: 1.5rem !important;
        padding-bottom: 1.25rem !important;
    }

    .card-body img {
        max-height: 56px !important;
        width: auto !important;
        filter: drop-shadow(0 4px 10px rgba(0,0,0,0.5)) !important;
    }

    /* 4. Labels & Text (Crisp Light Text on Dark Card) */
    .form-label, label, .col-form-label, .card-body p, .text-muted, .small {
        color: #cbd5e1 !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.375rem !important;
    }

    /* 5. Inputs & Form Controls */
    .form-control {
        background-color: #0f172a !important;
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        color: #f8fafc !important;
        border-radius: 10px !important;
        padding: 11px 14px !important;
        font-size: 0.9375rem !important;
        transition: all 0.15s ease-in-out !important;
    }

    .form-control::placeholder {
        color: #64748b !important;
    }

    .form-control:focus {
        background-color: #0f172a !important;
        background: #0f172a !important;
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
        color: #ffffff !important;
    }

    /* Eye Icon Button */
    .input-group .btn.o_show_password {
        background-color: #0f172a !important;
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        border-left: none !important;
        color: #94a3b8 !important;
        border-top-right-radius: 10px !important;
        border-bottom-right-radius: 10px !important;
    }

    /* Links */
    .btn-link, a, .card-body a {
        color: #818cf8 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }

    .btn-link:hover, a:hover {
        color: #a5b4fc !important;
        text-decoration: underline !important;
    }

    /* 6. Primary Action Button */
    .btn-primary {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        background-color: #4f46e5 !important;
        border: none !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        padding: 12px 20px !important;
        font-weight: 600 !important;
        font-size: 0.9375rem !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
        transition: all 0.15s ease-in-out !important;
    }

    .btn-primary:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6) !important;
        transform: translateY(-1px) !important;
        color: #ffffff !important;
    }

    /* 7. Passkey Link */
    .list-group-item {
        background-color: #0f172a !important;
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        color: #e2e8f0 !important;
        border-radius: 10px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }

    .list-group-item:hover {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }

    /* 8. Footer Section */
    .text-center.small.mt-4.pt-3.border-top {
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #64748b !important;
        font-size: 0.8125rem !important;
    }

    .text-center.small.mt-4.pt-3.border-top a {
        color: #818cf8 !important;
        text-decoration: none !important;
    }

    /* 9. Status Bar / Neutralization Banner */
    #oe_neutralize_banner {
        position: relative !important;
        width: 100% !important;
        display: block !important;
        margin-top: auto !important;
    }
]]></style>"""


def customize_login_screen(client: JSON2Client) -> dict[str, object]:
    """Inject modern dark styling into Odoo's ``web.login_layout`` view."""
    view = client.env["ir.ui.view"]
    parent_views = view.search_read(
        [("key", "=", "web.login_layout")],
        fields=["id", "name"],
    )
    if not parent_views:
        raise RuntimeError("Parent view 'web.login_layout' not found in Odoo database.")

    parent_id = parent_views[0]["id"]
    view_name = "Modern Simple Dark Login Theme (odoo-json2)"
    view_arch = f"""
    <xpath
        expr="//div[
            contains(@t-attf-class, 'o_database_list') or
            contains(@class, 'o_database_list') or
            contains(@class, 'container')
        ]"
        position="before"
    >
        {DARK_THEME_CSS}
    </xpath>
    """

    existing = view.search_read(
        [("name", "like", "Modern Simple")],
        fields=["id"],
    )
    if existing:
        view_id = existing[0]["id"]
        view.write(
            [view_id],
            {"arch": view_arch, "active": True, "name": view_name},
        )
        return {"status": "updated", "view_id": view_id, "name": view_name}

    view_ids = view.create(
        [
            {
                "name": view_name,
                "type": "qweb",
                "mode": "extension",
                "inherit_id": parent_id,
                "arch": view_arch,
                "priority": 99,
            }
        ]
    )
    return {"status": "created", "view_id": view_ids[0], "name": view_name}


def main() -> None:
    """Create or update the login theme."""
    logging.basicConfig(level=logging.INFO)
    client = JSON2Client(
        host=HOST,
        api_key=API_KEY,
        database=DATABASE,
        protocol=PROTOCOL,
    )
    try:
        result = customize_login_screen(client)
        print(
            f"Status: {result['status']} | View ID: {result['view_id']} | "
            f"Name: {result['name']}"
        )
        print(
            f"Open https://{HOST}/web/login to view your custom dark login screen!"
        )
    except (OdooJSON2Error, RuntimeError) as error:
        print(f"Error customizing login screen: {error}")


if __name__ == "__main__":
    main()
