"""
Vernika HRA - Positions Screen
Industry-Level Human Resource Management System

This module provides the positions/roles management screen.
Fixed for Flet 0.25+
"""

import flet as ft
import sqlite3


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#28A745"
ERROR = "#DC3545"
WARNING = "#FFC107"
BACKGROUND = "#F8F9FA"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"


class PositionsScreen(ft.Container):
    """
    Screen for managing job positions/roles.
    """

    def __init__(self, page, user):
        """
        Initialize positions screen.

        Args:
            page: Flet page object
            user: Current user object
        """
        super().__init__()
        self._page = page
        self._user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.content = self._build_content()

    def _get_db(self):
        """Get database connection"""
        conn = sqlite3.connect('vernika.db')
        conn.row_factory = sqlite3.Row
        return conn

    def _build_content(self):
        """Build the UI"""
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self._on_back
                ),
                ft.Text("Positions Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Add Position",
                    icon=ft.Icons.ADD,
                    on_click=self._on_add,
                    style=ft.ButtonStyle(bgcolor="#1976D2", color="WHITE")
                ),
            ])
        )

        positions_list = self._build_positions_list()

        content = ft.Column([
            header,
            ft.Container(
                padding=20,
                content=positions_list,
                expand=True
            )
        ], expand=True)

        return content

    def _on_back(self, e):
        """Go back to dashboard"""
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self._user)

    def _on_add(self, e):
        """Show add position dialog"""
        self._show_add_dialog()

    def _build_positions_list(self):
        """Build positions list"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.title, p.code, p.description, p.min_salary, p.max_salary,
                       p.is_active, d.name as department_name
                FROM positions p
                LEFT JOIN departments d ON p.department_id = d.id
                ORDER BY p.id
            """)
            positions = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error loading positions: {e}")
            positions = []

        if not positions:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.WORK, size=64, color="#BDBDBD"),
                    ft.Text("No positions. Add one!",
                            size=14, color=TEXT_SECONDARY),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Add First Position",
                        on_click=self._on_add,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        rows = []
        for p in positions:
            status_color = SUCCESS if p['is_active'] else ERROR
            status_text = "Active" if p['is_active'] else "Inactive"
            salary_range = f"Rs.{p['min_salary'] or 0:,.0f} - Rs.{p['max_salary'] or 0:,.0f}" if p['min_salary'] or p['max_salary'] else "Not set"

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(p['id']))),
                        ft.DataCell(ft.Text(p['code'] or "")),
                        ft.DataCell(ft.Text(p['title'] or "")),
                        ft.DataCell(
                            ft.Text(p['department_name'] or "No Department")),
                        ft.DataCell(ft.Text(salary_range)),
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
                                    icon=ft.Icons.EDIT,
                                    icon_color="#1976D2",
                                    on_click=lambda e, pos_id=p['id']: self._show_edit_dialog(
                                        pos_id),
                                    tooltip="Edit"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ERROR,
                                    on_click=lambda e, pos_id=p['id']: self._show_delete_dialog(
                                        pos_id),
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
                ft.DataColumn(label=ft.Text("Code")),
                ft.DataColumn(label=ft.Text("Title")),
                ft.DataColumn(label=ft.Text("Department")),
                ft.DataColumn(label=ft.Text("Salary Range")),
                ft.DataColumn(label=ft.Text("Status")),
                ft.DataColumn(label=ft.Text("Actions")),
            ],
            rows=rows,
            expand=True,
        )

        return ft.Container(content=table, expand=True)

    def _get_departments(self):
        """Get list of departments for dropdown"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM departments ORDER BY name")
            departments = cursor.fetchall()
            conn.close()
            return departments
        except Exception as e:
            print(f"Error loading departments: {e}")
            return []

    def _show_add_dialog(self):
        """Show add position dialog"""
        departments = self._get_departments()

        dept_options = [ft.dropdown.Option(
            key=str(d['id']), text=d['name']) for d in departments]

        title = ft.TextField(label="Title *", width=300)
        code = ft.TextField(label="Code *", width=150)
        description = ft.TextField(
            label="Description", width=450, multiline=True, min_lines=2)
        department = ft.Dropdown(
            width=250, options=dept_options, label="Department")
        min_salary = ft.TextField(
            label="Min Salary (Rs.)", width=150, value="0")
        max_salary = ft.TextField(
            label="Max Salary (Rs.)", width=150, value="0")
        error = ft.Text("", color=ERROR, size=12, visible=False)

        def save(e):
            if not title.value or not code.value:
                error.value = "Title and Code are required!"
                error.visible = True
                self._page.update()
                return

            try:
                min_sal = float(min_salary.value) if min_salary.value else 0
                max_sal = float(max_salary.value) if max_salary.value else 0

                conn = self._get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM positions WHERE code=?", (code.value.upper(),))
                if cursor.fetchone():
                    error.value = "Code already exists!"
                    error.visible = True
                    conn.close()
                    self._page.update()
                    return

                cursor.execute("""INSERT INTO positions 
                    (title, code, description, department_id, min_salary, max_salary, is_active) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                               (title.value, code.value.upper(), description.value or None,
                                int(department.value) if department.value else None,
                                min_sal, max_sal, True))
                conn.commit()
                conn.close()

                self._close_dialog()
                self._show_success("Position added successfully!")
                self._refresh()
            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()

        # Build form content with scroll support
        tab_content = ft.Column([
            ft.Text("Position Details", size=14,
                    weight=ft.FontWeight.BOLD, color=PRIMARY),
            ft.Row([title, code], spacing=10),
            description,
            ft.Divider(),
            ft.Text("Department & Salary", size=14,
                    weight=ft.FontWeight.BOLD, color=SUCCESS),
            ft.Row([department, min_salary, max_salary], spacing=10),
            error,
            ft.Container(height=20),  # Extra space at bottom
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Position"),
            content=ft.Container(
                content=tab_content,
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="WHITE"))
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_edit_dialog(self, pos_id):
        """Show edit position dialog"""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM positions WHERE id=?", (pos_id,))
        p = cursor.fetchone()
        conn.close()

        if not p:
            self._show_error("Position not found!")
            return

        departments = self._get_departments()

        dept_options = [ft.dropdown.Option(
            key=str(d['id']), text=d['name']) for d in departments]

        title = ft.TextField(label="Title", width=300, value=p['title'] or "")
        code = ft.TextField(label="Code", width=150,
                            value=p['code'] or "", disabled=True)
        description = ft.TextField(label="Description", width=450, value=p['description'] or "",
                                   multiline=True, min_lines=2)
        department = ft.Dropdown(width=250, options=dept_options, label="Department",
                                 value=str(p['department_id']) if p['department_id'] else None)
        min_salary = ft.TextField(
            label="Min Salary (Rs.)", width=150, value=str(p['min_salary'] or 0))
        max_salary = ft.TextField(
            label="Max Salary (Rs.)", width=150, value=str(p['max_salary'] or 0))
        status_switch = ft.Switch(label="Active", value=bool(p['is_active']))

        def update(e):
            try:
                min_sal = float(min_salary.value) if min_salary.value else 0
                max_sal = float(max_salary.value) if max_salary.value else 0

                conn = self._get_db()
                cursor = conn.cursor()
                cursor.execute("""UPDATE positions SET 
                    title=?, description=?, department_id=?, min_salary=?, max_salary=?, is_active=? 
                    WHERE id=?""",
                               (title.value, description.value or None,
                                int(department.value) if department.value else None,
                                min_sal, max_sal, status_switch.value, pos_id))
                conn.commit()
                conn.close()

                self._close_dialog()
                self._show_success("Position updated successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))

        tab_content = ft.Column([
            ft.Text("Position Details", size=14,
                    weight=ft.FontWeight.BOLD, color=PRIMARY),
            ft.Row([title, code], spacing=10),
            description,
            ft.Divider(),
            ft.Text("Department & Salary", size=14,
                    weight=ft.FontWeight.BOLD, color=SUCCESS),
            ft.Row([department, min_salary, max_salary], spacing=10),
            ft.Divider(),
            status_switch,
            ft.Container(height=20),  # Extra space at bottom
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Position"),
            content=ft.Container(
                content=tab_content,
                width=500,
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

    def _show_delete_dialog(self, pos_id):
        """Show delete confirmation dialog"""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM positions WHERE id=?", (pos_id,))
        p = cursor.fetchone()
        conn.close()

        if not p:
            self._show_error("Position not found!")
            return

        def confirm(e):
            try:
                conn = self._get_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM positions WHERE id=?", (pos_id,))
                conn.commit()
                conn.close()

                self._close_dialog()
                self._show_success("Position deleted!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Position?", color=ERROR),
            content=ft.Text(f"Delete '{p['title']}'?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm, style=ft.ButtonStyle(
                    bgcolor=ERROR, color="WHITE"))
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self):
        """Close all open dialogs"""
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _refresh(self):
        """Refresh the positions list"""
        self.content = self._build_content()
        self._page.update()

    def _show_success(self, msg):
        """Show success message"""
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        """Show error message"""
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=ERROR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_positions(page, user):
    """Helper function to show positions screen"""
    page.clean()
    page.add(PositionsScreen(page, user))
