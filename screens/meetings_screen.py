"""
Vernika HRA - Meetings Screen
Fixed version with working dialogs and calendar
Modern design with enhanced date visibility
"""

import flet as ft
from datetime import datetime, date, timedelta
from typing import List
import calendar as cal
from database.session_manager import get_db_session
from database.models import Meeting, MeetingParticipant, Employee
from database.operations import (
    create_meeting, get_meeting_participants,
    respond_to_meeting, cancel_meeting,
    get_employee_by_user_id
)
from components.dialogs import (
    show_meeting_schedule, show_meeting_details, show_date_meetings
)

# Color constants
PRIMARY = "#2E86AB"
PRIMARY_LIGHT = "#4DA8DA"
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
ERROR = "#F44336"
INFO = "#2196F3"
SURFACE = "#FFFFFF"
BACKGROUND = "#F5F5F5"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#666666"


class MeetingsScreen(ft.Container):
    def __init__(self, page, current_user=None):
        super().__init__()
        self._page = page
        self.current_user = current_user
        self.expand = True
        self.bgcolor = BACKGROUND

        self._current_date = datetime.now()
        self._current_view = "month"
        self._selected_date = None
        self._meetings = []

        self._is_admin = False
        self._user_id = None
        if isinstance(current_user, dict):
            self._is_admin = current_user.get('role') == 'admin'
            self._user_id = current_user.get('id')
        else:
            self._user_id = getattr(current_user, 'id', None)
            self._is_admin = getattr(current_user, 'role', None) == 'admin'

        self._employee_id = None
        self._load_employee()
        self._load_meetings()
        self.content = self._build_content()

    def _load_employee(self):
        if self._user_id:
            try:
                db = get_db_session()
                emp = get_employee_by_user_id(db, self._user_id)
                if emp:
                    self._employee_id = emp.id
                db.close()
            except Exception as e:
                print(f"Error loading employee: {e}")

    def _load_meetings(self):
        self._meetings = []
        try:
            from sqlalchemy.orm import joinedload
            db = get_db_session()
            if self._is_admin:
                meetings = db.query(Meeting).options(joinedload(
                    Meeting.organizer)).order_by(Meeting.start_time).all()
            else:
                meetings = db.query(Meeting).options(joinedload(Meeting.organizer)).join(MeetingParticipant).filter(
                    MeetingParticipant.user_id == self._user_id).order_by(Meeting.start_time).all()
            self._meetings = meetings
            db.close()
        except Exception as e:
            print(f"Error loading meetings: {e}")

    def _get_meetings_for_date(self, target_date: date) -> List[Meeting]:
        return [m for m in self._meetings if m.start_time.date() <= target_date <= m.end_time.date()]

    def _build_content(self):
        return ft.Container(
            content=ft.Column([self._build_header(), self._build_view_switcher(
            ), self._build_calendar()], expand=True, scroll=ft.ScrollMode.AUTO),
            padding=20, expand=True)

    def _build_header(self):
        return ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("Meetings & Calendar", size=24, weight=ft.FontWeight.BOLD, color=PRIMARY), ft.Text(
                    "Schedule and manage meetings", size=14, color="#666")]),
                ft.Container(expand=True),
                ft.ElevatedButton("Schedule Meeting", icon=ft.Icons.ADD, on_click=self._show_schedule_dialog,
                                  style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE"))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=20))

    def _build_view_switcher(self):
        return ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.CHEVRON_LEFT,
                              on_click=self._previous_period, icon_color=PRIMARY),
                ft.Text(self._get_period_label(), size=18,
                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT,
                              on_click=self._next_period, icon_color=PRIMARY),
                ft.Container(width=20),
                ft.ElevatedButton("Today", on_click=self._go_to_today, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="WHITE")),
                ft.Container(expand=True),
                ft.Container(content=ft.Row([
                    ft.ElevatedButton("Month", on_click=lambda e: self._change_view("month"), style=ft.ButtonStyle(
                        bgcolor=PRIMARY if self._current_view == "month" else SURFACE, color="WHITE" if self._current_view == "month" else TEXT_PRIMARY)),
                    ft.Container(width=5),
                    ft.ElevatedButton("Week", on_click=lambda e: self._change_view("week"), style=ft.ButtonStyle(
                        bgcolor=PRIMARY if self._current_view == "week" else SURFACE, color="WHITE" if self._current_view == "week" else TEXT_PRIMARY)),
                    ft.Container(width=5),
                    ft.ElevatedButton("List", on_click=lambda e: self._change_view("list"), style=ft.ButtonStyle(
                        bgcolor=PRIMARY if self._current_view == "list" else SURFACE, color="WHITE" if self._current_view == "list" else TEXT_PRIMARY))
                ], spacing=0))
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=15))

    def _get_period_label(self) -> str:
        if self._current_view == "month":
            return self._current_date.strftime("%B %Y")
        elif self._current_view == "week":
            start = self._current_date - \
                timedelta(days=self._current_date.weekday())
            end = start + timedelta(days=6)
            return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
        return self._current_date.strftime("%B %Y")

    def _previous_period(self, e):
        if self._current_view == "month":
            if self._current_date.month == 1:
                self._current_date = self._current_date.replace(
                    year=self._current_date.year - 1, month=12)
            else:
                self._current_date = self._current_date.replace(
                    month=self._current_date.month - 1)
        elif self._current_view == "week":
            self._current_date -= timedelta(days=7)
        else:
            if self._current_date.month == 1:
                self._current_date = self._current_date.replace(
                    year=self._current_date.year - 1, month=12)
            else:
                self._current_date = self._current_date.replace(
                    month=self._current_date.month - 1)
        self._refresh_view()

    def _next_period(self, e):
        if self._current_view == "month":
            if self._current_date.month == 12:
                self._current_date = self._current_date.replace(
                    year=self._current_date.year + 1, month=1)
            else:
                self._current_date = self._current_date.replace(
                    month=self._current_date.month + 1)
        elif self._current_view == "week":
            self._current_date += timedelta(days=7)
        else:
            if self._current_date.month == 12:
                self._current_date = self._current_date.replace(
                    year=self._current_date.year + 1, month=1)
            else:
                self._current_date = self._current_date.replace(
                    month=self._current_date.month + 1)
        self._refresh_view()

    def _go_to_today(self, e):
        self._current_date = datetime.now()
        self._refresh_view()

    def _change_view(self, view: str):
        self._current_view = view
        self._refresh_view()

    def _refresh_view(self):
        self.content = self._build_content()
        self.update()

    def _build_calendar(self):
        if self._current_view == "month":
            return self._build_month_view()
        elif self._current_view == "week":
            return self._build_week_view()
        return self._build_list_view()

    def _build_month_view(self):
        year = self._current_date.year
        month = self._current_date.month
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, cal.monthrange(year, month)[1])
        start_weekday = first_day.weekday()

        cell_width = 100

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        header_row = []
        for day_name in day_names:
            header_row.append(ft.Container(
                content=ft.Text(day_name, size=12, weight=ft.FontWeight.BOLD, color=PRIMARY if day_name not in [
                                "Sat", "Sun"] else "#999", text_align=ft.TextAlign.CENTER),
                width=cell_width, padding=5))

        calendar_rows = []
        current_row = []

        for _ in range(start_weekday):
            current_row.append(ft.Container(width=cell_width))

        day = 1
        while day <= last_day.day:
            current_date = datetime(year, month, day).date()
            meetings = self._get_meetings_for_date(current_date)
            is_today = current_date == datetime.now().date()
            is_weekend = current_date.weekday() >= 5

            day_cell = self._build_day_cell(
                current_date, meetings, is_today, is_weekend, cell_width)
            current_row.append(day_cell)

            if len(current_row) == 7:
                calendar_rows.append(ft.Row(current_row, spacing=2))
                current_row = []
            day += 1

        if current_row:
            while len(current_row) < 7:
                current_row.append(ft.Container(width=cell_width))
            calendar_rows.append(ft.Row(current_row, spacing=2))

        return ft.Container(
            content=ft.Column([ft.Row(header_row, spacing=2), ft.Container(
                height=5), ft.Column(calendar_rows, spacing=2)]),
            bgcolor=SURFACE, padding=15, border_radius=10)

    def _build_day_cell(self, current_date: date, meetings: List[Meeting], is_today: bool, is_weekend: bool, cell_width: int = 100) -> ft.Container:
        display_meetings = meetings[:3]
        more_count = len(meetings) - 3

        meeting_widgets = []
        for meeting in display_meetings:
            status_color = self._get_meeting_status_color(meeting.status)
            meeting_widgets.append(ft.Container(
                content=ft.Text(meeting.start_time.strftime(
                    "%H:%M") + " " + meeting.title[:12], size=9, color="WHITE", overflow=ft.TextOverflow.ELLIPSIS),
                bgcolor=status_color, padding=ft.padding.symmetric(horizontal=4, vertical=2), border_radius=3, margin=ft.margin.only(bottom=2)))

        if more_count > 0:
            meeting_widgets.append(
                ft.Text(f"+{more_count} more", size=9, color=PRIMARY))

        # Date number display - ensure it's always visible
        date_text_color = "WHITE" if is_today else (
            PRIMARY if not is_weekend else "#999")

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(str(current_date.day), size=14,
                                    weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL,
                                    color=date_text_color, text_align=ft.TextAlign.CENTER),
                    width=30, height=30, bgcolor=PRIMARY if is_today else "transparent",
                    border_radius=15, alignment=ft.alignment.Alignment(0, 0)),
                ft.Column(meeting_widgets, spacing=1)],
                spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=cell_width, height=80,
            bgcolor="#E3F2FD" if is_today else (
                SURFACE if not is_weekend else "#F5F5F5"),
            border_radius=5, padding=5, border=ft.border.all(1, "#E0E0E0" if not is_weekend else "#EEEEEE"),
            on_click=lambda e, d=current_date: self._on_date_click(d))

    def _build_week_view(self):
        start_date = self._current_date - \
            timedelta(days=self._current_date.weekday())
        week_days = [start_date + timedelta(days=i) for i in range(7)]

        day_columns = []
        for day in week_days:
            meetings = self._get_meetings_for_date(day.date())
            is_today = day.date() == datetime.now().date()
            meeting_cards = [self._create_meeting_card(m) for m in meetings]
            if not meeting_cards:
                meeting_cards = [ft.Text("No meetings", size=11, color="#999")]

            day_columns.append(ft.Container(content=ft.Column([
                ft.Container(content=ft.Column([
                    ft.Text(day.strftime("%a"), size=11, color="#666"),
                    ft.Text(str(day.day), size=20, weight=ft.FontWeight.BOLD, color="WHITE" if is_today else PRIMARY)],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=60, padding=10, bgcolor=PRIMARY if is_today else "#E3F2FD", border_radius=8),
                ft.Container(height=10),
                ft.Column(meeting_cards, spacing=5)], spacing=0),
                width=140, padding=10, bgcolor=SURFACE, border_radius=8))

        return ft.Container(content=ft.Row(day_columns, scroll=ft.ScrollMode.AUTO))

    def _build_list_view(self):
        year = self._current_date.year
        month = self._current_date.month
        month_meetings = [m for m in self._meetings if m.start_time.year ==
                          year and m.start_time.month == month]

        if not month_meetings:
            return ft.Container(content=ft.Column([
                ft.Icon(ft.Icons.VIDEO_CALL, size=64, color="#BDBDBD"),
                ft.Text("No meetings scheduled", size=16, color="#757575"),
                ft.Text("Click 'Schedule Meeting' to create one", size=12, color="#999")],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0), padding=50, bgcolor=SURFACE, border_radius=10)

        meetings_by_date = {}
        for meeting in month_meetings:
            date_key = meeting.start_time.date()
            if date_key not in meetings_by_date:
                meetings_by_date[date_key] = []
            meetings_by_date[date_key].append(meeting)

        sections = []
        for date_key in sorted(meetings_by_date.keys()):
            meetings = meetings_by_date[date_key]
            sections.append(ft.Column([
                ft.Text(date_key.strftime("%A, %B %d, %Y"), size=14,
                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Container(height=8),
                ft.Column([self._create_meeting_card(m)
                          for m in meetings], spacing=8),
                ft.Container(height=20)]))

        return ft.Container(content=ft.Column(sections, scroll=ft.ScrollMode.AUTO), bgcolor=SURFACE, padding=20, border_radius=10)

    def _create_meeting_card(self, meeting: Meeting) -> ft.Container:
        status_color = self._get_meeting_status_color(meeting.status)
        is_organizer = meeting.organizer_id == self._user_id
        organizer_name = getattr(
            meeting.organizer, 'username', 'Unknown') if meeting.organizer else "Unknown"
        desc_text = meeting.description[:80] + "..." if meeting.description and len(
            meeting.description) > 80 else meeting.description
        status_text = str(meeting.status.value.title()) if hasattr(
            meeting.status, 'value') else str(meeting.status).title()

        # Format date prominently
        meeting_date = meeting.start_time.strftime("%a, %b %d, %Y")

        return ft.Card(content=ft.Container(content=ft.Column([
            # Date row - PROMINENT
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=PRIMARY),
                    ft.Text(meeting_date, size=12,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                ]),
                margin=ft.margin.only(bottom=5),
            ),
            ft.Row([
                ft.Container(content=ft.Text(meeting.start_time.strftime("%H:%M"), size=14, weight=ft.FontWeight.BOLD, color="WHITE"),
                             bgcolor=status_color, padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=4),
                ft.Text(f"- {meeting.end_time.strftime('%H:%M')}",
                        size=12, color="#666"),
                ft.Container(expand=True),
                ft.Container(content=ft.Text(status_text, size=10, color="WHITE"),
                             bgcolor=status_color, padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=10)]),
            ft.Container(height=5),
            ft.Text(meeting.title, size=14, weight=ft.FontWeight.BOLD),
            ft.Text(desc_text, size=11,
                    color="#666") if desc_text else ft.Container(),
            ft.Container(height=5),
            ft.Row([ft.Icon(ft.Icons.PERSON, size=12, color="#999"),
                    ft.Text(f"Organizer: {organizer_name}",
                            size=10, color="#999"),
                    ft.Container(content=ft.Text("You", size=9, color=PRIMARY),
                    bgcolor="#E3F2FD", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=10) if is_organizer else ft.Container()]),
            ft.Container(height=8),
            ft.Row([
                ft.ElevatedButton("View", icon=ft.Icons.VISIBILITY, on_click=lambda e, m=meeting: self._show_meeting_details(m),
                                  style=ft.ButtonStyle(bgcolor=INFO, color="WHITE", padding=5), height=30),
                ft.ElevatedButton("Cancel", icon=ft.Icons.CLOSE, on_click=lambda e, m=meeting: self._cancel_meeting(m),
                                  style=ft.ButtonStyle(bgcolor=ERROR, color="WHITE", padding=5), height=30) if is_organizer else ft.Container()], spacing=10)], spacing=3), padding=12), elevation=1)

    def _get_meeting_status_color(self, status) -> str:
        status_str = str(status.value) if hasattr(
            status, 'value') else str(status)
        return {"scheduled": INFO, "in_progress": WARNING, "completed": SUCCESS, "cancelled": ERROR}.get(status_str, INFO)

    def _on_date_click(self, date: date):
        self._selected_date = date
        meetings = self._get_meetings_for_date(date)
        if meetings:
            self._show_date_meetings(date, meetings)
        else:
            self._show_schedule_dialog(default_date=date)

    def _show_date_meetings(self, date: date, meetings: List[Meeting]):
        """Show meetings for a specific date using the modern dialog."""

        def handle_add_meeting(e):
            self._show_schedule_dialog(default_date=date)

        def handle_view_meeting(meeting):
            self._show_meeting_details(meeting)

        def handle_close(e=None):
            self._close_all_dialogs()

        show_date_meetings(
            page=self._page,
            date=date,
            meetings=meetings,
            on_add_meeting=handle_add_meeting,
            on_view_meeting=handle_view_meeting,
            on_close=handle_close,
        )

    def _show_schedule_dialog(self, e=None, default_date: date = None):
        """Show the modern schedule meeting dialog."""

        def handle_save(meeting_data, event):
            if not meeting_data.get("title"):
                self._show_error("Meeting title is required!")
                return
            if not meeting_data.get("date"):
                self._show_error("Date is required!")
                return

            start_datetime = datetime.combine(
                meeting_data["date"], meeting_data["start_time"])
            end_datetime = datetime.combine(
                meeting_data["date"], meeting_data["end_time"])

            if end_datetime <= start_datetime:
                self._show_error("End time must be after start time!")
                return

            try:
                db = get_db_session()
                meeting = create_meeting(
                    db=db,
                    title=meeting_data["title"],
                    description=meeting_data.get("description", ""),
                    organizer_id=self._user_id,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    participant_ids=meeting_data.get("participant_ids", []),
                    is_recurring=meeting_data.get("is_recurring", False),
                    recurrence_pattern=meeting_data.get("recurrence_pattern")
                )
                db.close()
                self._show_success(
                    f"Meeting '{meeting_data['title']}' scheduled!")
                self._close_all_dialogs()
                self._load_meetings()
                self._refresh_view()
            except Exception as ex:
                self._show_error(f"Error creating meeting: {str(ex)}")
                print(f"Meeting creation error: {ex}")

        def handle_cancel(e=None):
            self._close_all_dialogs()

        show_meeting_schedule(
            page=self._page,
            on_save=handle_save,
            on_cancel=handle_cancel,
            default_date=default_date,
        )

    def _show_meeting_details(self, meeting: Meeting):
        """Show meeting details using the modern dialog."""
        participants = []
        try:
            db = get_db_session()
            participants = get_meeting_participants(db, meeting.id)
            db.close()
        except Exception as e:
            print(f"Error loading participants: {e}")

        is_organizer = meeting.organizer_id == self._user_id

        def handle_accept(e):
            self._respond_to_meeting(meeting, "accepted")

        def handle_decline(e):
            self._respond_to_meeting(meeting, "declined")

        def handle_cancel_meeting(e):
            self._cancel_meeting(meeting)

        def handle_close(e):
            self._close_all_dialogs()

        show_meeting_details(
            page=self._page,
            meeting=meeting,
            participants=participants,
            is_organizer=is_organizer,
            on_accept=handle_accept,
            on_decline=handle_decline,
            on_cancel_meeting=handle_cancel_meeting,
            on_close=handle_close,
        )

    def _respond_to_meeting(self, meeting: Meeting, response: str):
        try:
            db = get_db_session()
            respond_to_meeting(db, meeting.id, self._user_id, response)
            db.close()
            self._show_success(f"Meeting response: {response}")
            self._close_dialog()
            self._load_meetings()
            self._refresh_view()
        except Exception as e:
            self._show_error(f"Error responding to meeting: {str(e)}")

    def _cancel_meeting(self, meeting: Meeting):
        def confirm_cancel(e):
            try:
                db = get_db_session()
                cancel_meeting(db, meeting.id)
                db.close()
                self._show_success(f"Meeting '{meeting.title}' cancelled")
                self._close_dialog()
                self._load_meetings()
                self._refresh_view()
            except Exception as ex:
                self._show_error(f"Error cancelling meeting: {str(ex)}")

        dlg = ft.AlertDialog(title=ft.Text("Cancel Meeting?"),
                             content=ft.Text(
                                 f"Are you sure you want to cancel '{meeting.title}'?"),
                             actions=[ft.TextButton("No", on_click=self._close_dialog),
                                      ft.ElevatedButton("Yes, Cancel", on_click=confirm_cancel, style=ft.ButtonStyle(bgcolor=ERROR, color="WHITE"))],
                             actions_alignment=ft.MainAxisAlignment.END)
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_success(self, message):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, message):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=ERROR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _close_dialog(self, e=None):
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _close_all_dialogs(self, e=None):
        """Close all dialogs in the page overlay."""
        for overlay in self._page.overlay[:]:
            if isinstance(overlay, ft.AlertDialog):
                overlay.open = False
        self._page.update()


def show_meetings(page, user=None):
    page.clean()
    page.add(MeetingsScreen(page, user))
    page.update()
