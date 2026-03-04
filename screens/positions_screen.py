"""
Vernika HRA - Positions Screen
PostgreSQL/SQLAlchemy based positions management
"""

import flet as ft
from sqlalchemy.orm import Session, joinedload
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Position, Department


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#28A745"
ERROR = "#DC3545"
WARNING = "#FFC107"
BACKGROUND = "#F8F9FA"
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


class PositionsScreen(ft.Container):
    """
    Screen for managing job positions/roles.
    """

    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self._nav_rail_visible = True
        self.content = self._build_content()

    def _build_content(self):
        """Build the UI"""
        # Note: Navigation toggle is disabled for stability
        # The toggle functionality was causing UI issues
        self.nav_toggle_btn = ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="Menu",
            icon_color="WHITE"
        )

        # Add header with Add Position button
        header = self._create_header()
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

    def _create_header(self):
        """Create header with company name and logout"""
        return ft.Container(
            content=ft.Row([
                ft.Container(width=10),
                ft.Icon(ft.Icons.WORK, color="WHITE", size=28),
                ft.Text("Vernika HRA - Positions Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                # Add Position button
                ft.ElevatedButton(
                    "Add Position",
                    icon=ft.Icons.ADD,
                    on_click=self._on_add,
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

    def _on_back(self, e):
        """Go back to dashboard"""
        _safe_navigate_to_home(self._page, self.user)

    def _on_add(self, e):
        """Show add position dialog"""
        self._show_add_dialog()

    def _get_positions(self):
        """Get all positions from PostgreSQL with eager loading"""
        db = get_db_session()
        try:
            positions = db.query(Position).options(joinedload(
                Position.department)).order_by(Position.id).all()
            return positions
        except Exception as e:
            print(f"Error loading positions: {e}")
            return []
        finally:
            db.close()

    def _get_departments(self):
        """Get list of departments from PostgreSQL"""
        db = get_db_session()
        try:
            departments = db.query(Department).filter(
                Department.is_active == True).order_by(Department.name).all()
            return departments
        except Exception as e:
            print(f"Error loading departments: {e}")
            return []
        finally:
            db.close()

    def _build_positions_list(self):
        """Build positions list"""
        positions = self._get_positions()

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
            status_color = SUCCESS if p.is_active else ERROR
            status_text = "Active" if p.is_active else "Inactive"
            salary_range = f"Rs.{p.min_salary or 0:,.0f} - Rs.{p.max_salary or 0:,.0f}" if p.min_salary or p.max_salary else "Not set"

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(p.id))),
                        ft.DataCell(ft.Text(p.code or "")),
                        ft.DataCell(ft.Text(p.title or "")),
                        ft.DataCell(
                            ft.Text(p.department.name if p.department else "No Department")),
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
                                    on_click=lambda e, pos_id=p.id: self._show_edit_dialog(
                                        pos_id),
                                    tooltip="Edit"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ERROR,
                                    on_click=lambda e, pos_id=p.id: self._show_delete_dialog(
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

    def _show_add_dialog(self):
        """Show add position dialog"""
        departments = self._get_departments()

        dept_options = [ft.dropdown.Option(
            key=str(d.id), text=d.name) for d in departments]

        title = ft.TextField(label="Title *", width=280)
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

            db = get_db_session()
            try:
                min_sal = float(min_salary.value) if min_salary.value else 0
                max_sal = float(max_salary.value) if max_salary.value else 0

                # Check if code exists
                existing = db.query(Position).filter(
                    Position.code == code.value.upper()).first()
                if existing:
                    error.value = "Code already exists!"
                    error.visible = True
                    self._page.update()
                    return

                # Create new position
                new_position = Position(
                    title=title.value,
                    code=code.value.upper(),
                    description=description.value or None,
                    department_id=int(
                        department.value) if department.value else None,
                    min_salary=min_sal,
                    max_salary=max_sal,
                    is_active=True
                )
                db.add(new_position)
                db.commit()

                self._close_dialog()
                self._show_success("Position added successfully!")
                self._refresh()
            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Position"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Position Details", size=14,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Row([title, code], spacing=15),
                    description,
                    ft.Container(height=10),
                    ft.Divider(),
                    ft.Text("Department & Salary", size=14,
                            weight=ft.FontWeight.BOLD, color=SUCCESS),
                    ft.Container(height=5),
                    ft.Row([department], spacing=15),
                    ft.Row([min_salary, max_salary], spacing=15),
                    error,
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=520,
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
        db = get_db_session()
        try:
            p = db.query(Position).filter(Position.id == pos_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not p:
            self._show_error("Position not found!")
            return

        departments = self._get_departments()

        dept_options = [ft.dropdown.Option(
            key=str(d.id), text=d.name) for d in departments]

        title = ft.TextField(label="Title", width=300, value=p.title or "")
        code = ft.TextField(label="Code", width=150,
                            value=p.code or "", disabled=True)
        description = ft.TextField(label="Description", width=450, value=p.description or "",
                                   multiline=True, min_lines=2)
        department = ft.Dropdown(width=250, options=dept_options, label="Department",
                                 value=str(p.department_id) if p.department_id else None)
        min_salary = ft.TextField(
            label="Min Salary (Rs.)", width=150, value=str(p.min_salary or 0))
        max_salary = ft.TextField(
            label="Max Salary (Rs.)", width=150, value=str(p.max_salary or 0))
        status_switch = ft.Switch(label="Active", value=bool(p.is_active))

        def update(e):
            db = get_db_session()
            try:
                min_sal = float(min_salary.value) if min_salary.value else 0
                max_sal = float(max_salary.value) if max_salary.value else 0

                db.query(Position).filter(Position.id == pos_id).update({
                    Position.title: title.value,
                    Position.description: description.value or None,
                    Position.department_id: int(department.value) if department.value else None,
                    Position.min_salary: min_sal,
                    Position.max_salary: max_sal,
                    Position.is_active: status_switch.value
                })
                db.commit()

                self._close_dialog()
                self._show_success("Position updated successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        tab_content = ft.Column([
            ft.Text("Position Details", size=14,
                    weight=ft.FontWeight.BOLD, color=PRIMARY),
            ft.Row([
                ft.Container(content=title, width=300),
                ft.Container(content=code, width=150),
            ], spacing=10),
            ft.Container(content=description, width=450),
            ft.Divider(),
            ft.Text("Department & Salary", size=14,
                    weight=ft.FontWeight.BOLD, color=SUCCESS),
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(content=department, width=250),
                        ft.Container(content=min_salary, width=150),
                        ft.Container(content=max_salary, width=150),
                    ],
                    spacing=10,
                ),
            ),
            ft.Divider(),
            status_switch,
            ft.Container(height=20),
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
        db = get_db_session()
        try:
            p = db.query(Position).filter(Position.id == pos_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not p:
            self._show_error("Position not found!")
            return

        def confirm(e):
            db = get_db_session()
            try:
                db.query(Position).filter(Position.id == pos_id).delete()
                db.commit()

                self._close_dialog()
                self._show_success("Position deleted!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Position?", color=ERROR),
            content=ft.Text(f"Delete '{p.title}'?"),
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
