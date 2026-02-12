"""
Vernika HRA - Enhanced Chat Screen
Multi-user chat with contacts, groups, meetings, email, and document sharing
Outlook + Teams combination

Fixed version with real database integration for multi-user support
"""

from database.operations import (
    get_all_users, get_user_groups, get_all_user_permissions,
    send_chat_message, get_direct_messages, get_group_messages,
    mark_chat_messages_as_read, create_chat_group, add_group_member,
    send_email, get_user_emails, create_meeting, get_user_meetings,
    create_chat_group as db_create_chat_group,
    get_group_by_id, get_group_members, get_user_by_id,
    get_meeting_participants, get_user_documents, upload_document,
    EmailCategory, MeetingStatus
)
from database.models import User, UserStatus, MessageType
from database.connection import get_db_session
import flet as ft
from flet import Container, Column, Row, Text, IconButton, TextField, ElevatedButton, Card, CircleAvatar, Icon, Divider, Badge, ListView, ScrollMode, icons, padding, margin, alignment, border_radius, AlertDialog, SnackBar, Checkbox, Dropdown, dropdown, Stack, Border, BorderSide, CrossAxisAlignment, MainAxisAlignment, FontWeight, TextAlign
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Get colors from ft.Colors - Using hex values for compatibility with newer Flet versions
PRIMARY = "#2E86AB"
PRIMARY_CONTAINER = "#2E86AB"
ON_PRIMARY_CONTAINER = ft.Colors.ON_PRIMARY_CONTAINER
SECONDARY = "#A23B72"
SURFACE = ft.Colors.SURFACE
SURFACE_VARIANT = "#E7E0EC"
ON_SURFACE_VARIANT = "#49454F"
BACKGROUND = "#FAFAFA"
ON_BACKGROUND = "#1C1B1F"
ON_PRIMARY = ft.Colors.ON_PRIMARY
GREEN = "#4CAF50"
RED = "#F44336"
BLUE = "#2196F3"
BLUE_400 = "#2196F3"
BLUE_GREY_50 = "#ECEFF1"
PURPLE_400 = "#AB47BC"
GREY = ft.Colors.GREY
GREY_400 = "#9E9E9E"
GREY_500 = "#757575"
GREY_600 = "#616161"
GREY_300 = "#E0E0E0"
GREY_700 = "#616161"
GREY_200 = ft.Colors.GREY_200
AMBER = ft.Colors.AMBER
CYAN = ft.Colors.CYAN
INDIGO = ft.Colors.INDIGO
LIME = ft.Colors.LIME
ORANGE = ft.Colors.ORANGE
PINK = ft.Colors.PINK
TEAL = ft.Colors.TEAL
YELLOW = ft.Colors.YELLOW
BROWN = ft.Colors.BROWN
BLUE_GREY = "#607D8B"
OUTLINE_VARIANT = "#CAC4D0"
WHITE = ft.Colors.WHITE
PURPLE = ft.Colors.PURPLE


@dataclass
class ChatMessage:
    sender_id: int
    sender_name: str
    content: str
    timestamp: Optional[datetime] = None
    is_own: bool = False
    is_group: bool = False
    group_name: Optional[str] = None


@dataclass
class Contact:
    id: int
    username: str
    email: str
    role: str
    status: str = "offline"
    last_seen: object = None


@dataclass
class Group:
    id: int
    name: str
    created_by: int
    member_ids: List[int]
    member_names: List[str]


@dataclass
class Meeting:
    id: int
    title: str
    description: str
    organizer: str
    start_time: datetime
    end_time: datetime
    participants: List[str]
    status: str = "scheduled"


@dataclass
class Email:
    id: int
    sender: str
    subject: str
    body: str
    category: str
    recipients: List[str]
    created_at: datetime
    is_read: bool = False
    is_sent: bool = False


@dataclass
class Document:
    id: int
    name: str
    file_type: str
    uploaded_by: str
    created_at: datetime
    size: str = ""


class ChatMessageControl(ft.Row):
    """Custom chat message bubble"""

    def __init__(self, message: ChatMessage):
        super().__init__()
        self.vertical_alignment = CrossAxisAlignment.START

        avatar = CircleAvatar(
            content=Text(message.sender_name[:1].upper() if message.sender_name else "U",
                         size=14, weight=FontWeight.BOLD),
            color=WHITE,
            bgcolor=self._get_color(message.sender_name),
            radius=18,
        )

        bubble_bg = PRIMARY_CONTAINER if message.is_own else SURFACE_VARIANT
        bubble_color = ON_PRIMARY_CONTAINER if message.is_own else ON_SURFACE_VARIANT

        message_col = Column(tight=True, spacing=2, controls=[
            Row(controls=[
                Text(f"{message.sender_name}" +
                     (f" ({message.group_name})" if message.is_group else ""),
                     size=11, weight=FontWeight.BOLD,
                     color=PRIMARY if message.is_group else GREY_600)
            ]) if not message.is_own else Container(),
            Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=bubble_bg,
                border_radius=border_radius.only(
                    top_left=0 if not message.is_own else 12,
                    top_right=12,
                    bottom_left=12,
                    bottom_right=12 if not message.is_own else 0
                ),
                content=Text(message.content, color=bubble_color,
                             selectable=True, size=14)
            ),
            Text(message.timestamp.strftime("%H:%M") if message.timestamp else "",
                 size=10, color=GREY_500, text_align=TextAlign.RIGHT)
        ])

        if message.is_own:
            self.controls = [Container(expand=True),
                             message_col, Container(width=8), avatar]
        else:
            self.controls = [avatar, Container(
                width=8), message_col, Container(expand=True)]

    def _get_color(self, name: str) -> str:
        colors_list = [AMBER, BLUE, BLUE_GREY, BROWN, CYAN, GREEN, INDIGO, LIME,
                       ORANGE, PINK, PURPLE, RED, TEAL, YELLOW]
        return colors_list[hash(name) % len(colors_list)]


