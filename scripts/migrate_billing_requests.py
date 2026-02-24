#!/usr/bin/env python3
"""
Migration script for PostgreSQL to add/update billing request tables
Run: cd /Users/shashankrajput/Desktop/Vernika && python3 scripts/migrate_billing_requests.py
"""

from database.connection import get_engine
from sqlalchemy import text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate_billing_requests_postgres():
    """Create/update billing request tables in PostgreSQL"""
    engine = get_engine()

    print("=" * 60)
    print("MIGRATING BILLING REQUEST TABLES (PostgreSQL)")
    print("=" * 60)

    with engine.connect() as conn:
        # Check if billing_requests table exists
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'billing_requests'
        """))

        if not result.fetchone():
            print("Creating billing_requests table...")
            conn.execute(text("""
                CREATE TABLE billing_requests (
                    id SERIAL PRIMARY KEY,
                    request_number VARCHAR(50) UNIQUE NOT NULL,
                    request_type VARCHAR(50) NOT NULL DEFAULT 'bill_reimbursement',
                    employee_id INTEGER NOT NULL REFERENCES employees(id),
                    bill_description TEXT NOT NULL,
                    bill_amount DOUBLE PRECISION NOT NULL,
                    bill_date DATE NOT NULL,
                    bill_category VARCHAR(100),
                    payment_mode VARCHAR(50),
                    payment_details TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    reviewed_by_id INTEGER REFERENCES users(id),
                    reviewed_at TIMESTAMP,
                    review_notes TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ billing_requests table created!")
        else:
            print("✅ billing_requests table already exists")

            # Check and add missing columns
            print("Checking for missing columns...")

            # Check for required columns
            columns_result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'billing_requests'
            """))
            existing_columns = [row[0] for row in columns_result]
            print(f"  Existing columns: {existing_columns}")

            # Add missing columns
            column_additions = [
                ("bill_category", "VARCHAR(100)"),
                ("payment_mode", "VARCHAR(50)"),
                ("payment_details", "TEXT"),
                ("status", "VARCHAR(50) DEFAULT 'pending'"),
                ("reviewed_by_id", "INTEGER REFERENCES users(id)"),
                ("reviewed_at", "TIMESTAMP"),
                ("review_notes", "TEXT"),
                ("notes", "TEXT"),
            ]

            for col_name, col_type in column_additions:
                if col_name not in existing_columns:
                    print(f"  Adding column: {col_name}")
                    try:
                        conn.execute(text(f"""
                            ALTER TABLE billing_requests ADD COLUMN {col_name} {col_type}
                        """))
                        conn.commit()
                        print(f"    ✅ Added {col_name}")
                    except Exception as e:
                        print(f"    ⚠️ Error adding {col_name}: {e}")

        # Check if billing_request_attachments table exists
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'billing_request_attachments'
        """))

        if not result.fetchone():
            print("Creating billing_request_attachments table...")
            conn.execute(text("""
                CREATE TABLE billing_request_attachments (
                    id SERIAL PRIMARY KEY,
                    billing_request_id INTEGER NOT NULL REFERENCES billing_requests(id) ON DELETE CASCADE,
                    file_name VARCHAR(200) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type VARCHAR(50),
                    attachment_type VARCHAR(50) DEFAULT 'receipt',
                    description VARCHAR(200),
                    uploaded_by_id INTEGER NOT NULL REFERENCES users(id),
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ billing_request_attachments table created!")
        else:
            print("✅ billing_request_attachments table already exists")

            # Check for required columns
            columns_result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'billing_request_attachments'
            """))
            existing_columns = [row[0] for row in columns_result]
            print(f"  Existing columns: {existing_columns}")

            # Add missing columns
            column_additions = [
                ("file_type", "VARCHAR(50)"),
                ("attachment_type", "VARCHAR(50) DEFAULT 'receipt'"),
                ("description", "VARCHAR(200)"),
            ]

            for col_name, col_type in column_additions:
                if col_name not in existing_columns:
                    print(f"  Adding column: {col_name}")
                    try:
                        conn.execute(text(f"""
                            ALTER TABLE billing_request_attachments ADD COLUMN {col_name} {col_type}
                        """))
                        conn.commit()
                        print(f"    ✅ Added {col_name}")
                    except Exception as e:
                        print(f"    ⚠️ Error adding {col_name}: {e}")

        # Check if transaction_attachments table exists
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'transaction_attachments'
        """))

        if not result.fetchone():
            print("Creating transaction_attachments table...")
            conn.execute(text("""
                CREATE TABLE transaction_attachments (
                    id SERIAL PRIMARY KEY,
                    transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
                    file_path VARCHAR(500) NOT NULL,
                    file_name VARCHAR(200) NOT NULL,
                    file_size INTEGER NOT NULL,
                    uploaded_by_id INTEGER REFERENCES users(id),
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ transaction_attachments table created!")
        else:
            print("✅ transaction_attachments table already exists")

        # Verify all tables exist
        print("\nVerifying tables...")
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('billing_requests', 'billing_request_attachments', 'transaction_attachments')
            ORDER BY table_name
        """))

        for row in result:
            print(f"  ✅ {row[0]}")

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = migrate_billing_requests_postgres()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
