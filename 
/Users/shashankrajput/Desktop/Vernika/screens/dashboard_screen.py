"""
Vernika HRA - Dashboard Screen
"""

import flet as ft
from core.theme import PRIMARY


class DashboardScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        if isinstance(user, dict):
            self.user = user
            self.username = user.get('username', 'User')
            self.user_id = user.get('id')
        else:
            self.user = user
            self.username = getattr(user, 'username', 'User')
            self.user_id = getattr(user, 'id', None)
        self.expand = True
        self.bgcolor = "#F5F5F5"
        self.content = self.build_ui()

    def build_ui(self):
        header = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color="WHITE", size=22),
                    ft.Text(f"Welcome, {self.username}", size=15,
                            color="WHITE", weight=ft.FontWeight.BOLD),
                ], spacing=8),
                ft.Container(expand=True),
                ft.TextButton("Logout", on_click=self.logout,
                              style=ft.ButtonStyle(color="WHITE")),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        )

        total_users = total_employees = total_departments = pending_tasks = 0
        try:
            import sqlite3
            conn = sqlite3.connect('vernika.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM employees")
            total_employees = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM departments")
            total_departments = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'todo'")
            pending_tasks = cursor.fetchone()[0]
            conn.close()
        except:
            pass

        def stat_card(title, value, icon_name, color):
            return ft.Container(
                width=130, height=110,
                padding=ft.padding.all(12),
                border_radius=12, bgcolor="WHITE",
                shadow=ft.BoxShadow(spread_radius=0.5,
                                    blur_radius=4, color="#00000015"),
                content=ft.Column([
                    ft.Icon(icon_name, size=28, color=color),
                    ft.Text(value, size=24,
                            weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(title, size=11, color="#757575"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            )

        stats_row = ft.Row([
            ft.Container(expand=True),
            stat_card("Users", str(total_users), ft.Icons.PEOPLE, "#2196F3"),
            stat_card("Employees", str(total_employees),
                      ft.Icons.BADGE, "#4CAF50"),
            stat_card("Depts", str(total_departments),
                      ft.Icons.BUSINESS, "#FF9800"),
            stat_card("Pending", str(pending_tasks), ft.Icons.TASK, "#9C27B0"),
            ft.Container(expand=True),
        ], spacing=15)

        def nav_card(title, icon_name, color, on_click):
            return ft.Container(
                width=110, height=95,
                padding=ft.padding.all(10),
                border_radius=10, bgcolor="WHITE",
                shadow=ft.BoxShadow(spread_radius=0.5,
                                    blur_radius=3, color="#00000010"),
                on_click=on_click, ink=True,
                content=ft.Column([
                    ft.Icon(icon_name, size=28, color=color),
                    ft.Text(title, size=11, weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            )

        nav_content = ft.Column([
            ft.Row([
                ft.Container(expand=True),
                nav_card("Employees", ft.Icons.PEOPLE,
                         "#2196F3", self.show_employees),
                nav_card("Depts", ft.Icons.BUSINESS,
                         "#4CAF50", self.show_departments),
                nav_card("Attendance", ft.Icons.ACCESS_TIME,
                         "#FF9800", self.show_attendance),
                nav_card("Leaves", ft.Icons.CALENDAR_MONTH,
                         "#9C27B0", self.show_leaves),
                ft.Container(expand=True),
            ], spacing=12),
            ft.Container(height=12),
            ft.Row([
                ft.Container(expand=True),
                nav_card("Tasks", ft.Icons.TASK, "#009688", self.show_tasks),
                nav_card("Chat", ft.Icons.CHAT, "#FFC107", self.show_chat),
                nav_card("Todo", ft.Icons.CHECKLIST,
                         "#00BCD4", self.show_todo),
                ft.Container(expand=True),
            ], spacing=12),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        nav_section = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            content=ft.Column([
                ft.Text("Quick Navigation", size=15,
                        weight=ft.FontWeight.BOLD, color="#333"),
                ft.Container(height=10),
                nav_content,
            ], spacing=0),
        )

        main_content = ft.Container(
            expand=True, padding=ft.padding.all(20),
            content=ft.Column([
                ft.Text("Quick Stats", size=15,
                        weight=ft.FontWeight.BOLD, color="#333"),
                ft.Container(height=12),
                stats_row,
                ft.Container(height=16),
                nav_section,
            ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )

        return ft.Column([header, main_content], expand=True, spacing=0)

    def logout(self, e):
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))

    def _check_admin_access(self):
        role = ""
        if isinstance(self.user, dict):
            role = str(self.user.get('role', '')).lower()
        else:
            role = str(getattr(self.user, 'role', '')).lower()
        if role != 'admin':
            snack = ft.SnackBar(content=ft.Text(
                "Access Denied: Admin privileges required"), bgcolor="#DC3545")
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
            return False
        return True

    def show_employees(self, e):
        if not self._check_admin_access():
            return
        from screens.employees_screen import show_employees
        show_employees(self._page, self.user)

    def show_departments(self, e):
        if not self._check_admin_access():
            return
        from screens.departments_screen import show_departments
        show_departments(self._page, self.user)

    def show_attendance(self, e):
        if not self._check_admin_access():
            return
        from screens.attendance_screen import show_attendance
        show_attendance(self._page, self.user)

    def show_leaves(self, e):
        if not self._check_admin_access():
            return
        from screens.leaves_screen import show_leaves
        show_leaves(self._page, self.user)

    def show_tasks(self, e):
        if not self._check_admin_access():
            return
        from screens.tasks_screen import show_tasks
        show_tasks(self._page, self.user)

    def show_chat(self, e):
        from screens.chat_screen import ChatScreen
        self._page.clean()
        self._page.add(ChatScreen(self._page, self.user))

    def show_todo(self, e):
        from screens.todo_screen import TodoScreen
        self._page.clean()
        self._page.add(TodoScreen(self._page, self.user))


def show_dashboard(page, user_data=None):
    username = user_data.get("username", "User") if user_data else "User"
    user_id = user_data.get("user_id") if user_data else None

    class UserLike:
        def __init__(self, username, user_id):
            self.username = username
            self.id = user_id
    page.add(DashboardScreen(page, UserLike(username, user_id)))
