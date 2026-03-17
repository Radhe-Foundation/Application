"""
RadheFoundation HRA - Centralized Theme Constants
Use these constants throughout the application for consistent UI
"""

import flet as ft


# Primary Colors
PRIMARY = "#2E86AB"
PRIMARY_DARK = "#1A5F7A"
PRIMARY_LIGHT = "#4DA8DA"
PRIMARY_VARIENT = "#A8D4E6"

# Secondary Colors
SECONDARY = "#A23B72"
SECONDARY_DARK = "#7A2A55"
SECONDARY_LIGHT = "#C75B9A"

# Tertiary
TERTIARY = "#0B6E99"

# Background Colors
BACKGROUND = "#F8F9FA"
BACKGROUND_DARK = "#121212"
SURFACE = "#FFFFFF"
SURFACE_DARK = "#1E1E1E"
SURFACE_VARIANT = "#E8E8E8"

# Text Colors
TEXT_PRIMARY = "#212529"
TEXT_SECONDARY = "#6C757D"
TEXT_DISABLED = "#ADB5BD"
TEXT_ON_PRIMARY = "#FFFFFF"
TEXT_ON_SECONDARY = "#FFFFFF"

# Status Colors
SUCCESS = "#28A745"
SUCCESS_LIGHT = "#4CAF50"
SUCCESS_VARIENT = "#E8F5E9"

ERROR = "#DC3545"
ERROR_LIGHT = "#F44336"
ERROR_VARIENT = "#FFEBEE"

WARNING = "#FFC107"
WARNING_LIGHT = "#FF9800"
WARNING_VARIENT = "#FFF3E0"

INFO = "#17A2B8"
INFO_LIGHT = "#2196F3"
INFO_VARIENT = "#E3F2FD"

# Status-specific Colors
STATUS_ACTIVE = "#4CAF50"
STATUS_INACTIVE = "#9E9E9E"
STATUS_PENDING = "#FFC107"
STATUS_APPROVED = "#4CAF50"
STATUS_REJECTED = "#F44336"
STATUS_CANCELLED = "#9E9E9E"

# Priority Colors
PRIORITY_LOW = "#4CAF50"
PRIORITY_MEDIUM = "#FFC107"
PRIORITY_HIGH = "#FF9800"
PRIORITY_URGENT = "#F44336"

# Employment Type Colors
EMP_FULL_TIME = "#2196F3"
EMP_PART_TIME = "#FF9800"
EMP_CONTRACT = "#9C27B0"
EMP_INTERN = "#4CAF50"

# Card/Container Colors
CARD_BG = "#FFFFFF"
CARD_BG_ALT = "#F5F5F5"
CARD_SHADOW = "#00000010"

# Border Colors
BORDER_LIGHT = "#E0E0E0"
BORDER_MEDIUM = "#BDBDBD"
BORDER_DARK = "#9E9E9E"

# Table Colors
TABLE_HEADER_BG = "#F5F5F5"
TABLE_ROW_ALT = "#FAFAFA"
TABLE_ROW_HOVER = "#F0F0F0"
TABLE_BORDER = "#E0E0E0"

# Navigation Colors
NAV_BG = "#FFFFFF"
NAV_SELECTED = "#E3F2FD"
NAV_HOVER = "#F5F5F5"
NAV_TEXT_ACTIVE = PRIMARY
NAV_TEXT_INACTIVE = TEXT_SECONDARY

# Button Colors
BUTTON_PRIMARY = PRIMARY
BUTTON_SECONDARY = SECONDARY
BUTTON_SUCCESS = SUCCESS
BUTTON_ERROR = ERROR
BUTTON_WARNING = WARNING
BUTTON_INFO = INFO
BUTTON_DISABLED = "#E0E0E0"

# Icon Colors
ICON_PRIMARY = PRIMARY
ICON_SECONDARY = TEXT_SECONDARY
ICON_ERROR = ERROR
ICON_SUCCESS = SUCCESS
ICON_WARNING = WARNING

# Chart Colors (for dashboards)
CHART_COLORS = [
    "#2E86AB",  # Blue
    "#A23B72",  # Pink
    "#28A745",  # Green
    "#FFC107",  # Yellow
    "#17A2B8",  # Cyan
    "#9C27B0",  # Purple
    "#FF5722",  # Deep Orange
    "#00BCD4",  # Cyan
    "#8BC34A",  # Light Green
    "#FF9800",  # Orange
]

# Dark Theme Colors
DARK_BACKGROUND = "#121212"
DARK_SURFACE = "#1E1E1E"
DARK_SURFACE_VARIANT = "#2D2D2D"
DARK_TEXT_PRIMARY = "#FFFFFF"
DARK_TEXT_SECONDARY = "#B0B0B0"
DARK_BORDER = "#404040"


# Color helper functions
def get_color_for_status(status: str) -> str:
    """Get color for status string"""
    status_lower = str(status).lower().replace('_', '').replace(' ', '')

    status_map = {
        'active': SUCCESS,
        'inactive': ERROR,
        'pending': WARNING,
        'approved': SUCCESS,
        'rejected': ERROR,
        'cancelled': TEXT_SECONDARY,
        'completed': SUCCESS,
        'inprogress': INFO,
        'todo': TEXT_SECONDARY,
        'draft': TEXT_SECONDARY,
        'sent': INFO,
        'viewed': INFO,
        'paid': SUCCESS,
        'partial': WARNING,
        'overdue': ERROR,
    }

    return status_map.get(status_lower, TEXT_SECONDARY)


