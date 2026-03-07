"""
Vernika HRA - Dashboard Screen
Modern dashboard with sidebar navigation matching admin_screen style
"""

import flet as ft
from datetime import datetime
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Employee, Attendance, LeaveRequest, Task
from sqlalchemy import func, and_


# Theme colors - matching admin_screen
PRIMARY = "#2E86AB"
SECONDARY = "#A23B72"
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
ERROR = "#F44336"
INFO = "#2196F3"
BACKGROUND = "#F5F5F5"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"


class DashboardScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.content = self._build_content()

    def refresh(self):
        """Refresh the dashboard content"""
        self.content = self._build_content()
        self._page.update()

    def _build_content(self):
        """Build dashboard with modern sidebar navigation"""

        # Get user info
        username = "User"
        user_id = None
        user_role = "employee"

        if isinstance(self.user, dict):
            username = self.user.get('username', 'User')
            user_id = self.user.get('id')
            user_role = self.user.get('role', 'employee').lower()

        is_admin = user_role == 'admin'

        # Get stats
        stats = self._get_dashboard_stats()

        # Navigation items - simplified for dashboard
        nav_items = []

        # Define navigation
        nav_data = [
            (0, "Dashboard", ft.Icons.DASHBOARD, ft.Icons.DASHBOARD_OUTLINED),
            (1, "Profile", ft.Icons.PERSON, ft.Icons.PERSON_OUTLINED),
            (2, "Chat", ft.Icons.CHAT, ft.Icons.CHAT_OUTLINED),
            (3, "Mail", ft.Icons.EMAIL, ft.Icons.EMAIL_OUTLINED),
            (4, "Tasks", ft.Icons.TASK, ft.Icons.TASK_OUTLINED),
            (5, "Leave", ft.Icons.CALENDAR_MONTH,
             ft.Icons.CALENDAR_MONTH_OUTLINED),
            (6, "Attendance", ft.Icons.EVENT, ft.Icons.EVENT_OUTLINED),
        ]

        if is_admin:
            nav_data.extend([
                (7, "Employees", ft.Icons.BADGE, ft.Icons.BADGE_OUTLINED),
                (8, "Departments", ft.Icons.BUSINESS, ft.Icons.BUSINESS_OUTLINED),
                (9, "Teams", ft.Icons.GROUP, ft.Icons.GROUP_OUTLINED),
                (10, "Projects", ft.Icons.WORK, ft.Icons.WORK_OUTLINED),
            ])

        self._selected_nav_index = 0

        def create_nav_item(index, label, selected_icon, unselected_icon):
            def on_click(e):
                self._selected_nav_index = index
                for item in nav_items:
                    item.bgcolor = "transparent" if item != nav_items[index] else PRIMARY + "15"
                content_area.content = self._get_tab_content(index)
                self._page.update()

            return ft.Container(
                content=ft.Row([
                    ft.Icon(
                        selected_icon if index == self._selected_nav_index else unselected_icon,
                        size=20,
                        color=PRIMARY if index == self._selected_nav_index else TEXT_SECONDARY,
                    ),
                    ft.Text(
                        label,
                        size=13,
                        weight=ft.FontWeight.W_500 if index == self._selected_nav_index else ft.FontWeight.W_400,
                        color=PRIMARY if index == self._selected_nav_index else TEXT_SECONDARY,
                    ),
                ], spacing=8, alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                border_radius=8,
                bgcolor=PRIMARY + "15" if index == self._selected_nav_index else "transparent",
                on_click=on_click,
                ink=True,
            )

        # Create nav items
        for idx, label, sel_icon, unsel_icon in nav_data:
            nav_items.append(create_nav_item(idx, label, sel_icon, unsel_icon))

        # Sidebar
        sidebar = ft.Container(
            width=180,
            bgcolor=SURFACE,
            content=ft.Column([
                # Logo
                ft.Container(
                    content=ft.Image(
                        src="/assets/logo/Vernikalogo.png",
                        width=100,
                        height=60,
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=ft.padding.only(top=15, bottom=10),
                ),
                ft.Divider(height=1),
                # Navigation
                ft.ListView(
                    controls=nav_items,
                    spacing=2,
                    padding=10,
                    expand=True,
                ),
            ], spacing=0),
        )

        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Text(
                    "Vernika HRA - Dashboard",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY
                ),
                ft.Container(expand=True),
                ft.Text(
                    f"Welcome, {username}",
                    size=14,
                    color=TEXT_SECONDARY
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    tooltip="Logout",
                    on_click=self.logout,
                    icon_color=ERROR
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=SURFACE,
        )

        # Main content area
        content_area = ft.Container(
            content=self._get_tab_content(0),
            expand=True,
        )

        # Main layout
        return ft.Container(
            content=ft.Row([
                sidebar,
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=ft.Column([
                        header,
                        content_area,
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
        elif index == 7 and self._is_admin():
            return self._create_employees_tab()
        elif index == 8 and self._is_admin():
            return self._create_departments_tab()
        elif index == 9 and self._is_admin():
            return self._create_teams_tab()
        elif index == 10 and self._is_admin():
            return self._create_projects_tab()
        return self._create_dashboard_tab()

    def _is_admin(self):
        """Check if user is admin"""
        user_role = ""
        if isinstance(self.user, dict):
            user_role = self.user.get('role', '').lower()
        return user_role == 'admin'

    def _create_dashboard_tab(self):
        """Create main dashboard tab"""
        stats = self._get_dashboard_stats()

        return ft.Container(
            content=ft.Column([
                ft.Text("Dashboard Overview", size=24,
                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Container(height=20),

                # Stats cards
                ft.Row([
                    self._create_stat_card("Total Employees", str(
                        stats.get('total_employees', 0)), ft.Icons.PEOPLE, INFO),
                    self._create_stat_card("Present Today", str(
                        stats.get('present_today', 0)), ft.Icons.CHECK_CIRCLE, SUCCESS),
                    self._create_stat_card("On Leave", str(
                        stats.get('on_leave', 0)), ft.Icons.EVENT_BUSY, WARNING),
                    self._create_stat_card("Pending Tasks", str(
                        stats.get('pending_tasks', 0)), ft.Icons.TASK, ERROR),
                ], spacing=20),

                ft.Container(height=30),

                # Quick actions
                ft.Text("Quick Actions", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Row([
                    self._create_action_btn(
                        "My Profile", ft.Icons.PERSON, PRIMARY, self._go_to_profile),
                    self._create_action_btn(
                        "View Tasks", ft.Icons.TASK, INFO, self._go_to_tasks),
                    self._create_action_btn(
                        "Apply Leave", ft.Icons.CALENDAR_MONTH, SECONDARY, self._go_to_leaves),
                    self._create_action_btn(
                        "Attendance", ft.Icons.EVENT, WARNING, self._go_to_attendance),
                ], spacing=15),

                ft.Container(height=30),

                # Recent activity
                ft.Text("Recent Activity", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                self._create_recent_activity(),

            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

    def _create_stat_card(self, title, value, icon_name, color):
        """Create a statistics card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon=icon_name, size=32, color=color),
                    ft.Text(value, size=28,
                            weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(title, size=12, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=20,
                width=150,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=2
        )

    def _create_action_btn(self, title, icon_name, color, on_click):
        """Create action button"""
        return ft.Container(
            content=ft.ElevatedButton(
                title,
                icon=icon_name,
                on_click=on_click,
                style=ft.ButtonStyle(bgcolor=color, color="WHITE"),
                height=45,
            ),
        )

    def _create_recent_activity(self):
        """Create recent activity section"""
        activities = self._get_recent_activities()

        if not activities:
            return ft.Container(
                content=ft.Text("No recent activity", size=14,
                                color=TEXT_SECONDARY),
                padding=20,
            )

        items = []
        for activity in activities:
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(activity['icon'], size=18, color=PRIMARY),
                        ft.Text(activity['text'], size=13, expand=True),
                        ft.Text(activity['time'], size=11,
                                color=TEXT_SECONDARY),
                    ], spacing=10),
                    padding=10,
                    border=ft.border.only(bottom=ft.BorderSide(1, "#eee")),
                )
            )

        return ft.Container(
            content=ft.Column(items, spacing=0),
            bgcolor=SURFACE,
            border_radius=10,
            padding=10,
        )

    def _get_dashboard_stats(self):
        """Get dashboard statistics with caching for better performance"""
        # Use cached version for better performance
        from utils.cache import get_cached_dashboard_stats
        stats = get_cached_dashboard_stats()

        # Return the cached stats
        return {
            'total_employees': stats.get('total_employees', 0),
            'present_today': stats.get('present_today', 0),
            'on_leave': stats.get('on_leave', 0),
            'pending_tasks': stats.get('pending_tasks', 0),
        }

    def _get_recent_activities(self):
        """Get recent activities"""
        activities = []
        try:
            # Use context manager for proper session handling
            with get_session() as session:
                # Get recent leave requests with eager loading
                from database.models import LeaveRequest
                recent_leaves = session.query(LeaveRequest).order_by(
                    LeaveRequest.created_at.desc()
                ).limit(3).all()

                for lr in recent_leaves:
                    if lr.employee_id:
                        emp = session.query(Employee).filter(
                            Employee.id == lr.employee_id).first()
                        if emp:
                            emp_name = f"{emp.first_name} {emp.last_name}"
                        else:
                            emp_name = "Unknown"
                    else:
                        emp_name = "Unknown"

                    status_str = str(lr.status.value) if hasattr(
                        lr.status, 'value') else str(lr.status)
                    activities.append({
                        'text': f"Leave: {emp_name} - {status_str}",
                        'icon': ft.Icons.CALENDAR_MONTH,
                        'time': self._format_time_ago(lr.created_at) if lr.created_at else "Recently"
                    })

        except Exception as e:
            print(f"Error getting recent activities: {e}")

        return activities[:5]

    def _format_time_ago(self, dt):
        """Format datetime as time ago"""
        if not dt:
            return "Recently"
        now = datetime.now()
        if hasattr(dt, 'replace'):
            dt = dt.replace(tzinfo=None)
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"

    # Tab content methods
    def _create_profile_tab(self):
        from screens.profile_screen import ProfileScreen
        return ft.Container(content=ProfileScreen(self._page, self.user), expand=True)

    def _create_chat_tab(self):
        from screens.chat_screen import ChatScreen
        return ft.Container(content=ChatScreen(self._page, self.user), expand=True)

    def _create_mail_tab(self):
        from screens.mail_screen import MailScreen
        return ft.Container(content=MailScreen(self._page, self.user), expand=True)

    def _create_tasks_tab(self):
        from screens.tasks_screen import TasksScreen
        return ft.Container(content=TasksScreen(self._page, self.user), expand=True)

    def _create_leaves_tab(self):
        from screens.leaves_screen import LeavesScreen
        view_mode = "admin" if self._is_admin() else "employee"
        return ft.Container(content=LeavesScreen(self._page, self.user, view_mode=view_mode), expand=True)

    def _create_attendance_tab(self):
        from screens.attendance_screen import AttendanceScreen
        view_mode = "admin" if self._is_admin() else "employee"
        return ft.Container(content=AttendanceScreen(self._page, self.user, view_mode=view_mode), expand=True)

    def _create_employees_tab(self):
        from screens.employees_screen import show_employees
        show_employees(self._page, self.user)
        return ft.Container()

    def _create_departments_tab(self):
        from screens.departments_screen import show_departments
        show_departments(self._page, self.user)
        return ft.Container()

    def _create_teams_tab(self):
        from screens.teams_screen import TeamsScreen
        return ft.Container(content=TeamsScreen(self._page, self.user), expand=True)

    def _create_projects_tab(self):
        from screens.projects_screen import ProjectsScreen
        return ft.Container(content=ProjectsScreen(self._page, self.user), expand=True)

    # Navigation methods
    def _go_to_profile(self, e):
        self._selected_nav_index = 1
        content_area = self.content.content.controls[1]
        content_area.content.controls[1].content = self._create_profile_tab()
        self._page.update()

    def _go_to_tasks(self, e):
        from screens.tasks_screen import TasksScreen
        self._page.clean()
        self._page.add(TasksScreen(self._page, self.user))

    def _go_to_leaves(self, e):
        from screens.leaves_screen import LeavesScreen
        view_mode = "admin" if self._is_admin() else "employee"
        self._page.clean()
        self._page.add(LeavesScreen(
            self._page, self.user, view_mode=view_mode))

    def _go_to_attendance(self, e):
        from screens.attendance_screen import AttendanceScreen
        view_mode = "admin" if self._is_admin() else "employee"
        self._page.clean()
        self._page.add(AttendanceScreen(
            self._page, self.user, view_mode=view_mode))

    def logout(self, e):
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))


def show_dashboard(page, user):
    """Helper function to show dashboard"""
    page.clean()
    page.add(DashboardScreen(page, user))
