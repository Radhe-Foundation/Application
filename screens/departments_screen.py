"""
Vernika HRA - Enhanced Departments Screen - Fixed for Flet 0.80+
"""

import flet as ft
import sqlite3


class DepartmentsScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = "#F5F5F5"
        self.content = self._build_content()

    def _get_db(self):
        conn = sqlite3.connect('vernika.db')
        conn.row_factory = sqlite3.Row
        return conn

    def _build_content(self):
        header = ft.Container(
            padding=15,
            bgcolor="#4CAF50",
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self.on_back
                ),
                ft.Text("Department Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Add Department",
                    icon=ft.Icons.ADD,
                    on_click=self.on_add,
                    style=ft.ButtonStyle(bgcolor="#388E3C", color="WHITE")
                ),
            ])
        )

        department_list = self._build_department_list()

        content = ft.Column([
            header,
            ft.Container(
                padding=20,
                content=department_list,
                expand=True
            )
        ], expand=True)

        return content

    def on_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def on_add(self, e):
        self._show_add_dialog()

    def _build_department_list(self):
        conn = None
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            # Only query columns that exist in the database
            cursor.execute("""
                SELECT d.id, d.name, d.code, d.description,
                       d.head_id, d.is_active, d.created_at,
                       e.first_name || ' ' || e.last_name as head_name
                FROM departments d
                LEFT JOIN employees e ON d.head_id = e.id
                ORDER BY d.id
            """)
            departments = cursor.fetchall()
        except Exception as e:
            print(f"Error loading departments: {e}")
            departments = []
        finally:
            if conn:
                conn.close()

        if not departments:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.BUSINESS, size=64, color="#BDBDBD"),
                    ft.Text("No departments. Add one!",
                            size=14, color="#757575"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Add First Department",
                        on_click=self.on_add,
                        style=ft.ButtonStyle(bgcolor="#4CAF50", color="WHITE")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        rows = []
        for d in departments:
            status_color = "#4CAF50" if d['is_active'] else "#F44336"
            status_text = "Active" if d['is_active'] else "Inactive"

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(d['id']))),
                        ft.DataCell(ft.Text(d['name'] or "")),
                        ft.DataCell(ft.Text(d['code'] or "")),
                        ft.DataCell(ft.Text(d['head_name'] or "Not Assigned")),
                        ft.DataCell(ft.Text(d['description'] or "-")),
                        ft.DataCell(
                            ft.Container(
                                ft.Text(status_text, size=11, color="WHITE"),
                                bgcolor=status_color,
                                padding=ft.padding.all(5),
                                border_radius=4
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT, icon_color="#1976D2",
                                    on_click=lambda e, dept_id=d['id']: self._show_edit_dialog(
                                        dept_id),
                                    tooltip="Edit"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE, icon_color="#D32F2F",
                                    on_click=lambda e, dept_id=d['id']: self._show_delete_dialog(
                                        dept_id),
                                    tooltip="Delete"
                                ),
                            ], spacing=2)
                        ),
                    ]
                )
            )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(label=ft.Text("ID")),
                ft.DataColumn(label=ft.Text("Name")),
                ft.DataColumn(label=ft.Text("Code")),
                ft.DataColumn(label=ft.Text("Head/Manager")),
                ft.DataColumn(label=ft.Text("Description")),
                ft.DataColumn(label=ft.Text("Status")),
                ft.DataColumn(label=ft.Text("Actions")),
            ],
            rows=rows,
            expand=True,
        )

        return ft.Container(content=table, expand=True)

    def _get_employees(self):
        """Get list of employees for dropdown"""
        conn = None
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, first_name || ' ' || last_name as name FROM employees ORDER BY first_name")
            employees = cursor.fetchall()
            return employees
        except Exception as e:
            print(f"Error loading employees: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _get_departments(self):
        """Get list of departments for parent dropdown"""
        conn = None
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM departments ORDER BY name")
            departments = cursor.fetchall()
            return departments
        except Exception as e:
            print(f"Error loading departments: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _show_add_dialog(self):
        employees = self._get_employees()
        # Departments for parent dropdown removed (column doesn't exist)

        # Basic Info
        name = ft.TextField(label="Name *", width=300)
        code = ft.TextField(label="Code *", width=150)
        desc = ft.TextField(label="Description", width=500, multiline=True)

        # Head/Manager Assignment
        emp_options = [ft.dropdown.Option(
            key=str(e['id']), text=e['name']) for e in employees]
        head_dropdown = ft.Dropdown(
            width=250, options=emp_options, label="Department Head/Manager")

        # Removed: Parent Department, Budget, Location, Contact Info (columns don't exist)

        error = ft.Text("", color="#F44336", size=12, visible=False)

        def save(e):
            if not name.value or not code.value:
                error.value = "Name and Code required!"
                error.visible = True
                self._page.update()
                return
            conn = None
            try:
                conn = self._get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM departments WHERE code=?", (code.value.upper(),))
                if cursor.fetchone():
                    error.value = "Code already exists!"
                    error.visible = True
                    self._page.update()
                    return

                cursor.execute("""INSERT INTO departments 
                    (name, code, description, head_id, is_active) 
                    VALUES (?, ?, ?, ?, 1)""",
                               (name.value, code.value.upper(), desc.value or None,
                                int(head_dropdown.value) if head_dropdown.value else None))
                conn.commit()
                self._close_dialog()
                self._show_success("Department added successfully!")
                self._refresh()
            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()
            finally:
                if conn:
                    conn.close()

        # Build form content with scroll support
        tab_content = ft.Column([
            ft.Text("Basic Information", size=14,
                    weight=ft.FontWeight.BOLD, color="#2E86AB"),
            ft.Row([name, code], spacing=10),
            desc,
            ft.Divider(),
            ft.Text("Organization", size=14,
                    weight=ft.FontWeight.BOLD, color="#9C27B0"),
            head_dropdown,
            error,
            ft.Container(height=20),  # Extra space at bottom
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Department"),
            content=ft.Container(
                content=tab_content,
                width=550,
                height=350,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save, style=ft.ButtonStyle(
                    bgcolor="#4CAF50", color="WHITE"))
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_edit_dialog(self, dept_id):
        conn = None
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments WHERE id=?", (dept_id,))
            d = cursor.fetchone()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not d:
            self._show_error("Not found!")
            return

        employees = self._get_employees()

        # Basic Info
        name = ft.TextField(label="Name *", width=300, value=d['name'] or "")
        code = ft.TextField(label="Code *", width=150,
                            value=d['code'] or "", disabled=True)
        desc = ft.TextField(label="Description", width=500,
                            value=d['description'] or "", multiline=True)

        # Head/Manager Assignment
        emp_options = [ft.dropdown.Option(
            key=str(e['id']), text=e['name']) for e in employees]
        head_dropdown = ft.Dropdown(width=250, options=emp_options, label="Department Head/Manager",
                                    value=str(d['head_id']) if d['head_id'] else None)

        # Status toggle
        is_active = d['is_active'] if 'is_active' in d.keys() else True
        status_switch = ft.Switch(label="Active", value=bool(is_active))

        # Removed fields that don't exist in database:
        # - parent_dept_id, budget, location, contact_email, contact_phone

        def update(e):
            conn = None
            try:
                conn = self._get_db()
                cursor = conn.cursor()
                cursor.execute("""UPDATE departments SET 
                    name=?, description=?, head_id=?, is_active=? 
                    WHERE id=?""",
                               (name.value, desc.value or None,
                                int(head_dropdown.value) if head_dropdown.value else None,
                                status_switch.value, dept_id))
                conn.commit()
                self._close_dialog()
                self._show_success("Department updated successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                if conn:
                    conn.close()

        tab_content = ft.Column([
            ft.Text("Basic Information", size=14,
                    weight=ft.FontWeight.BOLD, color="#2E86AB"),
            ft.Row([name, code], spacing=10),
            desc,
            ft.Divider(),
            ft.Text("Organization", size=14,
                    weight=ft.FontWeight.BOLD, color="#9C27B0"),
            head_dropdown,
            ft.Divider(),
            status_switch,
            ft.Container(height=20),  # Extra space at bottom
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Department"),
            content=ft.Container(
                content=tab_content,
                width=550,
                height=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Update", on_click=update, style=ft.ButtonStyle(
                    bgcolor="#1976D2", color="WHITE"))
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_employees_dialog(self, dept_id):
        """Show employees in this department"""
        conn = None
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM departments WHERE id=?", (dept_id,))
            dept = cursor.fetchone()

            if not dept:
                self._show_error("Department not found!")
                return

            cursor.execute("""
                SELECT id, employee_code, first_name, last_name, email, position_id,
                       (SELECT title FROM positions WHERE id = position_id) as position_title
                FROM employees WHERE department_id=? ORDER BY first_name
            """, (dept_id,))
            employees = cursor.fetchall()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not employees:
            content = ft.Column([
                ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=48, color="#BDBDBD"),
                ft.Text(
                    f"No employees in {dept['name']}", size=14, color="#757575"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            rows = []
            for emp in employees:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(emp['id']))),
                            ft.DataCell(ft.Text(emp['employee_code'] or "-")),
                            ft.DataCell(
                                ft.Text(f"{emp['first_name'] or ''} {emp['last_name'] or ''}")),
                            ft.DataCell(ft.Text(emp['email'] or "-")),
                            ft.DataCell(ft.Text(emp['position_title'] or "-")),
                        ]
                    )
                )
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(label=ft.Text("ID")),
                    ft.DataColumn(label=ft.Text("Code")),
                    ft.DataColumn(label=ft.Text("Name")),
                    ft.DataColumn(label=ft.Text("Email")),
                    ft.DataColumn(label=ft.Text("Position")),
                ],
                rows=rows,
            )
            content = ft.Container(content=table, expand=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Employees - {dept['name']}"),
            content=ft.Container(content=content, height=350, width=600),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_delete_dialog(self, dept_id):
        conn = None
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM departments WHERE id=?", (dept_id,))
            d = cursor.fetchone()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not d:
            self._show_error("Not found!")
            return

        def confirm(e):
            conn = None
            try:
                conn = self._get_db()
                cursor = conn.cursor()

                # Check if any employees belong to this department
                cursor.execute(
                    "SELECT COUNT(*) FROM employees WHERE department_id=?", (dept_id,))
                employee_count = cursor.fetchone()[0]
                if employee_count > 0:
                    self._show_error(
                        f"Cannot delete! {employee_count} employees are assigned to this department.")
                    return

                cursor.execute(
                    "DELETE FROM departments WHERE id=?", (dept_id,))
                conn.commit()
                self._close_dialog()
                self._show_success("Deleted!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                if conn:
                    conn.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete?", color="#F44336"),
            content=ft.Text(f"Delete '{d['name']}'?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm, style=ft.ButtonStyle(
                    bgcolor="#F44336", color="WHITE"))
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self):
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _refresh(self):
        self.content = self._build_content()
        self._page.update()

    def _show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#4CAF50")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#F44336")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_departments(page, user):
    page.clean()
    page.add(DepartmentsScreen(page, user))
