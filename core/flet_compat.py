"""
Flet Compatibility Module
Provides backward-compatible constants and wrappers for Flet 0.25+
Handles differences between Flet versions for icons, colors, button styles, etc.
"""

import flet as ft
from typing import Optional, Any

# Try to import from flet, fall back to compatibility layer
try:
    # Flet 0.25+ style imports
    from flet import Icons as _Icons
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False

try:
    from flet import Colors as _Colors
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

try:
    from flet import FontWeight as _FontWeight
    FONTWEIGHT_AVAILABLE = True
except ImportError:
    FONTWEIGHT_AVAILABLE = False

try:
    from flet import TextAlign as _TextAlign
    TEXTALIGN_AVAILABLE = True
except ImportError:
    TEXTALIGN_AVAILABLE = False

try:
    from flet import MainAxisAlignment as _MainAxisAlignment
    MAINAXIS_AVAILABLE = True
except ImportError:
    MAINAXIS_AVAILABLE = False

try:
    from flet import CrossAxisAlignment as _CrossAxisAlignment
    CROSSAXIS_AVAILABLE = True
except ImportError:
    CROSSAXIS_AVAILABLE = False

try:
    from flet import ButtonStyle as _ButtonStyle
    BUTTONSTYLE_AVAILABLE = True
except ImportError:
    BUTTONSTYLE_AVAILABLE = False

try:
    from flet import ScrollMode as _ScrollMode
    SCROLLMODE_AVAILABLE = True
except ImportError:
    SCROLLMODE_AVAILABLE = False

try:
    from flet import ClipBehavior as _ClipBehavior
    CLIPBEHAVIOR_AVAILABLE = True
except ImportError:
    CLIPBEHAVIOR_AVAILABLE = False

try:
    from flet import InputBorder as _InputBorder
    INPUTBORDER_AVAILABLE = True
except ImportError:
    INPUTBORDER_AVAILABLE = False

try:
    from flet import KeyboardType as _KeyboardType
    KEYBOARDTYPE_AVAILABLE = True
except ImportError:
    KEYBOARDTYPE_AVAILABLE = False

try:
    from flet import BlendMode as _BlendMode
    BLENDMODE_AVAILABLE = True
except ImportError:
    BLENDMODE_AVAILABLE = False

try:
    from flet import BoxShape as _BoxShape
    BOXSHAPE_AVAILABLE = True
except ImportError:
    BOXSHAPE_AVAILABLE = False


class Icons:
    """Icon constants compatible with all Flet versions"""

    # Communication
    CHAT = "chat" if not ICONS_AVAILABLE else _Icons.CHAT
    EMAIL = "email" if not ICONS_AVAILABLE else _Icons.EMAIL
    PHONE = "phone" if not ICONS_AVAILABLE else _Icons.PHONE
    VIDEO_CALL = "video_call" if not ICONS_AVAILABLE else _Icons.VIDEO_CALL
    EVENT = "event" if not ICONS_AVAILABLE else _Icons.EVENT
    SCHEDULE = "schedule" if not ICONS_AVAILABLE else _Icons.SCHEDULE

    # People
    PEOPLE = "people" if not ICONS_AVAILABLE else _Icons.PEOPLE
    PERSON = "person" if not ICONS_AVAILABLE else _Icons.PERSON
    GROUPS = "groups" if not ICONS_AVAILABLE else _Icons.GROUPS
    GROUP_ADD = "group_add" if not ICONS_AVAILABLE else _Icons.GROUP_ADD

    # Files/Documents
    FOLDER = "folder" if not ICONS_AVAILABLE else _Icons.FOLDER
    DESCRIPTION = "description" if not ICONS_AVAILABLE else _Icons.DESCRIPTION
    IMAGE = "image" if not ICONS_AVAILABLE else _Icons.IMAGE
    UPLOAD_FILE = "upload_file" if not ICONS_AVAILABLE else _Icons.UPLOAD_FILE
    DOWNLOAD = "download" if not ICONS_AVAILABLE else _Icons.DOWNLOAD
    ATTACH_FILE = "attach_file" if not ICONS_AVAILABLE else _Icons.ATTACH_FILE

    # Actions
    ADD = "add" if not ICONS_AVAILABLE else _Icons.ADD
    CREATE = "create" if not ICONS_AVAILABLE else _Icons.CREATE
    SEND = "send" if not ICONS_AVAILABLE else _Icons.SEND
    ARROW_BACK = "arrow_back" if not ICONS_AVAILABLE else _Icons.ARROW_BACK

    # UI
    EMOJI_EMOTIONS = "emoji_emotions" if not ICONS_AVAILABLE else _Icons.EMOJI_EMOTIONS


