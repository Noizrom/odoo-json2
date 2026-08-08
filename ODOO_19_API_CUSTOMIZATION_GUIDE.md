# Odoo 19 External JSON-2 API & Customization Guide

> **Note on Versioning & Deprecation:**  
> Starting in **Odoo 19.0**, the legacy XML-RPC (`/xmlrpc`, `/xmlrpc/2`), JSON-RPC (`/jsonrpc`), and third-party libraries like `odoorpc` are **deprecated**. They remain supported concurrently through Odoo 21, with **complete removal scheduled for Odoo 22 (Fall 2028)**.  
> Odoo 19 introduces the **External JSON-2 API (`/json/2`)** as the new standard HTTP interface for external integrations.

---

## 1. Odoo 19 External JSON-2 API Specification

### Endpoint Format
All ORM method invocations use `POST` requests to:
```http
POST /json/2/<model>/<method> HTTP/1.1
```

### Request Headers
| Header | Requirement | Description |
| :--- | :--- | :--- |
| `Authorization` | **Required** | `bearer <API_KEY>` |
| `Content-Type` | **Required** | `application/json; charset=utf-8` |
| `X-Odoo-Database` | Optional | Database name (Required if multi-DB instance and domain dbfilter is not configured) |
| `User-Agent` | Recommended | Identifier for client application |

### Request Body Schema
The JSON payload passes parameters as named key-value pairs:
```json
{
  "ids": [10, 11],
  "context": {
    "lang": "en_US"
  },
  "domain": [
    ["is_company", "=", true]
  ],
  "fields": ["name", "email"]
}
```
*Note:* All parameters in JSON-2 are named keyword parameters (no positional arguments array).

### Success Response (HTTP 200)
Returns the JSON-serialized result of the ORM method:
```json
[
  {"id": 10, "name": "Azure Interior", "email": "azure@example.com"}
]
```

### Error Response (HTTP 4xx / 5xx)
Returns an error object containing exception diagnostics:
```json
{
  "name": "werkzeug.exceptions.Unauthorized",
  "message": "Invalid apikey",
  "arguments": ["Invalid apikey", 401],
  "context": {},
  "debug": "Traceback (most recent call last)..."
}
```

### Transaction Isolation
Each `/json/2` HTTP request executes within its own isolated **SQL transaction**. 
- On HTTP 200, the SQL transaction is committed automatically.
- On error (4xx/5xx), the SQL transaction is rolled back.
- *Caveat:* External side-effects (such as HTTP webhooks or outbound emails dispatched during execution) are non-transactional and will not be rolled back by a SQL failure.

### Plan & License Requirements
Access to the External API (`/json/2` and legacy RPC) is available **only on Custom Odoo pricing plans**. It is **not available** on *One App Free* or *Standard* plans.

---

## 2. API Key Management & Authentication

Odoo 19 replaces username/password session authentication for external clients with **API Keys**.

### Manual Generation
1. Navigate to **User Profile / Preferences** ‣ **Account Security**.
2. Click **New API Key**.
3. Provide a description and expiration duration. (Manual keys have a maximum validity of **3 months**).
4. Store the 160-bit key securely; it is shown only once upon creation.

### Programmatic Generation & Revocation
With appropriate permissions (`base.enable_programmatic_api_keys = True`), users can manage keys via API:

#### Generate API Key:
```python
import requests

API_KEY = "your_existing_valid_api_key"

response = requests.post(
    "https://mycompany.odoo.com/json/2/res.users.apikeys/generate",
    headers={"Authorization": f"bearer {API_KEY}"},
    json={
        "key": API_KEY,
        "scope": None,  # None or "rpc"
        "name": "Integration Service Key",
        "expiration_date": "2026-05-19"
    }
)
new_key = response.json()
```

#### Revoke API Key:
```python
response = requests.post(
    "https://mycompany.odoo.com/json/2/res.users.apikeys/revoke",
    headers={"Authorization": f"bearer {API_KEY}"},
    json={
        "key": key_to_revoke
    }
)
```

---

## 3. Deprecation & Migration Matrix (XML-RPC / JSON-RPC -> JSON-2)

| Feature | Legacy XML-RPC / JSON-RPC (`odoorpc`) | Odoo 19 External JSON-2 API |
| :--- | :--- | :--- |
| **Status** | Deprecated in v19 (Removed in v22 / 2028) | **Current Standard (v19+)** |
| **Authentication** | `login(db, username, password)` -> Returns `uid` | `Authorization: bearer <API_KEY>` |
| **Endpoint** | `/xmlrpc/2/object` or `/jsonrpc` | `/json/2/<model>/<method>` |
| **Argument Style** | Positional arrays (`args`) + kwargs dict | Named JSON key-value parameters |
| **Server Version** | `common.version()` | `GET /web/version` |
| **Database Operations**| `/xmlrpc/2/db` | `/web/database/*` HTTP controllers |

---

## 4. Customizing Odoo over API (Without Server / Python Access)

