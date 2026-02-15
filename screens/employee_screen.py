"""
Vernika HRA - Employee Dashboard Screen
Employee personal dashboard with all features accessible
"""

import flet as ft
from datetime import datetime

from database.connection import get_db_session
from database.operations import (
    get_user_by_id,
    get_employee_by_user_id,
)


# Color constants
PRIMARY = "#009688"
ERROR = "#DC3545"
SUCCESS = "#28A745"
WARNING = "#FFC107"
INFO = "#17A2B8"
BACKGROUND = "#F8F9FA"
SURFACE = "#FFFFFF"
SURFACE_VARIANT = "#E8E8E8"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"
BLUE_500 = "#2196F3"
GREEN_500 = "#4CAF50"
ORANGE_500 = "#FF9800"
PURPLE_500 = "#9C27B0"
RED_500 = "#F44336"
TEAL_500 = "#009688"
CYAN_600 = "#00ACC1"
AMBER_500 = "#FFC107"
INDIGO_500 = "#3F51B5"
PINK_500 = "#E91E63"


class EmployeeScreen(ft.Container):
    def __init__(self, page, current_user):
        super().__init__()
        self._page = page
        self.current_user = current_user
        self.expand = True
        self.bgcolor = BACKGROUND

        # Get user ID
        self.user_id = None
        if isinstance(current_user, dict):
            self.user_id = current_user.get('id')

        self.content = self._build_content()

    def _build_content(self):
        """Build and add the employee content to the page"""
        # Header
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.DASHBOARD, color="WHITE", size=24),
                    ft.Text(
                        "Vernika HRA - Employee Dashboard",
                        size=18,
                        color="WHITE",
                        weight=ft.FontWeight.BOLD
                    ),
                ], spacing=10),
                ft.Container(expand=True),
                ft.Text(
                    f"Welcome, {self.current_user.get('username', 'Employee')}",
                    size=14,
                    color="WHITE"
                ),
                ft.Container(width=10),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color="WHITE",
                    on_click=self._handle_logout,
                    tooltip="Logout"
                )
            ])
        )

        # Get employee info for welcome message
        first_name = "Employee"
        try:
            db = get_db_session()
            emp = get_employee_by_user_id(db, self.user_id)
            if emp:
                first_name = emp.first_name or "Employee"
            db.close()
        except:
            pass

        # Quick actions section - all buttons now available
        action_cards = []

        # Profile card
        action_cards.append(
            self._create_action_card(
                "My Profile",
                "View and edit your profile",
                ft.Icons.PERSON,
                self._view_profile,
                PRIMARY
            )
        )

        # Tasks card
        action_cards.append(
            self._create_action_card(
                "My Tasks",
                "View your assigned tasks",
                ft.Icons.TASK,
                self._view_tasks,
                ORANGE_500
            )
        )

        # Time Off card
        action_cards.append(
            self._create_action_card(
                "Time Off",
                "Request time off",
                ft.Icons.CALENDAR_MONTH,
                self._request_time_off,
                PURPLE_500
            )
        )

        # Attendance card
        action_cards.append(
            self._create_action_card(
                "My Attendance",
                "View your attendance",
                ft.Icons.EVENT,
                self._view_attendance,
                BLUE_500
            )
        )

        # Chat card
        action_cards.append(
            self._create_action_card(
                "Team Chat",
                "Chat with colleagues",
                ft.Icons.CHAT,
                self._open_chat,
                TEAL_500
            )
        )

        # Mail card
        action_cards.append(
            self._create_action_card(
                "Internal Mail",
                "Send and receive messages",
                ft.Icons.EMAIL,
                self._open_mail,
                AMBER_500
            )
        )

        # Documents card
        action_cards.append(
            self._create_action_card(
                "Documents",
                "Access shared documents",
                ft.Icons.FOLDER,
                self._open_documents,
                INDIGO_500
            )
        )

        # Announcements card
        action_cards.append(
            self._create_action_card(
                "Announcements",
                "Company news and updates",
                ft.Icons.CAMPAIGN,
                self._view_announcements,
                RED_500
            )
        )

        # Teams card
        action_cards.append(
            self._create_action_card(
                "My Teams",
                "View your teams",
                ft.Icons.GROUP,
                self._view_teams,
                CYAN_600
            )
        )

        # Projects card
        action_cards.append(
            self._create_action_card(
                "Projects",
                "View assigned projects",
                ft.Icons.WORK,
                self._view_projects,
                PINK_500
            )
        )

        # Performance card
        action_cards.append(
            self._create_action_card(
                "Performance",
                "View performance reviews",
                ft.Icons.TRENDING_UP,
                self._view_performance,
                GREEN_500
            )
        )

        # Reports card
        action_cards.append(
            self._create_action_card(
                "My Reports",
                "View personal reports",
                ft.Icons.ASSESSMENT,
                self._view_reports,
                PURPLE_500
            )
        )

        quick_actions = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Quick Actions", size=20,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=15),
                ft.Row(action_cards[:4], spacing=20),
                ft.Container(height=15),
                ft.Row(action_cards[4:8], spacing=20),
                ft.Container(height=15),
                ft.Row(action_cards[8:12], spacing=20),
            ])
        )

        # My Information section
        my_info = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("My Information", size=20,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                self._get_employee_info_card()
            ])
        )

        # Recent Activity section
        activity = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Recent Activity", size=20,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
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

    def _create_action_card(self, title, subtitle, icon, on_click, color):
        """Create an action card with modern design"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=36, color=color),
                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle, size=11, color=TEXT_SECONDARY),
                    ft.Container(height=8),
                    ft.ElevatedButton(
                        "Open",
                        icon=ft.Icons.ARROW_FORWARD,
                        on_click=on_click,
                        style=ft.ButtonStyle(
                            bgcolor=color,
                            color="WHITE"
                        ),
                        height=32,
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=ft.padding.all(15),
                width=150
            ),
            elevation=2
        )

    def _get_employee_info_card(self):
        """Get employee information from database"""
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

                # Load user and linked employee profile
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
                        leading=ft.Icon(ft.Icons.LOGIN, color=SUCCESS)
                    ),
                    ft.ListTile(
                        title=ft.Text("Viewed dashboard"),
                        subtitle=ft.Text("Just now"),
                        leading=ft.Icon(ft.Icons.VISIBILITY, color=BLUE_500)
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

    def _open_chat(self, e):
        """Open chat screen"""
        from screens.chat_screen import ChatScreen
        self._page.clean()
        self._page.add(ChatScreen(self._page, self.current_user))

    def _open_mail(self, e):
        """Open mail screen"""
        from screens.mail_screen import MailScreen
        self._page.clean()
        self._page.add(MailScreen(self._page, self.current_user))

    def _open_documents(self, e):
        """Open documents screen"""
        from screens.documents_screen import DocumentsScreen
        self._page.clean()
        self._page.add(DocumentsScreen(self._page))

    def _view_announcements(self, e):
        """View announcements"""
        from screens.announcements_screen import AnnouncementsScreen
        self._page.clean()
        self._page.add(AnnouncementsScreen(self._page))

    def _view_teams(self, e):
        """View teams"""
        from screens.teams_screen import TeamsScreen
        self._page.clean()
        self._page.add(TeamsScreen(self._page, self.current_user))

    def _view_projects(self, e):
        """View projects"""
        from screens.projects_screen import ProjectsScreen
        self._page.clean()
        self._page.add(ProjectsScreen(self._page, self.current_user))

    def _view_performance(self, e):
        """View performance"""
        from screens.performance_screen import PerformanceScreen
        self._page.clean()
        self._page.add(PerformanceScreen(self._page))

    def _view_reports(self, e):
        """View reports"""
        from screens.reports_screen import ReportsScreen
        self._page.clean()
        self._page.add(ReportsScreen(self._page))

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
