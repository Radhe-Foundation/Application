"""
Vernika HRA - Role-Based Access Control Decorators
Industry-Level Human Resource Management System

This module provides decorators for role-based access control.
"""

from functools import wraps
from typing import List, Callable, Any
import flet as ft


class AccessDeniedError(Exception):
    """Exception raised when access is denied"""
    pass


def require_roles(allowed_roles: List[str]):
    """
    Decorator to require specific roles for accessing a function.

    Args:
        allowed_roles: List of role names that are allowed access

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get page from args (first argument should be self with page attribute)
            page = None
            for arg in args:
                if isinstance(arg, ft.Page):
                    page = arg
                    break
                if hasattr(arg, 'page'):
                    page = arg.page
                    break

            if page is None:
                # Try to get from kwargs
                page = kwargs.get('page')

            if page is None:
                raise AccessDeniedError("Could not determine page context")

            # Get user from session
            user = page.session.get("user") if hasattr(
                page.session, 'get') else None

            if user is None:
                # Try alternative session access
                try:
                    user = page.session.get("user")
                except Exception:
                    raise AccessDeniedError("User not logged in")

            if user is None:
                raise AccessDeniedError("User not logged in")

            # Get user role
            user_role = user.get("role", "")

            if user_role not in allowed_roles:
                raise AccessDeniedError(
                    f"Access denied. Required roles: {', '.join(allowed_roles)}. "
                    f"Your role: {user_role}"
                )

            return func(*args, **kwargs)

        return wrapper
    return decorator


def require_admin(func: Callable) -> Callable:
    """
    Decorator to require Admin role.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    return require_roles(["Admin", "Administrator"])(func)


def require_hr(func: Callable) -> Callable:
    """
    Decorator to require HR Manager role.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    return require_roles(["Admin", "HR", "HR Manager"])(func)


def require_manager(func: Callable) -> Callable:
    """
    Decorator to require Manager role.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    return require_roles(["Admin", "Manager", "HR Manager"])(func)


def require_employee(func: Callable) -> Callable:
    """
    Decorator to require Employee role (or above).

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    return require_roles(["Admin", "HR Manager", "Manager", "Employee"])(func)


def check_permission(page: ft.Page, permission: str) -> bool:
    """
    Check if current user has a specific permission.

    Args:
        page: Flet page object
        permission: Permission name to check

    Returns:
        bool: True if user has permission
    """
    user = page.session.get("user") if hasattr(page.session, 'get') else None
    if user is None:
        return False

    role = user.get("role", "")
    permissions = user.get("permissions", {})

    # Admin has all permissions
    if role in ["Admin", "Administrator"]:
        return True

    # Check specific permission
    return permissions.get(permission, False)


def get_role_permissions(role_name: str) -> dict:
    """
    Get permissions dictionary for a role.

    Args:
        role_name: Name of the role

    Returns:
        dict: Permissions dictionary
    """
    role_permissions = {
        "Admin": {
            "manage_users": True,
            "manage_employees": True,
            "manage_departments": True,
            "manage_positions": True,
            "manage_attendance": True,
            "manage_leaves": True,
            "manage_tasks": True,
            "manage_performance": True,
            "manage_documents": True,
            "manage_announcements": True,
            "view_reports": True,
            "manage_settings": True,
            "view_audit_logs": True,
            "export_data": True,
        },
        "HR Manager": {
            "manage_users": False,
            "manage_employees": True,
            "manage_departments": True,
            "manage_positions": True,
            "manage_attendance": True,
            "manage_leaves": True,
            "manage_tasks": False,
            "manage_performance": True,
            "manage_documents": True,
            "manage_announcements": True,
            "view_reports": True,
            "manage_settings": False,
            "view_audit_logs": False,
            "export_data": True,
        },
        "Manager": {
            "manage_users": False,
            "manage_employees": False,
            "manage_departments": False,
            "manage_positions": False,
            "manage_attendance": False,
            "manage_leaves": True,
            "manage_tasks": True,
            "manage_performance": True,
            "manage_documents": False,
            "manage_announcements": False,
            "view_reports": True,
            "manage_settings": False,
            "view_audit_logs": False,
            "export_data": False,
        },
        "Employee": {
            "manage_users": False,
            "manage_employees": False,
            "manage_departments": False,
            "manage_positions": False,
            "manage_attendance": False,
            "manage_leaves": True,
            "manage_tasks": True,
            "manage_performance": False,
            "manage_documents": True,
            "manage_announcements": False,
            "view_reports": False,
            "manage_settings": False,
            "view_audit_logs": False,
            "export_data": False,
        },
    }

    return role_permissions.get(role_name, {})


def role_hierarchy() -> dict:
    """
    Get role hierarchy (higher number = more permissions).

    Returns:
        dict: Role hierarchy mapping
    """
    return {
        "Admin": 100,
        "HR Manager": 80,
        "Manager": 60,
        "Employee": 40,
    }


def has_higher_or_equal_role(user_role: str, required_role: str) -> bool:
    """
    Check if user role has higher or equal privileges.

    Args:
        user_role: User's role name
        required_role: Required role name        bool: True

    Returns:
 if user has sufficient role level
    """
    hierarchy = role_hierarchy()
    user_level = hierarchy.get(user_role, 0)
    required_level = hierarchy.get(required_role, 0)
    return user_level >= required_level
