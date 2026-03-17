"""
RadheFoundation HRA - Base Screen Class
Industry-Level Human Resource Management System

This module provides the base screen class that all screens should inherit from.
Fixed for Flet 0.25+
"""

from typing import Optional, Callable, Any
from dataclasses import dataclass
import flet as ft


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#28A745"
ERROR = "#DC3545"
WARNING = "#FFC107"
INFO = "#17A2B8"
BACKGROUND = "#F8F9FA"
SURFACE = "#FFFFFF"


class BaseScreen(ft.Column):
    """
    Base screen class for all application screens.
    Provides common functionality and consistent behavior.
    """

    def __init__(self, page: ft.Page, **kwargs):
        """
        Initialize base screen.

        Args:
            page: Flet page object
            **kwargs: Additional arguments passed to the parent Column
        """
        super().__init__(**kwargs)
        self._page = page
        self._user = None

    @property
    def page(self) -> ft.Page:
        """Get current page"""
        return self._page

    @property
    def user(self) -> Optional[Any]:
        """Get current user from session"""
        if hasattr(self._page, 'session'):
            return self._page.session.get("user")
        return None

    @user.setter
    def user(self, value):
        """Set current user in session"""
        if hasattr(self._page, 'session'):
            self._page.session.set("user", value)
        self._user = value

    def build(self):
        """Build the screen UI. Override in subclasses."""
        pass

    def did_mount(self):
        """Called when screen is mounted. Override in subclasses."""
        pass

    def will_unmount(self):
        """Called before screen is unmounted. Override in subclasses."""
        pass

    def on_resize(self, e):
        """Handle window resize. Override in subclasses."""
        pass

    def show_snackbar(self, message: str, duration: int = 3000, bgcolor: str = PRIMARY):
        """
        Show a snackbar notification.

        Args:
            message: Message to display
            duration: Duration in milliseconds
            bgcolor: Background color
        """
        snack = ft.SnackBar(
            content=ft.Text(message),
            duration=duration,
            bgcolor=bgcolor
        )
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_success(self, message: str):
        """Show success message"""
        self.show_snackbar(message, bgcolor=SUCCESS)

    def show_error(self, message: str):
        """Show error message"""
        self.show_snackbar(message, bgcolor=ERROR)

    def show_warning(self, message: str):
        """Show warning message"""
        self.show_snackbar(message, bgcolor=WARNING)

    def show_info(self, message: str):
        """Show info message"""
        self.show_snackbar(message, bgcolor=INFO)

    def show_dialog(self, dialog: ft.AlertDialog):
        """
        Show a dialog.

        Args:
            dialog: Dialog to show
        """
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def hide_dialog(self, dialog: ft.AlertDialog):
        """
        Hide a dialog.

        Args:
            dialog: Dialog to hide
        """
        dialog.open = False
        self._page.update()

    def navigate_to(self, route: str, **params):
        """
        Navigate to a different screen.

        Args:
            route: Route path
            **params: Additional parameters to pass
        """
        self._page.route = route
        if params:
            for key, value in params.items():
                self._page.session.set(key, value)
        self._page.update()

    def go_back(self):
        """Navigate back to previous screen"""
        if self._page.route != "/":
            self._page.go("/")

    def confirm_action(
        self,
        title: str,
        content: str,
        on_confirm: Callable,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel"
    ):
        """
        Show a confirmation dialog.

        Args:
            title: Dialog title
            content: Dialog content
            on_confirm: Callback when confirmed
            confirm_text: Confirm button text
            cancel_text: Cancel button text
        """
        def handle_confirm(e):
            dialog.open = False
            self._page.update()
            if on_confirm:
                on_confirm()

        def handle_cancel(e):
            dialog.open = False
            self._page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(content),
            actions=[
                ft.TextButton(cancel_text, on_click=handle_cancel),
                ft.ElevatedButton(
                    confirm_text,
                    on_click=handle_confirm,
                    bgcolor=PRIMARY,
                    color="WHITE"
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.show_dialog(dialog)

    def create_stat_card(
        self,
        title: str,
        value: str,
        icon: str = "stats",
        color: str = PRIMARY
    ) -> ft.Card:
        """
        Create a statistic card.

        Args:
            title: Card title
            value: Value to display
            icon: Icon name
            color: Color theme

        Returns:
            ft.Card: Stat card control
        """
        icon_map = {
            "stats": ft.Icons.PIE_CHART,
            "people": ft.Icons.PEOPLE,
            "calendar": ft.Icons.CALENDAR_MONTH,
            "check": ft.Icons.CHECK_CIRCLE,
            "warning": ft.Icons.WARNING,
            "error": ft.Icons.ERROR,
        }

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon_map.get(icon, ft.Icons.PIE_CHART),
                            size=32, color=color),
                    ft.Text(value, size=24,
                            weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(title, size=12, color="#757575"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, scroll=ft.ScrollMode.AUTO, expand=True),
                padding=20,
                width=150,
            ),
            elevation=2
        )


@dataclass
class ScreenConfig:
    """Configuration dataclass for screen properties"""
    title: str = "RadheFoundation HRA"
    icon: str = "apps"
    show_nav: bool = True
    require_auth: bool = True
    allowed_roles: list = None

    def __post_init__(self):
        if self.allowed_roles is None:
            self.allowed_roles = []


class ScreenRegistry:
    """
    Registry for managing screen instances.
    Implements singleton pattern for screen management.
    """

    _instance = None
    _screens = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, name: str, screen_class: type, config: ScreenConfig = None):
        """
        Register a screen.

        Args:
            name: Screen name
            screen_class: Screen class
            config: Screen configuration
        """
        self._screens[name] = {
            "class": screen_class,
            "config": config or ScreenConfig()
        }

    def get(self, name: str) -> Optional[type]:
        """
        Get screen class by name.

        Args:
            name: Screen name

        Returns:
            Screen class or None
        """
        return self._screens.get(name, {}).get("class")

    def get_config(self, name: str) -> ScreenConfig:
        """
        Get screen configuration by name.

        Args:
            name: Screen name

        Returns:
            ScreenConfig or default
        """
        return self._screens.get(name, {}).get("config", ScreenConfig())

    def list_screens(self) -> list:
        """
        List all registered screens.

        Returns:
            list: List of screen names
        """
        return list(self._screens.keys())


# Global screen registry instance
screen_registry = ScreenRegistry()
