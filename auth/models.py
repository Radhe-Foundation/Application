"""
Vernika HRA - Auth Models
Industry-Level Human Resource Management System

This module provides authentication-related models and utilities.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# Try to import PyJWT, fall back to python-jose if not available
try:
    import jwt
except ImportError:
    try:
        from jose import jwt  # type: ignore
    except ImportError:
        jwt = None
        print("WARNING: Neither PyJWT nor python-jose is installed. JWT functionality will not work.")

import bcrypt
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.connection import Base
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


class AuthStatus(Enum):
    """Authentication status enumeration"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    EXPIRED = "expired"
    INVALID = "invalid"


@dataclass
class TokenPayload:
    """Token payload dataclass"""
    user_id: int
    username: str
    role: str
    exp: datetime = field(default_factory=lambda: datetime.utcnow())
    iat: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "exp": self.exp.isoformat(),
            "iat": self.iat.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """Create from dictionary"""
        return cls(
            user_id=data.get("user_id", 0),
            username=data.get("username", ""),
            role=data.get("role", ""),
            exp=datetime.fromisoformat(
                data.get("exp", datetime.utcnow().isoformat())),
            iat=datetime.fromisoformat(
                data.get("iat", datetime.utcnow().isoformat()))
        )


@dataclass
class AuthResult:
    """Authentication result dataclass"""
    status: AuthStatus
    message: str = ""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    token: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status.value,
            "message": self.message,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "token": self.token,
            "user_data": self.user_data
        }

    @property
    def is_success(self) -> bool:
        """Check if authentication was successful"""
        return self.status == AuthStatus.SUCCESS

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == "Admin"


class Permission(Enum):
    """Permission enumeration"""
    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"

    # Employee management
    MANAGE_EMPLOYEES = "manage_employees"
    VIEW_EMPLOYEES = "view_employees"

    # Department management
    MANAGE_DEPARTMENTS = "manage_departments"
    VIEW_DEPARTMENTS = "view_departments"

    # Position management
    MANAGE_POSITIONS = "manage_positions"
    VIEW_POSITIONS = "view_positions"

    # Attendance management
    MANAGE_ATTENDANCE = "manage_attendance"
    VIEW_ATTENDANCE = "view_attendance"
    MARK_ATTENDANCE = "mark_attendance"

    # Leave management
    MANAGE_LEAVES = "manage_leaves"
    VIEW_LEAVES = "view_leaves"
    APPROVE_LEAVES = "approve_leaves"
    APPLY_LEAVE = "apply_leave"

    # Task management
    MANAGE_TASKS = "manage_tasks"
    VIEW_TASKS = "view_tasks"
    ASSIGN_TASKS = "assign_tasks"

    # Performance management
    MANAGE_PERFORMANCE = "manage_performance"
    VIEW_PERFORMANCE = "view_performance"

    # Document management
    MANAGE_DOCUMENTS = "manage_documents"
    VIEW_DOCUMENTS = "view_documents"
    UPLOAD_DOCUMENTS = "upload_documents"

    # Announcement management
    MANAGE_ANNOUNCEMENTS = "manage_announcements"
    VIEW_ANNOUNCEMENTS = "view_announcements"

    # Reports
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"

    # Settings
    MANAGE_SETTINGS = "manage_settings"
    VIEW_SETTINGS = "view_settings"

    # Audit
    VIEW_AUDIT_LOGS = "view_audit_logs"


# Role-based permissions
ROLE_PERMISSIONS = {
    "Admin": list(Permission),
    "HR Manager": [
        Permission.MANAGE_EMPLOYEES,
        Permission.VIEW_EMPLOYEES,
        Permission.MANAGE_DEPARTMENTS,
        Permission.VIEW_DEPARTMENTS,
        Permission.MANAGE_POSITIONS,
        Permission.VIEW_POSITIONS,
        Permission.MANAGE_ATTENDANCE,
        Permission.VIEW_ATTENDANCE,
        Permission.MANAGE_LEAVES,
        Permission.VIEW_LEAVES,
        Permission.APPROVE_LEAVES,
        Permission.MANAGE_TASKS,
        Permission.VIEW_TASKS,
        Permission.ASSIGN_TASKS,
        Permission.VIEW_PERFORMANCE,
        Permission.MANAGE_DOCUMENTS,
        Permission.VIEW_DOCUMENTS,
        Permission.UPLOAD_DOCUMENTS,
        Permission.MANAGE_ANNOUNCEMENTS,
        Permission.VIEW_ANNOUNCEMENTS,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_SETTINGS,
    ],
    "Manager": [
        Permission.VIEW_EMPLOYEES,
        Permission.VIEW_DEPARTMENTS,
        Permission.VIEW_POSITIONS,
        Permission.VIEW_ATTENDANCE,
        Permission.MARK_ATTENDANCE,
        Permission.VIEW_LEAVES,
        Permission.APPROVE_LEAVES,
        Permission.MANAGE_TASKS,
        Permission.VIEW_TASKS,
        Permission.ASSIGN_TASKS,
        Permission.VIEW_PERFORMANCE,
        Permission.VIEW_DOCUMENTS,
        Permission.VIEW_ANNOUNCEMENTS,
        Permission.VIEW_REPORTS,
    ],
    "Employee": [
        Permission.VIEW_EMPLOYEES,
        Permission.VIEW_ATTENDANCE,
        Permission.MARK_ATTENDANCE,
        Permission.APPLY_LEAVE,
        Permission.VIEW_LEAVES,
        Permission.VIEW_TASKS,
        Permission.VIEW_DOCUMENTS,
        Permission.VIEW_ANNOUNCEMENTS,
    ],
}


