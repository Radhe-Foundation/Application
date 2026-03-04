"""
Vernika HRA - Page Overlay Cleanup Utilities
Provides functions to clean up FilePickers and other overlay elements
when navigating between screens to prevent stale component errors.
"""

import flet as ft
from typing import Optional


def cleanup_file_pickers(page: ft.Page) -> None:
    """
    Clean up all FilePicker instances from the page overlay.
    This should be called before navigating to a new screen to prevent
    stale FilePicker errors.

    Args:
        page: The Flet page to clean up
    """
    if not page or not hasattr(page, 'overlay'):
        return

    file_pickers_to_remove = []

    try:
        for item in page.overlay:
            if isinstance(item, ft.FilePicker):
                file_pickers_to_remove.append(item)
    except Exception as e:
        print(f"Error scanning overlay for FilePickers: {e}")
        return

    # Remove all FilePickers
    for fp in file_pickers_to_remove:
        try:
            page.overlay.remove(fp)
            print(f"[Cleanup] Removed FilePicker from overlay")
        except Exception as e:
            print(f"Error removing FilePicker from overlay: {e}")


def cleanup_all_pickers(page: ft.Page) -> None:
    """
    Clean up all picker instances from the page overlay.
    This includes FilePicker, DatePicker, TimePicker, ColorPicker, etc.

    Args:
        page: The Flet page to clean up
    """
    if not page or not hasattr(page, 'overlay'):
        return

    pickers_to_remove = []
    picker_types = (ft.FilePicker, ft.DatePicker, ft.TimePicker,
                    ft.CupertinoDatePicker, ft.CupertinoTimerPicker)

    try:
        for item in page.overlay:
            if isinstance(item, picker_types):
                pickers_to_remove.append(item)
    except Exception as e:
        print(f"Error scanning overlay for pickers: {e}")
        return

    # Remove all pickers
    for picker in pickers_to_remove:
        try:
            page.overlay.remove(picker)
            print(f"[Cleanup] Removed {type(picker).__name__} from overlay")
        except Exception as e:
            print(f"Error removing {type(picker).__name__} from overlay: {e}")


def cleanup_snackbars(page: ft.Page) -> None:
    """
    Clean up all open SnackBars from the page overlay.

    Args:
        page: The Flet page to clean up
    """
    if not page or not hasattr(page, 'overlay'):
        return

    snackbars_to_remove = []

    try:
        for item in page.overlay:
            if isinstance(item, ft.SnackBar):
                snackbars_to_remove.append(item)
    except Exception as e:
        print(f"Error scanning overlay for SnackBars: {e}")
        return

    for snack in snackbars_to_remove:
        try:
            page.overlay.remove(snack)
        except Exception:
            pass


def setup_page_overlay_cleanup(page: ft.Page) -> None:
    """
    Set up automatic overlay cleanup when navigating.
    This adds a route change handler that cleans up old pickers
    before showing a new screen.

    Args:
        page: The Flet page to set up cleanup for
    """
    if not page or not hasattr(page, 'overlay'):
        return

    # Store the original on_route_change if exists
    original_route_change = getattr(page, 'on_route_change', None)

    def cleanup_on_route_change(e):
        """Handler that cleans up overlay before route change"""
        # Clean up pickers before navigation
        cleanup_all_pickers(page)

        # Also close any open dialogs
        close_all_dialogs(page)

        # Call original handler if exists
        if original_route_change:
            try:
                original_route_change(e)
            except Exception as ex:
                print(f"Error in original route change handler: {ex}")

    page.on_route_change = cleanup_on_route_change


def close_all_dialogs(page: ft.Page) -> None:
    """
    Close all open dialogs on the page.

    Args:
        page: The Flet page to close dialogs on
    """
    if not page or not hasattr(page, 'overlay'):
        return

    try:
        for item in page.overlay:
            if isinstance(item, ft.AlertDialog) and hasattr(item, 'open') and item.open:
                item.open = False
            elif isinstance(item, ft.Container):
                # Check if it's a dialog container
                if hasattr(item, 'open') and item.open:
                    item.open = False
    except Exception as e:
        print(f"Error closing dialogs: {e}")


def safe_navigate_with_cleanup(page: ft.Page, screen_content) -> None:
    """
    Safely navigate to a new screen with proper overlay cleanup.

    Args:
        page: The Flet page
        screen_content: The new screen content to add
    """
    # Clean up overlays before navigation
    cleanup_all_pickers(page)
    close_all_dialogs(page)

    # Perform navigation
    page.clean()
    page.add(screen_content)


def get_overlay_debug_info(page: ft.Page) -> dict:
    """
    Get debug information about current overlay items.
    Useful for troubleshooting overlay-related issues.

    Args:
        page: The Flet page

    Returns:
        Dictionary with debug information
    """
    info = {
        'overlay_count': 0,
        'file_pickers': 0,
        'date_pickers': 0,
        'time_pickers': 0,
        'snackbars': 0,
        'dialogs': 0,
        'other': 0
    }

    if not page or not hasattr(page, 'overlay'):
        return info

    try:
        info['overlay_count'] = len(page.overlay)

        for item in page.overlay:
            if isinstance(item, ft.FilePicker):
                info['file_pickers'] += 1
            elif isinstance(item, ft.DatePicker):
                info['date_pickers'] += 1
            elif isinstance(item, ft.TimePicker):
                info['time_pickers'] += 1
            elif isinstance(item, ft.SnackBar):
                info['snackbars'] += 1
            elif isinstance(item, ft.AlertDialog):
                info['dialogs'] += 1
            else:
                info['other'] += 1
    except Exception as e:
        print(f"Error getting overlay debug info: {e}")

    return info
