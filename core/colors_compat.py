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

    # Blue shades
    BLUE_50 = "#E3F2FD"
    BLUE_100 = "#BBDEFB"
    BLUE_200 = "#90CAF9"
    BLUE_300 = "#64B5F6"
    BLUE_400 = "#42A5F5"
    BLUE_500 = "#2196F3"
    BLUE_600 = "#1E88E5"
    BLUE_700 = "#1976D2"
    BLUE_800 = "#1565C0"
    BLUE_900 = "#0D47A1"

    # Green shades
    GREEN_50 = "#E8F5E9"
    GREEN_100 = "#C8E6C9"
    GREEN_200 = "#A5D6A7"
    GREEN_300 = "#81C784"
    GREEN_400 = "#66BB6A"
    GREEN_500 = "#4CAF50"
    GREEN_600 = "#43A047"
    GREEN_700 = "#388E3C"
    GREEN_800 = "#2E7D32"
    GREEN_900 = "#1B5E20"

    # Red shades
    RED_50 = "#FFEBEE"
    RED_100 = "#FFCDD2"
    RED_200 = "#EF9A9A"
    RED_300 = "#E57373"
    RED_400 = "#EF5350"
    RED_500 = "#F44336"
    RED_600 = "#E53935"
    RED_700 = "#D32F2F"
    RED_800 = "#C62828"
    RED_900 = "#B71C1C"

    # Orange shades
    ORANGE_50 = "#FFF3E0"
    ORANGE_100 = "#FFE0B2"
    ORANGE_200 = "#FFCC80"
    ORANGE_300 = "#FFB74D"
    ORANGE_400 = "#FFA726"
    ORANGE_500 = "#FF9800"
    ORANGE_600 = "#FB8C00"
    ORANGE_700 = "#F57C00"
    ORANGE_800 = "#EF6C00"
    ORANGE_900 = "#E65100"

    # Grey scale (50-900) for dark theme compatibility
    GREY_50 = "#FAFAFA"
    GREY_100 = "#F5F5F5"
    GREY_200 = "#EEEEEE"
    GREY_300 = "#E0E0E0"
    GREY_400 = "#BDBDBD"
    GREY_500 = "#9E9E9E"
    GREY_600 = "#757575"
    GREY_700 = "#616161"
    GREY_800 = "#424242"
    GREY_850 = "#2D2D2D"
    GREY_900 = "#212121"

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
