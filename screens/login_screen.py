"""
Vernika HRA - Login Screen - Fixed
Proper user handling and navigation
"""

import flet as ft
import os

from core.theme import PRIMARY
from database.connection import get_db_session
from database.operations import authenticate_user


class LoginScreen(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.expand = True
        self.alignment = ft.alignment.Alignment(0, 0)

        # Check theme
        self.is_dark = False  # Use light theme by default
        self._init_components()
        self.content = self.build_ui()
        print("✓ LoginScreen initialized")

    def _init_components(self):
        """Initialize UI components"""

        # Logo - show image or text fallback
        if os.path.exists("/assets/logo/logo.jpeg"):
            logo_content = ft.Image(
                src="/assets/logo/logo.jpeg",
                width=80,
                height=80,
            )
        else:
            logo_content = ft.Text(
                "VH", size=32, color="white", weight=ft.FontWeight.BOLD)

        self.logo = ft.Container(
            width=80,
            height=80,
            content=logo_content,
            border_radius=16,
            bgcolor="#2E86AB",
            alignment=ft.alignment.Alignment(0, 0),
        )

        # App title
        self.app_title = ft.Text(
            "Vernika HRA",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )

        # Tagline
        self.tagline = ft.Text(
            "Human Resource Management",
            size=14,
            color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
        )

        # Welcome text
        self.welcome_title = ft.Text(
            "Welcome Back!",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )

        self.welcome_subtitle = ft.Text(
            "Sign in to access your dashboard",
            size=13,
            color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
        )

        # Username field
        self.username = ft.TextField(
            label="Username or Email",
            width=320,
            height=52,
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=10,
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.GREY_500),
            focused_border_color=PRIMARY,
            focused_border_width=2,
            cursor_color=PRIMARY,
            label_style=ft.TextStyle(color=ft.Colors.GREY_500, size=11),
            content_padding=ft.padding.symmetric(horizontal=14, vertical=16),
            text_size=14,
        )

        # Password field
        self.password = ft.TextField(
            label="Password",
            width=320,
            height=52,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            border_radius=10,
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.GREY_500),
            focused_border_color=PRIMARY,
            focused_border_width=2,
            cursor_color=PRIMARY,
            label_style=ft.TextStyle(color=ft.Colors.GREY_500, size=11),
            content_padding=ft.padding.symmetric(horizontal=14, vertical=16),
            text_size=14,
        )

        # Remember me checkbox
        self.remember_me = ft.Checkbox(
            label="Remember me",
            value=False,
            fill_color=PRIMARY,
            check_color=ft.Colors.WHITE,
        )

        # Forgot password
        self.forgot_password = ft.TextButton(
            "Forgot Password?",
            style=ft.ButtonStyle(color=PRIMARY),
            on_click=self._on_forgot_password
        )

        # Sign in button
        self.sign_in_btn = ft.Container(
            content=ft.Text("Sign In", size=15,
                            weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            width=320,
            height=50,
            bgcolor=PRIMARY,
            border_radius=10,
            alignment=ft.alignment.Alignment(0, 0),
            on_click=self.login,
            ink=True,
        )

        # Error message
        self.error_msg = ft.Text(
            color="#DC3545",
            size=12,
            visible=False,
            weight=ft.FontWeight.W_500,
        )

        # Loading indicator
        self.loading = ft.ProgressRing(
            width=18, height=18, stroke_width=2, color=ft.Colors.WHITE, visible=False)

        # Production: No demo credentials displayed
        self.demo_card = ft.Container(visible=False)

        # Footer
        self.footer = ft.Text("© 2024 Vernika HRA",
                              size=10, color=ft.Colors.GREY_500)

    def _on_forgot_password(self, e):
        self._show_snackbar("Contact administrator to reset password.")

    def _show_snackbar(self, message: str, bgcolor: str = "#323232"):
        """Show a snackbar message"""
        try:
            snack = ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor)
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
        except Exception as ex:
            print(f"Snackbar error: {ex}")

    def build_ui(self):
        """Build the complete UI with everything perfectly centered"""

        # Left panel - branded content
        left_panel = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                colors=["#2E86AB", "#A23B72", "#1A3A52"],
                begin=ft.alignment.Alignment(0, 0),
                end=ft.alignment.Alignment(1, 1),
            ),
            content=ft.Stack([
                # Decorative circles
                ft.Stack([
                    ft.Container(width=350, height=350, right=-100, top=-100, border_radius=175,
                                 bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                    ft.Container(width=200, height=200, left=-50, bottom=-50, border_radius=100,
                                 bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
                    ft.Container(width=120, height=120, right=80, bottom=150, border_radius=60,
                                 bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
                ]),
                # Centered content in left panel
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        controls=[
                            self.logo,
                            ft.Container(height=20),
                            self.app_title,
                            self.tagline,
                            ft.Container(height=30),
                            self.welcome_title,
                            ft.Container(height=8),
                            self.welcome_subtitle,
                            ft.Container(height=25),
                            ft.Text("Streamline your HR\noperations efficiently", size=13, color=ft.Colors.with_opacity(
                                0.85, ft.Colors.WHITE), text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=ft.padding.symmetric(horizontal=30),
                ),
            ]),
        )

        # Right panel - form content
        right_panel = ft.Container(
            expand=True,
            bgcolor=ft.Colors.WHITE,
            content=ft.Container(
                expand=True,
                content=ft.Column(
                    controls=[
                        # Spacer to push content to center vertically
                        ft.Container(expand=True),
                        # Form header - centered
                        ft.Text("Sign In", size=28,
                                weight=ft.FontWeight.BOLD, color="#1A1C1E"),
                        ft.Text("Enter your credentials", size=13,
                                color=ft.Colors.GREY_500),
                        ft.Container(height=25),
                        # Form fields - centered
                        self.username,
                        ft.Container(height=12),
                        self.password,
                        ft.Container(height=10),
                        # Remember + Forgot - centered row
                        ft.Row([self.remember_me, self.forgot_password], width=320,
                               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=6),
                        # Error message
                        self.error_msg,
                        ft.Container(height=12),
                        # Sign in button
                        self.sign_in_btn,
                        ft.Container(height=18),
                        # Footer
                        ft.Container(height=25),
                        self.footer,
                        # Spacer to push content to center vertically
                        ft.Container(expand=True),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=30),
            ),
        )

        # Main layout
        return ft.Row([
            left_panel,
            ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(
                0.1, ft.Colors.GREY_300)),
            right_panel,
        ], expand=True)

    def login(self, e):
        """Handle login button click using unified SQLAlchemy auth (supports cloud DB)"""
        self.error_msg.visible = False
        username_val = self.username.value.strip()
        password_val = self.password.value.strip()

        if not username_val or not password_val:
            self.error_msg.value = "Please enter username and password"
            self.error_msg.visible = True
            self._page.update()
            return

        self._show_loading(True)

        db = None
        try:
            # Use central SQLAlchemy-based authentication so it works with
            # both local SQLite and cloud PostgreSQL configured in config.py
            db = get_db_session()
            success, user_data, message = authenticate_user(
                db, username_or_email=username_val, password=password_val
            )

            if not success or not user_data:
                self._show_loading(False)
                self.error_msg.value = message or "Invalid username or password"
                self.error_msg.visible = True
                self._page.update()
                return

            self._show_loading(False)
            print(
                f"Login successful for user: {user_data['username']}, role: {user_data['role']}"
            )
            self.show_dashboard(user_data)

        except Exception as ex:
            # Surface database/connection issues clearly (e.g. cloud DB problems)
            self._show_loading(False)
            self.error_msg.value = f"Login error: {str(ex)}"
            self.error_msg.visible = True
            self._page.update()
            import traceback
            traceback.print_exc()
        finally:
            if db is not None:
                db.close()

    def _show_loading(self, show: bool):
        """Show/hide loading indicator"""
        self.loading.visible = show
        if show:
            self.sign_in_btn.content = ft.Row([
                self.loading,
                ft.Text("Signing In...", size=15,
                        weight=ft.FontWeight.W_500, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)
        else:
            self.sign_in_btn.content = ft.Text(
                "Sign In", size=15, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE)
        self.sign_in_btn.bgcolor = "#2470A0" if show else PRIMARY
        self._page.update()

    def show_dashboard(self, user_data: dict):
        """Navigate to appropriate dashboard based on role"""
        try:
            self._page.clean()

            role = user_data.get('role', 'employee').lower()
            user_id = user_data.get('id')
            username = user_data.get('username', '')

            print(f"Logging in user: {username}, role: {role}")

            # Redirect admin to AdminScreen, employees to EmployeeScreen
            if role == 'admin':
                from screens.admin_screen import AdminScreen
                self._page.add(AdminScreen(self._page, user_data))
            else:
                from screens.employee_screen import EmployeeScreen
                self._page.add(EmployeeScreen(self._page, user_data))

        except Exception as ex:
            print(f"Navigation error: {str(ex)}")
            import traceback
            traceback.print_exc()
            self._page.clean()
            self._page.add(LoginScreen(self._page))
            self._show_snackbar(
                f"Navigation error: {str(ex)}", bgcolor="#DC3545")


def show_login(page: ft.Page):
    """Helper to show login screen"""
    page.clean()
    page.add(LoginScreen(page))
