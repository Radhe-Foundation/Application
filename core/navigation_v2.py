"""
Navigation Helper Module - Fixed Version
Provides navigation stack functionality with proper back button support
and screen state management.
"""

import flet as ft
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import copy


@dataclass
class ScreenState:
    """Represents a screen's state in the navigation stack"""
    name: str
    screen_class: Any
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    scroll_position: float = 0.0
    form_data: Dict[str, Any] = field(default_factory=dict)


class NavigationManager:
    """
    Centralized navigation manager for the application.
    Handles screen transitions, back navigation, and state preservation.
    """

    def __init__(self, page: ft.Page):
        self._page = page
        self._nav_stack: List[ScreenState] = []
        self._current_screen: Optional[ScreenState] = None
        self._screen_instances: Dict[str, Any] = {}  # Cache screen instances
        self._navigation_callbacks: List[Callable] = []

    @property
    def page(self) -> ft.Page:
        return self._page

    @property
    def can_go_back(self) -> bool:
        """Check if there's a previous screen to go back to"""
        return len(self._nav_stack) > 0

    @property
    def current_screen_name(self) -> Optional[str]:
        """Get the current screen name"""
        return self._current_screen.name if self._current_screen else None

    @property
    def stack_size(self) -> int:
        """Get the current navigation stack size"""
        return len(self._nav_stack)

    def register_callback(self, callback: Callable):
        """Register a callback for navigation changes"""
        self._navigation_callbacks.append(callback)

    def _notify_callbacks(self):
        """Notify all registered callbacks of navigation change"""
        for callback in self._navigation_callbacks:
            try:
                callback(self)
            except Exception as e:
                print(f"Navigation callback error: {e}")

    def push(self, screen_name: str, screen_content, params: Dict[str, Any] = None):
        """
        Push a new screen onto the navigation stack.

        Args:
            screen_name: Unique identifier for the screen
            screen_content: The screen content (Flet control)
            params: Optional parameters to pass to the screen
        """
        # Save current screen state if exists
        if self._current_screen:
            self._nav_stack.append(self._current_screen)

        # Create new screen state
        self._current_screen = ScreenState(
            name=screen_name,
            screen_class=screen_content,
            params=params or {}
        )

        # Navigate to new screen
        self._page.clean()
        self._page.add(screen_content)
        self._notify_callbacks()

        print(
            f"Navigation: Pushed '{screen_name}'. Stack size: {len(self._nav_stack)}")

    def replace(self, screen_name: str, screen_content, params: Dict[str, Any] = None):
        """
        Replace the current screen without adding to history.
        Used for redirects (e.g., after login).

        Args:
            screen_name: Unique identifier for the screen
            screen_content: The screen content
            params: Optional parameters
        """
        # Don't save current screen to history (replacement)
        self._current_screen = ScreenState(
            name=screen_name,
            screen_class=screen_content,
            params=params or {}
        )

        self._page.clean()
        self._page.add(screen_content)
        self._notify_callbacks()

        print(f"Navigation: Replaced with '{screen_name}'")

    def pop(self) -> bool:
        """
        Pop the previous screen from the navigation stack.

        Returns:
            True if successful, False if stack is empty
        """
        if not self._nav_stack:
            print("Navigation: Stack empty, cannot pop")
            return False

        # Get previous screen
        prev_screen = self._nav_stack.pop()

        # Restore current from stack
        if self._current_screen:
            # Move current back to cache or create new instance if needed
            pass

        self._current_screen = prev_screen

        # Navigate to previous screen
        self._page.clean()
        self._page.add(prev_screen.screen_class)
        self._notify_callbacks()

        print(
            f"Navigation: Popped back to '{prev_screen.name}'. Stack size: {len(self._nav_stack)}")
        return True

    def go_back(self, user_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Go back one step in navigation, or to appropriate home screen if stack is empty.

        Args:
            user_data: Optional user data for determining home screen

        Returns:
            True if navigated back, False if went to home
        """
        if self._nav_stack:
            # We have history, go back
            return self.pop()
        else:
            # No history, navigate to home based on role
            self.navigate_to_home(user_data)
            return False

    def navigate_to_home(self, user_data: Optional[Dict[str, Any]] = None):
        """
        Navigate to admin or employee screen based on user role.

        Args:
            user_data: Optional user data dict or User model
        """
        # Clear the navigation stack
        self.clear_stack()

        # Get user role
        user_role = None
        if user_data:
            if isinstance(user_data, dict):
                user_role = user_data.get('role', '').lower()
            else:
                user_role = getattr(user_data, 'role', None)
                if user_role:
                    user_role = user_role.lower()

        # Navigate based on role
        self._page.clean()

        if user_role == 'admin':
            from screens.admin_screen import AdminScreen
            self._page.add(AdminScreen(self._page, user_data))
        else:
            from screens.employee_screen import EmployeeScreen
            self._page.add(EmployeeScreen(self._page, user_data))

        print(f"Navigation: Went to home (role: {user_role})")
        self._notify_callbacks()

    def clear_stack(self):
        """Clear the navigation stack"""
        self._nav_stack = []
        self._current_screen = None
        self._screen_instances.clear()
        print("Navigation: Stack cleared")

    def get_navigation_history(self) -> List[Dict[str, Any]]:
        """
        Get the navigation history as a list.

        Returns:
            List of screen info dictionaries
        """
        history = []

        if self._current_screen:
            history.append({
                'name': self._current_screen.name,
                'timestamp': self._current_screen.timestamp.isoformat(),
                'is_current': True
            })

        for i, screen in enumerate(reversed(self._nav_stack)):
            history.append({
                'name': screen.name,
                'timestamp': screen.timestamp.isoformat(),
                'is_current': False,
                'depth': i + 1
            })

        return history


# Global navigation manager instance
_nav_manager: Optional[NavigationManager] = None


def init_navigation(page: ft.Page) -> NavigationManager:
    """Initialize navigation manager for a page"""
    global _nav_manager
    _nav_manager = NavigationManager(page)
    return _nav_manager


def get_navigation_manager(page: ft.Page = None) -> Optional[NavigationManager]:
    """Get the current navigation manager"""
    global _nav_manager
    if _nav_manager is None and page is not None:
        _nav_manager = init_navigation(page)
    return _nav_manager


# Legacy functions for backward compatibility

def push_screen(page: ft.Page, screen_name: str, screen_content):
    """Legacy push screen function"""
    manager = get_navigation_manager(page)
    if manager:
        manager.push(screen_name, screen_content)
    else:
        # Fallback to old behavior
        page.clean()
        page.add(screen_content)


def pop_screen(page: ft.Page) -> bool:
    """Legacy pop screen function"""
    manager = get_navigation_manager(page)
    if manager:
        return manager.pop()
    return False


def go_back(page: ft.Page, user=None):
    """Legacy go back function"""
    manager = get_navigation_manager(page)
    if manager:
        manager.go_back(user)
    else:
        # Fallback to old behavior
        from core.navigation import navigate_to_home
        navigate_to_home(page, user)


def can_go_back() -> bool:
    """Check if can go back"""
    global _nav_manager
    return _nav_manager.can_go_back if _nav_manager else False


def clear_stack():
    """Clear navigation stack"""
    global _nav_manager
    if _nav_manager:
        _nav_manager.clear_stack()


def navigate_to_home(page: ft.Page, user=None):
    """Navigate to home screen"""
    manager = get_navigation_manager(page)
    if manager:
        manager.navigate_to_home(user)
    else:
        # Fallback
        from screens.login_screen import LoginScreen
        from screens.admin_screen import AdminScreen
        from screens.employee_screen import EmployeeScreen

        user_role = None
        if isinstance(user, dict):
            user_role = user.get('role', '').lower()

        page.clean()
        if user_role == 'admin':
            page.add(AdminScreen(page, user))
        else:
            page.add(EmployeeScreen(page, user))


def get_stack_size() -> int:
    """Get navigation stack size"""
    global _nav_manager
    return _nav_manager.stack_size if _nav_manager else 0


class BackButton(ft.Container):
    """A reusable back button component with proper navigation"""

    def __init__(self, page: ft.Page, on_click: Callable = None,
                 show_text: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._page = page
        self._on_click = on_click

        # Get navigation manager
        self._nav_manager = get_navigation_manager(page)

        # Build button content
        content = [ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=kwargs.get('icon_color', '#2E86AB'),
            on_click=self._handle_click,
            tooltip="Go Back"
        )]

        if show_text:
            content.append(ft.Text(
                "Back",
                color=kwargs.get('icon_color', '#2E86AB'),
                size=14
            ))

        self.content = ft.Row(content, spacing=5)
        self.alignment = ft.alignment.Alignment(-1, 0)

    def _handle_click(self, e):
        if self._on_click:
            self._on_click(e)
        elif self._nav_manager:
            # Use navigation manager
            if not self._nav_manager.pop():
                # Couldn't pop, try go_back
                self._nav_manager.go_back()
        else:
            # Fallback to legacy behavior
            pop_screen(self._page)


class NavigationHeader(ft.Container):
    """A header with optional back button"""

    def __init__(self, page: ft.Page, title: str, show_back_button: bool = False,
                 on_back_click: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self._page = page
        self._show_back = show_back_button
        self._on_back = on_back_click
        self._nav_manager = get_navigation_manager(page)

        controls = []

        if show_back_button:
            controls.append(
                BackButton(
                    page,
                    on_click=self._handle_back if not on_back_click else on_back_click,
                    show_text=False,
                    icon_color=kwargs.get('icon_color', '#2E86AB')
                )
            )

        controls.append(
            ft.Text(
                title,
                size=kwargs.get('title_size', 20),
                weight=ft.FontWeight.BOLD,
                color=kwargs.get('title_color', '#2E86AB'),
                expand=True
            )
        )

        self.content = ft.Row(
            controls,
            alignment=ft.MainAxisAlignment.START if show_back_button else ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.padding = kwargs.get('padding', 15)
        self.bgcolor = kwargs.get('bgcolor', '#FFFFFF')


class ScreenRefreshMixin:
    """
    Mixin class to add refresh functionality to screens.
    Use this for screens that need periodic data refresh.
    """

    def __init__(self):
        self._refresh_interval = 30  # seconds
        self._auto_refresh_enabled = False
        self._last_refresh_time = None
        self._refresh_timer = None

    def enable_auto_refresh(self, interval_seconds: int = 30):
        """
        Enable automatic refresh.

        Args:
            interval_seconds: How often to refresh (default 30s)
        """
        self._refresh_interval = interval_seconds
        self._auto_refresh_enabled = True
        self._start_refresh_timer()

    def disable_auto_refresh(self):
        """Disable automatic refresh"""
        self._auto_refresh_enabled = False
        self._stop_refresh_timer()

    def _start_refresh_timer(self):
        """Start the refresh timer"""
        if self._refresh_timer:
            return

        def timer_callback():
            if self._auto_refresh_enabled:
                try:
                    self.refresh_data()
                except Exception as e:
                    print(f"Auto-refresh error: {e}")

        # Note: Flet doesn't have native timer, this would need threading
        # For now, this is a placeholder
        pass

    def _stop_refresh_timer(self):
        """Stop the refresh timer"""
        if self._refresh_timer:
            self._refresh_timer = None

    def refresh_data(self):
        """
        Override this method to implement actual data refresh.
        Called automatically when auto-refresh is enabled.
        """
        self._last_refresh_time = datetime.now()
        print(f"{self.__class__.__name__}: Data refreshed at {self._last_refresh_time}")

    def manual_refresh(self, e=None):
        """Handle manual refresh button click"""
        self.refresh_data()
        if hasattr(self, '_page'):
            self._page.update()
