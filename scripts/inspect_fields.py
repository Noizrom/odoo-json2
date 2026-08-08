import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from odoo_rpc_utils import OdooClient, console
from dotenv import load_dotenv

load_dotenv()

def inspect_fields():
    try:
        # Initialize client
        client = OdooClient.from_env()
        client.login()
        odoo = client.odoo
        
        Employee = odoo.env['hr.employee']
        fields_info = Employee.fields_get(['civil_status', 'gender'])
        
        console.print("[bold]Civil Status Options:[/bold]")
        console.print(fields_info.get('civil_status', {}).get('selection'))

        console.print("\n[bold]Gender Options:[/bold]")
        console.print(fields_info.get('gender', {}).get('selection'))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    inspect_fields()
