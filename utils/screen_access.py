"""
Vernika HRA - Screen Access Management
PostgreSQL/SQLAlchemy based screen access control for employees
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database.session_manager import get_db_session, get_session
from database.models import ScreenAccess, User, Employee, Role


# Screen access configuration (for display purposes only, not data)
# This configuration automatically includes all features from admin screen tabs
SCREEN_ACCESS_CONFIG = {
    # Personal screens (always available)
    "profile": {
        "name": "My Profile",
        "icon": "PERSON",
        "description": "View and edit personal profile",
        "default_admin": True,
        "default_employee": True,
        "category": "personal",
        "admin_tab_index": None
    },
    # Work-related screens
    "dashboard": {
        "name": "Dashboard",
        "icon": "DASHBOARD",
        "description": "View dashboard overview and stats",
        "default_admin": True,
        "default_employee": True,
        "category": "work",
        "admin_tab_index": 0
    },
    "tasks": {
        "name": "My Tasks",
        "icon": "TASK",
        "description": "View and manage assigned tasks",
        "default_admin": True,
        "default_employee": False,
        "category": "work",
        "admin_tab_index": 3
    },
    "todo": {
        "name": "Todo List",
        "icon": "LIST_ALT",
        "description": "Manage personal todo lists",
        "default_admin": True,
        "default_employee": False,
        "category": "work",
        "admin_tab_index": 4
    },
    "leaves": {
        "name": "Time Off",
        "icon": "CALENDAR_MONTH",
        "description": "Request and manage leave requests",
        "default_admin": True,
        "default_employee": False,
        "category": "work",
        "admin_tab_index": 7
    },
    "attendance": {
        "name": "Attendance",
        "icon": "ACCESS_TIME",
        "description": "View attendance records",
        "default_admin": True,
        "default_employee": False,
        "category": "work",
        "admin_tab_index": 6
    },
    # HR Management screens
    "employees": {
        "name": "Employees",
        "icon": "BADGE",
        "description": "Manage employee records",
        "default_admin": True,
        "default_employee": False,
        "category": "hr",
        "admin_tab_index": 8
    },
    "departments": {
        "name": "Departments",
        "icon": "BUSINESS",
        "description": "Manage departments",
        "default_admin": True,
        "default_employee": False,
        "category": "hr",
        "admin_tab_index": 5
    },
    "positions": {
        "name": "Positions",
        "icon": "WORK",
        "description": "Manage job positions",
        "default_admin": True,
        "default_employee": False,
        "category": "hr",
        "admin_tab_index": 9
    },
    # Communication screens
    "chat": {
        "name": "Chat",
        "icon": "CHAT",
        "description": "Send and receive messages",
        "default_admin": True,
        "default_employee": False,
        "category": "communication",
        "admin_tab_index": 1
    },
    "mail": {
        "name": "Mail",
        "icon": "EMAIL",
        "description": "Internal email system",
        "default_admin": True,
        "default_employee": False,
        "category": "communication",
        "admin_tab_index": 2
    },
    "announcements": {
        "name": "Announcements",
        "icon": "CAMPAIGN",
        "description": "Company news and updates",
        "default_admin": True,
        "default_employee": False,
        "category": "communication",
        "admin_tab_index": 10
    },
    # Resources screens
    "documents": {
        "name": "Documents",
        "icon": "DESCRIPTION",
        "description": "Access and share documents",
        "default_admin": True,
        "default_employee": False,
        "category": "resources",
        "admin_tab_index": 11
    },
    # Admin & Reports screens
    "performance": {
        "name": "Performance",
        "icon": "TRENDING_UP",
        "description": "Performance reviews and analytics",
        "default_admin": True,
        "default_employee": False,
        "category": "admin",
        "admin_tab_index": 12
    },
    "reports": {
        "name": "Reports",
        "icon": "ASSESSMENT",
        "description": "Reports and analytics",
        "default_admin": True,
        "default_employee": False,
        "category": "admin",
        "admin_tab_index": 13
    },
    "settings": {
        "name": "Settings",
        "icon": "SETTINGS",
        "description": "System settings",
        "default_admin": True,
        "default_employee": False,
        "category": "admin",
        "admin_tab_index": 15
    },
    "etl": {
        "name": "ETL",
        "icon": "STORAGE",
        "description": "Data import/export",
        "default_admin": True,
        "default_employee": False,
        "category": "admin",
        "admin_tab_index": 17
    },
    "audit": {
        "name": "Audit Logs",
        "icon": "HISTORY",
        "description": "Activity logs",
        "default_admin": True,
        "default_employee": False,
        "category": "admin",
        "admin_tab_index": 16
    },
    # Business Screens
    "data_entry": {
        "name": "Data Entry",
        "icon": "TABLE_ROWS",
        "description": "Spreadsheet and data management",
        "default_admin": True,
        "default_employee": False,
        "category": "business",
        "admin_tab_index": 22
    },
    "inventory": {
        "name": "Inventory",
        "icon": "INVENTORY",
        "description": "Inventory and stock management",
        "default_admin": True,
        "default_employee": False,
        "category": "business",
        "admin_tab_index": 23
    },
    "transactions": {
        "name": "Transactions",
        "icon": "PAYMENT",
        "description": "Financial transactions and payments",
        "default_admin": True,
        "default_employee": False,
        "category": "business",
        "admin_tab_index": 24
    },
    "crm": {
        "name": "CRM",
        "icon": "PEOPLE",
        "description": "Customer relationship management",
        "default_admin": True,
        "default_employee": False,
        "category": "business",
        "admin_tab_index": 25
    },
    "invoicing": {
        "name": "Invoicing",
        "icon": "RECEIPT_LONG",
        "description": "Invoice generation and billing",
        "default_admin": True,
        "default_employee": False,
        "category": "business",
        "admin_tab_index": 26
    },
    "assets": {
        "name": "Assets",
        "icon": "INVENTORY_2",
        "description": "Company asset management",
        "default_admin": True,
        "default_employee": False,
        "category": "business",
        "admin_tab_index": 27
    },
    "time_tracking": {
        "name": "Time Track",
        "icon": "TIMER",
        "description": "Employee time tracking",
        "default_admin": True,
        "default_employee": False,
        "category": "business",
        "admin_tab_index": 28
    },
    "admin_panel": {
        "name": "Admin Panel",
        "icon": "ADMIN_PANEL_SETTINGS",
        "description": "Full admin access",
        "default_admin": True,
        "default_employee": False,
        "category": "admin",
        "admin_tab_index": None
    },
}


# Button-level access configuration
# Each button/feature can be enabled/disabled for employees
BUTTON_ACCESS_CONFIG = {
    # Dashboard buttons
    "dashboard_view": {
        "name": "View Dashboard",
        "screen": "dashboard",
        "description": "View dashboard overview",
        "default_admin": True,
        "default_employee": True
    },
    "dashboard_stats": {
        "name": "View Statistics",
        "screen": "dashboard",
        "description": "View dashboard statistics",
        "default_admin": True,
        "default_employee": False
    },
    # Employee management buttons
    "employees_add": {
        "name": "Add Employee",
        "screen": "employees",
        "description": "Add new employee",
        "default_admin": True,
        "default_employee": False
    },
    "employees_edit": {
        "name": "Edit Employee",
        "screen": "employees",
        "description": "Edit employee records",
        "default_admin": True,
        "default_employee": False
    },
    "employees_delete": {
        "name": "Delete Employee",
        "screen": "employees",
        "description": "Delete employee records",
        "default_admin": True,
        "default_employee": False
    },
    "employees_view": {
        "name": "View Employees",
        "screen": "employees",
        "description": "View employee list",
        "default_admin": True,
        "default_employee": False
    },
    # Department buttons
    "departments_add": {
        "name": "Add Department",
        "screen": "departments",
        "description": "Add new department",
        "default_admin": True,
        "default_employee": False
    },
    "departments_edit": {
        "name": "Edit Department",
        "screen": "departments",
        "description": "Edit department",
        "default_admin": True,
        "default_employee": False
    },
    # Position buttons
    "positions_add": {
        "name": "Add Position",
        "screen": "positions",
        "description": "Add new position",
        "default_admin": True,
        "default_employee": False
    },
    # Leave management buttons
    "leaves_apply": {
        "name": "Apply Leave",
        "screen": "leaves",
        "description": "Apply for leave",
        "default_admin": True,
        "default_employee": True
    },
    "leaves_approve": {
        "name": "Approve Leave",
        "screen": "leaves",
        "description": "Approve/reject leave requests",
        "default_admin": True,
        "default_employee": False
    },
    # Attendance buttons
    "attendance_mark": {
        "name": "Mark Attendance",
        "screen": "attendance",
        "description": "Mark daily attendance",
        "default_admin": True,
        "default_employee": True
    },
    "attendance_view": {
        "name": "View Attendance",
        "screen": "attendance",
        "description": "View attendance records",
        "default_admin": True,
        "default_employee": False
    },
    # Task buttons
    "tasks_add": {
        "name": "Add Task",
        "screen": "tasks",
        "description": "Create new task",
        "default_admin": True,
        "default_employee": False
    },
    "tasks_manage": {
        "name": "Manage Tasks",
        "screen": "tasks",
        "description": "Manage all tasks",
        "default_admin": True,
        "default_employee": False
    },
    # Chat buttons
    "chat_send": {
        "name": "Send Messages",
        "screen": "chat",
        "description": "Send chat messages",
        "default_admin": True,
        "default_employee": False
    },
    # Document buttons
    "documents_upload": {
        "name": "Upload Document",
        "screen": "documents",
        "description": "Upload documents",
        "default_admin": True,
        "default_employee": False
    },
    "documents_download": {
        "name": "Download Document",
        "screen": "documents",
        "description": "Download documents",
        "default_admin": True,
        "default_employee": False
    },
    # Reports buttons
    "reports_view": {
        "name": "View Reports",
        "screen": "reports",
        "description": "View and generate reports",
        "default_admin": True,
        "default_employee": False
    },
    "reports_export": {
        "name": "Export Reports",
        "screen": "reports",
        "description": "Export reports to file",
        "default_admin": True,
        "default_employee": False
    },
    # Settings buttons
    "settings_manage": {
        "name": "Manage Settings",
        "screen": "settings",
        "description": "Manage system settings",
        "default_admin": True,
        "default_employee": False
    },
    # ETL buttons
    "etl_import": {
        "name": "Import Data",
        "screen": "etl",
        "description": "Import data from Excel",
        "default_admin": True,
        "default_employee": False
    },
    "etl_export": {
        "name": "Export Data",
        "screen": "etl",
        "description": "Export data to Excel",
        "default_admin": True,
        "default_employee": False
    },
    # Access management (admin only)
    "access_manage": {
        "name": "Manage Access",
        "screen": "access",
        "description": "Manage user access permissions",
        "default_admin": True,
        "default_employee": False
    },
    # Performance buttons
    "performance_view": {
        "name": "View Performance",
        "screen": "performance",
        "description": "View performance reviews",
        "default_admin": True,
        "default_employee": False
    },
    "performance_add": {
        "name": "Add Review",
        "screen": "performance",
        "description": "Add performance review",
        "default_admin": True,
        "default_employee": False
    },
    # CRM buttons
    "crm_leads_add": {
        "name": "Add Lead",
        "screen": "crm",
        "description": "Add new CRM lead",
        "default_admin": True,
        "default_employee": False
    },
    "crm_leads_edit": {
        "name": "Edit Lead",
        "screen": "crm",
        "description": "Edit CRM lead",
        "default_admin": True,
        "default_employee": False
    },
    "crm_leads_delete": {
        "name": "Delete Lead",
        "screen": "crm",
        "description": "Delete CRM lead",
        "default_admin": True,
        "default_employee": False
    },
    "crm_contacts_add": {
        "name": "Add Contact",
        "screen": "crm",
        "description": "Add new contact",
        "default_admin": True,
        "default_employee": False
    },
    "crm_contacts_edit": {
        "name": "Edit Contact",
        "screen": "crm",
        "description": "Edit contact",
        "default_admin": True,
        "default_employee": False
    },
    "crm_contacts_delete": {
        "name": "Delete Contact",
        "screen": "crm",
        "description": "Delete contact",
        "default_admin": True,
        "default_employee": False
    },
    "crm_deals_add": {
        "name": "Add Deal",
        "screen": "crm",
        "description": "Add new deal",
        "default_admin": True,
        "default_employee": False
    },
    "crm_deals_edit": {
        "name": "Edit Deal",
        "screen": "crm",
        "description": "Edit deal",
        "default_admin": True,
        "default_employee": False
    },
    "crm_activities_add": {
        "name": "Add Activity",
        "screen": "crm",
        "description": "Add CRM activity",
        "default_admin": True,
        "default_employee": False
    },
    "crm_quotes_add": {
        "name": "Create Quote",
        "screen": "crm",
        "description": "Create quote/proposal",
        "default_admin": True,
        "default_employee": False
    },
    "crm_products_add": {
        "name": "Add Product",
        "screen": "crm",
        "description": "Add CRM product",
        "default_admin": True,
        "default_employee": False
    },
    # Invoicing buttons
    "invoicing_create": {
        "name": "Create Invoice",
        "screen": "invoicing",
        "description": "Create new invoice",
        "default_admin": True,
        "default_employee": False
    },
    "invoicing_edit": {
        "name": "Edit Invoice",
        "screen": "invoicing",
        "description": "Edit invoice",
        "default_admin": True,
        "default_employee": False
    },
    "invoicing_delete": {
        "name": "Delete Invoice",
        "screen": "invoicing",
        "description": "Delete invoice",
        "default_admin": True,
        "default_employee": False
    },
    "invoicing_items_add": {
        "name": "Add Invoice Item",
        "screen": "invoicing",
        "description": "Add item to invoice",
        "default_admin": True,
        "default_employee": False
    },
    # Asset Management buttons
    "assets_add": {
        "name": "Add Asset",
        "screen": "assets",
        "description": "Add new asset",
        "default_admin": True,
        "default_employee": False
    },
    "assets_edit": {
        "name": "Edit Asset",
        "screen": "assets",
        "description": "Edit asset",
        "default_admin": True,
        "default_employee": False
    },
    "assets_delete": {
        "name": "Delete Asset",
        "screen": "assets",
        "description": "Delete asset",
        "default_admin": True,
        "default_employee": False
    },
    "assets_assign": {
        "name": "Assign Asset",
        "screen": "assets",
        "description": "Assign asset to employee",
        "default_admin": True,
        "default_employee": False
    },
    "assets_maintenance_add": {
        "name": "Add Maintenance",
        "screen": "assets",
        "description": "Add maintenance record",
        "default_admin": True,
        "default_employee": False
    },
    # Announcements buttons
    "announcements_add": {
        "name": "Add Announcement",
        "screen": "announcements",
        "description": "Add new announcement",
        "default_admin": True,
        "default_employee": False
    },
    "announcements_edit": {
        "name": "Edit Announcement",
        "screen": "announcements",
        "description": "Edit announcement",
        "default_admin": True,
        "default_employee": False
    },
    "announcements_delete": {
        "name": "Delete Announcement",
        "screen": "announcements",
        "description": "Delete announcement",
        "default_admin": True,
        "default_employee": False
    },
    # Documents buttons
    "documents_share": {
        "name": "Share Document",
        "screen": "documents",
        "description": "Share document with others",
        "default_admin": True,
        "default_employee": False
    },
    "documents_delete": {
        "name": "Delete Document",
        "screen": "documents",
        "description": "Delete document",
        "default_admin": True,
        "default_employee": False
    },
    # Time Tracking buttons
    "timetracking_add": {
        "name": "Add Time Entry",
        "screen": "time_tracking",
        "description": "Add time entry",
        "default_admin": True,
        "default_employee": False
    },
    # Inventory buttons
    "inventory_add": {
        "name": "Add Product",
        "screen": "inventory",
        "description": "Add inventory product",
        "default_admin": True,
        "default_employee": False
    },
    "inventory_edit": {
        "name": "Edit Product",
        "screen": "inventory",
        "description": "Edit inventory product",
        "default_admin": True,
        "default_employee": False
    },
    "inventory_delete": {
        "name": "Delete Product",
        "screen": "inventory",
        "description": "Delete inventory product",
        "default_admin": True,
        "default_employee": False
    },
    # Transactions buttons
    "transactions_add": {
        "name": "Add Transaction",
        "screen": "transactions",
        "description": "Add financial transaction",
        "default_admin": True,
        "default_employee": False
    },
}


def get_all_screen_keys():
    """Get list of all available screen keys"""
    return list(SCREEN_ACCESS_CONFIG.keys())


def get_all_button_keys():
    """Get list of all available button keys"""
    return list(BUTTON_ACCESS_CONFIG.keys())


def is_admin_user(user_id: int) -> bool:
    """
    Check if user is an admin.

    Args:
        user_id: The user's ID

    Returns:
        True if user is admin, False otherwise
    """
    if not user_id:
        return False

    db = None
    try:
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.role:
            return False
        return user.role.name.lower() == 'admin'
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False
    finally:
        if db:
            db.close()


def check_button_access_with_admin_override(user_id: int, button_key: str) -> bool:
    """
    Check if user has access to a specific button.
    Admin users always have access to all buttons.

    Args:
        user_id: The user's ID
        button_key: The button identifier

    Returns:
        True if access is allowed, False otherwise
    """
    # Admin users always have access
    if is_admin_user(user_id):
        return True

    return check_button_access(user_id, button_key)


def get_screens_by_category():
    """Get screens organized by category"""
    categories = {}
    for key, config in SCREEN_ACCESS_CONFIG.items():
        cat = config.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "key": key,
            "name": config["name"],
            "icon": config["icon"],
            "description": config["description"]
        })
    return categories


def get_buttons_by_screen():
    """Get buttons organized by screen"""
    by_screen = {}
    for key, config in BUTTON_ACCESS_CONFIG.items():
        screen = config.get("screen", "other")
        if screen not in by_screen:
            by_screen[screen] = []
        by_screen[screen].append({
            "key": key,
            "name": config["name"],
            "description": config["description"]
        })
    return by_screen


def _get_default_access(role_name: str = "employee") -> Dict[str, bool]:
    """Get default screen access based on role."""
    access_dict = {}
    for screen_key, config in SCREEN_ACCESS_CONFIG.items():
        if role_name == 'admin':
            access_dict[screen_key] = config['default_admin']
        else:
            access_dict[screen_key] = config['default_employee']
    return access_dict


def _get_default_button_access(role_name: str = "employee") -> Dict[str, bool]:
    """Get default button access based on role."""
    access_dict = {}
    for button_key, config in BUTTON_ACCESS_CONFIG.items():
        if role_name == 'admin':
            access_dict[button_key] = config['default_admin']
        else:
            access_dict[button_key] = config['default_employee']
    return access_dict


# ==================== BUTTON ACCESS FUNCTIONS ====================


def get_user_button_access(user_id: int) -> Dict[str, bool]:
    """
    Get all button access settings for a user from database.

    Args:
        user_id: The user's ID

    Returns:
        Dict with button_key -> is_enabled mapping
    """
    if not user_id:
        return _get_default_button_access("employee")

    db = None
    try:
        db = get_db_session()

        # Get user and role
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return _get_default_button_access("employee")

        role_name = user.role.name.lower() if user.role else "employee"

        # Build access dict - start with defaults
        access_dict = _get_default_button_access(role_name)

        # Check if ButtonAccess model exists and has records
        try:
            from database.models import ButtonAccess
            # Get user's button access from database
            access_records = db.query(ButtonAccess).filter(
                ButtonAccess.user_id == user_id
            ).all()

            # Override with database settings
            for record in access_records:
                access_dict[record.button_key] = bool(record.is_enabled)
        except Exception as e:
            print(f"ButtonAccess table not available: {e}")
            # Use defaults if table doesn't exist

        db.close()
        return access_dict

    except Exception as e:
        print(f"Error getting button access: {e}")
        if db:
            db.close()
        return _get_default_button_access("employee")


def check_button_access(user_id: int, button_key: str) -> bool:
    """
    Check if user has access to a specific button.

    Args:
        user_id: The user's ID
        button_key: The button identifier

    Returns:
        True if access is allowed, False otherwise
    """
    if not button_key:
        return False

    access_dict = get_user_button_access(user_id)
    return access_dict.get(button_key, False)


def set_button_access(
    user_id: int,
    button_key: str,
    is_enabled: bool,
    granted_by: Optional[int] = None
) -> bool:
    """
    Set button access for a user in database.

    Args:
        user_id: The user's ID
        button_key: The button identifier
        is_enabled: Whether access should be enabled
        granted_by: ID of admin granting access

    Returns:
        True if successful, False otherwise
    """
    from database.models import ButtonAccess

    db = None
    try:
        db = get_db_session()

        # Check if record exists
        existing = db.query(ButtonAccess).filter(
            and_(
                ButtonAccess.user_id == user_id,
                ButtonAccess.button_key == button_key
            )
        ).first()

        now = datetime.utcnow()

        if existing:
            # Update existing record
            db.query(ButtonAccess).filter(
                ButtonAccess.id == existing.id
            ).update({
                'is_enabled': is_enabled,
                'granted_by': granted_by,
                'granted_at': now,
                'updated_at': now
            })
        else:
            # Insert new record
            new_access = ButtonAccess(
                user_id=user_id,
                button_key=button_key,
                is_enabled=is_enabled,
                granted_by=granted_by,
                granted_at=now,
                created_at=now,
                updated_at=now
            )
            db.add(new_access)

        db.commit()
        db.close()
        return True

    except Exception as e:
        print(f"Error setting button access: {e}")
        if db:
            db.rollback()
            db.close()
        return False


def bulk_set_button_access(
    user_id: int,
    access_dict: Dict[str, bool],
    granted_by: Optional[int] = None
) -> bool:
    """
    Set multiple button access permissions for a user.

    Args:
        user_id: The user's ID
        access_dict: Dict of button_key -> is_enabled
        granted_by: ID of admin granting access

    Returns:
        True if all successful, False otherwise
    """
    from database.models import ButtonAccess

    db = None
    try:
        db = get_db_session()
        now = datetime.utcnow()

        for button_key, is_enabled in access_dict.items():
            # Check if record exists
            existing = db.query(ButtonAccess).filter(
                and_(
                    ButtonAccess.user_id == user_id,
                    ButtonAccess.button_key == button_key
                )
            ).first()

            if existing:
                # Update existing
                db.query(ButtonAccess).filter(
                    ButtonAccess.id == existing.id
                ).update({
                    'is_enabled': is_enabled,
                    'granted_by': granted_by,
                    'granted_at': now,
                    'updated_at': now
                })
            else:
                # Insert new record
                new_access = ButtonAccess(
                    user_id=user_id,
                    button_key=button_key,
                    is_enabled=is_enabled,
                    granted_by=granted_by,
                    granted_at=now,
                    created_at=now,
                    updated_at=now
                )
                db.add(new_access)

        db.commit()
        db.close()
        return True

    except Exception as e:
        print(f"Error bulk setting button access: {e}")
        if db:
            db.rollback()
            db.close()
        return False


def reset_button_access_to_defaults(user_id: int) -> bool:
    """
    Reset user's button access to default based on role.

    Args:
        user_id: The user's ID

    Returns:
        True if successful
    """
    from database.models import ButtonAccess

    db = None
    try:
        db = get_db_session()

        # Delete existing records
        db.query(ButtonAccess).filter(
            ButtonAccess.user_id == user_id
        ).delete()

        db.commit()
        db.close()
        return True

    except Exception as e:
        print(f"Error resetting button access: {e}")
        if db:
            db.rollback()
            db.close()
        return False


def get_user_full_access(user_id: int) -> Dict:
    """
    Get both screen and button access for a user.

    Args:
        user_id: The user's ID

    Returns:
        Dict with screen_access and button_access
    """
    return {
        'screen_access': get_user_screen_access(user_id),
        'button_access': get_user_button_access(user_id)
    }


def get_user_screen_access(user_id: int) -> Dict[str, bool]:
    """
    Get all screen access settings for a user from PostgreSQL database.

    Args:
        user_id: The user's ID

    Returns:
        Dict with screen_key -> is_enabled mapping
    """
    if not user_id:
        return _get_default_access("employee")

    db = None
    try:
        db = get_db_session()

        # Get user and role
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return _get_default_access("employee")

        role_name = user.role.name.lower() if user.role else "employee"

        # Get user's screen access from database
        access_records = db.query(ScreenAccess).filter(
            ScreenAccess.user_id == user_id
        ).all()

        # Build access dict - start with defaults
        access_dict = {}
        for screen_key, config in SCREEN_ACCESS_CONFIG.items():
            if role_name == 'admin':
                access_dict[screen_key] = config['default_admin']
            else:
                access_dict[screen_key] = config['default_employee']

        # Override with database settings
        for record in access_records:
            access_dict[record.screen_key] = bool(record.is_enabled)

        db.close()
        return access_dict

    except Exception as e:
        print(f"Error getting screen access: {e}")
        if db:
            db.close()
        return _get_default_access("employee")


def check_screen_access(user_id: int, screen_key: str) -> bool:
    """
    Check if user has access to a specific screen.

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
    Set screen access for a user in PostgreSQL database.

    Args:
        user_id: The user's ID
        screen_key: The screen identifier
        is_enabled: Whether access should be enabled
        granted_by: ID of admin granting access

    Returns:
        True if successful, False otherwise
    """
    db = None
    try:
        db = get_db_session()

        # Check if record exists
        existing = db.query(ScreenAccess).filter(
            and_(
                ScreenAccess.user_id == user_id,
                ScreenAccess.screen_key == screen_key
            )
        ).first()

        now = datetime.utcnow()

        if existing:
            # Update existing record using SQLAlchemy's setattr
            db.query(ScreenAccess).filter(
                ScreenAccess.id == existing.id
            ).update({
                'is_enabled': is_enabled,
                'granted_by': granted_by,
                'granted_at': now,
                'updated_at': now
            })
        else:
            # Insert new record
            new_access = ScreenAccess(
                user_id=user_id,
                screen_key=screen_key,
                is_enabled=is_enabled,
                granted_by=granted_by,
                granted_at=now,
                created_at=now,
                updated_at=now
            )
            db.add(new_access)

        db.commit()
        db.close()
        return True

    except Exception as e:
        print(f"Error setting screen access: {e}")
        if db:
            db.rollback()
            db.close()
        return False


def bulk_set_screen_access(
    user_id: int,
    access_dict: Dict[str, bool],
    granted_by: Optional[int] = None
) -> bool:
    """
    Set multiple screen access permissions for a user.

    Args:
        user_id: The user's ID
        access_dict: Dict of screen_key -> is_enabled
        granted_by: ID of admin granting access

    Returns:
        True if all successful, False otherwise
    """
    db = None
    try:
        db = get_db_session()
        now = datetime.utcnow()

        for screen_key, is_enabled in access_dict.items():
            # Check if record exists
            existing = db.query(ScreenAccess).filter(
                and_(
                    ScreenAccess.user_id == user_id,
                    ScreenAccess.screen_key == screen_key
                )
            ).first()

            if existing:
                # Update using SQLAlchemy update
                db.query(ScreenAccess).filter(
                    ScreenAccess.id == existing.id
                ).update({
                    'is_enabled': is_enabled,
                    'granted_by': granted_by,
                    'granted_at': now,
                    'updated_at': now
                })
            else:
                # Insert new record
                new_access = ScreenAccess(
                    user_id=user_id,
                    screen_key=screen_key,
                    is_enabled=is_enabled,
                    granted_by=granted_by,
                    granted_at=now,
                    created_at=now,
                    updated_at=now
                )
                db.add(new_access)

        db.commit()
        db.close()
        return True

    except Exception as e:
        print(f"Error bulk setting screen access: {e}")
        if db:
            db.rollback()
            db.close()
        return False


def get_active_employees_for_access_management() -> List[Dict]:
    """
    Get all active employees for the access management interface.
    Uses PostgreSQL database.

    Returns:
        List of dicts with user_id, username, email, role, screen_access and button_access summary
    """
    db = None
    try:
        db = get_db_session()

        # Get all users with employee profiles (excluding admins)
        users = db.query(User, Employee).outerjoin(
            Employee, User.id == Employee.user_id
        ).outerjoin(
            Role, User.role_id == Role.id
        ).filter(
            Role.name != 'admin'
        ).all()

        result = []
        for user, employee in users:
            if not user:
                continue

            # Get screen access for this user
            screen_access = get_user_screen_access(user.id)
            screen_enabled_count = sum(1 for v in screen_access.values() if v)

            # Get button access for this user
            button_access = get_user_button_access(user.id)
            button_enabled_count = sum(1 for v in button_access.values() if v)

            full_name = ""
            if employee:
                full_name = f"{employee.first_name or ''} {employee.last_name or ''}".strip(
                )

            result.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.name if user.role else 'employee',
                'full_name': full_name,
                'screen_access': screen_access,
                'button_access': button_access,
                'enabled_count': screen_enabled_count,
                'button_enabled_count': button_enabled_count,
                'total_screens': len(screen_access),
                'total_buttons': len(button_access)
            })

        db.close()
        return result

    except Exception as e:
        print(f"Error getting employees for access management: {e}")
        if db:
            db.close()
        return []


def get_employee_screen_access_detail(user_id: int) -> Dict:
    """
    Get detailed screen access information for an employee.

    Args:
        user_id: The user's ID

    Returns:
        Dict with detailed access information
    """
    db = None
    try:
        db = get_db_session()

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {}

        # Get all screen access records
        access_records = db.query(ScreenAccess).filter(
            ScreenAccess.user_id == user_id
        ).all()

        # Get employee info
        employee = db.query(Employee).filter(
            Employee.user_id == user_id
        ).first()

        access_details = []
        for screen_key, config in SCREEN_ACCESS_CONFIG.items():
            # Find if there's a specific record
            record = next(
                (r for r in access_records if r.screen_key == screen_key), None)

            is_enabled = config['default_employee']
            granted_by = None
            granted_at = None

            if record:
                is_enabled = bool(record.is_enabled)
                granted_by = record.granted_by
                granted_at = record.granted_at

            access_details.append({
                'screen_key': screen_key,
                'name': config['name'],
                'icon': config['icon'],
                'description': config['description'],
                'is_enabled': is_enabled,
                'granted_by': granted_by,
                'granted_at': granted_at,
                'category': config['category']
            })

        full_name = ""
        if employee:
            full_name = f"{employee.first_name or ''} {employee.last_name or ''}".strip(
            )

        db.close()

        return {
            'user_id': user_id,
            'username': user.username,
            'email': user.email,
            'full_name': full_name,
            'role': user.role.name if user.role else 'employee',
            'access_details': access_details
        }

    except Exception as e:
        print(f"Error getting employee access detail: {e}")
        if db:
            db.close()
        return {}


def reset_to_defaults(user_id: int) -> bool:
    """
    Reset user's screen access to default based on role.

    Args:
        user_id: The user's ID

    Returns:
        True if successful
    """
    db = None
    try:
        db = get_db_session()

        # Get user role
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return False

        # Delete existing records
        db.query(ScreenAccess).filter(
            ScreenAccess.user_id == user_id
        ).delete()

        db.commit()
        db.close()
        return True

    except Exception as e:
        print(f"Error resetting screen access: {e}")
        if db:
            db.rollback()
            db.close()
        return False


def delete_user_screen_access(user_id: int) -> bool:
    """
    Delete all screen access records for a user.

    Args:
        user_id: The user's ID

    Returns:
        True if successful
    """
    db = None
    try:
        db = get_db_session()

        db.query(ScreenAccess).filter(
            ScreenAccess.user_id == user_id
        ).delete()

        db.commit()
        db.close()
        return True

    except Exception as e:
        print(f"Error deleting screen access: {e}")
        if db:
            db.rollback()
            db.close()
        return False


def get_screen_access_summary() -> Dict:
    """
    Get summary of all screen access settings in the system.

    Returns:
        Dict with summary statistics
    """
    db = None
    try:
        db = get_db_session()

        # Total users with access
        total_users = db.query(ScreenAccess.user_id).distinct().count()

        # Count by screen
        screen_stats = {}
        _enabled = True
        for screen_key in SCREEN_ACCESS_CONFIG.keys():
            count = db.query(ScreenAccess).filter(
                and_(
                    ScreenAccess.screen_key == screen_key,
                    ScreenAccess.is_enabled == _enabled
                )
            ).count()
            screen_stats[screen_key] = count

        db.close()

        return {
            'total_users_with_custom_access': total_users,
            'screen_stats': screen_stats,
            'available_screens': list(SCREEN_ACCESS_CONFIG.keys())
        }

    except Exception as e:
        print(f"Error getting screen access summary: {e}")
        if db:
            db.close()
        return {}
