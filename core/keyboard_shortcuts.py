"""
Global Keyboard Shortcuts Manager for RadheFoundation HRA
Handles keyboard shortcuts across the application
"""

import flet as ft
from typing import Dict, Callable, Optional
from dataclasses import dataclass


@dataclass
class KeyboardShortcut:
    """Represents a keyboard shortcut"""
    key: str
    ctrl: bool = False
    shift: bool = False
    alt: bool = False
    callback: Callable = None
    description: str = ""


class KeyboardShortcutsManager:
    """Manages global keyboard shortcuts for the application"""

    def __init__(self, page: ft.Page):
        self._page = page
        self._shortcuts: Dict[str, KeyboardShortcut] = {}
        self._current_screen = None

        # Register global keyboard event handler
        self._page.on_keyboard_event = self._handle_keyboard_event

    def register_shortcut(self, name: str, shortcut: KeyboardShortcut):
        """Register a keyboard shortcut"""
        self._shortcuts[name] = shortcut

    def unregister_shortcut(self, name: str):
        """Unregister a keyboard shortcut"""
        if name in self._shortcuts:
            del self._shortcuts[name]

    def set_current_screen(self, screen_name: str):
        """Set the current screen context for context-aware shortcuts"""
        self._current_screen = screen_name

    def _handle_keyboard_event(self, e: ft.KeyboardEvent):
        """Handle keyboard events globally"""
        if e.key == "Enter":
            # Handle Enter key for sending messages in chat
            if self._current_screen == "chat":
                self._handle_chat_enter()
                e.handled = True
            elif self._current_screen == "mail":
                self._handle_mail_enter()
                e.handled = True

        elif e.key == "S" and e.ctrl:
            # Handle Ctrl+S for save operations
            self._handle_save_shortcut()
            e.handled = True

        elif e.key == "F" and e.ctrl:
            # Handle Ctrl+F for search
            self._handle_search_shortcut()
            e.handled = True

        elif e.key == "Escape":
            # Handle Escape for closing dialogs/modals
            self._handle_escape_shortcut()
            e.handled = True

    def _handle_chat_enter(self):
        """Handle Enter key in chat screen - send message"""
        try:
            # Find chat screen instance and trigger send
            from core.navigation_v2 import get_navigation_manager
            nav_manager = get_navigation_manager(self._page)
            if nav_manager and nav_manager.current_screen_name == "chat":
                # Get the current screen instance
                current_screen = None
                for overlay in self._page.overlay:
                    if hasattr(overlay, '_send_message'):
                        current_screen = overlay
                        break

                # Try to find in page controls
                if not current_screen:
                    for control in self._page.controls:
                        if hasattr(control, '_send_message'):
                            current_screen = control
                            break

                if current_screen and hasattr(current_screen, '_on_send_clicked'):
                    # Simulate send button click
                    current_screen._on_send_clicked(None)
        except Exception as e:
            print(f"[Keyboard] Error handling chat Enter: {e}")

    def _handle_mail_enter(self):
        """Handle Enter key in mail screen - send email"""
        try:
            # Find mail screen instance and trigger send
            from core.navigation_v2 import get_navigation_manager
            nav_manager = get_navigation_manager(self._page)
            if nav_manager and nav_manager.current_screen_name == "mail":
                # Get the current screen instance
                current_screen = None
                for overlay in self._page.overlay:
                    if hasattr(overlay, '_send_email'):
                        current_screen = overlay
                        break

                # Try to find in page controls
                if not current_screen:
                    for control in self._page.controls:
                        if hasattr(control, '_send_email'):
                            current_screen = control
                            break

                if current_screen and hasattr(current_screen, '_send_email'):
                    # Simulate send button click
                    current_screen._send_email(None)
        except Exception as e:
            print(f"[Keyboard] Error handling mail Enter: {e}")

    def _handle_save_shortcut(self):
        """Handle Ctrl+S for save operations"""
        try:
            # Find current screen and trigger save if available
            current_screen = None
            for control in self._page.controls:
                if hasattr(control, '_save_changes'):
                    current_screen = control
                    break

            if current_screen and hasattr(current_screen, '_save_changes'):
                current_screen._save_changes(None)
        except Exception as e:
            print(f"[Keyboard] Error handling save shortcut: {e}")

    def _handle_search_shortcut(self):
        """Handle Ctrl+F for search operations"""
        try:
            # Find current screen and trigger search if available
            current_screen = None
            for control in self._page.controls:
                if hasattr(control, '_show_search'):
                    current_screen = control
                    break

            if current_screen and hasattr(current_screen, '_show_search'):
                current_screen._show_search(None)
        except Exception as e:
            print(f"[Keyboard] Error handling search shortcut: {e}")

    def _handle_escape_shortcut(self):
        """Handle Escape key for closing dialogs/modals"""
        try:
            # Close any open dialogs
            if self._page.dialog and self._page.dialog.open:
                self._page.dialog.open = False
                self._page.update()
                return

            # Close any open bottom sheets
            if hasattr(self._page, 'bottom_sheet') and self._page.bottom_sheet and self._page.bottom_sheet.open:
                self._page.bottom_sheet.open = False
                self._page.update()
                return

            # Try navigation back
            from core.navigation_v2 import get_navigation_manager
            nav_manager = get_navigation_manager(self._page)
            if nav_manager and nav_manager.can_go_back:
                nav_manager.go_back()
        except Exception as e:
            print(f"[Keyboard] Error handling escape shortcut: {e}")


# Global instance
_keyboard_manager: Optional[KeyboardShortcutsManager] = None


def init_keyboard_shortcuts(page: ft.Page) -> KeyboardShortcutsManager:
    """Initialize keyboard shortcuts manager"""
    global _keyboard_manager
    _keyboard_manager = KeyboardShortcutsManager(page)
    return _keyboard_manager


def get_keyboard_manager() -> Optional[KeyboardShortcutsManager]:
    """Get the global keyboard shortcuts manager"""
    global _keyboard_manager
    return _keyboard_manager
