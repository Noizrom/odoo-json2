import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import random
from faker import Faker
from rich.progress import track
from dotenv import load_dotenv

from odoo_rpc_utils import OdooClient, console

load_dotenv()
fake = Faker()

# --- Helpers ---
def get_psgc_data(odoo):
    """
    Fetches PSGC data and builds a structured lookup.
    Returns:
        provinces: dict of key -> id
        municipalities: dict of key -> {id, province_key}
        barangays_by_muni: dict of municipal_key -> [list of {id, name}]
    """
    console.print("[cyan]Fetching PSGC data (this might take a moment)...[/cyan]")
    PSGC = odoo.env['psa.psgc']
    
    # Fetch needed fields
    fields = ['id', 'area_type', 'region_code', 'province_code', 'municipal_code', 'barangay_code', 'name']
    
    # Optimize: Fetch only a random subset of barangays to avoid timeout
    # Fetch all Provinces and Municipalities first (they are few)
    prov_ids = PSGC.search([('area_type', '=', 'Province')])
    muni_ids = PSGC.search([('area_type', 'in', ['Municipal', 'City'])])
    
    # Fetch random 1000 barangays
    # Since we can't easily random sort in search, we verify total count and pick a range or just limit
    # For simplicity, just get first 2000. It's enough for mock data variety.
    bar_ids = PSGC.search([('area_type', '=', 'Barangay')], limit=2000)
    
    all_ids = prov_ids + muni_ids + bar_ids
    console.print(f"Fetching {len(all_ids)} PSGC records (Optimized)...")
    
    # Read in batches
    records = []
    batch_size = 2000
    for i in track(range(0, len(all_ids), batch_size), description="Reading PSGC..."):
        batch_ids = all_ids[i:i+batch_size]
        try:
            records.extend(PSGC.read(batch_ids, fields))
        except Exception as e:
            console.print(f"[yellow]Batch read failed: {e}[/yellow]")

    provinces = {} # (reg, prov) -> id
    municipalities = {} # (reg, prov, mun) -> id
    barangays = [] # list of dicts

    for r in records:
        atype = r.get('area_type')
        reg = r.get('region_code')
        prov = r.get('province_code')
        mun = r.get('municipal_code')
        bar = r.get('barangay_code')
        
        if atype == 'Province':
            key = (reg, prov)
            provinces[key] = r['id']
        elif atype in ['Municipal', 'City']:
            key = (reg, prov, mun)
            municipalities[key] = r['id']
        elif atype == 'Barangay':
            barangays.append(r)
    
    console.print(f"Mapped {len(provinces)} provinces, {len(municipalities)} municipalities, {len(barangays)} barangays.")
    return provinces, municipalities, barangays

def get_companies(odoo):
    return odoo.env['res.company'].search([])

def generate_employee_vals(psgc_data, company_ids):
    provinces, municipalities, all_barangays = psgc_data
    
    # Gender
    gender = random.choice(['male', 'female'])
    
    # Name
    if gender == 'male':
        first_name = fake.first_name_male()
        middle_name = fake.last_name() # Using surname as middle
    else:
        first_name = fake.first_name_female()
        middle_name = fake.last_name()
    
    surname = fake.last_name()
    
    # Parents (Random names)
    father_fname = fake.first_name_male()
    father_sname = surname # Usually same surname
    mother_fname = fake.first_name_female()
    mother_sname = fake.last_name() # Maiden name

    # Address Logic
    # Pick a random barangay
    # We need to trace back its Mun/City and Province
    if not all_barangays:
        bar_id = False
        mun_id = False
        prov_id = False
    else:
        bar = random.choice(all_barangays)
        bar_id = bar['id']
        
        reg = bar['region_code']
        prov = bar['province_code']
        mun = bar['municipal_code']
        
        mun_key = (reg, prov, mun)
        prov_key = (reg, prov)
        
        mun_id = municipalities.get(mun_key, False)
        prov_id = provinces.get(prov_key, False)

    # We reuse the same logic for Permanent and Residential for simplicity, 
    # but maybe different for realism? Let's make them different 50% of time.
    def get_addr_set():
        if not all_barangays: return (False, False, False)
        b = random.choice(all_barangays)
        mk = (b['region_code'], b['province_code'], b['municipal_code'])
        pk = (b['region_code'], b['province_code'])
        return (
            b['id'],
            municipalities.get(mk, False),
            provinces.get(pk, False)
        )

    p_bar, p_mun, p_prov = get_addr_set()
    r_bar, r_mun, r_prov = get_addr_set()

    vals = {
        'first_name': first_name,
        'surname': surname,
        # 'middle_name': middle_name, # Not in required_fields.csv but common
        'gender': gender,
        'citizenship': 'filipino', # Default for PSA usually
        'civil_status': random.choice(['single', 'married', 'widowed', 'separated']),
        'date_of_birth': fake.date_of_birth(minimum_age=20, maximum_age=65).strftime('%Y-%m-%d'),
        'height': round(random.uniform(1.50, 1.90), 2),
        'weight': round(random.uniform(50, 90), 2),
        
        # Parents
        'father_first_name': father_fname,
        'father_surname': father_sname,
        'mother_first_name': mother_fname,
        'mother_surname': mother_sname,
        
        # Permanent Address
        'p_address_street': fake.street_name(),
        'p_address_house_no': fake.building_number(),
        'p_address_zip': fake.postcode(),
        'p_address_barangay_id': p_bar,
        'p_address_city_id': p_mun,
        'p_address_province_id': p_prov,
        
        # Residential Address
        'r_address_street': fake.street_name(),
        'r_address_house_no': fake.building_number(),
        'r_address_zip': fake.postcode(),
        'r_address_barangay_id': r_bar,
        'r_address_city_id': r_mun,
        'r_address_province_id': r_prov,
        
        # Company
        'company_id': random.choice(company_ids) if company_ids else False,
    }
    
    return vals

def main():
    try:
        # Connect to Odoo
        client = OdooClient.from_env()
        client.login()
        odoo = client.odoo
        
        console.print(f"[green]Connected as {client.username}[/green]")
        
        # 1. Fetch References
        psgc_data = get_psgc_data(odoo)
        company_ids = get_companies(odoo)
        
        # 2. Fetch Employees
        Employee = odoo.env['hr.employee']
        employee_ids = Employee.search([])
        console.print(f"[cyan]Found {len(employee_ids)} employees to update.[/cyan]")
        
        # 3. Update Loop
        success_count = 0
        with console.status("[bold green]Updating employees...") as status:
            for emp_id in track(employee_ids, description="Updating employees..."):
                try:
                    vals = generate_employee_vals(psgc_data, company_ids)
                    Employee.write([emp_id], vals)
                    success_count += 1
                except Exception as e:
                    console.print(f"[red]Failed to update employee {emp_id}: {e}[/red]")
                    
        console.print(f"[bold green]Successfully updated {success_count}/{len(employee_ids)} employees![/bold green]")
        
    except Exception as e:
        console.print(f"[red]Fatal Error: {e}[/red]")

if __name__ == "__main__":
    main()
