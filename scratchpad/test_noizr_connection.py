"""Explore an Odoo 19 connection, credentials, models, and user context."""

import os

from dotenv import load_dotenv

from odoo_json2 import JSON2Client, OdooJSON2Error

load_dotenv(override=True)

HOST = os.getenv("ODOO_HOST", "noizr-test.odoo.com")
API_KEY = os.getenv("ODOO_API_KEY", "")
DATABASE = os.getenv("ODOO_DATABASE", "noizr-test")
PROTOCOL = os.getenv("ODOO_PROTOCOL", "https")


def main() -> None:
    """Run the Odoo connection exploration scratchpad."""
    print(f"Connecting to Odoo instance at: {PROTOCOL}://{HOST} (db: {DATABASE})...")
    client = JSON2Client(
        host=HOST,
        api_key=API_KEY,
        database=DATABASE,
        protocol=PROTOCOL,
    )

    try:
        # 1. Fetch server version info
        version_info = client.version()
        print(f"\n[✓] Server Version: {version_info}")

        # 2. Test current user context retrieval via res.users
        print("\n--- Current User Info ---")
        user = client.env["res.users"]
        # In Odoo JSON-2 API, context_get or search_read for active user.
        users = user.search_read(
            [],
            fields=["id", "name", "login", "email"],
            limit=5,
        )
        print(f"Found {len(users)} user(s):")
        for user_record in users:
            print(
                f"  - ID: {user_record['id']} | Name: {user_record['name']} | "
                f"Login: {user_record['login']} | "
                f"Email: {user_record.get('email', '-')}"
            )

        # 3. Test Partner model access
        print("\n--- Partner Records ---")
        partner = client.env["res.partner"]
        partners = partner.search_read(
            [("is_company", "=", True)],
            fields=["id", "name", "email"],
            limit=5,
        )
        print(f"Found {len(partners)} company partner(s):")
        for partner_record in partners:
            print(
                f"  - ID: {partner_record['id']} | "
                f"Name: {partner_record['name']} | "
                f"Email: {partner_record.get('email', '-')}"
            )

        # 4. Check installed modules / models access
        print("\n--- Checking Installed Studio / Core Models ---")
        ir_model = client.env["ir.model"]
        studio_models = ir_model.search_read(
            [("model", "like", "x_")],
            fields=["model", "name"],
            limit=5,
        )
        print(f"Custom/Studio Models Count (x_*): {len(studio_models)}")
        for model in studio_models:
            print(f"  - {model['model']}: {model['name']}")

        print("\n[✓] Connection test completed successfully!")

    except OdooJSON2Error as error:
        print(f"\n[✗] Odoo JSON-2 Error: {error}")
        if getattr(error, "status_code", None) == 401:
            print("\n[!] 401 Unauthorized Diagnosis:")
            print(
                "  1. External API (/json/2) requires a valid API key from "
                "User Preferences -> Security -> API Keys."
            )
            print(
                "  2. In Odoo Online (SaaS), External API is restricted to Custom "
                "plans (not available on One App Free / Standard plans)."
            )
            print("  3. Check that ODOO_API_KEY in .env contains a valid active key.")
        elif hasattr(error, "raw_error") and error.raw_error:
            print(f"Details: {error.raw_error}")
    except Exception as error:
        print(f"\n[✗] Unexpected Error: {type(error).__name__}: {error}")

if __name__ == "__main__":
    main()
