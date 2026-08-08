"""
Re-export JSON2OdooClient from modern odoo_json2 package for backward compatibility.
"""

from odoo_json2 import JSON2Client as JSON2OdooClient, OdooJSON2Error

__all__ = ["JSON2OdooClient", "OdooJSON2Error"]
