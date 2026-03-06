#!/usr/bin/env python3
"""
Script to update admin credentials in the cloud database
"""

from database.models import User
from database.connection import get_db_session
from dotenv import load_dotenv
import os
import sys
import bcrypt
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()


def update_admin_credentials():
    """Update admin username and password in the cloud database"""

    # New credentials
    new_username = "Vernika"
    new_password = "vernika8268"
    admin_email = "admin@vernika.com"

    # Generate bcrypt hash for the new password
    password_hash = bcrypt.hashpw(
        new_password.encode(), bcrypt.gensalt()).decode()

    print(f"New username: {new_username}")
    print(f"New password: {new_password}")
    print(f"Password hash: {password_hash}")

    # Connect to database and update
    session = get_db_session()
    try:
        # Find the admin user
        admin_user = session.query(User).filter(
            (User.username == "admin") | (User.email == admin_email)
        ).first()

        if admin_user:
            print(
                f"\nFound admin user: {admin_user.username} ({admin_user.email})")
            print(f"Current user_id: {admin_user.id}")

            # Update username and password
            admin_user.username = new_username
            admin_user.password_hash = password_hash

            session.commit()
            print("\n✅ Admin credentials updated successfully!")
            print(f"   New login: {new_username} / {new_password}")
        else:
            print("\n❌ Admin user not found in database!")
            print("   The database may not be initialized yet.")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error updating admin credentials: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Updating Admin Credentials")
    print("=" * 50)
    update_admin_credentials()
