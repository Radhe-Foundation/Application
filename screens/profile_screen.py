"""
Vernika HRA - Profile Screen
Simple profile screen for non-admin users with screen access management
"""

import flet as ft
import sqlite3
from datetime import datetime


class ProfileScreen(ft.Container):
    def __init__(self, page: ft.Page, user_data: dict = None):
        super().__init__()
        self._page = page
        self.user_data = user_data or {}
        self.expand = True
        self.employee_data = None
        self._get_employee_data()
        self.content = self.build_ui()

    def _get_db(self):
        """Get database connection"""
        conn = sqlite3.connect('vernika.db')
        conn.row_factory = sqlite3.Row
        return conn

    def _get_employee_data(self):
        """Fetch employee data from database"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()

            # Get employee data based on user_id or email
            user_id = self.user_data.get("user_id")
            username = self.user_data.get("username", "")

            if user_id:
                cursor.execute("""
                    SELECT e.*, d.name as department_name, p.title as position_title,
                           r.name as role_name
                    FROM employees e
                    LEFT JOIN departments d ON e.department_id = d.id
                    LEFT JOIN positions p ON e.position_id = p.id
                    LEFT JOIN users u ON e.user_id = u.id
                    LEFT JOIN roles r ON u.role_id = r.id
                    WHERE e.user_id = ?
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT e.*, d.name as department_name, p.title as position_title,
                           r.name as role_name
                    FROM employees e
                    LEFT JOIN departments d ON e.department_id = d.id
                    LEFT JOIN positions p ON e.position_id = p.id
                    LEFT JOIN users u ON e.user_id = u.id
                    LEFT JOIN roles r ON u.role_id = r.id
                    WHERE u.username = ?
                """, (username,))

            emp = cursor.fetchone()
            conn.close()

            if emp:
                self.employee_data = dict(emp)
        except Exception as e:
            print(f"Error fetching employee data: {e}")
            self.employee_data = None

    def _get_leave_count(self):
        """Get leave counts from database"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            user_id = self.user_data.get("user_id")

            if user_id:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM leave_requests lr
                    JOIN employees e ON lr.employee_id = e.id
                    WHERE e.user_id = ? AND lr.status = 'pending'
                """, (user_id,))
                result = cursor.fetchone()
                conn.close()
                return result['count'] if result else 0
            conn.close()
        except Exception as e:
            print(f"Warning: Error getting leave count: {e}")
        return 0

    def _get_task_count(self):
        """Get pending task counts from database"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            user_id = self.user_data.get("user_id")

            if user_id:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM tasks
                    WHERE assigned_to_id = ? AND status != 'completed'
                """, (user_id,))
                result = cursor.fetchone()
                conn.close()
                return result['count'] if result else 0
            conn.close()
        except Exception as e:
            print(f"Warning: Error getting task count: {e}")
        return 0

    def _get_attendance_percentage(self):
        """Calculate attendance percentage"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            user_id = self.user_data.get("user_id")

            if user_id:
                # Get current month
                current_month = datetime.now().strftime('%Y-%m')

                # Get total working days this month (simplified - 22 days)
                total_days = 22

                # Get present days
                cursor.execute("""
                    SELECT COUNT(*) as count FROM attendances a
                    JOIN employees e ON a.employee_id = e.id
                    WHERE e.user_id = ? AND strftime('%Y-%m', a.date) = ?
                """, (user_id, current_month))
                result = cursor.fetchone()
                conn.close()

                present_days = result['count'] if result else 0
                percentage = (present_days / total_days *
                              100) if total_days > 0 else 0
                return min(100, round(percentage))
            conn.close()
        except Exception as e:
            print(f"Warning: Error calculating attendance: {e}")
        return 0

    def _can_access(self, screen_key: str) -> bool:
        """Check if user can access a specific screen based on screen_access table"""
        try:
            user_id = self.user_data.get("user_id")
            if not user_id:
                # If no user_id, allow access for now
                return True

            conn = self._get_db()
            cursor = conn.cursor()

            # Check screen_access table
            cursor.execute("""
                SELECT is_enabled FROM screen_access 
                WHERE user_id = ? AND screen_key = ?
            """, (user_id, screen_key))

            result = cursor.fetchone()
            conn.close()

            if result:
                return bool(result[0])

            # If no record exists, check role-based defaults
            # For employees, only profile is enabled by default
            user_role = self.user_data.get("role", "").lower()
            if user_role == "admin":
                return True  # Admin has access to everything

            # Default: employees only have profile access
            return screen_key == "profile"

        except Exception as e:
            print(f"Error checking screen access: {e}")
            # On error, allow access (fail-open)
            return True

    def _create_action_card(self, title, subtitle, icon, on_click, enabled: bool = True):
        """Create an action card with access control"""
        if enabled:
            # Enabled card - normal appearance
            return ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Icon(icon, size=40, color="#2E86AB"),
                        ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(subtitle, size=12, color="#757575"),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Open",
                            icon=ft.Icons.ARROW_FORWARD,
                            on_click=on_click,
                            style=ft.ButtonStyle(
                                bgcolor="#2E86AB", color="white")
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=ft.padding.all(20),
                    width=200
                ),
                elevation=3
            )
        else:
            # Disabled card - grayed out
            return ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Icon(icon, size=40, color="#BDBDBD"),
                        ft.Text(title, size=18,
                                weight=ft.FontWeight.BOLD, color="#9E9E9E"),
                        ft.Text(subtitle, size=12, color="#BDBDBD"),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Locked",
                            icon=ft.Icons.LOCK,
                            on_click=self._show_access_denied,
                            style=ft.ButtonStyle(
                                bgcolor="#E0E0E0", color="#9E9E9E"),
                            disabled=True
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=ft.padding.all(20),
                    width=200
                ),
                elevation=1
            )

    def _show_access_denied(self, e):
        """Show access denied message"""
        snack = ft.SnackBar(
            content=ft.Text(
                "Access Restricted: Contact administrator for access"),
            bgcolor="#DC3545"
        )
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _view_profile(self, e):
        """View profile (current screen)"""
        pass

    def _view_tasks(self, e):
        """View tasks"""
        from screens.tasks_screen import TasksScreen
        self._page.clean()
        self._page.add(TasksScreen(self._page, self.user_data))

    def _request_time_off(self, e):
        """Request time off"""
        from screens.leaves_screen import LeavesScreen
        self._page.clean()
        self._page.add(LeavesScreen(
            self._page, self.user_data, view_mode="employee"))

    def _view_attendance(self, e):
        """View attendance"""
        from screens.attendance_screen import AttendanceScreen
        self._page.clean()
        self._page.add(AttendanceScreen(
            self._page, self.user_data, view_mode="employee"))

    def _view_documents(self, e):
        """View documents"""
        from screens.documents_screen import DocumentsScreen
        self._page.clean()
        self._page.add(DocumentsScreen(self._page, self.user_data))

    def _view_chat(self, e):
        """View chat"""
        from screens.chat_screen import ChatScreen
        self._page.clean()
        self._page.add(ChatScreen(self._page, self.user_data))

    def build_ui(self):
        username = self.user_data.get("username", "User")
        emp = self.employee_data

        # Get real stats
        leave_count = self._get_leave_count()
        task_count = self._get_task_count()
        attendance_pct = self._get_attendance_percentage()

        # Personal info from database
        full_name = username
        role = "Employee"
        department = "Not assigned"
        position = "Not assigned"
        email = f"{username}@vernika.com"
        phone = "Not provided"
        date_of_joining = "N/A"

        if emp:
            full_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(
            )
            if not full_name:
                full_name = username
            role = emp.get('role_name', 'Employee')
            department = emp.get('department_name', 'Not assigned')
            position = emp.get('position_title', 'Not assigned')
            email = emp.get('email', email)
            phone = emp.get('phone', 'Not provided')
            doj = emp.get('date_of_joining')
            if doj:
                date_of_joining = str(doj)

        header = ft.Container(
            padding=15,
            bgcolor="#2E86AB",
            content=ft.Row([
                ft.Text("My Profile", size=18, color="WHITE",
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.LOGOUT, icon_color="WHITE",
                              on_click=self.logout),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

        # Profile card with real data
        profile_card = ft.Card(
            content=ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Container(
                        width=80, height=80,
                        bgcolor="#2E86AB",
                        border_radius=40,
                        content=ft.Text(
                            full_name[:1].upper(
                            ) if full_name else username[:1].upper(),
                            size=32,
                            color="WHITE",
                            weight=ft.FontWeight.BOLD
                        ),
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Text(full_name, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(role, size=14, color="#757575"),
                    ft.Container(height=10),
                    ft.Text(email, size=12, color="#757575"),
                    ft.Text(phone, size=12, color="#757575"),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Edit Profile",
                        icon=ft.Icons.EDIT,
                        width=200,
                        on_click=self.edit_profile,
                        bgcolor="#2E86AB",
                        color="WHITE",
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            ),
            width=300,
        )

        # Stats with real data
        stats = ft.Card(
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Quick Stats", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Column([
                            ft.Text(
                                str(leave_count), size=24, weight=ft.FontWeight.BOLD,
                                color="#2E86AB"),
                            ft.Text("Pending Leaves",
                                    size=12, color="#757575"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(width=30),
                        ft.Column([
                            ft.Text(
                                str(task_count), size=24, weight=ft.FontWeight.BOLD, color="#4CAF50"),
                            ft.Text("Tasks", size=12, color="#757575"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(width=30),
                        ft.Column([
                            ft.Text(
                                f"{attendance_pct}%", size=24, weight=ft.FontWeight.BOLD, color="#FF9800"),
                            ft.Text("Attendance", size=12, color="#757575"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(height=20),
                    ft.Text("Department", size=12, color="#757575"),
                    ft.Text(department, size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(height=5),
                    ft.Text("Position", size=12, color="#757575"),
                    ft.Text(position, size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(height=5),
                    ft.Text("Date of Joining", size=12, color="#757575"),
                    ft.Text(date_of_joining, size=14,
                            weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            ),
            expand=True,
        )

        # Action cards with screen access control
        action_cards = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column([
                ft.Text("Quick Actions", size=16,
                        weight=ft.FontWeight.BOLD, color="#333"),
                ft.Container(height=10),
                ft.Row([
                    self._create_action_card(
                        "My Profile",
                        "View and edit your profile",
                        ft.Icons.PERSON,
                        self._view_profile,
                        enabled=self._can_access("profile")
                    ),
                    self._create_action_card(
                        "My Tasks",
                        "View your assigned tasks",
                        ft.Icons.TASK,
                        self._view_tasks,
                        enabled=self._can_access("tasks")
                    ),
                    self._create_action_card(
                        "Time Off",
                        "Request time off",
                        ft.Icons.CALENDAR_MONTH,
                        self._request_time_off,
                        enabled=self._can_access("leaves")
                    ),
                ], spacing=20),
                ft.Container(height=15),
                ft.Row([
                    self._create_action_card(
                        "Attendance",
                        "View your attendance",
                        ft.Icons.EVENT,
                        self._view_attendance,
                        enabled=self._can_access("attendance")
                    ),
                    self._create_action_card(
                        "Documents",
                        "View your documents",
                        ft.Icons.DESCRIPTION,
                        self._view_documents,
                        enabled=self._can_access("documents")
                    ),
                    self._create_action_card(
                        "Chat",
                        "Chat with colleagues",
                        ft.Icons.CHAT,
                        self._view_chat,
                        enabled=self._can_access("chat")
                    ),
                ], spacing=20),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )

        content = ft.Row([
            profile_card,
            stats,
        ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Column([
            header,
            ft.Container(
                padding=20,
                content=ft.Column([
                    content,
                    ft.Container(height=20),
                    action_cards,
                ], expand=True),
                expand=True
            ),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    def logout(self, e):
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))

    def edit_profile(self, e):
        snack = ft.SnackBar(
            content=ft.Text("Profile editing coming soon!"),
            duration=3000
        )
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_profile_screen(page, user_data):
    """Helper function to show profile screen"""
    page.clean()
    page.add(ProfileScreen(page, user_data))
