"""
RadheFoundation HRA - Base Screen Classes
Provides base functionality for all screens including loading states and common operations
"""

import flet as ft
from typing import Optional, Any, Callable


class BaseScreen(ft.Container):
    """
    Base screen class with common functionality
    All screens should inherit from this class
    """

    def __init__(self, page: ft.Page, user: Any = None, **kwargs):
        super().__init__(**kwargs)
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = "#F5F5F5"

        # Loading state
        self._is_loading = False
        self._loadingOverlay = None

        # Error state
        self._error_message = None

    @property
    def page(self) -> ft.Page:
        """Get page reference"""
        return self._page

    @property
    def is_loading(self) -> bool:
        """Check if screen is loading"""
        return self._is_loading

    def show_loading(self, message: str = "Loading..."):
        """Show loading overlay"""
        if self._loadingOverlay:
            self._loadingOverlay.visible = True
            self._is_loading = True
            self._page.update()

    def hide_loading(self):
        """Hide loading overlay"""
        if self._loadingOverlay:
            self._loadingOverlay.visible = False
            self._is_loading = False
            self._page.update()

    def create_loading_overlay(self):
        """Create loading overlay - call in _build_content"""
        self._loadingOverlay = ft.Container(
            visible=False,
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
            content=ft.Column([
                ft.ProgressRing(width=50, height=50),
                ft.Text("Loading...", size=16),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            alignment=ft.alignment.Alignment(0, 0)
        )
        return self._loadingOverlay

    def show_success(self, message: str):
        """Show success snackbar"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor="#4CAF50")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_error(self, message: str):
        """Show error snackbar"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor="#F44336")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_info(self, message: str):
        """Show info snackbar"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor="#2196F3")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_warning(self, message: str):
        """Show warning snackbar"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor="#FF9800")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def close_all_dialogs(self):
        """Close all open dialogs"""
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def navigate_to_home(self):
        """Navigate to home screen based on user role"""
        from utils.navigation_helpers import safe_navigate_to_home
        safe_navigate_to_home(self._page, self.user)

    def refresh(self):
        """Override in subclass to implement refresh"""
        self._page.update()


class AdminBaseScreen(BaseScreen):
    """
    Base class for admin screens
    Provides admin-specific functionality
    """

    def __init__(self, page: ft.Page, user: Any = None, **kwargs):
        # Set default bgcolor for admin screens
        kwargs.setdefault('bgcolor', "#F5F5F5")
        super().__init__(page, user, **kwargs)

        # Navigation rail state
        self._nav_rail_visible = True

    def toggle_nav_rail(self):
        """Toggle navigation rail visibility"""
        self._nav_rail_visible = not self._nav_rail_visible
        if hasattr(self, 'content') and self.content:
            try:
                # Update visibility in content
                self.content.content.controls[0].visible = self._nav_rail_visible
                self.content.content.controls[1].visible = self._nav_rail_visible
                self._page.update()
            except Exception as e:
                print(f"Error toggling nav rail: {e}")

    def is_admin(self) -> bool:
        """Check if current user is admin"""
        if isinstance(self.user, dict):
            return self.user.get('role', '').lower() == 'admin'
        return False


class EmployeeBaseScreen(BaseScreen):
    """
    Base class for employee screens
    Provides employee-specific functionality
    """

    def __init__(self, page: ft.Page, user: Any = None, **kwargs):
        kwargs.setdefault('bgcolor', "#F5F5F5")
        super().__init__(page, user, **kwargs)

        # Get employee ID if available
        self.employee_id = None
        if self.user:
            user_id = self.user.get('id') if isinstance(
                self.user, dict) else None
            if user_id:
                try:
                    from database.operations import get_employee_by_user_id
                    from database.session_manager import get_db_session
                    db = get_db_session()
                    emp = get_employee_by_user_id(db, user_id)
                    if emp:
                        self.employee_id = int(emp.id)
                    db.close()
                except Exception as e:
                    print(f"Error getting employee ID: {e}")

    def is_admin(self) -> bool:
        """Check if current user is admin"""
        if isinstance(self.user, dict):
            return self.user.get('role', '').lower() == 'admin'
        return False


# Loading button with state
class LoadingButton(ft.Container):
    """Button with loading state"""

    def __init__(
        self,
        text: str,
        on_click: Callable,
        bgcolor: str = "#2E86AB",
        color: str = "WHITE",
        icon: Any = None,
        loading: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self._text = text
        self._on_click = on_click
        self._bgcolor = bgcolor
        self._color = color
        self._icon = icon
        self._loading = loading

        self.bgcolor = bgcolor
        self.border_radius = 8
        self.padding = 10
        self.on_click = self._handle_click

        self._build_content()

    def _build_content(self):
        if self._loading:
            content = ft.Row([
                ft.ProgressRing(width=16, height=16, color=self._color),
                ft.Text("Loading...", color=self._color)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)
        else:
            controls = []
            if self._icon:
                controls.append(self._icon)
            controls.append(ft.Text(self._text, color=self._color))
            content = ft.Row(
                controls, alignment=ft.MainAxisAlignment.CENTER, spacing=8)

        self.content = content

    def _handle_click(self, e):
        if not self._loading and self._on_click:
            self._on_click(e)

    def set_loading(self, loading: bool):
        """Set loading state"""
        self._loading = loading
        self._build_content()
        self.update()


# Data table with pagination
class PaginatedDataTable(ft.Container):
    """
    Data table with built-in pagination
    """

    def __init__(
        self,
        columns: list,
        rows: list,
        rows_per_page: int = 20,
        on_page_change: Callable = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self._columns = columns
        self._all_rows = rows
        self._rows_per_page = rows_per_page
        self._current_page = 1
        self._on_page_change = on_page_change

        self._total_pages = (len(rows) + rows_per_page - 1) // rows_per_page

        self.content = self._build()

    def _build(self):
        # Get rows for current page
        start_idx = (self._current_page - 1) * self._rows_per_page
        end_idx = start_idx + self._rows_per_page
        page_rows = self._all_rows[start_idx:end_idx]

        table = ft.DataTable(
            columns=self._columns,
            rows=page_rows
        )

        # Pagination controls
        pagination = ft.Row([
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                on_click=self._prev_page if self._current_page > 1 else None,
                disabled=self._current_page <= 1
            ),
            ft.Text(f"Page {self._current_page} of {self._total_pages}"),
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                on_click=self._next_page if self._current_page < self._total_pages else None,
                disabled=self._current_page >= self._total_pages
            ),
        ], alignment=ft.MainAxisAlignment.CENTER)

        return ft.Column([table, pagination], spacing=10)

    def _prev_page(self, e):
        if self._current_page > 1:
            self._current_page -= 1
            self.content = self._build()
            if self._on_page_change:
                self._on_page_change(self._current_page)

    def _next_page(self, e):
        if self._current_page < self._total_pages:
            self._current_page += 1
            self.content = self._build()
            if self._on_page_change:
                self._on_page_change(self._current_page)

    def update_data(self, rows: list):
        """Update table data"""
        self._all_rows = rows
        self._total_pages = max(
            1, (len(rows) + self._rows_per_page - 1) // self._rows_per_page)
        self._current_page = 1
        self.content = self._build()


# Search bar component
class SearchBar(ft.Container):
    """
    Reusable search bar component
    """

    def __init__(
        self,
        hint_text: str = "Search...",
        on_search: Callable = None,
        width: int = 300,
        **kwargs
    ):
        super().__init__(**kwargs)

        self._on_search = on_search
        self._search_field = ft.TextField(
            hint_text=hint_text,
            prefix_icon=ft.Icons.SEARCH,
            width=width,
            on_submit=self._handle_search
        )

        self.content = ft.Row([self._search_field])

    def _handle_search(self, e):
        if self._on_search:
            self._on_search(self._search_field.value)

    def get_value(self) -> str:
        """Get search value"""
        return self._search_field.value or ""

    def clear(self):
        """Clear search field"""
        self._search_field.value = ""
        self.update()


# Empty state component
class EmptyState(ft.Container):
    """
    Empty state placeholder for lists
    """

    def __init__(
        self,
        icon: Any = ft.Icons.INBOX,
        title: str = "No Data",
        message: str = "Nothing to display",
        action_text: str = None,
        on_action: Callable = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.alignment = ft.alignment.Alignment(0, 0)

        content = ft.Column([
            ft.Icon(icon, size=64, color="#BDBDBD"),
            ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
            ft.Text(message, size=14, color="#757575"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        if action_text and on_action:
            content.controls.append(
                ft.ElevatedButton(action_text, on_click=on_action)
            )

        self.content = content


# Confirmation dialog helper
def show_confirmation_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm: Callable,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    confirm_color: str = "#F44336"
):
    """Show a confirmation dialog"""

    def close_dlg(e):
        for overlay in page.overlay:
            if isinstance(overlay, ft.AlertDialog):
                overlay.open = False
        page.update()

    def handle_confirm(e):
        on_confirm()
        close_dlg(None)

    dialog = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton(cancel_text, on_click=close_dlg),
            ft.ElevatedButton(
                confirm_text,
                on_click=handle_confirm,
                style=ft.ButtonStyle(bgcolor=confirm_color, color="WHITE")
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()
