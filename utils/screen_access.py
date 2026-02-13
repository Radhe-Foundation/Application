"""
Screen Access Management Utilities
Helper functions for managing employee screen access permissions
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


# Screen access configuration
SCREEN_ACCESS_CONFIG = {
    "profile": {
        "name": "My Profile",
        "icon": "PERSON",
        "description": "View and edit personal profile",
        "default_admin": True,
        "default_employee": True,  # Always enabled for employees
        "category": "personal"
    },
    "tasks": {
        "name": "My Tasks",
        "icon": "TASK",
        "description": "View and manage assigned tasks",
        "default_admin": True,
        "default_employee": False,
        "category": "work"
    },
    "leaves": {
        "name": "Time Off",
        "icon": "CALENDAR_MONTH",
        "description": "Request and manage leave requests",
        "default_admin": True,
        "default_employee": False,
        "category": "work"
    },
    "attendance": {
        "name": "Attendance",
        "icon": "ACCESS_TIME",
        "description": "View attendance records",
        "default_admin": True,
        "default_employee": False,
        "category": "work"
    },
    "documents": {
        "name": "Documents",
        "icon": "DESCRIPTION",
        "description": "Access and share documents",
        "default_admin": True,
        "default_employee": False,
        "category": "resources"
    },
    "chat": {
        "name": "Chat",
        "icon": "CHAT",
        "description": "Send and receive messages",
        "default_admin": True,
        "default_employee": False,
        "category": "communication"
    }
}


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('vernika.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_user_screen_access(user_id: int) -> Dict[str, bool]:
    """
    Get all screen access settings for a user

    Args:
        user_id: The user's ID

    Returns:
        Dict with screen_key -> is_enabled mapping
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user role
    cursor.execute("SELECT role_id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    role_name = "employee"
    if user:
        cursor.execute("SELECT name FROM roles WHERE id = ?",
                       (user['role_id'],))
        role = cursor.fetchone()
        if role:
            role_name = role['name'].lower()

    # Get user's screen access settings
    cursor.execute(
        "SELECT screen_key, is_enabled FROM screen_access WHERE user_id = ?",
        (user_id,)
    )
    access_records = cursor.fetchall()
    conn.close()

    # Build access dict - start with defaults
    access_dict = {}
    for screen_key, config in SCREEN_ACCESS_CONFIG.items():
        if role_name == 'admin':
            access_dict[screen_key] = config['default_admin']
        else:
            access_dict[screen_key] = config['default_employee']

    # Override with database settings
    for record in access_records:
        access_dict[record['screen_key']] = bool(record['is_enabled'])

    return access_dict


def check_screen_access(user_id: int, screen_key: str) -> bool:
    """
    Check if user has access to a specific screen

    Args:
        user_id: The user's ID
        screen_key: The screen identifier

    Returns:
        True if access is allowed, False otherwise
    """
    if not screen_key:
        return False

    access_dict = get_user_screen_access(user_id)
    return access_dict.get(screen_key, False)


def set_screen_access(
    user_id: int,
    screen_key: str,
    is_enabled: bool,
    granted_by: Optional[int] = None
) -> bool:
    """
    Set screen access for a user

    Args:
        user_id: The user's ID
        screen_key: The screen identifier
        is_enabled: Whether access should be enabled
        granted_by: ID of admin granting access

    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if record exists
        cursor.execute(
            "SELECT id FROM screen_access WHERE user_id = ? AND screen_key = ?",
            (user_id, screen_key)
        )
        existing = cursor.fetchone()

        now = datetime.now().isoformat()

        if existing:
            # Update existing record
            cursor.execute("""
                UPDATE screen_access
                SET is_enabled = ?, granted_by = ?, granted_at = ?, updated_at = ?
                WHERE id = ?
            """, (1 if is_enabled else 0, granted_by, now, now, existing['id']))
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO screen_access (user_id, screen_key, is_enabled, granted_by, granted_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, screen_key, 1 if is_enabled else 0, granted_by, now, now, now))

        conn.commit()
        return True

    except Exception as e:
        print(f"Error setting screen access: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def bulk_set_screen_access(
    user_id: int,
    access_dict: Dict[str, bool],
    granted_by: Optional[int] = None
) -> bool:
    """
    Set multiple screen access permissions for a user

    Args:
        user_id: The user's ID
        access_dict: Dict of screen_key -> is_enabled
        granted_by: ID of admin granting access

    Returns:
        True if all successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now().isoformat()

        for screen_key, is_enabled in access_dict.items():
            # Check if record exists
            cursor.execute(
                "SELECT id FROM screen_access WHERE user_id = ? AND screen_key = ?",
                (user_id, screen_key)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE screen_access
                    SET is_enabled = ?, granted_by = ?, granted_at = ?, updated_at = ?
                    WHERE id = ?
                """, (1 if is_enabled else 0, granted_by, now, now, existing['id']))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO screen_access (user_id, screen_key, is_enabled, granted_by, granted_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, screen_key, 1 if is_enabled else 0, granted_by, now, now, now))

        conn.commit()
        return True

    except Exception as e:
        print(f"Error bulk setting screen access: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_all_employees_for_access_management() -> List[Dict]:
    """
    Get all employees for the access management interface

    Returns:
        List of dicts with user_id, username, email, role, screen_access summary
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.username, u.email, r.name as role_name,
               e.first_name, e.last_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        LEFT JOIN employees e ON u.id = e.user_id
        WHERE r.name != 'admin'
        ORDER BY u.id
    """)

    users = cursor.fetchall()
    conn.close()

    result = []
    for user in users:
        access = get_user_screen_access(user['id'])
        enabled_count = sum(1 for v in access.values() if v)

        result.append({
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role_name'],
            'full_name': f"{user['first_name'] or ''} {user['last_name'] or ''}".strip(),
            'screen_access': access,
            'enabled_count': enabled_count,
            'total_screens': len(access)
        })

    return result


def reset_to_defaults(user_id: int) -> bool:
    """
    Reset user's screen access to default based on role

    Args:
        user_id: The user's ID

    Returns:
        True if successful
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get user role
        cursor.execute("SELECT role_id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        role_name = "employee"
        if user:
            cursor.execute("SELECT name FROM roles WHERE id = ?",
                           (user['role_id'],))
            role = cursor.fetchone()
            if role:
                role_name = role['name'].lower()

        # Delete existing records
        cursor.execute(
            "DELETE FROM screen_access WHERE user_id = ?", (user_id,))

        conn.commit()
        return True

    except Exception as e:
        print(f"Error resetting screen access: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
