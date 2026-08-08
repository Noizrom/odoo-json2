# Developer & AI Agent Guide (`AGENT.md`)

Welcome to `odoo-json2`! This guide provides architecture overview, development workflows, testing instructions, and codebase conventions for human developers and AI coding agents.

---

## 🛠️ Package Overview & Architecture

`odoo-json2` is a lightweight, modern Python 3 library and CLI for interacting with Odoo 19+ instances over the new **External JSON-2 API (`/json/2`)**.

### Directory Structure
```text
odoo-rpc/
├── src/
│   ├── odoo_json2/           # Core library package
│   │   ├── __init__.py       # Public package exports & version
│   │   ├── client.py         # JSON2Client main HTTP client & endpoint handler
│   │   ├── env.py            # Environment dict accessor & ModelProxy dynamic ORM
│   │   ├── exceptions.py     # Custom exception hierarchy
│   │   ├── theme.py          # QWeb login page theme manager
│   │   └── cli.py            # Rich terminal CLI interface (odoo-json2)
│   └── odoo_rpc_utils/       # Legacy compatibility wrapper module
├── tests/                    # Pytest suite (100% mocked HTTP tests)
├── examples/                 # Public demo scripts & tutorials
├── scratchpad/               # Local exploratory testing playground (gitignored)
├── .github/workflows/        # GitHub Actions CI pipelines
├── pyproject.toml            # Build metadata, dependencies & CLI script definition
└── README.md                 # Public badged documentation
```

---

## ⚡ Development Setup with `uv`

We use **`uv`** for fast Python package and virtual environment management.

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-username/odoo-json2.git
cd odoo-json2

# Create virtual environment and install in editable mode with dev dependencies
uv venv
uv pip install -e ".[dev]"
```

---

## 🧪 Running Tests & Quality Verification

All HTTP calls in unit tests are mocked using `requests-mock` so tests run deterministically without requiring a live Odoo instance.

```bash
# Run full pytest suite
uv run python -m pytest -p no:xonsh

# Run tests with coverage report
uv run python -m pytest --cov=src/odoo_json2 -p no:xonsh
```

---

## 🔌 Odoo 19 External JSON-2 API Protocol Rules

When adding new ORM methods or API proxies, ensure adherence to Odoo 19 spec:

1. **HTTP Endpoint**: `POST /json/2/<model>/<method>`
2. **Headers**:
   - `Authorization: bearer <API_KEY>` (Required)
   - `Content-Type: application/json; charset=utf-8` (Required)
   - `X-Odoo-Database: <dbname>` (Optional / Required if multi-DB without host filter)
3. **Payload Parameters**: All method arguments must be passed as **named JSON keys** (`ids`, `context`, `domain`, `fields`, `limit`, etc.). Positional parameter arrays are NOT used in JSON-2.
4. **Transaction Handling**: Each HTTP request executes in a single SQL transaction. Successful HTTP 200 responses commit SQL; HTTP 4xx/5xx responses trigger a rollback.

---

## 📝 Code & Contribution Conventions

- **Type Hints**: All new public functions and methods must include Python 3 typing annotations.
- **Rich Formatting**: CLI commands and user-facing logging should leverage `rich` console tables, panels, and syntax highlighters.
- **Exception Mapping**: Ensure HTTP response status codes are mapped to appropriate exceptions (`OdooAuthError` for 401, `OdooNotFoundError` for 404, `OdooValidationError` for 422, `OdooServerException` for 500).
