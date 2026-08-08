"""
02_sales_and_inventory.py - Sales Order & Product Catalog Management using odoo-json2.
"""

import os
from dotenv import load_dotenv
from odoo_json2 import JSON2Client, OdooJSON2Error

load_dotenv()

HOST = os.getenv("ODOO_HOST", "mycompany.odoo.com")
API_KEY = os.getenv("ODOO_API_KEY", "your_bearer_api_key")
DATABASE = os.getenv("ODOO_DATABASE", "mycompany")


def main():
    print(f"Connecting to Odoo 19 instance at {HOST}...")
    client = JSON2Client(host=HOST, api_key=API_KEY, database=DATABASE, protocol="https")

    # Access models via odoorpc-style env dictionary syntax
    Product = client.env["product.product"]
    Partner = client.env["res.partner"]
    SaleOrder = client.env["sale.order"]

    try:
        # 1. Search for available products in catalog
        print("\n--- 1. Querying Product Catalog ---")
        products = Product.search_read(
            domain=[("sale_ok", "=", True)],
            fields=["id", "name", "list_price", "default_code"],
            limit=5
        )
        if not products:
            print("No published products found in catalog.")
            return

        for p in products:
            code_str = f"[{p['default_code']}] " if p.get("default_code") else ""
            print(f"Product ID: {p['id']} | {code_str}{p['name']} | Price: ${p.get('list_price', 0.0):.2f}")

        # 2. Find or pick a customer partner
        print("\n--- 2. Fetching Customer Partner ---")
        customers = Partner.search_read(domain=[("is_company", "=", True)], fields=["id", "name"], limit=1)
        if not customers:
            print("No customer partners found. Creating a test customer...")
            customer_id = Partner.create({"name": "Global Tech Logistics", "is_company": True})[0]
        else:
            customer_id = customers[0]["id"]
            print(f"Selected Customer: {customers[0]['name']} (ID: {customer_id})")

        # 3. Create a new Quotation / Sales Order with order line
        print("\n--- 3. Creating Sales Quotation ---")
        selected_product = products[0]
        
        sale_order_ids = SaleOrder.create([{
            "partner_id": customer_id,
            "order_line": [
                (0, 0, {
                    "product_id": selected_product["id"],
                    "product_uom_qty": 5,
                    "price_unit": selected_product.get("list_price", 100.0),
                })
            ]
        }])
        
        order_id = sale_order_ids[0]
        print(f"[✓] Created Quotation / Sale Order ID: {order_id}")

        # 4. Read Quotation summary
        order_info = SaleOrder.read([order_id], fields=["name", "amount_total", "state"])[0]
        print(f"Order Summary: {order_info['name']} | Total: ${order_info.get('amount_total', 0.0):.2f} | Status: {order_info['state']}")

    except OdooJSON2Error as e:
        print(f"Odoo Sales API Error: {e}")


if __name__ == "__main__":
    main()
