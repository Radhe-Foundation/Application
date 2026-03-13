#!/usr/bin/env python3
# Fix CRM schema - add missing columns

from sqlalchemy import text
from database.connection import get_engine
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


print("Fixing CRM schema...")

engine = get_engine()

with engine.begin() as conn:
    # crm_leads missing columns
    lead_cols = [
        ('position', 'VARCHAR(100)'),
        ('notes', 'TEXT'),
        ('assigned_to_id', 'INTEGER REFERENCES users(id)'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ]
    for col, typ in lead_cols:
        conn.execute(
            text(f"ALTER TABLE IF EXISTS crm_leads ADD COLUMN IF NOT EXISTS {col} {typ}"))
        print(f"✅ crm_leads.{col}")

    # crm_contacts
    contact_cols = [
        ('position', 'VARCHAR(100)'),
        ('address', 'TEXT'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ]
    for col, typ in contact_cols:
        conn.execute(
            text(f"ALTER TABLE IF EXISTS crm_contacts ADD COLUMN IF NOT EXISTS {col} {typ}"))
        print(f"✅ crm_contacts.{col}")

    # warehouses
    wh_cols = [
        ('address', 'TEXT'),
        ('city', 'VARCHAR(100)'),
        ('state', 'VARCHAR(100)'),
        ('pincode', 'VARCHAR(20)'),
    ]
    for col, typ in wh_cols:
        conn.execute(
            text(f"ALTER TABLE IF EXISTS warehouses ADD COLUMN IF NOT EXISTS {col} {typ}"))
        print(f"✅ warehouses.{col}")

print("✅ CRM schema fixed!")
print("Restart: python3 web_main.py")