class Colors:
    """Color constants compatible with all Flet versions"""

    # Primary
    PRIMARY = "#2E86AB"
    ON_PRIMARY = "#FFFFFF"
    PRIMARY_CONTAINER = "#C3E7FF"
    ON_PRIMARY_CONTAINER = "#001D35"

    # Secondary
    SECONDARY = "#A23B72"
    ON_SECONDARY = "#FFFFFF"
    SECONDARY_CONTAINER = "#FFD9E3"
    ON_SECONDARY_CONTAINER = "#3D001F"

    # Surface
    SURFACE = "#FFFFFF"
    ON_SURFACE = "#1A1C1E"
    SURFACE_VARIANT = "#E8E8E8"
    ON_SURFACE_VARIANT = "#43474E"

    # Background
    BACKGROUND = "#F8F9FA"
    ON_BACKGROUND = "#1A1C1E"

    # Outline
    OUTLINE = "#73777F"
    OUTLINE_VARIANT = "#C3C7CF"

    # Standard colors
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

    # Status
    ERROR = "#BA1A1A"
    SUCCESS = "#4CAF50"
    WARNING = "#FFC107"
    INFO = "#2196F3"

    # Special
    TRANSPARENT = "transparent"
    NONE = None


class FontWeight:
    """Font weight constants compatible with all Flet versions"""

    NORMAL = "normal" if not FONTWEIGHT_AVAILABLE else _FontWeight.NORMAL
    BOLD = "bold" if not FONTWEIGHT_AVAILABLE else _FontWeight.BOLD
    W_100 = "w100" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_100
    W_200 = "w200" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_200
    W_300 = "w300" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_300
    W_400 = "w400" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_400
    W_500 = "w500" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_500
    W_600 = "w600" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_600
    W_700 = "w700" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_700
    W_800 = "w800" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_800
    W_900 = "w900" if not FONTWEIGHT_AVAILABLE else _FontWeight.W_900


class TextAlign:
    """Text alignment constants compatible with all Flet versions"""

    LEFT = "left" if not TEXTALIGN_AVAILABLE else _TextAlign.LEFT
    RIGHT = "right" if not TEXTALIGN_AVAILABLE else _TextAlign.RIGHT
    CENTER = "center" if not TEXTALIGN_AVAILABLE else _TextAlign.CENTER
    START = "start" if not TEXTALIGN_AVAILABLE else _TextAlign.START
    END = "end" if not TEXTALIGN_AVAILABLE else _TextAlign.END
    JUSTIFY = "justify" if not TEXTALIGN_AVAILABLE else _TextAlign.JUSTIFY


class MainAxisAlignment:
    """Main axis alignment constants compatible with all Flet versions"""

    START = "start" if not MAINAXIS_AVAILABLE else _MainAxisAlignment.START
    END = "end" if not MAINAXIS_AVAILABLE else _MainAxisAlignment.END
    CENTER = "center" if not MAINAXIS_AVAILABLE else _MainAxisAlignment.CENTER
    SPACE_BETWEEN = "space_between" if not MAINAXIS_AVAILABLE else _MainAxisAlignment.SPACE_BETWEEN
    SPACE_AROUND = "space_around" if not MAINAXIS_AVAILABLE else _MainAxisAlignment.SPACE_AROUND
    SPACE_EVENLY = "space_evenly" if not MAINAXIS_AVAILABLE else _MainAxisAlignment.SPACE_EVENLY


class CrossAxisAlignment:
    """Cross axis alignment constants compatible with all Flet versions"""

    START = "start" if not CROSSAXIS_AVAILABLE else _CrossAxisAlignment.START
    END = "end" if not CROSSAXIS_AVAILABLE else _CrossAxisAlignment.END
    CENTER = "center" if not CROSSAXIS_AVAILABLE else _CrossAxisAlignment.CENTER
    STRETCH = "stretch" if not CROSSAXIS_AVAILABLE else _CrossAxisAlignment.STRETCH
    BASELINE = "baseline" if not CROSSAXIS_AVAILABLE else _CrossAxisAlignment.BASELINE


