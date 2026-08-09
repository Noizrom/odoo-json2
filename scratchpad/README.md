# Scratchpad: Odoo 19 JSON-2 API Exploratory Suite

This directory contains local exploratory and diagnostic scripts for inspecting
and customizing Odoo 19 instances through the external JSON-2 API (`/json/2`)
with `odoo-json2`.

## Credential Configuration

Copy [`.env.example`](../.env.example) to `.env` and configure credentials
before running a scratchpad:

- **Host:** `ODOO_HOST` (defaults to `noizr-test.odoo.com`)
- **Database:** `ODOO_DATABASE` (defaults to `noizr-test`)
- **API Key:** required `ODOO_API_KEY`; it is never stored in these scripts
- **Protocol:** `ODOO_PROTOCOL` (defaults to `https`)

---

## 📜 Exploratory Scripts

### 1. `test_noizr_connection.py`

- **Purpose:** Quick connection health check, server version lookup
  (`/web/version`), user-context check (`res.users`), partner lookup
  (`res.partner`), and Studio model count (`ir.model`).
- **Run:**

  ```bash
  uv run python scratchpad/test_noizr_connection.py
  ```

### 2. `01_explore_models_schema.py`

- **Purpose:** Deep schema and model metadata explorer. Inspects installed main
  apps (`ir.module.module`), Studio/custom models (`x_*`), and field definitions
  (`ir.model.fields`).
- **Run:**

  ```bash
  uv run python scratchpad/01_explore_models_schema.py
  ```

### 3. `02_explore_sales_inventory.py`

- **Purpose:** Business-domain explorer. Queries company partners
  (`res.partner`), product catalog (`product.product`), and sales orders
  (`sale.order`).
- **Run:**

  ```bash
  uv run python scratchpad/02_explore_sales_inventory.py
  ```

### 4. `03_explore_ui_customization.py`

- **Purpose:** Frontend and UI-customization explorer. Injects QWeb extension
  views (`ir.ui.view`) over `/json/2` to apply custom login-page styles without
  source-code access.
- **Run:**

  ```bash
  uv run python scratchpad/03_explore_ui_customization.py
  ```

### 5. `04_full_library_feature_demo.py`

- **Purpose:** End-to-end demonstration of `odoo_json2`: `JSON2Client`,
  `ModelProxy` ORM calls, exception handling, and QWeb theme injection.
- **Run:**

  ```bash
  uv run python scratchpad/04_full_library_feature_demo.py
  ```

### 6. CLI Exploration (`odoo-json2`)

- **Purpose:** Use the library's built-in Rich CLI from the terminal.
- **Run:**

  ```bash
  uv run odoo-json2 test-connection
  uv run odoo-json2 inspect res.partner
  ```

---

## 💡 Key Technical Insights & Troubleshooting

1. **Odoo 19 JSON-2 API Endpoint:**
   * Requests: `POST https://<host>/json/2/<model>/<method>`
   * Headers: `Authorization: bearer <API_KEY>`, `X-Odoo-Database: <dbname>`

2. **HTTP 401 `Unauthorized: Invalid apikey`:**
   * **Plan Requirement:** Odoo Online (SaaS) restricts External API access to **Custom** plans. It is not supported on *One App Free* or *Standard* plans.
   * **API Key Generation:** API keys must be generated inside Odoo under **User Preferences -> Security -> API Keys**.
   * **Database Match:** Ensure `X-Odoo-Database` matches the target database name.
