"""
Migration script to add suppliers table
Run this script to create the suppliers table in the database
"""

from database.models import Supplier
from sqlalchemy import create_engine
from config import DATABASE_URL


def migrate_suppliers():
    """Create suppliers table"""
    print("Creating suppliers table...")

    # Create engine from config
    engine = create_engine(DATABASE_URL)

    # Create table
    Supplier.__table__.create(engine, checkfirst=True)

    print("✅ Suppliers table created successfully!")
    print("\nYou can now use the Suppliers feature in Inventory Management.")


if __name__ == "__main__":
    migrate_suppliers()
