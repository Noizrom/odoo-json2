# 🚀 odoo-json2

[![CI](https://github.com/Noizrom/odoo-json2/actions/workflows/ci.yml/badge.svg)](https://github.com/Noizrom/odoo-json2/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Odoo Version](https://img.shields.io/badge/odoo-19.0%2B-purple.svg)](https://www.odoo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Managed with uv](https://img.shields.io/badge/managed--with-uv-000000.svg)](https://github.com/astral-sh/uv)
[![Styled with Rich](https://img.shields.io/badge/UI-Rich-magenta.svg)](https://github.com/Textualize/rich)

> **The Modern Python Client & CLI for Odoo 19+ External JSON-2 API (`/json/2`)**  
> Built with `uv`, `rich` terminal output, type annotations, and 100% `odoorpc` backward-compatible `env['model_name']` syntax.

---

## ⚡ Why `odoo-json2`?

Starting in **Odoo 19.0**, legacy XML-RPC (`/xmlrpc`, `/xmlrpc/2`), JSON-RPC (`/jsonrpc`), and legacy libraries like `odoorpc` are **deprecated** and scheduled for complete removal in **Odoo 22 (Fall 2028)**.

`odoo-json2` is designed to be the premier Python library for Odoo 19+ external integrations:

- 🔒 **Bearer API Key Authentication**: Uses Odoo 19's native `Authorization: bearer <API_KEY>` scheme.
- ⚡ **Zero-Rewrite Migration from `odoorpc`**: Supports the exact `client.env['res.partner']` syntax you already know.
- 🎨 **Rich Terminal Experience**: Beautiful CLI with colorized tables, progress spinners, JSON syntax highlighting, and model inspection powered by `rich`.
- 📦 **Modern Tooling**: Package managed with `uv` and standard `pyproject.toml`.

---

## 📦 Installation

```bash
# Using uv (Recommended)
uv add odoo-json2

# Using pip
pip install odoo-json2
```

---

## 🚀 Quickstart

### 1. Python API

```python
from odoo_json2 import JSON2Client

# Initialize client with host and Bearer API Key
client = JSON2Client(
    host="mycompany.odoo.com",
    api_key="your_160bit_bearer_api_key",
    database="mycompany"
)

# Access models via odoorpc-style env dictionary syntax
Partner = client.env["res.partner"]

# Search and read records
companies = Partner.search_read(
    domain=[("is_company", "=", True)],
    fields=["name", "email", "phone"],
    limit=5
)
print(companies)

# Create record
new_id = Partner.create({
    "name": "Acme Global",
    "email": "contact@acme.example",
    "is_company": True
})

# Write / Update record
Partner.write([new_id], {"phone": "+1-800-555-0199"})

# Delete record
Partner.unlink([new_id])
```

---

## 💻 Rich CLI Usage

`odoo-json2` includes a built-in CLI tool with rich formatting:

```bash
# Test connection & display Odoo server info
odoo-json2 --host mycompany.odoo.com --key YOUR_API_KEY test-connection

# Inspect model fields, data types, and record count in a Rich table
odoo-json2 inspect res.partner --limit 20

# Search records and print formatted Rich table or JSON
odoo-json2 search res.partner --domain '[["is_company", "=", true]]' --fields "id,name,email"
odoo-json2 search res.partner --json

```

---

## 📁 Examples & Documentation

Explore the `examples/` directory for ready-to-run scripts:
- [`examples/01_quickstart.py`](examples/01_quickstart.py): Basic CRUD operations, `search_read`, `create`, `write`, and `unlink`.
- [`examples/02_customize_login_screen.py`](examples/02_customize_login_screen.py): QWeb login screen customization example built on generic `client.env["ir.ui.view"]` model proxy calls.
- [`examples/02_sales_and_inventory.py`](examples/02_sales_and_inventory.py): Sales quotation creation, product catalog queries, and customer management.
- [`scratchpad/ODOO_19_API_CUSTOMIZATION_GUIDE.md`](scratchpad/ODOO_19_API_CUSTOMIZATION_GUIDE.md): In-depth guide on JSON-2 API specifications, API Key security, and QWeb view customization without server access.
- [`AGENT.md`](AGENT.md): Architectural guide and developer workflow instructions for human developers and AI agents.

---

## 🔄 Migration Matrix: `odoorpc` -> `odoo-json2`

| Feature | Legacy `odoorpc` | `odoo-json2` |
| :--- | :--- | :--- |
| **API Endpoint** | `/xmlrpc/2/object` / `/jsonrpc` | `/json/2/<model>/<method>` |
| **Authentication** | `login(db, user, password)` | `Authorization: bearer <API_KEY>` |
| **Model Access** | `Partner = odoo.env['res.partner']` | `Partner = client.env['res.partner']` |
| **Search & Read** | `Partner.search_read(domain, fields)` | `Partner.search_read(domain, fields)` |
| **Create** | `Partner.create(vals_dict)` | `Partner.create(vals_dict)` |
| **Update / Write** | `Partner.write(ids, vals_dict)` | `Partner.write(ids, vals_dict)` |
| **Delete / Unlink**| `Partner.unlink(ids)` | `Partner.unlink(ids)` |

---

## 🧪 Development & Testing

```bash
# Clone repository
git clone https://github.com/Noizrom/odoo-json2.git

# Install dependencies with uv
uv pip install -e ".[dev]"

# Run test suite
uv run python -m pytest -p no:xonsh
```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