When hosting on Odoo SaaS or lacking backend server/filesystem access, you can perform extensive UI and data customizations by manipulating Odoo technical data models over the JSON-2 API.

### A. Modifying QWeb Views (`ir.ui.view`)
UI structures (Form, List, Kanban, QWeb pages) are stored in `ir.ui.view`. You can extend existing views using QWeb `<xpath>` inheritances.

#### Target Models for UI Customization:
- **`web.login_layout`**: Master wrapper template for the login screen (calls `web.frontend_layout`).
- **`web.login`**: Core login card form (contains login inputs, database selection, password fields).
- **`web.frontend_layout`**: Modern frontend root layout containing `<head>` and asset bundle loads.

### B. Injecting Custom CSS & JavaScript
Custom styling can be applied in two ways over API:

1. **Embedded `<style>` Tags in Inherited QWeb View:**
   Create an inherited view targeting `web.login_layout` or `web.frontend_layout` and insert a `<style>` block into the head.

2. **Web Asset Bundling (`ir.asset`):**
   Create an `ir.asset` record referencing an external CDN stylesheet or a public attachment URL (`/web/content/<attachment_id>`).
   *Requirement:* Attachments used for asset paths must have `public = True` or an `access_token`.

### C. Creating Custom Models & Fields via API
- **Models (`ir.model`)**: Create new technical models dynamically.
- **Fields (`ir.model.fields`)**: Create new custom fields (e.g., `x_custom_field`).

### D. Server Actions & Automated Actions
- **`base.automation`**: Triggers execution on record create/write/unlink.
- **`ir.actions.server`**: Executes Python code inside Odoo's `safe_eval` sandbox.

#### Sandboxed Python Context in Odoo 19:
Available variables in `ir.actions.server`:
`env`, `model`, `record`, `records`, `uid`, `user`, `time`, `datetime`, `dateutil`, `timezone`, `float_compare`, `b64encode`, `b64decode`, `Command`, `log`, `_logger`, `UserError`.

*Security Restriction:* `safe_eval` prohibits `import`, system binaries, filesystem access, or unauthorized bytecode execution.

---

## 5. Complete Python 3 JSON-2 Client & Login Redesign Script

Below is a complete Python module (`json2_odoo_client.py`) using `requests` to interact with Odoo 19 JSON-2 API and apply a modern glassmorphic theme to the Odoo Login Page.

```python
from src.odoo_rpc_utils import JSON2OdooClient

# 1. Initialize with host and Bearer API Key
client = JSON2OdooClient(host="mycompany.odoo.com", api_key="YOUR_API_KEY", database="mycompany")

# 2. Access models via odoorpc-style env syntax:
Partner = client.env['res.partner']

# Search & Read records
partners = Partner.search_read([('is_company', '=', True)], fields=['name', 'email'], limit=5)

# Create record
new_id = Partner.create({'name': 'Acme Corporation', 'email': 'info@acme.com'})

# Write / Update record
Partner.write([new_id], {'phone': '+1-555-0199'})

# Delete record
Partner.unlink([new_id])
```

def apply_modern_login_theme(client: JSON2OdooClient):
    """Injects a modern glassmorphic design into the Odoo 19 login page via ir.ui.view over JSON-2 API."""
    
    # 1. Locate web.login_layout view
    views = client.search_read("ir.ui.view", domain=[("key", "=", "web.login_layout")], fields=["id", "name"])
    if not views:
        raise RuntimeError("web.login_layout view not found")
    
    parent_id = views[0]["id"]
    
    # 2. Modern Glassmorphic CSS Theme
    modern_css = """
    <style>
        body {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }
        div.o_database_list {
            background: rgba(255, 255, 255, 0.07) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 24px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4) !important;
            padding: 32px !important;
        }
        .card-body {
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

    # 3. Create Inherited QWeb View targeting the container
    view_arch = f"""
    <xpath expr="//div[contains(@class, 'o_database_list')]" position="before">
        {modern_css}
    </xpath>
    """
    
    view_name = "Modern Glassmorphism Login Theme (JSON-2 API)"
    existing = client.search_read("ir.ui.view", domain=[("name", "=", view_name)], fields=["id"])
    
    if existing:
        client.write("ir.ui.view", ids=[existing[0]["id"]], vals={"arch": view_arch, "active": True})
        print(f"Updated existing login theme view ID: {existing[0]['id']}")
    else:
        created_ids = client.create("ir.ui.view", vals_list=[{
            "name": view_name,
            "type": "qweb",
            "mode": "extension",
            "inherit_id": parent_id,
            "arch": view_arch,
            "priority": 99
        }])
        print(f"Successfully created login theme view ID: {created_ids[0]}")


if __name__ == "__main__":
    # Example usage:
    # client = JSON2OdooClient(host="mycompany.odoo.com", api_key="YOUR_API_KEY", database="mycompany")
    # apply_modern_login_theme(client)
    pass
```
