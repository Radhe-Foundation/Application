"""
Vernika HRA - Dialog Components
Industry-Level Human Resource Management System

This module provides reusable dialog components for the application.
"""

from datetime import datetime, date
from typing import Optional, Callable, List
import flet as ft

# Import for Employee model
try:
    from database.models import Employee
    from database.session_manager import get_db_session
    from database.operations import get_all_employees
    HAS_EMPLOYEE_SUPPORT = True
except ImportError:
    HAS_EMPLOYEE_SUPPORT = False


class ConfirmDialog(ft.AlertDialog):
    """
    Confirmation dialog with title, content, and confirm/cancel buttons.
    """

    def __init__(
        self,
        title: str,
        content: str,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_color: str = "#2E86AB",
        cancel_color: str = "#6C757D",
    ):
        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Icon(ft.Icons.HELP_OUTLINE, size=48, color=confirm_color),
                ft.Container(height=10),
                ft.Text(content),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=self._handle_cancel,
                ),
                ft.ElevatedButton(
                    confirm_text,
                    on_click=self._handle_confirm,
                    bgcolor=confirm_color,
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

    def _handle_confirm(self, e: ft.ControlEvent):
        """Handle confirm action."""
        self.open = False
        self.page.update()
        if self._on_confirm:
            self._on_confirm(e)

    def _handle_cancel(self, e: ft.ControlEvent):
        """Handle cancel action."""
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)


class AlertDialog(ft.AlertDialog):
    """
    Alert dialog with a single OK button.
    """

    def __init__(
        self,
        title: str,
        content: str,
        on_ok: Optional[Callable] = None,
        ok_text: str = "OK",
    ):
        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Icon(ft.Icons.INFO, size=48, color="#2E86AB"),
                ft.Container(height=10),
                ft.Text(content),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            actions=[
                ft.ElevatedButton(
                    ok_text,
                    on_click=self._handle_ok,
                    bgcolor="#2E86AB",
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        self._on_ok = on_ok

    def _handle_ok(self, e: ft.ControlEvent):
        """Handle OK action."""
        self.open = False
        self.page.update()
        if self._on_ok:
            self._on_ok(e)


class InputDialog(ft.AlertDialog):
    """
    Dialog with input field.
    """

    def __init__(
        self,
        title: str,
        label: str,
        placeholder: str = "",
        default_value: str = "",
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        submit_text: str = "Submit",
        cancel_text: str = "Cancel",
        multiline: bool = False,
        password: bool = False,
        width: int = 400,
    ):
        self.input_field = ft.TextField(
            label=label,
            hint_text=placeholder,
            value=default_value,
            multiline=multiline,
            password=password,
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            width=width - 40,
        )

        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=self.input_field,
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=self._handle_cancel,
                ),
                ft.ElevatedButton(
                    submit_text,
                    on_click=self._handle_submit,
                    bgcolor="#2E86AB",
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._on_submit = on_submit
        self._on_cancel = on_cancel

    def _handle_submit(self, e: ft.ControlEvent):
        """Handle submit action."""
        value = self.input_field.value
        self.open = False
        self.page.update()
        if self._on_submit:
            self._on_submit(value, e)

    def _handle_cancel(self, e: ft.ControlEvent):
        """Handle cancel action."""
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)

    def get_value(self) -> str:
        """Get the input value."""
        return self.input_field.value or ""


class LoadingDialog(ft.AlertDialog):
    """
    Loading dialog with progress indicator.
    """

    def __init__(
        self,
        message: str = "Loading...",
        title: str = "Please Wait",
    ):
        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.ProgressRing(width=40, height=40, color="#2E86AB"),
                ft.Container(height=15),
                ft.Text(message),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            actions=[],
        )


