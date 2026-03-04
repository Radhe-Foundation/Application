"""
Vernika HRA - Employee Dashboard Screen
Employee personal dashboard with NavigationRail navigation
"""

import flet as ft
import os
from datetime import datetime

from database.session_manager import get_session, get_db_session, check_db_connection
from database.operations import (
    get_user_by_id,
    get_employee_by_user_id,
)

# Logo path resolution - similar to login_screen


def get_logo_path():
    """Get the absolute path to the Vernikalogo"""
    # Try multiple paths to find the logo
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "assets", "logo", "Vernikalogo.png"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "assets", "logo", "Vernikalogo.png"),
        "assets/logo/Vernikalogo.png",
    ]

    for logo_path in possible_paths:
        if os.path.exists(logo_path):
            # Use forward slashes for Flet with leading slash
            flet_path = logo_path.replace("\\", "/")
            if not flet_path.startswith("/"):
                flet_path = "/" + flet_path
            return flet_path

    # Fallback to relative path
    return "/assets/logo/Vernikalogo.png"


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

        # Loading state
        self._is_loading = False
        self._loading_progress = ft.ProgressRing(
            width=20, height=20, visible=False)

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
            # Update the icon to toggle between MENU_OPEN and MENU
            self.nav_toggle_btn.icon = ft.Icons.MENU_OPEN if self._nav_rail_visible else ft.Icons.MENU
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
        except Exception:
            pass

        # Define navigation items with icon and label - Employee specific
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
            (11, "Announcements", ft.Icons.CAMPAIGN, ft.Icons.CAMPAIGN_OUTLINED),
            # Business Screens
            (12, "Data Entry", ft.Icons.TABLE_ROWS, ft.Icons.TABLE_ROWS_OUTLINED),
            (13, "Inventory", ft.Icons.INVENTORY, ft.Icons.INVENTORY_OUTLINED),
            (14, "Transactions", ft.Icons.PAYMENT, ft.Icons.PAYMENT_OUTLINED),
            (15, "Time Track", ft.Icons.TIMER, ft.Icons.TIMER_OUTLINED),
            # Org Tree
            (16, "Org Tree", ft.Icons.ACCOUNT_TREE, ft.Icons.ACCOUNT_TREE_OUTLINED),
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
                        src=get_logo_path(),
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
                    expand=True,
                ),
            ], spacing=0),
            visible=self._nav_rail_visible,
        )

        # Build the main content based on selected index
        content_area = ft.Container(
            content=self._get_tab_content(self._selected_index),
            expand=True,
        )

        # Main layout with custom sidebar - NO duplicate header here
        # Each screen (including dashboard) will have its own header via wrapper
        return ft.Container(
            content=ft.Row([
                # Custom Sidebar
                sidebar,
                ft.VerticalDivider(width=1, visible=self._nav_rail_visible),
                # Main content area (each tab has its own header via wrapper)
                content_area,
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
            return self._create_announcements_tab()
        # Business Screens (indices 12-15)
        elif index == 12:
            return self._create_data_entry_tab()
        elif index == 13:
            return self._create_inventory_tab()
        elif index == 14:
            return self._create_transactions_tab()
        elif index == 15:
            return self._create_time_tracking_tab()
        elif index == 16:
            return self._create_org_tree_tab()
        return self._create_dashboard_tab()

    def _handle_back(self, e):
        """Handle back navigation - return to login"""
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))

    def _create_header(self):
        """Create header with user info, toggle button and logout"""
        return ft.Container(
            content=ft.Row([
                # Navigation toggle button
                self.nav_toggle_btn,
                ft.Container(width=10),
                ft.Text(
                    "Vernika HRA - Employee Portal",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY
                ),
                ft.Container(expand=True),
                # Loading indicator
                self._loading_progress,
                ft.Container(width=10),
                # Refresh button
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh",
                    on_click=lambda e: self._refresh(),
                    icon_color=PRIMARY
                ),
                ft.Container(width=5),
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
        from screens.profile_screen import ProfileScreen

        # Get employee info
        first_name = "Employee"
        try:
            db = get_db_session()
            emp = get_employee_by_user_id(db, self.user_id)
            if emp:
                first_name = emp.first_name or "Employee"
            db.close()
        except Exception:
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

        # Documents card - navigate to Meetings (index 10)
        action_cards.append(
            self._create_action_card(
                "Documents",
                "Access shared documents",
                ft.Icons.FOLDER,
                lambda _: self._navigate_to(10),
                INDIGO_500
            )
        )

        # Announcements card
        action_cards.append(
            self._create_action_card(
                "Announcements",
                "Company news and updates",
                ft.Icons.CAMPAIGN,
                lambda _: self._navigate_to(11),
                RED_500
            )
        )

        # Teams card
        action_cards.append(
            self._create_action_card(
                "My Teams",
                "View your teams",
                ft.Icons.GROUP,
                lambda _: self._navigate_to(7),
                CYAN_600
            )
        )

        # Projects card
        action_cards.append(
            self._create_action_card(
                "Projects",
                "View assigned projects",
                ft.Icons.WORK,
                lambda _: self._navigate_to(8),
                PINK_500
            )
        )

        # Holidays card
        action_cards.append(
            self._create_action_card(
                "Holidays",
                "Company holidays",
                ft.Icons.CALENDAR_TODAY,
                lambda _: self._navigate_to(9),
                GREEN_500
            )
        )

        # Meetings card - navigate to meetings (index 10)
        action_cards.append(
            self._create_action_card(
                "Meetings",
                "View scheduled meetings",
                ft.Icons.VIDEO_CALL,
                lambda _: self._navigate_to(10),
                PURPLE_500
            )
        )

        # Business Screen Cards - Data Entry (index 12)
        action_cards.append(
            self._create_action_card(
                "Data Entry",
                "Spreadsheet & data management",
                ft.Icons.TABLE_ROWS,
                lambda _: self._navigate_to(12),
                CYAN_600
            )
        )

        # Inventory (index 13)
        action_cards.append(
            self._create_action_card(
                "Inventory",
                "Stock & inventory management",
                ft.Icons.INVENTORY,
                lambda _: self._navigate_to(13),
                ORANGE_500
            )
        )

        # Transactions (index 14)
        action_cards.append(
            self._create_action_card(
                "Transactions",
                "Financial transactions",
                ft.Icons.PAYMENT,
                lambda _: self._navigate_to(14),
                TEAL_500
            )
        )

        # Time Track (index 15)
        action_cards.append(
            self._create_action_card(
                "Time Track",
                "Employee time tracking",
                ft.Icons.TIMER,
                lambda _: self._navigate_to(15),
                RED_500
            )
        )

        # Dashboard content
        dashboard_content = ft.Container(
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
                ft.Container(height=15),
                ft.Row(action_cards[12:16], spacing=20),

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

        # Wrap with header - show back button False for dashboard
        return self._wrap_with_employee_header("Dashboard", dashboard_content, show_back_button=False)

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
        profile_content = ProfileScreen(
            self._page, self.current_user, show_own_header=False)
        return self._wrap_with_employee_header("My Profile", profile_content)

    def _create_chat_tab(self):
        """Create chat tab"""
        from screens.chat_screen import ChatScreen
        chat_content = ChatScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("Team Chat", chat_content)

    def _create_mail_tab(self):
        """Create mail tab"""
        from screens.mail_screen import MailScreen
        mail_content = MailScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("Internal Mail", mail_content)

    def _create_tasks_tab(self):
        """Create tasks tab"""
        from screens.tasks_screen import TasksScreen
        tasks_content = TasksScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("My Tasks", tasks_content)

    def _create_leaves_tab(self):
        """Create leaves tab"""
        from screens.leaves_screen import LeavesScreen
        leaves_content = LeavesScreen(
            self._page, self.current_user, view_mode="employee")
        return self._wrap_with_employee_header("Time Off", leaves_content)

    def _create_attendance_tab(self):
        """Create attendance tab"""
        from screens.attendance_screen import AttendanceScreen
        attendance_content = AttendanceScreen(
            self._page, self.current_user, view_mode="employee")
        return self._wrap_with_employee_header("My Attendance", attendance_content)

    def _create_announcements_tab(self):
        """Create announcements tab"""
        from screens.announcements_screen import AnnouncementsScreen
        announcements_content = AnnouncementsScreen(self._page)
        return self._wrap_with_employee_header("Announcements", announcements_content)

    def _create_teams_tab(self):
        """Create teams tab"""
        from screens.teams_screen import TeamsScreen
        teams_content = TeamsScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("My Teams", teams_content)

    def _create_projects_tab(self):
        """Create projects tab"""
        from screens.projects_screen import ProjectsScreen
        projects_content = ProjectsScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("Projects", projects_content)

    def _create_holidays_tab(self):
        """Create holidays tab"""
        from screens.holidays_screen import HolidaysScreen
        holidays_content = HolidaysScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("Holidays", holidays_content)

    def _create_meetings_tab(self):
        """Create meetings tab"""
        from screens.meetings_screen import MeetingsScreen
        meetings_content = MeetingsScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("Meetings", meetings_content)

    # ==================== Business Screen Tabs ====================

    def _create_data_entry_tab(self):
        """Create Data Entry tab - spreadsheet and data management"""
        from screens.data_entry_screen import DataEntryScreen
        data_entry_content = DataEntryScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("Data Entry", data_entry_content)

    def _create_inventory_tab(self):
        """Create Inventory tab - stock management"""
        from screens.inventory_screen import InventoryScreen
        inventory_content = InventoryScreen(self._page, self.current_user)
        return self._wrap_with_employee_header("Inventory", inventory_content)

    def _create_transactions_tab(self):
        """Create Transactions tab - financial transactions"""
        from screens.transactions_screen import TransactionsScreen
        transactions_content = TransactionsScreen(
            self._page, self.current_user)
        return self._wrap_with_employee_header("Transactions", transactions_content)

    def _create_time_tracking_tab(self):
        """Create Time Tracking tab - employee time logs"""
        from screens.time_tracking_screen import TimeTrackingScreen
        time_tracking_content = TimeTrackingScreen(
            self._page, self.current_user)
        return self._wrap_with_employee_header("Time Track", time_tracking_content)

    def _create_org_tree_tab(self):
        """Create Organization Tree tab"""
        from screens.organization_tree_screen import OrganizationTreeScreen
        org_tree_content = OrganizationTreeScreen(
            self._page, self.current_user)
        return self._wrap_with_employee_header("Org Tree", org_tree_content)

    def _wrap_with_employee_header(self, screen_title: str, content, show_back_button: bool = True):
        """Wrap any screen content with the consistent employee portal header"""

        def handle_back(e):
            """Handle back navigation to return to dashboard"""
            self._selected_index = 0
            if hasattr(self, '_selected_nav_index'):
                self._selected_nav_index = 0
            # Update nav items visual state
            try:
                sidebar = self.content.content.controls[0]
                if hasattr(sidebar, 'content') and hasattr(sidebar.content, 'controls'):
                    nav_items = sidebar.content.controls
                    for item in nav_items:
                        item.bgcolor = "transparent"
                    if nav_items:
                        nav_items[0].bgcolor = PRIMARY + "15"
            except Exception as e:
                print(f"Error updating nav: {e}")
            # Navigate to dashboard
            main_container = self.content.content.controls[2]
            main_container.content = self._get_tab_content(0)
            self._page.update()

        return ft.Container(
            content=ft.Column([
                # Consistent Header for all employee screens - matching admin screen style
                ft.Container(
                    content=ft.Row([
                        # Back button (navigation button)
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            tooltip="Back to Dashboard",
                            on_click=handle_back,
                            icon_color=PRIMARY
                        ) if show_back_button else ft.Container(width=0),
                        # Navigation toggle - menu button
                        self.nav_toggle_btn,
                        ft.Container(width=10),
                        # Screen title
                        ft.Text(
                            f"Vernika HRA - {screen_title}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=PRIMARY
                        ),
                        ft.Container(expand=True),
                        # Welcome message
                        ft.Text(
                            f"Welcome, {self.current_user.get('username', 'Employee') if isinstance(self.current_user, dict) else 'Employee'}",
                            size=14,
                            color=TEXT_SECONDARY
                        ),
                        ft.Container(width=10),
                        # Logout button
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            tooltip="Logout",
                            on_click=self._handle_logout,
                            icon_color=ERROR
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=20, vertical=15),
                    bgcolor=SURFACE,
                ),
                # Content area
                ft.Container(
                    content=content,
                    expand=True,
                ),
            ], expand=True),
            expand=True,
        )

    def _navigate_to(self, index):
        """Navigate to a specific tab"""
        self._selected_index = index
        # Update navigation item visual state
        if hasattr(self, '_selected_nav_index'):
            self._selected_nav_index = index
        # Navigate to the tab content - content_area is at controls[2]
        # content_area.content contains the actual tab content
        try:
            main_container = self.content.content.controls[2]
            main_container.content = self._get_tab_content(index)
            self._page.update()
        except Exception as e:
            print(f"Error in navigation: {e}")
            # Fallback: rebuild the entire content
            self.content = self._build_content()
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

    def _refresh(self):
        """Refresh the employee screen"""
        # Rebuild content to refresh data
        self.content = self._build_content()
        self._page.update()


def show_employee_dashboard(page, current_user):
    """Helper function to show employee dashboard"""
    page.clean()
    page.add(EmployeeScreen(page, current_user))
