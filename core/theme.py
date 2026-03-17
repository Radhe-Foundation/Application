"""
RadheFoundation HRA - Theme Configuration
Industry-Level Human Resource Management System

This module provides theme configuration and color utilities for Flet.
Fixed for Flet 0.25+
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

# Color constants for the application
PRIMARY = "#2E86AB"
PRIMARY_CONTAINER = "#C3E7FF"
ON_PRIMARY = "#FFFFFF"

SECONDARY = "#A23B72"
SECONDARY_CONTAINER = "#FFD9E3"
ON_SECONDARY = "#FFFFFF"

TERTIARY = "#0B6E99"
TERTIARY_CONTAINER = "#C3E7FF"
ON_TERTIARY = "#FFFFFF"

ERROR = "#BA1A1A"
ERROR_CONTAINER = "#FFDAD6"
ON_ERROR = "#FFFFFF"

BACKGROUND = "#F8F9FA"
ON_BACKGROUND = "#1A1C1E"
SURFACE = "#FFFFFF"
ON_SURFACE = "#1A1C1E"
SURFACE_VARIANT = "#E8E8E8"
ON_SURFACE_VARIANT = "#43474E"

OUTLINE = "#73777F"
OUTLINE_VARIANT = "#C3C7CF"

INVERSE_SURFACE = "#2F3033"
INVERSE_ON_SURFACE = "#F1F0F4"
INVERSE_PRIMARY = "#86D1FF"

# Text colors
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"
BORDER = "#E0E0E0"

# Status colors
SUCCESS = "#28A745"
WARNING = "#FFC107"
INFO = "#17A2B8"

# Dark theme colors
DARK_PRIMARY = "#86D1FF"
DARK_PRIMARY_CONTAINER = "#004C70"
DARK_ON_PRIMARY = "#00344F"

DARK_SECONDARY = "#FFB1C4"
DARK_SECONDARY_CONTAINER = "#7D294A"
DARK_ON_SECONDARY = "#5E1133"

DARK_TERTIARY = "#86D1FF"
DARK_TERTIARY_CONTAINER = "#004C70"
DARK_ON_TERTIARY = "#00344F"

DARK_ERROR = "#FFB4AB"
DARK_ERROR_CONTAINER = "#93000A"
DARK_ON_ERROR = "#690005"

DARK_BACKGROUND = "#121212"
DARK_ON_BACKGROUND = "#E2E2E6"
DARK_SURFACE = "#121212"
DARK_ON_SURFACE = "#E2E2E6"
DARK_SURFACE_VARIANT = "#1E1E1E"
DARK_ON_SURFACE_VARIANT = "#C3C7CF"

DARK_OUTLINE = "#8D9199"
DARK_OUTLINE_VARIANT = "#43474E"


class ThemeMode(Enum):
    """Theme mode enumeration"""
    LIGHT = "light"
    DARK = "dark"


class Theme:
    """Theme class for managing application theme"""

    # Public color constants
    PRIMARY = PRIMARY
    SECONDARY = SECONDARY
    SUCCESS = SUCCESS
    WARNING = WARNING
    ERROR = ERROR
    INFO = INFO

    BACKGROUND = BACKGROUND
    SURFACE = SURFACE
    ON_SURFACE = ON_SURFACE
    TEXT_PRIMARY = "#1A1C1E"
    TEXT_SECONDARY = "#6C757D"
    BORDER = "#E0E0E0"

    SPACING_SM = 8
    SPACING_MD = 16
    SPACING_LG = 24
    BORDER_RADIUS = 8

    def __init__(self, mode: ThemeMode = ThemeMode.LIGHT):
        """Initialize theme with mode"""
        self._mode = mode
        self._update_colors()

    def _update_colors(self):
        """Update colors based on mode"""
        if self._mode == ThemeMode.DARK:
            self.primary = DARK_PRIMARY
            self.primary_container = DARK_PRIMARY_CONTAINER
            self.on_primary = DARK_ON_PRIMARY
            self.secondary = DARK_SECONDARY
            self.secondary_container = DARK_SECONDARY_CONTAINER
            self.on_secondary = DARK_ON_SECONDARY
            self.error = DARK_ERROR
            self.error_container = DARK_ERROR_CONTAINER
            self.on_error = DARK_ON_ERROR
            self.background = DARK_BACKGROUND
            self.on_background = DARK_ON_BACKGROUND
            self.surface = DARK_SURFACE
            self.on_surface = DARK_ON_SURFACE
            self.surface_variant = DARK_SURFACE_VARIANT
            self.on_surface_variant = DARK_ON_SURFACE_VARIANT
            self.outline = DARK_OUTLINE
            self.outline_variant = DARK_OUTLINE_VARIANT
        else:
            self.primary = PRIMARY
            self.primary_container = PRIMARY_CONTAINER
            self.on_primary = ON_PRIMARY
            self.secondary = SECONDARY
            self.secondary_container = SECONDARY_CONTAINER
            self.on_secondary = ON_SECONDARY
            self.error = ERROR
            self.error_container = ERROR_CONTAINER
            self.on_error = ON_ERROR
            self.background = BACKGROUND
            self.on_background = ON_BACKGROUND
            self.surface = SURFACE
            self.on_surface = ON_SURFACE
            self.surface_variant = SURFACE_VARIANT
            self.on_surface_variant = ON_SURFACE_VARIANT
            self.outline = OUTLINE
            self.outline_variant = OUTLINE_VARIANT

    @property
    def mode(self):
        """Get current theme mode"""
        return self._mode

    @mode.setter
    def mode(self, value):
        """Set theme mode"""
        self._mode = value
        self._update_colors()

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self._mode = ThemeMode.DARK if self._mode == ThemeMode.LIGHT else ThemeMode.LIGHT
        self._update_colors()

    def is_dark(self):
        """Check if dark theme is active"""
        return self._mode == ThemeMode.DARK


# Create global theme instance
theme = Theme(ThemeMode.LIGHT)


def get_status_color(status: str) -> str:
    """
    Get color for a given status.

    Args:
        status: Status string (success, error, warning, info, etc.)

    Returns:
        str: Color hex code
    """
    status_colors = {
        "success": SUCCESS,
        "error": ERROR,
        "warning": WARNING,
        "info": INFO,
        "active": SUCCESS,
        "inactive": ERROR,
        "pending": WARNING,
        "approved": SUCCESS,
        "rejected": ERROR,
        "completed": SUCCESS,
        "in_progress": INFO,
        "todo": "#9E9E9E",
        "cancelled": "#757575",
    }
    return status_colors.get(status.lower(), INFO)


def get_priority_color(priority: str) -> str:
    """
    Get color for a given priority.

    Args:
        priority: Priority string (low, medium, high, urgent)

    Returns:
        str: Color hex code
    """
    priority_colors = {
        "low": SUCCESS,
        "medium": WARNING,
        "high": "#FF9800",
        "urgent": ERROR,
    }
    return priority_colors.get(priority.lower(), WARNING)


# Export for compatibility
Colors = type('Colors', (), {
    'PRIMARY': PRIMARY,
    'SECONDARY': SECONDARY,
    'SUCCESS': SUCCESS,
    'WARNING': WARNING,
    'ERROR': ERROR,
    'INFO': INFO,
    'BACKGROUND': BACKGROUND,
    'SURFACE': SURFACE,
    'TEXT_PRIMARY': TEXT_PRIMARY,
    'TEXT_SECONDARY': TEXT_SECONDARY,
    'BORDER': BORDER,
})()

Spacing = type('Spacing', (), {
    'SM': 8,
    'MD': 16,
    'LG': 24,
})()

BorderRadius = type('BorderRadius', (), {
    'ROUNDED': 8,
    'MD': 12,
})()

FontWeight = type('FontWeight', (), {
    'BOLD': 'bold',
    'NORMAL': 'normal',
    'SEMIBOLD': '600',
    'MEDIUM': '500',
})()
