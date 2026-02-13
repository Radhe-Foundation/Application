# Vernika Application - Chat/Messaging Module
# Real-time chat with contacts, groups, and video/voice call features

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import flet as ft
from datetime import datetime
from database.connection import get_session
from database.operations import get_all_users

# Message types


class MessageType(Enum):
    CHAT = "chat"
    LOGIN = "login"
    LOGOUT = "logout"
    GROUP_CREATED = "group_created"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"


@dataclass
class Message:
    """Chat message data class"""
    sender_id: str
    sender_name: str
    content: str
    message_type: MessageType
    timestamp: datetime = None
    recipient_id: str = None  # For direct messages
    group_id: str = None  # For group messages
    is_read: bool = False


@dataclass
class Contact:
    """Contact data class"""
    user_id: str
    username: str
    email: str
    role: str
    status: str  # online, offline, busy
    avatar_url: str = None


@dataclass
class Group:
    """Group chat data class"""
    group_id: str
    name: str
    description: str
    created_by: str
    members: List[str]
    created_at: datetime = None


class ChatView(ft.Column):
    """Main chat view with all features"""

    def __init__(self, page: ft.Page, current_user: dict):
        super().__init__()
        self._page = page  # Use _page instead of page to avoid conflict with ft.Column.page
        self.current_user = current_user
        self.expand = True

        # State
        self.selected_contact = None
        self.selected_group = None
        self.messages: List[Message] = []
        self.contacts: List[Contact] = []
        self.groups: List[Group] = []

        # Initialize sample data
        self._init_sample_data()

        # Build UI
        self._build_ui()

    def _init_sample_data(self):
        """Initialize contacts, groups, and messages from database"""
        with get_session() as db:
            # Load real users as contacts
            db_users = get_all_users(db)
            self.contacts = [
                Contact(
                    user_id=str(u.id),
                    username=u.username,
                    email=u.email,
                    role=u.role.name if u.role else "Unknown",
                    status="online" if u.is_active else "offline"
                )
                for u in db_users if u.username != self.current_user["username"]
            ]

        # For now, keep sample groups (can be enhanced later)
        self.groups = [
            Group("g1", "General", "General discussion",
                  self.current_user["username"], [c.user_id for c in self.contacts[:3]]),
        ]

        # Load messages from database if a contact is selected
        self.messages = []

    def _build_ui(self):
        """Build the chat UI"""
        self.controls = [
            ft.Row(
                expand=True,
                controls=[
                    # Left sidebar - Contacts & Groups
                    self._build_sidebar(),

                    # Vertical divider
                    ft.VerticalDivider(width=1),

                    # Right side - Chat area
                    self._build_chat_area(),
                ]
            )
        ]

    def _build_sidebar(self) -> ft.Container:
        """Build the sidebar with contacts and groups"""
        def create_tab(icon_name, label):
            """Helper to create a Tab with proper Flet 0.25+ syntax"""
            return ft.Tab(
                tab_content=ft.Row([
                    ft.Icon(name=icon_name, size=18),
                    ft.Text(label, size=12)
                ], spacing=3)
            )

        # Tab selector - updated for Flet 0.25+
        self.tab = ft.Tabs(
            selected_index=0,
            tabs=[
                create_tab(ft.Icons.PEOPLE, "Contacts"),
                create_tab(ft.Icons.GROUPS, "Groups"),
                create_tab(ft.Icons.PHONE, "Calls"),
            ],
            on_change=self._on_tab_change,
        )

        # Contact list
        self.contact_list = self._build_contact_list()

        # Group list
        self.group_list = self._build_group_list()

        self.sidebar_content = ft.Container(
            content=ft.Column([
                self.tab,
                ft.Container(height=10),
                self.contact_list,
            ], expand=True),
            expand=True,
        )

        return ft.Container(
            content=self.sidebar_content,
            width=280,
            bgcolor=ft.Colors.SURFACE,
            padding=10,
        )

    def _build_contact_list(self) -> ft.Column:
        """Build the contact list"""
        items = []
        for contact in self.contacts:
            # Status indicator color
            status_color = ft.Colors.GREEN if contact.status == "online" else ft.Colors.GREY if contact.status == "offline" else ft.Colors.ORANGE

            item = ft.Container(
                content=ft.Row([
                    ft.Stack([
                        ft.CircleAvatar(
                            content=ft.Text(contact.username[:1].upper()),
                            radius=22,
                            bgcolor=ft.Colors.BLUE_400,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Container(
                            width=12,
                            height=12,
                            bgcolor=status_color,
                            border_radius=6,
                        ),
                    ]),
                    ft.Column([
                        ft.Text(contact.username,
                                weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(contact.role, size=11,
                                color=ft.Colors.GREY_500),
                    ], expand=True),
                ]),
                padding=10,
                border_radius=8,
                ink=True,
                on_click=lambda e, c=contact: self._select_contact(c),
            )
            items.append(item)

        return ft.Column(items, scroll=ft.ScrollMode.AUTO, expand=True)

    def _build_group_list(self) -> ft.Column:
        """Build the group list"""
        items = []
        for group in self.groups:
            item = ft.Container(
                content=ft.Row([
                    ft.CircleAvatar(
                        content=ft.Icon(ft.Icons.GROUPS,
                                        color=ft.Colors.WHITE),
                        radius=22,
                        bgcolor=ft.Colors.PURPLE_400,
                    ),
                    ft.Column([
                        ft.Text(group.name, weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(f"{len(group.members)} members",
                                size=11, color=ft.Colors.GREY_500),
                    ], expand=True),
                ]),
                padding=10,
                border_radius=8,
                ink=True,
                on_click=lambda e, g=group: self._select_group(g),
            )
            items.append(item)

        return ft.Column(items, scroll=ft.ScrollMode.AUTO, expand=True)

    def _build_chat_area(self) -> ft.Container:
        """Build the main chat area"""
        # Chat header
        self.chat_header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON, size=28, color=ft.Colors.PRIMARY),
                ft.Column([
                    ft.Text("Select a contact or group",
                            weight=ft.FontWeight.BOLD, size=16),
                    ft.Text("Start chatting", size=12,
                            color=ft.Colors.GREY_500),
                ], expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.VIDEO_CALL,
                        tooltip="Video Call",
                        on_click=self._start_video_call,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PHONE,
                        tooltip="Voice Call",
                        on_click=self._start_voice_call,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.MORE_VERT,
                        tooltip="More options",
                    ),
                ]),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.SURFACE,
        )

        # Messages list
        self.message_list = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True,
            padding=10,
        )

        # Message input
        self.message_input = ft.TextField(
            hint_text="Type a message...",
            expand=True,
            min_lines=1,
            max_lines=4,
            on_submit=self._send_message,
        )

        send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            tooltip="Send message",
            on_click=self._send_message,
            bgcolor=ft.Colors.PRIMARY,
            icon_color=ft.Colors.WHITE,
            width=50,
            height=50,
            border_radius=25,
        )

        input_row = ft.Container(
            content=ft.Row([
                self.message_input,
                send_button,
            ]),
            padding=10,
            bgcolor=ft.Colors.SURFACE,
        )

        return ft.Container(
            content=ft.Column([
                self.chat_header,
                ft.Container(
                    content=self.message_list,
                    expand=True,
                    bgcolor=ft.Colors.BLUE_GREY_50,
                ),
                input_row,
            ]),
            expand=True,
        )

    def _on_tab_change(self, e):
        """Handle tab change"""
        tab_index = e.control.selected_index

        if tab_index == 0:
            self.sidebar_content.content.controls[2] = self.contact_list
        elif tab_index == 1:
            self.sidebar_content.content.controls[2] = self.group_list

        self.sidebar_content.content.update()

    def _select_contact(self, contact: Contact):
        """Select a contact to chat with"""
        self.selected_contact = contact
        self.selected_group = None

        # Update header
        self.chat_header.content.controls[0] = ft.Icon(
            ft.Icons.PERSON, size=28, color=ft.Colors.PRIMARY)
        self.chat_header.content.controls[1].controls[0].value = contact.username
        self.chat_header.content.controls[1].controls[1].value = contact.status.capitalize(
        )

        self.chat_header.update()

        # Load messages for this contact
        self._load_messages()

    def _select_group(self, group: Group):
        """Select a group to chat with"""
        self.selected_group = group
        self.selected_contact = None

        # Update header
        self.chat_header.content.controls[0] = ft.Icon(
            ft.Icons.GROUPS, size=28, color=ft.Colors.PURPLE)
        self.chat_header.content.controls[1].controls[0].value = group.name
        self.chat_header.content.controls[1].controls[
            1].value = f"{len(group.members)} members"

        self.chat_header.update()

        # Load messages for this group
        self._load_messages()

    def _load_messages(self):
        """Load messages for selected contact/group"""
        self.message_list.controls.clear()

        for msg in self.messages:
            is_self = msg.sender_id == self.current_user["username"]
            control = self._create_message_control(msg, is_self)
            self.message_list.controls.append(control)

        self.message_list.update()

    def _create_message_control(self, message: Message, is_self: bool) -> ft.Control:
        """Create a message control"""
        # Avatar with initials
        avatar = ft.CircleAvatar(
            content=ft.Text(message.sender_name[:1].upper()),
            color=ft.Colors.WHITE,
            bgcolor=self._get_avatar_color(message.sender_name),
            radius=20,
        )

        # Message bubble colors
        bubble_color = ft.Colors.BLUE_100 if is_self else ft.Colors.GREY_100

        message_content = ft.Column(spacing=5, tight=True)

        if message.message_type == MessageType.CHAT:
            # Sender name (only show for others)
            if not is_self:
                message_content.controls.append(
                    ft.Text(message.sender_name,
                            weight=ft.FontWeight.BOLD, size=12)
                )

            # Message text
            message_content.controls.append(
                ft.Text(message.content, selectable=True)
            )

            # Timestamp
            time_str = message.timestamp.strftime(
                "%H:%M") if message.timestamp else ""
            message_content.controls.append(
                ft.Text(time_str, size=10, color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.RIGHT)
            )

        else:
            # System messages (join/leave)
            message_content.controls.append(
                ft.Text(message.content, italic=True,
                        color=ft.Colors.GREY_500, size=12)
            )

        bubble = ft.Container(
            content=message_content,
            bgcolor=bubble_color,
            border_radius=15,
            padding=10,
            width=300 if not is_self else 250,
        )

        # Layout based on sender
        if is_self:
            return ft.Row([
                ft.Container(expand=True),
                bubble,
                ft.Container(width=10),
                avatar,
            ], alignment=ft.MainAxisAlignment.END)
        else:
            return ft.Row([
                avatar,
                ft.Container(width=10),
                bubble,
                ft.Container(expand=True),
            ])

    def _get_avatar_color(self, user_name: str) -> str:
        """Get avatar color based on username"""
        colors = [
            ft.Colors.AMBER, ft.Colors.BLUE, ft.Colors.BROWN, ft.Colors.CYAN,
            ft.Colors.GREEN, ft.Colors.INDIGO, ft.Colors.LIME, ft.Colors.ORANGE,
            ft.Colors.PINK, ft.Colors.PURPLE, ft.Colors.RED, ft.Colors.TEAL,
        ]
        return colors[hash(user_name) % len(colors)]

    def _send_message(self, e):
        """Send a message"""
        content = self.message_input.value.strip()
        if not content:
            return

        # Create message
        msg = Message(
            sender_id=self.current_user["username"],
            sender_name=self.current_user["username"],
            content=content,
            message_type=MessageType.CHAT,
            timestamp=datetime.now(),
        )

        if self.selected_contact:
            msg.recipient_id = self.selected_contact.user_id
        elif self.selected_group:
            msg.group_id = self.selected_group.group_id

        # Add to messages
        self.messages.append(msg)

        # Add to UI
        control = self._create_message_control(msg, is_self=True)
        self.message_list.controls.append(control)

        # Clear input
        self.message_input.value = ""
        self.message_list.scroll_to(offset=999999)
        self.message_list.update()
        self.message_input.update()

    def _start_video_call(self, e):
        """Start a video call"""
        if not self.selected_contact and not self.selected_group:
            self._show_notification("Select a contact or group first")
            return

        name = self.selected_contact.username if self.selected_contact else self.selected_group.name
        self._show_call_dialog("Video Call", name)

    def _start_voice_call(self, e):
        """Start a voice call"""
        if not self.selected_contact and not self.selected_group:
            self._show_notification("Select a contact or group first")
            return

        name = self.selected_contact.username if self.selected_contact else self.selected_group.name
        self._show_call_dialog("Voice Call", name)

    def _show_notification(self, message: str):
        """Show notification"""
        snack = ft.SnackBar(ft.Text(message))
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_call_dialog(self, call_type: str, name: str):
        """Show call dialog"""
        icon = ft.Icons.VIDEO_CAM if call_type == "Video Call" else ft.Icons.PHONE

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(icon, color=ft.Colors.GREEN),
                ft.Text(f"{call_type} with {name}"),
            ]),
            content=ft.Column([
                ft.Container(
                    width=200,
                    height=150,
                    bgcolor=ft.Colors.GREY_200,
                    border_radius=10,
                    content=ft.Column([
                        ft.Icon(icon, size=60, color=ft.Colors.GREY_400),
                        ft.Text("Connecting...", color=ft.Colors.GREY_500),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
                ft.Text("Call features require external integration",
                        size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.Button("End Call", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE,
                          on_click=lambda e: self._end_call(e, dlg)),
            ],
        )
        self._page.dialog = dlg
        dlg.open = True
        self._page.update()

    def _end_call(self, e, dlg):
        """End the call"""
        dlg.open = False
        self._page.update()
        self._show_notification("Call ended")
