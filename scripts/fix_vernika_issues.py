#!/usr/bin/env python3
"""
Fix script for RadheFoundation issues
Run this to fix the identified issues
"""

import os
import sys


def fix_announcements_dropdown():
    """Fix on_change to on_select for Dropdown in announcements_screen.py"""
    file_path = "/Users/shashankrajput/Desktop/RadheFoundation/screens/announcements_screen.py"

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Fix on_change to on_select for Dropdown widgets
        if 'on_change=self._on_target_change' in content:
            content = content.replace(
                'on_change=self._on_target_change', 'on_select=self._on_target_change')
            with open(file_path, 'w') as f:
                f.write(content)
            print("✓ Fixed announcements_screen.py - Changed on_change to on_select")
        else:
            print("✓ announcements_screen.py already fixed or no change needed")

    except Exception as e:
        print(f"✗ Error fixing announcements_screen.py: {e}")


def verify_button_access_config():
    """Verify button access config is complete"""
    print("\n=== Verifying Button Access Config ===")

    # Key buttons that should be available
    critical_buttons = [
        "crm_leads_add", "crm_contacts_add", "crm_deals_add",
        "assets_add", "invoicing_items_add",
        "announcements_add"
    ]

    try:
        sys.path.insert(0, '/Users/shashankrajput/Desktop/RadheFoundation')
        from utils.screen_access import BUTTON_ACCESS_CONFIG, is_admin_user

        for btn in critical_buttons:
            if btn in BUTTON_ACCESS_CONFIG:
                config = BUTTON_ACCESS_CONFIG[btn]
                print(f"✓ {btn}: default_admin={config.get('default_admin')}")
            else:
                print(f"✗ Missing button config: {btn}")

        print("\n✓ Button access config verified")
    except Exception as e:
        print(f"✗ Error verifying config: {e}")


def check_database_users():
    """Check database users and roles"""
    print("\n=== Checking Database Users ===")

    try:
        sys.path.insert(0, '/Users/shashankrajput/Desktop/RadheFoundation')
        from database.session_manager import get_db_session
        from database.models import User

        db = get_db_session()
        users = db.query(User).all()

        for user in users:
            role_name = user.role.name if user.role else "No role"
            print(f"  User: {user.username}, Role: {role_name}, ID: {user.id}")

        db.close()
    except Exception as e:
        print(f"✗ Error checking users: {e}")


def main():
    print("Running RadheFoundation fixes...")
    print("=" * 50)

    fix_announcements_dropdown()
    verify_button_access_config()
    check_database_users()

    print("\n" + "=" * 50)
    print("Fixes completed!")
    print("\nNote: If buttons still don't work, check:")
    print("1. Login as admin user (role='admin')")
    print("2. Check console for any error messages")
    print("3. Verify database connection is working")


if __name__ == "__main__":
    main()
