"""
Migration script to add file_data columns for multi-device support
Adds binary storage for:
- Transaction attachments
- Billing request attachments  
- Employee profile photos
"""

from sqlalchemy import text
from database.connection import get_engine
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate_add_file_data_columns():
    """Add file_data columns to existing tables"""
    engine = get_engine()

    migrations = [
        # Add file_data to transaction_attachments
        """
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'transaction_attachments' 
                          AND column_name = 'file_data') THEN
                ALTER TABLE transaction_attachments ADD COLUMN file_data BYTEA;
            END IF;
        END $$;
        """,

        # Add file_data to billing_request_attachments
        """
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'billing_request_attachments' 
                          AND column_name = 'file_data') THEN
                ALTER TABLE billing_request_attachments ADD COLUMN file_data BYTEA;
            END IF;
        END $$;
        """,

        # Add profile_photo_data to employees
        """
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'employees' 
                          AND column_name = 'profile_photo_data') THEN
                ALTER TABLE employees ADD COLUMN profile_photo_data BYTEA;
            END IF;
        END $$;
        """
    ]

    with engine.connect() as conn:
        for i, migration in enumerate(migrations):
            try:
                conn.execute(text(migration))
                conn.commit()
                print(f"✅ Migration {i+1} executed successfully")
            except Exception as e:
                print(f"⚠️ Migration {i+1}: {str(e)}")
                # Continue with other migrations

    print("\n✅ All migrations completed!")


if __name__ == "__main__":
    print("Starting migration for file_data columns...")
    migrate_add_file_data_columns()
    print("\nDone!")
