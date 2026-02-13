# Vernika Application - Constants
# Application-wide constants and enums

from enum import Enum


class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "Admin"
    EMPLOYEE = "Employee"


class UserStatus(Enum):
    """User status enumeration"""
    ACTIVE = True
    INACTIVE = False


class AppRoute(Enum):
    """Application routes"""
    LOGIN = "/login"
    ADMIN_DASHBOARD = "/admin/dashboard"
    EMPLOYEE_DASHBOARD = "/employee/dashboard"
    ADMIN_USERS = "/admin/users"
    ADMIN_EMPLOYEES = "/admin/employees"
    ADMIN_REPORTS = "/admin/reports"
    ADMIN_SETTINGS = "/admin/settings"
    ADMIN_AUDIT = "/admin/audit"
    EMPLOYEE_PROFILE = "/employee/profile"
    EMPLOYEE_TASKS = "/employee/tasks"


class DatabaseConfig(Enum):
    """Database configuration"""
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600


class SessionConfig(Enum):
    """Session configuration"""
    TOKEN_EXPIRY_HOURS = 24
    SESSION_TIMEOUT_MINUTES = 30
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15


class UIConstants(Enum):
    """UI-related constants"""
    DEFAULT_WINDOW_WIDTH = 1280
    DEFAULT_WINDOW_HEIGHT = 800
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600
    PAGE_PADDING = 20
    CARD_ELEVATION = 3
    BORDER_RADIUS = 10


class ErrorMessage(Enum):
    """Error messages"""
    INVALID_CREDENTIALS = "Invalid username or password"
    ACCOUNT_LOCKED = "Account is locked. Please try again later."
    ACCOUNT_INACTIVE = "Account is inactive. Please contact administrator."
    SESSION_EXPIRED = "Session expired. Please login again."
    PERMISSION_DENIED = "You don't have permission to access this resource."
    UNKNOWN_ERROR = "An unknown error occurred. Please try again."
