#!/usr/bin/env python3
# Complete CRM Schema Fix - Add ALL missing columns

from sqlalchemy import text
from database.connection import get_engine
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('🔧 Complete CRM Schema Fix...')

engine = get_engine()

with engine.begin() as conn:
    # crm_leads - ALL columns from Lead model
    lead_cols = [
        ('value', 'FLOAT DEFAULT 0'),
        ('status', 'VARCHAR(50) DEFAULT \"new\"'),
        ('source', 'VARCHAR(50) DEFAULT \"website\"'),
    ]
    for col, typ in lead_cols:
        conn.execute(
            text(f"ALTER TABLE IF EXISTS crm_leads ADD COLUMN IF NOT EXISTS {col} {typ}"))
        print(f'✅ crm_leads.{col}')

    # assets - ALL columns from Asset model
    asset_cols = [
        ('current_value', 'FLOAT DEFAULT 0'),
        ('asset_code', 'VARCHAR(50)'),
        ('category', 'VARCHAR(50) DEFAULT \"other\"'),
        ('description', 'TEXT'),
        ('purchase_date', 'DATE'),
        ('status', 'VARCHAR(50) DEFAULT \"available\"'),
        ('assigned_to_id', 'INTEGER REFERENCES employees(id)'),
        ('warehouse_id', 'INTEGER REFERENCES warehouses(id)'),
        ('serial_number', 'VARCHAR(100)'),
        ('warranty_expiry', 'DATE'),
        ('notes', 'TEXT'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ]
    for col, typ in asset_cols:
        conn.execute(
            text(f"ALTER TABLE IF EXISTS assets ADD COLUMN IF NOT EXISTS {col} {typ}"))
        print(f'✅ assets.{col}')

    # Create tables if missing
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS crm_contacts (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100),
            company VARCHAR(200),
            email VARCHAR(100),
            phone VARCHAR(20),
            position VARCHAR(100),
            address TEXT,
            notes TEXT,
            is_customer BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    print('✅ crm_contacts table')

print('🎉 Complete CRM schema fixed!')
print('Restart app: python3 main.py')
