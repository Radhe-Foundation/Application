# RadheFoundation Application - Role Check
# Decorators and utilities for role-based access control

import flet as ft
from functools import wraps
from auth.session import session_manager
from flet import Page


class RoleError(Exception):
    """Custom exception for role-based access violations"""
    pass


def require_role(allowed_roles: list):
    """
    Decorator to require specific roles for accessing a function

    Usage:
        @require_role(["Admin"])
        def admin_function():
            pass

        @require_role(["Admin", "Employee"])
        def any_privileged_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not session_manager.is_logged_in:
                raise RoleError(
                    "User must be logged in to access this feature")

            user_role = session_manager.current_user.role.name

            if user_role not in allowed_roles:
                raise RoleError(
                    f"Access denied. Required role: {', '.join(allowed_roles)}. "
                    f"Your role: {user_role}"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(func):
    """
    Decorator to require Admin role
    """
    return require_role(["Admin"])(func)


def require_employee(func):
    """
    Decorator to require Employee role
    """
    return require_role(["Employee"])(func)


def check_user_role(user_role: str, required_roles: list) -> bool:
    """
    Check if user role is in allowed roles

    Args:
        user_role: The user's role name
        required_roles: List of allowed role names

    Returns:
        bool: True if user has required role, False otherwise
    """
    return user_role in required_roles


def get_user_permissions(role_name: str) -> dict:
    """
    Get permissions based on role

    Args:
        role_name: The user's role name

    Returns:
        dict: Dictionary of permissions
    """
    permissions = {
        "Admin": {
            "can_manage_users": True,
            "can_manage_employees": True,
            "can_view_reports": True,
            "can_manage_settings": True,
            "can_audit_logs": True,
            "can_delete_records": True,
            "can_export_data": True,
            "dashboard_access": "full"
        },
        "Employee": {
            "can_manage_users": False,
            "can_manage_employees": False,
            "can_view_reports": False,
            "can_manage_settings": False,
            "can_audit_logs": False,
            "can_delete_records": False,
            "can_export_data": False,
            "dashboard_access": "limited"
        }
    }

    return permissions.get(role_name, {
        "can_manage_users": False,
        "can_manage_employees": False,
        "can_view_reports": False,
        "can_manage_settings": False,
        "can_audit_logs": False,
        "can_delete_records": False,
        "can_export_data": False,
        "dashboard_access": "none"
    })


def can_access_feature(feature: str, user_role: str) -> bool:
    """
    Check if user can access a specific feature

    Args:
        feature: The feature to check (e.g., "manage_users")
        user_role: The user's role name

    Returns:
        bool: True if feature is accessible
    """
    permissions = get_user_permissions(user_role)
    return permissions.get(feature, False)


# Role-based navigation config for Flet
ROLE_NAVIGATION = {
    "Admin": [
        {"name": "Dashboard", "route": "/admin/dashboard", "icon": "dashboard"},
        {"name": "Users", "route": "/admin/users", "icon": "people"},
        {"name": "Employees", "route": "/admin/employees", "icon": "badge"},
        {"name": "Reports", "route": "/admin/reports", "icon": "assessment"},
        {"name": "Settings", "route": "/admin/settings", "icon": "settings"},
        {"name": "Audit Logs", "route": "/admin/audit", "icon": "history"},
    ],
    "Employee": [
        {"name": "Dashboard", "route": "/employee/dashboard", "icon": "dashboard"},
        {"name": "My Profile", "route": "/employee/profile", "icon": "person"},
        {"name": "My Tasks", "route": "/employee/tasks", "icon": "task"},
    ]
}


def get_navigation_items(user_role: str) -> list:
    """
    Get navigation items based on user role

    Args:
        user_role: The user's role name

    Returns:
        list: List of navigation items
    """
    return ROLE_NAVIGATION.get(user_role, [])


# Role hierarchy for permission inheritance
ROLE_HIERARCHY = {
    "Admin": 100,
    "HR Manager": 80,
    "Manager": 60,
    "Employee": 40,
    "Guest": 0
}


def has_higher_or_equal_role(user_role: str, required_role: str) -> bool:
    """
    Check if user role has higher or equal privilege than required role.

    Args:
        user_role: The user's role name
        required_role: The required role name

    Returns:
        bool: True if user has sufficient role level
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def get_role_level(role_name: str) -> int:
    """
    Get the privilege level for a role.

    Args:
        role_name: The role name

    Returns:
        int: Privilege level (higher = more privilege)
    """
    return ROLE_HIERARCHY.get(role_name, 0)


def verify_admin_access(current_user) -> tuple:
    """
    Verify if the current user has admin access.

    Args:
        current_user: The current user object or dict

    Returns:
        tuple: (is_admin: bool, user_role: str, message: str)
    """
    if not current_user:
        return (False, "Guest", "User must be logged in to access this feature")

    # Handle both User object and dict format
    if isinstance(current_user, dict):
        user_role = current_user.get('role', '').lower()
    else:
        user_role = getattr(current_user, 'role', None)
        if user_role:
            user_role = user_role.name.lower() if hasattr(
                user_role, 'name') else str(user_role).lower()
        else:
            user_role = str(current_user).lower()

    # Check for admin role (both "admin" and "Admin" should work)
    if user_role == 'admin':
        return (True, user_role, "Admin access verified")

    return (False, user_role, f"Access denied. Admin privileges required. Your role: {user_role}")


def check_admin_access(current_user) -> bool:
    """
    Simple check if user has admin access.

    Args:
        current_user: The current user object or dict

    Returns:
        bool: True if user is admin, False otherwise
    """
    if not current_user:
        return False

    # Handle both User object and dict format
    if isinstance(current_user, dict):
        user_role = current_user.get('role', '').lower()
    else:
        user_role = getattr(current_user, 'role', None)
        if user_role:
            user_role = user_role.name.lower() if hasattr(
                user_role, 'name') else str(user_role).lower()
        else:
            user_role = str(current_user).lower()

    return user_role == 'admin'


def redirect_if_not_admin(page, current_user, target_screen="admin"):
    """
    Redirect user if they don't have admin access.

    Args:
        page: Flet page object
        current_user: The current user object or dict
        target_screen: Screen to redirect to if not admin

    Returns:
        bool: True if access is allowed, False if redirected
    """
    is_admin, user_role, message = verify_admin_access(current_user)

    if not is_admin:
        # Show snackbar with access denied message
        snack = ft.SnackBar(
            content=ft.Text(message, color="WHITE"),
            bgcolor="#DC3545"
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

        # Redirect to appropriate screen
        from screens.login_screen import LoginScreen
        page.clean()
        page.add(LoginScreen(page))
        return False

    return True
