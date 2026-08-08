"""
Rich CLI Interface for odoo-json2 library.
"""

import argparse
import json
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from .client import JSON2Client
from .exceptions import OdooJSON2Error

console = Console()


def get_client_from_args(args: argparse.Namespace) -> JSON2Client:
    load_dotenv(override=True)
    host = args.host or os.getenv("ODOO_HOST")
    api_key = args.key or os.getenv("ODOO_API_KEY")
    database = args.db or os.getenv("ODOO_DATABASE")
    protocol = args.protocol or os.getenv("ODOO_PROTOCOL", "https").replace("+ssl", "")

    if not host or not api_key:
        console.print("[bold red]Error:[/bold red] Odoo host and API key must be provided via CLI arguments or .env (ODOO_HOST, ODOO_API_KEY).")
        sys.exit(1)

    return JSON2Client(host=host, api_key=api_key, database=database, protocol=protocol, verify_ssl=not args.insecure)


def cmd_test_connection(args: argparse.Namespace) -> None:
    """Test connection to Odoo server, check version, and display system info."""
    client = get_client_from_args(args)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Connecting to Odoo 19 JSON-2 API...", total=None)
        
        try:
            version_info = client.version()
            # Test simple API query
            user_data = client.env["res.users"].search_read([], fields=["name", "login"], limit=1)
            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"[bold red]Connection Failed:[/bold red] {e}")
            sys.exit(1)

    table = Table(title="[bold green]Odoo 19 Connection Status[/bold green]", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Server Host", client.host)
    table.add_row("Protocol", client.protocol)
    table.add_row("Database", client.database or "[dim]Not Specified[/dim]")
    table.add_row("Server Version", str(version_info.get("server_version", "19.0")))
    table.add_row("JSON-2 Endpoint", f"{client.base_url}")
    table.add_row("Auth Status", "[bold green]Authenticated (Bearer Key)[/bold green]")

    console.print(table)


def cmd_inspect_model(args: argparse.Namespace) -> None:
    """Inspect model fields, types, and record count."""
    client = get_client_from_args(args)
    model_name = args.model

    with Progress(SpinnerColumn(), TextColumn(f"Inspecting model '{model_name}'..."), console=console):
        try:
            count = client.env[model_name].search_count([])
            fields_dict = client.env[model_name].fields_get(attributes=["type", "string", "required"])
        except OdooJSON2Error as e:
            console.print(f"[bold red]Inspect Failed:[/bold red] {e}")
            sys.exit(1)

    table = Table(title=f"Model Inspection: [bold cyan]{model_name}[/bold cyan] (Total Records: {count})", header_style="bold blue")
    table.add_column("Field Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Label / String", style="green")
    table.add_column("Required", style="yellow")

    for f_name, f_info in sorted(fields_dict.items())[:args.limit]:
        table.add_row(
            f_name,
            str(f_info.get("type", "unknown")),
            str(f_info.get("string", "")),
            "✓" if f_info.get("required") else "-"
        )

    console.print(table)
    if len(fields_dict) > args.limit:
        console.print(f"[dim]Showing {args.limit} of {len(fields_dict)} total fields. Use --limit N to see more.[/dim]")


def cmd_search(args: argparse.Namespace) -> None:
    """Search and display records for a model."""
    client = get_client_from_args(args)
    model_name = args.model
    domain_str = args.domain

    try:
        domain = json.loads(domain_str) if domain_str else []
    except Exception:
        console.print("[bold red]Invalid domain JSON format.[/bold red]")
        sys.exit(1)

    fields = [f.strip() for f in args.fields.split(",")] if args.fields else None

    with Progress(SpinnerColumn(), TextColumn(f"Searching {model_name}..."), console=console):
        records = client.env[model_name].search_read(domain=domain, fields=fields, limit=args.limit)

    if args.json:
        syntax = Syntax(json.dumps(records, indent=2), "json", theme="monokai")
        console.print(syntax)
    else:
        table = Table(title=f"Search Results: {model_name} ({len(records)} records)", header_style="bold green")
        if records:
            keys = list(records[0].keys())
            for k in keys:
                table.add_column(k, style="cyan")
            for rec in records:
                table.add_row(*[str(rec.get(k, "")) for k in keys])
            console.print(table)
        else:
            console.print(f"[yellow]No records found for domain {domain}[/yellow]")




def main() -> None:
    parser = argparse.ArgumentParser(
        prog="odoo-json2",
        description="Odoo 19 External JSON-2 API CLI Utility"
    )
    parser.add_argument("--host", help="Odoo host (e.g. mycompany.odoo.com)")
    parser.add_argument("--key", help="Odoo Bearer API Key")
    parser.add_argument("--db", help="Odoo Database Name")
    parser.add_argument("--protocol", choices=["http", "https"], help="Protocol (http/https)")
    parser.add_argument("--insecure", action="store_true", help="Disable SSL verification")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # test-connection
    p_test = subparsers.add_parser("test-connection", help="Test connection & API key authentication")
    p_test.set_defaults(func=cmd_test_connection)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect a model's fields & count")
    p_inspect.add_argument("model", help="Technical model name (e.g. res.partner)")
    p_inspect.add_argument("--limit", type=int, default=30, help="Max fields to display")
    p_inspect.set_defaults(func=cmd_inspect_model)

    # search
    p_search = subparsers.add_parser("search", help="Search records in a model")
    p_search.add_argument("model", help="Technical model name")
    p_search.add_argument("--domain", default="[]", help="JSON domain array, e.g. '[[\"is_company\", \"=\", true]]'")
    p_search.add_argument("--fields", help="Comma-separated field names")
    p_search.add_argument("--limit", type=int, default=10, help="Limit results")
    p_search.add_argument("--json", action="store_true", help="Output raw JSON")
    p_search.set_defaults(func=cmd_search)


    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
