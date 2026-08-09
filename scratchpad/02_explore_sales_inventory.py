"""Explore sales orders, products, and partners through the JSON-2 API."""

import os

from dotenv import load_dotenv

from odoo_json2 import JSON2Client, OdooJSON2Error

load_dotenv(override=True)

HOST = os.getenv("ODOO_HOST", "noizr-test.odoo.com")
API_KEY = os.getenv("ODOO_API_KEY", "")
DATABASE = os.getenv("ODOO_DATABASE", "noizr-test")
PROTOCOL = os.getenv("ODOO_PROTOCOL", "https")


def main() -> None:
    """Run the sales and inventory exploration scratchpad."""
    print(f"=== Odoo 19 Business Explorer ({HOST}) ===")
    client = JSON2Client(
        host=HOST,
        api_key=API_KEY,
        database=DATABASE,
        protocol=PROTOCOL,
    )

    try:
        # 1. Partner Exploration
        print("\n--- 1. Company Partners ---")
        partner = client.env["res.partner"]
        companies = partner.search_read(
            domain=[("is_company", "=", True)],
            fields=["id", "name", "email", "phone", "city", "country_id"],
            limit=5,
        )
        print(f"Found {len(companies)} company partner(s):")
        for company in companies:
            print(
                f"  - [{company['id']}] {company['name']} | "
                f"Email: {company.get('email', '-')} | "
                f"Phone: {company.get('phone', '-')}"
            )
        # 2. Studio / Custom Data Records
        print("\n--- 2. Custom Studio App Records (x_employees / x_leave_cards) ---")
        for custom_model in [
            "x_employees",
            "x_leave_cards",
            "x_accomplishment_repor",
        ]:
            try:
                records = client.env[custom_model].search_read(
                    [],
                    fields=["id", "display_name", "x_name", "name"],
                    limit=3,
                )
                print(f"Found {len(records)} record(s) in '{custom_model}':")
                for record in records:
                    name_value = (
                        record.get("display_name")
                        or record.get("x_name")
                        or record.get("name")
                        or f"ID {record['id']}"
                    )
                    print(f"  - [{record['id']}] {name_value}")
            except Exception as error:
                print(f"Model '{custom_model}' not available or unreadable: {error}")
        # 3. Sales Orders
        print("\n--- 3. Recent Sales Orders ---")
        try:
            sale_order = client.env["sale.order"]
            orders = sale_order.search_read(
                domain=[],
                fields=["id", "name", "partner_id", "amount_total", "state"],
                limit=5,
            )
            print(f"Found {len(orders)} sales order(s):")
            for order in orders:
                print(
                    f"  - {order['name']} | "
                    f"Total: ${order.get('amount_total', 0.0):.2f}"
                )
        except Exception:
            print("Sales order model 'sale.order' is not installed on this database.")

    except OdooJSON2Error as error:
        print(f"\n[✗] Odoo JSON-2 Error: {error}")
        if getattr(error, "status_code", None) == 401:
            print("\n[!] 401 Unauthorized Diagnosis:")
            print("  - Check ODOO_API_KEY in .env.")
    except Exception as error:
        print(f"\n[✗] Error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