class AuthService:
    """
    Authentication service for handling authentication operations.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            str: Hashed password
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            password: Plain text password
            hashed_password: Hashed password

        Returns:
            bool: True if password matches
        """
        return bcrypt.checkpw(
            password.encode(),
            hashed_password.encode()
        )

    @staticmethod
    def create_token(
        user_id: int,
        username: str,
        role: str,
        expires_in_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
    ) -> str:
        """
        Create a JWT token.

        Args:
            user_id: User ID
            username: Username
            role: User role
            expires_in_minutes: Token expiration time

        Returns:
            str: JWT token
        """
        if jwt is None:
            raise ImportError(
                "JWT library not installed. Please install PyJWT or python-jose")

        payload = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[TokenPayload]:
        """
        Decode a JWT token.

        Args:
            token: JWT token

        Returns:
            TokenPayload or None
        """
        if jwt is None:
            print("WARNING: JWT library not installed. Token decode failed.")
            return None

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return TokenPayload.from_dict(payload)
        except Exception:
            return None

    @staticmethod
    def validate_token(token: str) -> AuthResult:
        """
        Validate a JWT token.

        Args:
            token: JWT token

        Returns:
            AuthResult with validation status
        """
        payload = AuthService.decode_token(token)

        if payload is None:
            return AuthResult(
                status=AuthStatus.EXPIRED,
                message="Token has expired or is invalid"
            )

        # Check if token is expired
        if payload.exp < datetime.utcnow():
            return AuthResult(
                status=AuthStatus.EXPIRED,
                message="Token has expired"
            )

        return AuthResult(
            status=AuthStatus.SUCCESS,
            message="Token is valid",
            user_id=payload.user_id,
            username=payload.username,
            role=payload.role,
            token=token
        )

    @staticmethod
    def get_user_permissions(role: str) -> list:
        """
        Get permissions for a role.

        Args:
            role: Role name

        Returns:
            list: List of permissions
        """
        return ROLE_PERMISSIONS.get(role, [])

    @staticmethod
    def has_permission(role: str, permission: Permission) -> bool:
        """
        Check if a role has a specific permission.

        Args:
            role: Role name
            permission: Permission to check

        Returns:
            bool: True if role has permission
        """
        permissions = AuthService.get_user_permissions(role)
        return permission in permissions

    @staticmethod
    def has_any_permission(role: str, permissions: list) -> bool:
        """
        Check if a role has any of the specified permissions.

        Args:
            role: Role name
            permissions: List of permissions

        Returns:
            bool: True if role has any permission
        """
        user_permissions = AuthService.get_user_permissions(role)
        return any(p in user_permissions for p in permissions)

    @staticmethod
    def has_all_permissions(role: str, permissions: list) -> bool:
        """
        Check if a role has all specified permissions.

        Args:
            role: Role name
            permissions: List of permissions

        Returns:
            bool: True if role has all permissions
        """
        user_permissions = AuthService.get_user_permissions(role)
        return all(p in user_permissions for p in permissions)


# Session token storage (in-memory for desktop app)
class SessionStore:
    """
    Session token storage for desktop application.
    """

    _instance = None
    _sessions: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_session(
        self,
        token: str,
        user_id: int,
        username: str,
        role: str
    ) -> None:
        """
        Create a new session.

        Args:
            token: Session token
            user_id: User ID
            username: Username
            role: User role
        """
        self._sessions[token] = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": datetime.utcnow()
        }

    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.

        Args:
            token: Session token

        Returns:
            Session data or None
        """
        return self._sessions.get(token)

    def delete_session(self, token: str) -> bool:
        """
        Delete a session.

        Args:
            token: Session token

        Returns:
            True if session was deleted
        """
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False

    def clear_all_sessions(self):
        """Clear all sessions"""
        self._sessions.clear()

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all sessions"""
        return self._sessions.copy()


# Global session store instance
session_store = SessionStore()
