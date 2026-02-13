# Vernika Application - Base Screen
# Base class for all application screens

import flet as ft
from flet import Column, Container, Row, IconButton, Text, padding
from flet import Colors
from flet import Icons
from auth.session import session_manager


class BaseScreen(Column):
    """
    Base screen class with common functionality
    All screens should inherit from this class
    """

    def __init__(self, page, *args, **kwargs):
        super().__init__()
        # Store page reference safely - don't overwrite Control.page property
        self._page_ref = page
        self.expand = True

        # Create header with user info and logout
        self.header = self._create_header()

        # Main content area (to be implemented by subclasses)
        self.content = self._create_content()

        # Add components
        self.controls = [self.header, self.content]

    @property
    def page(self):
        """Get the page reference safely"""
        return self._page_ref

    @page.setter
    def page(self, value):
        """Set the page reference"""
        self._page_ref = value

    def _create_header(self):
        """Create screen header with navigation and user info"""
        return Container(
            content=Row(
                controls=[
                    # App title
                    Text(
                        value="Vernika",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.PRIMARY
                    ),
                    # Spacer
                    Container(expand=True),

                    # User info
                    Text(
                        value=f"Welcome, {session_manager.current_user.username if session_manager.current_user else 'Guest'}",
                        size=14,
                        color=Colors.SECONDARY
                    ),

                    # User role badge
                    Text(
                        value=f"({session_manager.get_user_role()})",
                        size=12,
                        color=Colors.GREY_500
                    ),

                    # Logout button
                    IconButton(
                        icon=Icons.LOGOUT,
                        tooltip="Logout",
                        on_click=self._handle_logout,
                        icon_color=Colors.RED_500
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=padding.all(10),
            bgcolor=Colors.SURFACE,
            border=None,
            shadow=None
        )

    def _create_content(self):
        """Create main content area - override in subclasses"""
        return Container(
            content=Text("Content area - implement in subclass"),
            expand=True
        )

    def _handle_logout(self, e):
        """Handle logout button click"""
        # Clear session
        session_manager.clear_session()

        # Navigate to login screen
        from screens.login_screen import show_login
        self.page.clean()
        show_login(self.page)

    def on_navigate(self, route: str):
        """Called when navigating to this screen"""
        # Override in subclasses for custom navigation logic
        pass

    def refresh(self):
        """Refresh screen content"""
        # Override in subclasses to implement refresh logic
        self.update()
