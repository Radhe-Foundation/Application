"""
RadheFoundation HRA - Attendance Management Screen - Fixed with Check-Out Support
Updated with view_mode support: admin (manage all) or employee (self only)
"""

import flet as ft
from datetime import datetime, date
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Attendance, Employee, AttendanceStatus
from database.operations import (
    get_all_employees, mark_attendance, get_attendance_records,
    get_employee_by_id, get_today_attendance, get_user_by_id,
    get_employee_by_user_id
)
from components.forms import DatePickerField, TimePickerField


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


class AttendanceScreen(ft.Container):
    def __init__(self, page, user, view_mode="admin"):
        """
        AttendanceScreen constructor.

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
            set_current_screen("attendance")
        except Exception as e:
            print(f"[Attendance] Error setting keyboard screen: {e}")

        # Initialize notifications (no test notification on load)
        try:
            from utils.notification_manager import get_notification_manager
            self._notification_manager = get_notification_manager()
        except Exception as e:
            print(f"[Attendance] Error initializing notifications: {e}")
            self._notification_manager = None

    def _build_content(self):
        # Header title based on view mode
        title = "Attendance Management" if self.view_mode == "admin" else "My Attendance"

        # Header buttons based on view mode
        if self.view_mode == "admin":
            header_buttons = ft.ElevatedButton(
                "Mark Attendance",
                icon=ft.Icons.ADD,
                on_click=self.on_add,
                style=ft.ButtonStyle(bgcolor="#F57C00", color="WHITE")
            )
        else:
            # Employee mode: Show Punch In/Punch Out buttons instead of Mark Attendance
            header_buttons = ft.Row([
                ft.ElevatedButton(
                    "Punch In",
                    icon=ft.Icons.LOGIN,
                    on_click=self._on_punch_in,
                    style=ft.ButtonStyle(bgcolor="#4CAF50", color="WHITE")
                ),
                ft.Container(width=10),
                ft.ElevatedButton(
                    "Punch Out",
                    icon=ft.Icons.LOGOUT,
                    on_click=self._on_punch_out,
                    style=ft.ButtonStyle(bgcolor="#F44336", color="WHITE")
                ),
            ])

        header = ft.Container(
            padding=15,
            bgcolor="#FF9800" if self.view_mode == "admin" else "#009688",
            content=ft.Row([
                ft.Text(title, size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                header_buttons,
            ])
        )

        # Quick Actions Panel - only for admin mode
        quick_actions = self._build_quick_actions(
        ) if self.view_mode == "admin" else ft.Container()

        # Load attendance records based on view mode
        records = []
        try:
            session = get_db_session()
            attendances = get_attendance_records(session, limit=100)

            for att in attendances:
                # In employee mode, only show current user's records
                if self.view_mode == "employee" and att.employee_id != self.employee_id:
                    continue

                # Get employee name
                employee = get_employee_by_id(session, att.employee_id)
                emp_name = f"{employee.first_name} {employee.last_name}" if employee else "Unknown"

                # Safely extract values from SQLAlchemy model
                att_id = int(att.id) if att.id else 0
                att_date = str(att.date) if att.date else "-"
                att_status = str(att.status.value) if hasattr(
                    att.status, 'value') else str(att.status)

                # Handle check_in/check_out times
                check_in = None
                check_out = None
                if att.check_in:
                    if hasattr(att.check_in, 'strftime'):
                        check_in = att.check_in.strftime('%H:%M')
                    else:
                        check_in = str(att.check_in)

                if att.check_out:
                    if hasattr(att.check_out, 'strftime'):
                        check_out = att.check_out.strftime('%H:%M')
                    else:
                        check_out = str(att.check_out)

                # Handle working_hours
                working_hours = None
                if att.working_hours:
                    working_hours = float(att.working_hours)

                records.append({
                    'id': att_id,
                    'employee_id': att.employee_id,
                    'emp_name': emp_name,
                    'date': att_date,
                    'check_in': check_in,
                    'check_out': check_out,
                    'status': att_status,
                    'working_hours': working_hours
                })
            session.close()
        except Exception as e:
            print(f"Error loading attendance: {e}")
            records = []

        if not records:
            empty_message = "No attendance records yet. Check in to get started!" if self.view_mode == "employee" else "No records. Mark one!"
            table_content = ft.Column([
                ft.Icon(ft.Icons.EVENT, size=64, color="#BDBDBD"),
                ft.Text(empty_message, size=14, color="#757575"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        else:
            rows = []
            for r in records:
                colors = {"present": "#4CAF50", "absent": "#F44336",
                          "late": "#FF9800", "half_day": "#FFC107", "on_leave": "#2196F3"}
                status_val = r.get("status", "present")
                color = colors.get(status_val, "#9E9E9E")
                check_in = r.get('check_in', '-') or "-"
                check_out = r.get('check_out', '-') or "-"

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(r['id']))),
                            ft.DataCell(ft.Text(r['emp_name'] or "Unknown")),
                            ft.DataCell(ft.Text(str(r['date']))),
                            ft.DataCell(ft.Text(check_in)),
                            ft.DataCell(ft.Text(check_out)),
                            ft.DataCell(
                                ft.Container(
                                    ft.Text(status_val.title(),
                                            size=11, color="WHITE"),
                                    bgcolor=color, padding=5, border_radius=4
                                )
                            ),
                            ft.DataCell(
                                ft.Text(f"{r['working_hours']:.1f}h" if r.get('working_hours') else "-")),
                        ]
                    )
                )

            # Columns based on view mode - hide employee name in employee mode
            if self.view_mode == "employee":
                columns = [
                    ft.DataColumn(label=ft.Text("ID")),
                    ft.DataColumn(label=ft.Text("Date")),
                    ft.DataColumn(label=ft.Text("Check In")),
                    ft.DataColumn(label=ft.Text("Check Out")),
                    ft.DataColumn(label=ft.Text("Status")),
                    ft.DataColumn(label=ft.Text("Hours")),
                    # Empty column to match cells
                    ft.DataColumn(label=ft.Text("")),
                ]
            else:
                columns = [
                    ft.DataColumn(label=ft.Text("ID")),
                    ft.DataColumn(label=ft.Text("Employee")),
                    ft.DataColumn(label=ft.Text("Date")),
                    ft.DataColumn(label=ft.Text("In")),
                    ft.DataColumn(label=ft.Text("Out")),
                    ft.DataColumn(label=ft.Text("Status")),
                    ft.DataColumn(label=ft.Text("Hours"))
                ]

            table = ft.DataTable(
                columns=columns,
                rows=rows, expand=True,
            )
            table_content = ft.Container(
                content=table, expand=True, padding=10)

        return ft.Column([header, quick_actions, ft.Container(padding=20, content=table_content, expand=True)], expand=True)

    def _build_quick_actions(self):
        """Build quick check-in/check-out buttons for HR (admin mode only)"""
        # Load employees
        employees = []
        try:
            session = get_db_session()
            employees = get_all_employees(session)
            session.close()
        except Exception as e:
            print(f"Error loading employees: {e}")

        emp_options = []
        for emp in employees:
            emp_name = f"{emp.first_name} {emp.last_name}"
            emp_id = int(emp.id)
            emp_options.append(ft.dropdown.Option(
                key=str(emp_id), text=emp_name))

        if not emp_options:
            emp_options = [ft.dropdown.Option(key="1", text="Tanu singh")]

        selected_emp = ft.Dropdown(
            width=250,
            options=emp_options,
            label="Select Employee",
            value=emp_options[0].key if emp_options else None
        )

        def on_check_in(e):
            if not selected_emp.value:
                self._show_error("Please select an employee!")
                return
            self._quick_attendance(selected_emp.value, "check_in")

        def on_check_out(e):
            if not selected_emp.value:
                self._show_error("Please select an employee!")
                return
            self._quick_attendance(selected_emp.value, "check_out")

        return ft.Container(
            padding=15,
            bgcolor=ft.Colors.WHITE,
            content=ft.Row([
                ft.Text("Quick Actions:", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(width=20),
                selected_emp,
                ft.Container(width=10),
                ft.ElevatedButton(
                    "Check In",
                    icon=ft.Icons.LOGIN,
                    bgcolor="#4CAF50",
                    color="WHITE",
                    on_click=on_check_in
                ),
                ft.Container(width=10),
                ft.ElevatedButton(
                    "Check Out",
                    icon=ft.Icons.LOGOUT,
                    bgcolor="#F44336",
                    color="WHITE",
                    on_click=on_check_out
                ),
            ], alignment=ft.MainAxisAlignment.START),
            margin=ft.margin.only(bottom=10)
        )

    def _quick_attendance(self, employee_id, action):
        """Handle quick check-in/check-out"""
        try:
            emp_id = int(employee_id)
            today = date.today()
            now = datetime.now()

            session = get_db_session()
            try:
                # Check if attendance exists for today
                existing = get_today_attendance(session, emp_id)

                if action == "check_in":
                    if existing:
                        # Update check-in time
                        existing.check_in = now
                        session.commit()
                        self._show_success("Check-in time updated!")
                    else:
                        # Create new attendance with check-in
                        mark_attendance(
                            session,
                            employee_id=emp_id,
                            date=today,
                            status=AttendanceStatus.PRESENT,
                            check_in=now
                        )
                        self._show_success("Check-in recorded!")

                elif action == "check_out":
                    if not existing:
                        self._show_error(
                            "No attendance record found! Please check in first.")
                        return

                    # Update check-out time
                    existing.check_out = now

                    # Calculate working hours
                    if existing.check_in:
                        working_hours = (
                            now - existing.check_in).total_seconds() / 3600
                        existing.working_hours = working_hours

                    session.commit()
                    self._show_success("Check-out recorded!")

                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                session.close()

        except Exception as ex:
            self._show_error(f"Error: {str(ex)}")

    def _on_punch_in(self, e):
        """Handle punch in for employee - auto records current time"""
        if not self.employee_id:
            self._show_error("Employee not found! Please contact admin.")
            return
        self._quick_attendance(self.employee_id, "check_in")

    def _on_punch_out(self, e):
        """Handle punch out for employee - auto records current time"""
        if not self.employee_id:
            self._show_error("Employee not found! Please contact admin.")
            return
        self._quick_attendance(self.employee_id, "check_out")

    def on_back(self, e):
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)

    def on_add(self, e):
        """Show add attendance dialog - only for admin mode"""
        if self.view_mode == "employee":
            self._show_error(
                "Please use Punch In/Punch Out buttons to mark your attendance.")
            return
        self._show_add_dialog()

    def _show_add_dialog(self):
        # Load employees using SQLAlchemy
        employees = []
        try:
            session = get_db_session()
            employees = get_all_employees(session)
            session.close()
        except Exception as e:
            print(f"Error loading employees: {e}")
            employees = []

        emp_options = []
        for emp in employees:
            emp_name = f"{emp.first_name} {emp.last_name}"
            emp_id = int(emp.id)
            emp_options.append(ft.dropdown.Option(
                key=str(emp_id), text=emp_name))

        status_options = [
            ft.dropdown.Option(key="present", text="Present"),
            ft.dropdown.Option(key="absent", text="Absent"),
            ft.dropdown.Option(key="late", text="Late"),
            ft.dropdown.Option(key="half_day", text="Half Day"),
            ft.dropdown.Option(key="on_leave", text="On Leave"),
        ]

        # In employee mode, pre-select current user and disable dropdown
        default_emp_value = str(self.employee_id) if self.employee_id and self.view_mode == "employee" else (
            emp_options[0].key if emp_options else None)

        employee = ft.Dropdown(
            width=300,
            options=emp_options,
            label="Employee *",
            value=default_emp_value,
            disabled=(self.view_mode == "employee")
        )
        status = ft.Dropdown(width=150, options=status_options,
                             label="Status *", value="present")

        # Date picker for attendance date
        att_date_picker = DatePickerField(label="Date", width=200)
        att_date_picker._page = self._page
        att_date_picker.value = date.today().isoformat()

        # Time pickers for check in/out
        check_in_picker = TimePickerField(label="Check In", width=150)
        check_in_picker._page = self._page

        check_out_picker = TimePickerField(label="Check Out", width=150)
        check_out_picker._page = self._page

        error = ft.Text("", color="#F44336", size=12, visible=False)

        def save(e):
            # Validate required fields
            if not employee.value:
                error.value = "Please select an Employee!"
                error.visible = True
                self._page.update()
                return
            if not status.value:
                error.value = "Please select a Status!"
                error.visible = True
                self._page.update()
                return
            if not att_date_picker.value:
                error.value = "Please select a Date!"
                error.visible = True
                self._page.update()
                return

            try:
                working_hours = None
                in_time = None
                out_time = None

                # Parse check-in time
                in_val = check_in_picker.value
                if in_val:
                    if isinstance(in_val, str):
                        try:
                            in_time = datetime.strptime(in_val, "%H:%M").time()
                        except ValueError:
                            try:
                                in_time = datetime.strptime(
                                    in_val, "%H:%M:%S").time()
                            except ValueError:
                                error.value = f"Invalid check-in time format: {in_val}"
                                error.visible = True
                                self._page.update()
                                return
                    elif isinstance(in_val, datetime):
                        in_time = in_val.time()
                    elif hasattr(in_val, 'hour'):
                        in_time = in_val

                # Parse check-out time
                out_val = check_out_picker.value
                if out_val:
                    if isinstance(out_val, str):
                        try:
                            out_time = datetime.strptime(
                                out_val, "%H:%M").time()
                        except ValueError:
                            try:
                                out_time = datetime.strptime(
                                    out_val, "%H:%M:%S").time()
                            except ValueError:
                                error.value = f"Invalid check-out time format: {out_val}"
                                error.visible = True
                                self._page.update()
                                return
                    elif isinstance(out_val, datetime):
                        out_time = out_val.time()
                    elif hasattr(out_val, 'hour'):
                        out_time = out_val

                # Calculate working hours
                if in_time and out_time:
                    dt_in = datetime.combine(date.today(), in_time)
                    dt_out = datetime.combine(date.today(), out_time)
                    delta = (dt_out - dt_in).total_seconds() / 3600
                    # Prevent negative hours (handle overnight shifts)
                    if delta < 0:
                        delta += 24
                    working_hours = max(0, delta)

                # Get the date value
                att_date = att_date_picker.value
                if isinstance(att_date, str):
                    pass
                elif isinstance(att_date, date):
                    att_date = att_date.isoformat()

                # Get employee ID as integer
                emp_id = int(employee.value)

                # Get status enum
                status_enum = AttendanceStatus.PRESENT
                status_map = {
                    "present": AttendanceStatus.PRESENT,
                    "absent": AttendanceStatus.ABSENT,
                    "late": AttendanceStatus.LATE,
                    "half_day": AttendanceStatus.HALF_DAY,
                    "on_leave": AttendanceStatus.ON_LEAVE
                }
                status_enum = status_map.get(
                    status.value, AttendanceStatus.PRESENT)

                # Parse date for datetime
                if isinstance(att_date, str):
                    att_date_obj = datetime.strptime(
                        att_date, '%Y-%m-%d').date()
                else:
                    att_date_obj = att_date

                # Create datetime objects for check-in/check-out
                check_in_dt = None
                check_out_dt = None
                if in_time:
                    check_in_dt = datetime.combine(att_date_obj, in_time)
                if out_time:
                    check_out_dt = datetime.combine(att_date_obj, out_time)

                # Mark attendance using SQLAlchemy
                session = get_db_session()
                try:
                    mark_attendance(
                        session,
                        employee_id=emp_id,
                        date=att_date_obj,
                        status=status_enum,
                        check_in=check_in_dt,
                        check_out=check_out_dt
                    )
                    self._close_dialog()
                    self._show_success("Attendance marked successfully!")
                    self._refresh()
                except Exception as ex:
                    error.value = f"Error saving attendance: {str(ex)}"
                    error.visible = True
                    self._page.update()
                finally:
                    session.close()

            except Exception as ex:
                error.value = f"Error saving attendance: {str(ex)}"
                error.visible = True
                self._page.update()
                import traceback
                traceback.print_exc()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Mark Attendance"),
            content=ft.Container(
                content=ft.Column([
                    employee, ft.Row([status, att_date_picker], spacing=10),
                    ft.Row([check_in_picker, check_out_picker], spacing=10),
                    ft.Text("Leave times empty for absent status",
                            size=11, color="#757575"),
                    error,
                    ft.Container(height=20),
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=300,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  style=ft.ButtonStyle(bgcolor="#FF9800", color="WHITE"))
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


def show_attendance(page, user, view_mode="admin"):
    """Helper function to show attendance screen.

    Args:
        page: Flet page object
        user: Current user dictionary
        view_mode: "admin" for admin view, "employee" for employee view
    """
    page.clean()
    page.add(AttendanceScreen(page, user, view_mode))
