"""
Flet Color Compatibility Module
Provides backward-compatible color constants for Flet 0.25+

This module fixes the issue where Flet 0.25+ uses Colors (capital C) 
instead of colors (lowercase), and adds missing color constants.
"""

from enum import Enum


class Colors:
    """Backward-compatible color constants for Flet"""

    # Primary colors
    PRIMARY = "#2E86AB"
    PRIMARY_CONTAINER = "#C3E7FF"
    ON_PRIMARY = "#FFFFFF"

    # Secondary colors
    SECONDARY = "#A23B72"
    SECONDARY_CONTAINER = "#FFD9E3"
    ON_SECONDARY = "#FFFFFF"

    # Tertiary colors
    TERTIARY = "#0B6E99"
    TERTIARY_CONTAINER = "#C3E7FF"
    ON_TERTIARY = "#FFFFFF"

    # Error colors
    ERROR = "#BA1A1A"
    ERROR_CONTAINER = "#FFDAD6"
    ON_ERROR = "#FFFFFF"

    # Background and surface
    BACKGROUND = "#F8F9FA"
    ON_BACKGROUND = "#1A1C1E"
    SURFACE = "#FFFFFF"
    ON_SURFACE = "#1A1C1E"
    SURFACE_VARIANT = "#E8E8E8"
    ON_SURFACE_VARIANT = "#43474E"

    # Outline
    OUTLINE = "#73777F"
    OUTLINE_VARIANT = "#C3C7CF"

    # Inverse
    INVERSE_SURFACE = "#2F3033"
    INVERSE_ON_SURFACE = "#F1F0F4"
    INVERSE_PRIMARY = "#86D1FF"

    # Standard colors (from Material Design)
    RED = "#F44336"
    PINK = "#E91E63"
    PURPLE = "#9C27B0"
    DEEP_PURPLE = "#673AB7"
    INDIGO = "#3F51B5"
    BLUE = "#2196F3"
    LIGHT_BLUE = "#03A9F4"
    CYAN = "#00BCD4"
    TEAL = "#009688"
    GREEN = "#4CAF50"
    LIGHT_GREEN = "#8BC34A"
    LIME = "#CDDC39"
    YELLOW = "#FFEB3B"
    AMBER = "#FFC107"
    ORANGE = "#FF9800"
    DEEP_ORANGE = "#FF5722"
    BROWN = "#795548"
    GREY = "#9E9E9E"
    BLUE_GREY = "#607D8B"
    BLACK = "#000000"
    WHITE = "#FFFFFF"

    # Special colors
    TRANSPARENT = "transparent"
    NONE = None

    # Additional status colors
    SUCCESS = "#4CAF50"
    WARNING = "#FFC107"
    INFO = "#2196F3"

    # Badge/status colors
    DRAFT = "#9E9E9E"
    SELF_REVIEW = "#2196F3"
    MANAGER_REVIEW = "#9C27B0"
    COMPLETED = "#4CAF50"
    ACKNOWLEDGED = "#009688"
    CANCELLED = "#F44336"

    # Chart colors
    CHART_1 = "#2196F3"
    CHART_2 = "#4CAF50"
    CHART_3 = "#FF9800"
    CHART_4 = "#9C27B0"
    CHART_5 = "#00BCD4"


# Create a singleton instance for easier use
colors = Colors()
