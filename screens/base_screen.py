"""
Vernika - Base Screen Class
Provides common functionality for all screens including:
- Proper session management
- Automatic data refresh
- Loading states
- Error handling
"""

from utils.cache import get_cache, SessionCache
from database.session_manager import get_session, get_db_session, check_db_connection
import flet as ft
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseScreen(ft.Container):
    """
    Base class for all screens in the application.
    Provides common functionality for database operations,
    caching, and UI management.
    """

    def __init__(self, page: ft.Page, user_data: Dict[str, Any] = None, **kwargs):
        super().__init__(**kwargs)
        self._page = page
        self._user_data = user_data or {}
        self._is_loading = False
        self._error_message = None
        self._last_refresh = None

        # Initialize
        self.expand = True
        self.bgcolor = "#F5F5F5"

    @property
    def page(self) -> ft.Page:
        return self._page

    @property
    def user_data(self) -> Dict[str, Any]:
        return self._user_data

    @property
    def user_id(self) -> int:
        return self._user_data.get('id') or self._user_data.get('user_id')

    @property
    def user_role(self) -> str:
        role = self._user_data.get('role', 'employee')
        if hasattr(role, 'name'):
            return role.name
        return str(role).lower()

    @property
    def is_admin(self) -> bool:
        return self.user_role == 'admin'

    # ==================== Database Operations ====================

    def with_session(self, operation: Callable, *args, **kwargs):
        """
        Execute a database operation with proper session management.

        Usage:
            result = self.with_session(session.query, User)

        Args:
            operation: Function that takes session as first argument
            *args, **kwargs: Additional arguments for the operation

        Returns:
            Result of the operation
        """
        with get_session() as session:
            return operation(session, *args, **kwargs)

    def query(self, model, *filters):
        """
        Simple query wrapper with session management.

        Usage:
            users = self.query(User, User.is_active == True)
        """
        with get_session() as session:
            return session.query(model).filter(*filters).all()

    def get_or_none(self, model, id: int):
        """Get a single record by ID"""
        with get_session() as session:
            return session.query(model).get(id)

    def save(self, obj):
        """Save an object to database"""
        with get_session() as session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj

    def delete(self, obj):
        """Delete an object from database"""
        with get_session() as session:
            session.delete(obj)
            session.commit()

    # ==================== Cache Operations ====================

    def get_cached(self, key: str, default=None):
        """Get value from cache"""
        cache = get_cache()
        value = cache.get(key)
        return value if value is not None else default

    def set_cached(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        cache = get_cache()
        cache.set(key, value, ttl)

    def invalidate_cache(self, pattern: str = None, key: str = None):
        """Invalidate cache"""
        cache = get_cache()
        if key:
            cache.delete(key)
        if pattern:
            cache.invalidate_pattern(pattern)

    # ==================== UI State Management ====================

    def show_loading(self, show: bool = True):
        """Show or hide loading indicator"""
        self._is_loading = show
        if hasattr(self, '_loading_indicator'):
            self._loading_indicator.visible = show
        if hasattr(self, 'content') and self.content:
            # Rebuild content or update
            pass
        self._page.update()

    def show_error(self, message: str):
        """Show error message"""
        self._error_message = message
        if hasattr(self, '_error_text'):
            self._error_text.value = message
            self._error_text.visible = True
        self._page.update()

    def hide_error(self):
        """Hide error message"""
        self._error_message = None
        if hasattr(self, '_error_text'):
            self._error_text.visible = False
        self._page.update()

    def show_snackbar(self, message: str, is_error: bool = False):
        """Show a snackbar message"""
        try:
            bgcolor = "#DC3545" if is_error else "#323232"
            snack = ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor)
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
        except Exception as e:
            logger.error(f"Snackbar error: {e}")

    # ==================== Refresh Functionality ====================

    def refresh(self):
        """
        Refresh the screen data.
        Override this in subclasses to implement custom refresh logic.
        """
        self._last_refresh = datetime.now()
        logger.info(
            f"{self.__class__.__name__} refreshed at {self._last_refresh}")

        # Update UI if needed
        if hasattr(self, '_page'):
            self._page.update()

    def should_refresh(self, max_age_seconds: int = 30) -> bool:
        """
        Check if screen should be refreshed.

        Args:
            max_age_seconds: Maximum age before refresh needed

        Returns:
            True if refresh is needed
        """
        if self._last_refresh is None:
            return True

        age = (datetime.now() - self._last_refresh).total_seconds()
        return age > max_age_seconds

    # ==================== Database Health ====================

    def check_database_connection(self) -> bool:
        """Check if database connection is healthy"""
        return check_db_connection()

    def ensure_database_connection(self) -> bool:
        """
        Ensure database connection is available.
        Shows error dialog if not connected.
        """
        if not self.check_database_connection():
            self._show_connection_error()
            return False
        return True

    def _show_connection_error(self):
        """Show connection error dialog"""
        def close_and_restart(e):
            self._page.dialog = None
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Database Connection Error"),
            content=ft.Column([
                ft.Icon(ft.Icons.WARNING, size=48, color="#DC3545"),
                ft.Container(height=10),
                ft.Text("Unable to connect to the database."),
                ft.Text("Please check your internet connection and try again."),
            ]),
            actions=[
                ft.TextButton("Close", on_click=close_and_restart),
                ft.ElevatedButton(
                    "Retry",
                    on_click=lambda e: (
                        setattr(self._page.dialog, 'open', False),
                        self.refresh() if self.ensure_database_connection() else None,
                        self._page.update()
                    )
                )
            ]
        )
        self._page.dialog = dlg
        dlg.open = True
        self._page.update()

    # ==================== Navigation ====================

    def navigate_to(self, screen_name: str, screen_class, **params):
        """Navigate to another screen"""
        try:
            from core.navigation_v2 import get_navigation_manager

            nav_manager = get_navigation_manager(self._page)
            if nav_manager:
                nav_manager.push(screen_name, screen_class(
                    **params) if params else screen_class(self._page, self._user_data))
            else:
                # Fallback
                self._page.clean()
                self._page.add(screen_class(self._page, self._user_data))
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            self.show_snackbar(f"Navigation error: {str(e)}", is_error=True)

    def go_back(self):
        """Go back to previous screen"""
        try:
            from core.navigation_v2 import get_navigation_manager

            nav_manager = get_navigation_manager(self._page)
            if nav_manager:
                nav_manager.go_back(self._user_data)
            else:
                from core.navigation import go_back
                go_back(self._page, self._user_data)
        except Exception as e:
            logger.error(f"Go back error: {e}")
            # Fallback to login
            from screens.login_screen import LoginScreen
            self._page.clean()
            self._page.add(LoginScreen(self._page))

    # ==================== Logout ====================

    def logout(self, e=None):
        """Handle logout"""
        # Clear session cache
        SessionCache.clear()

        # Clear user data
        self._user_data = {}

        # Navigate to login
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))


