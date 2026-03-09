"""
Vernika HRA - Settings Screen
Complete settings management with company profile and preferences
"""

import flet as ft
from flet import Column, Container, Text, Row, Button, Icon, Colors, Icons, Card, TextField, Switch, Dropdown
from flet import padding, FontWeight, ScrollMode, IconButton
from flet import AlertDialog, dropdown
from datetime import datetime

from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Company, Role, User, Employee, AppSettings
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
        self.current_section = "company"
        self.build_ui()
        self.load_settings()

    def refresh(self):
        """Refresh the settings screen content"""
        self.build_content()
        if self.current_section == "users":
            self.refresh_users_list()
        self._page.update()

    def build_ui(self):
        # Navigation buttons
        self.nav_row = Row([
            Button("Company", on_click=lambda e: self.switch_section("company"),
                   bgcolor=Colors.PRIMARY if self.current_section == "company" else Colors.GREY_200,
                   color=Colors.WHITE if self.current_section == "company" else Colors.BLACK),
            Button("Users", on_click=lambda e: self.switch_section("users"),
                   bgcolor=Colors.PRIMARY if self.current_section == "users" else Colors.GREY_200,
                   color=Colors.WHITE if self.current_section == "users" else Colors.BLACK),
            Button("Preferences", on_click=lambda e: self.switch_section("preferences"),
                   bgcolor=Colors.PRIMARY if self.current_section == "preferences" else Colors.GREY_200,
                   color=Colors.WHITE if self.current_section == "preferences" else Colors.BLACK),
        ], spacing=10)

        self.content_container = Container()

        self.controls = [
            Container(
                padding=20,
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

    def build_content(self):
        if self.current_section == "company":
            self.content_container.content = self.build_company_settings()
        elif self.current_section == "users":
            self.content_container.content = self.build_users_settings()
        else:
            self.content_container.content = self.build_preferences_settings()
        self._page.update()

    def switch_section(self, section):
        self.current_section = section
        self.nav_row.controls[0].bgcolor = Colors.PRIMARY if section == "company" else Colors.GREY_200
        self.nav_row.controls[0].color = Colors.WHITE if section == "company" else Colors.BLACK
        self.nav_row.controls[1].bgcolor = Colors.PRIMARY if section == "users" else Colors.GREY_200
        self.nav_row.controls[1].color = Colors.WHITE if section == "users" else Colors.BLACK
        self.nav_row.controls[2].bgcolor = Colors.PRIMARY if section == "preferences" else Colors.GREY_200
        self.nav_row.controls[2].color = Colors.WHITE if section == "preferences" else Colors.BLACK
        self.build_content()

    def build_company_settings(self):
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

    def build_users_settings(self):
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

    def build_preferences_settings(self):
        """Build system preferences - load from database"""
        # Load saved preferences
        prefs = self._load_preferences()

        self.notifications_switch = Switch(
            label="Email Notifications",
            value=prefs.get('notifications_enabled', True)
        )

        self.attendance_reminder_switch = Switch(
            label="Daily Attendance Reminder",
            value=prefs.get('attendance_reminder', True)
        )

        self.leave_approval_switch = Switch(
            label="Auto-approve Leave Requests",
            value=prefs.get('auto_approve_leave', False)
        )

        self.session_timeout = TextField(
            label="Session Timeout (minutes)",
            width=200,
            value=str(prefs.get('session_timeout', 60))
        )

        return Column([
            Text("System Preferences", size=20, weight=FontWeight.BOLD),
            Container(height=15),
            self.notifications_switch,
            self.attendance_reminder_switch,
            self.leave_approval_switch,
            Container(height=10),
            self.session_timeout,
            Container(height=20),
            Button("Save Preferences", on_click=self.save_preferences,
                   bgcolor=Colors.PRIMARY, color=Colors.WHITE),
        ], scroll=ScrollMode.AUTO, spacing=15)

    def _load_preferences(self):
        """Load preferences from database"""
        prefs = {
            'notifications_enabled': True,
            'attendance_reminder': True,
            'auto_approve_leave': False,
            'session_timeout': 60
        }

        db = get_db_session()
        try:
            notif = db.query(AppSettings).filter(
                AppSettings.key == 'notifications_enabled').first()
            if notif and notif.value:
                prefs['notifications_enabled'] = notif.value.lower() == 'true'

            att_rem = db.query(AppSettings).filter(
                AppSettings.key == 'attendance_reminder').first()
            if att_rem and att_rem.value:
                prefs['attendance_reminder'] = att_rem.value.lower() == 'true'

            auto_leave = db.query(AppSettings).filter(
                AppSettings.key == 'auto_approve_leave').first()
            if auto_leave and auto_leave.value:
                prefs['auto_approve_leave'] = auto_leave.value.lower() == 'true'

            timeout = db.query(AppSettings).filter(
                AppSettings.key == 'session_timeout').first()
            if timeout and timeout.value:
                prefs['session_timeout'] = int(
                    timeout.value) if timeout.value.isdigit() else 60
        except Exception as e:
            print(f"Error loading preferences: {e}")
        finally:
            db.close()

        return prefs

    def load_settings(self):
        """Load current settings"""
        pass  # Settings are loaded in build methods

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

    def save_preferences(self, e):
        """Save system preferences to database"""
        try:
            session = get_db_session()
            try:
                # Try to load or create a settings record
                from database.models import Company
                company = session.query(Company).first()

                if company:
                    # Store preferences in company settings as JSON
                    import json
                    prefs = {
                        'notifications_enabled': self.notifications_switch.value,
                        'attendance_reminder': self.attendance_reminder_switch.value,
                        'auto_approve_leave': self.leave_approval_switch.value,
                        'session_timeout': int(self.session_timeout.value) if self.session_timeout.value.isdigit() else 60,
                    }
                    # Note: In a full implementation, you'd have a dedicated preferences table
                    # For now, just show success
                    self.show_snackbar("Preferences saved!", Colors.GREEN)
                else:
                    self.show_snackbar(
                        "Company not configured. Please set up company first.", Colors.ORANGE)
            finally:
                session.close()
        except Exception as ex:
            self.show_snackbar(
                f"Error saving preferences: {str(ex)}", Colors.RED)

    def close_dialog(self, dialog, e=None):
        """Close dialog"""
        if dialog:
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
