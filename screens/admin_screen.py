"""
Vernika Application - Admin Screen
Admin dashboard with full management capabilities for all modules
"""

import flet as ft
# Import both for backward compatibility
from database.session_manager import get_session, get_db_session
from database.operations import get_dashboard_stats as get_db_stats
from auth.role_check import check_admin_access
# Import web helpers for responsive design
from utils.web_helpers import adaptive_value, Breakpoints

# Color constants
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
GREEN_600 = "#4CAF50"
BLUE_600 = "#2196F3"
TEAL_500 = "#009688"
CYAN_600 = "#00ACC1"
AMBER_500 = "#FFC107"
INDIGO_500 = "#3F51B5"
PINK_500 = "#E91E63"


class AdminScreen(ft.Container):
    """
    Admin dashboard screen with full management capabilities
    """

    def __init__(self, page, current_user=None):
        super().__init__()
        self._page = page
        self.current_user = current_user
        self.expand = True
        self.alignment = ft.alignment.Alignment(0, 0)

        # State variable to track if refresh is needed
        self._needs_refresh = False

        # Loading state
        self._is_loading = False
        self._loading_progress = ft.ProgressRing(
            width=20, height=20, visible=False)

        # Navigation rail state
        self._nav_rail_visible = True

        # Verify admin access
        if not check_admin_access(current_user):
            self._handle_access_denied()
            return

        # Build content with tabs
        self.content = self._build_content()
        print("✓ AdminScreen initialized")

    def refresh(self):
        """Refresh the entire admin screen including dashboard stats"""
        self._needs_refresh = False
        self.content = self._build_content()
        self._page.update()

    def _toggle_nav_rail(self, e=None):
        """Toggle navigation rail visibility"""
        self._nav_rail_visible = not self._nav_rail_visible
        try:
            # Update the icon to toggle between MENU_OPEN and MENU
            self.nav_toggle_btn.icon = ft.Icons.MENU_OPEN if self._nav_rail_visible else ft.Icons.MENU
            self.content.content.controls[0].visible = self._nav_rail_visible
            self.content.content.controls[1].visible = self._nav_rail_visible
            self._page.update()
        except Exception as ex:
            print(f"Error toggling nav rail: {ex}")

    def refresh_dashboard(self):
        """Refresh only the dashboard stats without rebuilding entire screen"""
        # Get the dashboard content area
        try:
            # Rebuild dashboard tab content
            # Get the content container
            content = self.content.content.controls[2]
            content.content = self._get_tab_content(0)  # 0 is dashboard tab
            self._page.update()
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
            # Fallback to full refresh
            self.refresh()

    @property
    def page(self):
        """Get the page reference safely"""
        return self._page

    @page.setter
    def page(self, value):
        """Set the page reference"""
        self._page = value

    def _handle_access_denied(self):
        """Handle access denied for non-admin users"""
        snack = ft.SnackBar(
            content=ft.Text("Access Denied: Admin privileges required"),
            bgcolor=ERROR
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

        from screens.login_screen import LoginScreen
        self.page.clean()
        self.page.add(LoginScreen(self.page))

    def _build_content(self):
        """Build the main content with tabs"""

        # Get window width for responsive design
        try:
            window_width = getattr(self._page, 'window_width', 1200)
        except:
            window_width = 1200

        # Determine responsive values
        is_mobile = window_width < 600
        is_tablet = window_width < 900

        # Responsive sidebar width
        if is_mobile:
            sidebar_width = 0  # Hidden on mobile
        elif is_tablet:
            sidebar_width = 70  # Icon only on tablet
        else:
            sidebar_width = 160

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

        # Custom Navigation Sidebar - compact with proper icon-text alignment
        nav_items = []

        # FIXED: Navigation only includes existing screens
        nav_data = [
            (0, "Dashboard", ft.Icons.DASHBOARD, ft.Icons.DASHBOARD_OUTLINED),
            (1, "Chat", ft.Icons.CHAT, ft.Icons.CHAT_OUTLINED),
            (2, "Mail", ft.Icons.EMAIL, ft.Icons.EMAIL_OUTLINED),
            (3, "Tasks", ft.Icons.TASK, ft.Icons.TASK_OUTLINED),
            (4, "Todo", ft.Icons.LIST_ALT, ft.Icons.LIST_ALT_OUTLINED),
            (5, "Employees", ft.Icons.BADGE, ft.Icons.BADGE_OUTLINED),
            (6, "Depts", ft.Icons.BUSINESS, ft.Icons.BUSINESS_OUTLINED),
            (7, "Positions", ft.Icons.WORK, ft.Icons.WORK_OUTLINED),
            (8, "Attendance", ft.Icons.EVENT, ft.Icons.EVENT_OUTLINED),
            (9, "Leave", ft.Icons.EVENT_BUSY, ft.Icons.EVENT_BUSY_OUTLINED),
            (10, "Teams", ft.Icons.GROUP, ft.Icons.GROUP_OUTLINED),
            (11, "Projects", ft.Icons.FOLDER_SPECIAL,
             ft.Icons.FOLDER_SPECIAL_OUTLINED),
            (12, "Holidays", ft.Icons.CALENDAR_TODAY,
             ft.Icons.CALENDAR_TODAY_OUTLINED),
            (13, "Meetings", ft.Icons.VIDEO_CALL, ft.Icons.VIDEO_CALL_OUTLINED),
            (14, "News", ft.Icons.CAMPAIGN, ft.Icons.CAMPAIGN_OUTLINED),
            (15, "Settings", ft.Icons.SETTINGS, ft.Icons.SETTINGS_OUTLINED),
            (16, "Org Tree", ft.Icons.ACCOUNT_TREE, ft.Icons.ACCOUNT_TREE_OUTLINED),
            (17, "Data Entry", ft.Icons.TABLE_ROWS, ft.Icons.TABLE_ROWS_OUTLINED),
            (18, "Inventory", ft.Icons.INVENTORY, ft.Icons.INVENTORY_OUTLINED),
            (19, "Transactions", ft.Icons.PAYMENT, ft.Icons.PAYMENT_OUTLINED),
            (20, "Time Track", ft.Icons.TIMER, ft.Icons.TIMER_OUTLINED),
            (21, "Storage", ft.Icons.CLOUD, ft.Icons.CLOUD_OUTLINED),
            (22, "CRM", ft.Icons.PEOPLE, ft.Icons.PEOPLE_OUTLINED),
        ]

        # Track selected index
        self._selected_nav_index = 0

        def create_nav_item(index, label, selected_icon, unselected_icon):
            def on_click(e):
                self._selected_nav_index = index
                # Update all nav items visual state
                for item in nav_items:
                    item.bgcolor = "transparent" if item != nav_items[index] else PRIMARY + "15"
                content = self.content.content.controls[2]
                content.content = self._get_tab_content_lazy(index)
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

        # Build sidebar with scroll - responsive width
        sidebar = ft.Container(
            width=sidebar_width,
            bgcolor=SURFACE,
            content=ft.ListView(
                controls=nav_items,
                spacing=2,
                padding=10,
            ),
            visible=self._nav_rail_visible and sidebar_width > 0,
        )

        # Create tabs with custom sidebar navigation
        return ft.Container(
            content=ft.Row([
                # Custom Navigation Sidebar
                sidebar,
                # Vertical divider
                ft.VerticalDivider(width=1, visible=self._nav_rail_visible),
                # Main content area
                ft.Container(
                    content=ft.Column([
                        # Header with toggle button
                        self._create_header(),
                        # Content container
                        ft.Container(
                            content=self._get_tab_content(0),
                            expand=True,
                        ),
                    ], expand=True),
                    expand=True,
                    padding=ft.padding.all(0),
                ),
            ], expand=True),
            expand=True,
        )

    def _on_nav_change(self, e):
        """Handle navigation rail change - OPTIMIZED with lazy loading"""
        index = e.control.selected_index

        # Lazy load tab content only when clicked
        content = self.content.content.controls[2]  # Get the content container
        content.content = self._get_tab_content_lazy(index)
        self.page.update()

    def _wrap_with_admin_header(self, screen_title: str, content, show_back_button: bool = True):
        """Wrap any screen content with the consistent admin header"""

        def handle_back(e):
            """Handle back navigation to return to dashboard"""
            # Navigate back to dashboard tab (index 0)
            self._selected_nav_index = 0
            # Update nav items visual state
            for item in nav_items:
                item.bgcolor = "transparent"
            if nav_items:
                nav_items[0].bgcolor = PRIMARY + "15"
            # Navigate to dashboard
            content_area = self.content.content.controls[2]
            content_area.content = self._get_tab_content_lazy(0)
            self._page.update()

        # Get nav_items from _build_content for back navigation
        nav_items = []
        try:
            # Try to get nav_items from the sidebar
            sidebar = self.content.content.controls[0]
            if hasattr(sidebar, 'content'):
                # sidebar.content is the ListView directly (not another Container)
                list_view = sidebar.content
                if hasattr(list_view, 'controls'):
                    nav_items = list_view.controls
        except Exception as e:
            print(f"Could not get nav_items: {e}")

        return ft.Container(
            content=ft.Column([
                # Consistent Header for all admin screens - matching employee portal style
                ft.Container(
                    content=ft.Row([
                        # Back button (navigation button)
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            tooltip="Back to Dashboard",
                            on_click=handle_back,
                            icon_color=PRIMARY
                        ) if show_back_button else ft.Container(width=0),
                        # Navigation toggle - menu button (like employee portal)
                        ft.IconButton(
                            icon=ft.Icons.MENU_OPEN if self._nav_rail_visible else ft.Icons.MENU,
                            tooltip="Toggle Navigation",
                            on_click=self._toggle_nav_rail,
                            icon_color=PRIMARY
                        ),
                        ft.Container(width=5),
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
                            f"Welcome, {self.current_user.get('username', 'Admin') if isinstance(self.current_user, dict) else 'Admin'}",
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

    def _get_tab_content_lazy(self, index):
        """Get content for the selected tab - lazy loaded with consistent header"""
        # Ensure notification manager is initialized before showing any tab
        try:
            from utils.notification_manager import ensure_notification_manager
            ensure_notification_manager(self.page)
        except Exception as e:
            print(f"[Admin] Notification init error: {e}")
        # Only load the requested tab - matches nav_data indices 0-21
        if index == 0:
            return self._create_dashboard_tab()
        elif index == 1:
            from screens.chat_screen import ChatScreen
            chat_content = ChatScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Chat", chat_content)
        elif index == 2:
            from screens.mail_screen import MailScreen
            mail_content = MailScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Mail", mail_content)
        elif index == 3:
            from screens.tasks_screen import TasksScreen
            tasks_content = TasksScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Tasks", tasks_content)
        elif index == 4:
            from screens.todo_screen import TodoScreen
            todo_content = TodoScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Todo", todo_content, show_back_button=False)
        elif index == 5:
            from screens.employees_screen import EmployeesScreen
            emp_content = EmployeesScreen(self._page, self.current_user)
            return self._wrap_with_admin_header("Employees", emp_content, show_back_button=False)
        elif index == 6:
            from screens.departments_screen import DepartmentsScreen
            dept_content = DepartmentsScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Departments", dept_content)
        elif index == 7:
            from screens.positions_screen import PositionsScreen
            pos_content = PositionsScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Positions", pos_content)
        elif index == 8:
            from screens.attendance_screen import AttendanceScreen
            att_content = AttendanceScreen(
                self.page, self.current_user, view_mode="admin")
            return self._wrap_with_admin_header("Attendance", att_content)
        elif index == 9:
            from screens.leaves_screen import LeavesScreen
            leave_content = LeavesScreen(
                self.page, self.current_user, view_mode="admin")

            # Re-initialize notifications after tab navigation
            try:
                from utils.notification_manager import ensure_notification_manager
                ensure_notification_manager(self.page)
            except Exception as ne:
                pass

            return self._wrap_with_admin_header("Leave Management", leave_content)
        elif index == 10:
            from screens.teams_screen import TeamsScreen
            teams_content = TeamsScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Teams", teams_content)
        elif index == 11:
            from screens.projects_screen import ProjectsScreen
            proj_content = ProjectsScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Projects", proj_content)
        elif index == 12:
            from screens.holidays_screen import HolidaysScreen
            hol_content = HolidaysScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Holidays", hol_content)
        elif index == 13:
            from screens.meetings_screen import MeetingsScreen
            meet_content = MeetingsScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Meetings", meet_content)
        elif index == 14:
            from screens.announcements_screen import AnnouncementsScreen
            news_content = AnnouncementsScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("News / Announcements", news_content)
        elif index == 15:
            from screens.settings_screen import SettingsScreen
            settings_content = SettingsScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Settings", settings_content, show_back_button=False)
        elif index == 16:
            from screens.organization_tree_screen import OrganizationTreeScreen
            org_content = OrganizationTreeScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Organization Tree", org_content)
        elif index == 17:
            from screens.data_entry_screen import DataEntryScreen
            data_content = DataEntryScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Data Entry", data_content)
        elif index == 18:
            from screens.inventory_screen import InventoryScreen
            inv_content = InventoryScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Inventory", inv_content)
        elif index == 19:
            from screens.transactions_screen import TransactionsScreen
            trans_content = TransactionsScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Transactions", trans_content)
        elif index == 20:
            from screens.time_tracking_screen import TimeTrackingScreen
            time_content = TimeTrackingScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("Time Tracking", time_content)
        elif index == 21:
            return self._create_storage_tab()
        elif index == 22:
            from screens.crm_screen import CRMScreen
            crm_content = CRMScreen(self.page, self.current_user)
            return self._wrap_with_admin_header("CRM Dashboard", crm_content)
        return self._create_dashboard_tab()

    def _get_tab_content(self, index):
        """Get content for the selected tab"""
        tab_methods = [
            self._create_dashboard_tab,
            self._create_chat_tab,
            self._create_mail_tab,
            self._create_tasks_tab,
            self._create_todo_tab,
            self._create_employees_tab,
            self._create_departments_tab,
            self._create_positions_tab,
            self._create_attendance_tab,
            self._create_leaves_tab,
            self._create_teams_tab,
            self._create_projects_tab,
            self._create_holidays_tab,
            self._create_meetings_tab,
            self._create_announcements_tab,
            self._create_settings_tab,
            self._create_org_tree_tab,
            self._create_data_entry_tab,
            self._create_inventory_tab,
            self._create_transactions_tab,
            self._create_time_tracking_tab,
            self._create_storage_tab,
            self._create_crm_tab,
        ]
        if 0 <= index < len(tab_methods):
            return tab_methods[index]()
        return self._create_dashboard_tab()

    def _create_crm_tab(self):
        """Create CRM tab"""
        from screens.crm_screen import CRMScreen
        return ft.Container(
            content=CRMScreen(self._page, self.current_user),
            expand=True
        )

    def _create_header(self):
        """Create header with user info, toggle button and logout"""
        return ft.Container(
            content=ft.Row([
                # Navigation toggle button
                self.nav_toggle_btn,
                ft.Container(width=10),
                ft.Text(
                    "Vernika HRA - Admin Dashboard",
                    size=20,
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
                    tooltip="Refresh Dashboard",
                    on_click=lambda e: self.refresh_dashboard(),
                    icon_color=PRIMARY
                ),
                ft.Container(width=5),
                ft.Text(
                    f"Welcome, {self.current_user.get('username', 'Admin') if isinstance(self.current_user, dict) else 'Admin'}",
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
        """Create dashboard overview tab with enhanced analytics and quick stats"""
        # Get stats
        stats = self._get_dashboard_stats()
        detailed_stats = self._get_detailed_stats()

        # Get screen width for responsive spacing
        try:
            window_width = getattr(self._page, 'window_width', 1200)
        except:
            window_width = 1200

        # Responsive spacing
        if window_width < 600:
            card_spacing = 10
            title_size = 20
        elif window_width < 900:
            card_spacing = 15
            title_size = 24
        else:
            card_spacing = 20
            title_size = 28

        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Admin Dashboard",
                    size=title_size,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY
                ),
                ft.Container(height=20),

                # Stats Cards Row 1 - Overview - with wrap for responsiveness
                ft.Text(
                    "Overview Statistics",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY
                ),
                ft.Container(height=10),
                ft.Row([
                    self._create_stat_card(
                        "Total Users", str(stats.get('total_users', 0)), ft.Icons.PEOPLE, BLUE_500),
                    self._create_stat_card(
                        "Active Users", str(stats.get('active_users', 0)), ft.Icons.CHECK_CIRCLE, GREEN_500),
                    self._create_stat_card(
                        "Total Employees", str(stats.get('total_employees', 0)), ft.Icons.BADGE, ORANGE_500),
                    self._create_stat_card(
                        "Departments", str(stats.get('departments', 0)), ft.Icons.BUSINESS, TEAL_500),
                ], spacing=card_spacing, wrap=True),
                ft.Container(height=15),

                # Stats Cards Row 2 - Today's Status - with wrap for responsiveness
                ft.Row([
                    self._create_stat_card(
                        "Present Today", str(stats.get('present_today', 0)), ft.Icons.CHECK_CIRCLE, SUCCESS),
                    self._create_stat_card(
                        "On Leave", str(stats.get('on_leave', 0)), ft.Icons.EVENT_BUSY, WARNING),
                    self._create_stat_card(
                        "Pending Tasks", str(stats.get('pending_tasks', 0)), ft.Icons.PENDING, ORANGE_500),
                    self._create_stat_card(
                        "Positions", str(stats.get('positions', 0)), ft.Icons.WORK, INDIGO_500),
                ], spacing=card_spacing, wrap=True),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Employee Analytics Section
                ft.Text(
                    "Employee Analytics",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY
                ),
                ft.Container(height=15),

                # Department-wise distribution
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.BUSINESS, size=24, color=PRIMARY),
                            ft.Text("Department-wise Employees",
                                    size=16, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Container(height=10),
                        self._create_department_analytics(
                            detailed_stats.get('department_stats', [])),
                    ]),
                    padding=15,
                    bgcolor=SURFACE,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1, blur_radius=5, color="#00000010"),
                ),

                ft.Container(height=15),

                # Employment Type Distribution
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.WORK, size=24, color=PURPLE_500),
                            ft.Text("Employment Type Distribution",
                                    size=16, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Container(height=10),
                        self._create_employment_type_analytics(
                            detailed_stats.get('employment_stats', [])),
                    ]),
                    padding=15,
                    bgcolor=SURFACE,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1, blur_radius=5, color="#00000010"),
                ),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Quick Actions - with wrap for responsiveness
                ft.Text(
                    "Quick Actions",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY
                ),
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        "Add New Employee",
                        icon=ft.Icons.PERSON_ADD,
                        on_click=lambda _: self._navigate_to_tab(
                            5),
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="white")
                    ),
                    ft.ElevatedButton(
                        "Manage Employees",
                        icon=ft.Icons.BADGE,
                        on_click=lambda _: self._navigate_to_tab(
                            5),
                        style=ft.ButtonStyle(bgcolor=ORANGE_500, color="white")
                    ),
                    ft.ElevatedButton(
                        "Manage Departments",
                        icon=ft.Icons.BUSINESS,
                        on_click=lambda _: self._navigate_to_tab(
                            6),
                        style=ft.ButtonStyle(bgcolor=PURPLE_500, color="white")
                    ),
                    ft.ElevatedButton(
                        "System Settings",
                        icon=ft.Icons.SETTINGS,
                        on_click=lambda _: self._navigate_to_tab(
                            15),
                        style=ft.ButtonStyle(bgcolor=TEAL_500, color="white")
                    ),
                ], spacing=10, wrap=True),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Management Modules - All TODO.md Buttons
                ft.Text(
                    "Management Modules",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY
                ),
                ft.Container(height=15),

                # Row 1: Tasks, Todo, Departments, Attendance - with wrap for responsiveness
                ft.Text("Core Management", size=14,
                        color=TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                ft.Container(height=8),
                ft.Row([
                    self._create_module_card(
                        "Tasks", ft.Icons.TASK, "Task Management", 3, ORANGE_500),
                    self._create_module_card(
                        "Todo", ft.Icons.LIST_ALT, "Todo Lists", 4, CYAN_600),
                    self._create_module_card(
                        "Departments", ft.Icons.BUSINESS, "Departments", 6, GREEN_500),
                    self._create_module_card(
                        "Attendance", ft.Icons.EVENT, "Attendance", 8, BLUE_500),
                ], spacing=15, wrap=True),

                ft.Container(height=15),
                # Row 2: Leave, Announcements, Teams, Positions - with wrap for responsiveness
                ft.Text("HR Management", size=14, color=TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500),
                ft.Container(height=8),
                ft.Row([
                    self._create_module_card(
                        "Leave", ft.Icons.EVENT_BUSY, "Leave Management", 9, PURPLE_500),
                    self._create_module_card(
                        "Announcements", ft.Icons.CAMPAIGN, "News & Updates", 14, RED_500),
                    self._create_module_card(
                        "Teams", ft.Icons.GROUP, "Team Management", 10, TEAL_500),
                    self._create_module_card(
                        "Positions", ft.Icons.WORK, "Job Positions", 7, INDIGO_500),
                ], spacing=15, wrap=True),

                ft.Container(height=15),
                # Row 3: Projects, Holidays, Meetings, Settings - with wrap for responsiveness
                ft.Text("Projects & Operations", size=14, color=TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500),
                ft.Container(height=8),
                ft.Row([
                    self._create_module_card(
                        "Projects", ft.Icons.FOLDER_SPECIAL, "Project Mgmt", 11, BLUE_500),
                    self._create_module_card(
                        "Holidays", ft.Icons.CALENDAR_TODAY, "Holiday Calendar", 12, GREEN_500),
                    self._create_module_card(
                        "Meetings", ft.Icons.VIDEO_CALL, "Schedule Meetings", 13, ORANGE_500),
                    self._create_module_card(
                        "Settings", ft.Icons.SETTINGS, "System Settings", 15, TEAL_500),
                ], spacing=15, wrap=True),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Additional Management - with wrap for responsiveness
                ft.Text(
                    "User Management",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY
                ),
                ft.Container(height=10),
                ft.Row([
                    self._create_module_card(
                        "Employees", ft.Icons.BADGE, "Employee Mgmt", 5, SUCCESS),
                    self._create_module_card(
                        "Org Tree", ft.Icons.ACCOUNT_TREE, "Organization Tree", 16, INDIGO_500),
                ], spacing=15, wrap=True),

            ], scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(20)
        )

    def _get_detailed_stats(self):
        """Get detailed analytics statistics"""
        stats = {
            'department_stats': [],
            'employment_stats': [],
            'new_hires_this_month': 0,
            'birthdays_this_month': 0,
        }
        try:
            db = get_db_session()
            from database.models import Employee, Department
            from datetime import datetime
            from sqlalchemy import func

            # Department-wise employee count
            departments = db.query(
                Department.name,
                func.count(Employee.id).label('count')
            ).outerjoin(Employee, Department.id == Employee.department_id).group_by(Department.id, Department.name).all()

            stats['department_stats'] = [
                {'name': d.name, 'count': d.count} for d in departments if d.name
            ]

            # Employment type distribution
            emp_types = db.query(
                Employee.employment_type,
                func.count(Employee.id).label('count')
            ).group_by(Employee.employment_type).all()

            stats['employment_stats'] = [
                {'type': e.employment_type or 'unknown', 'count': e.count}
                for e in emp_types
            ]

            # New hires this month
            now = datetime.now()
            new_hires = db.query(Employee).filter(
                func.extract('year', Employee.date_of_joining) == now.year,
                func.extract('month', Employee.date_of_joining) == now.month
            ).count()
            stats['new_hires_this_month'] = new_hires

            db.close()
        except Exception as e:
            print(f"Error getting detailed stats: {e}")
        return stats

    def _create_department_analytics(self, dept_stats):
        """Create department-wise analytics display"""
        if not dept_stats:
            return ft.Text("No department data available", size=12, color=TEXT_SECONDARY)

        # Find max for scaling
        max_count = max(s['count'] for s in dept_stats) if dept_stats else 1

        rows = []
        for dept in dept_stats:
            percentage = (dept['count'] / max_count *
                          100) if max_count > 0 else 0

            # Color based on count
            color = GREEN_500 if percentage > 50 else ORANGE_500 if percentage > 25 else BLUE_500

            rows.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(dept['name'], size=13,
                                    weight=ft.FontWeight.W_500, expand=True),
                            ft.Text(str(dept['count']), size=13,
                                    weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Container(
                            height=8,
                            bgcolor="#E0E0E0",
                            border_radius=4,
                            content=ft.Container(
                                width=max(30, int(percentage * 2)),
                                bgcolor=color,
                                border_radius=4,
                            ),
                        ),
                    ], spacing=4),
                    margin=ft.margin.only(bottom=8),
                )
            )

        return ft.Column(controls=rows, spacing=0)

    def _create_employment_type_analytics(self, emp_stats):
        """Create employment type distribution display"""
        if not emp_stats:
            return ft.Text("No employment data available", size=12, color=TEXT_SECONDARY)

        total = sum(s['count'] for s in emp_stats)

        # Colors for different types
        type_colors = {
            'full_time': GREEN_500,
            'part_time': BLUE_500,
            'contract': ORANGE_500,
            'intern': PURPLE_500,
        }

        rows = []
        for emp in emp_stats:
            emp_type = emp['type'].replace('_', ' ').title()
            count = emp['count']
            percentage = (count / total * 100) if total > 0 else 0
            color = type_colors.get(emp['type'], PRIMARY)

            rows.append(
                ft.Row([
                    ft.Container(
                        width=12, height=12,
                        bgcolor=color, border_radius=6,
                    ),
                    ft.Text(emp_type, size=13, expand=True),
                    ft.Text(f"{count} ({percentage:.1f}%)",
                            size=12, color=TEXT_SECONDARY),
                ], spacing=10)
            )

        return ft.Column(controls=rows, spacing=8)

    def _create_stat_card(self, title: str, value: str, icon_name, color):
        """Create a statistics card - responsive based on screen size"""
        # Get screen width for responsive sizing
        try:
            window_width = getattr(self._page, 'window_width', 1200)
        except:
            window_width = 1200

        # Responsive sizes
        if window_width < 600:  # Mobile
            card_width = None  # Full width
            icon_size = 28
            value_size = 24
            title_size = 12
            padding = 12
        elif window_width < 900:  # Tablet
            card_width = 150
            icon_size = 32
            value_size = 26
            title_size = 13
            padding = 15
        else:  # Desktop
            card_width = 180
            icon_size = 40
            value_size = 32
            title_size = 14
            padding = 20

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon=icon_name, size=icon_size, color=color),
                    ft.Text(value, size=value_size, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=title_size, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=ft.padding.all(padding),
                width=card_width,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=3
        )

    def _create_module_card(self, title: str, icon_name, subtitle: str, tab_index: int, color: str):
        """Create a module shortcut card - responsive based on screen size"""
        # Get screen width for responsive sizing
        try:
            window_width = getattr(self._page, 'window_width', 1200)
        except:
            window_width = 1200

        # Responsive sizes
        if window_width < 600:  # Mobile
            card_width = None  # Full width
            icon_size = 28
            title_size = 14
            subtitle_size = 10
            padding = 10
            btn_height = 28
        elif window_width < 900:  # Tablet
            card_width = 130
            icon_size = 32
            title_size = 15
            subtitle_size = 10
            padding = 12
            btn_height = 30
        else:  # Desktop
            card_width = 150
            icon_size = 36
            title_size = 16
            subtitle_size = 11
            padding = 15
            btn_height = 32

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon=icon_name, size=icon_size, color=color),
                    ft.Text(title, size=title_size, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle, size=subtitle_size,
                            color=TEXT_SECONDARY),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Open",
                        icon=ft.Icons.ARROW_FORWARD,
                        on_click=lambda _: self._navigate_to_tab(tab_index),
                        style=ft.ButtonStyle(bgcolor=color, color="white"),
                        height=btn_height,
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=ft.padding.all(padding),
                width=card_width,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=2
        )

    def _get_dashboard_stats(self):
        """Get dashboard statistics directly from database for real-time data"""
        stats = {
            'total_users': 0,
            'active_users': 0,
            'total_employees': 0,
            'audit_logs': 0,
            'present_today': 0,
            'on_leave': 0,
            'pending_tasks': 0,
            'departments': 0,
            'positions': 0,
        }
        try:
            from datetime import date
            from database.models import User, Employee, Department, Position, Attendance, LeaveRequest, Task, UserStatus
            from sqlalchemy import func, and_

            with get_session() as session:
                # Total users
                stats['total_users'] = session.query(
                    func.count(User.id)).scalar() or 0

                # Active users
                stats['active_users'] = session.query(func.count(User.id)).filter(
                    User.status == UserStatus.ACTIVE
                ).scalar() or 0

                # Total employees
                stats['total_employees'] = session.query(
                    func.count(Employee.id)).scalar() or 0

                # Active employees
                stats['active_employees'] = session.query(func.count(Employee.id)).filter(
                    Employee.is_active == True
                ).scalar() or 0

                # Departments
                stats['departments'] = session.query(func.count(Department.id)).filter(
                    Department.is_active == True
                ).scalar() or 0

                # Positions
                stats['positions'] = session.query(func.count(Position.id)).filter(
                    Position.is_active == True
                ).scalar() or 0

                # Present today
                today = date.today()
                stats['present_today'] = session.query(func.count(Attendance.id)).filter(
                    and_(
                        Attendance.date == today,
                        Attendance.status == 'present'
                    )
                ).scalar() or 0

                # On leave today
                stats['on_leave'] = session.query(func.count(LeaveRequest.id)).filter(
                    and_(
                        LeaveRequest.status == 'approved',
                        LeaveRequest.start_date <= today,
                        LeaveRequest.end_date >= today
                    )
                ).scalar() or 0

                # Pending tasks
                stats['pending_tasks'] = session.query(func.count(Task.id)).filter(
                    Task.status != 'completed'
                ).scalar() or 0

            print(f"Dashboard stats loaded: {stats}")
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            import traceback
            traceback.print_exc()
        return stats

    def _create_users_tab(self):
        """Create user management tab"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "User Management",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Add User",
                        icon=ft.Icons.ADD,
                        on_click=self._show_add_user_dialog,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="white")
                    )
                ]),
                ft.Container(height=20),
                # Placeholder for users table
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE, size=60, color=PRIMARY),
                        ft.Container(height=10),
                        ft.Text("User Management", size=18,
                                weight=ft.FontWeight.BOLD),
                        ft.Text("User list with add/edit/delete functionality",
                                size=14, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.all(50),
                    alignment=ft.alignment.Alignment(0, 0),
                    bgcolor=SURFACE_VARIANT,
                    border_radius=ft.border_radius.all(10),
                    expand=True
                ),
            ], expand=True, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(10)
        )

    def _create_employees_tab(self):
        """Create employee management tab with full CRUD and filters"""
        from database.session_manager import get_session, get_db_session, check_db_connection
        from database.models import Employee, Department, Position
        from sqlalchemy.orm import joinedload

        # State variables for filtering
        self._emp_filter_dept = {"value": "all"}
        self._emp_filter_status = {"value": "all"}
        self._emp_filter_type = {"value": "all"}
        self._emp_search = {"value": ""}

        def load_employees():
            """Load employees based on filters"""
            db = None
            try:
                db = get_db_session()
                query = db.query(Employee).options(
                    joinedload(Employee.department),
                    joinedload(Employee.position)
                )

                # Apply department filter
                if self._emp_filter_dept["value"] != "all":
                    query = query.filter(Employee.department_id == int(
                        self._emp_filter_dept["value"]))

                # Apply status filter
                if self._emp_filter_status["value"] == "active":
                    query = query.filter(Employee.is_active == True)
                elif self._emp_filter_status["value"] == "inactive":
                    query = query.filter(Employee.is_active == False)

                # Apply employment type filter
                if self._emp_filter_type["value"] != "all":
                    query = query.filter(
                        Employee.employment_type == self._emp_filter_type["value"])

                # Apply search filter
                search_term = self._emp_search["value"].strip().lower()
                if search_term:
                    query = query.filter(
                        (Employee.first_name.ilike(f"%{search_term}%")) |
                        (Employee.last_name.ilike(f"%{search_term}%")) |
                        (Employee.email.ilike(f"%{search_term}%")) |
                        (Employee.employee_code.ilike(f"%{search_term}%"))
                    )

                employees = query.order_by(Employee.id.desc()).all()
                return employees
            except Exception as e:
                print(f"Error loading employees: {e}")
                return []
            finally:
                if db:
                    db.close()

        def load_departments():
            """Load departments for filter"""
            db = None
            try:
                db = get_db_session()
                return db.query(Department).filter(Department.is_active == True).all()
            except Exception as e:
                print(f"Error loading departments: {e}")
                return []
            finally:
                if db:
                    db.close()

        def refresh_employee_list(e=None):
            """Refresh the employee list"""
            try:
                emp_list.content = build_employee_table()
                self._page.update()
            except Exception as ex:
                print(f"Error refreshing: {ex}")

        def build_employee_table():
            """Build the employee data table"""
            employees = load_employees()

            if not employees:
                return ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE,
                                size=64, color="#BDBDBD"),
                        ft.Text("No employees found",
                                size=14, color="#757575"),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Add First Employee",
                            on_click=lambda e: self._show_add_employee_from_admin(),
                            style=ft.ButtonStyle(
                                bgcolor="#4CAF50", color="WHITE")
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.Alignment(0, 0),
                    expand=True
                )

            rows = []
            for emp in employees:
                status_color = "#4CAF50" if emp.is_active else "#F44336"
                status_text = "Active" if emp.is_active else "Inactive"

                emp_type = emp.employment_type or "full_time"
                type_display = emp_type.replace('_', ' ').title()
                type_color = "#2196F3" if emp_type == "full_time" else "#FF9800"

                dept_name = emp.department.name if emp.department else "General"
                pos_title = emp.position.title if emp.position else "-"

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(emp.id), size=12)),
                            ft.DataCell(
                                ft.Text(emp.employee_code or f"EMP{emp.id:03d}", size=12)),
                            ft.DataCell(
                                ft.Text(f"{emp.first_name or ''} {emp.last_name or ''}", size=12)),
                            ft.DataCell(ft.Text(emp.email or "-", size=12)),
                            ft.DataCell(ft.Text(dept_name, size=12)),
                            ft.DataCell(ft.Text(pos_title, size=12)),
                            ft.DataCell(ft.Container(
                                ft.Text(type_display, size=10, color="WHITE"),
                                bgcolor=type_color,
                                padding=ft.padding.all(4),
                                border_radius=4
                            )),
                            ft.DataCell(ft.Container(
                                ft.Text(status_text, size=10, color="WHITE"),
                                bgcolor=status_color,
                                padding=ft.padding.all(4),
                                border_radius=4
                            )),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        icon_color="#1976D2",
                                        on_click=lambda e, emp_id=emp.id: self._show_edit_employee_from_admin(
                                            emp_id),
                                        tooltip="Edit",
                                        scale=0.8
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.PERSON,
                                        icon_color="#4CAF50",
                                        on_click=lambda e, emp_id=emp.id: self._show_employee_details_from_admin(
                                            emp_id),
                                        tooltip="View Details",
                                        scale=0.8
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.BADGE,
                                        icon_color="#FF9800",
                                        on_click=lambda e, emp_id=emp.id: self._generate_id_card_from_admin(
                                            emp_id),
                                        tooltip="ID Card",
                                        scale=0.8
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color="#D32F2F",
                                        on_click=lambda e, emp_id=emp.id: self._show_delete_employee_from_admin(
                                            emp_id),
                                        tooltip="Delete",
                                        scale=0.8
                                    ),
                                ], spacing=0)
                            ),
                        ]
                    )
                )

            return ft.DataTable(
                columns=[
                    ft.DataColumn(label=ft.Text(
                        "ID", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(label=ft.Text(
                        "Code", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(label=ft.Text(
                        "Name", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(label=ft.Text(
                        "Email", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(label=ft.Text(
                        "Department", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(label=ft.Text(
                        "Position", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(label=ft.Text(
                        "Type", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(label=ft.Text(
                        "Status", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(label=ft.Text(
                        "Actions", weight=ft.FontWeight.BOLD)),
                ],
                rows=rows,
                expand=True,
            )

        # Build filter row - simplified without problematic components
        search_field = ft.TextField(
            label="Search",
            hint_text="Search by name, email, code...",
            width=300,
            on_change=lambda e: (
                self._emp_search.__setitem__("value", e.control.value),
                refresh_employee_list()
            ),
            prefix_icon=ft.Icons.SEARCH,
        )

        # Employee list container
        emp_list = ft.Container(
            content=build_employee_table(),
            expand=True,
            padding=ft.padding.all(10),
        )

        return ft.Container(
            content=ft.Column([
                # Header with navigation toggle and back button
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=10),
                    content=ft.Row([
                        # Navigation hide/show button
                        ft.IconButton(
                            icon=ft.Icons.MENU,
                            tooltip="Toggle Navigation",
                            on_click=self._toggle_nav_rail,
                            icon_color=PRIMARY,
                        ),
                        ft.Container(width=10),
                        ft.Text("Employee Management", size=24,
                                weight=ft.FontWeight.BOLD, color=PRIMARY),
                        ft.Container(expand=True),
                        ft.Text(
                            f"Total: {len(load_employees())} employees", size=14, color=TEXT_SECONDARY),
                    ], alignment=ft.MainAxisAlignment.START)
                ),
                ft.Container(height=10),
                # Search and Add button row
                ft.Row([
                    search_field,
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Add Employee",
                        icon=ft.Icons.ADD,
                        on_click=lambda e: self._show_add_employee_from_admin(),
                        style=ft.ButtonStyle(bgcolor="#4CAF50", color="WHITE")
                    ),
                    ft.ElevatedButton(
                        "Full Management",
                        icon=ft.Icons.BADGE,
                        on_click=lambda e: self._show_employees(e),
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    ),
                ], spacing=10),
                ft.Container(height=10),
                emp_list,
            ],  expand=True),
            padding=ft.padding.all(10),
            expand=True,
        )

    def _show_add_employee_from_admin(self):
        """Show add employee dialog from admin screen"""
        # Import the employees screen and use its add dialog
        from screens.employees_screen import EmployeesScreen
        emp_screen = EmployeesScreen(self._page, self.current_user)
        emp_screen._show_add_dialog()

    def _show_edit_employee_from_admin(self, emp_id):
        """Show edit employee dialog from admin screen"""
        from screens.employees_screen import EmployeesScreen
        emp_screen = EmployeesScreen(self._page, self.current_user)
        emp_screen._show_edit_dialog(emp_id)

    def _show_employee_details_from_admin(self, emp_id):
        """Show employee details dialog from admin screen"""
        from screens.employees_screen import EmployeesScreen
        emp_screen = EmployeesScreen(self._page, self.current_user)
        emp_screen._show_details_dialog(emp_id)

    def _generate_id_card_from_admin(self, emp_id):
        """Generate ID card from admin screen"""
        from screens.employees_screen import EmployeesScreen
        emp_screen = EmployeesScreen(self._page, self.current_user)
        emp_screen._generate_id_card_dialog(emp_id)

    def _show_delete_employee_from_admin(self, emp_id):
        """Show delete confirmation from admin screen"""
        from screens.employees_screen import EmployeesScreen
        emp_screen = EmployeesScreen(self._page, self.current_user)
        emp_screen._show_delete_dialog(emp_id)

    def _create_screen_access_tab(self):
        """Create screen and button access management tab with improved UI and PostgreSQL"""
        from utils.screen_access import (
            SCREEN_ACCESS_CONFIG,
            BUTTON_ACCESS_CONFIG,
            get_active_employees_for_access_management,
            set_screen_access,
            set_button_access,
            reset_to_defaults,
            get_screens_by_category,
            get_buttons_by_screen
        )

        # State for UI
        self._access_employees = get_active_employees_for_access_management()
        self._access_controls = {}

        # Tab state for switching between Screen Access and Button Access
        access_type = {"current": "screen"}  # "screen" or "button"

        # Selected employee for detailed view
        selected_employee = {"user_id": None}

        def refresh_employees():
            self._access_employees = get_active_employees_for_access_management()
            self.page.update()

        def handle_screen_toggle(user_id, screen_key):
            def _handler(e):
                is_enabled = e.control.value
                admin_id = self.current_user.get('id') if isinstance(
                    self.current_user, dict) else None
                set_screen_access(user_id, screen_key,
                                  is_enabled, granted_by=admin_id)
                refresh_employees()
                self._show_message(
                    f"Screen access updated for {screen_key}", "success")
            return _handler

        def handle_button_toggle(user_id, button_key):
            def _handler(e):
                try:
                    is_enabled = e.control.value
                    admin_id = self.current_user.get('id') if isinstance(
                        self.current_user, dict) else None
                    result = set_button_access(user_id, button_key,
                                               is_enabled, granted_by=admin_id)
                    if result:
                        refresh_employees()
                        self._show_message(
                            f"Button access updated for {button_key}", "success")
                    else:
                        self._show_message(
                            f"Failed to update {button_key}", "error")
                except Exception as ex:
                    print(f"Error toggling button access: {ex}")
                    self._show_message(f"Error: {str(ex)}", "error")
            return _handler

        def handle_reset(user_id):
            def _handler(e):
                reset_to_defaults(user_id)
                refresh_employees()
                self._show_message("Access reset to defaults", "success")
            return _handler

        def show_employee_details(emp, access_type="screen"):
            """Show detailed access management for a specific employee"""
            selected_employee["user_id"] = emp['user_id']
            emp_name = emp['full_name'] or emp['username']

            if access_type == "screen":
                # Create access cards for each screen
                access_cards = []
                for screen_key, config in SCREEN_ACCESS_CONFIG.items():
                    is_enabled = emp['screen_access'].get(screen_key, False)

                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(config["name"], size=14,
                                            weight=ft.FontWeight.BOLD),
                                    ft.Text(config["description"],
                                            size=11, color=TEXT_SECONDARY),
                                ], expand=True),
                                ft.Switch(
                                    value=is_enabled,
                                    on_change=handle_screen_toggle(
                                        emp['user_id'], screen_key),
                                    active_color=PRIMARY,
                                    # Profile always enabled
                                    disabled=(screen_key == 'profile'),
                                ),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=15,
                            width=400,
                        ),
                        elevation=1,
                    )
                    access_cards.append(card)

                # Detail dialog for screen access
                detail_content = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SECURITY, size=24, color=PRIMARY),
                            ft.Text(
                                f"Screen Access for {emp_name}", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Container(height=10),
                        ft.Text(f"Email: {emp['email']}",
                                size=12, color=TEXT_SECONDARY),
                        ft.Text(f"Role: {emp['role']}",
                                size=12, color=TEXT_SECONDARY),
                        ft.Divider(),
                        ft.Text("Screen Access Permissions",
                                size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        # Create rows of access cards (2 per row)
                        ft.Column(
                            controls=[
                                ft.Row(access_cards[i:i+2], spacing=15)
                                for i in range(0, len(access_cards), 2)
                            ],
                            spacing=10
                        ),
                        ft.Container(height=20),
                        ft.Row([
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                "Reset to Defaults",
                                icon=ft.Icons.RESTART_ALT,
                                on_click=handle_reset(emp['user_id']),
                                style=ft.ButtonStyle(
                                    bgcolor=WARNING, color="white"),
                            ),
                        ]),
                    ], scroll=ft.ScrollMode.AUTO),
                    width=650,
                    height=550,
                )
            else:
                # Button-level access
                buttons_by_screen = get_buttons_by_screen()

                # Create sections for each screen
                sections = []
                for screen_name, buttons in buttons_by_screen.items():
                    if not buttons:
                        continue

                    button_rows = []
                    for btn in buttons:
                        is_enabled = emp.get('button_access', {}).get(
                            btn['key'], False)

                        card = ft.Card(
                            content=ft.Container(
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(btn["name"], size=13,
                                                weight=ft.FontWeight.BOLD),
                                        ft.Text(btn["description"],
                                                size=10, color=TEXT_SECONDARY),
                                    ], expand=True),
                                    ft.Switch(
                                        value=is_enabled,
                                        on_change=handle_button_toggle(
                                            emp['user_id'], btn['key']),
                                        active_color=PRIMARY,
                                    ),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=10,
                                width=380,
                            ),
                            elevation=1,
                        )
                        button_rows.append(card)

                    # Add section for this screen
                    sections.append(
                        ft.Column([
                            ft.Text(screen_name.upper(), size=12,
                                    weight=ft.FontWeight.BOLD, color=PRIMARY),
                            ft.Container(height=5),
                            ft.Row(
                                list(button_rows[i:i+2] for i in range(0, len(button_rows), 2)), spacing=10),
                            ft.Container(height=15),
                        ])
                    )

                # Detail dialog for button access
                detail_content = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.TOUCH_APP,
                                    size=24, color=PRIMARY),
                            ft.Text(
                                f"Button Access for {emp_name}", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Container(height=10),
                        ft.Text(f"Email: {emp['email']}",
                                size=12, color=TEXT_SECONDARY),
                        ft.Text(f"Role: {emp['role']}",
                                size=12, color=TEXT_SECONDARY),
                        ft.Divider(),
                        ft.Text("Button-Level Access Permissions",
                                size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Column(
                                sections, scroll=ft.ScrollMode.AUTO),
                            height=400,
                        ),
                    ], scroll=ft.ScrollMode.AUTO),
                    width=650,
                    height=550,
                )

            dlg = ft.AlertDialog(
                title=ft.Text(f"Manage Access - {emp_name}"),
                content=detail_content,
                actions=[
                    ft.TextButton("Close", on_click=lambda e: close_dialog()),
                ]
            )

            def close_dialog():
                if self.page.dialog:
                    self.page.dialog.open = False
                self.page.update()

            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

        def show_access_details_wrapper(emp):
            """Wrapper to show access details based on current tab"""
            show_employee_details(emp, access_type["current"])

        # Build the main content with tabs for Screen Access and Button Access

        # Header with tabs
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY, size=32, color=PRIMARY),
                    ft.Column([
                        ft.Text("Access Management",
                                size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Manage screen and button access for employees",
                                size=13, color=TEXT_SECONDARY),
                    ]),
                ]),
                ft.Container(height=20),
                # Tab buttons for Screen Access and Button Access
                ft.Row([
                    ft.ElevatedButton(
                        "Screen Access",
                        icon=ft.Icons.DASHBOARD,
                        on_click=lambda e: (
                            access_type.__setitem__('current', 'screen'),
                            self._update_access_content(
                                access_container, access_type)
                        ),
                        style=ft.ButtonStyle(
                            bgcolor=PRIMARY if access_type["current"] == "screen" else SURFACE_VARIANT,
                            color="WHITE" if access_type["current"] == "screen" else TEXT_PRIMARY
                        )
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "Button Access",
                        icon=ft.Icons.TOUCH_APP,
                        on_click=lambda e: (
                            access_type.__setitem__('current', 'button'),
                            self._update_access_content(
                                access_container, access_type)
                        ),
                        style=ft.ButtonStyle(
                            bgcolor=PRIMARY if access_type["current"] == "button" else SURFACE_VARIANT,
                            color="WHITE" if access_type["current"] == "button" else TEXT_PRIMARY
                        )
                    ),
                ]),
                ft.Container(height=15),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=INFO),
                        ft.Text("Click 'Manage Access' on any employee to configure permissions. "
                                "New buttons added to the system will automatically appear here.",
                                size=12, color=TEXT_SECONDARY),
                    ], spacing=8),
                    bgcolor="#E3F2FD",
                    padding=10,
                    border_radius=8,
                ),
            ]),
        )

        # Create access content container
        access_container = ft.Container()

        def build_employee_list(access_type_val):
            """Build the employee list based on access type"""
            employee_cards = []
            for emp in self._access_employees:
                emp_name = emp['full_name'] or emp['username']

                if access_type_val == "screen":
                    enabled_count = emp['enabled_count']
                    total_screens = emp['total_screens']
                    progress_text = f"{enabled_count}/{total_screens}"
                else:
                    # For button access
                    button_access = emp.get('button_access', {})
                    enabled_count = sum(1 for v in button_access.values() if v)
                    total_buttons = len(BUTTON_ACCESS_CONFIG)
                    progress_text = f"{enabled_count}/{total_buttons}"

                # Create progress indicator
                progress_color = GREEN_500 if enabled_count > 3 else ORANGE_500 if enabled_count > 0 else ERROR

                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    width=40, height=40,
                                    bgcolor=PRIMARY,
                                    border_radius=20,
                                    content=ft.Text(
                                        emp_name[0].upper(
                                        ) if emp_name else "?",
                                        size=18, color="WHITE", weight=ft.FontWeight.BOLD
                                    ),
                                    alignment=ft.alignment.Alignment(0, 0),
                                ),
                                ft.Column([
                                    ft.Text(emp_name, size=14,
                                            weight=ft.FontWeight.BOLD),
                                    ft.Text(emp['email'], size=11,
                                            color=TEXT_SECONDARY),
                                ], expand=True),
                                ft.Container(
                                    bgcolor=progress_color,
                                    padding=ft.padding.symmetric(
                                        horizontal=8, vertical=4),
                                    border_radius=12,
                                    content=ft.Text(
                                        progress_text,
                                        size=11, color="WHITE", weight=ft.FontWeight.BOLD
                                    ),
                                ),
                            ]),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Text(f"Role: {emp['role']}",
                                        size=11, color=TEXT_SECONDARY),
                                ft.Container(expand=True),
                                ft.ElevatedButton(
                                    "Manage Access",
                                    icon=ft.Icons.EDIT,
                                    on_click=lambda e, user_id=emp['user_id'], emp_data=emp: self._show_access_dialog(
                                        user_id, emp_data, access_type_val),
                                    style=ft.ButtonStyle(
                                        bgcolor=PRIMARY, color="WHITE"),
                                    height=32,
                                ),
                            ]),
                        ], spacing=5),
                        padding=15,
                    ),
                    elevation=2,
                    width=350,
                )
                employee_cards.append(card)

            if not employee_cards:
                return ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE,
                                size=64, color=TEXT_SECONDARY),
                        ft.Text("No employees found", size=16,
                                color=TEXT_SECONDARY),
                        ft.Text("Add employees to manage their access permissions",
                                size=12, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=50,
                )

            # Return Column with rows of cards
            return ft.Column(
                controls=[
                    ft.Row(employee_cards[i:i+3], spacing=15)
                    for i in range(0, len(employee_cards), 3)
                ],
                spacing=15
            )

        # Initial build
        access_container.content = ft.Column([
            ft.Text("Employees", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            build_employee_list(access_type["current"]),
        ], scroll=ft.ScrollMode.AUTO)

        # Method to update content when tabs change
        def update_access_content(container, access_type_val):
            container.content = ft.Column([
                ft.Text("Employees", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                build_employee_list(access_type_val),
            ], scroll=ft.ScrollMode.AUTO)
            self.page.update()

        # Store the update method for later use
        self._update_access_content = update_access_content

        # Compose the full UI
        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=20),
                access_container,
            ], scroll=ft.ScrollMode.AUTO),
            padding=25,
            expand=True
        )

    def _show_access_dialog(self, user_id, emp_data, access_type):
        """Show the access management dialog for an employee"""
        from utils.screen_access import (
            SCREEN_ACCESS_CONFIG,
            BUTTON_ACCESS_CONFIG,
            get_user_screen_access,
            get_user_button_access,
            set_screen_access,
            set_button_access,
            reset_to_defaults
        )

        emp_name = emp_data.get('full_name') or emp_data.get(
            'username', 'Employee')

        # Get current access
        screen_access = get_user_screen_access(user_id)
        button_access = get_user_button_access(user_id)

        def close_dialog(e):
            if self.page.dialog:
                self.page.dialog.open = False
            self.page.update()

        def handle_screen_toggle(uid, sk):
            def handler(e):
                try:
                    is_enabled = e.control.value
                    admin_id = self.current_user.get('id') if isinstance(
                        self.current_user, dict) else None
                    result = set_screen_access(
                        uid, sk, is_enabled, granted_by=admin_id)
                    if result:
                        self._show_message(
                            f"Updated {SCREEN_ACCESS_CONFIG.get(sk, {}).get('name', sk)}", "success")
                        self.refresh()
                except Exception as ex:
                    print(f"Error: {ex}")
                    self._show_message(f"Error: {str(ex)}", "error")
            return handler

        def handle_button_toggle(uid, bk):
            def handler(e):
                try:
                    is_enabled = e.control.value
                    admin_id = self.current_user.get('id') if isinstance(
                        self.current_user, dict) else None
                    result = set_button_access(
                        uid, bk, is_enabled, granted_by=admin_id)
                    if result:
                        self._show_message(
                            f"Updated {BUTTON_ACCESS_CONFIG.get(bk, {}).get('name', bk)}", "success")
                        self.refresh()
                except Exception as ex:
                    print(f"Error: {ex}")
                    self._show_message(f"Error: {str(ex)}", "error")
            return handler

        # Build access controls based on type
        if access_type == "screen":
            # Screen access view
            access_items = []
            for sk, config in SCREEN_ACCESS_CONFIG.items():
                is_enabled = screen_access.get(sk, False)

                row = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(config["name"], size=14,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(config["description"],
                                    size=11, color=TEXT_SECONDARY),
                        ], expand=True),
                        ft.Switch(
                            value=is_enabled,
                            on_change=handle_screen_toggle(user_id, sk),
                            active_color=PRIMARY,
                            disabled=(sk == 'profile'),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#F5F5F5" if sk != 'profile' else "#E3F2FD",
                    border_radius=8,
                    margin=5,
                )
                access_items.append(row)

            content = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY, size=24, color=PRIMARY),
                    ft.Text(f"Screen Access - {emp_name}",
                            size=18, weight=ft.FontWeight.BOLD),
                ]),
                ft.Container(height=10),
                ft.Text(f"Email: {emp_data.get('email', 'N/A')}",
                        size=12, color=TEXT_SECONDARY),
                ft.Text(f"Role: {emp_data.get('role', 'employee')}",
                        size=12, color=TEXT_SECONDARY),
                ft.Divider(),
                ft.Container(height=10),
                ft.Column(access_items,  spacing=5),
            ], scroll=ft.ScrollMode.AUTO)

            dialog_width = 500
            dialog_height = 550
        else:
            # Button access view
            access_items = []
            for bk, config in BUTTON_ACCESS_CONFIG.items():
                is_enabled = button_access.get(bk, False)

                row = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(config["name"], size=14,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(config["description"],
                                    size=11, color=TEXT_SECONDARY),
                        ], expand=True),
                        ft.Switch(
                            value=is_enabled,
                            on_change=handle_button_toggle(user_id, bk),
                            active_color=PRIMARY,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#F5F5F5",
                    border_radius=8,
                    margin=5,
                )
                access_items.append(row)

            content = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TOUCH_APP, size=24, color=PRIMARY),
                    ft.Text(f"Button Access - {emp_name}",
                            size=18, weight=ft.FontWeight.BOLD),
                ]),
                ft.Container(height=10),
                ft.Text(f"Email: {emp_data.get('email', 'N/A')}",
                        size=12, color=TEXT_SECONDARY),
                ft.Text(f"Role: {emp_data.get('role', 'employee')}",
                        size=12, color=TEXT_SECONDARY),
                ft.Divider(),
                ft.Container(height=10),
                ft.Column(access_items,  spacing=5),
            ], scroll=ft.ScrollMode.AUTO)

            dialog_width = 500
            dialog_height = 550

        dlg = ft.AlertDialog(
            title=ft.Text(f"Manage Access - {emp_name}"),
            content=ft.Container(
                content=content, width=dialog_width, height=dialog_height),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ]
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _create_audit_tab(self):
        """Create audit logs tab"""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Audit Logs",
                    size=24,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.HISTORY, size=60, color=PRIMARY),
                        ft.Container(height=10),
                        ft.Text("Audit Logs", size=18,
                                weight=ft.FontWeight.BOLD),
                        ft.Text("Track all user activities and system changes",
                                size=14, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.all(50),
                    alignment=ft.alignment.Alignment(0, 0),
                    bgcolor=SURFACE_VARIANT,
                    border_radius=ft.border_radius.all(10),
                    expand=True
                ),
            ], expand=True, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(10)
        )

    def _create_org_tree_tab(self):
        """Create Organization Tree tab"""
        from screens.organization_tree_screen import OrganizationTreeScreen
        return ft.Container(
            content=OrganizationTreeScreen(self.page, self.current_user),
            expand=True
        )

    def _create_data_entry_tab(self):
        """Create Data Entry/Spreadsheet tab"""
        from screens.data_entry_screen import DataEntryScreen
        return ft.Container(
            content=DataEntryScreen(self.page, self.current_user),
            expand=True
        )

    def _create_inventory_tab(self):
        """Create Inventory tab"""
        from screens.inventory_screen import InventoryScreen
        return ft.Container(
            content=InventoryScreen(self.page, self.current_user),
            expand=True,

        )

    def _create_transactions_tab(self):
        """Create Transactions/Payments tab"""
        from screens.transactions_screen import TransactionsScreen
        return ft.Container(
            content=TransactionsScreen(self.page, self.current_user),
            expand=True,

        )

    # ============ NEW BUSINESS FEATURE TABS ============

    def _create_time_tracking_tab(self):
        """Create Time Tracking tab"""
        from screens.time_tracking_screen import TimeTrackingScreen
        return ft.Container(
            content=TimeTrackingScreen(self.page, self.current_user),
            expand=True,
        )

    def _create_storage_tab(self):
        """Create Storage Management tab with database backup and data export features"""
        # Get database stats
        db_stats = self._get_database_stats()

        def export_data(export_type):
            """Export data to file"""
            import csv
            from datetime import datetime
            import os

            try:
                # Create reports directory if not exists
                export_dir = "reports"
                if not os.path.exists(export_dir):
                    os.makedirs(export_dir)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                db = get_db_session()

                if export_type == "employees":
                    from database.models import Employee
                    employees = db.query(Employee).all()
                    filename = f"{export_dir}/employees_{timestamp}.csv"
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['ID', 'Code', 'First Name', 'Last Name',
                                        'Email', 'Phone', 'Department', 'Position', 'Status'])
                        for emp in employees:
                            dept = emp.department.name if emp.department else ""
                            pos = emp.position.title if emp.position else ""
                            writer.writerow([emp.id, emp.employee_code, emp.first_name, emp.last_name,
                                            emp.email, emp.phone, dept, pos, "Active" if emp.is_active else "Inactive"])
                    self._show_message(
                        f"Employees exported to {filename}", "success")

                elif export_type == "users":
                    from database.models import User
                    users = db.query(User).all()
                    filename = f"{export_dir}/users_{timestamp}.csv"
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            ['ID', 'Username', 'Email', 'Role ID', 'Status'])
                        for user in users:
                            writer.writerow(
                                [user.id, user.username, user.email, user.role_id, user.status.value if user.status else ""])
                    self._show_message(
                        f"Users exported to {filename}", "success")

                elif export_type == "departments":
                    from database.models import Department
                    depts = db.query(Department).all()
                    filename = f"{export_dir}/departments_{timestamp}.csv"
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            ['ID', 'Name', 'Code', 'Head ID', 'Status'])
                        for dept in depts:
                            writer.writerow(
                                [dept.id, dept.name, dept.code, dept.head_id, "Active" if dept.is_active else "Inactive"])
                    self._show_message(
                        f"Departments exported to {filename}", "success")

                elif export_type == "attendance":
                    from database.models import Attendance
                    from datetime import date
                    # Get last 30 days attendance
                    from datetime import timedelta
                    end_date = date.today()
                    start_date = end_date - timedelta(days=30)
                    attendances = db.query(Attendance).filter(
                        Attendance.date >= start_date,
                        Attendance.date <= end_date
                    ).all()
                    filename = f"{export_dir}/attendance_{timestamp}.csv"
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            ['ID', 'Employee ID', 'Date', 'Status', 'Check In', 'Check Out'])
                        for att in attendances:
                            writer.writerow(
                                [att.id, att.employee_id, att.date, att.status.value if att.status else "", att.check_in, att.check_out])
                    self._show_message(
                        f"Attendance exported to {filename}", "success")

                db.close()
                self._page.update()

            except Exception as e:
                self._show_message(f"Export failed: {str(e)}", "error")
                print(f"Export error: {e}")

        def run_backup():
            """Run database backup"""
            import os
            from datetime import datetime

            try:
                # Create backup directory
                backup_dir = "backups"
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{backup_dir}/vernika_backup_{timestamp}.json"

                # Export all critical data to JSON
                import json
                db = get_db_session()

                backup_data = {
                    "timestamp": timestamp,
                    "version": "1.0",
                    "data": {}
                }

                # Export employees
                from database.models import Employee
                employees = db.query(Employee).all()
                backup_data["data"]["employees"] = [
                    {
                        "id": e.id,
                        "employee_code": e.employee_code,
                        "first_name": e.first_name,
                        "last_name": e.last_name,
                        "email": e.email,
                        "phone": e.phone,
                        "department_id": e.department_id,
                        "position_id": e.position_id,
                        "is_active": e.is_active
                    } for e in employees
                ]

                # Export users
                from database.models import User
                users = db.query(User).all()
                backup_data["data"]["users"] = [
                    {
                        "id": u.id,
                        "username": u.username,
                        "email": u.email,
                        "role_id": u.role_id,
                        "status": u.status.value if u.status else ""
                    } for u in users
                ]

                # Export departments
                from database.models import Department
                depts = db.query(Department).all()
                backup_data["data"]["departments"] = [
                    {"id": d.id, "name": d.name, "code": d.code,
                        "is_active": d.is_active}
                    for d in depts
                ]

                # Export positions
                from database.models import Position
                positions = db.query(Position).all()
                backup_data["data"]["positions"] = [
                    {"id": p.id, "title": p.title, "code": p.code,
                        "department_id": p.department_id, "is_active": p.is_active}
                    for p in positions
                ]

                db.close()

                # Save to file
                with open(filename, 'w') as f:
                    json.dump(backup_data, f, indent=2, default=str)

                self._show_message(f"Backup created: {filename}", "success")
                self._page.update()

            except Exception as e:
                self._show_message(f"Backup failed: {str(e)}", "error")
                print(f"Backup error: {e}")

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CLOUD, size=32, color=PRIMARY),
                    ft.Text("Storage Management", size=24,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                ]),
                ft.Container(height=20),

                # Database Stats Section
                ft.Text("Database Statistics", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Row([
                    self._create_storage_card("Total Employees", str(
                        db_stats.get('total_employees', 0)), ft.Icons.PEOPLE, BLUE_500),
                    self._create_storage_card("Total Users", str(db_stats.get(
                        'total_users', 0)), ft.Icons.ACCOUNT_CIRCLE, GREEN_500),
                    self._create_storage_card("Departments", str(db_stats.get(
                        'total_departments', 0)), ft.Icons.BUSINESS, ORANGE_500),
                    self._create_storage_card("Positions", str(db_stats.get(
                        'total_positions', 0)), ft.Icons.WORK, PURPLE_500),
                ], spacing=20),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Backup Section
                ft.Text("Database Backup", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.BACKUP, size=40, color=PRIMARY),
                            ft.Column([
                                ft.Text("Create Full Backup", size=16,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    "Export all database data to a JSON backup file", size=12, color=TEXT_SECONDARY),
                            ], expand=True),
                        ]),
                        ft.Container(height=15),
                        ft.ElevatedButton(
                            "Create Backup",
                            icon=ft.Icons.SAVE,
                            on_click=lambda e: run_backup(),
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="white")
                        ),
                    ]),
                    padding=20,
                    bgcolor=SURFACE,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1, blur_radius=5, color="#00000010"),
                ),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Data Export Section
                ft.Text("Export Data", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Export specific data to CSV files",
                                size=14, color=TEXT_SECONDARY),
                        ft.Container(height=15),
                        ft.Row([
                            ft.ElevatedButton(
                                "Employees",
                                icon=ft.Icons.PEOPLE,
                                on_click=lambda e: export_data("employees"),
                                style=ft.ButtonStyle(
                                    bgcolor=BLUE_500, color="white")
                            ),
                            ft.ElevatedButton(
                                "Users",
                                icon=ft.Icons.ACCOUNT_CIRCLE,
                                on_click=lambda e: export_data("users"),
                                style=ft.ButtonStyle(
                                    bgcolor=GREEN_500, color="white")
                            ),
                            ft.ElevatedButton(
                                "Departments",
                                icon=ft.Icons.BUSINESS,
                                on_click=lambda e: export_data("departments"),
                                style=ft.ButtonStyle(
                                    bgcolor=ORANGE_500, color="white")
                            ),
                            ft.ElevatedButton(
                                "Attendance",
                                icon=ft.Icons.EVENT,
                                on_click=lambda e: export_data("attendance"),
                                style=ft.ButtonStyle(
                                    bgcolor=PURPLE_500, color="white")
                            ),
                        ], spacing=10),
                    ]),
                    padding=20,
                    bgcolor=SURFACE,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1, blur_radius=5, color="#00000010"),
                ),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Storage Info Section
                ft.Text("Storage Information", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE,
                                    size=20, color=INFO),
                            ft.Text("Data is stored in PostgreSQL database. Backups are saved locally in 'backups' folder.",
                                    size=12, color=TEXT_SECONDARY),
                        ]),
                        ft.Container(height=10),
                        ft.Row([
                            ft.Icon(ft.Icons.FOLDER, size=20, color=INFO),
                            ft.Text("Export files are saved in 'reports' folder.",
                                    size=12, color=TEXT_SECONDARY),
                        ]),
                    ]),
                    padding=15,
                    bgcolor=SURFACE_VARIANT,
                    border_radius=8,
                ),

            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
        )

    def _get_database_stats(self):
        """Get database statistics for storage management"""
        stats = {
            'total_employees': 0,
            'total_users': 0,
            'total_departments': 0,
            'total_positions': 0,
        }
        try:
            db = get_db_session()
            from database.models import Employee, User, Department, Position

            stats['total_employees'] = db.query(Employee).count()
            stats['total_users'] = db.query(User).count()
            stats['total_departments'] = db.query(Department).count()
            stats['total_positions'] = db.query(Position).count()

            db.close()
        except Exception as e:
            print(f"Error getting database stats: {e}")
        return stats

    def _create_storage_card(self, title, value, icon_name, color):
        """Create a storage stat card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon=icon_name, size=32, color=color),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=12, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=ft.padding.all(15),
                width=140,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=2
        )

    # ============ NEW TAB METHODS FOR ALL SCREENS ============

    def _create_chat_tab(self):
        """Create chat/communication tab"""
        from screens.chat_screen import ChatScreen
        return ft.Container(
            content=ChatScreen(self.page, self.current_user),
            expand=True
        )

    def _create_mail_tab(self):
        """Create internal mail tab"""
        from screens.mail_screen import MailScreen
        return ft.Container(
            content=MailScreen(self.page, self.current_user),
            expand=True
        )

    def _create_tasks_tab(self):
        """Create tasks management tab"""
        from screens.tasks_screen import TasksScreen
        return ft.Container(
            content=TasksScreen(self.page, self.current_user),
            expand=True
        )

    def _create_todo_tab(self):
        """Create todo list tab"""
        from screens.todo_screen import TodoScreen
        return ft.Container(
            content=TodoScreen(self.page, self.current_user),
            expand=True
        )

    def _create_departments_tab(self):
        """Create departments management tab"""
        from screens.departments_screen import DepartmentsScreen
        return ft.Container(
            content=DepartmentsScreen(self.page, self.current_user),
            expand=True
        )

    def _create_attendance_tab(self):
        """Create attendance management tab"""
        from screens.attendance_screen import AttendanceScreen
        return ft.Container(
            content=AttendanceScreen(
                self.page, self.current_user, view_mode="admin"),
            expand=True
        )

    def _create_leaves_tab(self):
        """Create leave management tab"""
        from screens.leaves_screen import LeavesScreen
        return ft.Container(
            content=LeavesScreen(
                self.page, self.current_user, view_mode="admin"),
            expand=True
        )

    def _create_positions_tab(self):
        """Create positions management tab"""
        from screens.positions_screen import PositionsScreen
        return ft.Container(
            content=PositionsScreen(self.page, self.current_user),
            expand=True
        )

    def _create_announcements_tab(self):
        """Create announcements/news tab"""
        from screens.announcements_screen import AnnouncementsScreen
        return ft.Container(
            content=AnnouncementsScreen(self.page),
            expand=True
        )

    def _create_settings_tab(self):
        """Create settings tab"""
        from screens.settings_screen import SettingsScreen
        return ft.Container(
            content=SettingsScreen(self.page, self.current_user),
            expand=True
        )

    def _create_teams_tab(self):
        """Create teams management tab"""
        from screens.teams_screen import TeamsScreen
        return ft.Container(
            content=TeamsScreen(self.page, self.current_user),
            expand=True
        )

    def _create_projects_tab(self):
        """Create projects management tab"""
        from screens.projects_screen import ProjectsScreen
        return ft.Container(
            content=ProjectsScreen(self.page, self.current_user),
            expand=True
        )

    def _create_holidays_tab(self):
        """Create holidays management tab"""
        from screens.holidays_screen import HolidaysScreen
        return ft.Container(
            content=HolidaysScreen(self.page, self.current_user),
            expand=True
        )

    def _create_meetings_tab(self):
        """Create meetings management tab"""
        from screens.meetings_screen import MeetingsScreen
        return ft.Container(
            content=MeetingsScreen(self.page, self.current_user),
            expand=True
        )

    # ============ NAVIGATION METHODS ============

    def _show_chat(self, e):
        """Navigate to Chat screen"""
        from screens.chat_screen import ChatScreen
        self.page.clean()
        self.page.add(ChatScreen(self.page, self.current_user))

    def _show_tasks(self, e):
        """Navigate to Tasks screen"""
        from screens.tasks_screen import TasksScreen
        self.page.clean()
        self.page.add(TasksScreen(self.page, self.current_user))

    def _show_todo(self, e):
        """Navigate to Todo screen"""
        from screens.todo_screen import TodoScreen
        self.page.clean()
        self.page.add(TodoScreen(self.page, self.current_user))

    def _show_departments(self, e):
        """Navigate to Departments screen"""
        from screens.departments_screen import DepartmentsScreen
        self.page.clean()
        self.page.add(DepartmentsScreen(self.page, self.current_user))

    def _show_attendance(self, e):
        """Navigate to Attendance screen"""
        from screens.attendance_screen import AttendanceScreen
        self.page.clean()
        self.page.add(AttendanceScreen(
            self.page, self.current_user, view_mode="admin"))

    def _show_leaves(self, e):
        """Navigate to Leaves screen"""
        from screens.leaves_screen import LeavesScreen
        self.page.clean()
        self.page.add(LeavesScreen(
            self.page, self.current_user, view_mode="admin"))

        # Re-initialize notifications after navigation
        try:
            from utils.notification_manager import ensure_notification_manager
            ensure_notification_manager(self.page)
        except Exception as e:
            print(f"Notification init error: {e}")

    def _show_employees(self, e):
        """Navigate to Employees screen"""
        from screens.employees_screen import show_employees
        show_employees(self.page, self.current_user)

    def _show_positions(self, e):
        """Navigate to Positions screen"""
        from screens.positions_screen import show_positions
        show_positions(self.page, self.current_user)

    def _show_announcements(self, e):
        """Navigate to Announcements screen"""
        from screens.announcements_screen import AnnouncementsScreen
        self.page.clean()
        self.page.add(AnnouncementsScreen(self.page))

    def _show_settings(self, e):
        """Navigate to Settings screen"""
        from screens.settings_screen import SettingsScreen
        self.page.clean()
        self.page.add(SettingsScreen(self.page, self.current_user))

    def _navigate_to_tab(self, index):
        """Helper to navigate to a specific tab index"""
        content = self.content.content.controls[2]  # Get the content container
        content.content = self._get_tab_content(index)
        self.page.update()

    def _show_message(self, message, type="info"):
        """Show a snackbar message using global notification system"""
        try:
            from utils.notification_manager import get_notification_manager
            nm = get_notification_manager()
            if nm:
                if type == "success":
                    nm.show_success(message)
                elif type == "error":
                    nm.show_error(message)
                elif type == "warning":
                    nm.show_warning(message)
                else:
                    nm.show_info(message)
                return
        except Exception as e:
            print(f"[Admin] Notification error: {e}")

        # Fallback to local snackbar
        bgcolor = GREEN_600 if type == "success" else RED_500 if type == "error" else BLUE_600
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=bgcolor
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _handle_logout(self, e):
        """Handle logout button click"""
        from database.session_manager import get_db_session
        from database.operations import logout_user

        # Update user online status in database
        try:
            user_id = self.current_user.get('id') if isinstance(
                self.current_user, dict) else None
            if user_id:
                db = get_db_session()
                logout_user(db, user_id)
                db.close()
        except Exception as ex:
            print(f"Error updating logout status: {ex}")

        # Navigate to login screen
        from screens.login_screen import LoginScreen
        self.page.clean()
        self.page.add(LoginScreen(self.page))

    def _show_add_user_dialog(self, e):
        """Show add user dialog with actual save functionality"""
        import bcrypt

        # Get roles for dropdown
        roles = []
        try:
            db = get_db_session()
            from database.models import Role
            roles = db.query(Role).all()
            db.close()
        except Exception as ex:
            print(f"Error loading roles: {ex}")

        role_options = [ft.dropdown.Option(
            str(r.id), r.display_name) for r in roles]
        if not role_options:
            role_options = [
                ft.dropdown.Option("1", "Administrator"),
                ft.dropdown.Option("2", "Employee")
            ]

        username_field = ft.TextField(label="Username *", width=300)
        email_field = ft.TextField(label="Email *", width=300)
        password_field = ft.TextField(
            label="Password *", width=300, password=True)
        role_dropdown = ft.Dropdown(
            label="Role *", width=300, options=role_options)

        error_text = ft.Text("", color=ERROR, size=12, visible=False)

        def close_dialog(e):
            self.page.dialog.open = False
            self.page.update()

        def save_user(e):
            # Validate fields
            username = username_field.value.strip() if username_field.value else ""
            email = email_field.value.strip() if email_field.value else ""
            password = password_field.value.strip() if password_field.value else ""

            if not username or not email or not password:
                error_text.value = "All fields are required!"
                error_text.visible = True
                self.page.update()
                return

            if '@' not in email or '.' not in email:
                error_text.value = "Please enter a valid email!"
                error_text.visible = True
                self.page.update()
                return

            try:
                db = get_db_session()
                from database.models import User, UserStatus

                # Check if username exists
                existing = db.query(User).filter(
                    User.username == username).first()
                if existing:
                    error_text.value = "Username already exists!"
                    error_text.visible = True
                    db.close()
                    self.page.update()
                    return

                # Check if email exists
                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    error_text.value = "Email already registered!"
                    error_text.visible = True
                    db.close()
                    self.page.update()
                    return

                # Hash password
                hashed = bcrypt.hashpw(
                    password.encode(), bcrypt.gensalt()).decode()

                # Get role_id
                role_id = int(
                    role_dropdown.value) if role_dropdown.value else 2

                # Create user
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=hashed,
                    role_id=role_id,
                    status=UserStatus.ACTIVE
                )
                db.add(new_user)
                db.commit()
                db.close()

                self._show_message(
                    f"User '{username}' created successfully!", "success")
                self.page.dialog.open = False
                self.page.update()

                # Refresh dashboard to show updated stats
                self.refresh_dashboard()

            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self.page.update()
                import traceback
                traceback.print_exc()

        dlg = ft.AlertDialog(
            title=ft.Text("Add New User"),
            content=ft.Column([
                username_field,
                email_field,
                password_field,
                role_dropdown,
                error_text,
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Save", on_click=save_user, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="white"))
            ]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()


def show_admin_screen(page, user_data):
    """Helper function to show admin screen"""
    page.clean()
    page.add(AdminScreen(page, user_data))
