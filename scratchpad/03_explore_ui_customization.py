"""Explore Odoo UI-view and login-page customization through the JSON-2 API."""

import os

from dotenv import load_dotenv

from odoo_json2 import JSON2Client, OdooJSON2Error

load_dotenv(override=True)

HOST = os.getenv("ODOO_HOST", "noizr-test.odoo.com")
API_KEY = os.getenv("ODOO_API_KEY", "")
DATABASE = os.getenv("ODOO_DATABASE", "noizr-test")
PROTOCOL = os.getenv("ODOO_PROTOCOL", "https")

DARK_MODERN_CSS = """<style><![CDATA[
    body.o_home_menu_background, body {
        background-color: #090d16 !important;
        background-image: linear-gradient(
            135deg, #0f172a 0%, #090d16 50%, #1e1b4b 100%
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

    .container.py-5 {
        padding: 0 !important;
        margin: auto !important;
        width: 100% !important;
        max-width: 420px !important;
    }

    div.o_database_list, div.o_database_list.card, .card.bg-white, .card {
        background-color: #1e293b !important;
        background: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6) !important;
        padding: 32px !important;
        max-width: 420px !important;
        width: 100% !important;
        margin: 0 auto !important;
    }

    .card-body { padding: 0 !important; color: #f8fafc !important; }
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

    .form-label, label, .col-form-label, .card-body p, .text-muted {
        color: #cbd5e1 !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.375rem !important;
    }

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

    .form-control::placeholder { color: #64748b !important; }

    .form-control:focus {
        background-color: #0f172a !important;
        background: #0f172a !important;
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
        color: #ffffff !important;
    }

    .input-group .btn.o_show_password {
        background-color: #0f172a !important;
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        border-left: none !important;
        color: #94a3b8 !important;
        border-top-right-radius: 10px !important;
        border-bottom-right-radius: 10px !important;
    }

    .btn-link, a, .card-body a {
        color: #818cf8 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }

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

    .list-group-item {
        background-color: #0f172a !important;
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        color: #e2e8f0 !important;
        border-radius: 10px !important;
    }

    #oe_neutralize_banner {
        position: relative !important;
        width: 100% !important;
        display: block !important;
        margin-top: auto !important;
    }
]]></style>"""


def main() -> None:
    """Run the UI customization exploration scratchpad."""
    print(f"=== Odoo 19 UI & QWeb Customization Explorer ({HOST}) ===")
    client = JSON2Client(
        host=HOST,
        api_key=API_KEY,
        database=DATABASE,
        protocol=PROTOCOL,
    )

    try:
        view = client.env["ir.ui.view"]
        print("\n--- 1. Querying Parent Login View (web.login_layout) ---")
        parent_views = view.search_read(
            [("key", "=", "web.login_layout")],
            fields=["id", "name"],
        )
        if not parent_views:
            print("[x] Parent view 'web.login_layout' not found.")
            return
        parent_id = parent_views[0]["id"]
        print(f"[✓] Parent View ID: {parent_id} ({parent_views[0]['name']})")

        print("\n--- 2. Applying Dark Modern Login Theme via ir.ui.view ---")
        view_name = "Modern Simple Login Theme (odoo-json2)"
        arch = f"""<xpath
    expr="//div[
        contains(@t-attf-class, 'o_database_list') or
        contains(@class, 'o_database_list') or
        contains(@class, 'container')
    ]"
    position="before"
>
{DARK_MODERN_CSS}
</xpath>"""

        existing = view.search_read([("name", "=", view_name)], fields=["id"])
        if existing:
            view_id = existing[0]["id"]
            view.write([view_id], {"arch": arch, "active": True})
            print(f"[✓] Updated existing inherited view ID: {view_id}")
        else:
            new_ids = view.create(
                [
                    {
                        "name": view_name,
                        "type": "qweb",
                        "mode": "extension",
                        "inherit_id": parent_id,
                        "arch": arch,
                        "priority": 99,
                    }
                ]
            )
            print(f"[✓] Created new inherited view ID: {new_ids[0]}")

        print(
            "\n[✓] Login page updated successfully. "
            f"Visit https://{HOST}/web/login to view."
        )

    except OdooJSON2Error as error:
        print(f"\n[✗] Odoo JSON-2 Error: {error}")
    except Exception as error:
        print(f"\n[✗] Error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
