"""
Odoo Mock Data Insertion Script

Recreates the data insertion from mock_data.xml using OdooRPC.
Inserts users and employees with all required fields and images.
"""

import base64
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from odoo_rpc_utils import OdooClient, console, setup_logging

# Setup logging
log = setup_logging("odoo-mock-data")


@dataclass
class UserData:
    """User account data"""
    xml_id: str
    name: str
    login: str
    password: str
    groups: list[str]


@dataclass
class EmployeeData:
    """Employee record data"""
    xml_id: str
    name: str
    surname: str
    first_name: str
    user_xml_id: str
    image_file: str
    employee_id_no: str
    work_email: str
    work_phone: str
    mobile_phone: str = None
    nature_of_employment: str = "Permanent"
    plantilla_id_no: str = None
    
    # Required fields from CSV
    citizenship: str = "filipino"
    civil_status: str = "single"
    date_of_birth: str = None
    father_first_name: str = None
    father_surname: str = None
    gender: str = None
    height: float = None
    mother_first_name: str = None
    mother_surname: str = None
    weight: float = None
    
    # Permanent address fields
    p_address_house_no: str = None
    p_address_street: str = None
    p_address_barangay_id: int = None
    p_address_city_id: int = None
    p_address_province_id: int = None
    p_address_zip: str = None
    
    # Residential address fields
    r_address_house_no: str = None
    r_address_street: str = None
    r_address_barangay_id: int = None
    r_address_city_id: int = None
    r_address_province_id: int = None
    r_address_zip: str = None


