"""
Vernika HRA - UI Helper Utilities
Common utilities for UI improvements including debounce, loading states, and helpers
"""

import flet as ft
import time
from typing import Callable, Any, Optional
from functools import wraps


# ==================== DEBOUNCE UTILITY ====================

class Debouncer:
    """
    Debouncer class to limit the rate of function calls.
    Useful for search inputs and other frequently triggered events.
    """

    def __init__(self, delay: float = 0.5):
        """
        Initialize debouncer

        Args:
            delay: Time in seconds to wait before executing the function
        """
        self.delay = delay
        self._timer = None
        self._callback = None
        self._args = None
        self._kwargs = None

    def __call__(self, func: Callable) -> Callable:
        """Use as decorator"""
        @wraps(func)
        def debounced(*args, **kwargs):
            # Cancel previous timer if exists
            if self._timer:
                self._timer.cancel()

            # Store the callback and arguments
            self._callback = lambda: func(*args, **kwargs)
            self._args = args
            self._kwargs = kwargs

            # Schedule new timer
            def execute():
                if self._callback:
                    self._callback()
                self._timer = None

            # Use a simple approach - store the callback and call it after delay
            # In Flet, we can't use threading directly, so we use a simple counter
            self._call_id = getattr(self, '_call_id', 0) + 1
            call_id = self._call_id

            def delayed_call():
                if call_id == getattr(self, '_call_id', 0):
                    if self._callback:
                        self._callback()

            # Schedule execution
            import threading
            self._timer = threading.Timer(self.delay, delayed_call)
            self._timer.start()

        return debounced

    def cancel(self):
        """Cancel any pending execution"""
        if self._timer:
            self._timer.cancel()
            self._timer = None


def debounce(delay: float = 0.5):
    """
    Decorator to debounce a function call.

    Usage:
        @debounce(delay=0.3)
        def my_search_function(query):
            # This will only execute 300ms after the last call
            pass
    """
    def decorator(func: Callable) -> Callable:
        debouncer = Debouncer(delay=delay)
        return debouncer(func)
    return decorator


def create_debounced_textfield(
    label: str = "Search...",
    hint_text: str = "Type to search...",
    width: float = 300,
    on_debounce: Callable[[str], None] = None,
    delay: float = 0.5,
    prefix_icon: Any = ft.Icons.SEARCH,
    **kwargs
) -> ft.TextField:
    """
    Create a text field with built-in debouncing.

    Args:
        label: Label for the text field
        hint_text: Hint text
        width: Width of the text field
        on_debounce: Callback function that receives the debounced search text
        delay: Debounce delay in seconds
        prefix_icon: Icon to display
        **kwargs: Additional arguments for TextField

    Returns:
        A TextField with debouncing enabled
    """
    # State to track the debounce timer
    timer_ref = [None]
    call_id_ref = [0]

    def on_change(e):
        query = e.control.value

        # Cancel previous timer
        if timer_ref[0]:
            timer_ref[0].cancel()

        # Increment call ID to track latest call
        call_id_ref[0] += 1
        current_call_id = call_id_ref[0]

        def execute_callback():
            # Only execute if this is still the latest call
            if current_call_id == call_id_ref[0] and on_debounce:
                on_debounce(query)

        # Schedule new timer
        import threading
        timer_ref[0] = threading.Timer(delay, execute_callback)
        timer_ref[0].start()

    return ft.TextField(
        label=label,
        hint_text=hint_text,
        width=width,
        prefix_icon=prefix_icon,
        on_change=on_change,
        **kwargs
    )


# ==================== LOADING OVERLAY ====================

