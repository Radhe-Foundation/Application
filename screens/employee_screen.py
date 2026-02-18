"""
Vernika HRA - Employee Dashboard Screen
Employee personal dashboard with NavigationRail navigation
"""

import flet as ft
from datetime import datetime

from database.connection import get_db_session
from database.operations import (
    get_user_by_id,
    get_employee_by_user_id,
)


# Color constants - Match Admin Screen
PRIMARY = "#2E86AB"
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

        # Navigation rail state
        self._nav_rail_visible = True
        self._selected_index = 0

        # Get user ID
        self.user_id = None
        if isinstance(current_user, dict):
            self.user_id = current_user.get('id')

        self.content = self._build_content()

    def _build_content(self):
        """Build the employee content with custom sidebar navigation - matching admin screen style"""

        # Create toggle button for navigation rail
        def toggle_nav_rail(e):
            self._nav_rail_visible = not self._nav_rail_visible
            self.content.content.controls[0].visible = self._nav_rail_visible
            self.content.content.controls[1].visible = self._nav_rail_visible
            self._page.update()

        self.nav_toggle_btn = ft.IconButton(
            icon=ft.Icons.MENU_OPEN if self._nav_rail_visible else ft.Icons.MENU,
            tooltip="Toggle Navigation",
            on_click=toggle_nav_rail,
            icon_color=PRIMARY
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

        # Define navigation items with icon and label - Employee specific
        # FIXED: Added missing screens (Holiday, Meetings, Projects, Teams)
        nav_data = [
            (0, "Dashboard", ft.Icons.DASHBOARD, ft.Icons.DASHBOARD_OUTLINED),
            (1, "My Profile", ft.Icons.PERSON, ft.Icons.PERSON_OUTLINED),
            (2, "Team Chat", ft.Icons.CHAT, ft.Icons.CHAT_OUTLINED),
            (3, "Internal Mail", ft.Icons.EMAIL, ft.Icons.EMAIL_OUTLINED),
            (4, "My Tasks", ft.Icons.TASK, ft.Icons.TASK_OUTLINED),
            (5, "Time Off", ft.Icons.CALENDAR_MONTH,
             ft.Icons.CALENDAR_MONTH_OUTLINED),
            (6, "My Attendance", ft.Icons.EVENT, ft.Icons.EVENT_OUTLINED),
            (7, "My Teams", ft.Icons.GROUP, ft.Icons.GROUP_OUTLINED),
            (8, "Projects", ft.Icons.WORK, ft.Icons.WORK_OUTLINED),
            (9, "Holidays", ft.Icons.CALENDAR_TODAY,
             ft.Icons.CALENDAR_TODAY_OUTLINED),
            (10, "Meetings", ft.Icons.VIDEO_CALL, ft.Icons.VIDEO_CALL_OUTLINED),
            (11, "Documents", ft.Icons.FOLDER, ft.Icons.FOLDER_OUTLINED),
            (12, "Announcements", ft.Icons.CAMPAIGN, ft.Icons.CAMPAIGN_OUTLINED),
            (13, "Performance", ft.Icons.TRENDING_UP, ft.Icons.TRENDING_UP_OUTLINED),
            (14, "My Reports", ft.Icons.ASSESSMENT, ft.Icons.ASSESSMENT_OUTLINED),
        ]

        # Track selected index
        self._selected_nav_index = 0
        nav_items = []

        def create_nav_item(index, label, selected_icon, unselected_icon):
            def on_click(e):
                self._selected_nav_index = index
                # Update all nav items visual state
                for item in nav_items:
                    item.bgcolor = "transparent" if item != nav_items[index] else PRIMARY + "15"
                content_area.content = self._get_tab_content(index)
                self._page.update()

            is_selected = (index == self._selected_nav_index)

            return ft.Container(
                content=ft.Row([
                    ft.Icon(
                        selected_icon if is_selected else unselected_icon,
                        size=20,
                        color=PRIMARY if is_selected else TEXT_SECONDARY,
                    ),
                    ft.Text(
                        label,
                        size=13,
                        weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.W_400,
                        color=PRIMARY if is_selected else TEXT_SECONDARY,
                    ),
                ], spacing=8, alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                border_radius=8,
                bgcolor=PRIMARY + "15" if is_selected else "transparent",
                on_click=on_click,
                ink=True,
            )

        # Create nav items
        for idx, label, sel_icon, unsel_icon in nav_data:
            nav_items.append(create_nav_item(idx, label, sel_icon, unsel_icon))

        # Build sidebar with logo at top and scrollable nav items
        sidebar = ft.Container(
            width=180,
            bgcolor=SURFACE,
            content=ft.Column([
                # Logo at top center
                ft.Container(
                    content=ft.Image(
                        src="assets/logo/Vernikalogo.png",
                        width=100,
                        height=60,
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=ft.padding.only(top=15, bottom=10),
                ),
                # Divider below logo
                ft.Divider(height=1),
                # Navigation items in scrollable list
                ft.ListView(
                    controls=nav_items,
                    spacing=2,
                    padding=10,
                ),
            ], spacing=0),
            visible=self._nav_rail_visible,
        )

        # Build the main content based on selected index
        content_area = ft.Container(
            content=self._get_tab_content(self._selected_index),
            expand=True,
        )

        # Main layout with custom sidebar
        return ft.Container(
            content=ft.Row([
                # Custom Sidebar
                sidebar,
                ft.VerticalDivider(width=1, visible=self._nav_rail_visible),
                # Main content area
                ft.Container(
                    content=ft.Column([
                        # Header
                        self._create_header(),
                        content_area,
                        # Content
                    ], expand=True),
                    expand=True,
                ),
            ], expand=True),
            expand=True,
        )

    def _get_tab_content(self, index):
        """Get content for the selected tab"""
        if index == 0:
            return self._create_dashboard_tab()
        elif index == 1:
            return self._create_profile_tab()
        elif index == 2:
            return self._create_chat_tab()
        elif index == 3:
            return self._create_mail_tab()
        elif index == 4:
            return self._create_tasks_tab()
        elif index == 5:
            return self._create_leaves_tab()
        elif index == 6:
            return self._create_attendance_tab()
        elif index == 7:
            return self._create_teams_tab()
        elif index == 8:
            return self._create_projects_tab()
        elif index == 9:
            return self._create_holidays_tab()
        elif index == 10:
            return self._create_meetings_tab()
        elif index == 11:
            return self._create_documents_tab()
        elif index == 12:
            return self._create_announcements_tab()
        elif index == 13:
            return self._create_performance_tab()
        elif index == 14:
            return self._create_reports_tab()
        return self._create_dashboard_tab()

    def _create_header(self):
        """Create header with user info"""
        return ft.Container(
            content=ft.Row([
                # Navigation toggle button
                self.nav_toggle_btn,
                ft.Container(width=10),
                ft.Text(
                    "Vernika HRA - Employee Dashboard",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY
                ),
                ft.Container(expand=True),
                ft.Text(
                    f"Welcome, {self.current_user.get('username', 'Employee')}",
                    size=14,
                    color=TEXT_SECONDARY
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    tooltip="Logout",
                    on_click=self._handle_logout,
                    icon_color=ERROR
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=SURFACE,
        )

    def _create_dashboard_tab(self):
        """Create dashboard tab"""
        # Get employee info
        first_name = "Employee"
        try:
            db = get_db_session()
            emp = get_employee_by_user_id(db, self.user_id)
            if emp:
                first_name = emp.first_name or "Employee"
            db.close()
        except:
            pass

        # Quick actions section
        action_cards = []

        # Profile card
        action_cards.append(
            self._create_action_card(
                "My Profile",
                "View and edit your profile",
                ft.Icons.PERSON,
                lambda _: self._navigate_to(1),
                PRIMARY
            )
        )

        # Tasks card
        action_cards.append(
            self._create_action_card(
                "My Tasks",
                "View your assigned tasks",
                ft.Icons.TASK,
                lambda _: self._navigate_to(4),
                ORANGE_500
            )
        )

        # Time Off card
        action_cards.append(
            self._create_action_card(
                "Time Off",
                "Request time off",
                ft.Icons.CALENDAR_MONTH,
                lambda _: self._navigate_to(5),
                PURPLE_500
            )
        )

        # Attendance card
        action_cards.append(
            self._create_action_card(
                "My Attendance",
                "View your attendance",
                ft.Icons.EVENT,
                lambda _: self._navigate_to(6),
                BLUE_500
            )
        )

        # Chat card
        action_cards.append(
            self._create_action_card(
                "Team Chat",
                "Chat with colleagues",
                ft.Icons.CHAT,
                lambda _: self._navigate_to(2),
                TEAL_500
            )
        )

        # Mail card
        action_cards.append(
            self._create_action_card(
                "Internal Mail",
                "Send and receive messages",
                ft.Icons.EMAIL,
                lambda _: self._navigate_to(3),
                AMBER_500
            )
        )

        # Documents card
        action_cards.append(
            self._create_action_card(
                "Documents",
                "Access shared documents",
                ft.Icons.FOLDER,
                lambda _: self._navigate_to(7),
                INDIGO_500
            )
        )

        # Announcements card
        action_cards.append(
            self._create_action_card(
                "Announcements",
                "Company news and updates",
                ft.Icons.CAMPAIGN,
                lambda _: self._navigate_to(8),
                RED_500
            )
        )

        # Teams card
        action_cards.append(
            self._create_action_card(
                "My Teams",
                "View your teams",
                ft.Icons.GROUP,
                lambda _: self._navigate_to(9),
                CYAN_600
            )
        )

        # Projects card
        action_cards.append(
            self._create_action_card(
                "Projects",
                "View assigned projects",
                ft.Icons.WORK,
                lambda _: self._navigate_to(10),
                PINK_500
            )
        )

        # Performance card
        action_cards.append(
            self._create_action_card(
                "Performance",
                "View performance reviews",
                ft.Icons.TRENDING_UP,
                lambda _: self._navigate_to(11),
                GREEN_500
            )
        )

        # Reports card
        action_cards.append(
            self._create_action_card(
                "My Reports",
                "View personal reports",
                ft.Icons.ASSESSMENT,
                lambda _: self._navigate_to(12),
                PURPLE_500
            )
        )

        return ft.Container(
            content=ft.Column([
                ft.Text(f"Welcome, {first_name}!", size=24,
                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Container(height=20),

                # Quick Actions
                ft.Text("Quick Actions", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=15),
                ft.Row(action_cards[:4], spacing=20),
                ft.Container(height=15),
                ft.Row(action_cards[4:8], spacing=20),
                ft.Container(height=15),
                ft.Row(action_cards[8:12], spacing=20),

                ft.Container(height=30),

                # Info Section - Side by side (left and right)
                ft.Row([
                    # Left side - My Information
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Text("My Information", size=18,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Container(height=10),
                            self._get_employee_info_card(),
                        ], scroll=ft.ScrollMode.AUTO)
                    ),
                    ft.Container(width=20),
                    # Right side - Recent Activity
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Text("Recent Activity", size=18,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Container(height=10),
                            self._create_recent_activity_section(),
                        ], scroll=ft.ScrollMode.AUTO)
                    ),
                ], spacing=10),
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

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

    def _create_profile_tab(self):
        """Create profile tab"""
        from screens.profile_screen import ProfileScreen
        return ft.Container(content=ProfileScreen(self._page, self.current_user), expand=True)

    def _create_chat_tab(self):
        """Create chat tab"""
        from screens.chat_screen import ChatScreen
        return ft.Container(content=ChatScreen(self._page, self.current_user), expand=True)

    def _create_mail_tab(self):
        """Create mail tab"""
        from screens.mail_screen import MailScreen
        return ft.Container(content=MailScreen(self._page, self.current_user), expand=True)

    def _create_tasks_tab(self):
        """Create tasks tab"""
        from screens.tasks_screen import TasksScreen
        return ft.Container(content=TasksScreen(self._page, self.current_user), expand=True)

    def _create_leaves_tab(self):
        """Create leaves tab"""
        from screens.leaves_screen import LeavesScreen
        return ft.Container(content=LeavesScreen(self._page, self.current_user, view_mode="employee"), expand=True)

    def _create_attendance_tab(self):
        """Create attendance tab"""
        from screens.attendance_screen import AttendanceScreen
        return ft.Container(content=AttendanceScreen(self._page, self.current_user, view_mode="employee"), expand=True)

    def _create_documents_tab(self):
        """Create documents tab"""
        from screens.documents_screen import DocumentsScreen
        return ft.Container(content=DocumentsScreen(self._page), expand=True)

    def _create_announcements_tab(self):
        """Create announcements tab"""
        from screens.announcements_screen import AnnouncementsScreen
        return ft.Container(content=AnnouncementsScreen(self._page), expand=True)

    def _create_teams_tab(self):
        """Create teams tab"""
        from screens.teams_screen import TeamsScreen
        return ft.Container(content=TeamsScreen(self._page, self.current_user), expand=True)

    def _create_projects_tab(self):
        """Create projects tab"""
        from screens.projects_screen import ProjectsScreen
        return ft.Container(content=ProjectsScreen(self._page, self.current_user), expand=True)

    def _create_holidays_tab(self):
        """Create holidays tab"""
        from screens.holidays_screen import HolidaysScreen
        return ft.Container(content=HolidaysScreen(self._page, self.current_user), expand=True)

    def _create_meetings_tab(self):
        """Create meetings tab"""
        from screens.meetings_screen import MeetingsScreen
        return ft.Container(content=MeetingsScreen(self._page, self.current_user), expand=True)

    def _create_performance_tab(self):
        """Create performance tab"""
        from screens.performance_screen import PerformanceScreen
        return ft.Container(content=PerformanceScreen(self._page), expand=True)

    def _create_reports_tab(self):
        """Create reports tab"""
        from screens.reports_screen import ReportsScreen
        return ft.Container(content=ReportsScreen(self._page), expand=True)

    def _navigate_to(self, index):
        """Navigate to a specific tab"""
        self._selected_index = index
        # Update navigation item visual state
        if hasattr(self, '_selected_nav_index'):
            self._selected_nav_index = index
        # Navigate to the tab content - content_area is at controls[2].content.controls[1]
        main_container = self.content.content.controls[2]
        main_container.content.controls[1].content = self._get_tab_content(
            index)
        self._page.update()

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
