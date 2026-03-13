#!/usr/bin/env python3
# Fixed invoice schema fix - CRM customer_name error
from sqlalchemy import text
from database.connection import get_engine
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


print('🔧 Fixing invoices table for CRM...')

engine = get_engine()

with engine.begin() as conn:
    # Add missing model columns
    adds = [
        'ALTER TABLE invoices ADD COLUMN IF NOT EXISTS customer_name VARCHAR(200)',
        'ALTER TABLE invoices ADD COLUMN IF NOT EXISTS customer_email VARCHAR(100)',
        'ALTER TABLE invoices ADD COLUMN IF NOT EXISTS customer_address TEXT',
    ]

    for sql in adds:
        conn.execute(text(sql))
        col = sql.split()[4].split('(')[0]
        print(f'✅ Added/Verified: {col}')

    # Verify
    cols = [r[0] for r in conn.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices' ORDER BY ordinal_position"))]
    # Last 10 to confirm adds
    print('Invoices columns:', ', '.join(cols[-10:]))
    print('🎉 CRM Invoice schema fixed! Run `python3 main.py` to test.')

print('Done!')
