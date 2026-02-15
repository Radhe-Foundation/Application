"""
Migration script to create button_access table in PostgreSQL
"""

from sqlalchemy import create_engine, text
from config import DATABASE_URL
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_button_access_table():
    """Create the button_access table in the database"""

    print("Creating button_access table...")

    # Connect to the database
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Create the button_access table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS button_access (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                button_key VARCHAR(100) NOT NULL,
                is_enabled BOOLEAN DEFAULT TRUE,
                granted_by INTEGER REFERENCES users(id),
                granted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, button_key)
            );
            """
            conn.execute(text(create_table_sql))

            # Create index for faster queries
            create_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_button_access_user_id 
            ON button_access(user_id);
            """
            conn.execute(text(create_index_sql))

            conn.commit()
            print("✓ button_access table created successfully!")

    except Exception as e:
        print(f"Error creating button_access table: {e}")
        return False
    finally:
        engine.dispose()

    return True


if __name__ == "__main__":
    success = create_button_access_table()
    if success:
        print("\n✓ Migration completed successfully!")
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
