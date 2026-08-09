"""Explore Odoo 19 models and schemas through the JSON-2 API."""

import os

from dotenv import load_dotenv

from odoo_json2 import JSON2Client, OdooJSON2Error

load_dotenv(override=True)

HOST = os.getenv("ODOO_HOST", "noizr-test.odoo.com")
API_KEY = os.getenv("ODOO_API_KEY", "")
DATABASE = os.getenv("ODOO_DATABASE", "noizr-test")
PROTOCOL = os.getenv("ODOO_PROTOCOL", "https")


def main() -> None:
    """Run the schema exploration scratchpad."""
    print(f"=== Odoo 19 Schema Explorer ({HOST}) ===")
    client = JSON2Client(
        host=HOST,
        api_key=API_KEY,
        database=DATABASE,
        protocol=PROTOCOL,
    )

    try:
        # 1. Version Check
        ver = client.version()
        print(
            f"[✓] Odoo Server Version: "
            f"{ver.get('server_version', ver.get('version', '19.0'))}"
        )

        # 2. Query Installed Modules (ir.module.module)
        print("\n--- 1. Installed Modules & Apps ---")
        module = client.env["ir.module.module"]
        installed_apps = module.search_read(
            [("state", "=", "installed"), ("application", "=", True)],
            fields=["name", "shortdesc", "installed_version"],
            limit=10,
        )
        print(f"Installed Main Apps ({len(installed_apps)}):")
        for app in installed_apps:
            print(
                f"  - {app['name']}: {app['shortdesc']} "
                f"(v{app['installed_version']})"
            )

        # 3. Discover Studio & Custom Models (x_*)
        print("\n--- 2. Custom & Studio Models (x_*) ---")
        ir_model = client.env["ir.model"]
        studio_models = ir_model.search_read(
            [("model", "like", "x_")],
            fields=["model", "name", "state"],
            limit=10,
        )
        if studio_models:
            print(f"Found {len(studio_models)} Custom Studio Model(s):")
            for model in studio_models:
                print(
                    f"  - {model['model']} ({model['name']}) "
                    f"[State: {model.get('state')}]"
                )
        else:
            print("No custom Studio (x_*) models found.")

        # 4. Inspect Model Fields Metadata (ir.model.fields)
        print("\n--- 3. Field Discovery for 'res.partner' ---")
        ir_field = client.env["ir.model.fields"]
        partner_fields = ir_field.search_read(
            [("model", "=", "res.partner")],
            fields=["name", "field_description", "ttype", "required"],
            limit=10,
        )
        print(f"Sample Fields for res.partner ({len(partner_fields)}):")
        for field in partner_fields:
            req_str = " [Required]" if field.get("required") else ""
            print(
                f"  - {field['name']} ({field['ttype']}): "
                f"{field['field_description']}{req_str}"
            )

    except OdooJSON2Error as error:
        print(f"\n[✗] Odoo JSON-2 Error: {error}")
        if getattr(error, "status_code", None) == 401:
            print("\n[!] 401 Unauthorized Diagnosis:")
            print("  - External API requires Custom plan in Odoo Online.")
            print("  - Ensure ODOO_API_KEY in .env is valid.")
    except Exception as error:
        print(f"\n[✗] Error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
