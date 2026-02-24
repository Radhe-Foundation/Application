"""
Navigation Helper Module
Provides navigation stack functionality for back button support
"""

import flet as ft

# Global navigation stack
_nav_stack = []
_current_screen = None


def push_screen(page: ft.Page, screen_name: str, screen_content):
    """Push a new screen onto the navigation stack"""
    global _nav_stack, _current_screen

    # Store current screen
    if _current_screen:
        _nav_stack.append(_current_screen)

    # Set new current screen
    _current_screen = {
        'name': screen_name,
        'content': screen_content
    }

    # Clear and add new screen
    page.clean()
    page.add(screen_content)


def pop_screen(page: ft.Page):
    """Pop the previous screen from the navigation stack"""
    global _nav_stack, _current_screen

    if not _nav_stack:
        # Stack is empty, go to home/dashboard
        return False

    # Get previous screen
    prev_screen = _nav_stack.pop()

    # Set current screen to previous
    _current_screen = prev_screen

    # Navigate to previous screen
    page.clean()
    page.add(prev_screen['content'])

    return True


def go_back(page: ft.Page, user=None):
    """Go back one step in navigation, or to appropriate home screen if stack is empty

    Args:
        page: Flet page object
        user: Optional user object for determining home screen
    """
    global _nav_stack, _current_screen

    if _nav_stack:
        # We have history, go back
        pop_screen(page)
    else:
        # No history, go to home screen based on role
        navigate_to_home(page, user)


def can_go_back() -> bool:
    """Check if there's a previous screen to go back to"""
    return len(_nav_stack) > 0


def clear_stack():
    """Clear the navigation stack"""
    global _nav_stack, _current_screen
    _nav_stack = []
    _current_screen = None


def navigate_to_home(page: ft.Page, user=None):
    """Navigate to admin or employee screen based on user role

    Args:
        page: Flet page object
        user: Optional user object. Can be either a dict (from login) or User model.
    """
    global _nav_stack, _current_screen
    _nav_stack = []
    _current_screen = None

    # Get current user if not provided
    current_user = user

    # Handle case where user is passed as a dict (from login) or User model
    if not current_user:
        try:
            from auth.session import get_current_user
            session_user = get_current_user()
            if session_user:
                # Convert User object to dict for consistent handling
                if hasattr(session_user, 'id'):
                    current_user = {
                        'id': session_user.id,
                        'username': session_user.username,
                        'email': session_user.email,
                        'role': session_user.role.name if session_user.role else 'employee'
                    }
        except Exception as e:
            print(f"Could not get current user from session: {e}")

    if not current_user:
        # No user found, go to login
        from screens.login_screen import LoginScreen
        page.clean()
        page.add(LoginScreen(page))
        return

    # Determine user role - handle both dict and object
    user_role = None
    if isinstance(current_user, dict):
        user_role = current_user.get('role', '').lower()
    else:
        user_role = getattr(current_user, 'role', None)
        if user_role:
            user_role = user_role.lower()

    # Navigate based on role
    page.clean()

    if user_role == 'admin':
        from screens.admin_screen import AdminScreen
        page.add(AdminScreen(page, current_user))
    else:
        # Default to employee screen for non-admin users
        from screens.employee_screen import EmployeeScreen
        page.add(EmployeeScreen(page, current_user))


def get_stack_size() -> int:
    """Get the current size of the navigation stack"""
    return len(_nav_stack)


class BackButton(ft.Container):
    """A reusable back button component"""

    def __init__(self, page: ft.Page, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self._page = page
        self._on_click = on_click

        self.content = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=kwargs.get('icon_color', '#2E86AB'),
                on_click=self._handle_click,
                tooltip="Go Back"
            ),
        ])

        self.alignment = ft.alignment.Alignment(-1, 0)

    def _handle_click(self, e):
        if self._on_click:
            self._on_click(e)
        else:
            # Default behavior - pop from stack
            pop_screen(self._page)


class NavigationHeader(ft.Container):
    """A header with optional back button"""

    def __init__(self, page: ft.Page, title: str, show_back_button: bool = False,
                 on_back_click=None, **kwargs):
        super().__init__(**kwargs)
        self._page = page
        self._show_back = show_back_button
        self._on_back = on_back_click

        controls = []

        if show_back_button:
            controls.append(
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=kwargs.get('icon_color', '#2E86AB'),
                    on_click=self._handle_back,
                    tooltip="Go Back"
                )
            )

        controls.append(
            ft.Text(
                title,
                size=kwargs.get('title_size', 20),
                weight=ft.FontWeight.BOLD,
                color=kwargs.get('title_color', '#2E86AB'),
                expand=True
            )
        )

        self.content = ft.Row(
            controls,
            alignment=ft.MainAxisAlignment.START if show_back_button else ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.padding = kwargs.get('padding', 15)
        self.bgcolor = kwargs.get('bgcolor', '#FFFFFF')

    def _handle_back(self, e):
        if self._on_back:
            self._on_back(e)
        else:
            pop_screen(self._page)
