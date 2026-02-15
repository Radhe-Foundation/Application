"""
Vernika HRA - Navigation Manager
Industry-Level Human Resource Management System

This module provides navigation management for the application.
"""

from typing import Callable, Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import flet as ft


class NavigationType(Enum):
    """Navigation type enumeration"""
    DRAWER = "drawer"
    RAIL = "rail"
    TABS = "tabs"
    BOTTOM = "bottom"


@dataclass
class NavigationItem:
    """Navigation item dataclass"""
    name: str
    icon: str
    route: str
    label: str = ""
    badge: int = 0
    badge_color: str = "error"
    visible: bool = True
    children: List["NavigationItem"] = field(default_factory=list)
    on_click: Optional[Callable] = None
    tooltip: str = ""


class NavigationManager:
    """
    Manages application navigation.
    Provides consistent navigation across all screens.
    """

    def __init__(self):
        """Initialize navigation manager"""
        self._items: Dict[str, NavigationItem] = {}
        self._history: List[str] = []
        self._current_route: str = "/"
        self._on_route_change: Optional[Callable] = None

    @property
    def current_route(self) -> str:
        """Get current route"""
        return self._current_route

    @current_route.setter
    def current_route(self, value: str):
        """Set current route and add to history"""
        if value != self._current_route:
            self._history.append(self._current_route)
            self._current_route = value
            if self._on_route_change:
                self._on_route_change(value)

    @property
    def history(self) -> List[str]:
        """Get navigation history"""
        return self._history.copy()

    def can_go_back(self) -> bool:
        """Check if can go back"""
        return len(self._history) > 0

    def go_back(self) -> Optional[str]:
        """Go back to previous route"""
        if self._history:
            previous = self._history.pop()
            self._current_route = previous
            return previous
        return None

    def clear_history(self):
        """Clear navigation history"""
        self._history.clear()

    def add_item(self, item: NavigationItem):
        """
        Add a navigation item.

        Args:
            item: Navigation item to add
        """
        self._items[item.route] = item

    def get_item(self, route: str) -> Optional[NavigationItem]:
        """
        Get navigation item by route.

        Args:
            route: Route path

        Returns:
            NavigationItem or None
        """
        return self._items.get(route)

    def get_items(self) -> List[NavigationItem]:
        """
        Get all navigation items.

        Returns:
            List of navigation items
        """
        return list(self._items.values())

    def get_visible_items(self, role: str = "Employee") -> List[NavigationItem]:
        """
        Get visible navigation items for a role.

        Args:
            role: User role

        Returns:
            List of visible navigation items
        """
        items = []
        for item in self._items.values():
            if item.visible:
                # Filter by role if needed
                items.append(item)
        return items

    def remove_item(self, route: str):
        """
        Remove a navigation item.

        Args:
            route: Route path
        """
        if route in self._items:
            del self._items[route]

    def clear_items(self):
        """Clear all navigation items"""
        self._items.clear()

    def on_route_change(self, callback: Callable):
        """
        Set route change callback.

        Args:
            callback: Callback function
        """
        self._on_route_change = callback

    def build_navigation_control(
        self,
        page: ft.Page,
        nav_type: NavigationType = NavigationType.DRAWER,
        on_navigate: Optional[Callable] = None
    ) -> ft.Control:
        """
        Build navigation control based on type.

        Args:
            page: Flet page object
            nav_type: Navigation type
            on_navigate: Navigation callback

        Returns:
            Navigation control
        """
        if nav_type == NavigationType.RAIL:
            return self._build_rail_navigation(page, on_navigate)
        elif nav_type == NavigationType.TABS:
            return self._build_tabs_navigation(page, on_navigate)
        elif nav_type == NavigationType.BOTTOM:
            return self._build_bottom_nav(page, on_navigate)
        else:
            return self._build_drawer_navigation(page, on_navigate)

    def _build_drawer_navigation(
        self,
        page: ft.Page,
        on_navigate: Optional[Callable] = None
    ) -> ft.NavigationDrawer:
        """
        Build drawer navigation.

        Args:
            page: Flet page object
            on_navigate: Navigation callback

        Returns:
            NavigationDrawer control
        """
        def create_dest(item: NavigationItem) -> ft.NavigationDestination:
            dest = ft.NavigationDestination(
                icon=item.icon,
                label=item.label or item.name,
                selected_icon=item.icon,
            )
            if item.badge > 0:
                dest.badge_text = str(item.badge)
            return dest

        destinations = []
        for item in self.get_visible_items():
            if not item.children:
                destinations.append(create_dest(item))

        drawer = ft.NavigationDrawer(
            destinations=destinations,
            on_change=lambda e: self._handle_navigation(
                e, page, destinations, on_navigate
            ),
        )

        return drawer

    def _build_rail_navigation(
        self,
        page: ft.Page,
        on_navigate: Optional[Callable] = None
    ) -> ft.NavigationRail:
        """
        Build rail navigation.

        Args:
            page: Flet page object
            on_navigate: Navigation callback

        Returns:
            NavigationRail control
        """
        def create_dest(item: NavigationItem) -> ft.NavigationRailDestination:
            return ft.NavigationRailDestination(
                icon=item.icon,
                label=item.label or item.name,
                selected_icon=item.icon,
            )

        destinations = []
        for item in self.get_visible_items():
            if not item.children:
                destinations.append(create_dest(item))

        rail = ft.NavigationRail(
            destinations=destinations,
            on_change=lambda e: self._handle_navigation(
                e, page, destinations, on_navigate
            ),
            extended=False,
        )

        return rail

    def _build_tabs_navigation(
        self,
        page: ft.Page,
        on_navigate: Optional[Callable] = None
    ) -> ft.Tabs:
        """
        Build tabs navigation.

        Args:
            page: Flet page object
            on_navigate: Navigation callback

        Returns:
            Tabs control
        """
        def create_tab(icon_name, label):
            """Helper to create a Tab with proper Flet 0.25+ syntax"""
            return ft.Tab(
                tab_content=ft.Row([
                    ft.Icon(name=icon_name, size=18),
                    ft.Text(label, size=12)
                ], spacing=3)
            )

        tabs = ft.Tabs(
            tabs=[],
            on_change=lambda e: self._handle_tab_change(e, page, on_navigate),
        )

        for item in self.get_visible_items():
            if not item.children:
                tabs.tabs.append(
                    create_tab(item.icon, item.label or item.name)
                )

        return tabs

    def _build_bottom_nav(
        self,
        page: ft.Page,
        on_navigate: Optional[Callable] = None
    ) -> ft.NavigationBar:
        """
        Build bottom navigation bar.

        Args:
            page: Flet page object
            on_navigate: Navigation callback

        Returns:
            NavigationBar control
        """
        def create_dest(item: NavigationItem) -> ft.NavigationBarDestination:
            return ft.NavigationBarDestination(
                icon=item.icon,
                label=item.label or item.name,
            )

        destinations = []
        for item in self.get_visible_items():
            if not item.children:
                destinations.append(create_dest(item))

        nav_bar = ft.NavigationBar(
            destinations=destinations,
            on_change=lambda e: self._handle_navigation(
                e, page, destinations, on_navigate
            ),
        )

        return nav_bar

    def _handle_navigation(
        self,
        e: ft.ControlEvent,
        page: ft.Page,
        destinations: list,
        on_navigate: Optional[Callable]
    ):
        """
        Handle navigation event.

        Args:
            e: Control event
            page: Flet page object
            destinations: List of destinations
            on_navigate: Navigation callback
        """
        if e.control.selected_index < len(destinations):
            item = list(self._items.values())[e.control.selected_index]
            self.current_route = item.route
            if on_navigate:
                on_navigate(item.route)
            else:
                page.route = item.route
                page.update()

    def _handle_tab_change(
        self,
        e: ft.ControlEvent,
        page: ft.Page,
        on_navigate: Optional[Callable]
    ):
        """
        Handle tab change event.

        Args:
            e: Control event
            page: Flet page object
            on_navigate: Navigation callback
        """
        tab = e.control.tabs[e.control.selected_index]
        route = getattr(tab, 'route', None)
        if route:
            self.current_route = route
            if on_navigate:
                on_navigate(route)
            else:
                page.route = route
                page.update()

    def update_badge(self, route: str, count: int):
        """
        Update badge count for a route.

        Args:
            route: Route path
            count: New badge count
        """
        item = self.get_item(route)
        if item:
            item.badge = count

    def show_badge(self, route: str, count: int = 1):
        """
        Show badge for a route.

        Args:
            route: Route path
            count: Badge count
        """
        self.update_badge(route, count)

    def hide_badge(self, route: str):
        """
        Hide badge for a route.

        Args:
            route: Route path
        """
        self.update_badge(route, 0)


