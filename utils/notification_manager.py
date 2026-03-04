"""
Notification Manager for Vernika HRA
Handles in-app notifications and badges across the application
Supports both per-screen notifications and global notifications
Includes banner popup bubbles, notification bell, and queue management
"""

import flet as ft
from typing import Dict, Optional, Callable, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import threading
import time


# Global notification overlay container
_global_notification_container = None
_notification_polling_thread = None
_stop_polling = False


@dataclass
class Notification:
    """Represents a notification"""
    id: str
    title: str
    message: str
    type: str = "info"  # info, success, warning, error
    timestamp: datetime = field(default_factory=datetime.now)
    read: bool = False
    action: Optional[Callable] = None
    priority: str = "medium"  # low, medium, high, urgent
    related_entity_type: str = None
    related_entity_id: int = None


class GlobalNotificationBanner:
    """Global notification banner that appears at the top of the screen"""

    def __init__(self, page: ft.Page):
        self._page = page
        self._banner: Optional[ft.Container] = None
        self._is_visible = False
        self._close_event = threading.Event()

    def _get_icon_for_type(self, notification_type: str) -> ft.Icons:
        """Get icon for notification type"""
        icons = {
            "info": ft.Icons.INFO,
            "success": ft.Icons.CHECK_CIRCLE,
            "warning": ft.Icons.WARNING,
            "error": ft.Icons.ERROR,
            "leave_request": ft.Icons.CALENDAR_TODAY,
            "leave_approved": ft.Icons.CHECK_CIRCLE,
            "leave_rejected": ft.Icons.CANCEL,
            "task_assigned": ft.Icons.ASSIGNMENT,
            "task_updated": ft.Icons.UPDATE,
            "chat_message": ft.Icons.CHAT,
            "email_received": ft.Icons.MAIL,
            "meeting_invite": ft.Icons.VIDEO_CALL,
            "announcement": ft.Icons.CAMPAIGN,
            "system": ft.Icons.INFO,
        }
        return icons.get(notification_type, ft.Icons.NOTIFICATIONS)

    def _get_color_for_type(self, notification_type: str) -> str:
        """Get color for notification type"""
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
            "leave_request": "#FF9800",
            "leave_approved": "#4CAF50",
            "leave_rejected": "#F44336",
            "task_assigned": "#2196F3",
            "task_updated": "#9C27B0",
            "chat_message": "#00BCD4",
            "email_received": "#FF5722",
            "meeting_invite": "#3F51B5",
            "announcement": "#E91E63",
            "system": "#607D8B",
        }
        return colors.get(notification_type, "#2196F3")

    def show_banner(self, title: str, message: str, notification_type: str = "info",
                    duration: int = 5, priority: str = "medium"):
        """Show a banner notification at the top of the screen"""
        # Remove any existing banner
        self._dismiss_banner(None)

        icon = self._get_icon_for_type(notification_type)
        bg_color = self._get_color_for_type(notification_type)

        # Determine text color based on background
        text_color = ft.Colors.WHITE

        # Create banner container
        self._banner = ft.Container(
            width=400,
            padding=15,
            bgcolor=bg_color,
            border_radius=12,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.BLACK38,
                offset=ft.Offset(0, 4)
            ),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        width=36,
                        height=36,
                        bgcolor=ft.Colors.WHITE24,
                        border_radius=18,
                        content=ft.Icon(icon, color=text_color, size=20),
                        alignment=ft.alignment.Alignment(0, 0)
                    ),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(
                            title,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=text_color
                        ),
                        ft.Text(
                            message,
                            size=12,
                            color=text_color,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                    ], expand=True, spacing=2),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=text_color,
                        icon_size=18,
                        on_click=self._dismiss_banner,
                    )
                ], spacing=0)
            ], tight=True),
            right=20,
            top=20,
            animate_position=300,
            animate_size=300,
            animate_opacity=200,
        )

        # Add to page overlay
        self._page.overlay.append(self._banner)
        self._is_visible = True

        try:
            self._page.update()
        except Exception as e:
            print(f"[Banner] Update error: {e}")

        # Auto-dismiss after duration seconds
        def auto_dismiss():
            time.sleep(duration)
            self._dismiss_banner(None)

        threading.Thread(target=auto_dismiss, daemon=True).start()

    def _dismiss_banner(self, e):
        """Dismiss the banner"""
        if self._banner:
            try:
                self._page.overlay.remove(self._banner)
            except:
                pass
            self._banner = None
            self._is_visible = False
            try:
                self._page.update()
            except:
                pass

    def is_visible(self) -> bool:
        """Check if banner is currently visible"""
        return self._is_visible


