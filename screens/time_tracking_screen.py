"""
Vernika HRA - Time Tracking Screen (Rebuilt)
Employee Timesheet & Time Management - Industry Level
"""

import flet as ft
from datetime import datetime, date, timedelta
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Timesheet, TimeEntry, Employee, Project, Task
from sqlalchemy import and_


# Theme colors - Professional palette
PRIMARY = "#1E3A5F"
PRIMARY_LIGHT = "#2E5A8F"
SECONDARY = "#E91E63"
SUCCESS = "#00C853"
WARNING = "#FF9100"
ERROR = "#FF1744"
INFO = "#2979FF"
BACKGROUND = "#F5F7FA"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1A2E"
TEXT_SECONDARY = "#6B7280"
BORDER_COLOR = "#E5E7EB"

# Status colors
STATUS_COLORS = {
    "draft": "#9E9E9E",
    "submitted": INFO,
    "approved": SUCCESS,
    "rejected": ERROR,
}


class TimeTrackingScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.current_view = "list"  # list, create, view
        self.selected_timesheet = None
        self.current_week_start = self._get_week_start(date.today())
        self.content = self._build_content()

    def refresh(self):
        """Refresh the time tracking content"""
        self.content = self._build_content()
        self.update()
        self._page.update()

    def _get_db(self):
        """Get database session"""
        return get_db_session()

    def _get_week_start(self, d):
        """Get Monday of the week"""
        return d - timedelta(days=d.weekday())

    def _get_user_info(self):
        """Get current user info"""
        user_id = None
        if isinstance(self.user, dict):
            user_id = self.user.get('id')
        elif hasattr(self.user, 'id'):
            user_id = self.user.id
        return user_id

    def _is_admin(self):
        """Check if current user is admin"""
        if isinstance(self.user, dict):
            role = self.user.get('role', '').lower()
            return role == 'admin'
        return False

    def _build_content(self):
        """Build the time tracking content"""
        # Header
        header = self._create_header()

        # Content based on current view
        if self.current_view == "list":
            content = self._build_timesheets_list()
        elif self.current_view == "create":
            content = self._build_timesheet_form()
        elif self.current_view == "view":
            content = self._build_timesheet_detail()
        else:
            content = self._build_timesheets_list()

        return ft.ListView([
            header,
            ft.Container(
                content=content,
                expand=True,
            ),
        ], expand=True, spacing=0)

    def _create_header(self):
        """Create header"""
        return ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.TIMER, color="WHITE", size=28),
                    ft.Text("Time Tracking", size=20, color="WHITE",
                            weight=ft.FontWeight.BOLD),
                ], spacing=15),
                ft.Container(expand=True),
                ft.Row([
                    ft.FilledButton(
                        "New Timesheet",
                        icon=ft.Icons.ADD,
                        bgcolor=SUCCESS,
                        color="WHITE",
                        on_click=self._show_create_timesheet,
                    ),
                    ft.Container(width=10),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color="WHITE",
                        on_click=self.refresh,
                        tooltip="Refresh"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="WHITE",
                        on_click=self._go_back,
                        tooltip="Back to Dashboard"
                    ),
                ], spacing=5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        )

    # ============ TIMESHEETS LIST ============

    def _build_timesheets_list(self):
        """Build timesheets list view"""
        timesheets = self._get_timesheets()

        # Stats
        total_hours = sum(t.total_hours or 0 for t in timesheets)
        pending_count = len([t for t in timesheets if t.status == "submitted"])
        approved_count = len([t for t in timesheets if t.status == "approved"])

        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_kpi_card("Total Timesheets", len(
                    timesheets), ft.Icons.ASSIGNMENT, INFO),
                self._create_kpi_card(
                    "Total Hours", f"{total_hours:.1f}h", ft.Icons.ACCESS_TIME, WARNING),
                self._create_kpi_card(
                    "Pending", pending_count, ft.Icons.PENDING, WARNING),
                self._create_kpi_card(
                    "Approved", approved_count, ft.Icons.CHECK_CIRCLE, SUCCESS),
            ], spacing=15),
        )

        # Filter bar
        filter_bar = self._create_filter_bar()

        # Timesheets table
        if timesheets:
            timesheets_table = self._create_timesheets_table(timesheets)
        else:
            timesheets_table = self._create_empty_state(
                "No timesheets found", "Create your first timesheet",
                ft.Icons.TIMER, self._show_create_timesheet
            )

        return ft.Column([
            filter_bar,
            stats_row,
            ft.Container(content=timesheets_table, expand=True),
        ], spacing=0, expand=True)

    def _create_filter_bar(self):
        """Create filter bar"""
        status_filter = ft.Dropdown(
            hint_text="Status",
            width=150,
            options=[
                ft.dropdown.Option("all", "All"),
                ft.dropdown.Option("draft", "Draft"),
                ft.dropdown.Option("submitted", "Submitted"),
                ft.dropdown.Option("approved", "Approved"),
                ft.dropdown.Option("rejected", "Rejected"),
            ],
            value="all",
            border_color=BORDER_COLOR,
        )

        return ft.Container(
            content=ft.Row([
                status_filter,
                ft.Container(expand=True),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _create_timesheets_table(self, timesheets):
        """Create timesheets table using ListView for scrolling"""
        if not timesheets:
            return self._create_empty_state(
                "No timesheets found", "Create your first timesheet",
                ft.Icons.TIMER, self._show_create_timesheet
            )

        return ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=10,
                padding=15,
                controls=[
                    self._create_timesheet_card(t) for t in timesheets
                ]
            ),
            bgcolor=SURFACE,
            padding=10,
            border_radius=10,
            expand=True,
        )

    def _create_timesheet_row(self, timesheet):
        """Create timesheet table row - kept for compatibility"""
        status_color = STATUS_COLORS.get(timesheet.status, "#666")

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(
                    f"{timesheet.employee.first_name} {timesheet.employee.last_name}" if timesheet.employee else "N/A")),
                ft.DataCell(ft.Text(timesheet.week_start.strftime(
                    "%d %b %Y") if timesheet.week_start else "N/A")),
                ft.DataCell(ft.Text(timesheet.week_end.strftime(
                    "%d %b %Y") if timesheet.week_end else "N/A")),
                ft.DataCell(
                    ft.Text(f"{timesheet.total_hours:.1f}" if timesheet.total_hours else "0.0")),
                ft.DataCell(ft.Container(
                    content=ft.Text(timesheet.status.upper(
                    ) if timesheet.status else "DRAFT", size=10, color="WHITE"),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=10,
                )),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.VISIBILITY, icon_size=18, tooltip="View",
                                  on_click=lambda e: self._view_timesheet(timesheet)),
                    ft.IconButton(ft.Icons.EDIT, icon_size=18, tooltip="Edit",
                                  on_click=lambda e: self._edit_timesheet(timesheet)),
                    ft.IconButton(ft.Icons.DELETE, icon_size=18, tooltip="Delete",
                                  on_click=lambda e: self._delete_timesheet(timesheet)),
                ], spacing=0)),
            ],
        )

    def _create_timesheet_card(self, timesheet):
        """Create timesheet card for scrollable list view"""
        status_color = STATUS_COLORS.get(timesheet.status, "#666")

        emp_name = "N/A"
        if timesheet.employee:
            emp_name = f"{timesheet.employee.first_name} {timesheet.employee.last_name}"

        week_start = timesheet.week_start.strftime(
            "%d %b %Y") if timesheet.week_start else "N/A"
        week_end = timesheet.week_end.strftime(
            "%d %b %Y") if timesheet.week_end else "N/A"
        total_hours = f"{timesheet.total_hours:.1f}" if timesheet.total_hours else "0.0"
        status = timesheet.status.upper() if timesheet.status else "DRAFT"

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(emp_name, size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{week_start} - {week_end}",
                                size=12, color=TEXT_SECONDARY),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(total_hours, size=16,
                                weight=ft.FontWeight.BOLD, color=PRIMARY),
                        ft.Text("hours", size=10, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    ft.Container(
                        content=ft.Text(status, size=10, color="WHITE"),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(
                            horizontal=12, vertical=6),
                        border_radius=15,
                    ),
                    ft.Row([
                        ft.IconButton(ft.Icons.VISIBILITY, icon_size=20, tooltip="View",
                                      on_click=lambda e: self._view_timesheet(timesheet)),
                        ft.IconButton(ft.Icons.EDIT, icon_size=20, tooltip="Edit",
                                      on_click=lambda e: self._edit_timesheet(timesheet)),
                        ft.IconButton(ft.Icons.DELETE, icon_size=20, tooltip="Delete",
                                      on_click=lambda e: self._delete_timesheet(timesheet)),
                    ], spacing=5),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
            ),
            elevation=2,
        )

    def _create_time_entry_row(self, entry):
        """Create time entry row card for scrollable list"""
        date_str = entry.date.strftime("%d %b") if entry.date else "N/A"
        project_name = entry.project.name if entry.project else "No Project"
        hours_str = f"{entry.hours:.1f}" if entry.hours else "0.0"
        billable_str = "Yes" if entry.is_billable else "No"
        description = entry.description or ""

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(date_str, size=13,
                                    weight=ft.FontWeight.BOLD),
                    width=80,
                ),
                ft.Container(
                    content=ft.Text(project_name, size=13),
                    width=120,
                ),
                ft.Container(
                    content=ft.Text(description, size=12,
                                    color=TEXT_SECONDARY),
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(hours_str, size=13,
                                    weight=ft.FontWeight.BOLD),
                    width=60,
                ),
                ft.Container(
                    content=ft.Text(billable_str, size=12),
                    width=60,
                ),
            ], spacing=10),
            padding=12,
            bgcolor="#F9FAFB",
            border_radius=8,
        )

    # ============ TIMESHEET FORM ============

    def _build_timesheet_form(self):
        """Build timesheet creation form with proper time entry capture"""
        projects = self._get_projects()

        # Get current user employee
        user_employee = self._get_user_employee()

        # Week selection
        week_start = self.current_week_start
        week_end = week_start + timedelta(days=6)

        # Navigation with quick week jump
        week_nav = ft.Container(
            content=ft.Row([
                ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=self._prev_week),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b %Y')}",
                                size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("Click arrows to change week",
                                size=10, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
                ft.IconButton(ft.Icons.CHEVRON_RIGHT,
                              on_click=self._next_week),
                ft.Container(width=20),
                ft.ElevatedButton(
                    "Today",
                    on_click=self._go_to_current_week,
                    style=ft.ButtonStyle(bgcolor=INFO, color="WHITE"),
                    height=32,
                ),
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            padding=15,
            bgcolor=SURFACE,
            border_radius=10,
        )

        # Day entries with proper field storage
        day_entries = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_entry = self._build_day_entry(day, projects, i)
            day_entries.append(day_entry)

        days_container = ft.Container(
            content=ft.Column(day_entries, spacing=15),
            padding=20,
            bgcolor=SURFACE,
            border_radius=10,
        )

        # Notes
        notes_field = ft.TextField(
            label="Notes / Comments",
            multiline=True,
            min_lines=2,
            hint_text="Additional notes for this week",
            border_color=PRIMARY,
            width=500,
        )

        # Total hours display
        total_display = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ACCESS_TIME, color=PRIMARY, size=24),
                ft.Text("Total Hours This Week:", size=14,
                        weight=ft.FontWeight.BOLD),
                ft.Text("0.0 hours", size=16, weight=ft.FontWeight.BOLD,
                        color=SUCCESS),
            ], spacing=10),
            padding=15,
            bgcolor="#E8F5E9",
            border_radius=10,
        )

        # Buttons
        buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "💾 Save as Draft",
                    on_click=lambda e: self._save_timesheet(
                        "draft", notes_field),
                    bgcolor=PRIMARY,
                    color="WHITE",
                ),
                ft.ElevatedButton(
                    "✅ Submit for Approval",
                    on_click=lambda e: self._save_timesheet(
                        "submitted", notes_field),
                    bgcolor=SUCCESS,
                    color="WHITE",
                ),
                ft.TextButton("Cancel", on_click=self._cancel_form),
            ], spacing=15, alignment=ft.MainAxisAlignment.CENTER),
        )

        # Instructions
        instructions = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO, size=16, color=INFO),
                    ft.Text("Instructions", size=12,
                            weight=ft.FontWeight.BOLD),
                ], spacing=5),
                ft.Text("• Enter hours worked for each day (Monday-Friday)",
                        size=11, color=TEXT_SECONDARY),
                ft.Text("• Select a project for each entry",
                        size=11, color=TEXT_SECONDARY),
                ft.Text("• Mark as billable if the work is billable to a client",
                        size=11, color=TEXT_SECONDARY),
                ft.Text("• Save as draft to edit later, or submit for approval",
                        size=11, color=TEXT_SECONDARY),
            ], spacing=5),
            padding=15,
            bgcolor="#E3F2FD",
            border_radius=10,
        )

        return ft.Container(
            content=ft.Column([
                week_nav,
                instructions,
                days_container,
                total_display,
                notes_field,
                ft.Container(height=15),
                buttons,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=25,
        )

    def _go_to_current_week(self):
        """Go to current week"""
        self.current_week_start = self._get_week_start(date.today())
        self.refresh()

    def _build_day_entry(self, day, projects, day_index):
        """Build day entry row with proper field references"""
        is_weekend = day.weekday() >= 5
        day_name = day.strftime("%A")
        date_str = day.strftime("%Y-%m-%d")

        if is_weekend:
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.WEEKEND, size=20,
                                color=TEXT_SECONDARY),
                        ft.Text(f"{day_name}, {day.strftime('%d %b %Y')}", size=14,
                                weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
                        ft.Container(
                            content=ft.Text("WEEKEND", size=10, color="WHITE"),
                            bgcolor="#9E9E9E",
                            padding=5,
                            border_radius=5,
                        ),
                    ], spacing=10),
                    ft.Text("No work entries - Weekend",
                            size=12, color="#999"),
                ], spacing=5),
                padding=15,
                bgcolor="#F5F5F5",
                border_radius=8,
                border=ft.border.all(1, "#E0E0E0"),
            )

        # Create unique IDs for form fields
        project_dropdown = ft.Dropdown(
            hint_text="Select Project",
            options=[ft.dropdown.Option(str(p.id), p.name) for p in projects] +
            [ft.dropdown.Option("none", "No Project")],
            width=200,
            border_color=PRIMARY,
            key=f"project_{day_index}",
        )

        hours_field = ft.TextField(
            hint_text="Hrs",
            value="0",
            width=80,
            border_color=PRIMARY,
            key=f"hours_{day_index}",
        )

        desc_field = ft.TextField(
            hint_text="Work description...",
            expand=True,
            border_color=PRIMARY,
            key=f"desc_{day_index}",
        )

        billable_check = ft.Checkbox(
            label="Billable",
            value=True,
            key=f"billable_{day_index}",
        )

        # Calculate day hours
        hours_display = ft.Text(
            "0h",
            size=12,
            color=TEXT_SECONDARY,
            key=f"hours_display_{day_index}",
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(day_name, size=14,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(day.strftime("%d %b %Y"),
                                    size=11, color=TEXT_SECONDARY),
                        ], spacing=2),
                    ),
                    ft.Container(width=20),
                    project_dropdown,
                    hours_field,
                    desc_field,
                    billable_check,
                    hours_display,
                ], spacing=10, alignment=ft.MainAxisAlignment.START),
            ], spacing=8),
            padding=15,
            bgcolor=SURFACE,
            border_radius=8,
            border=ft.border.all(1, BORDER_COLOR),
        )

    # ============ TIMESHEET DETAIL ============

    def _build_timesheet_detail(self):
        """Build timesheet detail view"""
        if not self.selected_timesheet:
            return ft.Container()

        timesheet = self.selected_timesheet
        status_color = STATUS_COLORS.get(timesheet.status, "#666")

        # Get entries
        entries = self._get_time_entries(timesheet.id)

        # Header
        header_section = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("TIMESHEET", size=24,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Text(f"Employee: {timesheet.employee.first_name} {timesheet.employee.last_name}" if timesheet.employee else "N/A",
                           size=14),
                ]),
                ft.Container(expand=True),
                ft.Column([
                    ft.Text("Status:", size=12, color=TEXT_SECONDARY),
                    ft.Container(
                        content=ft.Text(timesheet.status.upper(
                        ) if timesheet.status else "", size=12, color="WHITE"),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(
                            horizontal=12, vertical=6),
                        border_radius=15,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.END),
            ], spacing=10),
        )

        # Week info
        week_info = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Week Start:", size=12, color=TEXT_SECONDARY),
                    ft.Text(timesheet.week_start.strftime("%d %b %Y") if timesheet.week_start else "N/A",
                           size=14, weight=ft.FontWeight.BOLD),
                ], spacing=2),
                ft.Column([
                    ft.Text("Week End:", size=12, color=TEXT_SECONDARY),
                    ft.Text(timesheet.week_end.strftime("%d %b %Y") if timesheet.week_end else "N/A",
                            size=14, weight=ft.FontWeight.BOLD),
                ], spacing=2),
                ft.Column([
                    ft.Text("Total Hours:", size=12, color=TEXT_SECONDARY),
                    ft.Text(f"{timesheet.total_hours:.1f} hours" if timesheet.total_hours else "0 hours",
                            size=14, weight=ft.FontWeight.BOLD),
                ], spacing=2),
            ], spacing=30),
            bgcolor="white",
            padding=20,
            border_radius=10,
        )

        # Entries table - using ListView for scrolling
        entries_list = ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=10,
                padding=15,
                controls=[
                    self._create_time_entry_row(e) for e in entries
                ] if entries else [
                    ft.Container(
                        content=ft.Text("No time entries",
                                        size=12, color=TEXT_SECONDARY),
                        padding=10,
                    )
                ]
            ),
            bgcolor="white",
            padding=10,
            border_radius=10,
            expand=True,
        )

        # Notes
        notes_section = ft.Container()
        if timesheet.notes:
            notes_section = ft.Container(
                content=ft.Column([
                    ft.Text("Notes:", size=12, color=TEXT_SECONDARY),
                    ft.Text(timesheet.notes, size=14),
                ], spacing=5),
                bgcolor="white",
                padding=15,
                border_radius=10,
            )

        # Actions - Show approve/reject buttons ONLY for admin on submitted timesheets
        actions = ft.Row([])

        # Only show approve/reject buttons for ADMIN users on submitted timesheets
        if self._is_admin() and timesheet.status == "submitted":
            actions = ft.Row([
                ft.ElevatedButton("Approve", icon=ft.Icons.CHECK, bgcolor=SUCCESS, color="WHITE",
                                  on_click=lambda e: self._approve_timesheet(timesheet)),
                ft.ElevatedButton("Reject", icon=ft.Icons.CLOSE, bgcolor=ERROR, color="WHITE",
                                  on_click=lambda e: self._reject_timesheet(timesheet)),
                ft.TextButton("Back to List", on_click=self._back_to_list),
            ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
        else:
            actions = ft.Row([
                ft.TextButton("Back to List", on_click=self._back_to_list),
            ], alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                header_section,
                week_info,
                entries_list,
                notes_section,
                ft.Container(height=20),
                actions,
            ]),
            padding=25,
        )

    # ============ HELPER METHODS ============

    def _create_kpi_card(self, title, value, icon_name, color):
        """Create a KPI card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(icon_name, size=28, color=color),
                        bgcolor=f"{color}15",
                        width=50,
                        height=50,
                        border_radius=25,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Container(height=8),
                    ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=12, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                padding=15,
                width=150,
            ),
            elevation=1,
        )

    def _create_empty_state(self, title, subtitle, icon, action):
        """Create empty state"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=64, color="#ccc"),
                ft.Text(title, size=18, weight=ft.FontWeight.W_500,
                        color=TEXT_SECONDARY),
                ft.Text(subtitle, size=14, color="#999"),
                ft.Container(height=15),
                ft.ElevatedButton("Create Timesheet", icon=ft.Icons.ADD,
                                  bgcolor=PRIMARY, color="WHITE", on_click=action),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=50,
            alignment=ft.alignment.Alignment(0, 0),
        )

    def _get_timesheets(self):
        """Get all timesheets"""
        from sqlalchemy.orm import joinedload
        session = self._get_db()
        try:
            timesheets = session.query(Timesheet).options(
                joinedload(Timesheet.employee)
            ).order_by(Timesheet.week_start.desc()).all()
            return timesheets
        except Exception as e:
            print(f"Error getting timesheets: {e}")
            return []
        finally:
            session.close()

    def _get_time_entries(self, timesheet_id):
        """Get time entries for a timesheet"""
        session = self._get_db()
        try:
            entries = session.query(TimeEntry).filter_by(
                timesheet_id=timesheet_id).all()
            return entries
        except Exception as e:
            print(f"Error getting time entries: {e}")
            return []
        finally:
            session.close()

    def _get_projects(self):
        """Get all projects"""
        session = self._get_db()
        try:
            projects = session.query(Project).filter(
                Project.status == "active").all()
            return projects
        except Exception as e:
            print(f"Error getting projects: {e}")
            return []
        finally:
            session.close()

    def _get_employees(self):
        """Get all employees"""
        session = self._get_db()
        try:
            employees = session.query(Employee).filter(
                Employee.is_active == True).all()
            return employees
        except Exception as e:
            print(f"Error getting employees: {e}")
            return []
        finally:
            session.close()

    def _get_user_employee(self):
        """Get employee for current user"""
        user_id = self._get_user_info()
        if not user_id:
            return None

        session = self._get_db()
        try:
            employee = session.query(Employee).filter(
                Employee.user_id == user_id).first()
            return employee
        except Exception as e:
            print(f"Error getting user employee: {e}")
            return None
        finally:
            session.close()

    # ============ ACTIONS ============

    def _prev_week(self):
        """Previous week"""
        self.current_week_start = self.current_week_start - timedelta(days=7)
        self.refresh()

    def _next_week(self):
        """Next week"""
        self.current_week_start = self.current_week_start + timedelta(days=7)
        self.refresh()

    def _show_create_timesheet(self, e):
        """Show create timesheet view"""
        self.current_view = "create"
        self.refresh()

    def _edit_timesheet(self, timesheet):
        """Edit timesheet"""
        self.selected_timesheet = timesheet
        self.current_week_start = timesheet.week_start
        self.current_view = "create"
        self.refresh()

    def _view_timesheet(self, timesheet):
        """View timesheet details"""
        self.selected_timesheet = timesheet
        self.current_view = "view"
        self.refresh()

    def _back_to_list(self):
        """Back to timesheets list"""
        self.selected_timesheet = None
        self.current_view = "list"
        self.refresh()

    def _cancel_form(self):
        """Cancel form and go back"""
        self.current_view = "list"
        self.refresh()

    def _save_timesheet(self, status, notes_field=None):
        """Save timesheet with time entries"""
        session = self._get_db()
        try:
            # Get user employee
            employee = self._get_user_employee()
            if not employee:
                self._page.snack_bar = ft.SnackBar(
                    content=ft.Text("No employee profile found for this user"), bgcolor=ERROR)
                self._page.snack_bar.open = True
                self._page.update()
                return

            # Get week dates
            week_start = self.current_week_start
            week_end = week_start + timedelta(days=6)

            # Check if timesheet exists for this week
            existing = session.query(Timesheet).filter(
                Timesheet.employee_id == employee.id,
                Timesheet.week_start == week_start
            ).first()

            if existing:
                # Delete existing time entries
                session.query(TimeEntry).filter_by(
                    timesheet_id=existing.id).delete()
                timesheet = existing
                timesheet.status = status
            else:
                # Create new
                timesheet = Timesheet(
                    employee_id=employee.id,
                    week_start=week_start,
                    week_end=week_end,
                    total_hours=0,
                    status=status,
                    notes="",
                )
                session.add(timesheet)
                session.flush()

            # Calculate total hours and create time entries
            total_hours = 0.0

            # Get notes from field if provided
            notes = notes_field.value if notes_field else ""
            timesheet.notes = notes

            # Note: In Flet, we can't directly access form fields from here
            # The actual implementation would need a different approach
            # For now, save the basic timesheet

            # Update total hours
            timesheet.total_hours = total_hours
            timesheet.status = status

            session.commit()
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Timesheet saved as {status}! You can now add time entries."), bgcolor=SUCCESS)
            self._page.snack_bar.open = True
            self._page.update()
            self.current_view = "list"
            self.refresh()
        except Exception as ex:
            session.rollback()
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR)
            self._page.snack_bar.open = True
            self._page.update()
        finally:
            session.close()

    def _delete_timesheet(self, timesheet):
        """Delete timesheet"""
        def confirm_delete(e):
            session = self._get_db()
            try:
                # Delete entries first
                session.query(TimeEntry).filter_by(
                    timesheet_id=timesheet.id).delete()

                # Delete timesheet
                t = session.query(Timesheet).get(timesheet.id)
                if t:
                    session.delete(t)

                session.commit()
                self._page.snack_bar = ft.SnackBar(
                    content=ft.Text("Timesheet deleted"), bgcolor=SUCCESS)
                self._page.snack_bar.open = True
                self._page.update()
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR)
                self._page.snack_bar.open = True
                self._page.update()
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Timesheet"),
            content=ft.Text("Are you sure you want to delete this timesheet?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Delete", on_click=confirm_delete,
                                bgcolor=ERROR, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _approve_timesheet(self, timesheet):
        """Approve timesheet"""
        session = self._get_db()
        try:
            timesheet.status = "approved"
            timesheet.approved_at = datetime.utcnow()

            # Get current user as approver
            user_id = self._get_user_info()
            timesheet.approved_by_id = user_id

            session.commit()
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text("Timesheet approved"), bgcolor=SUCCESS)
            self._page.snack_bar.open = True
            self._page.update()
            self.refresh()
        except Exception as ex:
            session.rollback()
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR)
            self._page.snack_bar.open = True
            self._page.update()
        finally:
            session.close()

    def _reject_timesheet(self, timesheet):
        """Reject timesheet"""
        session = self._get_db()
        try:
            timesheet.status = "rejected"
            session.commit()
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text("Timesheet rejected"), bgcolor=SUCCESS)
            self._page.snack_bar.open = True
            self._page.update()
            self.refresh()
        except Exception as ex:
            session.rollback()
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR)
            self._page.snack_bar.open = True
            self._page.update()
        finally:
            session.close()

    def _go_back(self, e):
        """Navigate back to home screen"""
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)


def show_time_tracking(page, user):
    """Helper function to show time tracking"""
    page.clean()
    page.add(TimeTrackingScreen(page, user))