class LoadingOverlay:
    """
    A loading overlay that can be shown/hidden over any container.
    """

    def __init__(self, page: ft.Page, message: str = "Loading..."):
        self._page = page
        self._message = message
        self._overlay: Optional[ft.Container] = None
        self._visible = False

    def show(self, message: str = None):
        """Show the loading overlay"""
        if message:
            self._message = message

        if not self._overlay:
            self._overlay = ft.Container(
                expand=True,
                bgcolor="#80000000",  # Semi-transparent black
                content=ft.Column([
                    ft.ProgressRing(width=50, height=50,
                                    color=ft.Colors.WHITE),
                    ft.Container(height=20),
                    ft.Text(
                        self._message,
                        size=16,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.Alignment(0, 0),
                visible=True,
            )
        else:
            self._overlay.visible = True

        self._visible = True
        self._page.update()

    def hide(self):
        """Hide the loading overlay"""
        if self._overlay:
            self._overlay.visible = False
        self._visible = False
        self._page.update()

    def is_visible(self) -> bool:
        """Check if overlay is visible"""
        return self._visible

    def update_message(self, message: str):
        """Update the loading message"""
        self._message = message
        if self._overlay and self._overlay.content:
            # Update the text control
            if hasattr(self._overlay.content, 'controls') and len(self._overlay.content.controls) > 1:
                self._overlay.content.controls[1].value = message
        self._page.update()


# ==================== FILE UPLOAD HELPERS ====================

class FileUploadHelper:
    """
    Helper class for file uploads with progress indication.
    """

    def __init__(self, page: ft.Page, max_size_mb: int = 10):
        self._page = page
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._upload_progress: Optional[ft.ProgressBar] = None
        self._status_text: Optional[ft.Text] = None

    def validate_file_size(self, file_path: str) -> tuple[bool, str]:
        """
        Validate file size.

        Returns:
            (is_valid, error_message)
        """
        import os
        if not os.path.exists(file_path):
            return False, "File not found"

        file_size = os.path.getsize(file_path)
        if file_size > self._max_size_bytes:
            max_mb = self._max_size_bytes / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"File too large! Max {max_mb:.1f}MB allowed (yours: {actual_mb:.1f}MB)"

        return True, ""

    def create_upload_indicator(self) -> tuple[ft.Container, ft.Text]:
        """
        Create upload progress indicator UI.

        Returns:
            (container, status_text)
        """
        self._status_text = ft.Text(
            "Ready to upload",
            size=12,
            color="#6C757D"
        )

        self._upload_progress = ft.ProgressBar(
            width=200,
            value=0,
            visible=False
        )

        container = ft.Container(
            content=ft.Column([
                self._upload_progress,
                self._status_text,
            ], spacing=5),
            visible=False,
            padding=10,
            bgcolor="#F8F9FA",
            border_radius=8,
        )

        return container, self._status_text

    def show_upload_progress(self, container: ft.Container, filename: str, progress: float):
        """Show upload progress"""
        container.visible = True
        self._upload_progress.visible = True
        self._upload_progress.value = progress
        self._status_text.value = f"Uploading {filename}... {int(progress * 100)}%"
        self._page.update()

    def hide_upload_progress(self, container: ft.Container):
        """Hide upload progress"""
        container.visible = False
        self._upload_progress.visible = False
        self._page.update()

    def show_upload_success(self, container: ft.Container, filename: str):
        """Show upload success"""
        container.visible = True
        self._upload_progress.visible = False
        self._status_text.value = f"✓ {filename} uploaded successfully"
        self._status_text.color = "#28A745"  # Success green
        self._page.update()

    def show_upload_error(self, container: ft.Container, error: str):
        """Show upload error"""
        container.visible = True
        self._upload_progress.visible = False
        self._status_text.value = f"✗ Upload failed: {error}"
        self._status_text.color = "#DC3545"  # Error red
        self._page.update()


# ==================== PROFILE PHOTO HELPER ====================

def resolve_profile_photo_path(profile_photo: str, base_dir: str = None) -> str:
    """
    Resolve profile photo path to a valid file path or URL.

    Args:
        profile_photo: The profile photo value (could be URL, path, or filename)
        base_dir: Base directory for relative paths (defaults to project root)

    Returns:
        Valid path or URL, or None if not found
    """
    import os
    from pathlib import Path

    if not profile_photo:
        return None

    # If it's a URL, return as-is
    if profile_photo.startswith('http://') or profile_photo.startswith('https://'):
        return profile_photo

    # If it's an absolute path and exists, return as-is
    if os.path.isabs(profile_photo) and os.path.exists(profile_photo):
        return profile_photo

    # Set base directory
    if base_dir is None:
        base_dir = Path(__file__).parent.parent

    # Try various relative paths
    possible_paths = [
        # Original path as-is
        profile_photo,
        # Relative to profile_photos directory
        str(base_dir / "assets" / "profile_photos" /
            os.path.basename(profile_photo)),
        # Relative to assets directory
        str(base_dir / "assets" / os.path.basename(profile_photo)),
        # Just the filename in profile_photos
        str(base_dir / "assets" / "profile_photos" /
            os.path.basename(profile_photo)),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None  # Return None if no valid path found


# ==================== DIALOG HELPERS ====================

def show_loading_dialog(page: ft.Page, message: str = "Loading...") -> ft.AlertDialog:
    """
    Show a loading dialog.

    Args:
        page: The Flet page
        message: Message to display

    Returns:
        The dialog (can be closed with close_loading_dialog)
    """
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Please Wait"),
        content=ft.Column([
            ft.ProgressRing(width=40, height=40),
            ft.Container(height=15),
            ft.Text(message, size=14),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        open=True,
    )
    page.overlay.append(dialog)
    page.update()
    return dialog


def close_loading_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """
    Close a loading dialog.

    Args:
        page: The Flet page
        dialog: The dialog to close
    """
    if dialog:
        dialog.open = False
        try:
            page.overlay.remove(dialog)
        except ValueError:
            pass
        page.update()


def show_confirm_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm: Callable,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    confirm_color: str = "#DC3545"
) -> ft.AlertDialog:
    """
    Show a confirmation dialog.

    Args:
        page: The Flet page
        title: Dialog title
        message: Dialog message
        on_confirm: Callback when confirmed
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button
        confirm_color: Color for confirm button

    Returns:
        The dialog
    """
    def close_dlg(e):
        dialog.open = False
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
    return dialog


# ==================== STATE PRESERVATION ====================

class StateManager:
    """
    Simple state manager to preserve UI state during refreshes.
    """

    def __init__(self):
        self._state = {}

    def set(self, key: str, value: Any):
        """Set a state value"""
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value"""
        return self._state.get(key, default)

    def clear(self, key: str = None):
        """Clear state"""
        if key:
            self._state.pop(key, None)
        else:
            self._state.clear()

    def has(self, key: str) -> bool:
        """Check if key exists"""
        return key in self._state


# Global state manager instance
_state_manager = StateManager()


def get_state_manager() -> StateManager:
    """Get the global state manager"""
    return _state_manager