class SelectionDialog(ft.AlertDialog):
    """
    Dialog for selecting from a list of options.
    """

    def __init__(
        self,
        title: str,
        options: list,
        on_select: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        display_property: str = "name",
        key_property: str = "id",
    ):
        self.options = options
        self._on_select = on_select
        self._on_cancel = on_cancel

        tiles = []
        for opt in options:
            key = opt.get(key_property, str(opt))
            display = opt.get(display_property, str(opt))
            tiles.append(
                ft.ListTile(
                    title=ft.Text(display),
                    on_click=lambda e, k=key: self._handle_select(k),
                )
            )

        list_view = ft.ListView(
            controls=tiles,
            height=300,
            width=400,
        )

        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=list_view,
                border_radius=8,
                border=ft.border.all(1, "#E0E0E0"),
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self._handle_cancel,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_select(self, key):
        """Handle selection."""
        self.open = False
        self.page.update()
        if self._on_select:
            self._on_select(key)

    def _handle_cancel(self, e: ft.ControlEvent):
        """Handle cancel."""
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)


class FormDialog(ft.AlertDialog):
    """
    Dialog for displaying forms with multiple fields.
    """

    def __init__(
        self,
        title: str,
        fields: list,
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        submit_text: str = "Submit",
        cancel_text: str = "Cancel",
        width: int = 400,
        height: int = 400,
    ):
        self.fields = fields

        form_fields = ft.Column(
            controls=fields,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=form_fields,
                width=width,
                height=height,
            ),
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=self._handle_cancel,
                ),
                ft.ElevatedButton(
                    submit_text,
                    on_click=self._handle_submit,
                    bgcolor="#2E86AB",
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._on_submit = on_submit
        self._on_cancel = on_cancel

    def _handle_submit(self, e: ft.ControlEvent):
        """Handle submit action."""
        values = {}
        for field in self.fields:
            if hasattr(field, 'value'):
                values[field.label if hasattr(
                    field, 'label') else 'field'] = field.value

        self.open = False
        self.page.update()
        if self._on_submit:
            self._on_submit(values, e)

    def _handle_cancel(self, e: ft.ControlEvent):
        """Handle cancel action."""
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)


def show_confirm(
    page: ft.Page,
    title: str,
    content: str,
    on_confirm: Callable,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
):
    """Show a confirmation dialog."""
    dialog = ConfirmDialog(
        title=title,
        content=content,
        on_confirm=on_confirm,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
    )
    page.dialog = dialog
    dialog.open = True
    page.update()


def show_alert(
    page: ft.Page,
    title: str,
    content: str,
    on_ok: Callable = None,
    ok_text: str = "OK",
):
    """Show an alert dialog."""
    dialog = AlertDialog(
        title=title,
        content=content,
        on_ok=on_ok,
        ok_text=ok_text,
    )
    page.dialog = dialog
    dialog.open = True
    page.update()


def show_input(
    page: ft.Page,
    title: str,
    label: str,
    on_submit: Callable,
    placeholder: str = "",
    default_value: str = "",
    submit_text: str = "Submit",
    cancel_text: str = "Cancel",
    multiline: bool = False,
):
    """Show an input dialog."""
    dialog = InputDialog(
        title=title,
        label=label,
        placeholder=placeholder,
        default_value=default_value,
        on_submit=on_submit,
        submit_text=submit_text,
        cancel_text=cancel_text,
        multiline=multiline,
    )
    page.dialog = dialog
    dialog.open = True
    page.update()


def show_loading(
    page: ft.Page,
    message: str = "Loading...",
) -> "LoadingDialog":
    """Show a loading dialog."""
    dialog = LoadingDialog(message=message)
    page.dialog = dialog
    dialog.open = True
    page.update()
    return dialog


def close_loading(page: ft.Page, dialog: "LoadingDialog" = None):
    """Close the loading dialog."""
    d = dialog or page.dialog
    if d:
        d.open = False
        page.update()


# ============================================================
# MEETING DIALOG COMPONENTS
# ============================================================


