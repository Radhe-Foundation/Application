"""
Vernika HRA - Admin Screen - Fixed
Full functionality with screen access management
"""

import flet as ft
import sqlite3
from utils.screen_access import (
    SCREEN_ACCESS_CONFIG, get_user_screen_access, bulk_set_screen_access,
    get_all_employees_for_access_management
)


class AdminScreen(ft.Container):
    def __init__(self, page, current_user=None):
        super().__init__()
        self._page = page
        self.current_user = current_user or {}
        self.expand = True
        self.bgcolor = "#F5F5F5"

        # Verify admin access
        role = self.current_user.get('role', '').lower(
        ) if isinstance(self.current_user, dict) else ''
        if role != 'admin':
            self._handle_access_denied()
            return

        self._selected_employee_id = None
        self._access_checkboxes = {}
        self.content = self._create_admin_content()

    def _handle_access_denied(self):
        """Handle access denied for non-admin users"""
        snack = ft.SnackBar(content=ft.Text(
            "Access Denied: Admin privileges required"))
        snack.bgcolor = "#DC3545"
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))

    def _create_admin_content(self):
        """Create admin dashboard content"""
        return ft.Container(
            padding=ft.padding.all(20),
            content=ft.Column([
                ft.Text("Admin Dashboard", size=28,
                        weight=ft.FontWeight.BOLD, color="#2E86AB"),
                ft.Container(height=20),
                ft.Row([
                    self._create_stat_card(
                        "Users", "0", ft.Icons.PEOPLE, "#2196F3"),
                    self._create_stat_card(
                        "Active", "0", ft.Icons.CHECK_CIRCLE, "#4CAF50"),
                    self._create_stat_card(
                        "Employees", "0", ft.Icons.BADGE, "#FF9800"),
                ], spacing=20),
                ft.Container(height=30),
                ft.Text("User Management", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                self._get_users_table(),
                ft.Container(height=20),
                ft.Text("Screen Access Management",
                        size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                self._create_screen_access_section(),
            ], scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def _create_stat_card(self, title, value, icon_name, color):
        """Create a statistics card"""
        return ft.Card(
            content=ft.Container(
                padding=ft.padding.all(20),
                width=150,
                content=ft.Column([
                    ft.Icon(icon_name, size=40, color=color),
                    ft.Text(value, size=32, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=14, color="#757575")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=3
        )

    def _get_users_table(self):
        """Get users data table"""
        users = []
        try:
            conn = sqlite3.connect('vernika.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.status, r.name as role_name
                FROM users u
                LEFT JOIN roles r ON u.role_id = r.id
                ORDER BY u.id
            """)
            users = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error loading users: {e}")

        if not users:
            return ft.Container(
                content=ft.Text("No users found"),
                padding=50,
                alignment=ft.alignment.Alignment(0, 0)
            )

        rows = []
        for user in users:
            status_color = "#4CAF50" if user['status'] == 'active' else "#F44336"
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(user['id']))),
                        ft.DataCell(ft.Text(user['username'])),
                        ft.DataCell(ft.Text(user['email'])),
                        ft.DataCell(ft.Text(user['role_name'] or 'N/A')),
                        ft.DataCell(
                            ft.Container(
                                padding=ft.padding.all(5),
                                border_radius=4,
                                bgcolor=status_color,
                                content=ft.Text(
                                    user['status'] or 'unknown', size=11, color="WHITE")
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    on_click=lambda e, u=user: self._edit_user(
                                        u)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color="#F44336",
                                    on_click=lambda e, u=user: self._delete_user(
                                        u)
                                )
                            ])
                        )
                    ]
                )
            )

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=rows,
            expand=True
        )

    def _create_screen_access_section(self):
        """Create screen access management section"""
        # Get employees for dropdown
        employees = get_all_employees_for_access_management()

        employee_options = [
            ft.dropdown.Option(
                key=str(emp['user_id']),
                text=f"{emp['full_name'] or emp['username']} ({emp['role']})"
            )
            for emp in employees
        ]

        if not employee_options:
            employee_options = [ft.dropdown.Option("1", "No employees")]

        # Selected employee dropdown
        self._employee_dropdown = ft.Dropdown(
            label="Select Employee",
            options=employee_options,
            width=400
        )

        # Store on_change handler
        def on_emp_change(e):
            self._on_employee_change(e)

        self._employee_dropdown.on_change = on_emp_change

        return ft.Container(
            padding=ft.padding.all(10),
            bgcolor="#FFFFFF",
            border_radius=10,
            content=ft.Column([
                ft.Row([self._employee_dropdown, ft.Container(expand=True)]),
                ft.Container(height=20),
                self._build_access_checkboxes_container(),
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        "Save Permissions",
                        icon=ft.Icons.SAVE,
                        bgcolor="#2E86AB",
                        color="WHITE",
                        on_click=self._save_access
                    ),
                    ft.TextButton(
                        "Reset to Defaults",
                        icon=ft.Icons.RESTORE,
                        on_click=self._reset_access
                    ),
                ], spacing=10)
            ], spacing=0),
        )

    def _build_access_checkboxes_container(self):
        """Build the checkboxes container for screen access"""
        if not self._access_checkboxes:
            return ft.Container(
                padding=20,
                bgcolor="#F5F5F5",
                border_radius=10,
                content=ft.Text(
                    "Select an employee to manage their screen access", color="#757575"),
                alignment=ft.alignment.Alignment(0, 0)
            )

        checkbox_controls = []
        for screen_key in self._access_checkboxes:
            config = SCREEN_ACCESS_CONFIG.get(screen_key, {})
            desc = config.get('description', '')
            checkbox_controls.append(
                ft.Row([
                    ft.Text(config.get('name', screen_key), width=120),
                    self._access_checkboxes[screen_key],
                    ft.Text(desc, size=11, color="#757575"),
                ], spacing=10)
            )

        return ft.Container(
            padding=20,
            bgcolor="#FFFFFF",
            border_radius=10,
            content=ft.Column(checkbox_controls, spacing=10,
                              scroll=ft.ScrollMode.AUTO),
        )

    def _on_employee_change(self, e):
        """Handle employee selection change"""
        user_id = self._employee_dropdown.value

        if not user_id:
            self._access_checkboxes = {}
            return

        # Create checkboxes for selected employee
        access = get_user_screen_access(int(user_id))
        self._access_checkboxes = {}

        for screen_key, config in SCREEN_ACCESS_CONFIG.items():
            checkbox = ft.Checkbox(value=access.get(screen_key, False))
            self._access_checkboxes[screen_key] = checkbox

        self._selected_employee_id = int(user_id)
        self._page.update()

    def _save_access(self, e):
        """Save screen access settings"""
        user_id = self._selected_employee_id or self._employee_dropdown.value

        if not user_id:
            self._show_message("Please select an employee first", "error")
            return

        # Collect all access settings
        access_dict = {}
        for screen_key, checkbox in self._access_checkboxes.items():
            access_dict[screen_key] = checkbox.value

        # Get admin user ID
        admin_user_id = None
        if self.current_user and isinstance(self.current_user, dict):
            admin_user_id = self.current_user.get('id')

        # Save to database
        success = bulk_set_screen_access(
            int(user_id), access_dict, granted_by=admin_user_id)

        if success:
            self._show_message("Screen access saved successfully!", "success")
        else:
            self._show_message("Error saving permissions", "error")

    def _reset_access(self, e):
        """Reset access to defaults"""
        from utils.screen_access import reset_to_defaults

        user_id = self._selected_employee_id or self._employee_dropdown.value

        if not user_id:
            self._show_message("Please select an employee first", "error")
            return

        reset_to_defaults(int(user_id))

        # Refresh checkboxes
        access = get_user_screen_access(int(user_id))
        for screen_key, checkbox in self._access_checkboxes.items():
            checkbox.value = access.get(screen_key, False)

        self._show_message("Reset to default permissions", "success")
        self._page.update()

    def _show_message(self, message, type="info"):
        """Show a snackbar message"""
        bgcolor = "#4CAF50" if type == "success" else "#F44336" if type == "error" else "#2196F3"
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _edit_user(self, user):
        """Edit user"""
        dlg = ft.AlertDialog(
            title=ft.Text(f"Edit User: {user['username']}"),
            content=ft.Column([
                ft.TextField(label="Username",
                             value=user['username'], width=300),
                ft.TextField(label="Email", value=user['email'], width=300),
                ft.Dropdown(
                    label="Status",
                    value=user['status'],
                    options=[
                        ft.dropdown.Option("active", "Active"),
                        ft.dropdown.Option("inactive", "Inactive"),
                    ],
                    width=300
                )
            ], tight=True),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog(dlg)),
                ft.ElevatedButton("Save", on_click=lambda e: self._save_user_changes(
                    user, dlg), bgcolor="#2E86AB", color="WHITE")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _save_user_changes(self, user, dlg):
        """Save user changes"""
        try:
            conn = sqlite3.connect('vernika.db')
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status='active' WHERE id=?", (user['id'],))
            conn.commit()
            conn.close()
            dlg.open = False
            self._show_message(f"User updated!", "success")
            self._page.update()
        except Exception as ex:
            self._show_message(f"Error: {str(ex)}", "error")

    def _delete_user(self, user):
        """Delete user"""
        dlg = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(
                f"Delete user '{user['username']}'? This cannot be undone."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog(dlg)),
                ft.ElevatedButton("Delete", on_click=lambda e: self._confirm_delete_user(
                    user, dlg), bgcolor="#F44336", color="WHITE")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _confirm_delete_user(self, user, dlg):
        """Confirm and delete user"""
        try:
            conn = sqlite3.connect('vernika.db')
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM employees WHERE user_id=?", (user['id'],))
            cursor.execute("DELETE FROM users WHERE id=?", (user['id'],))
            conn.commit()
            conn.close()
            dlg.open = False
            self._show_message(f"User deleted!", "success")
            self._page.update()
        except Exception as ex:
            self._show_message(f"Error: {str(ex)}", "error")

    def _close_dialog(self, dlg):
        """Close dialog"""
        dlg.open = False
        self._page.update()


def show_admin(page, user):
    """Helper to show admin screen"""
    page.clean()
    page.add(AdminScreen(page, user))
