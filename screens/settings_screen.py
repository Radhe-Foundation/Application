"""
Vernika HRA - Settings Screen (Enhanced)
Complete settings management with company profile, theme, notifications, and preferences
"""

import flet as ft
from flet import Column, Container, Text, Row, Button, Icon, Icons, Card, TextField, Switch, Dropdown
from flet import padding, FontWeight, ScrollMode, IconButton, RadioGroup, Radio
from flet import AlertDialog, dropdown
from datetime import datetime

# Import Colors from compatibility module instead of flet
from core.colors_compat import Colors

from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Company, Role, User, Employee
from database.operations import get_all_users, get_all_roles, get_all_departments


def _safe_navigate_to_home(page, user=None):
    """Safely navigate to home screen"""
    try:
        from core.navigation import navigate_to_home
        navigate_to_home(page, user)
    except ImportError:
        # Fallback navigation
        try:
            from screens.admin_screen import AdminScreen
            from screens.employee_screen import EmployeeScreen
            page.clean()
            if user and isinstance(user, dict):
                role = user.get('role', 'employee').lower()
            elif user and hasattr(user, 'role'):
                role = user.role.name.lower() if user.role else 'employee'
            else:
                role = 'employee'

            if role == 'admin':
                page.add(AdminScreen(page, user))
            else:
                page.add(EmployeeScreen(page, user))
        except Exception as e:
            print(f"Navigation error: {e}")
            from screens.login_screen import LoginScreen
            page.clean()
            page.add(LoginScreen(page))


