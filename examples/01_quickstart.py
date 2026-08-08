"""
01_quickstart.py - Basic CRUD operations with Odoo 19 JSON-2 API.
"""

import os
from dotenv import load_dotenv
from odoo_json2 import JSON2Client, OdooJSON2Error

load_dotenv()

HOST = os.getenv("ODOO_HOST", "mycompany.odoo.com")
API_KEY = os.getenv("ODOO_API_KEY", "your_bearer_api_key")
DATABASE = os.getenv("ODOO_DATABASE", "mycompany")


def main():
    print(f"Connecting to Odoo 19 JSON-2 API at {HOST}...")
    client = JSON2Client(host=HOST, api_key=API_KEY, database=DATABASE, protocol="https")

    # Access models via odoorpc-style env dictionary syntax
    Partner = client.env["res.partner"]

    try:
        # 1. Search & Read
        print("\n--- Searching for Companies ---")
        companies = Partner.search_read(
            domain=[("is_company", "=", True)],
            fields=["id", "name", "email", "phone"],
            limit=3
        )
        for comp in companies:
            print(f"[{comp['id']}] {comp['name']} | Email: {comp.get('email', '-')}")

        # 2. Create Record
        print("\n--- Creating New Partner Record ---")
        new_ids = Partner.create([{
            "name": "Acme Global Solutions",
            "email": "contact@acmeglobal.example",
            "is_company": True
        }])
        new_id = new_ids[0]
        print(f"Successfully created Partner ID: {new_id}")

        # 3. Read Record
        record = Partner.read([new_id], fields=["name", "email"])[0]
        print(f"Read back record: {record}")

        # 4. Update Record
        print("\n--- Updating Partner Record ---")
        Partner.write([new_id], {"phone": "+1-800-555-0199"})
        print("Updated phone number.")

        # 5. Delete Record
        print("\n--- Cleaning Up Record ---")
        Partner.unlink([new_id])
        print(f"Unlinked Partner ID: {new_id}")

    except OdooJSON2Error as e:
        print(f"Odoo API Error: {e}")


if __name__ == "__main__":
    main()
