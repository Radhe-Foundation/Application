"""
Vernika HRA - Meetings Screen
Industry-Level Human Resource Management System

This module provides the meeting scheduler and calendar functionality.
"""

from typing import List, Optional, Dict
import flet as ft
from datetime import datetime, timedelta, date
from database.connection import get_db_session
from database.models import Meeting, MeetingParticipant, User
from database.operations import create_meeting, get_user_meetings


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
ERROR = "#F44336"
INFO = "#2196F3"


class MeetingsScreen(ft.Container):
    """Meeting scheduler screen with calendar and scheduling"""

    def __init__(self, page, current_user=None):
        super().__init__()
        self._page = page
        self.current_user = current_user
        self.expand = True
        self.bgcolor = "#F5F5F5"

        # State
        self.meetings: List[Dict] = []
        self.selected_date = date.today()
        self.view_mode = "list"  # list or calendar

        # Load data
        self._load_meetings()

        # Build UI
        self.content = self._build_content()

    def _load_meetings(self):
        """Load meetings from database"""
        self.meetings = []
        try:
            db = get_db_session()

            # Get all meetings for the next 30 days
            from datetime import datetime
            now = datetime.now()
            end_date = now + timedelta(days=30)

            meetings = db.query(Meeting).filter(
                Meeting.start_time >= now,
                Meeting.start_time <= end_date
            ).order_by(Meeting.start_time).all()

            for meeting in meetings:
                # Get participant count
                participant_count = db.query(MeetingParticipant).filter(
                    MeetingParticipant.meeting_id == meeting.id
                ).count()

                self.meetings.append({
                    'id': meeting.id,
                    'title': meeting.title,
                    'description': meeting.description,
                    'start_time': meeting.start_time,
                    'end_time': meeting.end_time,
                    'organizer_id': meeting.organizer_id,
                    'status': meeting.status.value if hasattr(meeting.status, 'value') else str(meeting.status),
                    'participant_count': participant_count,
                    'meeting_link': meeting.meeting_link,
                })

            db.close()
        except Exception as e:
            print(f"Error loading meetings: {e}")

    def _build_content(self):
        """Build the main content"""
        return ft.Container(
            content=ft.Column([
                self._build_header(),
                self._build_toolbar(),
                self._build_meetings_list(),
            ], expand=True, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
        )

    def _build_header(self):
        """Build header"""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Meetings & Calendar", size=24,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Text("Schedule and manage meetings",
                            size=14, color="#666"),
                ]),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Schedule Meeting",
                    icon=ft.Icons.ADD,
                    on_click=self._show_schedule_dialog,
                    style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE"),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=20),
        )

    def _build_toolbar(self):
        """Build toolbar"""
        return ft.Container(
            content=ft.Row([
                ft.Text(f"Upcoming Meetings", size=18,
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.Text(f"Total: {len(self.meetings)} meetings",
                        size=14, color="#666"),
            ]),
            padding=ft.padding.only(bottom=15),
        )

    def _build_meetings_list(self):
        """Build meetings list"""
        if not self.meetings:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.EVENT_NOTE, size=64, color="#BDBDBD"),
                    ft.Text("No upcoming meetings", size=16, color="#757575"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Schedule First Meeting",
                        icon=ft.Icons.ADD,
                        on_click=self._show_schedule_dialog,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE"),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                padding=50,
            )

        # Group meetings by date
        meetings_by_date = {}
        for meeting in self.meetings:
            date_key = meeting['start_time'].strftime("%Y-%m-%d")
            if date_key not in meetings_by_date:
                meetings_by_date[date_key] = []
            meetings_by_date[date_key].append(meeting)

        # Build the list
        date_sections = []
        for date_key in sorted(meetings_by_date.keys()):
            meetings = meetings_by_date[date_key]
            display_date = datetime.strptime(
                date_key, "%Y-%m-%d").strftime("%A, %d %B %Y")

            meeting_cards = []
            for meeting in meetings:
                card = self._build_meeting_card(meeting)
                meeting_cards.append(card)

            date_sections.append(
                ft.Column([
                    ft.Text(display_date, size=14,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Container(height=8),
                    ft.Column(meeting_cards, spacing=10),
                    ft.Container(height=15),
                ])
            )

        return ft.Column(date_sections, spacing=0)

    def _build_meeting_card(self, meeting: Dict):
        """Build a meeting card"""
        start_time = meeting['start_time'].strftime("%H:%M")
        end_time = meeting['end_time'].strftime("%H:%M")

        # Status color
        status_colors = {
            'scheduled': INFO,
            'in_progress': WARNING,
            'completed': SUCCESS,
            'cancelled': ERROR,
        }
        status_color = status_colors.get(meeting['status'], INFO)

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    # Time indicator
                    ft.Container(
                        content=ft.Column([
                            ft.Text(start_time, size=16,
                                    weight=ft.FontWeight.BOLD, color=PRIMARY),
                            ft.Text(end_time, size=12, color="#666"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=60,
                    ),
                    ft.VerticalDivider(width=1, color="#E0E0E0"),
                    # Meeting details
                    ft.Column([
                        ft.Text(meeting['title'], size=16,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(meeting['description']
                                or "No description", size=12, color="#666"),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Icon(ft.Icons.PEOPLE, size=14, color="#666"),
                            ft.Text(
                                f"{meeting['participant_count']} participants", size=11, color="#666"),
                            ft.Container(width=15),
                            ft.Icon(ft.Icons.ACCESS_TIME,
                                    size=14, color="#666"),
                            ft.Text(f"{start_time} - {end_time}",
                                    size=11, color="#666"),
                        ]),
                    ], expand=True),
                    # Actions and status
                    ft.Column([
                        ft.Container(
                            content=ft.Text(meeting['status'].replace('_', ' ').title(),
                                            size=10, color="WHITE"),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(
                                horizontal=8, vertical=3),
                            border_radius=10,
                        ),
                        ft.Container(height=5),
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.VIDEO_CALL,
                                icon_color=SUCCESS,
                                tooltip="Join Meeting",
                                on_click=lambda e, m=meeting: self._join_meeting(
                                    m),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_color=PRIMARY,
                                tooltip="Edit",
                                on_click=lambda e, m=meeting: self._edit_meeting(
                                    m),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CANCEL,
                                icon_color=ERROR,
                                tooltip="Cancel",
                                on_click=lambda e, m=meeting: self._cancel_meeting(
                                    m),
                            ),
                        ], spacing=0),
                    ], horizontal_alignment=ft.CrossAxisAlignment.END),
                ], spacing=15),
                padding=15,
            ),
            elevation=1,
        )

    def _show_schedule_dialog(self, e=None):
        """Show schedule meeting dialog"""
        # Get all users for participants
        users = []
        try:
            db = get_db_session()
            users = db.query(User).filter(User.status == "active").all()
            db.close()
        except:
            pass

        title_field = ft.TextField(label="Meeting Title *", width=400)
        description_field = ft.TextField(
            label="Description", width=400, multiline=True, min_lines=3)

        # Date and time fields
        date_field = ft.TextField(
            label="Date (YYYY-MM-DD)", width=200, value=date.today().strftime("%Y-%m-%d"))
        start_time_field = ft.TextField(
            label="Start Time (HH:MM)", width=150, value="09:00")
        end_time_field = ft.TextField(
            label="End Time (HH:MM)", width=150, value="10:00")

        # Participants dropdown (simplified - just select one for now)
        participant_options = [ft.dropdown.Option(
            str(u.id), f"{u.username}") for u in users]
        participants_dropdown = ft.Dropdown(
            label="Add Participant",
            width=200,
            options=participant_options,
        )

        error_text = ft.Text("", color=ERROR, size=12, visible=False)

        def save_meeting(e):
            if not title_field.value:
                error_text.value = "Title is required!"
                error_text.visible = True
                self._page.update()
                return

            try:
                db = get_db_session()

                # Parse date and time
                meeting_date = datetime.strptime(
                    date_field.value, "%Y-%m-%d").date()
                start_time = datetime.strptime(
                    start_time_field.value, "%H:%M").time()
                end_time = datetime.strptime(
                    end_time_field.value, "%H:%M").time()

                start_datetime = datetime.combine(meeting_date, start_time)
                end_datetime = datetime.combine(meeting_date, end_time)

                # Get organizer ID
                organizer_id = 1  # Default admin
                if self.current_user and isinstance(self.current_user, dict):
                    organizer_id = self.current_user.get('id', 1)

                # Create meeting
                meeting = Meeting(
                    title=title_field.value,
                    description=description_field.value,
                    organizer_id=organizer_id,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    meeting_link=f"https://vernika.local/meeting/{organizer_id}_{int(start_datetime.timestamp())}"
                )
                db.add(meeting)
                db.flush()

                # Add participant if selected
                if participants_dropdown.value:
                    participant = MeetingParticipant(
                        meeting_id=meeting.id,
                        user_id=int(participants_dropdown.value)
                    )
                    db.add(participant)

                db.commit()
                db.close()

                self._show_success("Meeting scheduled successfully!")
                self._close_dialog()
                self._refresh()

            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self._page.update()
                print(f"Error scheduling meeting: {ex}")

        def close_dialog(e):
            self._close_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("Schedule Meeting"),
            content=ft.Column([
                title_field,
                description_field,
                ft.Row([date_field, start_time_field,
                       end_time_field], spacing=15),
                participants_dropdown,
                error_text,
            ], spacing=15),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Schedule", on_click=save_meeting, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="WHITE")),
            ]
        )

        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _join_meeting(self, meeting):
        """Join a meeting"""
        if meeting.get('meeting_link'):
            self._show_info(f"Meeting link: {meeting['meeting_link']}")
        else:
            self._show_info(
                "Meeting link not available yet. Use external video call apps.")

    def _edit_meeting(self, meeting):
        """Edit a meeting"""
        # Load meeting details
        db = get_db_session()
        try:
            meeting_obj = db.query(Meeting).filter(
                Meeting.id == meeting['id']).first()
            if not meeting_obj:
                self._show_info("Meeting not found")
                return

            # Get all users for participants
            users = db.query(User).filter(User.status == "active").all()

            title_field = ft.TextField(
                label="Meeting Title *", width=400, value=meeting_obj.title)
            description_field = ft.TextField(
                label="Description", width=400, multiline=True, min_lines=3,
                value=meeting_obj.description or ""
            )

            # Date and time fields
            date_field = ft.TextField(
                label="Date (YYYY-MM-DD)", width=200,
                value=meeting_obj.start_time.strftime("%Y-%m-%d"))
            start_time_field = ft.TextField(
                label="Start Time (HH:MM)", width=150,
                value=meeting_obj.start_time.strftime("%H:%M"))
            end_time_field = ft.TextField(
                label="End Time (HH:MM)", width=150,
                value=meeting_obj.end_time.strftime("%H:%M"))

            error_text = ft.Text("", color=ERROR, size=12, visible=False)

            def save_changes(e):
                if not title_field.value:
                    error_text.value = "Title is required!"
                    error_text.visible = True
                    self._page.update()
                    return

                try:
                    # Parse date and time
                    meeting_date = datetime.strptime(
                        date_field.value, "%Y-%m-%d").date()
                    start_time = datetime.strptime(
                        start_time_field.value, "%H:%M").time()
                    end_time = datetime.strptime(
                        end_time_field.value, "%H:%M").time()

                    meeting_obj.title = title_field.value
                    meeting_obj.description = description_field.value
                    meeting_obj.start_time = datetime.combine(
                        meeting_date, start_time)
                    meeting_obj.end_time = datetime.combine(
                        meeting_date, end_time)

                    db.commit()
                    db.close()

                    self._show_success("Meeting updated successfully!")
                    self._close_dialog()
                    self._refresh()

                except Exception as ex:
                    error_text.value = f"Error: {str(ex)}"
                    error_text.visible = True
                    self._page.update()

            def close_dialog(e):
                self._close_dialog()
                db.close()

            dialog = ft.AlertDialog(
                title=ft.Text("Edit Meeting"),
                content=ft.Column([
                    title_field,
                    description_field,
                    ft.Row([date_field, start_time_field,
                           end_time_field], spacing=15),
                    error_text,
                ], spacing=15),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dialog),
                    ft.ElevatedButton("Save Changes", on_click=save_changes, style=ft.ButtonStyle(
                        bgcolor=PRIMARY, color="WHITE")),
                ]
            )

            self._page.dialog = dialog
            dialog.open = True
            self._page.update()

        except Exception as e:
            print(f"Error loading meeting: {e}")
            self._show_info(f"Error: {str(e)}")
            db.close()

    def _cancel_meeting(self, meeting):
        """Cancel a meeting"""
        def confirm_cancel(e):
            db = get_db_session()
            try:
                meeting_obj = db.query(Meeting).filter(
                    Meeting.id == meeting['id']).first()
                if meeting_obj:
                    from database.models import MeetingStatus
                    meeting_obj.status = MeetingStatus.CANCELLED
                    db.commit()
                    self._show_success("Meeting cancelled successfully!")
                db.close()
            except Exception as ex:
                print(f"Error cancelling meeting: {ex}")
                self._show_info(f"Error: {str(ex)}")
                db.close()

            self._close_dialog()
            self._refresh()

        def close_dialog(e):
            self._close_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("Cancel Meeting"),
            content=ft.Text(
                f"Are you sure you want to cancel '{meeting['title']}'?"),
            actions=[
                ft.TextButton("No, Keep It", on_click=close_dialog),
                ft.ElevatedButton(
                    "Yes, Cancel",
                    on_click=confirm_cancel,
                    style=ft.ButtonStyle(bgcolor=ERROR, color="WHITE"),
                ),
            ],
            actions_alignment="end",
        )

        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _close_dialog(self):
        """Close dialog"""
        if self._page.dialog:
            self._page.dialog.open = False
        self._page.update()

    def _refresh(self):
        """Refresh the screen"""
        self._load_meetings()
        self.content = self._build_content()
        self._page.update()

    def _show_success(self, message):
        """Show success message"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_info(self, message):
        """Show info message"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=INFO)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_meetings(page, user=None):
    """Helper to show meetings screen"""
    page.clean()
    page.add(MeetingsScreen(page, user))
    page.update()
