import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from odoo_rpc_utils import OdooClient, console
from dotenv import load_dotenv

load_dotenv()

def inspect_psgc():
    try:
        # Initialize client
        client = OdooClient.from_env()
        client.login()
        odoo = client.odoo
        
        # Check fields of psa.psgc
        # We want to find barangays and see if they link to city/province
        PSGC = odoo.env['psa.psgc']
        
        # Search for a few records
        ids = PSGC.search([], limit=5)
        records = PSGC.read(ids, [])
        
        console.print("[bold]Sample PSGC Records Keys:[/bold]")
        if records:
            console.print(list(records[0].keys()))
            
        console.print("\n[bold]Sample Data:[/bold]")
        for r in records:
            console.print(r)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    inspect_psgc()
