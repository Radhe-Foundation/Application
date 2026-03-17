"""
RadheFoundation HRA - Enhanced Departments Screen
PostgreSQL/SQLAlchemy based departments management
"""

import flet as ft
from sqlalchemy.orm import Session, joinedload
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Department, Employee


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"
BACKGROUND = "#F5F5F5"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"


def _safe_navigate_to_home(page, user=None):
    """Safely navigate to home screen"""
    try:
        from core.navigation import navigate_to_home
        navigate_to_home(page, user)
    except ImportError:
        # Fallback navigation
        try:
            from screens.admin_screen import AdminScreen
            from screens.employee_screen import EmployeeScreen
            page.clean()
            if user and isinstance(user, dict):
                role = user.get('role', 'employee').lower()
            elif user and hasattr(user, 'role'):
                role = user.role.name.lower() if user.role else 'employee'
            else:
                role = 'employee'

            if role == 'admin':
                page.add(AdminScreen(page, user))
            else:
                page.add(EmployeeScreen(page, user))
        except Exception as e:
            print(f"Navigation error: {e}")
            from screens.login_screen import LoginScreen
            page.clean()
            page.add(LoginScreen(page))


class DepartmentsScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self._nav_rail_visible = True
        self.content = self._build_content()

    def _build_content(self):
        # Note: Header is now handled by admin wrapper (_wrap_with_admin_header)
        # This screen provides just the content without duplicate header elements
        # But we need a header within the screen for standalone viewing
        header = self._create_header()
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

    def _create_header(self):
        """Create header with Add Department button"""
        return ft.Container(
            content=ft.Row([
                ft.Container(width=10),
                ft.Icon(ft.Icons.BUSINESS, color="WHITE", size=28),
                ft.Text("RadheFoundation HRA - Departments Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                # Add Department button in header
                ft.ElevatedButton(
                    "Add Department",
                    icon=ft.Icons.ADD_BUSINESS,
                    on_click=self.on_add,
                    style=ft.ButtonStyle(
                        bgcolor="WHITE",
                        color=PRIMARY,
                    ),
                ),
                ft.Container(width=10),
                ft.Text(
                    f"Welcome, {self.user.get('username', 'User') if isinstance(self.user, dict) else 'User'}",
                    size=14,
                    color="WHITE"
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    tooltip="Logout",
                    on_click=self._handle_logout,
                    icon_color="WHITE"
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=PRIMARY,
        )

    def _handle_logout(self, e):
        """Handle logout"""
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))

    def _get_departments(self, limit: int = 50):
        """Get departments from PostgreSQL with head names and pagination"""
        db = get_db_session()
        try:
            # Get all employees first for head lookup (with limit)
            all_employees = {e.id: e for e in db.query(
                Employee).limit(100).all()}

            # Get departments with limit for performance
            departments = db.query(Department).order_by(
                Department.id).limit(limit).all()

            # Attach head names to departments
            result = []
            for d in departments:
                if d.head_id and d.head_id in all_employees:
                    head = all_employees[d.head_id]
                    d._head_name = f"{head.first_name or ''} {head.last_name or ''}".strip(
                    )
                else:
                    d._head_name = "Not Assigned"
                result.append(d)

            return result
        except Exception as e:
            print(f"Error loading departments: {e}")
            return []
        finally:
            db.close()

    def _get_employees(self):
        """Get list of employees for dropdown"""
        db = get_db_session()
        try:
            employees = db.query(Employee).filter(
                Employee.is_active == True).order_by(Employee.first_name).all()
            return employees
        except Exception as e:
            print(f"Error loading employees: {e}")
            return []
        finally:
            db.close()

    def _build_department_list(self):
        """Build department list"""
        departments = self._get_departments()

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
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        rows = []
        for d in departments:
            status_color = SUCCESS if d.is_active else ERROR
            status_text = "Active" if d.is_active else "Inactive"

            # Use pre-loaded head name
            head_name = getattr(d, '_head_name', "Not Assigned")

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(d.id))),
                        ft.DataCell(ft.Text(d.name or "")),
                        ft.DataCell(ft.Text(d.code or "")),
                        ft.DataCell(ft.Text(head_name)),
                        ft.DataCell(ft.Text(d.description or "-")),
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
                                    on_click=lambda e, dept_id=d.id: self._show_edit_dialog(
                                        dept_id),
                                    tooltip="Edit"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE, icon_color="#D32F2F",
                                    on_click=lambda e, dept_id=d.id: self._show_delete_dialog(
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

    def on_add(self, e):
        self._show_add_dialog()

    def _show_add_dialog(self):
        """Show add department dialog"""
        employees = self._get_employees()

        # Basic Info
        name = ft.TextField(label="Name *", width=280)
        code = ft.TextField(label="Code *", width=150)
        desc = ft.TextField(label="Description", width=450, multiline=True)

        # Head/Manager Assignment
        emp_options = [ft.dropdown.Option(
            key=str(e.id), text=f"{e.first_name or ''} {e.last_name or ''}".strip()) for e in employees]
        head_dropdown = ft.Dropdown(
            width=250, options=emp_options, label="Department Head/Manager")

        error = ft.Text("", color="#F44336", size=12, visible=False)

        def save(e):
            if not name.value or not code.value:
                error.value = "Name and Code required!"
                error.visible = True
                self._page.update()
                return

            db = get_db_session()
            try:
                # Check if code exists
                existing = db.query(Department).filter(
                    Department.code == code.value.upper()).first()
                if existing:
                    error.value = "Code already exists!"
                    error.visible = True
                    self._page.update()
                    return

                # Create new department
                new_dept = Department(
                    name=name.value,
                    code=code.value.upper(),
                    description=desc.value or None,
                    head_id=int(
                        head_dropdown.value) if head_dropdown.value else None,
                    is_active=True
                )
                db.add(new_dept)
                db.commit()

                # Invalidate dashboard stats cache
                try:
                    from database.operations import _invalidate_cache
                    _invalidate_cache("dashboard_")
                except Exception as cache_err:
                    print(f"Cache invalidation error: {cache_err}")

                self._close_dialog()
                self._show_success("Department added successfully!")
                self._refresh()
            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()
            finally:
                db.close()

        # Build form with proper alignment
        tab_content = ft.Column([
            ft.Text("Basic Information", size=14,
                    weight=ft.FontWeight.BOLD, color=PRIMARY),
            ft.Row([
                ft.Container(content=name, width=280),
                ft.Container(content=code, width=150),
            ], spacing=10),
            ft.Container(content=desc, width=450),
            ft.Divider(),
            ft.Text("Organization", size=14,
                    weight=ft.FontWeight.BOLD, color="#9C27B0"),
            ft.Container(content=head_dropdown, width=250),
            error,
            ft.Container(height=20),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Department"),
            content=ft.Container(
                content=tab_content,
                width=500,
                height=350,
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

    def _show_edit_dialog(self, dept_id):
        """Show edit department dialog"""
        db = get_db_session()
        try:
            d = db.query(Department).filter(Department.id == dept_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not d:
            self._show_error("Not found!")
            return

        employees = self._get_employees()

        # Basic Info
        name = ft.TextField(label="Name *", width=300, value=d.name or "")
        code = ft.TextField(label="Code *", width=150,
                            value=d.code or "", disabled=True)
        desc = ft.TextField(label="Description", width=500,
                            value=d.description or "", multiline=True)

        # Head/Manager Assignment
        emp_options = [ft.dropdown.Option(
            key=str(e.id), text=f"{e.first_name or ''} {e.last_name or ''}".strip()) for e in employees]
        head_dropdown = ft.Dropdown(width=250, options=emp_options, label="Department Head/Manager",
                                    value=str(d.head_id) if d.head_id else None)

        # Status toggle
        status_switch = ft.Switch(label="Active", value=bool(d.is_active))

        def update(e):
            db = get_db_session()
            try:
                db.query(Department).filter(Department.id == dept_id).update({
                    Department.name: name.value,
                    Department.description: desc.value or None,
                    Department.head_id: int(head_dropdown.value) if head_dropdown.value else None,
                    Department.is_active: status_switch.value
                })
                db.commit()

                self._close_dialog()
                self._show_success("Department updated successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        tab_content = ft.Column([
            ft.Text("Basic Information", size=14,
                    weight=ft.FontWeight.BOLD, color=PRIMARY),
            ft.Row([name, code], spacing=10),
            desc,
            ft.Divider(),
            ft.Text("Organization", size=14,
                    weight=ft.FontWeight.BOLD, color="#9C27B0"),
            head_dropdown,
            ft.Divider(),
            status_switch,
            ft.Container(height=20),
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

    def _show_delete_dialog(self, dept_id):
        """Show delete confirmation dialog"""
        db = get_db_session()
        try:
            d = db.query(Department).filter(Department.id == dept_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not d:
            self._show_error("Not found!")
            return

        def confirm(e):
            db = get_db_session()
            try:
                # Check if any employees belong to this department
                employee_count = db.query(Employee).filter(
                    Employee.department_id == dept_id).count()
                if employee_count > 0:
                    self._show_error(
                        f"Cannot delete! {employee_count} employees are assigned to this department.")
                    return

                db.query(Department).filter(Department.id == dept_id).delete()
                db.commit()

                # Invalidate dashboard stats cache
                try:
                    from database.operations import _invalidate_cache
                    _invalidate_cache("dashboard_")
                except Exception as cache_err:
                    print(f"Cache invalidation error: {cache_err}")

                self._close_dialog()
                self._show_success("Deleted!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete?", color="#F44336"),
            content=ft.Text(f"Delete '{d.name}'?"),
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
