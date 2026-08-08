
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from rich.progress import track
from dotenv import load_dotenv

from odoo_rpc_utils import OdooClient, console

load_dotenv()



def generate_login(name):
    """
    Generates a login from the name.
    Expects 'Surname, Firstname' format.
    Returns 'surname' (lowercase).
    """
    if ',' in name:
        login = name.split(',')[0].strip().lower()
    else:
        # Fallback for "First Last" or single word
        parts = name.split()
        login = parts[-1].lower() if parts else "user"
    
    # Clean up spaces in surname if any (e.g. "Dela Cruz" -> "dela cruz" or "delacruz")
    # User said "Benson", implies keeping it simple. 
    # Let's keep spaces as is, Odoo handles them, but standard is often no spaces.
    # But user specifically said "login is just the name".
    return login

def main():
    
    try:
        # Initialize client
        client = OdooClient.from_env()
        client.login()
        odoo = client.odoo
        
        console.print(f"[green]Connected as {client.username}[/green]")
        
        Employee = odoo.env['hr.employee']
        User = odoo.env['res.users']
        
        # Find employees without user_id
        emp_ids = Employee.search([('user_id', '=', False)])
        console.print(f"[cyan]Found {len(emp_ids)} employees without users.[/cyan]")
        
        if not emp_ids:
            return

        # Read names
        employees = Employee.read(emp_ids, ['name', 'work_email'])
        
        success_count = 0
        
        for emp in track(employees, description="Creating users..."):
            emp_id = emp['id']
            name = emp['name']
            
            login = generate_login(name)
            
            # Check if login exists
            existing = User.search([('login', '=', login)])
            if existing:
                # Append a number if duplicate
                login = f"{login}{emp_id}"
                console.print(f"[yellow]Login collision for {name}. Using {login}[/yellow]")

            try:
                # Create User
                user_vals = {
                    'name': name,
                    'login': login,
                    'password': login,
                    'active': True,
                    # Optional: 'email': emp.get('work_email') or f"{login}@example.com"
                }
                
                # We need to assign them to Internal User group usually to be useful
                # But let's stick to basics first. Odoo might auto-assign 'Internal User' (base.group_user)
                
                new_user_id = User.create(user_vals)
                
                # Update Employee
                Employee.write([emp_id], {'user_id': new_user_id})
                success_count += 1
                
            except Exception as e:
                console.print(f"[red]Failed to create user for {name} ({login}): {e}[/red]")
                
        console.print(f"[bold green]Successfully created {success_count} users![/bold green]")
        
    except Exception as e:
        console.print(f"[red]Fatal Error: {e}[/red]")

if __name__ == "__main__":
    main()