class LoadingContainer(ft.Container):
    """
    Container that shows loading indicator while data is being loaded.
    """

    def __init__(self, content: ft.Control = None, loading_message: str = "Loading...", **kwargs):
        super().__init__(**kwargs)
        self._content = content
        self._loading_message = loading_message
        self._is_loading = False

        self.content = self._build_content()

    def _build_content(self):
        """Build the content based on loading state"""
        if self._is_loading:
            return ft.Container(
                content=ft.Column([
                    ft.ProgressRing(width=40, height=40),
                    ft.Text(self._loading_message, size=14, color="#6C757D")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )
        elif self._content:
            return self._content
        else:
            return ft.Container()

    def set_loading(self, is_loading: bool):
        """Set loading state"""
        self._is_loading = is_loading
        self.content = self._build_content()

    def set_content(self, content: ft.Control):
        """Set the content to display when not loading"""
        self._content = content
        if not self._is_loading:
            self.content = content


class ErrorContainer(ft.Container):
    """
    Container that shows error message with retry option.
    """

    def __init__(self, error_message: str = None, on_retry: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self._error_message = error_message or "An error occurred"
        self._on_retry = on_retry

        self.content = self._build_content()

    def _build_content(self):
        """Build error display"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color="#DC3545"),
                ft.Container(height=10),
                ft.Text(self._error_message, size=14, color="#DC3545",
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=15),
                ft.ElevatedButton(
                    "Retry",
                    icon=ft.Icons.REFRESH,
                    on_click=self._handle_retry,
                    style=ft.ButtonStyle(bgcolor="#2E86AB", color="white")
                ) if self._on_retry else ft.Container()
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.Alignment(0, 0),
            padding=30
        )

    def _handle_retry(self, e):
        """Handle retry button click"""
        if self._on_retry:
            self._on_retry(e)

    def set_error(self, message: str):
        """Set error message"""
        self._error_message = message
        self.content = self._build_content()


class RefreshContainer(ft.Container):
    """
    Container with pull-to-refresh and manual refresh button.
    """

    def __init__(self, content: ft.Control, on_refresh: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self._content = content
        self._on_refresh = on_refresh

        self.content = self._build_content()

    def _build_content(self):
        """Build content with refresh button"""
        return ft.Column([
            # Refresh button row
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Refresh",
                        on_click=self._handle_refresh
                    )
                ]),
                alignment=ft.alignment.Alignment(1, 0)
            ),
            # Main content
            self._content
        ])

    def _handle_refresh(self, e):
        """Handle refresh"""
        if self._on_refresh:
            self._on_refresh(e)


# Utility functions

def create_loading_view(message: str = "Loading...") -> ft.Container:
    """Create a simple loading view"""
    return ft.Container(
        content=ft.Column([
            ft.ProgressRing(width=50, height=50),
            ft.Container(height=15),
            ft.Text(message, size=14, color="#6C757D")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.Alignment(0, 0),
        expand=True,
        padding=50
    )


def create_error_view(message: str, on_retry: Callable = None) -> ft.Container:
    """Create a simple error view"""
    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color="#DC3545"),
            ft.Container(height=10),
            ft.Text(message, size=14, color="#DC3545",
                    text_align=ft.TextAlign.CENTER),
            ft.Container(height=15),
            ft.ElevatedButton(
                "Retry",
                icon=ft.Icons.REFRESH,
                on_click=on_retry,
                style=ft.ButtonStyle(bgcolor="#2E86AB", color="white")
            ) if on_retry else ft.Container()
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.Alignment(0, 0),
        expand=True,
        padding=50
    )


def create_empty_view(message: str, icon=ft.Icons.INBOX, action_button=None) -> ft.Container:
    """Create a simple empty state view"""
    return ft.Container(
        content=ft.Column([
            ft.Icon(icon, size=64, color="#BDBDBD"),
            ft.Container(height=15),
            ft.Text(message, size=14, color="#757575"),
            ft.Container(height=15),
            action_button or ft.Container()
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.Alignment(0, 0),
        expand=True,
        padding=50
    )