class MeetingScheduleDialog(ft.AlertDialog):
    """
    Modern dialog for scheduling a new meeting with enhanced UI.
    """

    def __init__(
        self,
        on_save: Callable,
        on_cancel: Callable = None,
        default_date: date = None,
        meeting: object = None,
        width: int = 550,
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self.meeting = meeting
        self.default_date = default_date or datetime.now()
        self.width = width

        self.title_field = ft.TextField(
            label="Meeting Title",
            hint_text="Enter meeting title",
            value=self.meeting.title if self.meeting else "",
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            prefix_icon=ft.Icons.TITLE,
            width=width - 60,
        )

        self.description_field = ft.TextField(
            label="Description",
            hint_text="Enter meeting description",
            value=self.meeting.description if self.meeting else "",
            multiline=True,
            min_lines=3,
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            prefix_icon=ft.Icons.DESCRIPTION,
            width=width - 60,
        )

        self.date_field = ft.TextField(
            label="Date",
            hint_text="YYYY-MM-DD",
            value=self.default_date.strftime("%Y-%m-%d"),
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            prefix_icon=ft.Icons.CALENDAR_TODAY,
            width=150,
        )

        self.start_time_field = ft.TextField(
            label="Start Time",
            hint_text="HH:MM",
            value=self.meeting.start_time.strftime(
                "%H:%M") if self.meeting else "09:00",
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            prefix_icon=ft.Icons.ACCESS_TIME,
            width=120,
        )

        self.end_time_field = ft.TextField(
            label="End Time",
            hint_text="HH:MM",
            value=self.meeting.end_time.strftime(
                "%H:%M") if self.meeting else "10:00",
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            prefix_icon=ft.Icons.ACCESS_TIME,
            width=120,
        )

        # Employee selection components
        self.employee_checkboxes = {}
        self.employee_list_container = ft.Container()

        self.is_recurring_switch = ft.Switch(
            label="Recurring Meeting",
            value=False,
        )

        self.recurrence_dropdown = ft.Dropdown(
            label="Recurrence Pattern",
            width=180,
            options=[
                ft.dropdown.Option("daily", "Daily"),
                ft.dropdown.Option("weekly", "Weekly"),
                ft.dropdown.Option("monthly", "Monthly"),
            ],
            visible=False,
        )

        def toggle_recurrence(e):
            self.recurrence_dropdown.visible = self.is_recurring_switch.value
            self.update()

        self.is_recurring_switch.on_change = toggle_recurrence

        # Load employees if available
        if HAS_EMPLOYEE_SUPPORT:
            self._load_employees()
        else:
            # Fallback to text field if employee support not available
            self.participants_field = ft.TextField(
                label="Participants",
                hint_text="Enter participant IDs (comma-separated)",
                value="",
                border_radius=8,
                border_color="#2E86AB",
                focused_border_color="#2E86AB",
                prefix_icon=ft.Icons.PEOPLE,
                width=width - 60,
            )

    def _load_employees(self):
        """Load employees for selection."""
        self.employees = []
        try:
            if HAS_EMPLOYEE_SUPPORT:
                db = get_db_session()
                self.employees = get_all_employees(db, limit=100)
                db.close()
        except Exception as e:
            print(f"Error loading employees: {e}")
            self.employees = []

        # Create checkbox list for employee selection
        checkbox_items = []
        for emp in self.employees:
            full_name = f"{emp.first_name} {emp.last_name}"
            checkbox = ft.Checkbox(
                label=full_name,
                value=False,
            )
            self.employee_checkboxes[emp.id] = checkbox
            checkbox_items.append(checkbox)

        if not checkbox_items:
            checkbox_items = [
                ft.Text("No employees available", size=12, color="#999")]

        # Wrap in scrollable container
        self.employee_list_container = ft.Container(
            content=ft.Column(checkbox_items, spacing=5),
            height=150,
            width=400,
            border=ft.border.all(1, "#E0E0E0"),
            border_radius=8,
            padding=10,
        )

        form_content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.VIDEO_CALL, color="#2E86AB", size=24),
                    ft.Text(
                        "Schedule Meeting" if not self.meeting else "Edit Meeting",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="#2E86AB",
                    ),
                ]),
                margin=ft.margin.only(bottom=10),
            ),
            self.title_field,
            ft.Container(height=5),
            self.description_field,
            ft.Container(height=5),
            ft.Text("Date & Time", size=14,
                    weight=ft.FontWeight.W_500, color="#666"),
            ft.Container(height=3),
            ft.Row(
                [self.date_field, self.start_time_field, self.end_time_field],
                spacing=10,
            ),
            ft.Container(height=10),
            ft.Text("Participants", size=14,
                    weight=ft.FontWeight.W_500, color="#666"),
            ft.Container(height=3),
            # Show employee checkboxes if available, otherwise show text field
            self.employee_list_container if HAS_EMPLOYEE_SUPPORT and hasattr(
                self, 'employee_list_container') else self.participants_field,
            ft.Container(height=10),
            ft.Container(
                content=ft.Row(
                    [self.is_recurring_switch, self.recurrence_dropdown],
                    spacing=10,
                ),
                visible=False,
            ),
        ], spacing=2, scroll=ft.ScrollMode.AUTO)

        super().__init__(
            modal=True,
            title=ft.Text(
                "Schedule Meeting" if not self.meeting else "Edit Meeting",
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=form_content,
                width=self.width,
                height=420,
                padding=10,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self._handle_cancel_action,
                ),
                ft.ElevatedButton(
                    "Schedule" if not self.meeting else "Update",
                    on_click=self._handle_save,
                    bgcolor="#2E86AB",
                    color="#FFFFFF",
                    icon=ft.Icons.CHECK,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_save(self, e: ft.ControlEvent):
        if not self.title_field.value:
            self._show_validation_error("Meeting title is required!")
            return

        if not self.date_field.value:
            self._show_validation_error("Date is required!")
            return

        try:
            meeting_date = datetime.strptime(
                self.date_field.value, "%Y-%m-%d").date()
        except ValueError:
            self._show_validation_error("Invalid date format! Use YYYY-MM-DD")
            return

        try:
            start_time = datetime.strptime(
                self.start_time_field.value, "%H:%M").time()
            end_time = datetime.strptime(
                self.end_time_field.value, "%H:%M").time()
        except ValueError:
            self._show_validation_error("Invalid time format! Use HH:MM")
            return

        start_datetime = datetime.combine(meeting_date, start_time)
        end_datetime = datetime.combine(meeting_date, end_time)

        if end_datetime <= start_datetime:
            self._show_validation_error("End time must be after start time!")
            return

        participant_ids = []
        if HAS_EMPLOYEE_SUPPORT and hasattr(self, 'employee_checkboxes') and self.employee_checkboxes:
            # Get selected employee IDs from checkboxes
            for emp_id, checkbox in self.employee_checkboxes.items():
                if checkbox.value:
                    participant_ids.append(emp_id)
        elif hasattr(self, 'participants_field') and self.participants_field.value:
            # Fallback to text field
            try:
                participant_ids = [
                    int(pid.strip()) for pid in self.participants_field.value.split(',')
                    if pid.strip()
                ]
            except ValueError:
                self._show_validation_error("Invalid participant IDs!")
                return

        meeting_data = {
            "title": self.title_field.value,
            "description": self.description_field.value,
            "date": meeting_date,
            "start_time": start_time,
            "end_time": end_time,
            "participant_ids": participant_ids,
            "is_recurring": self.is_recurring_switch.value,
            "recurrence_pattern": self.recurrence_dropdown.value if self.is_recurring_switch.value else None,
        }

        self.open = False
        self.page.update()
        if self._on_save:
            self._on_save(meeting_data, e)

    def _handle_cancel_action(self, e: ft.ControlEvent):
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)

    def _show_validation_error(self, message: str):
        snack = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.ERROR, color="white", size=20),
                ft.Text(message, color="white"),
            ]),
            bgcolor="#F44336",
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()


