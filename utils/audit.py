"""
Vernika HRA - Audit Logging System
Tracks all user activities and system changes
"""

import flet as ft
from datetime import datetime
from typing import Optional, List, Dict
from database.connection import get_db_session
from database.models import AuditLog


class AuditLogger:
    """Centralized audit logging for the application"""

    # Action types constants
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    DOWNLOAD = "download"
    UPLOAD = "upload"

    @staticmethod
    def log(user_id: int, action: str, details: Optional[str] = None,
            module: str = "general", ip_address: Optional[str] = None):
        """
        Log an audit entry

        Args:
            user_id: ID of the user performing the action
            action: Type of action (login, create, update, etc.)
            details: Additional details about the action
            module: Module/screen where action occurred
            ip_address: User's IP address (optional)
        """
        try:
            db = get_db_session()
            try:
                # Build detail string
                detail_str = f"[{module}] {action}"
                if details:
                    detail_str += f": {details}"

                log_entry = AuditLog(
                    user_id=user_id,
                    action=action,
                    details=detail_str
                )
                db.add(log_entry)
                db.commit()
            except Exception as e:
                print(f"Audit log error: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            print(f"Audit logging failed: {e}")

    @staticmethod
    def log_login(user_id: int, username: str):
        """Log user login"""
        AuditLogger.log(user_id, AuditLogger.LOGIN,
                        f"User logged in: {username}")

    @staticmethod
    def log_logout(user_id: int, username: str):
        """Log user logout"""
        AuditLogger.log(user_id, AuditLogger.LOGOUT,
                        f"User logged out: {username}")

    @staticmethod
    def log_create(user_id: int, entity_type: str, entity_id: int, details: str = None):
        """Log entity creation"""
        detail = f"Created {entity_type} ID:{entity_id}"
        if details:
            detail += f" - {details}"
        AuditLogger.log(user_id, AuditLogger.CREATE,
                        detail, module=entity_type.lower())

    @staticmethod
    def log_update(user_id: int, entity_type: str, entity_id: int, changes: str = None):
        """Log entity update"""
        detail = f"Updated {entity_type} ID:{entity_id}"
        if changes:
            detail += f" - {changes}"
        AuditLogger.log(user_id, AuditLogger.UPDATE,
                        detail, module=entity_type.lower())

    @staticmethod
    def log_delete(user_id: int, entity_type: str, entity_id: int):
        """Log entity deletion"""
        AuditLogger.log(user_id, AuditLogger.DELETE, f"Deleted {entity_type} ID:{entity_id}",
                        module=entity_type.lower())

    @staticmethod
    def log_view(user_id: int, entity_type: str, entity_id: int = None):
        """Log entity view"""
        detail = f"Viewed {entity_type}"
        if entity_id:
            detail += f" ID:{entity_id}"
        AuditLogger.log(user_id, AuditLogger.VIEW, detail,
                        module=entity_type.lower())

    @staticmethod
    def get_recent_logs(limit: int = 50, user_id: Optional[int] = None,
                        action: Optional[str] = None) -> List[Dict]:
        """
        Get recent audit logs

        Args:
            limit: Maximum number of logs to return
            user_id: Filter by user (optional)
            action: Filter by action type (optional)

        Returns:
            List of audit log dictionaries
        """
        from database.operations import get_all_audit_logs
        from database.connection import get_db_session

        try:
            db = get_db_session()
            query = db.query(AuditLog)

            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action:
                query = query.filter(AuditLog.action == action)

            logs = query.order_by(
                AuditLog.created_at.desc()).limit(limit).all()

            result = []
            for log in logs:
                result.append({
                    'id': log.id,
                    'user_id': log.user_id,
                    'action': log.action,
                    'details': log.details,
                    'created_at': log.created_at
                })

            db.close()
            return result
        except Exception as e:
            print(f"Error getting audit logs: {e}")
            return []


# Global audit logger instance
audit_logger = AuditLogger()


def log_user_action(user_id: int, action: str, details: str = None):
    """Convenience function for logging user actions"""
    audit_logger.log(user_id, action, details)


def get_audit_trail(entity_type: str = None, user_id: int = None,
                    limit: int = 100) -> List[Dict]:
    """Get audit trail with optional filters"""
    return audit_logger.get_recent_logs(limit=limit, user_id=user_id)
