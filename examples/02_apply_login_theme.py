"""
02_apply_login_theme.py - Injecting modern QWeb glassmorphic theme into web.login_layout.
"""

import os
from dotenv import load_dotenv
from odoo_json2 import JSON2Client, apply_login_theme, OdooJSON2Error

load_dotenv()

HOST = os.getenv("ODOO_HOST", "mycompany.odoo.com")
API_KEY = os.getenv("ODOO_API_KEY", "your_bearer_api_key")
DATABASE = os.getenv("ODOO_DATABASE", "mycompany")


def main():
    print(f"Connecting to Odoo 19 instance: {HOST}...")
    client = JSON2Client(host=HOST, api_key=API_KEY, database=DATABASE, protocol="https")

    try:
        print("Injecting glassmorphic login page theme over JSON-2 API...")
        result = apply_login_theme(client, theme_name="glassmorphism")
        
        print("\n--- Result ---")
        print(f"Status:    {result['status']}")
        print(f"View ID:   {result['view_id']}")
        print(f"View Name: {result['name']}")
        print("\nOpen your browser and navigate to the login page to see your modern glassmorphic theme!")

    except OdooJSON2Error as e:
        print(f"Failed to apply theme: {e}")


if __name__ == "__main__":
    main()
