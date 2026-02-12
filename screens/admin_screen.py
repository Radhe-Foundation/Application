"""
Vernika Application - Admin Screen
Admin dashboard with full management capabilities for all modules
"""

import flet as ft
from database.connection import get_db_session
from auth.role_check import check_admin_access

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

        # Verify admin access
        if not check_admin_access(current_user):
            self._handle_access_denied()
            return

        # Build content with tabs
        self.content = self._build_content()
        print("✓ AdminScreen initialized")

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
        # Create tabs with NavigationRail for sidebar navigation
        return ft.Container(
            content=ft.Row([
                # Navigation Rail (sidebar)
                ft.NavigationRail(
                    selected_index=0,
                    destinations=[
                        ft.NavigationRailDestination(
                            icon=ft.Icons.DASHBOARD,
                            label="Dashboard"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.CHAT,
                            label="Chat"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.TASK,
                            label="Tasks"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.LIST_ALT,
                            label="Todo"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.BUSINESS,
                            label="Departments"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.EVENT,
                            label="Attendance"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.EVENT_BUSY,
                            label="Leave"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.BADGE,
                            label="Employees"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.WORK,
                            label="Positions"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.CAMPAIGN,
                            label="News"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.FOLDER,
                            label="Documents"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.TRENDING_UP,
                            label="Performance"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.ASSESSMENT,
                            label="Reports"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.SECURITY,
                            label="Access"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.SETTINGS,
                            label="Settings"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.HISTORY,
                            label="Audit"
                        ),
                    ],
                    on_change=self._on_nav_change,
                    extended=True,
                    bgcolor=SURFACE,
                    min_width=100,
                    label_type=ft.NavigationRailLabelType.ALL,
                ),
                ft.VerticalDivider(width=1),
                # Main content area
                ft.Container(
                    content=ft.Column([
                        # Header
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
        """Handle navigation rail change"""
        index = e.control.selected_index
        # Update the content
        content = self.content.content.controls[2]  # Get the content container
        content.content = self._get_tab_content(index)
        self.page.update()

    def _get_tab_content(self, index):
        """Get content for the selected tab"""
        tab_methods = [
            self._create_dashboard_tab,
            self._create_chat_tab,
            self._create_tasks_tab,
            self._create_todo_tab,
            self._create_departments_tab,
            self._create_attendance_tab,
            self._create_leaves_tab,
            self._create_employees_tab,
            self._create_positions_tab,
            self._create_announcements_tab,
            self._create_documents_tab,
            self._create_performance_tab,
            self._create_reports_tab,
            self._create_screen_access_tab,
            self._create_settings_tab,
            self._create_audit_tab,
        ]
        if 0 <= index < len(tab_methods):
            return tab_methods[index]()
        return self._create_dashboard_tab()

    def _create_header(self):
        """Create header with user info and logout"""
        return ft.Container(
            content=ft.Row([
                ft.Text(
                    "Vernika HRA - Admin Dashboard",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY
                ),
                ft.Container(expand=True),
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
        """Create dashboard overview tab"""
        # Get stats
        stats = self._get_dashboard_stats()

        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Admin Dashboard",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY
                ),
                ft.Container(height=20),

                # Stats Cards Row 1
                ft.Text(
                    "Statistics Overview",
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
                ], spacing=20),
                ft.Container(height=15),
                # Stats Cards Row 2
                ft.Row([
                    self._create_stat_card(
                        "Present Today", str(stats.get('present_today', 0)), ft.Icons.CHECK_CIRCLE, SUCCESS),
                    self._create_stat_card(
                        "On Leave", str(stats.get('on_leave', 0)), ft.Icons.EVENT_BUSY, WARNING),
                    self._create_stat_card(
                        "Pending Tasks", str(stats.get('pending_tasks', 0)), ft.Icons.PENDING, ORANGE_500),
                    self._create_stat_card(
                        "Positions", str(stats.get('positions', 0)), ft.Icons.WORK, INDIGO_500),
                ], spacing=20),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Quick Actions
                ft.Text(
                    "Quick Actions",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY
                ),
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        "Add New User",
                        icon=ft.Icons.ADD,
                        on_click=lambda _: self._navigate_to_tab(1),
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="white")
                    ),
                    ft.ElevatedButton(
                        "Manage Employees",
                        icon=ft.Icons.BADGE,
                        on_click=lambda _: self._navigate_to_tab(7),
                        style=ft.ButtonStyle(bgcolor=ORANGE_500, color="white")
                    ),
                    ft.ElevatedButton(
                        "View Reports",
                        icon=ft.Icons.ASSESSMENT,
                        on_click=lambda _: self._navigate_to_tab(12),
                        style=ft.ButtonStyle(bgcolor=PURPLE_500, color="white")
                    ),
                    ft.ElevatedButton(
                        "System Settings",
                        icon=ft.Icons.SETTINGS,
                        on_click=lambda _: self._navigate_to_tab(14),
                        style=ft.ButtonStyle(bgcolor=TEAL_500, color="white")
                    ),
                ], spacing=10),

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

                # Row 1: Tasks, Todo, Departments, Attendance
                ft.Text("Core Management", size=14,
                        color=TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                ft.Container(height=8),
                ft.Row([
                    self._create_module_card(
                        "Tasks", ft.Icons.TASK, "Task Management", 2, ORANGE_500),
                    self._create_module_card(
                        "Todo", ft.Icons.LIST_ALT, "Todo Lists", 3, CYAN_600),
                    self._create_module_card(
                        "Departments", ft.Icons.BUSINESS, "Departments", 4, GREEN_500),
                    self._create_module_card(
                        "Attendance", ft.Icons.EVENT, "Attendance", 5, BLUE_500),
                ], spacing=15),

                ft.Container(height=15),
                # Row 2: Leave, Announcements, Documents, Positions
                ft.Text("HR Management", size=14, color=TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500),
                ft.Container(height=8),
                ft.Row([
                    self._create_module_card(
                        "Leave", ft.Icons.EVENT_BUSY, "Leave Management", 6, PURPLE_500),
                    self._create_module_card(
                        "Announcements", ft.Icons.CAMPAIGN, "News & Updates", 9, RED_500),
                    self._create_module_card(
                        "Documents", ft.Icons.FOLDER, "Documents", 10, AMBER_500),
                    self._create_module_card(
                        "Positions", ft.Icons.WORK, "Job Positions", 8, INDIGO_500),
                ], spacing=15),

                ft.Container(height=15),
                # Row 3: Performance, Reports, Settings, Chat
                ft.Text("Admin & Tools", size=14, color=TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500),
                ft.Container(height=8),
                ft.Row([
                    self._create_module_card(
                        "Performance", ft.Icons.TRENDING_UP, "Performance Reviews", 11, PINK_500),
                    self._create_module_card(
                        "Reports", ft.Icons.ASSESSMENT, "Reports & Analytics", 12, CYAN_600),
                    self._create_module_card(
                        "Settings", ft.Icons.SETTINGS, "System Settings", 14, TEAL_500),
                    self._create_module_card(
                        "Chat", ft.Icons.CHAT, "Team Chat", 1, BLUE_500),
                ], spacing=15),

                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),

                # Additional Management
                ft.Text(
                    "User & Access Management",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY
                ),
                ft.Container(height=10),
                ft.Row([
                    self._create_module_card(
                        "Employees", ft.Icons.BADGE, "Employee Mgmt", 7, SUCCESS),
                    self._create_module_card(
                        "Screen Access", ft.Icons.SECURITY, "Access Control", 13, WARNING),
                    self._create_module_card(
                        "Audit Logs", ft.Icons.HISTORY, "Activity Logs", 15, ERROR),
                ], spacing=15),

            ], scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(20)
        )

    def _create_stat_card(self, title: str, value: str, icon_name, color):
        """Create a statistics card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon=icon_name, size=40, color=color),
                    ft.Text(value, size=32, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=14, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=ft.padding.all(20),
                width=180,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=3
        )

    def _create_module_card(self, title: str, icon_name, subtitle: str, tab_index: int, color: str):
        """Create a module shortcut card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon=icon_name, size=36, color=color),
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle, size=11, color=TEXT_SECONDARY),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Open",
                        icon=ft.Icons.ARROW_FORWARD,
                        on_click=lambda _: self._navigate_to_tab(tab_index),
                        style=ft.ButtonStyle(bgcolor=color, color="white"),
                        height=32,
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=ft.padding.all(15),
                width=150,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=2
        )

    def _get_dashboard_stats(self):
        """Get dashboard statistics"""
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
            import sqlite3
            from datetime import datetime

            conn = sqlite3.connect('vernika.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Total users
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            stats['total_users'] = result[0] if result else 0

            # Active users
            cursor.execute(
                "SELECT COUNT(*) as count FROM users WHERE status = 'active'")
            result = cursor.fetchone()
            stats['active_users'] = result[0] if result else 0

            # Total employees
            cursor.execute(
                "SELECT COUNT(*) as count FROM employees WHERE is_active = 1")
            result = cursor.fetchone()
            stats['total_employees'] = result[0] if result else 0

            # Audit logs
            cursor.execute("SELECT COUNT(*) as count FROM audit_logs")
            result = cursor.fetchone()
            stats['audit_logs'] = result[0] if result else 0

            # Present today
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                "SELECT COUNT(*) as count FROM attendances WHERE date = ? AND status = 'present'", (today,))
            result = cursor.fetchone()
            stats['present_today'] = result[0] if result else 0

            # On leave
            cursor.execute("""SELECT COUNT(*) as count FROM leave_requests 
                WHERE status = 'approved' AND start_date <= ? AND end_date >= ?""", (today, today))
            result = cursor.fetchone()
            stats['on_leave'] = result[0] if result else 0

            # Pending tasks
            cursor.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE status NOT IN ('completed', 'cancelled')")
            result = cursor.fetchone()
            stats['pending_tasks'] = result[0] if result else 0

            # Departments
            cursor.execute("SELECT COUNT(*) as count FROM departments")
            result = cursor.fetchone()
            stats['departments'] = result[0] if result else 0

            # Positions
            cursor.execute("SELECT COUNT(*) as count FROM positions")
            result = cursor.fetchone()
            stats['positions'] = result[0] if result else 0

            conn.close()
        except Exception as e:
            print(f"Error getting stats: {e}")
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
        """Create employee management tab"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Employee Management",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Manage Employees",
                        icon=ft.Icons.BADGE,
                        on_click=self._show_employees,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="white")
                    )
                ]),
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.BADGE, size=60, color=PRIMARY),
                        ft.Container(height=10),
                        ft.Text("Employee Management", size=18,
                                weight=ft.FontWeight.BOLD),
                        ft.Text("Full employee management with add/edit/view features, ID cards, offer letters, and salary slips.",
                                size=14, color=TEXT_SECONDARY),
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            "Open Employee Management",
                            icon=ft.Icons.ARROW_FORWARD,
                            on_click=self._show_employees,
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="white"),
                            height=40,
                        )
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

    def _create_screen_access_tab(self):
        """Create screen access management tab with real-time controls"""
        import threading
        from utils.screen_access import (
            SCREEN_ACCESS_CONFIG, get_all_employees_for_access_management, set_screen_access, reset_to_defaults
        )

        # State for UI
        self._access_employees = get_all_employees_for_access_management()
        self._access_controls = {}

        def refresh_employees():
            self._access_employees = get_all_employees_for_access_management()
            self.page.update()

        def handle_toggle(user_id, screen_key):
            def _handler(e):
                is_enabled = e.control.value
                admin_id = self.current_user.get('id') if isinstance(
                    self.current_user, dict) else None
                set_screen_access(user_id, screen_key,
                                  is_enabled, granted_by=admin_id)
                refresh_employees()
            return _handler

        def handle_reset(user_id):
            def _handler(e):
                reset_to_defaults(user_id)
                refresh_employees()
            return _handler

        # Build table header
        screen_keys = list(SCREEN_ACCESS_CONFIG.keys())
        header_row = ft.Row([
            ft.Text("Employee", weight=ft.FontWeight.BOLD, width=180),
        ] + [ft.Text(SCREEN_ACCESS_CONFIG[k]["name"], size=12, weight=ft.FontWeight.BOLD, width=110, text_align=ft.TextAlign.CENTER) for k in screen_keys] + [ft.Text("Actions", weight=ft.FontWeight.BOLD, width=120)], spacing=5)

        # Build employee rows
        employee_rows = []
        for emp in self._access_employees:
            emp_name = emp['full_name'] or emp['username']
            row_controls = [
                ft.Text(emp_name, width=180, size=13, color=TEXT_PRIMARY),
            ]
            for k in screen_keys:
                toggle = ft.Switch(
                    value=emp['screen_access'].get(k, False),
                    on_change=handle_toggle(emp['user_id'], k),
                    active_color=PRIMARY,
                    inactive_thumb_color=ft.Colors.GREY_400,
                    width=110,
                    disabled=(k == 'profile')  # Profile always enabled
                )
                row_controls.append(toggle)
            # Actions: Reset
            row_controls.append(
                ft.ElevatedButton(
                    "Reset to Default",
                    icon=ft.Icons.RESTART_ALT,
                    on_click=handle_reset(emp['user_id']),
                    style=ft.ButtonStyle(bgcolor=WARNING, color="white"),
                    height=32,
                    width=120
                )
            )
            employee_rows.append(ft.Row(row_controls, spacing=5))

        # Compose the full UI
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY, size=28, color=PRIMARY),
                    ft.Container(width=10),
                    ft.Text("Screen Access Management",
                            size=24, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Text("Grant or revoke employee access to various screens.",
                        size=14, color=TEXT_SECONDARY),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        header_row,
                        ft.Divider(),
                        *employee_rows
                    ], scroll=ft.ScrollMode.AUTO),
                    bgcolor=SURFACE_VARIANT,
                    border_radius=ft.border_radius.all(10),
                    padding=ft.padding.all(20),
                    expand=True
                ),
            ], scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(20),
            expand=True
        )

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

    # ============ NEW TAB METHODS FOR ALL SCREENS ============

    def _create_chat_tab(self):
        """Create chat/communication tab"""
        from screens.chat_screen import ChatScreen
        return ft.Container(
            content=ChatScreen(self.page, self.current_user),
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
            content=AttendanceScreen(self.page, self.current_user),
            expand=True
        )

    def _create_leaves_tab(self):
        """Create leave management tab"""
        from screens.leaves_screen import LeavesScreen
        return ft.Container(
            content=LeavesScreen(self.page, self.current_user),
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

    def _create_documents_tab(self):
        """Create documents management tab"""
        from screens.documents_screen import DocumentsScreen
        return ft.Container(
            content=DocumentsScreen(self.page),
            expand=True
        )

    def _create_performance_tab(self):
        """Create performance review tab"""
        from screens.performance_screen import PerformanceScreen
        return ft.Container(
            content=PerformanceScreen(self.page),
            expand=True
        )

    def _create_reports_tab(self):
        """Create reports tab"""
        from screens.reports_screen import ReportsScreen
        return ft.Container(
            content=ReportsScreen(self.page),
            expand=True
        )

    def _create_settings_tab(self):
        """Create settings tab"""
        from screens.settings_screen import SettingsScreen
        return ft.Container(
            content=SettingsScreen(self.page, self.current_user),
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
        self.page.add(AttendanceScreen(self.page, self.current_user))

    def _show_leaves(self, e):
        """Navigate to Leaves screen"""
        from screens.leaves_screen import LeavesScreen
        self.page.clean()
        self.page.add(LeavesScreen(self.page, self.current_user))

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

    def _show_documents(self, e):
        """Navigate to Documents screen"""
        from screens.documents_screen import DocumentsScreen
        self.page.clean()
        self.page.add(DocumentsScreen(self.page))

    def _show_performance(self, e):
        """Navigate to Performance screen"""
        from screens.performance_screen import PerformanceScreen
        self.page.clean()
        self.page.add(PerformanceScreen(self.page))

    def _show_reports(self, e):
        """Navigate to Reports screen"""
        from screens.reports_screen import ReportsScreen
        self.page.clean()
        self.page.add(ReportsScreen(self.page))

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
        """Show a snackbar message"""
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
        from screens.login_screen import LoginScreen
        self.page.clean()
        self.page.add(LoginScreen(self.page))

    def _show_add_user_dialog(self, e):
        """Show add user dialog"""
        def close_dialog(e):
            self.page.dialog.open = False
            self.page.update()

        def save_user(e):
            self._show_message("User added successfully!")
            self.page.dialog.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Add New User"),
            content=ft.Column([
                ft.TextField(label="Username", width=300),
                ft.TextField(label="Email", width=300),
                ft.TextField(label="Password", password=True, width=300),
                ft.Dropdown(
                    label="Role",
                    options=[
                        ft.dropdown.Option("admin"),
                        ft.dropdown.Option("employee")
                    ],
                    width=300
                )
            ], tight=True),
            actions=[
                ft.ElevatedButton("Cancel", on_click=close_dialog),
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