# Global navigation manager instance
navigation = NavigationManager()


# Predefined navigation items for Vernika HRA
def create_default_navigation() -> NavigationManager:
    """
    Create default navigation items for Vernika HRA.

    Returns:
        NavigationManager with default items
    """
    nav = NavigationManager()

    # Admin navigation
    admin_items = [
        NavigationItem(
            name="Dashboard",
            icon="dashboard",
            route="/admin/dashboard",
            label="Dashboard",
        ),
        NavigationItem(
            name="Employees",
            icon="people",
            route="/admin/employees",
            label="Employees",
        ),
        NavigationItem(
            name="Departments",
            icon="business",
            route="/admin/departments",
            label="Departments",
        ),
        NavigationItem(
            name="Positions",
            icon="badge",
            route="/admin/positions",
            label="Positions",
        ),
        NavigationItem(
            name="Attendance",
            icon="event",
            route="/admin/attendance",
            label="Attendance",
        ),
        NavigationItem(
            name="Leave",
            icon="event_busy",
            route="/admin/leaves",
            label="Leave",
        ),
        NavigationItem(
            name="Tasks",
            icon="task",
            route="/admin/tasks",
            label="Tasks",
        ),
        NavigationItem(
            name="Performance",
            icon="trending_up",
            route="/admin/performance",
            label="Performance",
        ),
        NavigationItem(
            name="Documents",
            icon="description",
            route="/admin/documents",
            label="Documents",
        ),
        NavigationItem(
            name="Announcements",
            icon="campaign",
            route="/admin/announcements",
            label="Announcements",
        ),
        NavigationItem(
            name="Reports",
            icon="assessment",
            route="/admin/reports",
            label="Reports",
        ),
        NavigationItem(
            name="Settings",
            icon="settings",
            route="/admin/settings",
            label="Settings",
        ),
    ]

    # Employee navigation
    employee_items = [
        NavigationItem(
            name="Dashboard",
            icon="dashboard",
            route="/employee/dashboard",
            label="Dashboard",
        ),
        NavigationItem(
            name="My Profile",
            icon="person",
            route="/employee/profile",
            label="My Profile",
        ),
        NavigationItem(
            name="My Attendance",
            icon="event",
            route="/employee/attendance",
            label="Attendance",
        ),
        NavigationItem(
            name="My Leave",
            icon="event_busy",
            route="/employee/leaves",
            label="Leave",
        ),
        NavigationItem(
            name="My Tasks",
            icon="task",
            route="/employee/tasks",
            label="Tasks",
        ),
        NavigationItem(
            name="Documents",
            icon="description",
            route="/employee/documents",
            label="Documents",
        ),
    ]

    # Add items to navigation manager
    for item in admin_items + employee_items:
        nav.add_item(item)

    return nav


