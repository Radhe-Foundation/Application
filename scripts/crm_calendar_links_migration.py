#!/usr/bin/env python3
"""
CRM Calendar Enhancement Migration:
Add lead_id, contact_id, agenda, related_contract_id, related_invoice_id to calendar_events
"""

from database.models import Base
from database.connection import get_engine
from sqlalchemy import text, create_engine
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate():
    """Add new columns to calendar_events table"""
    engine = get_engine()
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendar_events');"))
        if not result.scalar():
            print(
                "❌ calendar_events table missing. Run: python scripts/final_crm_tables.py")
            return False

        # Add columns if they don't exist (safe migration)
        columns_to_add = [
            "lead_id INTEGER REFERENCES crm_leads(id)",
            "contact_id INTEGER REFERENCES crm_contacts(id)",
            "agenda TEXT",
            "related_contract_id INTEGER REFERENCES contracts(id)",
            "related_invoice_id INTEGER REFERENCES invoices(id)"
        ]

        for col in columns_to_add:
            col_name = col.split()[0]
            check_sql = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='calendar_events' AND column_name='{col_name}'
            """)
            if not conn.execute(check_sql).fetchone():
                add_sql = text(f"ALTER TABLE calendar_events ADD COLUMN {col}")
                conn.execute(add_sql)
                print(f"✅ Added {col_name}")
            else:
                print(f"ℹ️  {col_name} already exists")

        # Add indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_calendar_events_lead_id ON calendar_events(lead_id)",
            "CREATE INDEX IF NOT EXISTS idx_calendar_events_contact_id ON calendar_events(contact_id)",
            "CREATE INDEX IF NOT EXISTS idx_calendar_events_contract_id ON calendar_events(related_contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_calendar_events_invoice_id ON calendar_events(related_invoice_id)"
        ]

        for idx_sql in indexes:
            conn.execute(text(idx_sql))
            print(f"✅ Added index: {idx_sql.split()[2]}")

        conn.commit()
        print("\n🎉 Migration completed successfully!")
        print("Restart app to apply model changes.")
        return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
