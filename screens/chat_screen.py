"""
Vernika HRA - Chat Screen with Real-time Supabase Support

Features:
- Real-time messaging using Supabase Realtime
- Online presence indicators
- Direct messages between users (admin <-> tanu)
- Automatic message sync
- Future-ready for multiple employees
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Union
import threading

import flet as ft

from database.connection import get_db_session
from database.models import User, UserStatus, ChatMessage as ChatMessageModel
from database.operations import (
    get_all_users,
    get_direct_messages,
    send_chat_message,
    mark_chat_messages_as_read,
    update_user_presence,
)


# Try to import Supabase for real-time features
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase not installed - using polling fallback")


@dataclass
class Contact:
    """Simple view-model for a chat contact."""
    id: int
    username: str
    email: str
    is_online: bool
    last_seen: Optional[datetime]


@dataclass
class ChatMessageVM:
    """View-model used to render chat messages."""
    sender_id: int
    sender_name: str
    content: str
    created_at: datetime
    is_own: bool


class ChatScreen(ft.Container):
    """Main chat screen: contacts on the left, conversation on the right."""

    def __init__(self, page: ft.Page, current_user: Union[dict, User]):
        super().__init__()
        self._page = page
        self.expand = True
        self.bgcolor = ft.Colors.GREY_50

        # Normalize current user
        if isinstance(current_user, dict):
            self.current_user_id: int = int(current_user.get("id", 0))
            self.current_username: str = str(
                current_user.get("username", "User"))
            self.current_email: str = str(
                current_user.get(
                    "email", f"{self.current_username}@vernika.local")
            )
        else:
            self.current_user_id = int(getattr(current_user, "id", 0))
            self.current_username = str(
                getattr(current_user, "username", "User"))
            email = getattr(current_user, "email", None)
            self.current_email = str(
                email or f"{self.current_username}@vernika.local")

        # In-memory view state
        self.contacts: List[Contact] = []
        self.selected_contact: Optional[Contact] = None
        self.messages: List[ChatMessageVM] = []

        # UI references
        self._contacts_column: Optional[ft.Column] = None
        self._messages_list: Optional[ft.ListView] = None
        self._input_field: Optional[ft.TextField] = None
        self._header_title: Optional[ft.Text] = None
        self._header_subtitle: Optional[ft.Text] = None

        # Supabase realtime subscription
        self._realtime_subscription = None
        self._presence_thread = None
        self._stop_threads = False

        # Load contacts and build layout
        self._load_contacts()
        self._update_presence_online()
        self.content = self._build_layout()

        # Start real-time features
        self._start_realtime()

    def _update_presence_online(self):
        """Update user presence to online"""
        try:
            db = get_db_session()
            update_user_presence(db, self.current_user_id, True)
            db.close()
        except Exception as e:
            print(f"[Chat] Error updating presence: {e}")

    def _start_realtime(self):
        """Start real-time features"""
        if SUPABASE_AVAILABLE:
            self._setup_supabase_realtime()
        else:
            # Fallback: Use polling
            self._start_polling()

    def _setup_supabase_realtime(self):
        """Setup Supabase realtime subscription"""
        try:
            from config import SUPABASE_URL, SUPABASE_KEY

            if not SUPABASE_KEY:
                print("[Chat] No Supabase key configured, using polling")
                self._start_polling()
                return

            self._supabase_client: Client = create_client(
                SUPABASE_URL, SUPABASE_KEY)

            # Subscribe to chat_messages table
            self._realtime_subscription = self._supabase_client.channel(
                'chat-messages'
            ).on(
                'postgres_changes',
                {
                    'event': 'INSERT',
                    'schema': 'public',
                    'table': 'chat_messages'
                },
                self._on_new_message
            ).subscribe()

            print("[Chat] Supabase realtime connected")
        except Exception as e:
            print(f"[Chat] Supabase setup failed: {e}")
            self._start_polling()

    def _on_new_message(self, payload):
        """Handle new message from Supabase realtime"""
        try:
            event_type = payload.get('eventType', '')
            if event_type == 'INSERT':
                new_record = payload.get('new', {})
                # Check if message is relevant to current conversation
                receiver_id = new_record.get('receiver_id')
                sender_id = new_record.get('sender_id')

                if (receiver_id == self.current_user_id or
                        sender_id == self.current_user_id):
                    # Reload messages
                    self._load_messages_for_selected()
                    self._refresh_messages_ui()
                    self._page.update()
        except Exception as e:
            print(f"[Chat] Error handling new message: {e}")

    def _start_polling(self):
        """Start polling fallback for real-time updates"""
        def poll_messages():
            while not self._stop_threads:
                try:
                    import time
                    time.sleep(3)  # Poll every 3 seconds
                    if self.selected_contact and not self._stop_threads:
                        # Check for new messages
                        self._load_messages_for_selected()
                        # Only update UI if there are new messages
                        if self._messages_list:
                            self._refresh_messages_ui()
                            try:
                                self._page.update()
                            except:
                                pass
                except Exception as e:
                    print(f"[Chat] Polling error: {e}")

        self._presence_thread = threading.Thread(
            target=poll_messages, daemon=True)
        self._presence_thread.start()

    def _load_contacts(self) -> None:
        """Load all other active users from the database."""
        self.contacts = []

        db = get_db_session()
        try:
            users = (
                db.query(User)
                .filter(
                    User.id != self.current_user_id,
                    User.status == UserStatus.ACTIVE,
                )
                .order_by(User.username.asc())
                .all()
            )

            for user in users:
                self.contacts.append(
                    Contact(
                        id=int(user.id),
                        username=str(user.username or "User"),
                        email=str(
                            user.email or f"{user.username}@vernika.local"),
                        is_online=bool(getattr(user, "is_online", False)),
                        last_seen=getattr(user, "last_seen", None),
                    )
                )
        except Exception as exc:
            print(f"[ChatScreen] Error loading contacts: {exc}")
        finally:
            db.close()

    def _load_messages_for_selected(self) -> None:
        """Load all direct messages between the current user and the selected contact."""
        self.messages = []

        if not self.selected_contact:
            return

        db = get_db_session()
        try:
            db_messages: List[ChatMessageModel] = get_direct_messages(
                db,
                user1_id=self.current_user_id,
                user2_id=self.selected_contact.id,
                limit=200,
            )

            # Oldest first
            db_messages = sorted(
                db_messages,
                key=lambda m: m.created_at or datetime.utcnow(),
            )

            # Map to view-model
            for m in db_messages:
                sender_name = "Unknown"
                try:
                    sender = db.query(User).filter(
                        User.id == m.sender_id).first()
                    if sender and sender.username:
                        sender_name = str(sender.username)
                except Exception:
                    pass

                self.messages.append(
                    ChatMessageVM(
                        sender_id=int(m.sender_id),
                        sender_name=sender_name,
                        content=str(m.content or ""),
                        created_at=m.created_at or datetime.utcnow(),
                        is_own=bool(m.sender_id == self.current_user_id),
                    )
                )

            # Mark all messages from the other user as read
            try:
                mark_chat_messages_as_read(
                    db, user_id=self.current_user_id, sender_id=self.selected_contact.id
                )
            except Exception as exc:
                print(f"[ChatScreen] Failed to mark messages as read: {exc}")

        except Exception as exc:
            print(f"[ChatScreen] Error loading messages: {exc}")
        finally:
            db.close()

    def _build_layout(self) -> ft.Container:
        """Top-level 2-column layout."""
        return ft.Container(
            expand=True,
            content=ft.Row(
                expand=True,
                controls=[
                    self._build_contacts_panel(),
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                    self._build_chat_panel(),
                ],
            ),
        )

    def _build_contacts_panel(self) -> ft.Container:
        """Left-hand panel with contacts."""
        header = ft.Container(
            bgcolor="#2E86AB",
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.WHITE, size=20),
                    ft.Text(
                        "People",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                ],
            ),
        )

        # Search bar
        search_field = ft.TextField(
            hint_text="Search by name...",
            dense=True,
            border_radius=8,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            height=40,
            prefix_icon=ft.Icons.SEARCH,
        )

        self._contacts_column = ft.Column(
            spacing=4, expand=True, scroll=ft.ScrollMode.AUTO)
        self._refresh_contacts_ui()

        def on_search_change(e: ft.ControlEvent) -> None:
            query = (e.control.value or "").strip().lower()
            self._refresh_contacts_ui(search_text=query)
            self._page.update()

        search_field.on_change = on_search_change

        return ft.Container(
            width=260,
            bgcolor=ft.Colors.WHITE,
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(padding=10, content=search_field),
                    ft.Container(
                        padding=ft.padding.only(left=8, right=8, bottom=8),
                        expand=True,
                        content=self._contacts_column,
                    ),
                ],
                expand=True,
            ),
        )

    def _build_chat_panel(self) -> ft.Container:
        """Right-hand panel with header + messages + input."""
        # Header
        self._header_title = ft.Text(
            "Select a person", size=16, weight=ft.FontWeight.BOLD, color="#1A1C1E"
        )
        self._header_subtitle = ft.Text(
            "Start a conversation",
            size=12,
            color=ft.Colors.GREY_600,
        )

        header = ft.Container(
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.CircleAvatar(
                                content=ft.Icon(
                                    ft.Icons.PERSON, color=ft.Colors.WHITE),
                                bgcolor="#2E86AB",
                                radius=18,
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[self._header_title,
                                          self._header_subtitle],
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Refresh messages",
                        on_click=self._on_refresh_clicked,
                    ),
                ],
            ),
        )

        # Messages list
        self._messages_list = ft.ListView(
            expand=True,
            spacing=6,
            padding=ft.padding.all(10),
            auto_scroll=True,
        )
        self._refresh_messages_ui()

        # Input row
        self._input_field = ft.TextField(
            hint_text="Type a message...",
            expand=True,
            min_lines=1,
            max_lines=4,
            border_radius=20,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_submit=self._on_send_clicked,
        )

        send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            tooltip="Send message",
            icon_color=ft.Colors.WHITE,
            bgcolor="#2E86AB",
            on_click=self._on_send_clicked,
        )

        input_row = ft.Container(
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.symmetric(horizontal=10, vertical=10),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self._input_field, send_button],
            ),
        )

        return ft.Container(
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    header,
                    ft.Container(
                        expand=True,
                        bgcolor=ft.Colors.GREY_100,
                        content=self._messages_list,
                    ),
                    input_row,
                ],
            ),
        )

    def _refresh_contacts_ui(self, search_text: str = "") -> None:
        """Rebuild the contact list column."""
        if not self._contacts_column:
            return

        self._contacts_column.controls.clear()
        filtered = self.contacts

        if search_text:
            st = search_text.lower()
            filtered = [
                c
                for c in self.contacts
                if st in c.username.lower() or st in c.email.lower()
            ]

        if not filtered:
            self._contacts_column.controls.append(
                ft.Text("No other users found", color=ft.Colors.GREY_600)
            )
            return

        for contact in filtered:
            self._contacts_column.controls.append(
                self._build_contact_tile(contact))

    def _build_contact_tile(self, contact: Contact) -> ft.Container:
        """Single row in the contacts list."""
        status_color = "#28A745" if contact.is_online else "#9E9E9E"
        status_text = "Online" if contact.is_online else "Offline"

        last_seen_str = ""
        if contact.last_seen and not contact.is_online:
            try:
                last_seen_str = "Last seen " + contact.last_seen.strftime(
                    "%Y-%m-%d %H:%M"
                )
            except Exception:
                last_seen_str = ""

        def on_click(e: ft.ControlEvent) -> None:
            self._on_contact_selected(contact)

        return ft.Container(
            on_click=on_click,
            padding=ft.padding.symmetric(horizontal=4, vertical=4),
            content=ft.Card(
                elevation=0,
                content=ft.Container(
                    padding=8,
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Stack(
                                controls=[
                                    ft.CircleAvatar(
                                        content=ft.Text(
                                            contact.username[:1].upper(),
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        radius=18,
                                        bgcolor="#2E86AB",
                                    ),
                                    ft.Container(
                                        alignment=ft.alignment.Alignment(1, 1),
                                        content=ft.Container(
                                            width=10,
                                            height=10,
                                            bgcolor=status_color,
                                            border_radius=10,
                                            border=ft.border.all(
                                                1, color=ft.Colors.WHITE
                                            ),
                                        ),
                                    ),
                                ]
                            ),
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        contact.username,
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        status_text,
                                        size=11,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Text(
                                        last_seen_str,
                                        size=10,
                                        color=ft.Colors.GREY_500,
                                    )
                                    if last_seen_str
                                    else ft.Container(),
                                ],
                            ),
                        ],
                    ),
                ),
            ),
        )

    def _refresh_messages_ui(self) -> None:
        """Rebuild the messages list UI."""
        if not self._messages_list:
            return

        self._messages_list.controls.clear()

        if not self.selected_contact:
            self._messages_list.controls.append(
                ft.Text(
                    "Select a person from the left panel to start chatting.",
                    color=ft.Colors.GREY_600,
                )
            )
            return

        for msg in self.messages:
            bubble = self._build_message_bubble(msg)
            self._messages_list.controls.append(bubble)

    def _build_message_bubble(self, msg: ChatMessageVM) -> ft.Row:
        """Create a chat bubble row for a single message."""
        align = ft.MainAxisAlignment.END if msg.is_own else ft.MainAxisAlignment.START
        bubble_color = "#DCF8C6" if msg.is_own else ft.Colors.WHITE
        text_color = "#1A1C1E"

        timestamp = msg.created_at.strftime("%H:%M")

        content = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=bubble_color,
            border_radius=ft.border_radius.all(12),
            content=ft.Column(
                spacing=2,
                controls=[
                    ft.Text(msg.sender_name, size=11,
                            color=ft.Colors.GREY_600),
                    ft.Text(msg.content, size=14,
                            color=text_color, selectable=True),
                    ft.Text(
                        timestamp,
                        size=10,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.END,
                    ),
                ],
            ),
        )

        return ft.Row(
            alignment=align,
            controls=[content],
        )

    def _update_header_for_selection(self) -> None:
        """Update header texts based on the selected contact."""
        if not (self._header_title and self._header_subtitle):
            return

        if not self.selected_contact:
            self._header_title.value = "Select a person"
            self._header_subtitle.value = "Start a conversation"
            return

        c = self.selected_contact
        self._header_title.value = c.username
        if c.is_online:
            self._header_subtitle.value = "Online"
        else:
            if c.last_seen:
                try:
                    self._header_subtitle.value = (
                        "Last seen "
                        + c.last_seen.strftime("%Y-%m-%d %H:%M")
                    )
                except Exception:
                    self._header_subtitle.value = "Offline"
            else:
                self._header_subtitle.value = "Offline"

    def _on_contact_selected(self, contact: Contact) -> None:
        """User clicked a contact in the left panel."""
        self.selected_contact = contact
        self._load_messages_for_selected()
        self._update_header_for_selection()
        self._refresh_messages_ui()
        self._page.update()

    def _on_send_clicked(self, e: ft.ControlEvent) -> None:
        """Send button or Enter pressed."""
        if not self._input_field:
            return

        content = (self._input_field.value or "").strip()
        if not content:
            return

        if not self.selected_contact:
            self._show_snackbar("Select a person to chat with first.")
            return

        db = get_db_session()
        try:
            send_chat_message(
                db,
                sender_id=self.current_user_id,
                content=content,
                receiver_id=self.selected_contact.id,
            )
        except Exception as exc:
            print(f"[ChatScreen] Error sending message: {exc}")
            self._show_snackbar(f"Error sending message: {exc}")
        finally:
            db.close()

        # Clear input and reload messages
        self._input_field.value = ""
        self._load_messages_for_selected()
        self._refresh_messages_ui()
        self._page.update()

    def _on_refresh_clicked(self, e: ft.ControlEvent) -> None:
        """Manual refresh button pressed."""
        if not self.selected_contact:
            self._show_snackbar("Select a person first.")
            return

        self._load_messages_for_selected()
        self._refresh_messages_ui()
        self._page.update()

    def _show_snackbar(self, message: str) -> None:
        try:
            snack = ft.SnackBar(content=ft.Text(message))
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
        except Exception as exc:
            print(f"[ChatScreen] Snackbar failed: {exc}")

    def cleanup(self):
        """Cleanup when leaving the screen"""
        self._stop_threads = True
        # Update presence to offline
        try:
            db = get_db_session()
            update_user_presence(db, self.current_user_id, False)
            db.close()
        except:
            pass

        # Unsubscribe from Supabase
        if self._realtime_subscription:
            try:
                self._supabase_client.remove_channel(
                    self._realtime_subscription)
            except:
                pass


def show_chat(page: ft.Page, user: Union[dict, User]) -> None:
    """Helper used elsewhere to show the chat screen full-screen."""
    page.clean()
    page.add(ChatScreen(page, user))
    try:
        page.update()
    except Exception as exc:
        print(f"[ChatScreen] Initial page update failed: {exc}")
