import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from rich.table import Table
from dotenv import load_dotenv

from odoo_rpc_utils import OdooClient, console

load_dotenv()

def main():
    try:
        # Initialize client
        client = OdooClient.from_env()
        client.login()
        odoo = client.odoo
        
        console.print(f"[green]Connected as {client.username}[/green]")

        # Fetch employees
        Employee = odoo.env['hr.employee']
        
        # Get all employee IDs
        employee_ids = Employee.search([])
        console.print(f"[cyan]Found {len(employee_ids)} employees. Fetching details...[/cyan]")

        # Read details
        employees = Employee.read(employee_ids, ['id', 'name', 'work_email', 'department_id', 'job_id'])

        # Display results
        table = Table(title="HR Employees from Odoo")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Email", style="green")
        table.add_column("Department", style="blue")
        table.add_column("Job Title", style="yellow")

        for emp in employees:
            dept = emp.get('department_id')
            dept_name = dept[1] if dept else "-"
            
            job = emp.get('job_id')
            job_name = job[1] if job else "-"

            table.add_row(
                str(emp.get('id')),
                str(emp.get('name')),
                str(emp.get('work_email') or "-"),
                str(dept_name),
                str(job_name)
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
