"""
Vernika HRA - Attendance Management Screen - Fixed for Flet 0.80+
Updated to use SQLAlchemy operations
"""

import flet as ft
from datetime import datetime, date
from database.connection import get_db_session
from database.models import Attendance, Employee, AttendanceStatus
from database.operations import (
    get_all_employees, mark_attendance, get_attendance_records,
    get_employee_by_id
)


class DatePickerField(ft.Container):
    """Custom Date Picker Field with integrated picker"""

    def __init__(self, label="Date", width=200, value=None, **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.date_value = value

        self.text_field = ft.TextField(
            label=label,
            width=width - 50,
            value=value if value else "",
            read_only=True,
            hint_text="YYYY-MM-DD"
        )

        self.picker_button = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=self._show_picker,
            tooltip="Select date"
        )

        self.content = ft.Row([
            self.text_field,
            self.picker_button
        ], spacing=0)

        # DatePicker control
        self.date_picker = ft.DatePicker(
            on_change=self._on_date_change,
            first_date=datetime(1950, 1, 1),
            last_date=datetime(2100, 12, 31),
        )

        # Add picker to page overlay when dialog opens
        self._page = None

    def _show_picker(self, e):
        if self._page:
            if self.date_value:
                # Set picker date if we have a value
                try:
                    dt = datetime.strptime(self.date_value, '%Y-%m-%d')
                    self.date_picker.value = dt
                except:
                    pass
            self._page.overlay.append(self.date_picker)
            self.date_picker.open = True
            self._page.update()

    def _on_date_change(self, e):
        if e.control.value:
            self.date_value = e.control.value.strftime('%Y-%m-%d')
            self.text_field.value = self.date_value
            if self._page:
                # Remove picker from overlay
                self._page.overlay.remove(self.date_picker)
                self._page.update()

    @property
    def value(self):
        return self.date_value

    @value.setter
    def value(self, val):
        self.date_value = val
        self.text_field.value = val if val else ""


class TimePickerField(ft.Container):
    """Custom Time Picker Field with integrated picker"""

    def __init__(self, label="Time", width=150, value=None, **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.time_value = value

        self.text_field = ft.TextField(
            label=label,
            width=width - 50,
            value=value if value else "",
            read_only=True,
            hint_text="HH:MM"
        )

        self.picker_button = ft.IconButton(
            icon=ft.Icons.ACCESS_TIME,
            on_click=self._show_picker,
            tooltip="Select time"
        )

        self.content = ft.Row([
            self.text_field,
            self.picker_button
        ], spacing=0)

        # TimePicker control
        self.time_picker = ft.TimePicker(
            on_change=self._on_time_change,
        )

        # Add picker to page overlay when dialog opens
        self._page = None

    def _show_picker(self, e):
        if self._page:
            self._page.overlay.append(self.time_picker)
            self.time_picker.open = True
            self._page.update()

    def _on_time_change(self, e):
        if e.control.value:
            # time_picker.value is a datetime.time object
            time_obj = e.control.value
            self.time_value = time_obj.strftime('%H:%M')
            self.text_field.value = self.time_value
            if self._page:
                # Remove picker from overlay
                self._page.overlay.remove(self.time_picker)
                self._page.update()

    @property
    def value(self):
        return self.time_value

    @value.setter
    def value(self, val):
        self.time_value = val
        self.text_field.value = val if val else ""


class AttendanceScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = "#F5F5F5"
        self.content = self._build_content()

    def _build_content(self):
        header = ft.Container(
            padding=15,
            bgcolor="#FF9800",
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self.on_back
                ),
                ft.Text("Attendance Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Mark Attendance",
                    icon=ft.Icons.ADD,
                    on_click=self.on_add,
                    style=ft.ButtonStyle(bgcolor="#F57C00", color="WHITE")
                ),
            ])
        )

        # Load attendance records using SQLAlchemy
        records = []
        try:
            session = get_db_session()
            attendances = get_attendance_records(session, limit=100)
            for att in attendances:
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
            table_content = ft.Column([
                ft.Icon(ft.Icons.EVENT, size=64, color="#BDBDBD"),
                ft.Text("No records. Mark one!", size=14, color="#757575"),
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
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(label=ft.Text("ID")),
                    ft.DataColumn(label=ft.Text("Employee")),
                    ft.DataColumn(label=ft.Text("Date")),
                    ft.DataColumn(label=ft.Text("In")),
                    ft.DataColumn(label=ft.Text("Out")),
                    ft.DataColumn(label=ft.Text("Status")),
                    ft.DataColumn(label=ft.Text("Hours"))
                ],
                rows=rows, expand=True,
            )
            table_content = ft.Container(
                content=table, expand=True, padding=10)

        return ft.Column([header, ft.Container(padding=20, content=table_content, expand=True)], expand=True)

    def on_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def on_add(self, e):
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

        # No fallback - show empty if no employees

        status_options = [
            ft.dropdown.Option(key="present", text="Present"),
            ft.dropdown.Option(key="absent", text="Absent"),
            ft.dropdown.Option(key="late", text="Late"),
            ft.dropdown.Option(key="half_day", text="Half Day"),
            ft.dropdown.Option(key="on_leave", text="On Leave"),
        ]

        employee = ft.Dropdown(
            width=300, options=emp_options, label="Employee *")
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
                    ft.Container(height=20),  # Extra space at bottom
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


def show_attendance(page, user):
    page.clean()
    page.add(AttendanceScreen(page, user))
