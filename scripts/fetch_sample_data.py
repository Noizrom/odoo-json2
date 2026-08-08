import csv
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from rich.table import Table
from dotenv import load_dotenv

from odoo_rpc_utils import OdooClient, console

# Load environment variables
load_dotenv()

def get_required_fields(csv_path):
    fields = []
    ignored = ['version_ids', 'resource_id']
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = row['Field Name']
            if fname not in ignored:
                fields.append(row)
    return fields

def main():
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "required_fields.csv"
    
    if not csv_path.exists():
        console.print(f"[red]File {csv_path} not found![/red]")
        return

    req_fields = get_required_fields(csv_path)
    field_names = [f['Field Name'] for f in req_fields]
    
    try:
        # Connect to Odoo
        client = OdooClient.from_env()
        client.login()
        odoo = client.odoo
        
        console.print(f"[green]Connected as {client.username}[/green]")

        Employee = odoo.env['hr.employee']
        
        # Try to find an employee who has address data set, to get a good sample
        # We look for one where p_address_barangay_id is set
        domain = [('p_address_barangay_id', '!=', False)]
        emp_ids = Employee.search(domain, limit=1)
        
        if not emp_ids:
            console.print("[yellow]No employee found with p_address_barangay_id set. Fetching any employee...[/yellow]")
            emp_ids = Employee.search([], limit=1)
            
        if not emp_ids:
            console.print("[red]No employees found![/red]")
            return

        emp_id = emp_ids[0]
        console.print(f"[cyan]Fetching data for Employee ID: {emp_id}[/cyan]")
        
        # Read the specific fields
        data = Employee.read(emp_ids, field_names)[0]
        
        # Document fields
        doc_lines = []
        doc_lines.append(f"# Sample Employee Data (ID: {emp_id})")
        doc_lines.append("")
        doc_lines.append("| Field Name | Label | Type | Sample Value (Raw) | Sample Value (Display) | Related Model |")
        doc_lines.append("|---|---|---|---|---|---|")

        # Also prepare a JSON payload example
        payload = {}

        for field_info in req_fields:
            fname = field_info['Field Name']
            flabel = field_info['Field Label']
            ftype = field_info['Field Type']
            rel_model = field_info['Related Model']
            
            val = data.get(fname)
            display_val = val
            raw_val = val

            # Handle Many2one (tuple: (id, name))
            if ftype == 'many2one' and isinstance(val, (list, tuple)) and len(val) == 2:
                raw_val = val[0] # ID
                display_val = val[1] # Name
                
                # Fetch more info about the related record?
                # User said: "some fields are m2o, so may need to fetch that first"
                # Let's just document the ID used.
                
            payload[fname] = raw_val
            
            doc_lines.append(f"| `{fname}` | {flabel} | {ftype} | `{raw_val}` | `{display_val}` | {rel_model} |")

        # Write to file
        # Write to file
        with open(data_dir / 'employee_sample_reference.md', 'w', encoding='utf-8') as f:
            f.write("\n".join(doc_lines))
        
        with open(data_dir / 'employee_sample_payload.json', 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)

        console.print(f"[green]Documentation saved to {data_dir}[/green]")
        console.print(Table("Field", "Value", title="Sample Data Preview"))
        
        # Show a preview on console
        preview_table = Table(show_header=True, header_style="bold magenta")
        preview_table.add_column("Field")
        preview_table.add_column("Value")
        for k, v in list(payload.items())[:10]: # First 10
            preview_table.add_row(str(k), str(v))
        console.print(preview_table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