# Initialize default navigation
navigation = create_default_navigation()


# ============================================================================
# HELPER FUNCTIONS FOR ROLE-BASED NAVIGATION
# ============================================================================

def get_user_role(user_data) -> str:
    """
    Extract user role from user data dictionary or object.

    Args:
        user_data: User data dictionary or object with 'role' attribute

    Returns:
        str: User role in lowercase ('admin' or 'employee')
    """
    if user_data is None:
        return 'employee'

    if isinstance(user_data, dict):
        return str(user_data.get('role', 'employee')).lower()
    else:
        # It's an object with attributes
        return str(getattr(user_data, 'role', 'employee')).lower()


def navigate_to_home(page: ft.Page, user_data):
    """
    Navigate user to their home screen based on role.
    Admin users go to AdminScreen, employees go to EmployeeScreen.

    Args:
        page: Flet page object
        user_data: User data dictionary or object
    """
    role = get_user_role(user_data)

    if role == 'admin':
        from screens.admin_screen import AdminScreen
        page.clean()
        page.add(AdminScreen(page, user_data))
    else:
        from screens.employee_screen import EmployeeScreen
        page.clean()
        page.add(EmployeeScreen(page, user_data))


def navigate_to_admin(page: ft.Page, user_data):
    """
    Navigate to AdminScreen (for admin users).

    Args:
        page: Flet page object
        user_data: User data dictionary or object
    """
    from screens.admin_screen import AdminScreen
    page.clean()
    page.add(AdminScreen(page, user_data))
