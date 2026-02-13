# Vernika Application - Utility Functions
# Helper functions for common operations

import re
from datetime import datetime
from flet import SnackBar, Text


def validate_username(username: str) -> tuple:
    """
    Validate username format

    Args:
        username: Username to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username must be less than 50 characters"

    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"

    return True, ""


def validate_email(email: str) -> tuple:
    """
    Validate email format

    Args:
        email: Email to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    return True, ""


def validate_password(password: str) -> tuple:
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"

    return True, ""


def format_date(date_obj: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string

    Args:
        date_obj: Datetime object
        format_str: Format string

    Returns:
        str: Formatted date string
    """
    if not date_obj:
        return ""

    return date_obj.strftime(format_str)


def show_snackbar(page, message: str, duration: int = 3000):
    """
    Show a snackbar notification

    Args:
        page: Flet page object
        message: Message to display
        duration: Duration in milliseconds
    """
    snackbar = SnackBar(
        content=Text(message),
        duration=duration
    )
    page.overlay.append(snackbar)
    snackbar.open = True
    page.update()


def get_current_timestamp() -> datetime:
    """
    Get current timestamp

    Returns:
        datetime: Current datetime
    """
    return datetime.utcnow()


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to specified length

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        str: Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."


class Logger:
    """Simple logger class"""

    def __init__(self, name: str = "Vernika"):
        self.name = name

    def info(self, message: str):
        print(f"[INFO] [{self.name}] {message}")

    def warning(self, message: str):
        print(f"[WARNING] [{self.name}] {message}")

    def error(self, message: str):
        print(f"[ERROR] [{self.name}] {message}")

    def debug(self, message: str):
        print(f"[DEBUG] [{self.name}] {message}")


# Create default logger instance
logger = Logger()