class MeetingDetailsDialog(ft.AlertDialog):
    """
    Modern dialog for displaying meeting details with enhanced UI.
    """

    def __init__(
        self,
        meeting: object,
        participants: list,
        is_organizer: bool,
        on_accept: Callable = None,
        on_decline: Callable = None,
        on_cancel_meeting: Callable = None,
        on_close: Callable = None,
        width: int = 500,
    ):
        self.meeting = meeting
        self.participants = participants
        self.is_organizer = is_organizer
        self._on_accept = on_accept
        self._on_decline = on_decline
        self._on_cancel_meeting = on_cancel_meeting
        self._on_close = on_close

        status_str = str(meeting.status.value) if hasattr(
            meeting.status, 'value') else str(meeting.status)
        status_color = {
            "scheduled": "#2196F3",
            "in_progress": "#FF9800",
            "completed": "#4CAF50",
            "cancelled": "#F44336",
        }.get(status_str, "#2196F3")

        status_text = str(meeting.status.value.title()) if hasattr(
            meeting.status, 'value') else str(meeting.status).title()

        date_str = meeting.start_time.strftime("%A, %B %d, %Y")
        time_str = f"{meeting.start_time.strftime('%H:%M')} - {meeting.end_time.strftime('%H:%M')}"

        participant_widgets = []
        for p in self.participants:
            status_color_p = {
                "pending": "#FF9800",
                "accepted": "#4CAF50",
                "declined": "#F44336",
                "tentative": "#2196F3",
            }.get(p.status, "#999")

            username = getattr(p.user, 'username',
                               'Unknown') if p.user else "Unknown"
            participant_widgets.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(
                                username[0].upper(), size=12, weight=ft.FontWeight.BOLD, color="white"),
                            width=28,
                            height=28,
                            border_radius=14,
                            bgcolor="#2E86AB",
                        ),
                        ft.Text(username, size=13, expand=True),
                        ft.Container(
                            content=ft.Text(p.status.title(),
                                            size=10, color="white"),
                            bgcolor=status_color_p,
                            padding=ft.padding.symmetric(
                                horizontal=8, vertical=3),
                            border_radius=10,
                        ),
                    ], spacing=10),
                    padding=8,
                    bgcolor="#F5F5F5",
                    border_radius=8,
                )
            )

        if not participant_widgets:
            participant_widgets = [
                ft.Container(
                    content=ft.Text("No participants", size=12, color="#999"),
                    padding=15,
                )
            ]

        desc_widget = ft.Container()
        if meeting.description:
            desc_widget = ft.Container(
                content=ft.Column([
                    ft.Text("Description", size=12,
                            weight=ft.FontWeight.BOLD, color="#666"),
                    ft.Text(meeting.description, size=12, color="#333"),
                ], spacing=5),
                padding=15,
                bgcolor="#F8F9FA",
                border_radius=8,
                margin=ft.margin.only(bottom=10),
            )

        content = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    meeting.start_time.strftime("%d"),
                                    size=36,
                                    weight=ft.FontWeight.BOLD,
                                    color="white",
                                ),
                                ft.Text(
                                    meeting.start_time.strftime("%b %Y"),
                                    size=14,
                                    color="white",
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor=status_color,
                            width=80,
                            height=80,
                            border_radius=12,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Container(height=15),
                        ft.Text(meeting.title, size=20,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY,
                                    size=14, color="#666"),
                            ft.Text(date_str, size=12, color="#666"),
                        ]),
                        ft.Container(height=3),
                        ft.Row([
                            ft.Icon(ft.Icons.ACCESS_TIME,
                                    size=14, color="#666"),
                            ft.Text(time_str, size=12, color="#666"),
                        ]),
                        ft.Container(height=8),
                        ft.Container(
                            content=ft.Text(
                                status_text, size=11, color="white"),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(
                                horizontal=10, vertical=4),
                            border_radius=12,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor="#FFFFFF",
                    border_radius=12,
                    margin=ft.margin.only(bottom=15),
                    border=ft.border.all(1, "#E0E0E0"),
                ),
                desc_widget,
                ft.Text("Participants", size=14,
                        weight=ft.FontWeight.BOLD, color="#333"),
                ft.Container(height=5),
                ft.Column(participant_widgets, spacing=8),
            ], scroll=ft.ScrollMode.AUTO),
            width=width,
            height=500,
            padding=10,
        )

        actions = []

        if not self.is_organizer:
            actions.append(
                ft.ElevatedButton(
                    "Decline",
                    on_click=self._handle_decline,
                    bgcolor="#F44336",
                    color="white",
                    icon=ft.Icons.CLOSE,
                )
            )
            actions.append(
                ft.ElevatedButton(
                    "Accept",
                    on_click=self._handle_accept,
                    bgcolor="#4CAF50",
                    color="white",
                    icon=ft.Icons.CHECK,
                )
            )

        if self.is_organizer:
            actions.append(
                ft.ElevatedButton(
                    "Cancel Meeting",
                    on_click=self._handle_cancel_meeting,
                    bgcolor="#F44336",
                    color="white",
                    icon=ft.Icons.CANCEL,
                )
            )

        actions.append(
            ft.TextButton(
                "Close",
                on_click=self._handle_close,
            )
        )

        super().__init__(
            modal=True,
            title=ft.Text("Meeting Details", weight=ft.FontWeight.BOLD),
            content=content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_accept(self, e: ft.ControlEvent):
        self.open = False
        self.page.update()
        if self._on_accept:
            self._on_accept(e)

    def _handle_decline(self, e: ft.ControlEvent):
        self.open = False
        self.page.update()
        if self._on_decline:
            self._on_decline(e)

    def _handle_cancel_meeting(self, e: ft.ControlEvent):
        self.open = False
        self.page.update()
        if self._on_cancel_meeting:
            self._on_cancel_meeting(e)

    def _handle_close(self, e: ft.ControlEvent):
        self.open = False
        self.page.update()
        if self._on_close:
            self._on_close(e)


class DateMeetingsDialog(ft.AlertDialog):
    """
    Modern dialog showing meetings for a specific date.
    """

    def __init__(
        self,
        date: date,
        meetings: list,
        on_add_meeting: Callable = None,
        on_view_meeting: Callable = None,
        on_close: Callable = None,
        width: int = 550,
    ):
        self.date = date
        self.meetings = meetings
        self._on_add_meeting = on_add_meeting
        self._on_view_meeting = on_view_meeting
        self._on_close = on_close

        date_str = date.strftime("%A, %B %d, %Y")

        meeting_widgets = []
        for meeting in self.meetings:
            status_color = {
                "scheduled": "#2196F3",
                "in_progress": "#FF9800",
                "completed": "#4CAF50",
                "cancelled": "#F44336",
            }.get(str(meeting.status.value) if hasattr(meeting.status, 'value') else str(meeting.status), "#2196F3")

            organizer_name = getattr(
                meeting.organizer, 'username', 'Unknown') if meeting.organizer else "Unknown"
            desc_text = meeting.description[:60] + "..." if meeting.description and len(
                meeting.description) > 60 else meeting.description

            meeting_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(
                                meeting.start_time.strftime("%H:%M"),
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="white",
                            ),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(
                                horizontal=10, vertical=6),
                            border_radius=6,
                        ),
                        ft.Text(
                            f"- {meeting.end_time.strftime('%H:%M')}", size=12, color="#666"),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(
                                str(meeting.status.value.title()) if hasattr(
                                    meeting.status, 'value') else str(meeting.status).title(),
                                size=10,
                                color="white",
                            ),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(
                                horizontal=8, vertical=3),
                            border_radius=10,
                        ),
                    ]),
                    ft.Container(height=8),
                    ft.Text(meeting.title, size=15, weight=ft.FontWeight.BOLD),
                    ft.Text(desc_text, size=11,
                            color="#666") if desc_text else ft.Container(),
                    ft.Container(height=5),
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON, size=12, color="#999"),
                        ft.Text(
                            f"Organizer: {organizer_name}", size=10, color="#999"),
                    ]),
                    ft.Container(height=8),
                    ft.ElevatedButton(
                        "View Details",
                        icon=ft.Icons.VISIBILITY,
                        on_click=lambda e, m=meeting: self._handle_view(m),
                        style=ft.ButtonStyle(
                            bgcolor="#2196F3", color="white", padding=8),
                        height=32,
                    ),
                ], spacing=5),
                padding=15,
                bgcolor="white",
                border_radius=10,
                border=ft.border.all(1, "#E0E0E0"),
            )
            meeting_widgets.append(meeting_card)

        if not meeting_widgets:
            meeting_widgets = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.EVENT_BUSY, size=48, color="#BDBDBD"),
                        ft.Text("No meetings scheduled",
                                size=14, color="#757575"),
                        ft.Text("Click 'Add Meeting' to create one",
                                size=12, color="#999"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30,
                )
            ]

        content = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(date_str, size=18,
                                    weight=ft.FontWeight.BOLD, color="#2E86AB"),
                            ft.Text(f"{len(self.meetings)} meeting(s)",
                                    size=12, color="#666"),
                        ], spacing=2),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Add Meeting",
                            icon=ft.Icons.ADD,
                            on_click=self._handle_add_meeting,
                            style=ft.ButtonStyle(
                                bgcolor="#2E86AB", color="white"),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=15,
                    bgcolor="#E3F2FD",
                    border_radius=10,
                ),
                ft.Container(height=15),
                ft.Column(meeting_widgets, spacing=12),
            ], scroll=ft.ScrollMode.AUTO),
            width=width,
            height=450,
            padding=10,
        )

        super().__init__(
            modal=True,
            title=ft.Text(f"Meetings - {date_str}", weight=ft.FontWeight.BOLD),
            content=content,
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=self._handle_close,
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_add_meeting(self, e: ft.ControlEvent):
        self.open = False
        self.page.update()
        if self._on_add_meeting:
            self._on_add_meeting(e)

    def _handle_view(self, meeting):
        self.open = False
        self.page.update()
        if self._on_view_meeting:
            self._on_view_meeting(meeting)

    def _handle_close(self, e: ft.ControlEvent):
        self.open = False
        self.page.update()
        if self._on_close:
            self._on_close(e)


# Helper functions for meeting dialogs

def show_meeting_schedule(
    page: ft.Page,
    on_save: Callable,
    on_cancel: Callable = None,
    default_date: date = None,
    meeting: object = None,
) -> MeetingScheduleDialog:
    """Show the meeting schedule dialog."""
    dialog = MeetingScheduleDialog(
        on_save=on_save,
        on_cancel=on_cancel,
        default_date=default_date,
        meeting=meeting,
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
    return dialog


def show_meeting_details(
    page: ft.Page,
    meeting: object,
    participants: list,
    is_organizer: bool,
    on_accept: Callable = None,
    on_decline: Callable = None,
    on_cancel_meeting: Callable = None,
    on_close: Callable = None,
) -> MeetingDetailsDialog:
    """Show the meeting details dialog."""
    dialog = MeetingDetailsDialog(
        meeting=meeting,
        participants=participants,
        is_organizer=is_organizer,
        on_accept=on_accept,
        on_decline=on_decline,
        on_cancel_meeting=on_cancel_meeting,
        on_close=on_close,
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
    return dialog


def show_date_meetings(
    page: ft.Page,
    date: date,
    meetings: list,
    on_add_meeting: Callable = None,
    on_view_meeting: Callable = None,
    on_close: Callable = None,
) -> DateMeetingsDialog:
    """Show meetings for a specific date."""
    dialog = DateMeetingsDialog(
        date=date,
        meetings=meetings,
        on_add_meeting=on_add_meeting,
        on_view_meeting=on_view_meeting,
        on_close=on_close,
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
    return dialog
