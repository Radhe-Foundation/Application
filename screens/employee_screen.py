"""
Vernika HRA - Employee Dashboard Screen
Employee personal dashboard with limited access
"""

import flet as ft
from datetime import datetime

from database.connection import get_db_session
from database.operations import (
    get_user_by_id,
    get_employee_by_user_id,
)
from utils.screen_access import (
    SCREEN_ACCESS_CONFIG, get_user_screen_access, check_screen_access
)


class EmployeeScreen(ft.Container):
    def __init__(self, page, current_user):
        super().__init__()
        self._page = page
        self.current_user = current_user
        self.expand = True
        self.bgcolor = "#F5F5F5"

        # Get user ID for permission checks
        self.user_id = None
        if isinstance(current_user, dict):
            self.user_id = current_user.get('id')

        # Load screen access permissions
        self.screen_access = get_user_screen_access(
            self.user_id) if self.user_id else {}

        self.content = self._build_content()

    def _get_screen_access(self, screen_key: str) -> bool:
        """Check if user has access to a specific screen"""
        # Admins always have access
        if isinstance(self.current_user, dict):
            if self.current_user.get('role', '').lower() == 'admin':
                return True
        return self.screen_access.get(screen_key, False)

    def _build_content(self):
        """Build and add the employee content to the page"""
        # Header - No back button for employees to prevent admin access
        header = ft.Container(
            padding=15,
            bgcolor="#009688",
            content=ft.Row([
                ft.Text(
                    f"Welcome, {self.current_user.get('username', 'Employee')}!",
                    size=18,
                    color="WHITE",
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Logout",
                    on_click=self._handle_logout,
                    style=ft.ButtonStyle(bgcolor="WHITE", color="#009688")
                )
            ])
        )

        # Quick actions section - only show screens user has access to
        action_cards = []

        # Profile card (always available)
        action_cards.append(
            self._create_action_card(
                "My Profile",
                "View and edit your profile",
                ft.Icons.PERSON,
                self._view_profile,
                enabled=True  # Always enabled
            )
        )

        # Tasks card (check access)
        if self._get_screen_access("tasks"):
            action_cards.append(
                self._create_action_card(
                    "My Tasks",
                    "View your assigned tasks",
                    ft.Icons.TASK,
                    self._view_tasks,
                    enabled=True
                )
            )
        else:
            action_cards.append(
                self._create_action_card(
                    "My Tasks",
                    "Access restricted",
                    ft.Icons.TASK,
                    self._show_access_denied,
                    enabled=False
                )
            )

        # Time Off card (check access)
        if self._get_screen_access("leaves"):
            action_cards.append(
                self._create_action_card(
                    "Time Off",
                    "Request time off",
                    ft.Icons.CALENDAR_MONTH,
                    self._request_time_off,
                    enabled=True
                )
            )
        else:
            action_cards.append(
                self._create_action_card(
                    "Time Off",
                    "Access restricted",
                    ft.Icons.CALENDAR_MONTH,
                    self._show_access_denied,
                    enabled=False
                )
            )

        # Attendance card (check access)
        if self._get_screen_access("attendance"):
            action_cards.append(
                self._create_action_card(
                    "My Attendance",
                    "View your attendance",
                    ft.Icons.EVENT,
                    self._view_attendance,
                    enabled=True
                )
            )
        else:
            action_cards.append(
                self._create_action_card(
                    "My Attendance",
                    "Access restricted",
                    ft.Icons.EVENT,
                    self._show_access_denied,
                    enabled=False
                )
            )

        quick_actions = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Quick Actions", size=20,
                        weight=ft.FontWeight.BOLD, color="#333"),
                ft.Row(action_cards, spacing=20)
            ])
        )

        # My Information section
        my_info = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("My Information", size=20,
                        weight=ft.FontWeight.BOLD, color="#333"),
                self._get_employee_info_card()
            ])
        )

        # Recent Activity section
        activity = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Recent Activity", size=20,
                        weight=ft.FontWeight.BOLD, color="#333"),
                self._create_recent_activity_section()
            ])
        )

        content = ft.Column([
            header,
            quick_actions,
            my_info,
            activity
        ], expand=True, scroll=ft.ScrollMode.AUTO)

        return content

    def _create_action_card(self, title, subtitle, icon, on_click, enabled=True):
        """Create an action card"""
        # If disabled, change appearance
        opacity = 0.6 if not enabled else 1.0
        icon_color = "#9E9E9E" if not enabled else "#009688"
        bgcolor = "#F5F5F5" if not enabled else "WHITE"

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=40, color=icon_color),
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD,
                            opacity=opacity),
                    ft.Text(subtitle, size=12, color="#757575",
                            opacity=opacity),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Open" if enabled else "Locked",
                        icon=ft.Icons.ARROW_FORWARD if enabled else ft.Icons.LOCK,
                        on_click=on_click,
                        style=ft.ButtonStyle(
                            bgcolor="#009688" if enabled else "#E0E0E0",
                            color="WHITE" if enabled else "#757575"
                        ),
                        disabled=not enabled
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=ft.padding.all(20),
                width=200
            ),
            elevation=3
        )

    def _show_access_denied(self, e):
        """Show access denied message"""
        snack = ft.SnackBar(
            content=ft.Text(
                "Access Restricted: Please contact administrator for access"),
            bgcolor="#DC3545"
        )
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _get_employee_info_card(self):
        """Get employee information from database and display as card (cloud-ready via SQLAlchemy)"""
        first_name = "Not provided"
        last_name = ""
        department = "Not assigned"
        position = "Not assigned"
        phone = "Not provided"
        email = self.current_user.get("email") or self.current_user.get(
            "username", ""
        )

        user_id = self.current_user.get("id")

        if user_id:
            db = None
            try:
                db = get_db_session()

                # Load user and linked employee profile using SQLAlchemy
                user = get_user_by_id(db, user_id)
                if user and user.email:
                    email = user.email

                employee = get_employee_by_user_id(db, user_id)

                if employee:
                    first_name = employee.first_name or "Not provided"
                    last_name = employee.last_name or ""
                    phone = employee.phone or "Not provided"

                    if employee.department and getattr(employee.department, "name", None):
                        department = employee.department.name

                    if employee.position and getattr(employee.position, "title", None):
                        position = employee.position.title

            except Exception as e:
                print(f"Error loading employee info: {e}")
            finally:
                if db is not None:
                    db.close()

        full_name = f"{first_name} {last_name}".strip(
        ) if last_name else first_name

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text("Personal Information",
                                      weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.BADGE),
                    ),
                    ft.Divider(),
                    ft.ListTile(
                        title=ft.Text("Full Name"),
                        subtitle=ft.Text(full_name)
                    ),
                    ft.ListTile(
                        title=ft.Text("Department"),
                        subtitle=ft.Text(department)
                    ),
                    ft.ListTile(
                        title=ft.Text("Position"),
                        subtitle=ft.Text(position)
                    ),
                    ft.ListTile(
                        title=ft.Text("Phone"),
                        subtitle=ft.Text(phone)
                    ),
                    ft.ListTile(
                        title=ft.Text("Email"),
                        subtitle=ft.Text(email)
                    ),
                ]),
                padding=ft.padding.all(10),
                width=400
            ),
            elevation=2
        )

    def _create_recent_activity_section(self):
        """Create recent activity section"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text("Recent Activity",
                                      weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.HISTORY)
                    ),
                    ft.Divider(),
                    ft.ListTile(
                        title=ft.Text("Logged in"),
                        subtitle=ft.Text(
                            datetime.now().strftime("%Y-%m-%d %H:%M")),
                        leading=ft.Icon(ft.Icons.LOGIN, color="#4CAF50")
                    ),
                    ft.ListTile(
                        title=ft.Text("Viewed dashboard"),
                        subtitle=ft.Text("Just now"),
                        leading=ft.Icon(ft.Icons.VISIBILITY, color="#2196F3")
                    )
                ]),
                padding=ft.padding.all(10),
                width=400
            ),
            elevation=2
        )

    def _view_profile(self, e):
        """View profile"""
        from screens.profile_screen import ProfileScreen
        self._page.clean()
        self._page.add(ProfileScreen(self._page, self.current_user))

    def _view_tasks(self, e):
        """View tasks"""
        from screens.tasks_screen import TasksScreen
        self._page.clean()
        self._page.add(TasksScreen(self._page, self.current_user))

    def _request_time_off(self, e):
        """Request time off"""
        from screens.leaves_screen import LeavesScreen
        self._page.clean()
        self._page.add(LeavesScreen(
            self._page, self.current_user, view_mode="employee"))

    def _view_attendance(self, e):
        """View own attendance"""
        from screens.attendance_screen import AttendanceScreen
        self._page.clean()
        self._page.add(AttendanceScreen(
            self._page, self.current_user, view_mode="employee"))

    def _handle_logout(self, e):
        """Handle logout"""
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))

    def _show_snack(self, message):
        """Show a snackbar message"""
        snack = ft.SnackBar(content=ft.Text(message), open=True)
        self._page.overlay.append(snack)
        self._page.update()


def show_employee_dashboard(page, current_user):
    """Helper function to show employee dashboard"""
    page.clean()
    page.add(EmployeeScreen(page, current_user))
