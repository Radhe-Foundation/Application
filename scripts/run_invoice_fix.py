#!/usr/bin/env python3
"""
Run invoice schema fix through main app context to use existing DB connection.
"""

from sqlalchemy import text
from database.connection import get_engine
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


print("🔧 Running invoice schema fix via app engine...")

engine = get_engine()

with engine.connect() as conn:
    # Check existing columns
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices'"))
    cols = [row[0] for row in result]
    print("Current invoice columns:", ', '.join(sorted(cols)))

    # Add missing columns if not exist
    missing_cols = []
    if 'customer_name' not in cols:
        missing_cols.append("customer_name VARCHAR(200)")
    if 'customer_email' not in cols:
        missing_cols.append("customer_email VARCHAR(100)")
    if 'customer_address' not in cols:
        missing_cols.append("customer_address TEXT")
    if 'due_date' not in cols:
        missing_cols.append("due_date DATE")
    if 'subtotal' not in cols:
        missing_cols.append("subtotal FLOAT DEFAULT 0")
    if 'tax_amount' not in cols:
        missing_cols.append("tax_amount FLOAT DEFAULT 0")
    if 'total_amount' not in cols:
        missing_cols.append("total_amount FLOAT DEFAULT 0")
    if 'status' not in cols:
        missing_cols.append("status VARCHAR(50) DEFAULT 'draft'")
    if 'notes' not in cols:
        missing_cols.append("notes TEXT")
    if 'contract_id' not in cols:
        missing_cols.append("contract_id INTEGER")

    if missing_cols:
        print("Adding missing columns...")
        for col in missing_cols:
            col_name = col.split()[0]
            conn.execute(
                text(f"ALTER TABLE invoices ADD COLUMN IF NOT EXISTS {col}"))
            print(f"✅ Added {col_name}")
    else:
        print("✅ All required columns exist")

    print("🎉 Invoice schema fixed! Ready to test app.")
