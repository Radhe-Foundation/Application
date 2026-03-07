"""
Vernika HRA - Web Helpers
Helper functions for web deployment including asset handling and responsive design
"""

import os
import flet as ft
from typing import Optional

# Flag to detect if running in web mode
_is_web_mode = False


def set_web_mode(enabled: bool):
    """Set web mode flag"""
    global _is_web_mode
    _is_web_mode = enabled


def is_web_mode() -> bool:
    """Check if running in web mode"""
    return _is_web_mode


def get_asset_path(relative_path: str) -> str:
    """
    Get the proper asset path for web deployment.
    In web mode, assets should be served from the root with / prefix.
    In desktop mode, use relative paths.
    """
    # Normalize path
    path = relative_path.replace("\\", "/")

    # Ensure it starts with / for web
    if not path.startswith("/"):
        path = "/" + path

    return path


def get_logo_path() -> str:
    """Get the Vernika logo path - works in both desktop and web"""
    return get_asset_path("assets/logo/Vernikalogo.png")


def get_profile_photo_path(filename: str) -> str:
    """Get profile photo path"""
    return get_asset_path(f"assets/profile_photos/{filename}")


# Responsive breakpoints
class Breakpoints:
    """Screen size breakpoints"""
    MOBILE = 600
    TABLET = 900
    DESKTOP = 1200
    LARGE = 1400


def get_screen_size(page: ft.Page) -> str:
    """Get current screen size category"""
    width = page.window_width if hasattr(page, 'window_width') else 1200

    if width < Breakpoints.MOBILE:
        return "mobile"
    elif width < Breakpoints.TABLET:
        return "tablet"
    elif width < Breakpoints.DESKTOP:
        return "laptop"
    else:
        return "desktop"


def is_mobile(page: ft.Page) -> bool:
    """Check if current device is mobile"""
    return get_screen_size(page) == "mobile"


def is_tablet(page: ft.Page) -> bool:
    """Check if current device is tablet"""
    return get_screen_size(page) == "tablet"


def is_desktop(page: ft.Page) -> bool:
    """Check if current device is desktop"""
    return get_screen_size(page) in ["desktop", "laptop"]


# Responsive dimensions
class ResponsiveDim:
    """Responsive dimension helpers"""

    @staticmethod
    def sidebar_width(page: ft.Page) -> int:
        """Get appropriate sidebar width based on screen size"""
        width = page.window_width if hasattr(page, 'window_width') else 1200

        if width < Breakpoints.MOBILE:
            return 0  # Hidden on mobile
        elif width < Breakpoints.TABLET:
            return 60  # Collapsed icon-only on tablet
        elif width < Breakpoints.DESKTOP:
            return 140
        else:
            return 180

    @staticmethod
    def content_padding(page: ft.Page) -> int:
        """Get appropriate content padding"""
        width = page.window_width if hasattr(page, 'window_width') else 1200

        if width < Breakpoints.MOBILE:
            return 8
        elif width < Breakpoints.TABLET:
            return 12
        else:
            return 20

    @staticmethod
    def card_width(page: ft.Page) -> Optional[int]:
        """Get appropriate card width"""
        width = page.window_width if hasattr(page, 'window_width') else 1200

        if width < Breakpoints.MOBILE:
            return None  # Full width
        elif width < Breakpoints.TABLET:
            return 200
        else:
            return None  # Auto

    @staticmethod
    def icon_size(page: ft.Page) -> float:
        """Get appropriate icon size"""
        width = page.window_width if hasattr(page, 'window_width') else 1200

        if width < Breakpoints.MOBILE:
            return 20.0
        elif width < Breakpoints.TABLET:
            return 22.0
        else:
            return 24.0

    @staticmethod
    def font_size(page: ft.Page, base_size: float) -> float:
        """Get scaled font size"""
        width = page.window_width if hasattr(page, 'window_width') else 1200

        if width < Breakpoints.MOBILE:
            return base_size * 0.85
        elif width < Breakpoints.TABLET:
            return base_size * 0.92
        else:
            return base_size

    @staticmethod
    def button_height(page: ft.Page) -> int:
        """Get appropriate button height"""
        width = page.window_width if hasattr(page, 'window_width') else 1200

        if width < Breakpoints.MOBILE:
            return 40
        elif width < Breakpoints.TABLET:
            return 45
        else:
            return 50


def adaptive_value(page: ft.Page, mobile_val, tablet_val, desktop_val):
    """Get value based on screen size"""
    size = get_screen_size(page)
    if size == "mobile":
        return mobile_val
    elif size == "tablet":
        return tablet_val
    else:
        return desktop_val


def responsive_row(controls: list, page: ft.Page,
                   mobile_spacing: int = 10,
                   tablet_spacing: int = 15,
                   desktop_spacing: int = 20) -> ft.Row:
    """Create a responsive row with adaptive spacing"""
    return ft.Row(
        controls,
        spacing=adaptive_value(page, mobile_spacing,
                               tablet_spacing, desktop_spacing),
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True
    )


def responsive_column(controls: list, page: ft.Page,
                      mobile_spacing: int = 10,
                      tablet_spacing: int = 15,
                      desktop_spacing: int = 20) -> ft.Column:
    """Create a responsive column with adaptive spacing"""
    return ft.Column(
        controls,
        spacing=adaptive_value(page, mobile_spacing,
                               tablet_spacing, desktop_spacing),
        alignment=ft.MainAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )


# Mobile-friendly navigation rail
class MobileNavRail:
    """Mobile navigation rail that works on all screen sizes"""

    @staticmethod
    def create_nav_rail(page: ft.Page, destinations: list, selected_index: int, on_change) -> ft.Container:
        """Create responsive navigation rail"""
        width = ResponsiveDim.sidebar_width(page)

        # Hide on mobile
        if width == 0:
            return ft.Container(visible=False)

        # Create navigation items
        nav_items = []
        for dest in destinations:
            nav_items.append(
                ft.NavigationRailDestination(
                    icon=dest.get("icon_outlined", ft.Icons.CIRCLE_OUTLINED),
                    selected_icon=dest.get("icon", ft.Icons.CIRCLE),
                    label=dest.get("label", ""),
                )
            )

        return ft.Container(
            width=width,
            content=ft.NavigationRail(
                selected_index=selected_index,
                on_change=on_change,
                destinations=nav_items,
                label_type=ft.NavigationRailLabelType.ALL if width > 80 else ft.NavigationRailLabelType.NONE,
            ),
            visible=width > 0,
        )


# Responsive container that adapts to screen size
class ResponsiveContainer:
    """Container that adapts to screen size"""

    @staticmethod
    def create(page: ft.Page, content,
               mobile_width: float = 1.0,
               tablet_width: float = 0.9,
               desktop_width: float = 0.8) -> ft.Container:
        """Create responsive container"""
        width_fraction = adaptive_value(
            page, mobile_width, tablet_width, desktop_width)

        return ft.Container(
            content=content,
            width=page.window_width *
            width_fraction if hasattr(page, 'window_width') else 800,
            alignment=ft.alignment.Alignment(0, 0),
        )


# Detect if running in browser/web
def is_browser() -> bool:
    """Check if running in a browser environment"""
    try:
        import js
        return True
    except ImportError:
        return False
