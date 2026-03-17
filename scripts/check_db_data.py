#!/usr/bin/env python3
"""
Database diagnostic script to check current data
"""
from database.models import Employee, User
from database.session_manager import get_db_session
import sys
sys.path.insert(0, '/Users/shashankrajput/Desktop/RadheFoundation')


def check_profile_photos():
    print("=== Checking Profile Photos in Database ===")

    db = get_db_session()
    try:
        employees = db.query(Employee).all()

        for emp in employees:
            print(f"\nEmployee ID: {emp.id}")
            print(f"  First Name: {emp.first_name}")
            print(f"  Last Name: {emp.last_name}")
            print(f"  profile_photo: {emp.profile_photo}")
            print(
                f"  profile_photo_data length: {len(emp.profile_photo_data) if emp.profile_photo_data else 0}")

        print("\n=== Checking User Profiles ===")
        users = db.query(User).all()

        for user in users:
            print(f"\nUser ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")

    finally:
        db.close()


if __name__ == "__main__":
    check_profile_photos()