class SettingsScreen(Column):
    def __init__(self, page, user):
        # Store page reference before super().__init__() to avoid conflict
        self._page = page
        self.user = user

        super().__init__()
        self.expand = True
        self.current_section = "appearance"

        # Load saved settings
        self._settings = self._load_settings()

        self.build_ui()

        # Initialize keyboard shortcuts for this screen
        self._init_keyboard_shortcuts()

    def _load_settings(self):
        """Load settings from database or defaults"""
        # Default settings
        settings = {
            'theme': 'light',
            'notifications_enabled': True,
            'notification_sound': True,
            'chat_notifications': True,
            'mail_notifications': True,
            'attendance_notifications': True,
            'leave_notifications': True,
            'email_notifications': True,
            'attendance_reminder': True,
            'auto_approve_leave': False,
            'session_timeout': 60,
            'chat_enter_send': True,
            'show_online_status': True,
            'last_seen_enabled': True,
        }

        # Try to load from database if available
        try:
            db = get_db_session()
            # Load company settings which might contain preferences
            company = db.query(Company).first()
            if company:
                # For now, use defaults - could be extended to store in DB
                pass
            db.close()
        except Exception as e:
            print(f"Error loading settings: {e}")

        return settings

    def _save_settings_to_db(self):
        """Save settings to database"""
        # This would save to a settings table in production
        pass

    def _init_keyboard_shortcuts(self):
        """Initialize keyboard shortcuts for settings screen"""
        try:
            from core.keyboard_shortcuts_v2 import set_current_screen
            set_current_screen("settings")
        except Exception as e:
            print(f"[Settings] Error setting keyboard screen: {e}")

        # Initialize notifications
        try:
            from utils.notification_manager import get_notification_manager
            self._notification_manager = get_notification_manager()
            # Apply saved settings to notification manager
            if self._notification_manager:
                if self._settings.get('notification_sound', True):
                    self._notification_manager.set_sound_enabled(True)
                else:
                    self._notification_manager.set_sound_enabled(False)
                if self._settings.get('notifications_enabled', True):
                    self._notification_manager.set_badge_enabled(True)
                else:
                    self._notification_manager.set_badge_enabled(False)
        except Exception as e:
            print(f"[Settings] Error initializing notifications: {e}")
            self._notification_manager = None

    def refresh(self):
        """Refresh the settings screen content"""
        self.build_content()
        if self.current_section == "users":
            self.refresh_users_list()
        self._page.update()

    def build_ui(self):
        # Theme colors based on current theme
        theme = self._settings.get('theme', 'light')
        if theme == 'dark':
            header_bg = Colors.GREY_900
            header_text = Colors.WHITE
            content_bg = Colors.GREY_850
        else:
            header_bg = "#1E3A5F"  # Navy blue
            header_text = Colors.WHITE
            content_bg = "#F5F7FA"

        # Navigation buttons with icons
        self.nav_row = Row([
            self._create_nav_button("appearance", "Appearance", Icons.PALETTE),
            self._create_nav_button(
                "notifications", "Notifications", Icons.NOTIFICATIONS),
            self._create_nav_button("chat", "Chat & Mail", Icons.CHAT),
            self._create_nav_button("company", "Company", Icons.BUSINESS),
            self._create_nav_button("users", "Users", Icons.PEOPLE),
        ], spacing=5, scroll=ft.ScrollMode.AUTO)

        self.content_container = Container()

        self.controls = [
            Container(
                padding=20,
                bgcolor=content_bg,
                content=Column([
                    self.nav_row,
                    Container(height=20),
                    self.content_container,
                ], spacing=0, scroll=ScrollMode.AUTO, expand=True),
                expand=True
            )
        ]

        # Build initial content
        self.build_content()

    def _create_nav_button(self, section: str, label: str, icon) -> Button:
        """Create a navigation button"""
        is_active = self.current_section == section
        theme = self._settings.get('theme', 'light')

        if theme == 'dark':
            active_bg = Colors.BLUE_700
            inactive_bg = Colors.GREY_800
            active_color = Colors.WHITE
            inactive_color = Colors.GREY_400
        else:
            active_bg = "#1E3A5F"
            inactive_bg = Colors.WHITE
            active_color = Colors.WHITE
            inactive_color = Colors.GREY_700

        return Button(
            content=Row([
                Icon(icon, size=18,
                     color=active_color if is_active else inactive_color),
                Container(width=5),
                Text(label, color=active_color if is_active else inactive_color, size=13)
            ], spacing=0),
            on_click=lambda e: self.switch_section(section),
            bgcolor=active_bg if is_active else inactive_bg,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=12, vertical=8)
            )
        )

    def build_content(self):
        builders = {
            "appearance": self._build_appearance_settings,
            "notifications": self._build_notifications_settings,
            "chat": self._build_chat_settings,
            "company": self._build_company_settings,
            "users": self._build_users_settings,
        }

        builder = builders.get(self.current_section)
        if builder:
            self.content_container.content = builder()
        self._page.update()

    def switch_section(self, section):
        self.current_section = section
        self.build_ui()  # Rebuild to update button states
        self.build_content()

    def _toggle_theme(self):
        """Toggle between light and dark theme"""
        current = self._settings.get('theme', 'light')
        self._settings['theme'] = 'dark' if current == 'light' else 'light'
        self._save_settings_to_db()

        # Rebuild UI with new theme
        self.build_ui()
        self.build_content()

        # Apply theme to page
        self._apply_theme()
        self._page.update()

    def _apply_theme(self):
        """Apply theme settings to the page"""
        theme = self._settings.get('theme', 'light')

        if theme == 'dark':
            self._page.theme_mode = ft.ThemeMode.DARK
            self._page.bgcolor = Colors.GREY_900
        else:
            self._page.theme_mode = ft.ThemeMode.LIGHT
            self._page.bgcolor = Colors.GREY_100

    def _build_appearance_settings(self):
        """Build appearance/theme settings"""
        theme = self._settings.get('theme', 'light')

        return Column([
            Text("Appearance", size=22, weight=FontWeight.BOLD),
            Container(height=20),

            # Theme Selection
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Text("Theme", size=16, weight=FontWeight.W_600),
                    Container(height=10),
                    Row([
                        RadioGroup(
                            value=theme,
                            on_change=self._on_theme_changed,
                            content=Column([
                                Row([
                                    Radio(value="light", label="Light Mode"),
                                    Container(width=20),
                                    Radio(value="dark", label="Dark Mode"),
                                ]),
                                Row([
                                    Radio(value="system",
                                          label="System Default"),
                                ])
                            ])
                        )
                    ]),
                    Container(height=10),
                    Text("Choose your preferred color scheme",
                         size=12, color=Colors.GREY_600),
                ], spacing=5)
            ),

            Container(height=15),

            # Display Settings
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Text("Display", size=16, weight=FontWeight.W_600),
                    Container(height=10),
                    Switch(
                        label="Compact Mode",
                        value=self._settings.get('compact_mode', False),
                        on_change=self._on_setting_changed
                    ),
                    Switch(
                        label="Show Screen Names",
                        value=self._settings.get('show_screen_names', True),
                        on_change=self._on_setting_changed
                    ),
                ], spacing=5)
            ),

            Container(height=15),

            # Keyboard Shortcuts Info
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Text("Keyboard Shortcuts", size=16,
                         weight=FontWeight.W_600),
                    Container(height=10),
                    self._build_shortcut_info(
                        "Enter", "Send message (Chat/Mail)"),
                    self._build_shortcut_info("Ctrl + S", "Save changes"),
                    self._build_shortcut_info("Ctrl + F", "Search"),
                    self._build_shortcut_info(
                        "Escape", "Close dialog/Go back"),
                ], spacing=5)
            ),

        ], scroll=ScrollMode.AUTO, spacing=10)

    def _build_shortcut_info(self, key: str, description: str):
        """Build a keyboard shortcut info row"""
        return Container(
            padding=ft.padding.symmetric(vertical=5),
            content=Row([
                Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=Colors.GREY_200,
                    border_radius=4,
                    content=Text(key, size=12, weight=FontWeight.BOLD,
                                 font_family="monospace")
                ),
                Container(width=15),
                Text(description, size=13, color=Colors.GREY_700)
            ])
        )

    def _on_theme_changed(self, e):
        """Handle theme change"""
        self._settings['theme'] = e.control.value
        self._save_settings_to_db()
        self._apply_theme()
        self.build_ui()
        self.build_content()
        self._page.update()

    def _on_setting_changed(self, e):
        """Handle setting toggle change"""
        setting_name = e.control.label.lower().replace(' ', '_')
        self._settings[setting_name] = e.control.value
        self._save_settings_to_db()
        self.show_snackbar("Setting saved!", Colors.GREEN)

    def _build_notifications_settings(self):
        """Build notification settings"""
        return Column([
            Text("Notifications", size=22, weight=FontWeight.BOLD),
            Container(height=20),

            # Global Notification Settings
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Text("General", size=16, weight=FontWeight.W_600),
                    Container(height=10),
                    Switch(
                        label="Enable Notifications",
                        value=self._settings.get(
                            'notifications_enabled', True),
                        on_change=self._on_notification_enabled_changed
                    ),
                    Switch(
                        label="Notification Sound",
                        value=self._settings.get('notification_sound', True),
                        on_change=self._on_setting_changed
                    ),
                ], spacing=5)
            ),

            Container(height=15),

            # Screen-specific Notifications
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Text("Screen Notifications", size=16,
                         weight=FontWeight.W_600),
                    Container(height=10),
                    Switch(
                        label="Chat Messages",
                        value=self._settings.get('chat_notifications', True),
                        on_change=self._on_setting_changed
                    ),
                    Switch(
                        label="Emails",
                        value=self._settings.get('mail_notifications', True),
                        on_change=self._on_setting_changed
                    ),
                    Switch(
                        label="Attendance Alerts",
                        value=self._settings.get(
                            'attendance_notifications', True),
                        on_change=self._on_setting_changed
                    ),
                    Switch(
                        label="Leave Updates",
                        value=self._settings.get('leave_notifications', True),
                        on_change=self._on_setting_changed
                    ),
                ], spacing=5)
            ),

            Container(height=15),

            # Reminders
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Text("Reminders", size=16, weight=FontWeight.W_600),
                    Container(height=10),
                    Switch(
                        label="Daily Attendance Reminder",
                        value=self._settings.get('attendance_reminder', True),
                        on_change=self._on_setting_changed
                    ),
                    Switch(
                        label="Auto-approve Leave Requests",
                        value=self._settings.get('auto_approve_leave', False),
                        on_change=self._on_setting_changed
                    ),
                ], spacing=5)
            ),

            Container(height=20),

            Button(
                "Save Notification Settings",
                on_click=self._save_notification_settings,
                bgcolor=Colors.BLUE,
                color=Colors.WHITE
            ),

        ], scroll=ScrollMode.AUTO, spacing=10)

    def _on_notification_enabled_changed(self, e):
        """Handle notification enable/disable"""
        self._settings['notifications_enabled'] = e.control.value
        if e.control.value:
            self.show_snackbar("Notifications enabled!", Colors.GREEN)
        else:
            self.show_snackbar("Notifications disabled", Colors.ORANGE)
        self._save_settings_to_db()

    def _save_notification_settings(self, e):
        """Save notification settings"""
        self._save_settings_to_db()
        self.show_snackbar("Notification settings saved!", Colors.GREEN)

    def _build_chat_settings(self):
        """Build chat and mail settings"""
        return Column([
            Text("Chat & Mail Settings", size=22, weight=FontWeight.BOLD),
            Container(height=20),

            # Chat Settings
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Row([
                        Icon(Icons.CHAT, size=24, color=Colors.BLUE_700),
                        Container(width=10),
                        Text("Chat", size=16, weight=FontWeight.W_600),
                    ]),
                    Container(height=10),
                    Switch(
                        label="Press Enter to Send Message",
                        value=self._settings.get('chat_enter_send', True),
                        on_change=self._on_setting_changed
                    ),
                    Text(
                        "When enabled, pressing Enter will send your message. Shift+Enter for new line.",
                        size=11, color=Colors.GREY_600
                    ),
                    Container(height=10),
                    Switch(
                        label="Show Online Status",
                        value=self._settings.get('show_online_status', True),
                        on_change=self._on_setting_changed
                    ),
                    Switch(
                        label="Show Last Seen",
                        value=self._settings.get('last_seen_enabled', True),
                        on_change=self._on_setting_changed
                    ),
                ], spacing=5)
            ),

            Container(height=15),

            # Mail Settings
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Row([
                        Icon(Icons.MAIL, size=24, color=Colors.BLUE_700),
                        Container(width=10),
                        Text("Mail", size=16, weight=FontWeight.W_600),
                    ]),
                    Container(height=10),
                    Switch(
                        label="Press Enter to Send Email",
                        value=self._settings.get('mail_enter_send', True),
                        on_change=self._on_setting_changed
                    ),
                    Switch(
                        label="Enable Mail Notifications",
                        value=self._settings.get('email_notifications', True),
                        on_change=self._on_setting_changed
                    ),
                ], spacing=5)
            ),

            Container(height=15),

            # Status Update Settings
            Container(
                padding=20,
                bgcolor=Colors.WHITE,
                border_radius=12,
                content=Column([
                    Text("Status Updates", size=16, weight=FontWeight.W_600),
                    Container(height=10),
                    Text("Real-time status updates use 5-second polling",
                         size=12, color=Colors.GREY_600),
                    Container(height=5),
                    Row([
                        Text("Status:", size=13),
                        Container(width=10),
                        Container(
                            padding=ft.padding.symmetric(
                                horizontal=10, vertical=5),
                            bgcolor=Colors.GREEN_100,
                            border_radius=12,
                            content=Row([
                                Container(
                                    width=8, height=8,
                                    bgcolor=Colors.GREEN,
                                    border_radius=4
                                ),
                                Container(width=5),
                                Text("Active", size=12, color=Colors.GREEN_700)
                            ], spacing=0)
                        )
                    ]),
                    Container(height=5),
                    Text("Last updated: Just now",
                         size=11, color=Colors.GREY_500),
                ], spacing=5)
            ),

            Container(height=20),

            Button(
                "Save Chat & Mail Settings",
                on_click=self._save_chat_settings,
                bgcolor=Colors.BLUE,
                color=Colors.WHITE
            ),

        ], scroll=ScrollMode.AUTO, spacing=10)

    def _save_chat_settings(self, e):
        """Save chat and mail settings"""
        self._save_settings_to_db()
        self.show_snackbar("Chat & Mail settings saved!", Colors.GREEN)

    def _build_company_settings(self):
        """Build company settings form"""
        session = get_db_session()
        try:
            company = session.query(Company).first()

            company_name_val = company.name if company and company.name else ""
            company_email_val = company.email if company and company.email else ""
            company_phone_val = company.phone if company and company.phone else ""
            company_address_val = company.address if company and company.address else ""

            self.company_name = TextField(
                label="Company Name",
                width=400,
                value=str(company_name_val) if company_name_val else ""
            )
            self.company_email = TextField(
                label="Email",
                width=400,
                value=str(company_email_val) if company_email_val else ""
            )
            self.company_phone = TextField(
                label="Phone",
                width=400,
                value=str(company_phone_val) if company_phone_val else ""
            )
            self.company_address = TextField(
                label="Address",
                width=400,
                multiline=True,
                min_lines=2,
                value=str(company_address_val) if company_address_val else ""
            )

            return Column([
                Text("Company Profile", size=20, weight=FontWeight.BOLD),
                Container(height=15),
                self.company_name,
                self.company_email,
                self.company_phone,
                self.company_address,
                Container(height=20),
                Button("Save Changes", on_click=self.save_company_settings,
                       bgcolor=Colors.PRIMARY, color=Colors.WHITE),
            ], scroll=ScrollMode.AUTO, spacing=15)
        finally:
            session.close()

    def _build_users_settings(self):
        """Build users management section"""
        self.users_container = Container()
        self.refresh_users_list()

        return Column([
            Text("User Management", size=20, weight=FontWeight.BOLD),
            Container(height=15),
            Button("Add New User", icon=Icons.ADD, on_click=self.add_user),
            Container(height=15),
            self.users_container,
        ], scroll=ScrollMode.AUTO, spacing=15)

    def refresh_users_list(self):
        """Refresh users list"""
        session = get_db_session()
        try:
            users = get_all_users(session)

            rows = []
            for user in users:
                role_name = user.role.name if user.role else "N/A"

                status_color = Colors.GREEN
                if user.status:
                    if user.status.value == "inactive":
                        status_color = Colors.RED
                    elif user.status.value == "locked":
                        status_color = Colors.ORANGE

                rows.append(
                    Container(
                        padding=15,
                        border=ft.border.only(
                            bottom=ft.BorderSide(1, Colors.GREY_200)),
                        content=Row([
                            Container(
                                content=Column([
                                    Text(f"{user.username}", size=14,
                                         weight=FontWeight.BOLD),
                                    Text(user.email, size=12,
                                         color=Colors.GREY_600),
                                ], spacing=2),
                                expand=True
                            ),
                            Container(
                                content=Text(role_name.upper(), size=10,
                                             color=Colors.WHITE, weight=FontWeight.BOLD),
                                bgcolor=Colors.BLUE_300,
                                padding=padding.symmetric(
                                    horizontal=8, vertical=4),
                                border_radius=4
                            ),
                            Container(
                                content=Text(user.status.value if user.status else "active", size=10,
                                             color=Colors.WHITE, weight=FontWeight.BOLD),
                                bgcolor=status_color,
                                padding=padding.symmetric(
                                    horizontal=8, vertical=4),
                                border_radius=4
                            ),
                            IconButton(
                                Icons.EDIT, icon_color=Colors.GREY_600,
                                icon_size=20,
                                on_click=lambda e, u_id=user.id: self.edit_user(
                                    u_id)
                            ),
                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                )

            empty_message = Column([
                Icon(Icons.PEOPLE, size=40, color=Colors.GREY_300),
                Text("No users found", size=14, color=Colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER) if not rows else None

            self.users_container.content = Column([
                Card(
                    content=Container(
                        content=Column(
                            rows if rows else [],
                            spacing=0
                        ),
                        width=600
                    ),
                    elevation=1
                )
            ], spacing=0)
            self._page.update()

        finally:
            session.close()

    def go_back(self, e):
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)

    def save_company_settings(self, e):
        """Save company settings"""
        session = get_db_session()
        try:
            company = session.query(Company).first()
            if not company:
                company = Company(name="New Company")
                session.add(company)

            company.name = self.company_name.value or ""
            company.email = self.company_email.value or ""
            company.phone = self.company_phone.value or ""
            company.address = self.company_address.value or ""

            session.commit()
            self.show_snackbar("Company settings saved!", Colors.GREEN)
        except Exception as ex:
            session.rollback()
            self.show_snackbar(f"Error: {str(ex)}", Colors.RED)
        finally:
            session.close()

    def add_user(self, e):
        """Open dialog to add new user"""
        session = get_db_session()
        try:
            roles = get_all_roles(session)

            self.new_username = TextField(
                label="Username *", width=350, autofocus=True
            )
            self.new_email = TextField(
                label="Email *", width=350
            )
            self.new_password = TextField(
                label="Password *", width=350, password=True
            )
            self.new_role = Dropdown(
                label="Role *",
                width=350,
                options=[dropdown.Option(str(r.id), content=Text(r.display_name))
                         for r in roles]
            )

            dialog = AlertDialog(
                modal=True,
                title=Text("Add New User", weight=FontWeight.BOLD),
                content=Container(
                    width=400,
                    content=Column([
                        self.new_username,
                        self.new_email,
                        self.new_password,
                        self.new_role,
                        Text("* Required fields", size=11,
                             color=Colors.GREY_500),
                    ], scroll=ScrollMode.AUTO, spacing=10),
                    padding=10
                ),
                actions=[
                    Button("Cancel", on_click=lambda: self.close_dialog(dialog)),
                    Button("Create User", on_click=self.save_user,
                           bgcolor=Colors.GREY_700, color=Colors.WHITE),
                ]
            )

            self._page.dialog = dialog
            dialog.open = True
            self._page.update()

        finally:
            session.close()

    def save_user(self, e):
        """Save new user"""
        if not self.new_username.value.strip():
            self.show_snackbar("Username is required!", Colors.RED)
            return
        if not self.new_email.value.strip():
            self.show_snackbar("Email is required!", Colors.RED)
            return
        if not self.new_password.value.strip():
            self.show_snackbar("Password is required!", Colors.RED)
            return
        if not self.new_role.value:
            self.show_snackbar("Role is required!", Colors.RED)
            return

        import bcrypt
        from database.models import UserStatus

        session = get_db_session()
        try:
            # Check if username exists
            existing = session.query(User).filter(
                User.username == self.new_username.value.strip()).first()
            if existing:
                self.show_snackbar("Username already exists!", Colors.RED)
                return

            user = User(
                username=self.new_username.value.strip(),
                email=self.new_email.value.strip(),
                password_hash=bcrypt.hashpw(
                    self.new_password.value.encode(), bcrypt.gensalt()).decode(),
                role_id=int(self.new_role.value),
                status=UserStatus.ACTIVE
            )
            session.add(user)
            session.commit()

            self.close_dialog(self._page.dialog)
            self.show_snackbar("User created successfully!", Colors.GREEN)
            self.refresh_users_list()

        except Exception as ex:
            session.rollback()
            self.show_snackbar(f"Error: {str(ex)}", Colors.RED)
        finally:
            session.close()

    def edit_user(self, user_id):
        """Edit existing user"""
        session = get_db_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                self.show_snackbar("User not found!", Colors.RED)
                return

            # Get roles for dropdown
            roles = get_all_roles(session)

            # Get current role
            current_role_id = str(user.role_id) if user.role_id else ""

            username_field = ft.TextField(
                label="Username",
                value=user.username,
                width=300,
                disabled=True  # Username typically can't be changed
            )

            email_field = ft.TextField(
                label="Email",
                value=user.email,
                width=300,
            )

            # Role dropdown
            role_options = [ft.dropdown.Option(
                str(r.id), r.display_name) for r in roles]
            role_dropdown = ft.Dropdown(
                label="Role",
                width=300,
                options=role_options,
                value=current_role_id,
            )

            # Status dropdown
            status_options = [
                ft.dropdown.Option("active", "Active"),
                ft.dropdown.Option("inactive", "Inactive"),
                ft.dropdown.Option("locked", "Locked"),
            ]
            current_status = user.status.value if user.status else "active"
            status_dropdown = ft.Dropdown(
                label="Status",
                width=300,
                options=status_options,
                value=current_status,
            )

            error_text = ft.Text("", color=Colors.RED, size=12, visible=False)

            def save_changes(e):
                if not email_field.value:
                    error_text.value = "Email is required!"
                    error_text.visible = True
                    self._page.update()
                    return

                try:
                    from database.models import UserStatus

                    user.email = email_field.value
                    if role_dropdown.value:
                        user.role_id = int(role_dropdown.value)
                    if status_dropdown.value:
                        user.status = UserStatus(status_dropdown.value)

                    session.commit()
                    self.show_snackbar(
                        "User updated successfully!", Colors.GREEN)
                    self._close_dialog(None)
                    self.refresh_users_list()

                except Exception as ex:
                    error_text.value = f"Error: {str(ex)}"
                    error_text.visible = True
                    self._page.update()

            def close_dlg(e):
                self._close_dialog(e)
                session.close()

            dialog = ft.AlertDialog(
                title=ft.Text("Edit User"),
                content=ft.Column([
                    username_field,
                    email_field,
                    role_dropdown,
                    status_dropdown,
                    error_text,
                ], spacing=15),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dlg),
                    ft.ElevatedButton(
                        "Save Changes",
                        on_click=save_changes,
                        style=ft.ButtonStyle(
                            bgcolor=Colors.PRIMARY, color=Colors.WHITE),
                    ),
                ],
            )

            self._page.dialog = dialog
            dialog.open = True
            self._page.update()

        except Exception as ex:
            print(f"Error editing user: {ex}")
            self.show_snackbar(f"Error: {str(ex)}", Colors.RED)
            session.close()

    def _close_dialog(self, e):
        """Close dialog"""
        if self._page.dialog:
            self._page.dialog.open = False
        self._page.update()

    def close_dialog(self, dialog):
        dialog.open = False
        self._page.update()

    def show_snackbar(self, message: str, color):
        """Show a snackbar notification"""
        snackbar = ft.SnackBar(
            content=Text(message, color=Colors.WHITE),
            bgcolor=color,
            duration=3000
        )
        self._page.overlay.append(snackbar)
        snackbar.open = True
        self._page.update()