def get_color_for_priority(priority: str) -> str:
    """Get color for priority string"""
    priority_lower = str(priority).lower()

    priority_map = {
        'low': PRIORITY_LOW,
        'medium': PRIORITY_MEDIUM,
        'high': PRIORITY_HIGH,
        'urgent': PRIORITY_URGENT,
        'critical': PRIORITY_URGENT,
    }

    return priority_map.get(priority_lower, PRIORITY_MEDIUM)


def get_color_for_employment_type(emp_type: str) -> str:
    """Get color for employment type"""
    emp_type_lower = str(emp_type).lower().replace('_', '')

    type_map = {
        'fulltime': EMP_FULL_TIME,
        'parttime': EMP_PART_TIME,
        'contract': EMP_CONTRACT,
        'intern': EMP_INTERN,
    }

    return type_map.get(emp_type_lower, EMP_FULL_TIME)


def lighten_color(hex_color: str, percent: int = 20) -> str:
    """Lighten a hex color by percentage"""
    try:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        new_rgb = tuple(
            min(255, int(rgb[i] + (255 - rgb[i]) * percent / 100)) for i in range(3))

        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)
    except Exception:
        return hex_color


def darken_color(hex_color: str, percent: int = 20) -> str:
    """Darken a hex color by percentage"""
    try:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        new_rgb = tuple(
            max(0, int(rgb[i] * (100 - percent) / 100)) for i in range(3))

        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)
    except Exception:
        return hex_color


# Theme configuration for Flet
def get_light_theme() -> ft.Theme:
    """Get light theme configuration"""
    return ft.Theme(
        color_scheme_seed=PRIMARY,
        brightness=ft.ThemeMode.LIGHT,
    )


def get_dark_theme() -> ft.Theme:
    """Get dark theme configuration"""
    return ft.Theme(
        color_scheme_seed=PRIMARY,
        brightness=ft.ThemeMode.DARK,
    )


# Common styles
BUTTON_STYLE_PRIMARY = {
    "bgcolor": BUTTON_PRIMARY,
    "color": "white",
    "height": 40,
    "padding": 10,
}

BUTTON_STYLE_SECONDARY = {
    "bgcolor": BUTTON_SECONDARY,
    "color": "white",
    "height": 40,
    "padding": 10,
}

BUTTON_STYLE_SUCCESS = {
    "bgcolor": BUTTON_SUCCESS,
    "color": "white",
    "height": 40,
    "padding": 10,
}

BUTTON_STYLE_ERROR = {
    "bgcolor": BUTTON_ERROR,
    "color": "white",
    "height": 40,
    "padding": 10,
}


# Card elevation styles
CARD_ELEVATION_1 = ft.BoxShadow(
    spread_radius=1,
    blur_radius=3,
    color="#00000008"
)

CARD_ELEVATION_2 = ft.BoxShadow(
    spread_radius=1,
    blur_radius=5,
    color="#00000010"
)

CARD_ELEVATION_3 = ft.BoxShadow(
    spread_radius=1,
    blur_radius=8,
    color="#00000015"
)


# Common paddings
PADDING_SMALL = 5
PADDING_MEDIUM = 10
PADDING_LARGE = 15
PADDING_XLARGE = 20

# Common margins
MARGIN_SMALL = 5
MARGIN_MEDIUM = 10
MARGIN_LARGE = 15
MARGIN_XLARGE = 20

# Common border radius
RADIUS_SMALL = 4
RADIUS_MEDIUM = 8
RADIUS_LARGE = 12
RADIUS_XLARGE = 16
RADIUS_CIRCLE = 50


# Icon sizes
ICON_SMALL = 16
ICON_MEDIUM = 20
ICON_LARGE = 24
ICON_XLARGE = 32
ICON_XXLARGE = 48


# Text sizes
TEXT_SIZE_SMALL = 12
TEXT_SIZE_MEDIUM = 14
TEXT_SIZE_LARGE = 16
TEXT_SIZE_XLARGE = 20
TEXT_SIZE_XXLARGE = 24
TEXT_SIZE_TITLE = 28


# Input field styles
INPUT_BORDER_COLOR = "#BDBDBD"
INPUT_FOCUS_BORDER_COLOR = PRIMARY
INPUT_ERROR_BORDER_COLOR = ERROR
INPUT_BORDER_RADIUS = 8


# Data table styles
TABLE_ROW_HEIGHT = 48
TABLE_HEADER_HEIGHT = 52


# Navigation rail width
NAV_RAIL_WIDTH = 180
NAV_RAIL_WIDTH_COLLAPSED = 60


# Dialog sizes
DIALOG_WIDTH_SMALL = 350
DIALOG_WIDTH_MEDIUM = 450
DIALOG_WIDTH_LARGE = 550
DIALOG_WIDTH_XLARGE = 650

DIALOG_HEIGHT_SMALL = 200
DIALOG_HEIGHT_MEDIUM = 350
DIALOG_HEIGHT_LARGE = 450
DIALOG_HEIGHT_XLARGE = 550


# Animation durations (in milliseconds)
ANIMATION_FAST = 150
ANIMATION_NORMAL = 300
ANIMATION_SLOW = 500


# Z-index values
Z_DIALOG = 100
Z_SNACKBAR = 200
Z_TOOLTIP = 300