# GlobalNotificationOverlay removed - using banner notifications instead


class NotificationManager:
    """Manages notifications for the application"""

    def __init__(self, page: ft.Page):
        self._page = page
        self._notifications: List[Notification] = []
        self._unread_count = 0
        self._badge_callbacks: List[Callable] = []
        self._sound_enabled = True
        self._notification_callback: Optional[Callable] = None
        self._global_banner: Optional[GlobalNotificationBanner] = None

        # Notification settings
        self._settings = {
            'sound_enabled': True,
            'badge_enabled': True,
            'toast_duration': 3,  # seconds
            'show_unread_count': True,
            'banner_enabled': True,  # Enable banner notifications
            'banner_position': 'top',  # top or bottom
            'banner_duration': 5,  # seconds
        }

        # Initialize global banner (only notification type now)
        try:
            self._global_banner = GlobalNotificationBanner(page)
        except Exception as e:
            print(f"[Notification] Global banner init error: {e}")

    def set_sound_enabled(self, enabled: bool):
        """Enable or disable notification sounds"""
        self._sound_enabled = enabled
        self._settings['sound_enabled'] = enabled

    def is_sound_enabled(self) -> bool:
        """Check if sound is enabled"""
        return self._sound_enabled

    def set_badge_enabled(self, enabled: bool):
        """Enable or disable badge display"""
        self._settings['badge_enabled'] = enabled

    def is_badge_enabled(self) -> bool:
        """Check if badge is enabled"""
        return self._settings['badge_enabled']

    def get_settings(self) -> Dict:
        """Get all notification settings"""
        return self._settings.copy()

    def update_settings(self, settings: Dict):
        """Update notification settings"""
        self._settings.update(settings)
        if 'sound_enabled' in settings:
            self._sound_enabled = settings['sound_enabled']

    def add_notification(self, title: str, message: str,
                         notification_type: str = "info",
                         action: Optional[Callable] = None,
                         priority: str = "medium",
                         related_entity_type: str = None,
                         related_entity_id: int = None,
                         show_banner: bool = True) -> Notification:
        """Add a new notification"""
        import uuid
        notification = Notification(
            id=str(uuid.uuid4()),
            title=title,
            message=message,
            type=notification_type,
            action=action,
            priority=priority,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )

        self._notifications.insert(0, notification)
        self._unread_count += 1

        # Show toast notification (on current screen)
        self._show_toast(notification)

        # Show banner notification (works across all screens)
        if show_banner and self._settings.get('banner_enabled', True):
            self._show_banner_notification(notification)

        # Trigger badge callback
        self._trigger_badge_update()

        # Play sound if enabled
        if self._sound_enabled:
            self._play_notification_sound()

        return notification

    def _show_banner_notification(self, notification: Notification):
        """Show banner notification"""
        try:
            if self._global_banner:
                duration = self._settings.get('banner_duration', 5)
                self._global_banner.show_banner(
                    notification.title,
                    notification.message,
                    notification.type,
                    duration,
                    notification.priority
                )
        except Exception as e:
            print(f"[Notification] Banner show error: {e}")

    def _show_toast(self, notification: Notification):
        """Show a toast notification"""
        colors = {
            "info": ft.Colors.BLUE,
            "success": ft.Colors.GREEN,
            "warning": ft.Colors.ORANGE,
            "error": ft.Colors.RED,
        }

        bgcolor = colors.get(notification.type, ft.Colors.BLUE)

        snack = ft.SnackBar(
            content=ft.Row([
                ft.Icon(
                    self._get_icon_for_type(notification.type),
                    color=ft.Colors.WHITE,
                    size=20
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(notification.title,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            size=14),
                    ft.Text(notification.message,
                            color=ft.Colors.WHITE,
                            size=12),
                ], expand=True)
            ], spacing=0),
            bgcolor=bgcolor,
            behavior=ft.SnackBarBehavior.FLOATING,
            duration=self._settings.get('toast_duration', 3) * 1000,
            margin=10,
        )

        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _get_icon_for_type(self, notification_type: str) -> str:
        """Get icon name for notification type"""
        icons = {
            "info": ft.Icons.INFO,
            "success": ft.Icons.CHECK_CIRCLE,
            "warning": ft.Icons.WARNING,
            "error": ft.Icons.ERROR,
            "leave_request": ft.Icons.CALENDAR_TODAY,
            "leave_approved": ft.Icons.CHECK_CIRCLE,
            "leave_rejected": ft.Icons.CANCEL,
            "task_assigned": ft.Icons.ASSIGNMENT,
            "chat_message": ft.Icons.CHAT,
            "email_received": ft.Icons.MAIL,
            "meeting_invite": ft.Icons.VIDEO_CALL,
        }
        return icons.get(notification_type, ft.Icons.INFO)

    def _play_notification_sound(self):
        """Play notification sound (placeholder - Flet doesn't have native audio)"""
        # This would require a native audio library
        # For now, we'll just show the notification
        pass

    def show_badge(self, count: int, target: ft.Control = None):
        """Show badge on a control"""
        if not self._settings.get('badge_enabled', True):
            return

        # Create badge
        badge = ft.Container(
            content=ft.Text(
                str(count) if count < 100 else "99+",
                size=10,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=ft.Colors.RED,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            alignment=ft.alignment.Alignment(1, -1)
        )

        return badge

    def register_badge_callback(self, callback: Callable):
        """Register callback for badge updates"""
        self._badge_callbacks.append(callback)

    def _trigger_badge_update(self):
        """Trigger all registered badge callbacks"""
        for callback in self._badge_callbacks:
            try:
                callback(self._unread_count)
            except Exception as e:
                print(f"[Notification] Badge callback error: {e}")

    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return self._unread_count

    def mark_as_read(self, notification_id: str = None):
        """Mark notifications as read"""
        if notification_id:
            for notif in self._notifications:
                if notif.id == notification_id:
                    if not notif.read:
                        notif.read = True
                        self._unread_count = max(0, self._unread_count - 1)
                    break
        else:
            # Mark all as read
            self._unread_count = 0
            for notif in self._notifications:
                notif.read = True

        self._trigger_badge_update()

    def get_notifications(self) -> List[Notification]:
        """Get all notifications"""
        return self._notifications.copy()

    def clear_notifications(self):
        """Clear all notifications"""
        self._notifications.clear()
        self._unread_count = 0
        self._trigger_badge_update()

    def show_success(self, message: str, title: str = "Success"):
        """Show success notification"""
        return self.add_notification(title, message, "success")

    def show_error(self, message: str, title: str = "Error"):
        """Show error notification"""
        return self.add_notification(title, message, "error")

    def show_warning(self, message: str, title: str = "Warning"):
        """Show warning notification"""
        return self.add_notification(title, message, "warning")

    def show_info(self, message: str, title: str = "Info"):
        """Show info notification"""
        return self.add_notification(title, message, "info")

    # Convenience methods for specific notification types
    def show_banner_notification(self, title: str, message: str,
                                 notification_type: str = "info",
                                 duration: int = 5):
        """Show a banner notification directly"""
        try:
            if self._global_banner:
                self._global_banner.show_banner(
                    title, message, notification_type, duration)
        except Exception as e:
            print(f"[Notification] Banner error: {e}")

    def show_leave_request(self, employee_name: str, days: float):
        """Show notification for new leave request"""
        return self.add_notification(
            title="New Leave Request",
            message=f"{employee_name} requested {days} day(s) leave",
            notification_type="leave_request",
            priority="high",
            show_banner=True
        )

    def show_leave_approved(self, employee_name: str):
        """Show notification for approved leave"""
        return self.add_notification(
            title="Leave Approved",
            message=f"Your leave request has been approved",
            notification_type="leave_approved",
            priority="medium",
            show_banner=True
        )

    def show_leave_rejected(self, reason: str = ""):
        """Show notification for rejected leave"""
        msg = "Your leave request has been rejected"
        if reason:
            msg += f": {reason}"
        return self.add_notification(
            title="Leave Rejected",
            message=msg,
            notification_type="leave_rejected",
            priority="high",
            show_banner=True
        )

    def show_task_assigned(self, task_title: str, assigned_by: str):
        """Show notification for task assignment"""
        return self.add_notification(
            title="New Task Assigned",
            message=f"'{task_title}' assigned by {assigned_by}",
            notification_type="task_assigned",
            priority="medium",
            show_banner=True
        )

    def show_chat_message(self, sender_name: str, preview: str):
        """Show notification for new chat message"""
        message = preview[:50] + "..." if len(preview) > 50 else preview
        return self.add_notification(
            title=f"Message from {sender_name}",
            message=message,
            notification_type="chat_message",
            priority="high",
            show_banner=True
        )

    def show_email_received(self, sender_name: str, subject: str):
        """Show notification for new email"""
        return self.add_notification(
            title=f"Email from {sender_name}",
            message=subject,
            notification_type="email_received",
            priority="medium",
            show_banner=True
        )

    def show_meeting_invite(self, organizer_name: str, meeting_title: str):
        """Show notification for meeting invitation"""
        return self.add_notification(
            title="Meeting Invitation",
            message=f"{organizer_name} invited you to: {meeting_title}",
            notification_type="meeting_invite",
            priority="high",
            show_banner=True
        )

    def show_attendance_marked(self, employee_name: str, status: str):
        """Show notification for attendance marked"""
        return self.add_notification(
            title="Attendance Marked",
            message=f"{employee_name} marked as {status}",
            notification_type="info",
            priority="medium",
            show_banner=True
        )


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def init_notification_manager(page: ft.Page) -> NotificationManager:
    """Initialize notification manager"""
    global _notification_manager
    _notification_manager = NotificationManager(page)
    return _notification_manager


def get_notification_manager() -> Optional[NotificationManager]:
    """Get the global notification manager"""
    global _notification_manager
    return _notification_manager


def ensure_notification_manager(page: ft.Page) -> NotificationManager:
    """
    Ensure notification manager exists and is properly initialized.
    Call this after page.clean() or navigation to re-initialize notifications.
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager(page)
    else:
        # Re-initialize the global banner with the current page
        try:
            _notification_manager._page = page
            _notification_manager._global_banner = GlobalNotificationBanner(
                page)
        except Exception as e:
            print(f"[Notification] Re-init error: {e}")
    return _notification_manager


def show_toast(page: ft.Page, title: str, message: str,
               notification_type: str = "info", duration: int = 3):
    """
    Show a quick toast notification that works across all screens.
    Call this directly from any screen after navigation.
    """
    colors = {
        "info": "#2196F3",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336"
    }

    icons = {
        "info": ft.Icons.INFO,
        "success": ft.Icons.CHECK_CIRCLE,
        "warning": ft.Icons.WARNING,
        "error": ft.Icons.ERROR
    }

    bgcolor = colors.get(notification_type, colors["info"])
    icon = icons.get(notification_type, icons["info"])

    content = ft.Row([
        ft.Icon(icon, color="white", size=20),
        ft.Container(width=10),
        ft.Column([
            ft.Text(title, weight=ft.FontWeight.BOLD, color="white", size=14),
            ft.Text(message, color="white", size=12),
        ], spacing=0, expand=True)
    ], spacing=0)

    snack = ft.SnackBar(
        content=content,
        bgcolor=bgcolor,
        duration=duration * 1000,
        behavior=ft.SnackBarBehavior.FLOATING,
        margin=10,
    )

    page.overlay.append(snack)
    snack.open = True
    page.update()


def notify_success(page: ft.Page, message: str, title: str = "Success"):
    """Show success toast notification"""
    show_toast(page, title, message, "success")


def notify_error(page: ft.Page, message: str, title: str = "Error"):
    """Show error toast notification"""
    show_toast(page, title, message, "error")


def notify_warning(page: ft.Page, message: str, title: str = "Warning"):
    """Show warning toast notification"""
    show_toast(page, title, message, "warning")


def notify_info(page: ft.Page, message: str, title: str = "Info"):
    """Show info toast notification"""
    show_toast(page, title, message, "info")