class ScrollMode:
    """Scroll mode constants compatible with all Flet versions"""

    NONE = None if not SCROLLMODE_AVAILABLE else getattr(
        _ScrollMode, 'NONE', None)
    AUTO = "auto" if not SCROLLMODE_AVAILABLE else getattr(
        _ScrollMode, 'AUTO', "auto")
    ADAPTIVE = "adaptive" if not SCROLLMODE_AVAILABLE else getattr(
        _ScrollMode, 'ADAPTIVE', "adaptive")
    ALWAYS = "always" if not SCROLLMODE_AVAILABLE else getattr(
        _ScrollMode, 'ALWAYS', "always")
    HIDDEN = "hidden" if not SCROLLMODE_AVAILABLE else getattr(
        _ScrollMode, 'HIDDEN', "hidden")


class ClipBehavior:
    """Clip behavior constants compatible with all Flet versions"""

    NONE = None if not CLIPBEHAVIOR_AVAILABLE else _ClipBehavior.NONE
    ANTI_ALIAS = "antiAlias" if not CLIPBEHAVIOR_AVAILABLE else _ClipBehavior.ANTI_ALIAS
    ANTI_ALIAS_WITH_SAVE_LAYER = "antiAliasWithSaveLayer" if not CLIPBEHAVIOR_AVAILABLE else _ClipBehavior.ANTI_ALIAS_WITH_SAVE_LAYER
    HARD_EDGE = "hardEdge" if not CLIPBEHAVIOR_AVAILABLE else _ClipBehavior.HARD_EDGE


class InputBorder:
    """Input border constants compatible with all Flet versions"""

    OUTLINE = "outline" if not INPUTBORDER_AVAILABLE else _InputBorder.OUTLINE
    UNDERLINE = "underline" if not INPUTBORDER_AVAILABLE else _InputBorder.UNDERLINE
    NONE = None if not INPUTBORDER_AVAILABLE else _InputBorder.NONE


class KeyboardType:
    """Keyboard type constants compatible with all Flet versions"""

    TEXT = "text" if not KEYBOARDTYPE_AVAILABLE else _KeyboardType.TEXT
    NUMBER = "number" if not KEYBOARDTYPE_AVAILABLE else _KeyboardType.NUMBER
    PHONE = "phone" if not KEYBOARDTYPE_AVAILABLE else _KeyboardType.PHONE
    EMAIL = "email" if not KEYBOARDTYPE_AVAILABLE else _KeyboardType.EMAIL
    URL = "url" if not KEYBOARDTYPE_AVAILABLE else _KeyboardType.URL
    MULTILINE = "multiline" if not KEYBOARDTYPE_AVAILABLE else _KeyboardType.MULTILINE


class BlendMode:
    """Blend mode constants compatible with all Flet versions"""

    SRC_OVER = "srcOver" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'SRC_OVER', "srcOver")
    SRC_IN = "srcIn" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'SRC_IN', "srcIn")
    SRC_OUT = "srcOut" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'SRC_OUT', "srcOut")
    SRC_ATOP = "srcATop" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'SRC_ATOP', "srcATop")
    DST_OVER = "dstOver" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'DST_OVER', "dstOver")
    DST_IN = "dstIn" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'DST_IN', "dstIn")
    DST_OUT = "dstOut" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'DST_OUT', "dstOut")
    DST_ATOP = "dstATop" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'DST_ATOP', "dstATop")
    PLUS = "plus" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'PLUS', "plus")
    MODULATE = "modulate" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'MODULATE', "modulate")
    SCREEN = "screen" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'SCREEN', "screen")
    OVERLAY = "overlay" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'OVERLAY', "overlay")
    DARKEN = "darken" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'DARKEN', "darken")
    LIGHTEN = "lighten" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'LIGHTEN', "lighten")
    COLOR_DODGE = "colorDodge" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'COLOR_DODGE', "colorDodge")
    COLOR_BURN = "colorBurn" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'COLOR_BURN', "colorBurn")
    HARD_LIGHT = "hardLight" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'HARD_LIGHT', "hardLight")
    SOFT_LIGHT = "softLight" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'SOFT_LIGHT', "softLight")
    DIFFERENCE = "difference" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'DIFFERENCE', "difference")
    EXCLUSION = "exclusion" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'EXCLUSION', "exclusion")
    MULTIPLY = "multiply" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'MULTIPLY', "multiply")
    HUE = "hue" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'HUE', "hue")
    SATURATION = "saturation" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'SATURATION', "saturation")
    COLOR = "color" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'COLOR', "color")
    LUMINOSITY = "luminosity" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'LUMINOSITY', "luminosity")
    CLEAR = "clear" if not BLENDMODE_AVAILABLE else getattr(
        _BlendMode, 'CLEAR', "clear")


