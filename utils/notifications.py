"""
RadheFoundation HRA - Notification System
In-app notification system for various events
"""

import flet as ft
from typing import List, Callable, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Notification:
    """Notification data class"""
    id: str
    title: str
    message: str
    notification_type: str = "info"  # info, success, warning, error
    created_at: datetime = field(default_factory=datetime.now)
    read: bool = False
    action_url: Optional[str] = None


class NotificationManager:
    """Manages in-app notifications"""

    def __init__(self):
        self._notifications: List[Notification] = []
        self._listeners: List[Callable] = []

    def add(self, notification: Notification):
        """Add a new notification"""
        self._notifications.insert(0, notification)
        self._notify_listeners()

    def mark_read(self, notification_id: str):
        """Mark notification as read"""
        for notif in self._notifications:
            if notif.id == notification_id:
                notif.read = True
                break
        self._notify_listeners()

    def mark_all_read(self):
        """Mark all notifications as read"""
        for notif in self._notifications:
            notif.read = True
        self._notify_listeners()

    def remove(self, notification_id: str):
        """Remove a notification"""
        self._notifications = [
            n for n in self._notifications if n.id != notification_id]
        self._notify_listeners()

    def clear(self):
        """Clear all notifications"""
        self._notifications = []
        self._notify_listeners()

    def get_all(self) -> List[Notification]:
        """Get all notifications"""
        return self._notifications

    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return sum(1 for n in self._notifications if not n.read)

    def add_listener(self, callback: Callable):
        """Add a listener for notification changes"""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable):
        """Remove a listener"""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        """Notify all listeners of changes"""
        for listener in self._listeners:
            try:
                listener(self._notifications)
            except Exception as e:
                print(f"Notification listener error: {e}")


# Global notification manager
_notification_manager = NotificationManager()


def get_notification_manager() -> NotificationManager:
    """Get the global notification manager"""
    return _notification_manager


def show_notification(page: ft.Page, title: str, message: str,
                      notification_type: str = "info", duration: int = 3):
    """
    Show a quick notification snackbar

    Args:
        page: Flet page
        title: Notification title
        message: Notification message  
        notification_type: info, success, warning, error
        duration: Duration in seconds
    """
    colors = {
        "info": "#2196F3",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336"
    }

    bgcolor = colors.get(notification_type, colors["info"])

    # Create content with icon based on type
    icons = {
        "info": ft.Icons.INFO,
        "success": ft.Icons.CHECK_CIRCLE,
        "warning": ft.Icons.WARNING,
        "error": ft.Icons.ERROR
    }

    icon = icons.get(notification_type, icons["info"])

    content = ft.Row([
        ft.Icon(icon, color="white", size=20),
        ft.Column([
            ft.Text(title, weight=ft.FontWeight.BOLD, color="white", size=14),
            ft.Text(message, color="white", size=12),
        ], spacing=0, expand=True)
    ], spacing=10)

    snack = ft.SnackBar(
        content=content,
        bgcolor=bgcolor,
        duration=duration * 1000,
        action="Dismiss",
        action_color="white"
    )

    page.overlay.append(snack)
    snack.open = True
    page.update()


def notify_success(page: ft.Page, message: str, title: str = "Success"):
    """Show success notification"""
    show_notification(page, title, message, "success")


def notify_error(page: ft.Page, message: str, title: str = "Error"):
    """Show error notification"""
    show_notification(page, title, message, "error")


def notify_warning(page: ft.Page, message: str, title: str = "Warning"):
    """Show warning notification"""
    show_notification(page, title, message, "warning")


def notify_info(page: ft.Page, message: str, title: str = "Info"):
    """Show info notification"""
    show_notification(page, title, message, "info")
