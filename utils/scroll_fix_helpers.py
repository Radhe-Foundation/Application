"""
Comprehensive Fix for Scrolling Issues in CRM, Inventory, Invoicing, and Asset Management Screens
This fixes the "fixed screen" issue where content doesn't scroll properly.
"""

import flet as ft


def fix_screen_scrolling(content_column):
    """
    Wrap a content Column with proper scrolling settings.
    Use this to fix any screen that has scrolling issues.
    """
    return ft.Container(
        content=ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            controls=[content_column]
        ),
        expand=True,
    )


def create_scrollable_content(controls, spacing=10, padding=20):
    """
    Create a properly scrollable content container.

    Args:
        controls: List of controls to include in the scrollable area
        spacing: Spacing between controls
        padding: Padding around the content

    Returns:
        A properly configured scrollable Container
    """
    return ft.Container(
        content=ft.ListView(
            expand=True,
            spacing=spacing,
            padding=padding,
            controls=controls
        ),
        expand=True,
    )


def create_card_list_view(controls, height=None):
    """
    Create a scrollable list of cards.

    Args:
        controls: List of card controls
        height: Optional fixed height (if not provided, expands to fill)

    Returns:
        A Container with scrollable ListView
    """
    container = ft.Container(
        content=ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            controls=controls if controls else [
                ft.Text("No items", color="#999")
            ]
        ),
        expand=True,
    )

    if height:
        container.height = height

    return container


def create_fixed_height_scrollable(controls, height=400):
    """
    Create a container with fixed height that scrolls internally.

    Args:
        controls: List of controls
        height: Fixed height for the container

    Returns:
        A Container with fixed height and internal scrolling
    """
    return ft.Container(
        content=ft.ListView(
            expand=True,
            spacing=8,
            padding=10,
            controls=controls
        ),
        height=height,
        expand=False,
    )


def create_stats_row(cards):
    """
    Create a row of stat cards that wraps if needed.
    """
    return ft.Container(
        content=ft.Wrap(
            controls=cards,
            spacing=15,
            run_spacing=15,
        ),
        padding=15,
    )


def create_filter_bar(controls):
    """
    Create a standard filter bar container.
    """
    return ft.Container(
        content=ft.Row(
            controls=controls,
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=15,
        bgcolor="#FFFFFF",
        border=ft.border.only(
            bottom=ft.border.BorderSide(1, "#E5E7EB")
        ),
    )


def create_tab_navigation(tabs, current_tab, on_tab_change):
    """
    Create horizontal tab navigation.

    Args:
        tabs: List of (tab_id, label, icon) tuples
        current_tab: Currently selected tab ID
        on_tab_change: Callback function for tab changes
    """
    return ft.Container(
        bgcolor="#FFFFFF",
        border=ft.border.only(
            bottom=ft.border.BorderSide(1, "#E5E7EB")
        ),
        padding=ft.padding.symmetric(horizontal=20, vertical=8),
        content=ft.Row([
            _create_tab_button(tab_id, label, icon, current_tab, on_tab_change)
            for tab_id, label, icon in tabs
        ], spacing=10),
    )


def _create_tab_button(tab_id, label, icon, current_tab, on_tab_change):
    """Create a single tab button."""
    is_selected = current_tab == tab_id
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=18,
                    color="#1E3A5F" if is_selected else "#6B7280"),
            ft.Text(label, size=14,
                    weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.NORMAL,
                    color="#1E3A5F" if is_selected else "#6B7280"),
        ], spacing=8),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        border_radius=8,
        bgcolor="#1E3A5F15" if is_selected else "transparent",
        on_click=lambda e: on_tab_change(tab_id),
        ink=True,
    )


# Theme colors for consistency
THEME = {
    "PRIMARY": "#1E3A5F",
    "SUCCESS": "#00C853",
    "ERROR": "#FF1744",
    "WARNING": "#FF9100",
    "INFO": "#2979FF",
    "BACKGROUND": "#F5F7FA",
    "SURFACE": "#FFFFFF",
    "TEXT_PRIMARY": "#1A1A2E",
    "TEXT_SECONDARY": "#6B7280",
    "BORDER_COLOR": "#E5E7EB",
}


def get_theme_color(key):
    """Get theme color by key."""
    return THEME.get(key, "#000000")