class BoxShape:
    """Box shape constants compatible with all Flet versions"""

    RECTANGLE = "rectangle" if not BOXSHAPE_AVAILABLE else _BoxShape.RECTANGLE
    CIRCLE = "circle" if not BOXSHAPE_AVAILABLE else _BoxShape.CIRCLE


def create_button_style(
    color: Optional[str] = None,
    bgcolor: Optional[str] = None,
    overlay_color: Optional[str] = None,
    shadow_color: Optional[str] = None,
    elevation: Optional[float] = None,
    animation_duration: Optional[int] = None,
    padding: Optional[Any] = None,
    side: Optional[Any] = None,
    shape: Optional[Any] = None,
    alignment: Optional[Any] = None,
    enable_feedback: Optional[bool] = None,
    text_style: Optional[Any] = None,
    icon_size: Optional[float] = None,
    icon_color: Optional[str] = None,
    visual_density: Optional[Any] = None,
    mouse_cursor: Optional[Any] = None
) -> Any:
    """
    Create a ButtonStyle with compatibility for all Flet versions.
    Falls back to simple dict if ButtonStyle class is not available.
    """
    if not BUTTONSTYLE_AVAILABLE:
        # Return a simple dict for older Flet versions
        style_dict = {}
        if color is not None:
            style_dict['color'] = color
        if bgcolor is not None:
            style_dict['bgcolor'] = bgcolor
        if elevation is not None:
            style_dict['elevation'] = elevation
        return style_dict

    # Use native ButtonStyle for newer Flet versions
    kwargs = {}
    if color is not None:
        kwargs['color'] = color
    if bgcolor is not None:
        kwargs['bgcolor'] = bgcolor
    if overlay_color is not None:
        kwargs['overlay_color'] = overlay_color
    if shadow_color is not None:
        kwargs['shadow_color'] = shadow_color
    if elevation is not None:
        kwargs['elevation'] = elevation
    if animation_duration is not None:
        kwargs['animation_duration'] = animation_duration
    if padding is not None:
        kwargs['padding'] = padding
    if side is not None:
        kwargs['side'] = side
    if shape is not None:
        kwargs['shape'] = shape
    if alignment is not None:
        kwargs['alignment'] = alignment
    if enable_feedback is not None:
        kwargs['enable_feedback'] = enable_feedback
    if text_style is not None:
        kwargs['text_style'] = text_style
    if icon_size is not None:
        kwargs['icon_size'] = icon_size
    if icon_color is not None:
        kwargs['icon_color'] = icon_color
    if visual_density is not None:
        kwargs['visual_density'] = visual_density
    if mouse_cursor is not None:
        kwargs['mouse_cursor'] = mouse_cursor

    try:
        return _ButtonStyle(**kwargs)
    except Exception as e:
        # If ButtonStyle fails, return kwargs as dict
        print(f"Warning: ButtonStyle creation failed: {e}")
        return kwargs


# Convenience imports for common Flet components
def safe_import_flet_component(name: str):
    """Safely import a Flet component, returning None if not available"""
    try:
        return getattr(ft, name)
    except AttributeError:
        print(f"Warning: Flet component '{name}' not available")
        return None


# Export all compatibility classes
__all__ = [
    'Icons',
    'Colors',
    'FontWeight',
    'TextAlign',
    'MainAxisAlignment',
    'CrossAxisAlignment',
    'ScrollMode',
    'ClipBehavior',
    'InputBorder',
    'KeyboardType',
    'BlendMode',
    'BoxShape',
    'create_button_style',
    'safe_import_flet_component',
]