class OdooMockDataClient(OdooClient):
    """Client for inserting mock data into Odoo"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_id_map = {}  # Maps xml_id to created user ID
        self.image_dir = Path(__file__).parent.parent / "data" / "mock_faces"

    def encode_image(self, filename: str) -> str:
        """Encode image file to base64 string"""
        image_path = self.image_dir / filename
        if not image_path.exists():
            log.warning(f"Image not found: {image_path}")
            return ""
        
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def get_group_ids(self, group_refs: list[str]) -> list[int]:
        """Resolve group XML IDs to database IDs"""
        group_ids = []
        for ref in group_refs:
            try:
                # Parse module.xml_id format
                if "." in ref:
                    module, xml_id = ref.split(".", 1)
                    ir_model_data = self.odoo.env["ir.model.data"]
                    result = ir_model_data.search_read(
                        [("module", "=", module), ("name", "=", xml_id), ("model", "=", "res.groups")],
                        ["res_id"]
                    )
                    if result:
                        group_ids.append(result[0]["res_id"])
            except Exception as e:
                log.warning(f"Could not resolve group {ref}: {e}")
        return group_ids

    def get_record_id(self, model: str, domain: list) -> int:
        """Search for a record and return its ID"""
        try:
            Model = self.odoo.env[model]
            ids = Model.search(domain, limit=1)
            return ids[0] if ids else None
        except Exception as e:
            log.warning(f"Could not find record in {model} with domain {domain}: {e}")
            return None

    def create_user(self, user_data: UserData) -> int:
        """Create a user account"""
        try:
            Users = self.odoo.env["res.users"]
            
            # Check if user already exists
            existing = Users.search([("login", "=", user_data.login)])
            if existing:
                log.info(f"User {user_data.login} already exists, skipping")
                self.user_id_map[user_data.xml_id] = existing[0]
                return existing[0]
            
            # Get group IDs
            group_ids = self.get_group_ids(user_data.groups)
            
            # Get company ID (main company)
            company_id = self.get_record_id("res.company", [("name", "=", "My Company")])
            if not company_id:
                company_id = 1  # Fallback to ID 1
            
            vals = {
                "name": user_data.name,
                "login": user_data.login,
                "password": user_data.password,
                "group_ids": [(6, 0, group_ids)],
                "company_id": company_id,
                "company_ids": [(6, 0, [company_id])],
            }
            
            user_id = Users.create(vals)
            self.user_id_map[user_data.xml_id] = user_id
            log.info(f"Created user: {user_data.login} (ID: {user_id})")
            return user_id
            
        except Exception as e:
            log.error(f"Failed to create user {user_data.login}: {e}")
            return None

    def generate_random_date_of_birth(self) -> str:
        """Generate random date of birth (25-60 years old)"""
        years_ago = random.randint(25, 60)
        dob = datetime.now() - timedelta(days=years_ago * 365 + random.randint(0, 365))
        return dob.strftime("%Y-%m-%d")

    def generate_random_address_ids(self) -> dict:
        """Generate random but valid PSGC address IDs"""
        # These are sample IDs from the employee_sample_payload.json
        # In production, you'd query the psa.psgc model for valid IDs
        return {
            "p_barangay": 48790,
            "p_city": 45898,
            "p_province": 45873,
            "r_barangay": 49364,
            "r_city": 45813,
            "r_province": 45793,
        }

    def create_employee(self, emp_data: EmployeeData) -> int:
        """Create an employee record with all required fields"""
        try:
            Employees = self.odoo.env["hr.employee"]
            
            # Check if employee already exists
            existing = Employees.search([("employee_id_no", "=", emp_data.employee_id_no)])
            if existing:
                log.info(f"Employee {emp_data.employee_id_no} already exists, skipping")
                return existing[0]
            
            # Get user ID
            user_id = self.user_id_map.get(emp_data.user_xml_id)
            if not user_id:
                log.warning(f"User not found for {emp_data.user_xml_id}, skipping employee")
                return None
            
            # Encode image
            image_data = self.encode_image(emp_data.image_file)
            
            # Get nature of employment ID
            nature_id = self.get_record_id(
                "hr.nature.of.employment",
                [("name", "=", emp_data.nature_of_employment)]
            )
            
            # Get plantilla ID if specified
            plantilla_id = None
            if emp_data.plantilla_id_no:
                plantilla_id = self.get_record_id(
                    "hr.plantilla",
                    [("name", "=", emp_data.plantilla_id_no)]
                )
            
            # Generate missing required fields
            if not emp_data.date_of_birth:
                emp_data.date_of_birth = self.generate_random_date_of_birth()
            
            if not emp_data.gender:
                emp_data.gender = random.choice(["male", "female"])
            
            if not emp_data.height:
                emp_data.height = round(random.uniform(1.50, 1.90), 2)
            
            if not emp_data.weight:
                emp_data.weight = round(random.uniform(50.0, 90.0), 2)
            
            if not emp_data.civil_status:
                emp_data.civil_status = random.choice(["single", "married", "widowed", "separated"])
            
            # Generate parent names if missing
            if not emp_data.father_first_name:
                emp_data.father_first_name = random.choice(["Juan", "Pedro", "Jose", "Antonio", "Manuel"])
            if not emp_data.father_surname:
                emp_data.father_surname = emp_data.surname
            if not emp_data.mother_first_name:
                emp_data.mother_first_name = random.choice(["Maria", "Ana", "Rosa", "Carmen", "Teresa"])
            if not emp_data.mother_surname:
                emp_data.mother_surname = random.choice(["Santos", "Reyes", "Cruz", "Bautista", "Garcia"])
            
            # Generate address data if missing
            addr_ids = self.generate_random_address_ids()
            if not emp_data.p_address_barangay_id:
                emp_data.p_address_barangay_id = addr_ids["p_barangay"]
                emp_data.p_address_city_id = addr_ids["p_city"]
                emp_data.p_address_province_id = addr_ids["p_province"]
                emp_data.p_address_house_no = str(random.randint(1, 9999))
                emp_data.p_address_street = f"{random.choice(['Main', 'Oak', 'Pine', 'Maple'])} Street"
                emp_data.p_address_zip = f"{random.randint(1000, 9999)}"
            
            if not emp_data.r_address_barangay_id:
                emp_data.r_address_barangay_id = addr_ids["r_barangay"]
                emp_data.r_address_city_id = addr_ids["r_city"]
                emp_data.r_address_province_id = addr_ids["r_province"]
                emp_data.r_address_house_no = str(random.randint(1, 9999))
                emp_data.r_address_street = f"{random.choice(['First', 'Second', 'Third', 'Fourth'])} Avenue"
                emp_data.r_address_zip = f"{random.randint(1000, 9999)}"
            
            # Build employee values
            vals = {
                "name": emp_data.name,
                "surname": emp_data.surname,
                "first_name": emp_data.first_name,
                "user_id": user_id,
                "employee_id_no": emp_data.employee_id_no,
                "work_email": emp_data.work_email,
                "work_phone": emp_data.work_phone,
                
                # Required fields
                "citizenship": emp_data.citizenship,
                "civil_status": emp_data.civil_status,
                "date_of_birth": emp_data.date_of_birth,
                "gender": emp_data.gender,
                "height": emp_data.height,
                "weight": emp_data.weight,
                
                # Parent information
                "father_first_name": emp_data.father_first_name,
                "father_surname": emp_data.father_surname,
                "mother_first_name": emp_data.mother_first_name,
                "mother_surname": emp_data.mother_surname,
                
                # Permanent address
                "p_address_house_no": emp_data.p_address_house_no,
                "p_address_street": emp_data.p_address_street,
                "p_address_barangay_id": emp_data.p_address_barangay_id,
                "p_address_city_id": emp_data.p_address_city_id,
                "p_address_province_id": emp_data.p_address_province_id,
                "p_address_zip": emp_data.p_address_zip,
                
                # Residential address
                "r_address_house_no": emp_data.r_address_house_no,
                "r_address_street": emp_data.r_address_street,
                "r_address_barangay_id": emp_data.r_address_barangay_id,
                "r_address_city_id": emp_data.r_address_city_id,
                "r_address_province_id": emp_data.r_address_province_id,
                "r_address_zip": emp_data.r_address_zip,
            }
            
            # Add optional fields
            if emp_data.mobile_phone:
                vals["mobile_phone"] = emp_data.mobile_phone
            
            if image_data:
                vals["image_1920"] = image_data
            
            if nature_id:
                vals["nature_of_employment_id"] = nature_id
            
            if plantilla_id:
                vals["plantilla_id_no"] = plantilla_id
            
            emp_id = Employees.create(vals)
            log.info(f"Created employee: {emp_data.name} (ID: {emp_id})")
            return emp_id
            
        except Exception as e:
            log.error(f"Failed to create employee {emp_data.name}: {e}")
            import traceback
            log.error(traceback.format_exc())
            return None


def get_mock_data() -> tuple[list[UserData], list[EmployeeData]]:
    """Define all mock users and employees from the XML file"""
    
    users = [
        # Central Office Users
        UserData("user_aguinaldo", "Aguinaldo, Emilio", "aguinaldo", "aguinaldo",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_agoncillo", "Agoncillo, Marcela", "agoncillo", "agoncillo",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_ejacinto", "Jacinto, Emilio", "ejacinto", "ejacinto",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_rizal", "Rizal, Jose", "rizal", "rizal",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_mabini", "Mabini, Apolinario", "mabini", "mabini",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_magbanua", "Magbanua, Teresa", "magbanua", "magbanua",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_jaena", "Jaena, Graciano Lopez", "jaena", "jaena",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_hr_admin_co"]),
        UserData("user_aquino", "Aquino, Melchora", "aquino", "aquino",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_reviewer"]),
        UserData("user_balagtas", "Balagtas, Francisco", "balagtas", "balagtas",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_bonifacio", "Bonifacio, Andres", "bonifacio", "bonifacio",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_clara", "Clara, Maria", "clara", "clara",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_admin_staff"]),
        UserData("user_delacruz", "Dela Cruz, Juan", "delacruz", "delacruz",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_kasilag", "Kasilag, Lucrecia", "kasilag", "kasilag",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_silang", "Silang, Gabriela", "silang", "silang",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_approver"]),
        UserData("user_alonzo", "Alonzo, Teodora", "alonzo", "alonzo",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_benitez", "Benitez, Helena", "benitez", "benitez",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_approver"]),
        UserData("user_gdelpilar", "Del Pilar, Gregorio", "gdelpilar", "gdelpilar",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_mdelpilar", "Del Pilar, Marcelo", "mdelpilar", "mdelpilar",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_florentino", "Florentino, Leona", "florentino", "florentino",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_luna", "Luna, Antonio", "luna", "luna",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_reviewer"]),
        UserData("user_palma", "Palma, Cecilia", "palma", "palma",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_admin_staff"]),
        
        # Field Office Users
        UserData("user_escoda", "Escoda, Josefa Llanes", "escoda", "escoda",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_jluna", "Luna, Juan", "jluna", "jluna",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_hr_admin_ro"]),
        UserData("user_amorsolo", "Amorsolo, Fernando", "amorsolo", "amorsolo",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_laurel", "Laurel, Jose P.", "laurel", "laurel",
                ["base.group_user", "psa_roles.group_psa_employee"]),
        UserData("user_ponce", "Ponce, Mariano", "ponce", "ponce",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_admin_staff"]),
        UserData("user_quezon", "Quezon, Manuel L.", "quezon", "quezon",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_approver"]),
        UserData("user_roxas", "Roxas, Manuel", "roxas", "roxas",
                ["base.group_user", "psa_roles.group_psa_employee", "psa_roles.group_psa_reviewer"]),
    ]
    
    employees = [
        # Central Office Employees
        EmployeeData("emp_emilio_aguinaldo", "Aguinaldo, Emilio", "Aguinaldo", "Emilio",
                    "user_aguinaldo", "face_8.png", "100008",
                    "emilio.aguinaldo@psa.gov.ph", "(02) 8461-0008", "+63 917 100 0008",
                    plantilla_id_no="PSA-NSTAT-9-2015"),
        EmployeeData("emp_marcela_agoncillo", "Agoncillo, Marcela", "Agoncillo", "Marcela",
                    "user_agoncillo", "face_7.png", "100007",
                    "marcela.agoncillo@psa.gov.ph", "(02) 8461-0007", "+63 917 100 0007",
                    plantilla_id_no="PSA-ADAS5-7-2015"),
        EmployeeData("emp_ejacinto", "Jacinto, Emilio", "Jacinto", "Emilio",
                    "user_ejacinto", "face_18.png", "100018",
                    "emilio.jacinto@psa.gov.ph", "(02) 8461-0018",
                    plantilla_id_no="PSA-DNS-4-2015"),
        EmployeeData("emp_jose_rizal", "Rizal, Jose", "Rizal", "Jose",
                    "user_rizal", "face_4.png", "100004",
                    "jose.rizal@psa.gov.ph", "(02) 8461-0004", "+63 917 100 0004",
                    plantilla_id_no="PSA-ADAS3-13-2015"),
        EmployeeData("emp_apolinario_mabini", "Mabini, Apolinario", "Mabini", "Apolinario",
                    "user_mabini", "face_10.png", "100010",
                    "apolinario.mabini@psa.gov.ph", "(02) 8461-0010", "+63 917 100 0010",
                    plantilla_id_no="PSA-ASSNS-7-2015"),
        EmployeeData("emp_magbanua", "Magbanua, Teresa", "Magbanua", "Teresa",
                    "user_magbanua", "face_19.png", "100020",
                    "teresa.magbanua@psa.gov.ph", "(02) 8461-0020",
                    plantilla_id_no="PSA-CADOF-89-2015"),
        EmployeeData("emp_jaena", "Jaena, Graciano Lopez", "Jaena", "Graciano Lopez",
                    "user_jaena", "face_23.png", "100023",
                    "graciano.jaena@psa.gov.ph", "(02) 8461-0023",
                    plantilla_id_no="PSA-ADAS2-91-2015"),
        EmployeeData("emp_melchora_aquino", "Aquino, Melchora", "Aquino", "Melchora",
                    "user_aquino", "face_5.png", "100005",
                    "melchora.aquino@psa.gov.ph", "(02) 8461-0005", "+63 917 100 0005",
                    plantilla_id_no="PSA-ITO2-57-2015"),
        EmployeeData("emp_balagtas", "Balagtas, Francisco", "Balagtas", "Francisco",
                    "user_balagtas", "face_20.png", "100019",
                    "francisco.balagtas@psa.gov.ph", "(02) 8461-0019",
                    plantilla_id_no="PSA-INFOSA3-61-2015"),
        EmployeeData("emp_andres_bonifacio", "Bonifacio, Andres", "Bonifacio", "Andres",
                    "user_bonifacio", "face_6.png", "100006",
                    "andres.bonifacio@psa.gov.ph", "(02) 8461-0006", "+63 917 100 0006",
                    plantilla_id_no="PSA-INFOSA2-66-2015"),
        EmployeeData("emp_maria_clara", "Clara, Maria", "Clara", "Maria",
                    "user_clara", "face_1.png", "100001",
                    "maria.clara@psa.gov.ph", "(02) 8461-0001", "+63 917 100 0001",
                    plantilla_id_no="PSA-INFOSA3-58-2015"),
        EmployeeData("emp_juan_delacruz", "Dela Cruz, Juan", "Dela Cruz", "Juan",
                    "user_delacruz", "face_2.png", "100002",
                    "juan.delacruz@psa.gov.ph", "(02) 8461-0002", "+63 917 100 0002",
                    plantilla_id_no="PSA-INFOSA1-75-2015"),
        EmployeeData("emp_lucrecia_kasilag", "Kasilag, Lucrecia", "Kasilag", "Lucrecia",
                    "user_kasilag", "face_9.png", "100009",
                    "lucrecia.kasilag@psa.gov.ph", "(02) 8461-0009", "+63 917 100 0009",
                    plantilla_id_no="PSA-INFOSA1-77-2015"),
        EmployeeData("emp_gabriela_silang", "Silang, Gabriela", "Silang", "Gabriela",
                    "user_silang", "face_3.png", "100003",
                    "gabriela.silang@psa.gov.ph", "(02) 8461-0003", "+63 917 100 0003",
                    plantilla_id_no="PSA-ITO3-56-2015"),
        EmployeeData("emp_teodora_alonzo", "Alonzo, Teodora", "Alonzo", "Teodora",
                    "user_alonzo", "face_17.png", "100017",
                    "teodora.alonzo@psa.gov.ph", "(02) 8461-0017", "+63 917 100 0017",
                    plantilla_id_no="PSA-INFOSA1-87-2015"),
        EmployeeData("emp_helena_benitez", "Benitez, Helena", "Benitez", "Helena",
                    "user_benitez", "face_11.png", "100011",
                    "helena.benitez@psa.gov.ph", "(02) 8461-0011", "+63 917 100 0011",
                    plantilla_id_no="PSA-ITO2-59-2015"),
        EmployeeData("emp_gregorio_del_pilar", "Del Pilar, Gregorio", "Del Pilar", "Gregorio",
                    "user_gdelpilar", "face_14.png", "100014",
                    "gregorio.delpilar@psa.gov.ph", "(02) 8461-0014", "+63 917 100 0014",
                    plantilla_id_no="PSA-INFOSA3-63-2015"),
        EmployeeData("emp_marcelo_del_pilar", "Del Pilar, Marcelo", "Del Pilar", "Marcelo",
                    "user_mdelpilar", "face_16.png", "100016",
                    "marcelo.delpilar@psa.gov.ph", "(02) 8461-0016", "+63 917 100 0016",
                    plantilla_id_no="PSA-INFOSA2-79-2015"),
        EmployeeData("emp_leona_florentino", "Florentino, Leona", "Florentino", "Leona",
                    "user_florentino", "face_13.png", "100013",
                    "leona.florentino@psa.gov.ph", "(02) 8461-0013", "+63 917 100 0013",
                    plantilla_id_no="PSA-ADAS2-57-2015"),
        EmployeeData("emp_antonio_luna", "Luna, Antonio", "Luna", "Antonio",
                    "user_luna", "face_12.png", "100012",
                    "antonio.luna@psa.gov.ph", "(02) 8461-0012", "+63 917 100 0012",
                    plantilla_id_no="PSA-INFOSA3-62-2015"),
        EmployeeData("emp_cecilia_palma", "Palma, Cecilia", "Palma", "Cecilia",
                    "user_palma", "face_15.png", "100015",
                    "cecilia.palma@psa.gov.ph", "(02) 8461-0015", "+63 917 100 0015",
                    plantilla_id_no="PSA-INFOSA2-76-2015"),
        
        # Field Office Employees
        EmployeeData("emp_escoda", "Escoda, Josefa Llanes", "Escoda", "Josefa Llanes",
                    "user_escoda", "face_21.png", "100021",
                    "josefa.escoda@psa.gov.ph", "(02) 8461-0021",
                    plantilla_id_no="PSA-DIR2-18-2015"),
        EmployeeData("emp_jluna", "Luna, Juan", "Luna", "Juan",
                    "user_jluna", "face_22.png", "100022",
                    "juan.luna@psa.gov.ph", "(02) 8461-0022",
                    plantilla_id_no="PSA-ADOF3-551-2015"),
        EmployeeData("emp_amorsolo", "Amorsolo, Fernando", "Amorsolo", "Fernando",
                    "user_amorsolo", "face_26.png", "100026",
                    "fernando.amorsolo@psa.gov.ph", "(02) 8461-0026",
                    plantilla_id_no="PSA-SS2-146-2015"),
        EmployeeData("emp_laurel", "Laurel, Jose P.", "Laurel", "Jose P.",
                    "user_laurel", "face_27.png", "100027",
                    "jose.laurel@psa.gov.ph", "(02) 8461-0027",
                    plantilla_id_no="PSA-ASTAT-90-2015"),
        EmployeeData("emp_ponce", "Ponce, Mariano", "Ponce", "Mariano",
                    "user_ponce", "face_24.png", "100024",
                    "mariano.ponce@psa.gov.ph", "(02) 8461-0024",
                    plantilla_id_no="PSA-SA-220-2015"),
        EmployeeData("emp_quezon", "Quezon, Manuel L.", "Quezon", "Manuel L.",
                    "user_quezon", "face_28.png", "100028",
                    "manuel.quezon@psa.gov.ph", "(02) 8461-0028",
                    plantilla_id_no="PSA-CSTATS-127-2015"),
        EmployeeData("emp_roxas", "Roxas, Manuel", "Roxas", "Manuel",
                    "user_roxas", "face_25.png", "100025",
                    "manuel.roxas@psa.gov.ph", "(02) 8461-0025",
                    plantilla_id_no="PSA-SVSTATS-128-2015"),
    ]
    
    return users, employees


def main():
    """Main entry point"""
    
    try:
        # Initialize client with proxy support from environment
        client = OdooMockDataClient.from_env(logger=log, use_proxy=True)
        client.login()
        
        # Get mock data
        users, employees = get_mock_data()
        
        # Create users
        console.print("\n[cyan]Creating users...[/cyan]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                     BarColumn(), console=console) as progress:
            task = progress.add_task(f"Creating {len(users)} users...", total=len(users))
            for user_data in users:
                client.create_user(user_data)
                progress.advance(task)
        
        # Create employees
        console.print("\n[cyan]Creating employees...[/cyan]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                     BarColumn(), console=console) as progress:
            task = progress.add_task(f"Creating {len(employees)} employees...", total=len(employees))
            for emp_data in employees:
                client.create_employee(emp_data)
                progress.advance(task)
        
        console.print("\n[green]✓ Mock data insertion complete![/green]")
        
    except Exception as e:
        log.critical(f"Fatal error: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise SystemExit(1)


if __name__ == "__main__":
    main()
