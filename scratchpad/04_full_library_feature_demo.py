"""Demonstrate the odoo-json2 library's main capabilities."""

import os

from dotenv import load_dotenv

from odoo_json2 import (
    JSON2Client,
    OdooAuthError,
    OdooJSON2Error,
    OdooNotFoundError,
    OdooServerException,
    OdooValidationError,
)

load_dotenv(override=True)

HOST = os.getenv("ODOO_HOST", "noizr-test.odoo.com")
API_KEY = os.getenv("ODOO_API_KEY", "")
DATABASE = os.getenv("ODOO_DATABASE", "noizr-test")
PROTOCOL = os.getenv("ODOO_PROTOCOL", "https")


def explore_with_odoo_json2_library() -> None:
    """Run the full library feature demonstration."""
    print("==================================================")
    print("   odoo-json2 Library Demonstration & Explorer    ")
    print("==================================================")
    print(f"Target: {PROTOCOL}://{HOST} (Database: {DATABASE})")

    # 1. Client Instantiation & Constructor options
    print("\n--- 1. Initializing JSON2Client ---")
    client = JSON2Client(
        host=HOST,
        api_key=API_KEY,
        database=DATABASE,
        protocol=PROTOCOL,
        timeout=30,
        verify_ssl=True,
    )
    print(f"Client Instance: {client}")
    print(f"Base Endpoint: {client.base_url}")

    # 2. Server Version Lookup
    print("\n--- 2. Public Version Endpoint (/web/version) ---")
    ver_info = client.version()
    print(f"Server Info: {ver_info}")

    # 3. Model Proxy Access (client.env['model_name'])
    print("\n--- 3. Environment & Model Proxy Access ---")
    partner = client.env["res.partner"]
    user = client.env["res.users"]
    product = client.env["product.product"]
    print(f"Partner Proxy: {partner}")
    print(f"User Proxy:    {user}")
    print(f"Product Proxy: {product}")

    # 4. ORM Method Calls via ModelProxy
    print("\n--- 4. ORM Operations (search_read, search_count, fields_get) ---")
    try:
        # 4a. Count Records
        partner_count = partner.search_count([("is_company", "=", True)])
        print(f"[✓] Total Company Partners: {partner_count}")

        # 4b. Search & Read
        partners = partner.search_read(
            domain=[("is_company", "=", True)],
            fields=["id", "name", "email"],
            limit=3,
        )
        print(f"[✓] Fetched {len(partners)} partner(s):")
        for partner_record in partners:
            print(
                f"    - [{partner_record['id']}] {partner_record['name']} "
                f"({partner_record.get('email', 'No email')})"
            )

        # 4c. Fields Metadata (fields_get)
        fields_meta = partner.fields_get(
            attributes=["string", "type", "required"]
        )
        print(f"[✓] Retrieved metadata for {len(fields_meta)} fields on res.partner")

        # 4d. Create / Update / Delete Workflow
        print("\n--- 5. Record Creation, Write, and Unlink ---")
        new_ids = partner.create(
            [{"name": "odoo-json2 Scratchpad Test Company", "is_company": True}]
        )
        new_id = new_ids[0]
        print(f"[✓] Created Partner ID: {new_id}")

        partner.write([new_id], {"email": "scratchpad@example.com"})
        print(f"[✓] Updated Partner ID: {new_id}")

        partner.unlink([new_id])
        print(f"[✓] Unlinked Partner ID: {new_id}")

    except OdooAuthError as error:
        print(f"[✗] OdooAuthError (HTTP {error.status_code}): {error}")
        print(
            "    Diagnosis: Invalid or expired API Key, or instance is restricted "
            "to Custom Plan."
        )
    except OdooValidationError as error:
        print(f"[✗] OdooValidationError (HTTP {error.status_code}): {error}")
    except OdooNotFoundError as error:
        print(f"[✗] OdooNotFoundError (HTTP {error.status_code}): {error}")
    except OdooServerException as error:
        print(f"[✗] OdooServerException (HTTP {error.status_code}): {error}")
    except OdooJSON2Error as error:
        print(f"[✗] OdooJSON2Error: {error}")

    # 6. Direct QWeb View Customization (ir.ui.view)
    print("\n--- 6. QWeb View Customization via ir.ui.view ---")
    try:
        view = client.env["ir.ui.view"]
        custom_views = view.search_read(
            [("key", "=", "web.login_layout")],
            fields=["id", "name"],
        )
        print(f"[✓] Found parent login layout view: {custom_views}")
    except OdooJSON2Error as error:
        print(f"[✗] View lookup exception: {error}")


if __name__ == "__main__":
    explore_with_odoo_json2_library()
