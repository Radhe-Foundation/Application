"""
Vernika HRA - Login Screen - Updated
Proper user handling and navigation with responsive design
"""

import flet as ft
import os

from core.theme import PRIMARY
from database.session_manager import get_session, get_db_session, check_db_connection
from database.operations import authenticate_user
from config import SUPABASE_URL, SUPABASE_STORAGE_BUCKET


def get_logo_src() -> str:
    """Get logo source path that works in both desktop and web"""
    import os
    # Check if running in web mode by checking environment
    is_web = os.getenv('FLET_WEB', '').lower(
    ) == 'true' or os.getenv('MODE', '') == 'web'

    # For web deployment, use absolute path from root with web_assets prefix
    # Flet web serves assets from web_assets folder at root
    if is_web or os.name == 'nt' == False:
        # Web mode - use web_assets path
        return "/web_assets/assets/logo/Vernikalogo.png"
    else:
        # Desktop mode - use relative path
        return "assets/logo/Vernikalogo.png"


class LoginScreen(ft.Container):

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.expand = True
        self.alignment = ft.alignment.Alignment(0, 0)

        # Store responsive values
        self._is_mobile = self._check_mobile()
        self._is_tablet = self._check_tablet()

        # Check theme
        self.is_dark = False  # Use light theme by default
        self._init_components()
        self.content = self.build_ui()
        print("✓ LoginScreen initialized")

    def _check_mobile(self) -> bool:
        """Check if running on mobile"""
        try:
            width = getattr(self._page, 'window_width', 1200)
            return width < 768
        except:
            return False

    def _check_tablet(self) -> bool:
        """Check if running on tablet"""
        try:
            width = getattr(self._page, 'window_width', 1200)
            return 768 <= width < 1024
        except:
            return False

    def _get_window_width(self) -> float:
        """Get window width safely"""
        try:
            return getattr(self._page, 'window_width', 1200)
        except:
            return 1200

    def _get_window_height(self) -> float:
        """Get window height safely"""
        try:
            return getattr(self._page, 'window_height', 800)
        except:
            return 800

    def _init_components(self):
        """Initialize UI components - responsive sizing"""

        window_width = self._get_window_width()

        # Responsive sizing - use 768px for mobile breakpoint
        if window_width < 768:  # Mobile
            logo_size = 100
            title_size = 24
            welcome_size = 18
            form_width = window_width - 50
            field_height = 48
            btn_height = 45
            icon_size = 20
        elif window_width < 1024:  # Tablet
            logo_size = 140
            title_size = 28
            welcome_size = 20
            form_width = 300
            field_height = 50
            btn_height = 48
            icon_size = 22
        else:  # Desktop
            logo_size = 200
            title_size = 32
            welcome_size = 24
            form_width = 320
            field_height = 52
            btn_height = 50
            icon_size = 24

        self._logo_size = logo_size
        self._form_width = form_width
        self._field_height = field_height
        self._btn_height = btn_height
        self._icon_size = icon_size

        # Logo - use Supabase bucket URL with proper fit for full fit
        # Use config values instead of hardcoded URL
        if SUPABASE_URL and SUPABASE_STORAGE_BUCKET:
            logo_src = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/logo/Vernikalogo.png"
        else:
            logo_src = "assets/logo/Vernikalogo.png"  # Fallback to local

        self.logo = ft.Container(
            width=logo_size,
            height=logo_size,
            border_radius=30,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            margin=0,
            content=ft.Image(
                src=logo_src,
                fit="contain",
                width=logo_size,
                height=logo_size,
            ),
        )

        # App title - VERNIKASTORE - responsive size
        self.app_title = ft.Text(
            "VERNIKASTORE",
            size=title_size,
            weight=ft.FontWeight.W_900,
            color=ft.Colors.WHITE,
        )

        # Welcome text - WELCOME BACK - responsive size
        self.welcome_title = ft.Text(
            "WELCOME BACK",
            size=welcome_size,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.WHITE,
        )

        # Welcome subtitle - simplified - responsive size
        self.welcome_subtitle = ft.Text(
            "Sign in to continue",
            size=14,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )

        # Username field - responsive (expand instead of fixed width)
        self.username = ft.TextField(
            label="Username or Email",
            height=field_height,
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=10,
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.GREY_500),
            focused_border_color=PRIMARY,
            focused_border_width=2,
            cursor_color=PRIMARY,
            label_style=ft.TextStyle(color=ft.Colors.GREY_500, size=11),
            content_padding=ft.padding.symmetric(horizontal=14, vertical=16),
            text_size=14,
            expand=True,
        )

        # Password field - responsive
        self.password = ft.TextField(
            label="Password",
            height=field_height,
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
            expand=True,
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

        # Sign in button - responsive
        self.sign_in_btn = ft.Container(
            content=ft.Text("Sign In", size=15,
                            weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            height=btn_height,
            bgcolor=PRIMARY,
            border_radius=10,
            alignment=ft.alignment.Alignment(0, 0),
            on_click=self.login,
            ink=True,
            expand=True,
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
        """Show forgot password dialog"""
        self._show_forgot_password_dialog()

    def _show_forgot_password_dialog(self):
        """Show forgot password dialog with email input"""
        email_field = ft.TextField(
            label="Email Address",
            height=52,
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            border_radius=10,
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.GREY_500),
            focused_border_color=PRIMARY,
            focused_border_width=2,
            cursor_color=PRIMARY,
            label_style=ft.TextStyle(color=ft.Colors.GREY_500, size=11),
            content_padding=ft.padding.symmetric(horizontal=14, vertical=16),
            text_size=14,
            expand=True,
        )

        verification_code_field = ft.TextField(
            label="Verification Code",
            height=52,
            prefix_icon=ft.Icons.PIN_OUTLINED,
            border_radius=10,
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.GREY_500),
            focused_border_color=PRIMARY,
            focused_border_width=2,
            cursor_color=PRIMARY,
            label_style=ft.TextStyle(color=ft.Colors.GREY_500, size=11),
            content_padding=ft.padding.symmetric(horizontal=14, vertical=16),
            text_size=14,
            expand=True,
            visible=False,
        )

        new_password_field = ft.TextField(
            label="New Password",
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
            expand=True,
            visible=False,
        )

        confirm_password_field = ft.TextField(
            label="Confirm Password",
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
            expand=True,
            visible=False,
        )

        status_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER,
        )

        step = {"value": 1}  # 1: email, 2: code, 3: password

        def close_dlg(e):
            self._page.dialog = None
            self._page.update()

        def send_verification(e):
            """Send verification code to email"""
            email = email_field.value.strip()
            if not email:
                status_text.value = "Please enter your email address"
                status_text.color = "#DC3545"
                self._page.update()
                return

            # Check if email exists in database
            try:
                db = get_db_session()
                from database.operations import get_user_by_email
                user = get_user_by_email(db, email)
                db.close()

                if not user:
                    status_text.value = "Email not found in our system"
                    status_text.color = "#DC3545"
                    self._page.update()
                    return

                # Generate a 6-digit verification code
                import random
                code = str(random.randint(100000, 999999))

                # Store the code and email temporarily (in memory for demo)
                # In production, store in database with expiration
                self._reset_code = code
                self._reset_email = email
                self._reset_code_expiry = None

                import time
                self._reset_code_expiry = time.time() + 300  # 5 minutes

                # Show success and move to next step
                status_text.value = f"Demo: Your verification code is {code}\n(This would be sent to your email in production)"
                status_text.color = "#28A745"

                # Show verification code field
                verification_code_field.visible = True
                step["value"] = 2
                submit_btn.text = "Verify Code"
                self._page.update()

            except Exception as ex:
                status_text.value = f"Error: {str(ex)}"
                status_text.color = "#DC3545"
                self._page.update()

        def verify_code(e):
            """Verify the code entered by user"""
            code = verification_code_field.value.strip()
            if not code:
                status_text.value = "Please enter the verification code"
                status_text.color = "#DC3545"
                self._page.update()
                return

            # Verify the code
            if code == self._reset_code:
                import time
                if self._reset_code_expiry and time.time() > self._reset_code_expiry:
                    status_text.value = "Verification code has expired"
                    status_text.color = "#DC3545"
                    self._page.update()
                    return

                # Show password fields
                new_password_field.visible = True
                confirm_password_field.visible = True
                email_field.visible = False
                verification_code_field.visible = False
                status_text.value = "Code verified! Enter your new password"
                status_text.color = "#28A745"
                step["value"] = 3
                submit_btn.text = "Reset Password"
                self._page.update()
            else:
                status_text.value = "Invalid verification code"
                status_text.color = "#DC3545"
                self._page.update()

        def reset_password(e):
            """Reset the password"""
            new_pass = new_password_field.value
            confirm_pass = confirm_password_field.value

            if not new_pass or not confirm_pass:
                status_text.value = "Please enter and confirm your password"
                status_text.color = "#DC3545"
                self._page.update()
                return

            if len(new_pass) < 6:
                status_text.value = "Password must be at least 6 characters"
                status_text.color = "#DC3545"
                self._page.update()
                return

            if new_pass != confirm_pass:
                status_text.value = "Passwords do not match"
                status_text.color = "#DC3545"
                self._page.update()
                return

            # Update password in database
            try:
                db = get_db_session()
                from database.operations import get_user_by_email, update_user_password

                success = update_user_password(db, self._reset_email, new_pass)
                db.close()

                if success:
                    status_text.value = "Password reset successfully!"
                    status_text.color = "#28A745"
                    # Close dialog after a short delay
                    import time
                    time.sleep(1)
                    self._page.dialog = None
                    self._page.update()
                    self._show_snackbar(
                        "Password reset successful! Please login with your new password.")
                else:
                    status_text.value = "Failed to reset password"
                    status_text.color = "#DC3545"
                    self._page.update()

            except Exception as ex:
                status_text.value = f"Error: {str(ex)}"
                status_text.color = "#DC3545"
                self._page.update()

        # Determine which function to call based on step
        def on_submit(e):
            if step["value"] == 1:
                send_verification(e)
            elif step["value"] == 2:
                verify_code(e)
            else:
                reset_password(e)

        submit_btn = ft.Container(
            content=ft.Text("Send Code", size=15,
                            weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            height=50,
            bgcolor=PRIMARY,
            border_radius=10,
            alignment=ft.alignment.Alignment(0, 0),
            on_click=on_submit,
            ink=True,
            expand=True,
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Reset Password"),
            content=ft.Column([
                ft.Container(height=10),
                ft.Text(
                    "Enter your email address and we'll send you a verification code to reset your password.",
                    size=13,
                    color=ft.Colors.GREY_600,
                ),
                ft.Container(height=15),
                email_field,
                verification_code_field,
                new_password_field,
                confirm_password_field,
                ft.Container(height=10),
                status_text,
            ], tight=True, spacing=5),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                submit_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.dialog = dlg
        dlg.open = True
        self._page.update()

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
        """Build the complete UI with everything perfectly centered and responsive"""

        window_width = self._get_window_width()
        # Use 768px as mobile breakpoint for better mobile detection
        is_mobile = window_width < 768
        is_tablet = window_width < 1024

        # Responsive padding and sizing
        if is_mobile:
            horiz_padding = 15
            form_width = window_width - 40  # More margin on mobile
            left_panel_visible = True
            panel_ratio = 0.35
        elif is_tablet:
            horiz_padding = 20
            form_width = 300
            left_panel_visible = True
            panel_ratio = 0.4
        else:
            horiz_padding = 30
            form_width = 320
            left_panel_visible = True
            panel_ratio = 0.5

        # Left panel - clean centered design with proper logo centering
        left_panel = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                colors=["#2E86AB", "#A23B72", "#1A3A52"],
                begin=ft.alignment.Alignment(0, -1),
                end=ft.alignment.Alignment(0, 1),
            ),
            content=ft.Column([
                # Logo and title section - centered properly with top spacing
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        controls=[
                            # Top spacing for vertical centering - adjusted for better centering
                            ft.Container(height=60) if not is_mobile else ft.Container(
                                height=30),
                            # Logo container - perfectly centered
                            ft.Container(
                                content=self.logo,
                                alignment=ft.alignment.Alignment(0, 0),
                            ),
                            ft.Container(height=25) if not is_mobile else ft.Container(
                                height=15),
                            # App title - centered below logo
                            self.app_title if left_panel_visible else ft.Container(),
                            ft.Container(height=15) if not is_mobile else ft.Container(
                                height=8),
                            # Welcome title - centered
                            self.welcome_title if left_panel_visible else ft.Container(),
                            ft.Container(height=8) if not is_mobile else ft.Container(
                                height=5),
                            # Welcome subtitle - centered
                            self.welcome_subtitle if left_panel_visible else ft.Container(),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                ),
            ], spacing=0),
        )

        # Right panel - form content - responsive
        right_panel = ft.Container(
            expand=True,
            bgcolor=ft.Colors.WHITE,
            content=ft.Container(
                expand=True,
                content=ft.Column(
                    controls=[
                        # Spacer to push content to center vertically
                        ft.Container(expand=True) if not is_mobile else ft.Container(
                            height=20),
                        # Form header - centered
                        ft.Text("Sign In", size=28 if not is_mobile else 24,
                                weight=ft.FontWeight.BOLD, color="#1A1C1E"),
                        ft.Text("Enter your credentials", size=14 if not is_mobile else 12,
                                color=ft.Colors.GREY_500),
                        ft.Container(height=25) if not is_mobile else ft.Container(
                            height=20),
                        # Form fields - centered with responsive width
                        ft.Container(
                            content=ft.Column([
                                self.username,
                                ft.Container(height=12),
                                self.password,
                                ft.Container(height=10),
                                # Remember + Forgot - centered row
                                ft.Row([self.remember_me, self.forgot_password],
                                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Container(height=6),
                                # Error message
                                self.error_msg,
                                ft.Container(height=12),
                                # Sign in button
                                self.sign_in_btn,
                            ], spacing=0),
                            width=form_width,
                        ),
                        ft.Container(height=18) if not is_mobile else ft.Container(
                            height=15),
                        # Footer
                        ft.Container(height=25) if not is_mobile else ft.Container(
                            height=15),
                        self.footer,
                        # Spacer to push content to center vertically
                        ft.Container(
                            expand=True) if not is_mobile else ft.Container(),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=horiz_padding),
            ),
        )

        # Main layout - responsive: combine panels on mobile
        if is_mobile:
            # On mobile: Stack panels vertically - logo on top, form below
            return ft.Column([
                # Left panel (logo) on top
                ft.Container(
                    height=window_width * 0.5,  # Square aspect ratio
                    expand=False,
                    content=left_panel.content,
                ),
                # Right panel (form) below
                ft.Container(
                    expand=True,
                    content=right_panel.content,
                ),
            ], spacing=0, expand=True)
        else:
            # Desktop/Tablet: Side by side panels
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

            # Close database session before navigation
            if db:
                db.close()
                db = None

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

            # Re-initialize notifications after navigation
            try:
                from utils.notification_manager import ensure_notification_manager
                ensure_notification_manager(self._page)
            except Exception as e:
                print(f"Notification init error: {e}")

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
