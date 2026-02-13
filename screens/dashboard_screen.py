"""
Vernika HRA - Dashboard Screen
Main dashboard with navigation to all modules
"""

import flet as ft
from datetime import datetime
from database.connection import get_db_session
from database.models import Employee, Attendance, LeaveRequest, Task
from sqlalchemy import func, and_


# Theme colors
PRIMARY = "#2E86AB"
SECONDARY = "#A23B72"
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
ERROR = "#F44336"
INFO = "#2196F3"
BACKGROUND = "#F5F5F5"


class DashboardScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.content = self._build_content()

    def _get_db(self):
        """Get database session"""
        return get_db_session()

    def _build_content(self):
        """Build the dashboard content"""
        # Get user info
        username = "User"
        if isinstance(self.user, dict):
            username = self.user.get('username', 'User')
        elif hasattr(self.user, 'username'):
            username = self.user.username

        # Get stats
        stats = self._get_dashboard_stats()

        # Header
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.DASHBOARD, color="WHITE", size=24),
                    ft.Text("Vernika HRA", size=18, color="WHITE",
                            weight=ft.FontWeight.BOLD),
                ], spacing=10),
                ft.Container(expand=True),
                ft.Row([
                    ft.Icon(ft.Icons.NOTIFICATIONS, color="WHITE", size=20),
                    ft.Text(f"Welcome, {username}", size=14, color="WHITE"),
                    ft.Container(width=10),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color="WHITE",
                        on_click=self.logout,
                        tooltip="Logout"
                    ),
                ], spacing=5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        )

        # Quick stats
        stats_row = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            content=ft.Row([
                self._create_stat_card("Total Employees", str(stats.get('total_employees', 0)),
                                       ft.Icons.PEOPLE, INFO),
                self._create_stat_card("Present Today", str(stats.get('present_today', 0)),
                                       ft.Icons.CHECK_CIRCLE, SUCCESS),
                self._create_stat_card("On Leave", str(stats.get('on_leave', 0)),
                                       ft.Icons.EVENT_BUSY, WARNING),
                self._create_stat_card("Pending Tasks", str(stats.get('pending_tasks', 0)),
                                       ft.Icons.TASK, ERROR),
            ], spacing=20),
        )

        # Quick actions grid
        quick_actions = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column([
                ft.Text("Quick Actions", size=16,
                        weight=ft.FontWeight.BOLD, color="#333"),
                ft.Container(height=10),
                ft.Row([
                    self._create_action_card("My Profile", ft.Icons.PERSON, "View profile",
                                             PRIMARY, self._go_to_profile),
                    self._create_action_card("Attendance", ft.Icons.EVENT, "Mark attendance",
                                             WARNING, self._go_to_attendance),
                    self._create_action_card("Leave", ft.Icons.CALENDAR_MONTH, "Apply leave",
                                             SECONDARY, self._go_to_leaves),
                    self._create_action_card("Tasks", ft.Icons.TASK, "View tasks",
                                             INFO, self._go_to_tasks),
                ], spacing=15),
                ft.Container(height=15),
                ft.Row([
                    self._create_action_card("Employees", ft.Icons.BADGE, "Manage employees",
                                             SUCCESS, self._go_to_employees),
                    self._create_action_card("Departments", ft.Icons.BUSINESS, "Manage departments",
                                             "#009688", self._go_to_departments),
                    self._create_action_card("Positions", ft.Icons.WORK, "Manage positions",
                                             "#673AB7", self._go_to_positions),
                    self._create_action_card("Chat", ft.Icons.CHAT, "Team chat",
                                             "#FF5722", self._go_to_chat),
                ], spacing=15),
            ], spacing=0),
        )

        # Admin section (for admin users)
        admin_section = ft.Container()
        user_role = ""
        if isinstance(self.user, dict):
            user_role = self.user.get('role', '').lower()
        elif hasattr(self.user, 'role'):
            user_role = self.user.role.lower()

        if user_role == 'admin':
            admin_section = ft.Container(
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                content=ft.Column([
                    ft.Text("Administration", size=16,
                            weight=ft.FontWeight.BOLD, color="#333"),
                    ft.Container(height=10),
                    ft.Row([
                        self._create_action_card("Admin Panel", ft.Icons.ADMIN_PANEL_SETTINGS,
                                                 "Full admin access", PRIMARY, self._go_to_admin),
                        self._create_action_card("Reports", ft.Icons.ASSESSMENT, "View reports",
                                                 "#607D8B", self._go_to_reports),
                        self._create_action_card("Settings", ft.Icons.SETTINGS, "System settings",
                                                 "#795548", self._go_to_settings),
                        self._create_action_card("Announcements", ft.Icons.CAMPAIGN,
                                                 "Company news", "#E91E63", self._go_to_announcements),
                    ], spacing=15),
                ], spacing=0),
            )

        # Get recent activities
        recent_activities = self._get_recent_activities()

        # Recent activity
        recent_activity = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column([
                ft.Text("Recent Activity", size=16,
                        weight=ft.FontWeight.BOLD, color="#333"),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        self._create_activity_item(
                            activity['text'], activity['time'], activity['icon'])
                        for activity in recent_activities
                    ]),
                    bgcolor="white",
                    padding=15,
                    border_radius=10,
                ),
            ], spacing=0),
        )

        return ft.Column([
            header,
            ft.Column([
                stats_row,
                ft.Divider(),
                quick_actions,
                admin_section,
                ft.Divider(),
                recent_activity,
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    def _get_dashboard_stats(self):
        """Get dashboard statistics"""
        stats = {
            'total_employees': 0,
            'present_today': 0,
            'on_leave': 0,
            'pending_tasks': 0,
        }
        try:
            session = self._get_db()

            # Total employees
            from database.models import Employee
            total = session.query(func.count(Employee.id)).filter(
                Employee.is_active == True).scalar()
            stats['total_employees'] = total or 0

            # Present today
            from database.models import Attendance, AttendanceStatus
            today = datetime.now().date()
            present = session.query(func.count(Attendance.id)).filter(
                and_(
                    Attendance.date == today,
                    Attendance.status == AttendanceStatus.PRESENT
                )
            ).scalar()
            stats['present_today'] = present or 0

            # On leave
            from database.models import LeaveRequest, LeaveStatus
            on_leave = session.query(func.count(LeaveRequest.id)).filter(
                and_(
                    LeaveRequest.status == LeaveStatus.APPROVED,
                    LeaveRequest.start_date <= today,
                    LeaveRequest.end_date >= today
                )
            ).scalar()
            stats['on_leave'] = on_leave or 0

            # Pending tasks
            from database.models import Task, TaskStatus
            pending = session.query(func.count(Task.id)).filter(
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            ).scalar()
            stats['pending_tasks'] = pending or 0

            session.close()
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")

        return stats

    def _get_recent_activities(self):
        """Get recent activities from database"""
        activities = []
        try:
            session = self._get_db()

            # Get recent leave requests
            from database.models import LeaveRequest
            recent_leaves = session.query(LeaveRequest).order_by(
                LeaveRequest.created_at.desc()
            ).limit(5).all()

            for lr in recent_leaves:
                from database.operations import get_employee_by_id
                emp = get_employee_by_id(
                    session, lr.employee_id) if lr.employee_id else None
                emp_name = f"{emp.first_name} {emp.last_name}" if emp else "Unknown"
                status_str = str(lr.status.value) if hasattr(
                    lr.status, 'value') else str(lr.status)
                activities.append({
                    'text': f"Leave: {emp_name} - {status_str}",
                    'icon': ft.Icons.CALENDAR_MONTH,
                    'time': self._format_time_ago(lr.created_at) if lr.created_at else "Recently"
                })

            # Get recent attendances
            from database.models import Attendance
            recent_att = session.query(Attendance).order_by(
                Attendance.created_at.desc()
            ).limit(5).all()

            for att in recent_att:
                from database.operations import get_employee_by_id
                emp = get_employee_by_id(
                    session, att.employee_id) if att.employee_id else None
                emp_name = f"{emp.first_name} {emp.last_name}" if emp else "Unknown"
                status_str = str(att.status.value) if hasattr(
                    att.status, 'value') else str(att.status)
                activities.append({
                    'text': f"Attendance: {emp_name} - {status_str}",
                    'icon': ft.Icons.CHECK,
                    'time': self._format_time_ago(att.created_at) if att.created_at else "Recently"
                })

            session.close()
        except Exception as e:
            print(f"Error getting recent activities: {e}")

        # If no activities, return sample data
        if not activities:
            activities = [
                {'text': "New employee joined",
                    'icon': ft.Icons.PERSON_ADD, 'time': "Recently"},
                {'text': "Leave request submitted",
                    'icon': ft.Icons.CALENDAR_MONTH, 'time': "Recently"},
                {'text': "Task completed",
                    'icon': ft.Icons.TASK_ALT, 'time': "Recently"},
                {'text': "Attendance marked",
                    'icon': ft.Icons.CHECK, 'time': "Recently"},
            ]

        return activities[:4]

    def _format_time_ago(self, dt):
        """Format datetime as time ago"""
        if not dt:
            return "Recently"
        now = datetime.now()
        if hasattr(dt, 'replace'):
            dt = dt.replace(tzinfo=None)
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

    def _create_stat_card(self, title: str, value: str, icon_name, color: str):
        """Create a statistics card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon=icon_name, size=28, color=color),
                    ft.Text(value, size=24,
                            weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(title, size=12, color="#666"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=15,
                width=130,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=2
        )

    def _create_action_card(self, title: str, icon_name, subtitle: str, color: str, on_click):
        """Create an action card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon=icon_name, size=32, color=color),
                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle, size=11, color="#666"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=15,
                width=120,
                alignment=ft.alignment.Alignment(0, 0),
                ink=True,
                on_click=on_click,
            ),
            elevation=2,
        )

    def _create_activity_item(self, text: str, time_ago: str, icon_name):
        """Create a recent activity item"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon_name, size=18, color=PRIMARY),
                ft.Text(text, size=13, expand=True),
                ft.Text(time_ago, size=11, color="#999"),
            ], spacing=10),
            padding=ft.padding.symmetric(vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, "#eee")),
        )

    def _go_to_profile(self, e):
        """Navigate to profile screen"""
        from screens.profile_screen import ProfileScreen
        self._page.clean()
        self._page.add(ProfileScreen(self._page, self.user))

    def _go_to_attendance(self, e):
        """Navigate to attendance screen"""
        from screens.attendance_screen import AttendanceScreen
        # Determine view mode based on user role
        user_role = ""
        if isinstance(self.user, dict):
            user_role = self.user.get('role', '').lower()
        view_mode = "admin" if user_role == 'admin' else "employee"
        self._page.clean()
        self._page.add(AttendanceScreen(
            self._page, self.user, view_mode=view_mode))

    def _go_to_leaves(self, e):
        """Navigate to leaves screen"""
        from screens.leaves_screen import LeavesScreen
        # Determine view mode based on user role
        user_role = ""
        if isinstance(self.user, dict):
            user_role = self.user.get('role', '').lower()
        view_mode = "admin" if user_role == 'admin' else "employee"
        self._page.clean()
        self._page.add(LeavesScreen(
            self._page, self.user, view_mode=view_mode))

    def _go_to_tasks(self, e):
        """Navigate to tasks screen"""
        from screens.tasks_screen import TasksScreen
        self._page.clean()
        self._page.add(TasksScreen(self._page, self.user))

    def _go_to_employees(self, e):
        """Navigate to employees screen"""
        # Check if user has access
        user_role = ""
        if isinstance(self.user, dict):
            user_role = self.user.get('role', '').lower()
        elif hasattr(self.user, 'role'):
            user_role = self.user.role.lower()

        # Only admin can access employees management
        if user_role != 'admin':
            # Show access denied message
            snack = ft.SnackBar(
                content=ft.Text(
                    "Access Restricted: Only administrators can manage employees"),
                bgcolor="#F44336"
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
            return

        from screens.employees_screen import show_employees
        show_employees(self._page, self.user)

    def _go_to_departments(self, e):
        """Navigate to departments screen"""
        from screens.departments_screen import show_departments
        show_departments(self._page, self.user)

    def _go_to_positions(self, e):
        """Navigate to positions screen"""
        from screens.positions_screen import show_positions
        show_positions(self._page, self.user)

    def _go_to_chat(self, e):
        """Navigate to chat screen"""
        from screens.chat_screen import ChatScreen
        self._page.clean()
        self._page.add(ChatScreen(self._page, self.user))

    def _go_to_admin(self, e):
        """Navigate to admin screen"""
        from screens.admin_screen import AdminScreen
        self._page.clean()
        self._page.add(AdminScreen(self._page, self.user))

    def _go_to_reports(self, e):
        """Navigate to reports screen"""
        from screens.reports_screen import ReportsScreen
        self._page.clean()
        self._page.add(ReportsScreen(self._page))

    def _go_to_settings(self, e):
        """Navigate to settings screen"""
        from screens.settings_screen import SettingsScreen
        self._page.clean()
        self._page.add(SettingsScreen(self._page, self.user))

    def _go_to_announcements(self, e):
        """Navigate to announcements screen"""
        from screens.announcements_screen import AnnouncementsScreen
        self._page.clean()
        self._page.add(AnnouncementsScreen(self._page))

    def logout(self, e):
        """Handle logout"""
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))


def show_dashboard(page, user):
    """Helper function to show dashboard"""
    page.clean()
    page.add(DashboardScreen(page, user))
