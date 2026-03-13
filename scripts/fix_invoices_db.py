#!/usr/bin/env python3
# Fix invoices table - Run via main app context

from database.models import Invoice
from database.connection import get_engine
from sqlalchemy import text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))  # Fix for scripts dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


print('🔧 Checking/Fixing invoices table...')

engine = get_engine()

with engine.connect() as conn:
    conn.execute(text("BEGIN;"))

    # Check columns
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'invoices' AND column_name IN
        ('customer_name', 'customer_email', 'customer_address', 'due_date', 'subtotal',
         'tax_amount', 'total_amount', 'status', 'notes', 'contract_id');
    """))
    cols = [row[0] for row in result]
    print('Existing columns:', cols)

    missing = ['customer_name', 'customer_email', 'customer_address', 'due_date', 'subtotal',
               'tax_amount', 'total_amount', 'status', 'notes', 'contract_id']
    missing = [c for c in missing if c not in cols]

    if missing:
        print('Adding missing columns:', missing)
        adds = []
        if 'customer_name' in missing:
            adds.append(
                'ALTER TABLE invoices ADD COLUMN customer_name VARCHAR(200);')
        if 'customer_email' in missing:
            adds.append(
                'ALTER TABLE invoices ADD COLUMN customer_email VARCHAR(100);')
        if 'customer_address' in missing:
            adds.append(
                'ALTER TABLE invoices ADD COLUMN customer_address TEXT;')
        if 'due_date' in missing:
            adds.append('ALTER TABLE invoices ADD COLUMN due_date DATE;')
        if 'subtotal' in missing:
            adds.append(
                'ALTER TABLE invoices ADD COLUMN subtotal FLOAT DEFAULT 0;')
        if 'tax_amount' in missing:
            adds.append(
                'ALTER TABLE invoices ADD COLUMN tax_amount FLOAT DEFAULT 0;')
        if 'total_amount' in missing:
            adds.append(
                'ALTER TABLE invoices ADD COLUMN total_amount FLOAT DEFAULT 0;')
        if 'status' in missing:
            adds.append(
                "ALTER TABLE invoices ADD COLUMN status VARCHAR(50) DEFAULT 'draft';")
        if 'notes' in missing:
            adds.append('ALTER TABLE invoices ADD COLUMN notes TEXT;')
        if 'contract_id' in missing:
            adds.append(
                'ALTER TABLE invoices ADD COLUMN contract_id INTEGER REFERENCES contracts(id);')

        for sql in adds:
            conn.execute(text(sql))
            print(f'✅ {sql.split()[3]}')
    else:
        print('✅ All columns exist')

    conn.execute(text("COMMIT;"))
    print('🎉 Invoices table fixed!')
    print('Test: cd .. && python3 main.py')
