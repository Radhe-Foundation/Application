#!/usr/bin/env python3
# Fix invoices table schema - Add missing CRM columns

from database.session_manager import get_session
from database.connection import get_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


print('🔧 Fixing invoices table schema...')

engine = get_engine()

missing_columns = [
    'customer_name VARCHAR(200)',
    'customer_email VARCHAR(100)',
    'customer_address TEXT',
    'due_date DATE',
    'subtotal FLOAT DEFAULT 0',
    'tax_amount FLOAT DEFAULT 0',
    'total_amount FLOAT DEFAULT 0',
    'status VARCHAR(50) DEFAULT \"draft\"',
    'notes TEXT',
    'contract_id INTEGER REFERENCES contracts(id)',
    'created_by_id INTEGER REFERENCES users(id)',
    'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
]

try:
    with engine.begin() as conn:
        # Check current columns
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'invoices';
        """))
        existing_cols = {row[0] for row in result}
        print(f'Current columns: {sorted(existing_cols)}')

        # Add missing columns
        for col_def in missing_columns:
            col_name = col_def.split()[0]
            if col_name not in existing_cols:
                conn.execute(
                    text(f"ALTER TABLE invoices ADD COLUMN IF NOT EXISTS {col_def}"))
                print(f'✅ Added: {col_def}')
            else:
                print(f'⏭️  Exists: {col_name}')

        conn.commit()
        print('🎉 Invoices schema fixed!')
        print('Restart app: cd .. && python3 main.py')

except SQLAlchemyError as e:
    print(f'❌ DB Error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
