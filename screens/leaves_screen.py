"""
Vernika HRA - Leaves Management Screen - Fixed for Flet 0.80+
Updated with view_mode support: admin (manage all) or employee (self only)
"""

import flet as ft
from datetime import datetime, date
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import LeaveRequest, Employee, LeaveStatus, LeaveTypeConfig, LeaveBalance
from database.operations import (
    get_all_employees, get_leave_requests, get_leave_type_configs,
    get_employee_by_id, create_leave_request, approve_leave_request,
    reject_leave_request, get_employee_leave_balance, get_user_by_id,
    get_employee_by_user_id
)
from components.forms import DatePickerField


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


class LeavesScreen(ft.Container):
    def __init__(self, page, user, view_mode="admin"):
        """
        LeavesScreen constructor.

        Args:
            page: Flet page object
            user: Current user dictionary
            view_mode: "admin" for admin view (manage all), "employee" for employee view (self only)
        """
        super().__init__()
        self._page = page
        self.user = user
        self.view_mode = view_mode
        self.expand = True
        self.bgcolor = "#F5F5F5"

        # Get current user ID and their linked employee ID
        self.user_id = None
        self.employee_id = None
        if isinstance(user, dict):
            self.user_id = user.get('id')
            # Try to get the linked employee
            if self.user_id:
                try:
                    db = get_db_session()
                    emp = get_employee_by_user_id(db, self.user_id)
                    if emp:
                        self.employee_id = int(emp.id)
                    db.close()
                except Exception as e:
                    print(f"Error getting employee ID: {e}")

        self.content = self._build_content()

        # Set current screen for keyboard shortcuts
        try:
            from core.keyboard_shortcuts_v2 import set_current_screen
            set_current_screen("leaves")
        except Exception as e:
            print(f"[Leaves] Error setting keyboard screen: {e}")

        # Initialize notifications (no test notification on load)
        try:
            from utils.notification_manager import get_notification_manager
            self._notification_manager = get_notification_manager()
        except Exception as e:
            print(f"[Leaves] Error initializing notifications: {e}")
            self._notification_manager = None

    def _build_content(self):
        # Header title based on view mode
        title = "Leave Management" if self.view_mode == "admin" else "My Time Off"

        header = ft.Container(
            padding=15,
            bgcolor="#9C27B0" if self.view_mode == "admin" else "#009688",
            content=ft.Row([
                ft.Text(title, size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Apply Leave",
                    icon=ft.Icons.ADD,
                    on_click=self.on_add,
                    style=ft.ButtonStyle(bgcolor="#7B1FA2", color="WHITE")
                ),
            ])
        )

        # Load leave requests based on view mode
        requests_list = []
        try:
            session = get_db_session()
            leave_requests = get_leave_requests(session, limit=100)

            for lr in leave_requests:
                # In employee mode, only show current user's requests
                if self.view_mode == "employee" and lr.employee_id != self.employee_id:
                    continue

                # Get employee name
                employee = get_employee_by_id(session, lr.employee_id)
                emp_name = f"{employee.first_name} {employee.last_name}" if employee else "Unknown"

                # Safely extract values from SQLAlchemy model
                req_id = int(lr.id) if lr.id else 0
                start_date = str(lr.start_date) if lr.start_date else "-"
                end_date = str(lr.end_date) if lr.end_date else "-"
                days_requested = int(
                    lr.days_requested) if lr.days_requested else 0
                status_val = str(lr.status.value) if hasattr(
                    lr.status, 'value') else str(lr.status)

                requests_list.append({
                    'id': req_id,
                    'employee_id': lr.employee_id,
                    'emp_name': emp_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'days_requested': days_requested,
                    'reason': str(lr.reason) if lr.reason else "",
                    'status': status_val
                })
            session.close()
        except Exception as e:
            print(f"Error loading leave requests: {e}")
            requests_list = []

        if not requests_list:
            empty_message = "No leave requests yet. Apply for leave!" if self.view_mode == "employee" else "No requests. Apply one!"
            table_content = ft.Column([
                ft.Icon(ft.Icons.EVENT_BUSY, size=64, color="#BDBDBD"),
                ft.Text(empty_message, size=14, color="#757575"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        else:
            rows = []
            for r in requests_list:
                colors = {"approved": "#4CAF50", "rejected": "#F44336",
                          "cancelled": "#9E9E9E", "pending": "#FF9800"}
                status_val = r.get("status", "pending")
                color = colors.get(status_val, "#9E9E9E")

                # Build action buttons - only show for admin mode
                action_cells = []
                if self.view_mode == "admin":
                    action_cells = [
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.CHECK, icon_color="#4CAF50",
                                    on_click=lambda e, req_id=r['id']: self._update_status(
                                        req_id, "approved"),
                                    tooltip="Approve", visible=status_val == "pending"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE, icon_color="#F44336",
                                    on_click=lambda e, req_id=r['id']: self._update_status(
                                        req_id, "rejected"),
                                    tooltip="Reject", visible=status_val == "pending"
                                ),
                            ], spacing=2)
                        ),
                    ]
                else:
                    # Employee view - show status only
                    action_cells = [
                        ft.DataCell(ft.Text(status_val.title(),
                                    color=color, weight=ft.FontWeight.BOLD)),
                    ]

                # In employee mode, show employee name column as empty (redundant)
                emp_name = r['emp_name'] if self.view_mode == "admin" else "My Request"

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(r['id']))),
                            ft.DataCell(ft.Text(emp_name)),
                            ft.DataCell(
                                ft.Text(str(r['start_date']) if r['start_date'] else "-")),
                            ft.DataCell(
                                ft.Text(str(r['end_date']) if r['end_date'] else "-")),
                            ft.DataCell(ft.Text(str(r['days_requested']))),
                            ft.DataCell(
                                ft.Container(
                                    ft.Text(status_val.title(),
                                            size=11, color="WHITE"),
                                    bgcolor=color, padding=5, border_radius=4
                                )
                            ),
                        ] + action_cells,
                    )
                )

            # Build columns based on view mode
            columns = [
                ft.DataColumn(label=ft.Text("ID")),
                ft.DataColumn(label=ft.Text(
                    "Employee" if self.view_mode == "admin" else "Type")),
                ft.DataColumn(label=ft.Text("Start")),
                ft.DataColumn(label=ft.Text("End")),
                ft.DataColumn(label=ft.Text("Days")),
                ft.DataColumn(label=ft.Text("Status")),
                ft.DataColumn(label=ft.Text("Actions")),
            ]

            table = ft.DataTable(
                columns=columns,
                rows=rows, expand=True,
            )
            table_content = ft.Container(
                content=table, expand=True, padding=10)

        return ft.Column([header, ft.Container(padding=20, content=table_content, expand=True)], expand=True)

    def on_back(self, e):
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)

    def on_add(self, e):
        self._show_add_dialog()

    def _show_add_dialog(self):
        # In employee mode, only allow selecting self
        # In admin mode, allow selecting any employee

        employees = []
        leave_types = []
        try:
            session = get_db_session()
            employees = get_all_employees(session)
            leave_types = get_leave_type_configs(session)
            session.close()
        except Exception as e:
            print(f"Error loading data: {e}")

        emp_options = []
        for emp in employees:
            emp_name = f"{emp.first_name} {emp.last_name}"
            emp_id = int(emp.id)
            emp_options.append(ft.dropdown.Option(
                key=str(emp_id), text=emp_name))

        type_options = []
        for lt in leave_types:
            lt_id = int(lt.id)
            lt_name = str(lt.name) if lt.name else "Unknown"
            type_options.append(ft.dropdown.Option(
                key=str(lt_id), text=lt_name))

        # No demo fallbacks - require real data
        if not emp_options:
            emp_options = [ft.dropdown.Option(
                key="", text="No employees available")]
        if not type_options:
            type_options = [ft.dropdown.Option(
                key="", text="No leave types configured")]

        # In employee mode, pre-select current user
        default_emp_value = str(self.employee_id) if self.employee_id and self.view_mode == "employee" else (
            emp_options[0].key if emp_options else None)

        emp_dropdown = ft.Dropdown(
            width=300,
            options=emp_options,
            label="Employee *",
            value=default_emp_value,
            # Employees can only apply for themselves
            disabled=(self.view_mode == "employee")
        )
        type_dropdown = ft.Dropdown(
            width=250, options=type_options, label="Leave Type *")

        # Date pickers for leave dates
        start_date_picker = DatePickerField(label="Start Date *", width=200)
        start_date_picker._page = self._page

        end_date_picker = DatePickerField(label="End Date *", width=200)
        end_date_picker._page = self._page

        reason = ft.TextField(label="Reason *", width=500, multiline=True)
        error = ft.Text("", color="#F44336", size=12, visible=False)

        def save(e):
            if not emp_dropdown.value or not type_dropdown.value or not start_date_picker.value or not end_date_picker.value or not reason.value:
                error.value = "All fields required!"
                error.visible = True
                self._page.update()
                return

            try:
                d1 = date.fromisoformat(start_date_picker.value)
                d2 = date.fromisoformat(end_date_picker.value)
                days = (d2 - d1).days + 1

                emp_id = int(emp_dropdown.value)
                leave_type_id = int(type_dropdown.value)

                session = get_db_session()
                try:
                    create_leave_request(
                        session,
                        employee_id=emp_id,
                        leave_type_id=leave_type_id,
                        start_date=d1,
                        end_date=d2,
                        reason=reason.value
                    )
                    self._close_dialog()
                    self._show_success("Leave request submitted!")
                    self._refresh()
                except Exception as ex:
                    error.value = str(ex)
                    error.visible = True
                    self._page.update()
                finally:
                    session.close()

            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Apply Leave"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([emp_dropdown, type_dropdown], spacing=10),
                    ft.Row([start_date_picker, end_date_picker], spacing=10),
                    reason, error,
                    ft.Container(height=20),  # Extra space at bottom
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=550,
                height=350,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Submit", on_click=save,
                                  style=ft.ButtonStyle(bgcolor="#9C27B0", color="WHITE"))
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _update_status(self, req_id, status):
        try:
            session = get_db_session()
            try:
                if status == "approved":
                    approve_leave_request(session, req_id)
                elif status == "rejected":
                    reject_leave_request(session, req_id)
                self._show_success(f"Request {status}!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                session.close()
        except Exception as ex:
            self._show_error(str(ex))

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


def show_leaves(page, user, view_mode="admin"):
    """Helper function to show leaves screen.

    Args:
        page: Flet page object
        user: Current user dictionary
        view_mode: "admin" for admin view, "employee" for employee view
    """
    page.clean()
    page.add(LeavesScreen(page, user, view_mode))