class ChatScreen(ft.Container):
    """Main chat screen with contacts, groups, meetings, email, and documents"""

    def __init__(self, page: ft.Page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = SURFACE

        if isinstance(user, dict):
            self.current_user_id = user.get('id', 0)
            self.current_username = user.get('username', 'User')
            self.current_user_email = user.get(
                'email', f'{user.get("username", "user")}@vernika.local')
        else:
            self.current_user_id = getattr(user, 'id', 0)
            self.current_username = getattr(user, 'username', 'User')
            self.current_user_email = getattr(
                user, 'email', f'{getattr(user, "username", "user")}@vernika.local')

        self._load_permissions()
        self.contacts: List[Contact] = []
        self.groups: List[Group] = []
        self.messages: List[ChatMessage] = []
        self.meetings: List[Meeting] = []
        self.emails: List[Email] = []
        self.documents: List[Document] = []
        self.selected_contact: Optional[Contact] = None
        self.selected_group: Optional[Group] = None
        self.current_tab = "chat"
        self.chat_tab = "contacts"  # Track sub-tab for chat view

        # Store references to UI components for efficient updates
        self._main_area_ref: Optional[Container] = None
        self._nav_items: List[Container] = []

        self._load_contacts()
        self._load_groups()
        self._load_meetings()
        self._load_emails()
        self._load_documents()
        self._load_sample_messages()

        # Build UI once and store references
        self._build_ui()

        # --- File picker for document/chat file sharing ---
        # File picker compatibility - safely initialize
        self._file_picker = None
        try:
            # Check if FilePicker is available in this Flet version
            if hasattr(ft, 'FilePicker'):
                self._file_picker = ft.FilePicker(
                    on_result=self._on_file_selected)
                self._page.overlay.append(self._file_picker)
                print("✓ FilePicker initialized successfully")
            else:
                print("⚠ FilePicker not available in this Flet version")
        except Exception as ex:
            print(f"⚠ FilePicker initialization failed: {ex}")
            self._file_picker = None

        # --- Call log/history UI ---
        self.call_history = []

    def _on_file_selected(self, e):
        """Handle file selected from picker and upload."""
        if not e.files or len(e.files) == 0:
            self._show_snackbar("No file selected.")
            return
        file = e.files[0]
        # Upload file and attach to chat
        self._show_snackbar(f"Selected file: {file.name}")
        # TODO: Implement actual file upload to server

    def _attach_file(self, e):
        """Open file picker to attach file"""
        if self._file_picker:
            try:
                self._file_picker.pick_files(allow_multiple=False)
            except Exception as ex:
                self._show_snackbar(f"File picker error: {str(ex)}")
        else:
            self._show_snackbar("File attachment not available")

    def _start_video_call(self, e):
        name = self.selected_contact.username if self.selected_contact else "Chat"
        self._log_call("video")
        self._show_call_dialog("Video Call", name, ft.Icons.VIDEO_CALL)

    def _start_voice_call(self, e):
        name = self.selected_contact.username if self.selected_contact else "Chat"
        self._log_call("voice")
        self._show_call_dialog("Voice Call", name, ft.Icons.PHONE)

    def _log_call(self, call_type):
        """Log call in the database and update call history."""
        # For demo: just append to call_history. In production, call start_call() in DB.
        from datetime import datetime
        entry = {
            "type": call_type,
            "with": self.selected_contact.username if self.selected_contact else "Unknown",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.call_history.append(entry)
        self._show_snackbar(
            f"{call_type.title()} call started with {entry['with']}")

    def _show_call_history(self):
        """Show call history in a dialog."""
        items = [ft.Text(f"{c['type'].title()} with {c['with']} at {c['time']}")
                 for c in self.call_history]
        dlg = ft.AlertDialog(
            title=ft.Text("Call History"),
            content=ft.Column(items, tight=True),
            actions=[ft.TextButton("Close", on_click=lambda e: setattr(
                dlg, 'open', False) or self._page.update())],
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _load_permissions(self):
        try:
            session = get_db_session()
            self.permissions = get_all_user_permissions(
                session, self.current_user_id)
            session.close()
        except:
            self.permissions = {"can_chat": True, "can_create_group": True, "can_send_email": True,
                                "can_schedule_meeting": True, "can_upload_document": True}

    def _load_contacts(self):
        """Load contacts from database using SQLAlchemy session - REAL DATA ONLY"""
        session = get_db_session()
        try:
            # Get all users except current user using SQLAlchemy
            users = session.query(User).filter(
                User.id != self.current_user_id,
                User.status == UserStatus.ACTIVE
            ).all()

            for user in users:
                # Determine role name
                role_name = "Employee"
                if hasattr(user, 'role') and user.role:
                    role_name = str(
                        user.role.name) if user.role.name else "Employee"
                elif hasattr(user, 'role_id') and user.role_id:
                    try:
                        from database.operations import get_role_by_id
                        role = get_role_by_id(session, user.role_id)
                        if role:
                            role_name = str(
                                role.display_name) if role.display_name else str(role.name)
                    except:
                        pass

                # Check online status and last seen
                is_online = getattr(user, 'is_online', False)
                last_seen = getattr(user, 'last_seen', None)
                status = "online" if is_online else "offline"

                # Safely extract user attributes
                user_id = int(user.id)
                username = str(user.username) if user.username else "Unknown"
                email = str(
                    user.email) if user.email else "unknown@vernika.local"

                self.contacts.append(Contact(
                    id=user_id,
                    username=username,
                    email=email,
                    role=role_name,
                    status=status,
                    last_seen=last_seen
                ))

        except Exception as e:
            print(f"Error loading contacts from users: {e}")
        finally:
            session.close()
        # NO DEMO DATA - if no contacts found, empty list is fine

    def _load_groups(self):
        """Load chat groups from database using SQLAlchemy - REAL DATA ONLY"""
        session = get_db_session()
        try:
            # Get groups user is member of using SQLAlchemy
            user_groups = get_user_groups(session, self.current_user_id)

            for group in user_groups:
                # Get member details
                members = get_group_members(session, group.id)
                member_ids = [m.user_id for m in members]

                # Get member names
                member_names = []
                for m in members:
                    member_user = session.query(User).filter(
                        User.id == m.user_id).first()
                    if member_user and member_user.username:
                        member_names.append(str(member_user.username))

                self.groups.append(Group(
                    id=group.id,
                    name=str(group.name),
                    created_by=group.created_by,
                    member_ids=member_ids,
                    member_names=member_names if member_names else [
                        f"User {mid}" for mid in member_ids]
                ))

        except Exception as e:
            print(f"Error loading groups from database: {e}")
        finally:
            session.close()
        # NO DEMO DATA - if no groups found, empty list is fine

    def _load_meetings(self):
        """Load meetings from database using SQLAlchemy - REAL DATA ONLY"""
        session = get_db_session()
        try:
            # Get meetings for user using SQLAlchemy
            user_meetings = get_user_meetings(session, self.current_user_id)

            for meeting in user_meetings:
                # Get organizer name
                organizer_user = session.query(User).filter(
                    User.id == meeting.organizer_id).first()
                organizer_name = str(
                    organizer_user.username) if organizer_user and organizer_user.username else "Unknown"

                # Get participant names
                participants = get_meeting_participants(session, meeting.id)
                participant_names = []
                for p in participants:
                    p_user = session.query(User).filter(
                        User.id == p.user_id).first()
                    if p_user and p_user.username:
                        participant_names.append(str(p_user.username))

                # Get start and end times
                start_time = meeting.start_time if meeting.start_time else datetime.now()
                end_time = meeting.end_time if meeting.end_time else datetime.now()

                self.meetings.append(Meeting(
                    id=meeting.id,
                    title=str(meeting.title),
                    description=str(
                        meeting.description) if meeting.description else "",
                    organizer=organizer_name,
                    start_time=start_time,
                    end_time=end_time,
                    participants=participant_names if participant_names else [
                        "You"],
                    status=str(meeting.status.value) if hasattr(
                        meeting.status, 'value') else str(meeting.status)
                ))

        except Exception as e:
            print(f"Error loading meetings: {e}")
        finally:
            session.close()
        # NO DEMO DATA - if no meetings found, empty list is fine

    def _load_emails(self):
        """Load emails from database using SQLAlchemy - REAL DATA ONLY"""
        session = get_db_session()
        try:
            # Get received emails (inbox) using SQLAlchemy
            emails = get_user_emails(
                session, self.current_user_id, folder="inbox")

            for em in emails:
                # Get sender name
                sender_user = session.query(User).filter(
                    User.id == em.sender_id).first()
                sender_name = str(
                    sender_user.username) if sender_user and sender_user.username else "Unknown"

                # Get recipient names
                recipients = []
                for recipient in em.recipients:
                    if recipient.recipient_type == "to":
                        r_user = session.query(User).filter(
                            User.id == recipient.recipient_id).first()
                        if r_user and r_user.username:
                            recipients.append(str(r_user.username))

                # Get created_at
                created_at = em.created_at if em.created_at else datetime.now()

                self.emails.append(Email(
                    id=em.id,
                    sender=sender_name,
                    subject=str(em.subject) if em.subject else "",
                    body=str(em.body) if em.body else "",
                    category=str(em.category.value) if hasattr(
                        em.category, 'value') else str(em.category),
                    recipients=recipients if recipients else ["You"],
                    created_at=created_at,
                    is_read=bool(em.is_read),
                    is_sent=False
                ))

        except Exception as e:
            print(f"Error loading emails: {e}")
        finally:
            session.close()
        # NO DEMO DATA - if no emails found, empty list is fine

    def _load_documents(self):
        """Load documents from database using SQLAlchemy - REAL DATA ONLY"""
        session = get_db_session()
        try:
            # Get documents for user using SQLAlchemy
            documents = get_user_documents(session, self.current_user_id)

            for doc in documents:
                # Get uploader name
                uploader_user = session.query(User).filter(
                    User.id == doc.uploaded_by).first()
                uploader_name = str(
                    uploader_user.username) if uploader_user and uploader_user.username else "Unknown"

                # Get file size
                file_size = f"{doc.file_size / 1024:.1f} KB" if doc.file_size and doc.file_size < 1024 * \
                    1024 else f"{doc.file_size / (1024*1024):.1f} MB" if doc.file_size else ""

                self.documents.append(Document(
                    id=doc.id,
                    name=str(doc.name),
                    file_type=str(doc.file_type) if doc.file_type else "file",
                    uploaded_by=uploader_name,
                    created_at=doc.created_at if doc.created_at else datetime.now(),
                    size=file_size
                ))

        except Exception as e:
            print(f"Error loading documents: {e}")
        finally:
            session.close()
        # NO DEMO DATA - if no documents found, empty list is fine

    def _load_sample_messages(self):
        """Load messages for selected contact/group from database"""
        self.messages = []

        if not self.selected_contact and not self.selected_group:
            # No conversation selected, show welcome message
            self.messages = [
                ChatMessage(sender_id=0, sender_name="System",
                            content="Select a contact or group to start chatting",
                            timestamp=datetime.now(), is_own=False),
            ]
            return

        session = get_db_session()
        try:
            if self.selected_contact:
                # Load direct messages
                db_messages = get_direct_messages(
                    session, self.current_user_id, self.selected_contact.id)
                for msg in db_messages:
                    sender_username = "Unknown"
                    try:
                        sender = session.query(User).filter(
                            User.id == msg.sender_id).first()
                        sender_username = str(
                            sender.username) if sender and sender.username else "Unknown"
                    except:
                        pass

                    # Safely extract values from SQLAlchemy columns
                    msg_content = str(msg.content) if msg.content else ""
                    msg_timestamp = msg.created_at if msg.created_at else datetime.now()
                    is_own = bool(msg.sender_id == self.current_user_id)

                    self.messages.append(ChatMessage(
                        sender_id=int(msg.sender_id),
                        sender_name=sender_username,
                        content=msg_content,
                        timestamp=msg_timestamp,
                        is_own=is_own
                    ))
            elif self.selected_group:
                # Load group messages
                db_messages = get_group_messages(
                    session, self.selected_group.id)
                for msg in db_messages:
                    sender_username = "Unknown"
                    try:
                        sender = session.query(User).filter(
                            User.id == msg.sender_id).first()
                        sender_username = str(
                            sender.username) if sender and sender.username else "Unknown"
                    except:
                        pass

                    # Safely extract values from SQLAlchemy columns
                    msg_content = str(msg.content) if msg.content else ""
                    msg_timestamp = msg.created_at if msg.created_at else datetime.now()
                    is_own = bool(msg.sender_id == self.current_user_id)
                    group_name = str(
                        self.selected_group.name) if self.selected_group.name else "Group"

                    self.messages.append(ChatMessage(
                        sender_id=int(msg.sender_id),
                        sender_name=sender_username,
                        content=msg_content,
                        timestamp=msg_timestamp,
                        is_own=is_own,
                        is_group=True,
                        group_name=group_name
                    ))
        except Exception as e:
            print(f"Error loading messages: {e}")
        finally:
            session.close()

        # Sort by timestamp (oldest first)
        self.messages = sorted(
            self.messages, key=lambda m: m.timestamp or datetime.min)

    def _build_ui(self) -> None:
        """Build UI once and store references for efficient updates"""
        # Build navigation and store references
        navigation = self._build_navigation()

        # Build main area and store reference
        self._main_area_ref = self._build_main_area()

        # Set content - only build once
        self.content = Container(content=Row(expand=True, controls=[
            navigation,
            Container(width=1, bgcolor=OUTLINE_VARIANT),
            self._main_area_ref,
        ]))

        # Update page if already mounted
        if hasattr(self, '_page') and self._page:
            try:
                self._page.update()
            except:
                pass

    def _build_navigation(self) -> Container:
        nav_items = [
            {"icon": ft.Icons.CHAT, "label": "Chat", "key": "chat"},
            {"icon": ft.Icons.EVENT, "label": "Meetings", "key": "meetings"},
            {"icon": ft.Icons.EMAIL, "label": "Email", "key": "email"},
            {"icon": ft.Icons.FOLDER, "label": "Documents", "key": "documents"},
            {"icon": ft.Icons.PEOPLE, "label": "Contacts", "key": "contacts"},
        ]

        # Clear and rebuild nav items reference list
        self._nav_items = []
        nav_controls = []

        for item in nav_items:
            # Create inner container with styling
            inner_container = Container(
                padding=ft.padding.all(4),
                bgcolor=PRIMARY_CONTAINER if self.current_tab == item["key"] else None,
                border_radius=8,
                content=Row(
                    controls=[
                        Icon(icon=item["icon"], size=20,
                             color=PRIMARY if self.current_tab == item["key"] else GREY_600),
                        Text(item["label"], size=14,
                             weight=ft.FontWeight.W_500),
                    ],
                ),
            )

            # Create nav item container
            nav_item = Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                on_click=lambda e, key=item["key"]: self._switch_tab(key),
                content=inner_container,
            )

            # Store reference for efficient updates
            self._nav_items.append(nav_item)
            nav_controls.append(nav_item)

        return Container(width=200, bgcolor=SURFACE, content=Column(controls=[
            Container(padding=ft.padding.all(12), bgcolor=PRIMARY_CONTAINER,
                      content=Row(controls=[Icon(icon=ft.Icons.CHAT, color=PRIMARY),
                                            Text("Communications", size=15, weight=FontWeight.BOLD,
                                                 color=ON_PRIMARY_CONTAINER)])),
            Container(height=10),
            Column(controls=nav_controls, spacing=2),
            Container(expand=True),
            Container(padding=ft.padding.all(12), bgcolor=SURFACE_VARIANT,
                      content=Row(controls=[
                          CircleAvatar(content=Text(self.current_username[:1].upper(),
                                                    size=14, weight=FontWeight.BOLD),
                                       radius=16, bgcolor=PRIMARY),
                          Column(tight=True, controls=[
                              Text(self.current_username, size=13,
                                  weight=ft.FontWeight.W_500),
                              Text("Online", size=10, color=GREEN)]),
                      ])),
        ], expand=True))

    def _build_main_area(self) -> Container:
        if self.current_tab == "chat":
            return self._build_chat_view()
        elif self.current_tab == "meetings":
            return self._build_meetings_view()
        elif self.current_tab == "email":
            return self._build_email_view()
        elif self.current_tab == "documents":
            return self._build_documents_view()
        elif self.current_tab == "contacts":
            return self._build_contacts_view()
        return self._build_chat_view()

    def _build_chat_view(self) -> Container:
        return Container(expand=True, content=Row(expand=True, controls=[
            self._build_chat_sidebar(),
            Container(width=1, bgcolor=OUTLINE_VARIANT),
            self._build_chat_area(),
        ]))

    def _build_chat_sidebar(self) -> Container:
        # Use segmented control for switching between contacts and groups (compatible with all Flet versions)
        self.chat_tab = "contacts"

        def on_contacts_tab(e):
            self.chat_tab = "contacts"
            self.contact_list.visible = True
            self.group_list.visible = False
            self._page.update()

        def on_groups_tab(e):
            self.chat_tab = "groups"
            self.contact_list.visible = False
            self.group_list.visible = True
            self._page.update()

        contacts_tab = Container(
            on_click=on_contacts_tab,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            content=Row([
                Icon(icon=ft.Icons.PEOPLE, size=18,
                     color=PRIMARY if self.chat_tab == "contacts" else GREY_600),
                Text("Contacts", size=12, color=PRIMARY if self.chat_tab == "contacts" else GREY_600,
                     weight=ft.FontWeight.W_500 if self.chat_tab == "contacts" else None),
            ], spacing=4),
        )

        groups_tab = Container(
            on_click=on_groups_tab,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            content=Row([
                Icon(icon=ft.Icons.GROUPS, size=18,
                     color=PRIMARY if self.chat_tab == "groups" else GREY_600),
                Text("Groups", size=12, color=PRIMARY if self.chat_tab == "groups" else GREY_600,
                     weight=ft.FontWeight.W_500 if self.chat_tab == "groups" else None),
            ], spacing=4),
        )

        self.contact_list = self._build_contact_list()
        self.group_list = self._build_group_list()

        return Container(width=250, bgcolor=SURFACE, content=Column(controls=[
            Container(padding=ft.padding.all(12), bgcolor=PRIMARY_CONTAINER,
                      content=Row(controls=[
                         Text("Messages", size=15, weight=FontWeight.BOLD,
                              color=ON_PRIMARY_CONTAINER),
                         Container(expand=True),
                         IconButton(icon=ft.Icons.ADD, icon_size=20, tooltip="New Group",
                                    on_click=self._show_create_group_dialog,
                                    icon_color=ON_PRIMARY_CONTAINER),
                         ])),
            # Tab selector using Row (Flet version compatible)
            Container(
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                content=Row(controls=[contacts_tab, groups_tab], spacing=0),
            ),
            Container(height=5), self.contact_list,
        ], expand=True))

    def _build_contact_list(self) -> Container:
        items = []
        online = [c for c in self.contacts if c.status == "online"]
        offline = [c for c in self.contacts if c.status == "offline"]

        if online:
            items.append(Container(
                padding=padding.only(left=12, top=8, bottom=4),
                content=Text("Online", size=12,
                             weight=FontWeight.BOLD, color=PRIMARY)
            ))
            for c in online:
                items.append(self._create_contact_item(c, GREEN))
        if offline:
            items.append(Container(
                padding=padding.only(left=12, top=8, bottom=4),
                content=Text("Offline", size=12,
                             weight=FontWeight.BOLD, color=GREY)
            ))
            for c in offline:
                items.append(self._create_contact_item(c, GREY))
        if not items:
            items.append(
                Container(padding=20, content=Text("No contacts", color=GREY)))
        return Container(content=Column(controls=items, scroll=ScrollMode.AUTO), expand=True)

    def _create_contact_item(self, contact: Contact, status_color: str) -> Container:
        last_seen_str = ""
        if contact.status == "offline" and contact.last_seen:
            try:
                last_seen_dt = contact.last_seen
                if isinstance(last_seen_dt, str):
                    from dateutil import parser
                    last_seen_dt = parser.parse(last_seen_dt)
                last_seen_str = f"Last seen: {last_seen_dt.strftime('%Y-%m-%d %H:%M')}"
            except Exception:
                last_seen_str = "Last seen: Unknown"
        return Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_click=lambda e: self._select_contact(contact),
            content=Card(
                content=Container(
                    padding=8,
                    content=Row(
                        controls=[
                            Stack([
                                CircleAvatar(
                                    content=Text(contact.username[:1].upper(),
                                                 size=16, weight=FontWeight.BOLD),
                                    radius=20, bgcolor=BLUE_400
                                ),
                                Container(
                                    width=12, height=12, bgcolor=status_color, border_radius=6,
                                    right=0, bottom=0
                                ),
                            ]),
                            Column(
                                tight=True, expand=True,
                                controls=[
                                    Text(contact.username, size=14,
                                         weight=ft.FontWeight.W_500),
                                    Text(contact.role, size=11, color=GREY_600),
                                    Text(
                                        last_seen_str, size=10, color=GREY_500) if last_seen_str else Container(),
                                ]
                            ),
                            Row(
                                controls=[
                                    IconButton(
                                        icon=ft.Icons.CHAT, icon_size=18, tooltip="Chat",
                                        on_click=lambda e, c=contact: self._select_contact(
                                            c)
                                    ),
                                    IconButton(
                                        icon=ft.Icons.EMAIL, icon_size=18, tooltip="Email",
                                        on_click=lambda e, c=contact: self._show_compose_email(
                                            c)
                                    ),
                                ], spacing=0
                            ),
                        ]
                    )
                ),
                elevation=0
            )
        )

    def _build_group_list(self) -> Container:
        items = []
        for g in self.groups:
            items.append(Container(
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                on_click=lambda e, gr=g: self._select_group(gr),
                content=Card(
                    content=Container(
                        padding=8,
                        content=Row(
                            controls=[
                                CircleAvatar(
                                    content=Icon(
                                        icon=ft.Icons.GROUPS, color=WHITE),
                                    bgcolor=PURPLE_400, radius=20
                                ),
                                Column(
                                    tight=True, expand=True,
                                    controls=[
                                        Text(g.name, size=14,
                                             weight=ft.FontWeight.W_500),
                                        Text(
                                            f"{len(g.member_names)} members", size=11, color=GREY_600)
                                    ]
                                ),
                            ]
                        )
                    ),
                    elevation=0
                )
            ))
        if not items:
            items.append(Container(padding=20, content=Column(
                horizontal_alignment=CrossAxisAlignment.CENTER,
                controls=[Text("No groups", color=GREY),
                          ElevatedButton("Create Group", icon=ft.Icons.ADD, height=36,
                                         on_click=self._show_create_group_dialog)])))
        return Container(content=Column(controls=items, scroll=ScrollMode.AUTO), expand=True, visible=False)

    def _build_chat_area(self) -> Container:
        # Message list reference for sending messages
        self.message_list = ListView(
            expand=True, spacing=8, padding=10, auto_scroll=True)

        # Message input field reference
        self.message_input = TextField(
            hint_text="Type a message...",
            expand=True,
            min_lines=1,
            max_lines=4,
            filled=True,
            content_padding=10,
            on_submit=self._send_message
        )

        # Store header reference for updating later
        self.chat_header = Container(padding=ft.padding.symmetric(horizontal=12, vertical=8), bgcolor=SURFACE,
                                     content=Row(controls=[
                                         IconButton(
                                             icon=ft.Icons.ARROW_BACK, visible=False),
                                         CircleAvatar(content=Icon(icon=ft.Icons.PERSON, color=WHITE),
                                                      bgcolor=PRIMARY, radius=20),
                                         Column(tight=True, expand=True, controls=[
                                             Text("Select a conversation", size=15,
                                                  weight=ft.FontWeight.W_500),
                                             Text("Start chatting", size=12, color=GREY_600)]),
                                         Row(controls=[
                                             IconButton(icon=ft.Icons.VIDEO_CALL, tooltip="Video Call",
                                                        on_click=self._start_video_call, icon_color=PRIMARY),
                                             IconButton(icon=ft.Icons.PHONE, tooltip="Voice Call",
                                                        on_click=self._start_voice_call, icon_color=PRIMARY),
                                             IconButton(icon=ft.Icons.EMAIL, tooltip="Email",
                                                        on_click=self._quick_email, icon_color=SECONDARY),
                                         ]),
                                     ]))

        return Container(expand=True, content=Column(controls=[
            self.chat_header,
            Container(expand=True, bgcolor=BLUE_GREY_50,
                      content=self.message_list),
            Container(padding=ft.padding.all(10), bgcolor=SURFACE,
                      content=Row(controls=[
                          IconButton(
                              icon=ft.Icons.ATTACH_FILE, tooltip="Attach file", on_click=self._attach_file),
                          IconButton(
                              icon=ft.Icons.EMOJI_EMOTIONS,
                              tooltip="Emoji (coming soon)",
                              on_click=lambda e: self._show_snackbar("Emoji picker coming soon!")),
                          self.message_input,
                          ElevatedButton("", icon=ft.Icons.SEND, height=48, width=48,
                                         on_click=self._send_message,
                                         style=ft.ButtonStyle(bgcolor=PRIMARY, color=ON_PRIMARY)),
                      ], spacing=5, vertical_alignment=CrossAxisAlignment.CENTER)),
        ], expand=True))

    def _build_meetings_view(self) -> Container:
        meeting_items = []
        for m in self.meetings:
            meeting_items.append(Card(content=Container(padding=ft.padding.all(12), content=Row(controls=[
                Container(width=50, height=50, bgcolor=PRIMARY_CONTAINER, border_radius=8,
                          content=Column(horizontal_alignment=CrossAxisAlignment.CENTER, controls=[
                              Text(m.start_time.strftime("%d"), size=18, weight=FontWeight.BOLD,
                                   color=PRIMARY),
                              Text(m.start_time.strftime("%b"), size=10, color=GREY_600)])),
                Column(tight=True, expand=True, controls=[
                    Text(m.title, size=15, weight=ft.FontWeight.W_500),
                    Text(f"By {m.organizer}", size=12, color=GREY_600),
                    Row(controls=[Icon(icon=ft.Icons.SCHEDULE, size=12, color=GREY_500),
                                  Text(f"{m.start_time.strftime('%I:%M %p')}", size=11, color=GREY_500)]),
                ]),
                ElevatedButton("Join", icon=ft.Icons.VIDEO_CALL, height=32,
                               on_click=lambda e, mt=m: self._join_meeting(mt),
                               style=ft.ButtonStyle(bgcolor=PRIMARY, color=ON_PRIMARY)),
            ]))))

        return Container(expand=True, padding=ft.padding.all(16), content=Column(controls=[
            Row(controls=[Icon(icon=ft.Icons.EVENT, color=PRIMARY, size=24),
                         Text("Meetings", size=18, weight=FontWeight.BOLD),
                         Container(expand=True),
                         ElevatedButton("Schedule Meeting", icon=ft.Icons.ADD, bgcolor=PRIMARY,
                                        color=ON_PRIMARY, on_click=self._show_create_meeting_dialog)]),
            Container(height=16),
            Container(expand=True, content=ListView(
                controls=meeting_items, spacing=12, expand=True)),
        ], expand=True))

    def _build_email_view(self) -> Container:
        email_items = []
        for em in self.emails:
            email_items.append(Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                on_click=lambda e, email=em: self._view_email(em),
                content=Row(controls=[
                    Container(width=4, height=40, bgcolor=PRIMARY if not em.is_read else GREY_300,
                              border_radius=2),
                    Container(width=12),
                    Column(tight=True, expand=True, controls=[
                        Row(controls=[Text(em.sender, size=13, weight=FontWeight.BOLD,
                                           color=PRIMARY if not em.is_read else GREY_700),
                                      Container(expand=True),
                                      Text(em.created_at.strftime("%b %d"), size=11, color=GREY_500)]),
                        Text(em.subject, size=14, weight=ft.FontWeight.W_500),
                        Text(em.body[:60] + "..." if len(em.body) > 60 else em.body,
                             size=12, color=GREY_600),
                    ]),
                ]),
                bgcolor=PRIMARY_CONTAINER if not em.is_read else None,
            ))

        return Container(expand=True, padding=ft.padding.all(16), content=Column(controls=[
            Row(controls=[Icon(icon=ft.Icons.EMAIL, color=PRIMARY, size=24),
                         Text("Internal Email", size=18,
                              weight=FontWeight.BOLD),
                         Text("username@vernika.local",
                              size=12, color=GREY_500),
                         Container(expand=True),
                         ElevatedButton("Compose", icon=ft.Icons.CREATE, bgcolor=PRIMARY,
                                        color=ON_PRIMARY, on_click=self._show_compose_email_general)]),
            Container(height=12),
            Row(controls=[Text("Inbox", size=13, weight=ft.FontWeight.W_500, color=PRIMARY),
                          Container(width=20),
                Text("Sent", size=13,
                     weight=ft.FontWeight.W_500, color=GREY_600),
                Container(width=20),
                Text("Announcements", size=13,
                     weight=ft.FontWeight.W_500, color=GREY_600),
                Container(expand=True)]),
            Container(height=8),
            Container(expand=True, bgcolor=SURFACE,
                      content=ListView(controls=email_items, spacing=2, expand=True)),
        ], expand=True))

    def _build_documents_view(self) -> Container:
        doc_items = []
        for d in self.documents:
            icon = ft.Icons.IMAGE if d.file_type in [
                "jpg", "png", "gif"] else ft.Icons.DESCRIPTION
            doc_items.append(Card(content=Container(padding=ft.padding.all(12), content=Row(controls=[
                Container(width=40, height=40, bgcolor=SURFACE_VARIANT, border_radius=8,
                          content=Icon(icon=icon, size=20, color=PRIMARY)),
                Column(tight=True, expand=True, controls=[
                    Text(d.name, size=14, weight=ft.FontWeight.W_500),
                    Row(controls=[Text(d.uploaded_by, size=11, color=GREY_600),
                                  Text(" - ", color=GREY_400),
                        Text(d.size, size=11, color=GREY_600)]),
                ]),
                IconButton(icon=ft.Icons.DOWNLOAD, tooltip="Download"),
            ]))))

        return Container(expand=True, padding=ft.padding.all(16), content=Column(controls=[
            Row(controls=[Icon(icon=ft.Icons.FOLDER, color=PRIMARY, size=24),
                         Text("Documents", size=18, weight=FontWeight.BOLD),
                         Container(expand=True),
                         ElevatedButton("Upload", icon=ft.Icons.UPLOAD_FILE, bgcolor=PRIMARY,
                                        color=ON_PRIMARY, on_click=self._show_upload_document_dialog)]),
            Container(height=16),
            Container(expand=True, content=ListView(
                controls=doc_items, spacing=12, expand=True)),
        ], expand=True))

    def _build_contacts_view(self) -> Container:
        contact_items = []
        for c in self.contacts:
            contact_items.append(Card(content=Container(padding=ft.padding.all(12), content=Row(controls=[
                CircleAvatar(content=Text(c.username[:1].upper(), size=16, weight=FontWeight.BOLD),
                             radius=24, bgcolor=PRIMARY if c.status == "online" else GREY_400),
                Column(tight=True, expand=True, controls=[
                    Text(c.username, size=15, weight=ft.FontWeight.W_500),
                    Text(c.email, size=12, color=GREY_600),
                    Text(c.role, size=11, color=GREY_500),
                ]),
                Row(controls=[
                    IconButton(icon=ft.Icons.CHAT, tooltip="Chat",
                               on_click=lambda e, ct=c: self._start_chat(ct)),
                    IconButton(icon=ft.Icons.EMAIL, tooltip="Email",
                               on_click=lambda e, ct=c: self._show_compose_email(ct)),
                ]),
            ]))))

        return Container(expand=True, padding=ft.padding.all(16), content=Column(controls=[
            Row(controls=[Icon(icon=ft.Icons.PEOPLE, color=PRIMARY, size=24),
                         Text("Contacts", size=18, weight=FontWeight.BOLD),
                         Text(f"{len(self.contacts)} employees", size=12, color=GREY_500)]),
            Container(height=16),
            Container(expand=True, content=ListView(
                controls=contact_items, spacing=12, expand=True)),
        ], expand=True))

    def _switch_tab(self, key: str):
        """Switch main tab - only update content area, don't rebuild entire UI"""
        self.current_tab = key

        # Update navigation item styles efficiently
        nav_items = [
            {"icon": ft.Icons.CHAT, "label": "Chat", "key": "chat"},
            {"icon": ft.Icons.EVENT, "label": "Meetings", "key": "meetings"},
            {"icon": ft.Icons.EMAIL, "label": "Email", "key": "email"},
            {"icon": ft.Icons.FOLDER, "label": "Documents", "key": "documents"},
            {"icon": ft.Icons.PEOPLE, "label": "Contacts", "key": "contacts"},
        ]

        # Update the main area content only
        if self._main_area_ref:
            new_content = self._build_main_area()
            self._main_area_ref.content = new_content.content
            self._main_area_ref.update()

        # Update navigation highlighting
        self._update_navigation_highlight(key)

        # Update page efficiently
        try:
            self._page.update()
        except Exception as e:
            print(f"Error updating page: {e}")

    def _update_navigation_highlight(self, active_key: str):
        """Update navigation highlight without rebuilding"""
        nav_items = [
            {"icon": ft.Icons.CHAT, "label": "Chat", "key": "chat"},
            {"icon": ft.Icons.EVENT, "label": "Meetings", "key": "meetings"},
            {"icon": ft.Icons.EMAIL, "label": "Email", "key": "email"},
            {"icon": ft.Icons.FOLDER, "label": "Documents", "key": "documents"},
            {"icon": ft.Icons.PEOPLE, "label": "Contacts", "key": "contacts"},
        ]

        # Update navigation styling for active tab
        for idx, item in enumerate(nav_items):
            if idx < len(self._nav_items):
                nav_container = self._nav_items[idx]
                inner_container = nav_container.content
                is_active = item["key"] == active_key

                # The inner_container.content is a Row, get its controls
                if hasattr(inner_container, "content") and hasattr(inner_container.content, "controls"):
                    row_controls = inner_container.content.controls
                    if len(row_controls) >= 2:
                        icon = row_controls[0]
                        icon.color = PRIMARY if is_active else GREY_600
                        text = row_controls[1]
                        text.color = PRIMARY if is_active else GREY_600
                # Update background
                inner_container.bgcolor = PRIMARY_CONTAINER if is_active else None
                nav_container.update()

    def _on_chat_tab_change(self, e):
        if e.control.selected_index == 0:
            self.contact_list.visible = True
            self.group_list.visible = False
        else:
            self.contact_list.visible = False
            self.group_list.visible = True
        self._page.update()

    def _select_contact(self, contact: Contact):
        """Select a contact to chat with"""
        self.selected_contact = contact
        self.selected_group = None
        # Refresh messages and update header
        self._refresh_messages()
        self._update_chat_header()

    def _select_group(self, group: Group):
        """Select a group to chat with"""
        self.selected_group = group
        self.selected_contact = None
        # Refresh messages and update header
        self._refresh_messages()
        self._update_chat_header()

    def _update_chat_header(self):
        """Update chat header with selected conversation info"""
        if not hasattr(self, 'chat_header') or not self.chat_header:
            return

        row = self.chat_header.content

        if self.selected_contact:
            # Update for contact
            row.controls[1] = CircleAvatar(
                content=Icon(icon=ft.Icons.PERSON, color=WHITE),
                bgcolor=PRIMARY, radius=20
            )
            row.controls[2].controls[0].value = self.selected_contact.username
            row.controls[2].controls[1].value = "Online" if self.selected_contact.status == "online" else "Offline"
        elif self.selected_group:
            # Update for group
            row.controls[1] = CircleAvatar(
                content=Icon(icon=ft.Icons.GROUPS, color=WHITE),
                bgcolor=PURPLE_400, radius=20
            )
            row.controls[2].controls[0].value = self.selected_group.name
            row.controls[2].controls[1].value = f"{len(self.selected_group.member_names)} members"
        else:
            # Reset to default
            row.controls[1] = CircleAvatar(
                content=Icon(icon=ft.Icons.PERSON, color=WHITE),
                bgcolor=PRIMARY, radius=20
            )
            row.controls[2].controls[0].value = "Select a conversation"
            row.controls[2].controls[1].value = "Start chatting"

        self.chat_header.update()

    def _start_chat(self, contact: Contact):
        """Start chat with a contact - only update, don't rebuild"""
        # Switch to chat tab if not already there
        if self.current_tab != "chat":
            self.current_tab = "chat"
            # Update main area content only
            if self._main_area_ref:
                new_content = self._build_main_area()
                self._main_area_ref.content = new_content.content
                self._main_area_ref.update()
                self._update_navigation_highlight("chat")

        self._select_contact(contact)
        # Refresh messages for selected contact
        self._refresh_messages()

    def _refresh_messages(self):
        """Refresh messages for currently selected conversation"""
        self._load_sample_messages()
        # Update the message list UI
        if hasattr(self, 'message_list') and self.message_list:
            # Clear existing messages
            self.message_list.controls.clear()
            # Add new message controls
            for msg in self.messages:
                self.message_list.controls.append(ChatMessageControl(msg))
            # Scroll to bottom
            try:
                self.message_list.scroll_to(offset=-1)
            except:
                pass  # scroll_to may not be available in all Flet versions
        # Update the page
        self._page.update()

    def _send_message(self, e):
        """Send a chat message to selected contact or group"""
        if not hasattr(self, 'message_input') or not self.message_input.value.strip():
            self._show_snackbar("Please type a message first")
            return

        message_content = self.message_input.value.strip()

        session = get_db_session()
        try:
            if self.selected_contact:
                # Validate that contact exists in users table
                from database.operations import get_user_by_id
                contact_user = get_user_by_id(
                    session, self.selected_contact.id)

                if not contact_user:
                    self._show_snackbar(
                        f"User {self.selected_contact.username} not found in database")
                    return

                # Send direct message
                msg = send_chat_message(
                    session,
                    sender_id=self.current_user_id,
                    content=message_content,
                    receiver_id=self.selected_contact.id,
                    message_type=MessageType.TEXT
                )
                # Mark messages from this contact as read
                mark_chat_messages_as_read(
                    session, self.current_user_id, self.selected_contact.id)
                self._show_snackbar(
                    f"Message sent to {self.selected_contact.username}")

            elif self.selected_group:
                # Send group message
                msg = send_chat_message(
                    session,
                    sender_id=self.current_user_id,
                    content=message_content,
                    group_id=self.selected_group.id,
                    message_type=MessageType.TEXT
                )
                self._show_snackbar(
                    f"Message sent to {self.selected_group.name}")

            else:
                self._show_snackbar("Please select a contact or group first")
                return

            # Clear input field
            self.message_input.value = ""
            # Refresh messages
            self._refresh_messages()

        except Exception as ex:
            print(f"Error sending message: {ex}")
            self._show_snackbar(f"Error sending message: {str(ex)}")
        finally:
            session.close()

    def _show_compose_email(self, contact: Contact):
        """Show compose email dialog"""
        # Email subject and body fields
        subject_field = ft.TextField(label="Subject", width=400)
        body_field = ft.TextField(
            label="Message", width=400, min_lines=5, multiline=True)

        def send_email_action(e):
            subject = subject_field.value.strip()
            body = body_field.value.strip()

            if not subject or not body:
                self._show_snackbar("Please fill in subject and message")
                return

            # Send email via database
            session = get_db_session()
            try:
                # Determine recipient IDs - validate that recipient exists
                recipient_ids = []
                if contact.id == 0:  # Broadcast to all users
                    all_users = get_all_users(session)
                    recipient_ids = [
                        int(u.id) for u in all_users if int(u.id) != self.current_user_id]
                else:
                    # Validate that contact exists in users table
                    from database.operations import get_user_by_id
                    contact_user = get_user_by_id(session, contact.id)
                    if contact_user:
                        recipient_ids = [contact.id]
                    else:
                        self._show_snackbar(
                            f"User {contact.username} not found in database")
                        return

                if recipient_ids:
                    from database.models import EmailCategory
                    email = send_email(
                        session,
                        sender_id=self.current_user_id,
                        subject=subject,
                        body=body,
                        recipient_ids=recipient_ids,
                        category=EmailCategory.GENERAL
                    )
                    self._show_snackbar(f"Email sent to {contact.username}")
                    dlg.open = False
                    self._page.update()
                else:
                    self._show_snackbar("No recipients found")
            except Exception as ex:
                print(f"Error sending email: {ex}")
                self._show_snackbar(f"Error: {str(ex)}")
            finally:
                session.close()

        dlg = ft.AlertDialog(
            title=Row([Icon(icon=ft.Icons.EMAIL, color=PRIMARY),
                      Text(f"Email to {contact.username}")]),
            content=Column(controls=[
                TextField(label="To", value=contact.email,
                          width=400, read_only=True),
                subject_field,
                body_field,
                Text("Internal: username@vernika.local",
                     size=11, color=GREY_500),
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(
                    dlg, 'open', False) or self._page.update()),
                ElevatedButton("Send", on_click=send_email_action,
                               style=ft.ButtonStyle(bgcolor=PRIMARY, color=ON_PRIMARY)),
            ],
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_compose_email_general(self, e):
        self._show_compose_email(
            Contact(id=0, username="All", email="all@vernika.local", role="Broadcast"))

    def _send_email_action(self, dlg):
        self._show_snackbar("Email sent!")
        dlg.open = False
        self._page.update()

    def _show_create_group_dialog(self, e):
        """Show create group dialog with member selection"""
        group_name_field = ft.TextField(label="Group Name", width=400)

        # Create checkboxes for selecting members
        member_checkboxes = []
        session = get_db_session()
        try:
            users = get_all_users(session)
            for user in users:
                if int(user.id) != self.current_user_id:
                    username = str(
                        user.username) if user.username else "Unknown"
                    checkbox = Checkbox(label=username, value=False)
                    checkbox.user_id = int(user.id)
                    member_checkboxes.append(checkbox)
        except:
            pass
        finally:
            session.close()

        def create_group_action(e):
            group_name = group_name_field.value.strip()
            if not group_name:
                self._show_snackbar("Please enter a group name")
                return

            selected_members = [
                cb.user_id for cb in member_checkboxes if cb.value]
            if not selected_members:
                self._show_snackbar("Please select at least one member")
                return

            # Create group in database
            session = get_db_session()
            try:
                group = db_create_chat_group(
                    session,
                    name=group_name,
                    description="",
                    created_by=self.current_user_id
                )

                # Add members to group
                for member_id in selected_members:
                    add_group_member(session, group.id,
                                     member_id, role="member")

                # Reload groups
                self.groups = []
                self._load_groups()

                self._show_snackbar(f"Group '{group_name}' created!")
                dlg.open = False
                self._page.update()
            except Exception as ex:
                print(f"Error creating group: {ex}")
                self._show_snackbar(f"Error: {str(ex)}")
            finally:
                session.close()

        # Build member selection list
        member_list = Column(controls=member_checkboxes,
                             scroll=ScrollMode.AUTO)
        if not member_checkboxes:
            member_list = Text("No other users available", color=GREY_500)

        dlg = ft.AlertDialog(
            title=Row(controls=[
                Icon(icon=ft.Icons.GROUP_ADD, color=PRIMARY),
                Text("Create Group")
            ]),
            content=Column(controls=[
                group_name_field,
                Text("Select members:", weight=ft.FontWeight.W_500),
                Container(content=member_list, height=150, width=400)
            ], tight=True, scroll=ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(
                    dlg, 'open', False) or self._page.update()),
                ElevatedButton("Create", on_click=create_group_action,
                               style=ft.ButtonStyle(bgcolor=PRIMARY, color=ON_PRIMARY)),
            ],
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_create_meeting_dialog(self, e):
        """Show create meeting dialog with full functionality"""
        title_field = ft.TextField(label="Meeting Title", width=400)
        description_field = ft.TextField(
            label="Description", width=400, min_lines=2, multiline=True)
        date_field = ft.TextField(
            label="Date (YYYY-MM-DD)", width=400, value=datetime.now().strftime("%Y-%m-%d"))
        start_time_field = ft.TextField(
            label="Start Time (HH:MM, e.g., 09:00)", width=400, value="09:00")
        end_time_field = ft.TextField(
            label="End Time (HH:MM, e.g., 10:00)", width=400, value="10:00")

        # Create checkboxes for selecting participants
        member_checkboxes = []
        session = get_db_session()
        try:
            users = get_all_users(session)
            for user in users:
                if int(user.id) != self.current_user_id:
                    username = str(
                        user.username) if user.username else "Unknown"
                    checkbox = Checkbox(label=username, value=False)
                    checkbox.user_id = int(user.id)
                    member_checkboxes.append(checkbox)
        except Exception as ex:
            print(f"Error loading users: {ex}")
        finally:
            session.close()

        def create_meeting_action(btn_event):
            title = title_field.value.strip()
            description = description_field.value.strip()
            date_str = date_field.value.strip()
            start_str = start_time_field.value.strip()
            end_str = end_time_field.value.strip()

            if not title:
                self._show_snackbar("Please enter a meeting title")
                return

            if not date_str or not start_str or not end_str:
                self._show_snackbar("Please enter date and time")
                return

            # Parse date and time
            try:
                meeting_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                start_time = datetime.strptime(
                    f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(
                    f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
            except Exception as ex:
                self._show_snackbar("Invalid date or time format")
                return

            selected_members = [
                cb.user_id for cb in member_checkboxes if cb.value]
            if not selected_members:
                self._show_snackbar("Please select at least one participant")
                return

            # Create meeting in database
            session = get_db_session()
            try:
                meeting = create_meeting(
                    session,
                    title=title,
                    organizer_id=self.current_user_id,
                    start_time=start_time,
                    end_time=end_time,
                    description=description if description else None,
                    participant_ids=selected_members
                )

                # Reload meetings
                self.meetings = []
                self._load_meetings()

                self._show_snackbar(f"Meeting '{title}' scheduled!")
                dlg.open = False
                self._page.update()
            except Exception as ex:
                print(f"Error creating meeting: {ex}")
                self._show_snackbar(f"Error: {str(ex)}")
            finally:
                session.close()

        # Build participant selection list
        participant_list = Column(
            controls=member_checkboxes, scroll=ScrollMode.AUTO, spacing=5)
        if not member_checkboxes:
            participant_list = Text("No other users available", color=GREY_500)

        dlg = ft.AlertDialog(
            title=Row(controls=[
                Icon(icon=ft.Icons.EVENT, color=PRIMARY),
                Text("Schedule Meeting")
            ]),
            content=Column(controls=[
                title_field,
                description_field,
                date_field,
                Row(controls=[start_time_field, end_time_field], spacing=10),
                Text("Select Participants:", weight=ft.FontWeight.W_500),
                Container(content=participant_list, height=150, width=450)
            ], tight=True, scroll=ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancel", on_click=lambda ev: setattr(
                    dlg, 'open', False) or self._page.update()),
                ElevatedButton("Schedule", on_click=create_meeting_action,
                               style=ft.ButtonStyle(bgcolor=PRIMARY, color=ON_PRIMARY)),
            ],
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_upload_document_dialog(self, e):
        """Show upload document dialog"""
        name_field = ft.TextField(label="Document Name", width=400)
        description_field = ft.TextField(
            label="Description", width=400, min_lines=2, multiline=True)
        category_dropdown = ft.Dropdown(
            label="Category",
            width=400,
            options=[
                ft.dropdown.Option("general", "General"),
                ft.dropdown.Option("personal", "Personal"),
                ft.dropdown.Option("shared", "Shared"),
                ft.dropdown.Option("group", "Group Document"),
            ],
            value="general"
        )

        # Show info that file picker would be implemented here
        upload_info = Container(
            padding=ft.padding.all(20),
            content=Column(controls=[
                Icon(icon=ft.Icons.UPLOAD_FILE, size=48, color=PRIMARY),
                Text("Document upload feature",
                     size=16, weight=FontWeight.BOLD),
                Text("In production, this would open a file picker",
                     size=12, color=GREY_500),
                Text("For now, documents can be added via the Documents screen",
                     size=11, color=GREY_400),
            ], horizontal_alignment=CrossAxisAlignment.CENTER),
            bgcolor=SURFACE_VARIANT,
            border_radius=10
        )

        def upload_action(btn_event):
            name = name_field.value.strip()
            description = description_field.value.strip()

            if not name:
                self._show_snackbar("Please enter a document name")
                return

            self._show_snackbar(
                "Document upload requires file picker integration")
            dlg.open = False
            self._page.update()

        dlg = ft.AlertDialog(
            title=Row(controls=[
                Icon(icon=ft.Icons.FOLDER, color=PRIMARY),
                Text("Upload Document")
            ]),
            content=Column(controls=[
                name_field,
                description_field,
                category_dropdown,
                upload_info,
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda ev: setattr(
                    dlg, 'open', False) or self._page.update()),
                ElevatedButton("Upload", on_click=upload_action,
                               style=ft.ButtonStyle(bgcolor=PRIMARY, color=ON_PRIMARY)),
            ],
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _join_meeting(self, meeting: Meeting):
        self._show_snackbar(f"Joining {meeting.title}...")

    def _view_email(self, email: Email):
        self._show_snackbar(f"Opening: {email.subject}")

    def _start_video_call(self, e):
        name = self.selected_contact.username if self.selected_contact else "Chat"
        self._show_call_dialog("Video Call", name, ft.Icons.VIDEO_CALL)

    def _start_voice_call(self, e):
        name = self.selected_contact.username if self.selected_contact else "Chat"
        self._show_call_dialog("Voice Call", name, ft.Icons.PHONE)

    def _show_call_dialog(self, call_type: str, name: str, icon):
        dlg = ft.AlertDialog(
            title=Row([Icon(icon=icon, color=GREEN),
                      Text(f"{call_type} with {name}")]),
            content=Column(controls=[
                Container(width=200, height=120, bgcolor=GREY_200, border_radius=10,
                          content=Column(controls=[
                              Icon(icon=icon, size=50, color=GREY_400),
                              Text("Connecting...", color=GREY_500),
                          ], alignment=MainAxisAlignment.CENTER)),
                Text("Requires external integration", size=11, color=GREY_500),
            ], horizontal_alignment=CrossAxisAlignment.CENTER),
            actions=[
                ElevatedButton("End Call", bgcolor=RED, color=WHITE,
                               on_click=lambda e: self._end_call(dlg)),
            ],
        )
        self._page.dialog = dlg
        dlg.open = True
        self._page.update()

    def _end_call(self, dlg):
        dlg.open = False
        self._page.update()
        self._show_snackbar("Call ended")

    def _attach_file(self, e):
        self._show_snackbar("File attachment - Coming soon!")

    def _quick_email(self, e):
        self._show_compose_email(
            Contact(id=0, username="All", email="all@vernika.local", role="Broadcast"))

    def _show_snackbar(self, message: str):
        """Show a snackbar message"""
        try:
            snack = ft.SnackBar(content=ft.Text(message))
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
        except:
            pass

    def _go_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)


def show_chat(page: ft.Page, user):
    """Main entry point to show the chat screen"""
    # Clear existing content and add chat screen
    page.clean()
    chat_screen = ChatScreen(page, user)
    page.add(chat_screen)

    # Perform initial page update
    try:
        page.update()
    except Exception as e:
        print(f"Warning: Initial page update failed: {e}")
