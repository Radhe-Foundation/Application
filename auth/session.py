# RadheFoundation Application - Session Management
# Handle user sessions and state

from typing import Optional
from database.models import User


class SessionManager:
    """Manage user sessions"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_user = None
            cls._instance._current_token = None
        return cls._instance

    @property
    def current_user(self) -> Optional[User]:
        """Get current logged in user"""
        return self._current_user

    @current_user.setter
    def current_user(self, user: User):
        """Set current user"""
        self._current_user = user

    @property
    def current_token(self) -> Optional[str]:
        """Get current session token"""
        return self._current_token

    @current_token.setter
    def current_token(self, token: str):
        """Set current session token"""
        self._current_token = token

    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self._current_user is not None

    @property
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self._current_user and self._current_user.role.name.lower() == "admin"

    @property
    def is_employee(self) -> bool:
        """Check if current user is employee"""
        return self._current_user and self._current_user.role.name.lower() == "employee"

    def clear_session(self):
        """Clear current session"""
        self._current_user = None
        self._current_token = None

    def get_user_role(self) -> str:
        """Get current user's role name"""
        if self._current_user:
            return self._current_user.role.name
        return "Guest"


# Global session manager instance
session_manager = SessionManager()


def get_current_user() -> Optional[User]:
    """
    Get the current logged in user.

    Returns:
        User object if logged in, None otherwise
    """
    return session_manager.current_user


def set_current_user(user: User) -> None:
    """
    Set the current logged in user.

    Args:
        user: User object to set as current user
    """
    session_manager.current_user = user


def clear_current_user() -> None:
    """Clear the current user session"""
    session_manager.clear_session()
