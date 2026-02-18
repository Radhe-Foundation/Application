"""
Database Migration - Add New Tables
Run this script to add new tables for the enhanced features
"""

import database.models
from database.connection import get_engine, Base
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database connection and models properly


def run_migration():
    """Create all new tables"""
    print("Starting migration...")

    try:
        engine = get_engine()

        # Import all new models to register them with Base.metadata
        from database.models import (
            OrgHierarchy, TeamMember, ProjectMember,
            InventoryCategory, Product, ProductImage, InventoryTransaction,
            Transaction, TransactionAttachment,
            DataSheet, DataSheetColumn, DataSheetRow
        )

        # Create all tables
        print("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        print("All tables created/verified")

        # Verify tables
        import sqlite3
        db_path = "vernika.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [t[0] for t in cursor.fetchall()]
            conn.close()

            print(f"Total tables in database: {len(tables)}")

            # Check for new tables
            new_tables = ['org_hierarchy', 'team_members', 'project_members',
                          'inventory_categories', 'products', 'product_images',
                          'inventory_transactions', 'transactions', 'transaction_attachments',
                          'data_sheets', 'data_sheet_columns', 'data_sheet_rows']

            print("\nNew feature tables:")
            for t in new_tables:
                if t in tables:
                    print(f"  [OK] {t}")
                else:
                    print(f"  [MISSING] {t}")

        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
