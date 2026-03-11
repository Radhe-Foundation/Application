"""
Vernika HRA - Chat Screen with WhatsApp-Style UI
Real-time messaging with beautiful, modern WhatsApp-like interface
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Union, Dict, Any
import threading
import time

import flet as ft

from database.connection import get_db_session
from database.models import User, UserStatus, ChatMessage as ChatMessageModel, CallLog, CallType, CallStatus
from database.operations import (
    get_direct_messages,
    send_chat_message,
    mark_chat_messages_as_read,
    update_user_presence,
    create_chat_group,
    add_group_member,
    get_user_groups,
    get_group_members,
    get_group_messages,
    initiate_call,
    end_call,
    remove_group_member,
    delete_chat_group,
)


# Try to import Supabase for real-time features
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase not installed - using polling fallback")

# Import Supabase storage for file attachments
from utils.supabase_storage import upload_to_supabase, get_storage


# WhatsApp-Style Theme Colors
PRIMARY = "#075E54"  # WhatsApp dark green
PRIMARY_LIGHT = "#128C7E"  # WhatsApp medium green
PRIMARY_LIGHTER = "#25D366"  # WhatsApp light green
SECONDARY = "#34B7F1"  # WhatsApp blue for links
SUCCESS = "#25D366"
WARNING = "#F44336"
ERROR = "#F44336"
INFO = "#34B7F1"
BACKGROUND = "#ECE5DD"  # WhatsApp light background
CHAT_BACKGROUND = "#ECE5DD"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#667781"
TEXT_TERTIARY = "#9E9E9E"
BORDER = "#E0E0E0"
DIVIDER = "#E8E8E8"

# WhatsApp bubble colors
BUBBLE_SENT = "#DCF8C6"  # WhatsApp sent bubble (light green)
BUBBLE_RECEIVED = "#FFFFFF"  # WhatsApp received bubble (white)
BUBBLE_SENT_DARK = "#075E54"  # Dark mode sent
BUBBLE_RECEIVED_DARK = "#2A2A2A"  # Dark mode received

# WhatsApp Header Gradient
HEADER_BG = "linear-gradient(to right, #075E54, #128C7E)"


@dataclass
class Contact:
    """Simple view-model for a chat contact."""
    id: int
    username: str
    email: str
    is_online: bool = False
    last_seen: Optional[datetime] = None
    avatar_color: str = PRIMARY
    profile_photo: Optional[str] = None
    unread_count: int = 0
    last_message: str = ""
    last_message_time: Optional[datetime] = None


@dataclass
class ChatGroupVM:
    """View-model for chat groups."""
    id: int
    name: str
    description: str
    member_count: int = 0
    created_by: int = 0
    avatar_color: str = PRIMARY_LIGHT
    unread_count: int = 0
    last_message: str = ""
    last_message_time: Optional[datetime] = None


@dataclass
class ChatMessageVM:
    """View-model used to render chat messages."""
    id: Optional[int]
    sender_id: int
    sender_name: str
    content: str
    created_at: datetime
    is_own: bool
    is_read: bool = False
    group_id: Optional[int] = None
    is_image: bool = False
    attachment_name: str = ""
    attachment_path: str = ""


class ChatScreen(ft.Container):
    """Main chat screen: contacts on the left, conversation on the right - WhatsApp Style."""

    def __init__(self, page: ft.Page, current_user: Union[dict, User]):
        super().__init__()
        self._page = page
        self.expand = True
        self.bgcolor = BACKGROUND

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
        self.groups: List[ChatGroupVM] = []
        self.selected_contact: Optional[Contact] = None
        self.selected_group: Optional[ChatGroupVM] = None
        self.is_group_chat: bool = False
        self.messages: List[ChatMessageVM] = []
        self._message_ids: set = set()
        self.search_query = ""

        # Track online status
        self._online_contacts: Dict[int, bool] = {}

        # UI references - initialize as None
        self._contacts_column: Optional[ft.Column] = None
        self._messages_list: Optional[ft.ListView] = None
        self._input_field: Optional[ft.TextField] = None
        self._header_title: Optional[ft.Text] = None
        self._header_subtitle: Optional[ft.Text] = None
        self._search_field: Optional[ft.TextField] = None
        self._empty_state: Optional[ft.Container] = None
        self._tab_button: Optional[ft.SegmentedButton] = None
        self._show_groups: bool = False

        # New UI elements
        self._chat_header: Optional[ft.Container] = None
        self._chat_input_container: Optional[ft.Container] = None
        self._chat_messages_container: Optional[ft.Container] = None

        # Supabase realtime subscription
        self._realtime_subscription = None
        self._presence_thread = None
        self._stop_threads = False

# File picker for attachments - created once and reused
        self._file_picker: Optional[ft.FilePicker] = None

        # Polling thread for presence
        self._presence_poll_thread = None

        # Initialize FilePicker properly (Flet 0.80+ uses async pick_files)
        # Note: FilePicker is a Service, not a Control, so we add it to page.services
        try:
            self._file_picker = ft.FilePicker()
            self._page.services.append(self._file_picker)
        except Exception as e:
            print(f"[Chat] FilePicker init error: {e}")

        # Load contacts and build layout
        self._load_contacts()
        self._load_groups()
        self._update_presence_online()
        self.content = self._build_layout()

        # Start real-time features
        self._start_realtime()

        # Start presence polling
        self._start_presence_polling()

        # Note: Chat notifications are handled in _on_new_message and polling

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
            self._start_polling()

    def _start_presence_polling(self):
        """Poll for user presence updates"""
        def poll_presence():
            while not self._stop_threads:
                try:
                    time.sleep(10)
                    if self._stop_threads:
                        break
                    self._update_online_statuses()
                except Exception as e:
                    print(f"[Chat] Presence poll error: {e}")

        self._presence_poll_thread = threading.Thread(
            target=poll_presence, daemon=True)
        self._presence_poll_thread.start()

    def _update_online_statuses(self):
        """Update online status of all contacts"""
        try:
            db = get_db_session()
            try:
                users = db.query(User).filter(
                    User.id != self.current_user_id).all()
                for user in users:
                    self._online_contacts[user.id] = bool(
                        getattr(user, 'is_online', False))
            finally:
                db.close()
        except Exception as e:
            print(f"[Chat] Error updating presence: {e}")

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
                new_id = new_record.get('id') or new_record.get('message_id')
                if new_id and int(new_id) in self._message_ids:
                    return
                receiver_id = new_record.get('receiver_id')
                sender_id = new_record.get('sender_id')
                group_id = new_record.get('group_id')

                # Get sender name for notification
                sender_name = "Unknown"
                try:
                    db = get_db_session()
                    sender = db.query(User).filter(
                        User.id == sender_id).first()
                    if sender and sender.username:
                        sender_name = str(sender.username)
                    db.close()
                except:
                    pass

                # Check if message is relevant to current chat
                is_relevant = False
                if group_id and self.is_group_chat and self.selected_group:
                    is_relevant = group_id == self.selected_group.id
                elif receiver_id == self.current_user_id or sender_id == self.current_user_id:
                    if self.selected_contact:
                        is_relevant = (receiver_id == self.selected_contact.id or
                                       sender_id == self.selected_contact.id)

                # Show popup notification banner for new messages not from current user
                if sender_id != self.current_user_id:
                    try:
                        from utils.notification_manager import get_notification_manager
                        nm = get_notification_manager()
                        if nm:
                            nm.show_banner_notification(
                                f"Message from {sender_name}",
                                new_record.get('content', '')[:50],
                                "chat_message",
                                5
                            )
                    except Exception as e:
                        print(f"[Chat] Notification error: {e}")

                # Refresh contacts to update unread counts and reorder
                self._refresh_contacts_for_new_messages()

                if is_relevant:
                    self._load_messages_for_selected()
                    self._refresh_messages_ui()
                    try:
                        self._page.update()
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Chat] Error handling new message: {e}")

    def _start_polling(self):
        """Start polling fallback for real-time updates"""
        def poll_messages():
            last_message_count = 0
            while not self._stop_threads:
                try:
                    time.sleep(5)

                    # Refresh contacts and groups to check for new messages
                    self._refresh_contacts_for_new_messages()

                    if self.selected_contact and not self._stop_threads:
                        # Load messages and check for new ones
                        old_count = len(self.messages)
                        self._load_messages_for_selected()
                        new_count = len(self.messages)

                        # Show notification for new messages
                        if new_count > old_count:
                            # Get the latest message
                            latest_msg = self.messages[-1] if self.messages else None
                            if latest_msg and not latest_msg.is_own:
                                # Show popup notification banner
                                try:
                                    from utils.notification_manager import get_notification_manager
                                    nm = get_notification_manager()
                                    if nm:
                                        nm.show_banner_notification(
                                            f"Message from {latest_msg.sender_name}",
                                            latest_msg.content[:50],
                                            "chat_message",
                                            5
                                        )
                                except Exception as e:
                                    print(
                                        f"[Chat] Polling notification error: {e}")

                        if self._messages_list:
                            self._refresh_messages_ui()
                            try:
                                self._page.update()
                            except Exception:
                                pass
                except Exception as e:
                    print(f"[Chat] Polling error: {e}")

        self._presence_thread = threading.Thread(
            target=poll_messages, daemon=True)
        self._presence_thread.start()
        print("[Chat] Polling started (every 5 seconds)")

    def _refresh_contacts_for_new_messages(self):
        """Refresh contacts to check for new messages and reorder conversations"""
        try:
            db = get_db_session()

            # Get unread message counts for each contact
            from database.models import ChatMessage
            from sqlalchemy import or_, func

            for contact in self.contacts:
                # Get unread messages count for this contact
                unread_count = db.query(func.count(ChatMessage.id)).filter(
                    ChatMessage.receiver_id == self.current_user_id,
                    ChatMessage.sender_id == contact.id,
                    ChatMessage.is_read == False,
                    ChatMessage.group_id == None
                ).scalar() or 0

                # Update unread count
                contact.unread_count = unread_count

                # Get last message time and content
                last_msg = db.query(ChatMessage).filter(
                    or_(
                        (ChatMessage.sender_id == self.current_user_id) & (
                            ChatMessage.receiver_id == contact.id),
                        (ChatMessage.sender_id == contact.id) & (
                            ChatMessage.receiver_id == self.current_user_id)
                    ),
                    ChatMessage.group_id == None
                ).order_by(ChatMessage.created_at.desc()).first()

                if last_msg:
                    contact.last_message_time = last_msg.created_at
                    contact.last_message = (last_msg.content[:30] + "..." if len(
                        last_msg.content or "") > 30 else last_msg.content or "") if last_msg.content else ""

            # Get unread counts for groups
            for group in self.groups:
                unread_count = db.query(func.count(ChatMessage.id)).filter(
                    ChatMessage.receiver_id == self.current_user_id,
                    ChatMessage.group_id == group.id,
                    ChatMessage.is_read == False
                ).scalar() or 0

                group.unread_count = unread_count

                # Get last message for group
                last_msg = db.query(ChatMessage).filter(
                    ChatMessage.group_id == group.id
                ).order_by(ChatMessage.created_at.desc()).first()

                if last_msg:
                    group.last_message_time = last_msg.created_at
                    group.last_message = (last_msg.content[:30] + "..." if len(
                        last_msg.content or "") > 30 else last_msg.content or "") if last_msg.content else ""

            db.close()

            # Sort contacts by last message time (most recent first), but keep contacts with unread at top
            # Separate contacts with unread messages from those without
            contacts_with_unread = [
                c for c in self.contacts if c.unread_count > 0]
            contacts_without_unread = [
                c for c in self.contacts if c.unread_count == 0]

            # Sort each group by last message time
            contacts_with_unread.sort(
                key=lambda x: x.last_message_time or datetime.min, reverse=True)
            contacts_without_unread.sort(
                key=lambda x: x.last_message_time or datetime.min, reverse=True)

            # Combine: unread contacts first, then the rest
            self.contacts = contacts_with_unread + contacts_without_unread

            # Same for groups
            groups_with_unread = [g for g in self.groups if g.unread_count > 0]
            groups_without_unread = [
                g for g in self.groups if g.unread_count == 0]

            groups_with_unread.sort(
                key=lambda x: x.last_message_time or datetime.min, reverse=True)
            groups_without_unread.sort(
                key=lambda x: x.last_message_time or datetime.min, reverse=True)

            self.groups = groups_with_unread + groups_without_unread

            # Refresh UI if we have contacts column
            if self._contacts_column:
                search_val = self._search_field.value if self._search_field else ""
                self._refresh_contacts_ui(search_text=search_val)

        except Exception as e:
            print(f"[Chat] Error refreshing contacts for new messages: {e}")

    def _load_contacts(self) -> None:
        """Load all other active users from the database."""
        self.contacts = []
        self._online_contacts = {}

        # Get profile photos from Employee table
        profile_photos = {}
        try:
            from database.models import Employee
            db = get_db_session()
            employees = db.query(Employee.user_id, Employee.profile_photo).filter(
                Employee.user_id.isnot(None),
                Employee.profile_photo.isnot(None)
            ).all()
            for emp in employees:
                if emp.user_id:
                    profile_photos[int(emp.user_id)] = emp.profile_photo
            db.close()
        except Exception as e:
            print(f"[Chat] Error loading profile photos: {e}")

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
                # Get real online status and last_seen from database
                is_online = bool(getattr(user, "is_online", False))
                last_seen = getattr(user, "last_seen", None)

                # Update online contacts tracking
                self._online_contacts[user.id] = is_online

                # Get last message preview
                last_msg = ""
                try:
                    messages = get_direct_messages(
                        db, self.current_user_id, user.id, limit=1)
                    if messages:
                        last_msg = messages[0].content[:30] + "..." if len(
                            messages[0].content or "") > 30 else messages[0].content or ""
                except:
                    pass

                # Get profile photo from Employee table
                user_id = int(user.id)
                profile_photo = profile_photos.get(user_id)

                self.contacts.append(
                    Contact(
                        id=int(user.id),
                        username=str(user.username or "User"),
                        email=str(
                            user.email or f"{user.username}@vernika.local"),
                        is_online=is_online,
                        last_seen=last_seen,
                        avatar_color=self._get_avatar_color(
                            str(user.username or "User")),
                        profile_photo=profile_photo,
                        last_message=last_msg
                    )
                )
        except Exception as exc:
            print(f"[ChatScreen] Error loading contacts: {exc}")
        finally:
            db.close()

    def _load_groups(self) -> None:
        """Load user's chat groups"""
        self.groups = []
        db = get_db_session()
        try:
            user_groups = get_user_groups(db, self.current_user_id)

            # Debug logging
            print(
                f"[Chat] Found {len(user_groups) if user_groups else 0} groups for user {self.current_user_id}")

            if not user_groups:
                print("[Chat] No groups found for user")
                return

            for g in user_groups:
                # Safely get group id
                try:
                    group_id = int(g.id) if g.id is not None else 0
                except (TypeError, ValueError):
                    group_id = 0

                if group_id == 0:
                    continue

                # Count members in each group
                try:
                    members = get_group_members(
                        db, group_id) if group_id else []
                    member_count = len(members) if members else 0
                except Exception:
                    member_count = 0

                # Get last message preview
                last_msg = ""
                try:
                    messages = get_group_messages(db, group_id, limit=1)
                    if messages:
                        last_msg_content = getattr(
                            messages[0], 'content', None) or ""
                        if last_msg_content:
                            last_msg = last_msg_content[:30] + "..." if len(
                                last_msg_content) > 30 else last_msg_content
                except:
                    pass

                # Get group name safely
                try:
                    name = str(g.name) if g.name else "Group"
                except Exception:
                    name = "Group"

                # Get description safely
                try:
                    desc = str(g.description) if g.description else ""
                except Exception:
                    desc = ""

                # Get created_by safely
                try:
                    created_by = int(g.created_by) if g.created_by else 0
                except (TypeError, ValueError):
                    created_by = 0

                print(
                    f"[Chat] Loading group: {name} (id: {group_id}, members: {member_count})")

                self.groups.append(ChatGroupVM(
                    id=group_id,
                    name=name,
                    description=desc,
                    member_count=member_count,
                    created_by=created_by,
                    avatar_color=PRIMARY_LIGHT,
                    last_message=last_msg
                ))

            print(f"[Chat] Total groups loaded: {len(self.groups)}")

        except Exception as exc:
            print(f"[ChatScreen] Error loading groups: {exc}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

    def _load_messages_for_selected(self) -> None:
        """Load all direct messages between the current user and the selected contact OR group messages."""
        new_messages: List[ChatMessageVM] = []
        self._message_ids = set()

        if self.is_group_chat and self.selected_group:
            # Load group messages
            self._load_group_messages()
            return
        elif not self.selected_contact:
            return

        db = get_db_session()
        try:
            db_messages: List[ChatMessageModel] = get_direct_messages(
                db,
                user1_id=self.current_user_id,
                user2_id=self.selected_contact.id,
                limit=200,
            )

            # Sort messages by created_at
            try:
                db_messages = sorted(
                    db_messages,
                    key=lambda m: m.created_at or datetime.utcnow(),
                )
            except Exception:
                pass

            for m in db_messages:
                sender_name = "Unknown"
                try:
                    sender = db.query(User).filter(
                        User.id == m.sender_id).first()
                    if sender and sender.username:
                        sender_name = str(sender.username)
                except Exception:
                    pass

                # Get message ID safely
                try:
                    msg_id = int(getattr(m, 'id', 0) or 0)
                except (TypeError, ValueError):
                    msg_id = 0

                # Get created_at safely
                try:
                    created_at = m.created_at if m.created_at else datetime.utcnow()
                except Exception:
                    created_at = datetime.utcnow()

                # Check if has attachment
                has_attachment = getattr(m, 'has_attachment', False)
                attachment_path = getattr(m, 'attachment_path', "")

                vm = ChatMessageVM(
                    id=msg_id or None,
                    sender_id=int(m.sender_id),
                    sender_name=sender_name,
                    content=str(m.content or ""),
                    created_at=created_at,
                    is_own=bool(m.sender_id == self.current_user_id),
                    is_read=bool(getattr(m, 'is_read', False)),
                    is_image=has_attachment and attachment_path and any(attachment_path.lower(
                    ).endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']),
                    attachment_name=attachment_path.split(
                        '/')[-1] if attachment_path else "",
                    attachment_path=attachment_path if attachment_path else ""
                )

                if vm.id is None or vm.id not in self._message_ids:
                    new_messages.append(vm)
                    if vm.id:
                        self._message_ids.add(vm.id)

            self.messages = new_messages

            # Mark messages as read
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

    def _load_group_messages(self) -> None:
        """Load messages for selected group"""
        if not self.selected_group:
            return

        new_messages: List[ChatMessageVM] = []

        db = get_db_session()
        try:
            db_messages = get_group_messages(
                db, self.selected_group.id, limit=200)

            # Sort messages
            try:
                db_messages = sorted(
                    db_messages,
                    key=lambda m: m.created_at or datetime.utcnow(),
                )
            except Exception:
                pass

            for m in db_messages:
                sender_name = "Unknown"
                try:
                    sender = db.query(User).filter(
                        User.id == m.sender_id).first()
                    if sender and sender.username:
                        sender_name = str(sender.username)
                except Exception:
                    pass

                try:
                    msg_id = int(getattr(m, 'id', 0) or 0)
                except (TypeError, ValueError):
                    msg_id = 0

                try:
                    created_at = m.created_at if m.created_at else datetime.utcnow()
                except Exception:
                    created_at = datetime.utcnow()

                # Check if has attachment
                has_attachment = getattr(m, 'has_attachment', False)
                attachment_path = getattr(m, 'attachment_path', "")

                vm = ChatMessageVM(
                    id=msg_id or None,
                    sender_id=int(m.sender_id),
                    sender_name=sender_name,
                    content=str(m.content or ""),
                    created_at=created_at,
                    is_own=bool(m.sender_id == self.current_user_id),
                    is_read=bool(getattr(m, 'is_read', False)),
                    group_id=self.selected_group.id,
                    is_image=has_attachment and attachment_path and any(attachment_path.lower(
                    ).endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']),
                    attachment_name=attachment_path.split(
                        '/')[-1] if attachment_path else "",
                    attachment_path=attachment_path if attachment_path else ""
                )

                if vm.id is None or vm.id not in self._message_ids:
                    new_messages.append(vm)
                    if vm.id:
                        self._message_ids.add(vm.id)

            self.messages = new_messages

        except Exception as exc:
            print(f"[ChatScreen] Error loading group messages: {exc}")
        finally:
            db.close()

    def _build_layout(self) -> ft.Container:
        """Top-level 2-column layout with WhatsApp styling."""
        return ft.Container(
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Row(
                expand=True,
                controls=[
                    self._build_contacts_panel(),
                    ft.VerticalDivider(width=1, color=DIVIDER),
                    self._build_chat_panel(),
                ],
            ),
        )

    def _build_contacts_panel(self) -> ft.Container:
        """Left-hand panel with contacts - WhatsApp style - Responsive"""

        # Calculate responsive width based on page width
        # Default to 380px, but scale for smaller screens
        def get_contacts_panel_width():
            try:
                page_width = self._page.window_width if hasattr(
                    self._page, 'window_width') else 1200
                if page_width < 500:
                    return page_width  # Full width on mobile
                elif page_width < 800:
                    return min(320, page_width - 50)
                else:
                    return 380
            except:
                return 380

        contacts_panel_width = get_contacts_panel_width()

        # Header with title and create group button - WhatsApp style
        header = ft.Container(
            bgcolor=PRIMARY,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            content=ft.Row(
                controls=[
                    # Profile avatar
                    ft.CircleAvatar(
                        content=ft.Text(
                            self.current_username[:1].upper(),
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=PRIMARY,
                        ),
                        radius=18,
                        bgcolor="#DDFFDD",
                    ),
                    ft.Column(
                        spacing=0,
                        controls=[
                            ft.Text(
                                self.current_username,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                "online",
                                size=12,
                                color="#B3FFDD",
                            ),
                        ],
                    ),
                    ft.Container(expand=True),
                    # WhatsApp-style header icons - Removed Status button as requested
                    ft.IconButton(
                        icon=ft.Icons.GROUP_ADD,
                        icon_color="#DDFFDD",
                        tooltip="New Group",
                        on_click=self._show_create_group_dialog,
                    ),
                ],
            ),
        )

        # Search field - WhatsApp style - Fixed alignment
        self._search_field = ft.TextField(
            hint_text="Search or start new chat",
            dense=True,
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            fill_color=ft.Colors.WHITE,
            cursor_color=PRIMARY,
            text_size=14,
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

        def on_search_change(e):
            query = (e.control.value or "").strip().lower()
            self._refresh_contacts_ui(search_text=query)
            try:
                self._page.update()
            except Exception:
                pass

        self._search_field.on_change = on_search_change

        # Tab switcher for Contacts/Groups - WhatsApp style - Fixed alignment
        def on_tab_change(e):
            selected_value = e.control.selected
            # Handle both string and list selection
            if isinstance(selected_value, list):
                selected_value = selected_value[0] if selected_value else "0"
            # Convert to int for comparison
            try:
                tab_index = int(selected_value)
            except (ValueError, TypeError):
                tab_index = 0
            self._show_groups = tab_index == 1
            self._refresh_contacts_ui(
                search_text=self._search_field.value if self._search_field else "")
            try:
                self._page.update()
            except Exception:
                pass

        self._tab_button = ft.SegmentedButton(
            segments=[
                ft.Segment(value="0", label=ft.Text("Chats", size=13)),
                ft.Segment(value="1", label=ft.Text("Groups", size=13)),
            ],
            selected=["0"],
            on_change=on_tab_change,
        )

        self._contacts_column = ft.Column(
            spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
        self._refresh_contacts_ui()

        return ft.Container(
            width=contacts_panel_width,
            bgcolor=ft.Colors.WHITE,
            content=ft.Column(
                spacing=0,
                controls=[
                    header,
                    # Search container - fixed alignment
                    ft.Container(
                        bgcolor="#F0F0F0",
                        padding=ft.padding.only(
                            left=8, right=8, top=8, bottom=4),
                        content=ft.Container(
                            border_radius=8,
                            bgcolor=ft.Colors.WHITE,
                            content=self._search_field
                        )
                    ),
                    # Tab buttons - fixed alignment with center alignment
                    ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        padding=ft.padding.only(
                            left=16, right=16, top=4, bottom=8),
                        alignment=ft.alignment.Alignment(0, 0),
                        content=self._tab_button
                    ),
                    ft.Container(
                        expand=True,
                        content=self._contacts_column,
                    ),
                ],
                expand=True,
            ),
        )

    def _show_create_group_dialog(self, e=None):
        """Show dialog to create a new group"""
        def close_dlg(ev):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        name_field = ft.TextField(
            label="Group Name",
            border_color=PRIMARY,
            hint_text="Enter group name",
            prefix_icon=ft.Icons.GROUP
        )
        desc_field = ft.TextField(
            label="Description (optional)",
            multiline=True,
            min_lines=2,
            border_color=PRIMARY,
            hint_text="Group description"
        )

        # Member selection - filter out current user
        available_contacts = [c for c in self.contacts]

        member_chks = []
        for contact in available_contacts:
            # Use Checkbox for selection tracking
            chk = ft.Checkbox(value=False)
            member_chks.append(chk)

        # Create display rows with checkboxes
        member_rows = []
        for i, contact in enumerate(available_contacts):
            member_rows.append(
                ft.ListTile(
                    leading=member_chks[i],
                    title=ft.Text(contact.username, size=14),
                    subtitle=ft.Text(contact.email, size=11,
                                     color=TEXT_SECONDARY),
                    dense=True,
                    content_padding=ft.padding.symmetric(horizontal=8),
                )
            )

        error_txt = ft.Text("", color=ERROR, size=12, visible=False)

        def create_group(ev):
            group_name = name_field.value.strip() if name_field.value else ""

            if not group_name:
                error_txt.value = "Please enter a group name"
                error_txt.visible = True
                try:
                    self._page.update()
                except Exception:
                    pass
                return

            # Get selected members
            selected_members = []
            for i, contact in enumerate(available_contacts):
                if i < len(member_chks) and member_chks[i].value:
                    selected_members.append(contact.id)

            if not selected_members:
                error_txt.value = "Please select at least one member"
                error_txt.visible = True
                try:
                    self._page.update()
                except Exception:
                    pass
                return

            try:
                db = get_db_session()
                group = create_chat_group(
                    db,
                    group_name,
                    desc_field.value or "",
                    self.current_user_id
                )

                # Add members
                for member_id in selected_members:
                    add_group_member(db, group.id, member_id, role="member")

                db.close()
                self._show_success(f"Group '{group_name}' created!")

                # Reload groups
                self._load_groups()

                # Close dialog first
                close_dlg(ev)

                # Switch to groups tab
                self._show_groups = True

                # Rebuild layout
                self.content = self._build_layout()

                # Update tab selection
                if self._tab_button:
                    self._tab_button.selected = ["1"]
                    try:
                        self._tab_button.update()
                    except Exception:
                        pass

                # Refresh UI
                self._refresh_contacts_ui(
                    search_text=self._search_field.value if self._search_field else "")
                try:
                    self._page.update()
                except Exception:
                    pass

            except Exception as ex:
                error_txt.value = f"Error: {str(ex)}"
                error_txt.visible = True
                try:
                    self._page.update()
                except Exception:
                    pass

        dlg = ft.AlertDialog(
            title=ft.Text("Create New Group", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                height=450,
                content=ft.Column([
                    name_field,
                    ft.Container(height=8),
                    desc_field,
                    ft.Container(height=12),
                    ft.Text("Select Members:", size=14,
                            weight=ft.FontWeight.W_500),
                    ft.Container(height=8),
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            controls=member_rows,
                            spacing=0,
                        ) if member_rows else ft.Text("No contacts available", size=12, color=TEXT_TERTIARY)
                    ),
                    error_txt
                ], tight=True, scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg,
                              style=ft.ButtonStyle(color=TEXT_SECONDARY)),
                ft.ElevatedButton(
                    "Create Group",
                    on_click=create_group,
                    bgcolor=PRIMARY,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8))
                ),
            ]
        )
        self._page.show_dialog(dlg)

    def _show_add_member_dialog(self, group: ChatGroupVM):
        """Show dialog to add members to an existing group"""
        def close_dlg(ev):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        # Get current group members
        db = get_db_session()
        try:
            current_members = get_group_members(db, group.id)
            current_member_ids = {m.user_id for m in current_members}
        except Exception as exc:
            print(f"[ChatScreen] Error getting group members: {exc}")
            current_member_ids = set()
        finally:
            db.close()

        # Filter contacts not already in group
        available_contacts = [
            c for c in self.contacts if c.id not in current_member_ids]

        if not available_contacts:
            dlg = ft.AlertDialog(
                title=ft.Text(f"Add Members to '{group.name}'"),
                content=ft.Column([
                    ft.Text("No contacts available to add.",
                            size=14, color=TEXT_SECONDARY),
                    ft.Text("All your contacts are already members of this group.",
                            size=12, color=TEXT_TERTIARY),
                ], tight=True),
                actions=[ft.TextButton("Close", on_click=close_dlg)]
            )
            self._page.show_dialog(dlg)
            return

        # Member selection - use Checkbox for selection tracking
        member_chks = []
        for contact in available_contacts:
            chk = ft.Checkbox(value=False)
            member_chks.append(chk)

        # Create display rows with checkboxes
        member_rows = []
        for i, contact in enumerate(available_contacts):
            member_rows.append(
                ft.ListTile(
                    leading=member_chks[i],
                    title=ft.Text(contact.username, size=14),
                    dense=True,
                    content_padding=ft.padding.symmetric(horizontal=8),
                )
            )

        error_txt = ft.Text("", color=ERROR, size=12, visible=False)

        def add_members(ev):
            selected_members = []
            for i, contact in enumerate(available_contacts):
                if i < len(member_chks) and member_chks[i].value:
                    selected_members.append(contact.id)

            if not selected_members:
                error_txt.value = "Please select at least one member"
                error_txt.visible = True
                try:
                    self._page.update()
                except Exception:
                    pass
                return

            try:
                db = get_db_session()
                for member_id in selected_members:
                    add_group_member(db, group.id, member_id, role="member")
                db.close()

                self._show_success(
                    f"Added {len(selected_members)} member(s) to '{group.name}'!")
                self._load_groups()
                close_dlg(ev)

                # Refresh UI
                self._show_groups = True
                self.content = self._build_layout()

                if self._tab_button:
                    self._tab_button.selected = ["1"]
                    try:
                        self._tab_button.update()
                    except Exception:
                        pass

                self._refresh_contacts_ui(
                    search_text=self._search_field.value if self._search_field else "")
                try:
                    self._page.update()
                except Exception:
                    pass
            except Exception as ex:
                error_txt.value = f"Error: {str(ex)}"
                error_txt.visible = True
                try:
                    self._page.update()
                except Exception:
                    pass

        dlg = ft.AlertDialog(
            title=ft.Text(f"Add Members to '{group.name}'"),
            content=ft.Container(
                width=350,
                height=350,
                content=ft.Column([
                    ft.Text("Select members to add:", size=14,
                            weight=ft.FontWeight.W_500),
                    ft.Container(height=8),
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            controls=member_rows,
                            spacing=0,
                        )
                    ),
                    error_txt
                ], tight=True, scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton(
                    "Add Members", on_click=add_members, bgcolor=PRIMARY, color="white"),
            ]
        )
        self._page.show_dialog(dlg)

    def _show_leave_group_dialog(self, group: ChatGroupVM):
        """Show dialog to leave a group"""
        def close_dlg(ev):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        def leave_group(ev):
            try:
                db = get_db_session()
                remove_group_member(db, group.id, self.current_user_id)
                db.close()

                self._show_success(f"You left the group '{group.name}'")
                close_dlg(ev)

                # Clear selection if this was the selected group
                if self.selected_group and self.selected_group.id == group.id:
                    self.selected_group = None
                    self.is_group_chat = False
                    self.messages = []

                # Reload groups
                self._load_groups()
                self.content = self._build_layout()
                self._refresh_contacts_ui()
                try:
                    self._page.update()
                except Exception:
                    pass
            except Exception as ex:
                self._show_error(f"Error leaving group: {ex}")

        dlg = ft.AlertDialog(
            title=ft.Text(f"Leave '{group.name}'?"),
            content=ft.Text(f"Are you sure you want to leave '{group.name}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton(
                    "Leave Group", on_click=leave_group, bgcolor=ERROR, color="white"),
            ]
        )
        self._page.show_dialog(dlg)

    def _show_delete_group_dialog(self, group: ChatGroupVM):
        """Show dialog to delete a group (creator only)"""
        def close_dlg(ev):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        def delete_group(ev):
            try:
                db = get_db_session()
                delete_chat_group(db, group.id)
                db.close()

                self._show_success(f"Group '{group.name}' has been deleted")
                close_dlg(ev)

                # Clear selection if this was the selected group
                if self.selected_group and self.selected_group.id == group.id:
                    self.selected_group = None
                    self.is_group_chat = False
                    self.messages = []

                # Reload groups
                self._load_groups()
                self.content = self._build_layout()
                self._refresh_contacts_ui()
                try:
                    self._page.update()
                except Exception:
                    pass
            except Exception as ex:
                self._show_error(f"Error deleting group: {ex}")

        dlg = ft.AlertDialog(
            title=ft.Text(f"Delete '{group.name}'?"),
            content=ft.Text(
                f"Are you sure you want to delete '{group.name}'? This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton(
                    "Delete Group", on_click=delete_group, bgcolor=ERROR, color="white"),
            ]
        )
        self._page.show_dialog(dlg)

    def _build_chat_panel(self) -> ft.Container:
        """Right-hand panel with header + messages + input - WhatsApp style"""

        # Header title and subtitle
        self._header_title = ft.Text(
            "Vernika Drop",
            size=16,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.WHITE
        )
        self._header_subtitle = ft.Text(
            "",
            size=12,
            color="#B3FFDD",
        )

        # WhatsApp-style header
        header = ft.Container(
            bgcolor=PRIMARY,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    # Contact/Group info
                    ft.Row(
                        spacing=10,
                        controls=[
                            self._build_back_button(),
                            ft.CircleAvatar(
                                content=ft.Icon(
                                    ft.Icons.PERSON, color=PRIMARY, size=20),
                                bgcolor="#DDFFDD",
                                radius=20,
                            ),
                            ft.Column(
                                spacing=0,
                                controls=[self._header_title,
                                          self._header_subtitle],
                            ),
                        ],
                    ),
                    # Action buttons - WhatsApp style (voice/video call buttons removed as per requirement)
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.MORE_VERT,
                            tooltip="More",
                            on_click=self._show_chat_options,
                            icon_color="#DDFFDD",
                            icon_size=22,
                        ),
                    ], spacing=0),
                ],
            ),
        )

        # Messages list with WhatsApp background
        self._messages_list = ft.ListView(
            expand=True,
            spacing=4,
            padding=ft.padding.all(12),
            auto_scroll=True,
        )

        # Empty state - WhatsApp style with chat bubble icon
        self._empty_state = ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    # Chat bubble icon container - properly centered (circular)
                    ft.Container(
                        width=150,
                        height=150,
                        bgcolor=PRIMARY_LIGHT,
                        border_radius=75,  # Circular - half of 150px
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHAT_BUBBLE_OUTLINE,
                                    size=50,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Container(height=4),
                                ft.Text(
                                    "Drop",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(height=24),
                    ft.Text("Send and receive messages", size=16,
                            weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                    ft.Text("Your personal messages are end-to-end encrypted",
                            size=13, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=2,
            ),
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
        )

        self._refresh_messages_ui()

        # Input field - WhatsApp style
        self._input_field = ft.TextField(
            hint_text="Message...",
            expand=True,
            min_lines=1,
            max_lines=5,
            border_radius=20,
            filled=True,
            fill_color=ft.Colors.WHITE,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=PRIMARY,
            cursor_color=PRIMARY,
            text_size=15,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=10),
            on_submit=self._on_send_clicked,
        )

        def on_send_click(e):
            self._on_send_clicked(e)

        input_row = ft.Container(
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.symmetric(horizontal=8, vertical=8),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EMOJI_EMOTIONS,
                        icon_color=TEXT_SECONDARY,
                        on_click=self._show_emoji_picker,
                        tooltip="Emoji",
                        icon_size=24,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ATTACH_FILE,
                        icon_color=TEXT_SECONDARY,
                        on_click=self._on_attach_file,
                        tooltip="Attach File",
                        icon_size=24,
                    ),
                    self._input_field,
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.SEND,
                            tooltip="Send",
                            icon_color=ft.Colors.WHITE,
                            bgcolor=PRIMARY,
                            on_click=on_send_click,
                            width=42, height=42,
                            style=ft.ButtonStyle(
                                shape=ft.CircleBorder(),
                                bgcolor=PRIMARY,
                            )
                        ),
                    ),
                ],
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=CHAT_BACKGROUND,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    header,
                    ft.Container(
                        expand=True,
                        bgcolor=CHAT_BACKGROUND,
                        content=ft.Column(
                            expand=True,
                            spacing=0,
                            controls=[
                                self._messages_list,
                                self._empty_state,
                            ],
                        ),
                    ),
                    input_row,
                ],
            ),
        )

    def _build_back_button(self) -> ft.Container:
        """Build a back button for mobile view"""
        return ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color="#DDFFDD",
                icon_size=22,
                on_click=lambda e: self._show_contact_list(),
                visible=False,  # Hidden on desktop by default
            ),
            on_click=lambda e: self._show_contact_list(),
        )

    def _show_contact_list(self):
        """Show contact list (for mobile view)"""
        # This would toggle a view - simplified for now
        pass

    def _show_chat_options(self, e=None):
        """Show chat options menu"""
        def close_dlg(ev):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        options = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.GROUP_ADD, color=PRIMARY),
                title=ft.Text("Add to group"),
                on_click=lambda e: (close_dlg(e), self._show_add_member_dialog(
                    self.selected_group) if self.is_group_chat and self.selected_group else self._show_snackbar("Select a group first")),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.IMAGE, color=PRIMARY),
                title=ft.Text("Media"),
                on_click=lambda e: (close_dlg(e), self._show_snackbar(
                    "Media viewer coming soon!")),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.SEARCH, color=PRIMARY),
                title=ft.Text("Search"),
                on_click=lambda e: (
                    close_dlg(e), self._show_snackbar("Search coming soon!")),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.NOTIFICATIONS, color=PRIMARY),
                title=ft.Text("Mute notifications"),
                on_click=lambda e: (
                    close_dlg(e), self._show_snackbar("Muted!")),
            ),
        ]

        if self.is_group_chat and self.selected_group:
            if self.selected_group.created_by == self.current_user_id:
                options.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DELETE, color=ERROR),
                        title=ft.Text("Delete group"),
                        on_click=lambda e: (
                            close_dlg(e), self._show_delete_group_dialog(self.selected_group)),
                    )
                )
            else:
                options.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOGOUT, color=ERROR),
                        title=ft.Text("Leave group"),
                        on_click=lambda e: (
                            close_dlg(e), self._show_leave_group_dialog(self.selected_group)),
                    )
                )

        dlg = ft.AlertDialog(
            content=ft.Column(
                controls=options,
                spacing=0,
                tight=True,
            ),
            actions=[],
        )
        self._page.show_dialog(dlg)

    def _show_emoji_picker(self, e=None):
        """Show emoji picker dialog with a simple scrollable emoji grid"""
        def close_dlg(ev):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        # Combine all emojis into one flat list
        all_emojis = [
            # Smileys
            "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃", "😉", "😊", "😇", "🥰", "😍", "🤩",
            "😘", "😗", "😚", "😙", "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐", "🤨",
            "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥", "😌", "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕",
            "🤢", "🤮", "🤧", "🥵", "🥶", "🥴", "😵", "🤯", "🤠", "🥳", "😎", "🤓", "🧐", "😕", "😟", "🙁",
            "☹️", "😮", "😯", "😲", "😳", "🥺", "😦", "😧", "😨", "😰", "😥", "😢", "😭", "😱", "😖", "😣",
            "😞", "😓", "😩", "😫", "🥱", "😤", "😡", "😠", "🤬", "😈", "👿", "💀", "☠️", "💩", "🤡", "👹",
            "👺", "👻", "👽", "👾", "🤖", "😺", "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾", "🙈", "🙉",
            "🙊", "💋", "💌", "💘", "💝", "💖", "💗", "💓", "💞", "💕", "💟", "❣️", "💔", "❤", "🧡", "💛",
            "💚", "💙", "💜", "🤎", "🖤", "🤍", "💯", "💢", "💥", "💫", "💦", "💨", "🕳️", "💣", "💬", "👁️‍🗨️",
            # Gestures
            "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉", "👆",
            "🖕", "👇", "☝️", "👍", "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️",
            # People
            "💅", "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂", "🦻", "👃", "🧠", "🫀", "🫁", "🦷", "🦴", "👀",
            "👁️", "👅", "👄", "👶", "🧒", "👦", "👧", "🧑", "👱", "👨", "🧔", "👩", "🧓", "👴", "👵", "🙍",
            "🙎", "🙅", "💁", "🙆", "🙋", "🧏", "🙇", "🤦", "🤷", "👮", "🕵️", "💂", "🥷", "👷", "🤴", "👸",
            # Animals
            "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐻‍❄️", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵",
            "🙈", "🙉", "🙊", "🐒", "🐔", "🐧", "🐦", "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗",
            "🐴", "🦄", "🐝", "🪱", "🐛", "🦋", "🐌", "🐞", "🐜", "🪰", "🪲", "🪳", "🦟", "🦗", "🕷️", "🕸️",
            "🦂", "🐢", "🐍", "🦎", "🦖", "🦕", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡", "🐠", "🐟", "🐬", "🐳",
            "🐋", "🦈", "🐊", "🐅", "🐆", "🦓", "🦍", "🦧", "🦣", "🐘", "🦛", "🦏", "🐪", "🐫", "🦒", "🦘",
            # Nature
            "🌵", "🎄", "🌲", "🌳", "🌴", "🪵", "🌱", "🌿", "☘️", "🍀", "🎍", "🪴", "🎋", "🍃", "🍂", "🍁",
            "🍄", "🐚", "🪨", "🌾", "💐", "🌷", "🌹", "🥀", "🌺", "🌸", "🌼", "🌻", "🌞", "🌝", "🌛", "🌜",
            "🌚", "🌕", "🌖", "🌗", "🌘", "🌑", "🌒", "🌓", "🌔", "🌙", "🌎", "🌍", "🌏", "🪐", "💫", "⭐",
            "🌟", "✨", "⚡", "☄️", "💥", "🔥", "🌪️", "🌈", "☀️", "🌤️", "⛅", "🌥️", "☁️", "🌦️", "🌧️", "⛈️",
            "🌩️", "🌨️", "❄️", "☃️", "⛄", "🌬️", "💨", "💧", "💦", "☔", "☂️", "🌊", "🌫️",
            # Food
            "🍇", "🍈", "🍉", "🍊", "🍋", "🍌", "🍍", "🥭", "🍎", "🍏", "🍐", "🍑", "🍒", "🍓", "🫐", "🥝",
            "🍅", "🫒", "🥥", "🥑", "🥔", "🍆", "🥕", "🌽", "🌶️", "🫑", "🥒", "🥬", "🥦", "🧄", "🧅", "🍄",
            "🥜", "🫘", "🌰", "🍞", "🥐", "🥖", "🫓", "🥨", "🥯", "🥞", "🧇", "🧀", "🍖", "🍗", "🥩", "🥓",
            "🍔", "🍟", "🍕", "🌭", "🥪", "🌮", "🌯", "🫔", "🥙", "🧆", "🥚", "🍳", "🍿", "🧈", "🥞", "🧇",
            "🍝", "🍜", "🍲", "🍛", "🍣", "🍱", "🥟", "🦪", "🍤", "🍙", "🍚", "🍘", "🍥", "🥠", "🥮", "🍢",
            "🍡", "🍧", "🍨", "🍦", "🥧", "🧁", "🍰", "🎂", "🍮", "🍭", "🍬", "🍫", "🍿", "🍩", "🍪", "🌰",
            # Drinks
            "🥜", "🍯", "🥛", "🍼", "☕", "🫖", "🍵", "🧃", "🥤", "🧋", "🍶", "🍺", "🍻", "🥂", "🍷", "🥃",
            "🍸", "🍹", "🧉", "🍾", "🧊", "🥄", "🍴", "🍽️", "🥣", "🥤",
            # Activities
            "⚽", "🏀", "🏈", "⚾", "🥎", "🎾", "🏐", "🏉", "🥏", "🎱", "🪀", "🏓", "🏸", "🏒", "🏑", "🥍",
            "🏏", "🪃", "🥅", "⛳", "🪁", "🏹", "🎣", "🤿", "🥊", "🥋", "🎽", "🛹", "🛼", "🛷", "⛸️", "🥌",
            "🎿", "⛷️", "🏂", "🪂", "🏋️", "🤼", "🤸", "🤺", "⛹️", "🤾", "🏌️", "🏇", "🧘", "🏄", "🏊", "🤽",
            "🚣", "🧗", "🚵", "🚴", "🏆", "🥇", "🥈", "🥉", "🏅", "🎖️", "🏵️", "🎗️", "🎫", "🎟️", "🎪", "🤹",
            # Music
            "🎭", "🩰", "🎨", "🎬", "🎤", "🎧", "🎼", "🎹", "🥁", "🪘", "🎷", "🎺", "🪗", "🎸", "🪕", "🎻",
            "🪈", "🎲", "♟️", "🎯", "🎳", "🎮", "🎰", "🧩", "🧸", "♠️", "♣️", "♥️", "♦️", "🃏", "🎴", "🌁",
            # Travel
            "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑", "🚒", "🚐", "🛻", "🚚", "🚛", "🚜", "🏍️", "🛵",
            "🚲", "🛴", "🛹", "🛼", "🚨", "🚔", "🚍", "🚘", "🚖", "🚡", "🚠", "🚟", "🚃", "🚋", "🚞", "🚝",
            "🚄", "🚅", "🚈", "🚂", "🚆", "🚇", "🚊", "🚉", "✈️", "🛫", "🛬", "🛩️", "💺", "🛰️", "🚀", "🛸",
            "🚁", "🛶", "⛵", "🚤", "🛥️", "🛳️", "⛴️", "🚢", "⚓", "🪝", "⛽", "🚧", "🚦", "🚥", "🗺️", "🗿",
            "🗽", "🗼", "🏰", "🏯", "🏟️", "🎡", "🎢", "🎠", "⛲", "⛱️", "🏖️", "🏝️", "🏜️", "🌋", "⛰️", "🏔️",
            "🗻", "🏕️", "⛺", "🛖", "🏠", "🏡", "🏘️", "🏚️", "🏗️", "🏭", "🏢", "🏬", "🏣", "🏤", "🏥", "🏦",
            "🏨", "🏪", "🏫", "🏩", "💒", "🏛️", "⛪", "🕌", "🕍", "🛕", "🕋", "⛩️", "🛤️", "🛣️", "🗾", "🏞️",
            "🌅", "🌄", "🌠", "🎇", "🎆", "🌇", "🌆", "🏙️", "🌃", "🌌", "🌉", "🌁",
            # Objects
            "⌚", "📱", "📲", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "🖲️", "🕹️", "🗜️", "💽", "💾", "💿", "📀", "📼",
            "📷", "📸", "📹", "🎥", "📽️", "🎞️", "📞", "☎️", "📟", "📠", "📺", "📻", "🎙️", "🎚️", "🎛️", "🧭",
            "⏱️", "⏲️", "⏰", "🕰️", "⌛", "⏳", "📡", "🔋", "🔌", "💡", "🔦", "🕯️", "🪔", "🧯", "🛢️", "💸",
            "💵", "💴", "💶", "💷", "🪙", "💰", "💳", "💎", "⚖️", "🪜", "🧰", "🪛", "🔧", "🔨", "⚒️", "🛠️",
            "⛏️", "🪚", "🔩", "⚙️", "🪤", "🧱", "⛓️", "🧲", "🔫", "💣", "🧨", "🪓", "🔪", "🗡️", "⚔️", "🛡️",
            "🚬", "⚰️", "🪦", "⚱️", "🏺", "🔮", "📿", "🧿", "💈", "⚗️", "🔭", "🔬", "🕳️", "🩹", "🩺", "💊",
            "💉", "🩸", "🧬", "🦠", "🧫", "🧪", "🌡️", "🧹", "🪠", "🧺", "🧻", "🚽", "🚰", "🚿", "🛁", "🛀",
            "🧼", "🪥", "🪒", "🧽", "🪣", "🧴", "🛎️", "🔑", "🗝️", "🚪", "🪑", "🛋️", "🛏️", "🛌", "🧸", "🪆",
            "🖼️", "🪞", "🪟", "🛍️", "🛒", "🎁", "🎈", "🎏", "🎀", "🪄", "🪅", "🎊", "🎉", "🎎", "🏮", "🎐",
            "🧧", "✉️", "📩", "📨", "📧", "💌", "📥", "📤", "📦", "🏷️", "🪧", "📪", "📫", "📬", "📭", "📮",
            "📯", "📜", "📃", "📄", "📑", "🧾", "📊", "📈", "📉", "🗒️", "🗓️", "📆", "📅", "🗑️", "📇", "🗃️",
            "🗳️", "🗄️", "📋", "📁", "📂", "🗂️", "🗞️", "📰", "📓", "📔", "📒", "📕", "📗", "📘", "📙", "📚",
            "📖", "🔖", "🧷", "🔗", "📎", "🖇️", "📐", "📏", "🧮", "📌", "📍", "✂️", "🖊️", "🖋️", "✒️", "🖌️",
            "🖍️", "📝", "✏️", "🔍", "🔎", "🔏", "🔐", "🔒", "🔓",
            # Symbols
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖",
            "💘", "💝", "💟", "☮️", "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️", "☦️", "🛐", "⛎", "♈",
            "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓", "🆔", "⚛️", "🉑", "☢️", "☣️", "📴", "📳",
            "🈶", "🈚", "🈸", "🈺", "🈷️", "✴️", "🆚", "💮", "🉐", "㊙️", "㊗️", "🈴", "🈵", "🈹", "🈲", "🅰️",
            "🅱️", "🆎", "🆑", "🅾️", "🆘", "❌", "⭕", "🛑", "⛔", "📛", "🚫", "💯", "💢", "♨️", "🚷", "🚯",
            "🚳", "🚱", "🔞", "📵", "🚭", "❗", "❕", "❓", "❔", "‼️", "⁉️", "🔅", "🔆", "〽️", "⚠️", "🚸", "🔱",
            "⚜️", "🔰", "♻️", "✅", "🈯", "💹", "❇️", "✳️", "❎", "🌐", "💠", "Ⓜ️", "🌀", "💤", "🏧", "🚾", "♿",
            "🅿️", "🛗", "🈳", "🈂️", "🛂", "🛃", "🛄", "🛅", "🚹", "🚺", "🚼", "⚧️", "🚻", "🚮", "🎦", "📶",
            "🈁", "🔣", "ℹ️", "🔤", "🔡", "🔠", "🆖", "🆗", "🆙", "🆒", "🆕", "🆓", "0️⃣", "1️⃣", "2️⃣", "3️⃣",
            "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "🔢", "#️⃣", "*️⃣", "⏏️", "▶️", "⏸️", "⏯️", "⏹️", "⏺️",
            "⏭️", "⏮️", "⏩", "⏪", "⏫", "⏬", "◀️", "🔼", "🔽", "➡️", "⬅️", "⬆️", "⬇️", "↗️", "↘️", "↙️", "↖️",
            "↕️", "↔️", "↪️", "↩️", "⤴️", "⤵️", "🔀", "🔁", "🔂", "🔄", "🔃", "🎵", "🎶", "➕", "➖", "➗", "✖️",
            "♾️", "💲", "💱", "™️", "©️", "®️", "〰️", "➰", "➿", "🔚", "🔙", "🔛", "🔝", "🔜", "✔️", "☑️", "🔘",
            "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪", "🟤", "🔺", "🔻", "🔸", "🔹", "🔶", "🔷", "🔳", "🔲",
            "▪️", "▫️", "◾", "◽", "◼️", "◻️", "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "⬛", "⬜", "🟫", "🔈", "🔇",
            "🔉", "🔊", "🔔", "🔕", "📣", "📢", "💬", "💭", "🗯️", "♠️", "♣️", "♥️", "♦️", "🃏", "🎴", "🀄",
            # Flags
            "🏳️", "🏴", "🏴‍☠️", "🏁", "🚩", "🎌", "🏳️‍🌈", "🏳️‍⚧️", "🇺🇸", "🇬🇧", "🇨🇦", "🇦🇺", "🇮🇳", "🇩🇪",
            "🇫🇷", "🇪🇸", "🇮🇹", "🇯🇵", "🇰🇷", "🇨🇳", "🇧🇷", "🇲🇽", "🇷🇺", "🇿🇦", "🇳🇬", "🇪🇬", "🇸🇦", "🇦🇪",
            "🇹🇷", "🇮🇩", "🇵🇰", "🇱🇰", "🇳🇵", "🇦🇫", "🇪🇺", "🇺🇳",
        ]

        # Insert emoji into input field
        def insert_emoji(emoji):
            if self._input_field:
                current = self._input_field.value or ""
                self._input_field.value = current + emoji
                try:
                    self._page.update()
                except Exception:
                    pass

        # Create buttons for each emoji
        emoji_buttons = []
        for emoji in all_emojis:
            emoji_buttons.append(
                ft.Container(
                    content=ft.Text(emoji, size=22),
                    width=40,
                    height=40,
                    on_click=lambda ev, em=emoji: insert_emoji(em),
                    alignment=ft.alignment.Alignment(0, 0),
                    border_radius=8,
                )
            )

        dlg = ft.AlertDialog(
            title=ft.Text("Emoji", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=350,
                height=400,
                content=ft.GridView(
                    runs_count=8,
                    spacing=2,
                    run_spacing=2,
                    controls=emoji_buttons,
                ),
            ),
            actions=[ft.TextButton("Close", on_click=close_dlg)]
        )

        self._page.show_dialog(dlg)

    def _refresh_contacts_ui(self, search_text: str = "") -> None:
        """Rebuild the contact list column"""
        if not self._contacts_column:
            return

        self._contacts_column.controls.clear()

        if self._show_groups:
            # Show groups
            filtered = self.groups
            if search_text:
                st = search_text.lower()
                filtered = [g for g in self.groups if st in g.name.lower()]

            if not filtered:
                self._contacts_column.controls.append(
                    ft.Container(
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.GROUP, size=48,
                                        color=TEXT_TERTIARY),
                                ft.Text("No groups yet", size=15,
                                        color=TEXT_SECONDARY),
                                ft.Container(height=12),
                                ft.ElevatedButton(
                                    "Create Group",
                                    icon=ft.Icons.ADD,
                                    on_click=self._show_create_group_dialog,
                                    bgcolor=PRIMARY,
                                    color=ft.Colors.WHITE,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=20))
                                ),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.all(24),
                        alignment=ft.alignment.Alignment(0, 0),
                    )
                )
            else:
                for group in filtered:
                    self._contacts_column.controls.append(
                        self._build_group_tile(group))
        else:
            # Show contacts
            filtered = self.contacts
            if search_text:
                st = search_text.lower()
                filtered = [
                    c for c in self.contacts if st in c.username.lower() or st in c.email.lower()]

            if not filtered:
                self._contacts_column.controls.append(
                    ft.Container(
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF, size=48,
                                        color=TEXT_TERTIARY),
                                ft.Text("No contacts found", size=15,
                                        color=TEXT_SECONDARY),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.all(24),
                        alignment=ft.alignment.Alignment(0, 0),
                    )
                )
            else:
                for contact in filtered:
                    self._contacts_column.controls.append(
                        self._build_contact_tile(contact))

    def _build_group_tile(self, group: ChatGroupVM) -> ft.Container:
        """Build a group tile - WhatsApp style"""
        is_selected = self.selected_group and self.selected_group.id == group.id
        is_creator = group.created_by == self.current_user_id

        def on_click(e):
            self._on_group_selected(group)

        def on_add_member(e, grp=group):
            self._show_add_member_dialog(grp)

        return ft.Container(
            on_click=on_click,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=PRIMARY + "10" if is_selected else "transparent",
            content=ft.Container(
                content=ft.Row(
                    spacing=12,
                    controls=[
                        ft.Stack([
                            ft.CircleAvatar(
                                content=ft.Icon(
                                    ft.Icons.GROUP, color=ft.Colors.WHITE, size=24),
                                radius=26,
                                bgcolor=PRIMARY_LIGHT,
                            ),
                        ]),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(
                                    group.name,
                                    size=15,
                                    weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500,
                                    color=PRIMARY if is_selected else TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    group.last_message or f"{group.member_count} members",
                                    size=13,
                                    color=TEXT_SECONDARY,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                        ),
                        ft.Column(
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            controls=[
                                ft.Text(
                                    "",
                                    size=11,
                                    color=PRIMARY_LIGHTER if group.unread_count > 0 else TEXT_TERTIARY,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.PERSON_ADD,
                                    icon_color=PRIMARY,
                                    tooltip="Add Members",
                                    on_click=on_add_member,
                                    width=28, height=28,
                                    visible=is_creator,
                                ) if is_creator else ft.Container(width=0, height=28),
                            ],
                        ),
                    ],
                ),
            ),
        )

    def _build_contact_tile(self, contact: Contact) -> ft.Container:
        """Build a contact tile - WhatsApp style with unread count badge"""
        import os
        from pathlib import Path

        status_color = PRIMARY_LIGHTER if contact.is_online else TEXT_TERTIARY

        # Properly format last seen
        if contact.is_online:
            status_text = "online"
        elif contact.last_seen:
            status_text = self._format_last_seen(contact.last_seen)
        else:
            status_text = "offline"

        is_selected = self.selected_contact and self.selected_contact.id == contact.id

        def on_click(e):
            self._on_contact_selected(contact)

        # Build avatar - show profile photo if available and valid
        profile_photo_valid = False
        profile_photo_to_show = None

        if contact.profile_photo:
            # Check if profile photo path is valid
            if contact.profile_photo.startswith('http'):
                profile_photo_valid = True
                profile_photo_to_show = contact.profile_photo
            else:
                # Check if local path exists as-is
                if os.path.exists(contact.profile_photo):
                    profile_photo_valid = True
                    profile_photo_to_show = contact.profile_photo
                else:
                    # Try relative to assets/profile_photos directory
                    base_dir = Path(__file__).parent.parent
                    assets_path = base_dir / "assets" / "profile_photos" / \
                        os.path.basename(contact.profile_photo)
                    if assets_path.exists():
                        profile_photo_valid = True
                        profile_photo_to_show = str(assets_path)
                    else:
                        # Try just the basename in profile_photos
                        basename = os.path.basename(contact.profile_photo)
                        assets_path2 = base_dir / "assets" / "profile_photos" / basename
                        if assets_path2.exists():
                            profile_photo_valid = True
                            profile_photo_to_show = str(assets_path2)

        # Build avatar content
        if profile_photo_valid and profile_photo_to_show:
            # Use profile photo if available and valid - wrap in circular Container
            avatar_content = ft.Container(
                width=52,
                height=52,
                border_radius=26,  # Make it circular
                content=ft.Image(
                    src=profile_photo_to_show,
                    width=52,
                    height=52,
                    fit=ft.BoxFit.COVER,
                ),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,  # Clip to circle
            )
        else:
            # Show initials as fallback
            avatar_content = ft.Text(
                contact.username[:1].upper(),
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            )

        # Unread count badge
        unread_badge = None
        if contact.unread_count > 0:
            unread_badge = ft.Container(
                content=ft.Text(
                    str(contact.unread_count) if contact.unread_count < 100 else "99+",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                bgcolor=PRIMARY_LIGHTER,
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                width=20,
                height=20,
                alignment=ft.alignment.Alignment(0, 0),
            )

        return ft.Container(
            on_click=on_click,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=PRIMARY + "10" if is_selected else "transparent",
            content=ft.Container(
                content=ft.Row(
                    spacing=12,
                    controls=[
                        ft.Stack([
                            ft.CircleAvatar(
                                content=avatar_content,
                                radius=26,
                                bgcolor=contact.avatar_color if not (
                                    profile_photo_valid and profile_photo_to_show) else "transparent",
                            ),
                            # Online indicator
                            ft.Container(
                                alignment=ft.alignment.Alignment(1, 1),
                                content=ft.Container(
                                    width=14, height=14,
                                    bgcolor=status_color,
                                    border_radius=7,
                                    border=ft.border.all(2, ft.Colors.WHITE),
                                ),
                            ),
                        ]),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(
                                    contact.username,
                                    size=15,
                                    weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500,
                                    color=PRIMARY if is_selected else TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    contact.last_message or status_text,
                                    size=13,
                                    color=PRIMARY_LIGHTER if contact.is_online else TEXT_SECONDARY,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                        ),
                        # Unread count badge on the right
                        ft.Column(
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            controls=[
                                ft.Text(
                                    self._format_message_time(
                                        contact.last_message_time) if contact.last_message_time else "",
                                    size=11,
                                    color=PRIMARY_LIGHTER if contact.unread_count > 0 else TEXT_TERTIARY,
                                ),
                                unread_badge if unread_badge else ft.Container(
                                    width=0, height=20),
                            ],
                        ),
                    ],
                ),
            ),
        )

    def _format_message_time(self, msg_time: Optional[datetime]) -> str:
        """Format message time for display in contact list"""
        if not msg_time:
            return ""
        try:
            now = datetime.now()
            today = now.date()
            msg_date = msg_time.date()

            if msg_date == today:
                return msg_time.strftime("%H:%M")
            elif msg_date == today.replace(day=today.day - 1):
                return "Yesterday"
            elif (today - msg_date).days < 7:
                return msg_date.strftime("%a")  # Day name
            else:
                return msg_date.strftime("%d/%m/%y")
        except Exception:
            return ""

    def _get_avatar_color(self, username: str) -> str:
        """Generate color based on username."""
        colors = [PRIMARY, PRIMARY_LIGHT, SECONDARY, SUCCESS,
                  "#9C27B0", "#00BCD4", "#795548", "#FF5722"]
        index = sum(ord(c) for c in username) % len(colors)
        return colors[index]

    def _format_last_seen(self, last_seen: datetime) -> str:
        """Format last seen datetime."""
        try:
            # Handle both naive and aware datetime
            now = datetime.utcnow()
            if last_seen.tzinfo is not None:
                # If last_seen is timezone-aware, convert to UTC
                import calendar
                now = datetime.utcnow()
                last_seen = last_seen.replace(
                    tzinfo=None) if last_seen.tzinfo else last_seen

            diff = now - last_seen
            seconds = diff.total_seconds()

            if seconds < 60:
                return "online"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"last seen {minutes}m ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"last seen {hours}h ago"
            elif diff.days == 1:
                return "last seen yesterday"
            elif diff.days < 7:
                return f"last seen {diff.days} days ago"
            else:
                return f"last seen {last_seen.strftime('%b %d')}"
        except Exception:
            return "offline"

    def _refresh_messages_ui(self) -> None:
        """Rebuild the messages list UI - WhatsApp style"""
        if not self._messages_list:
            return

        self._messages_list.controls.clear()

        if not self.selected_contact and not self.is_group_chat:
            if self._empty_state:
                self._empty_state.visible = True
            return

        if self._empty_state:
            self._empty_state.visible = len(self.messages) == 0

        if not self.messages:
            return

        # Add date separators and messages
        last_date = None
        for msg in self.messages:
            try:
                msg_date = msg.created_at.date() if msg.created_at else date.today()
            except Exception:
                msg_date = date.today()

            if last_date is None or msg_date != last_date:
                self._messages_list.controls.append(
                    self._build_date_separator(msg_date))
                last_date = msg_date

            bubble = self._build_message_bubble(msg)
            self._messages_list.controls.append(bubble)

    def _build_date_separator(self, msg_date: date) -> ft.Container:
        """Build a date separator - WhatsApp style"""
        today = date.today()
        yesterday = today.replace(
            day=today.day - 1) if today.day > 1 else today

        if msg_date == today:
            date_text = "Today"
        elif msg_date == yesterday:
            date_text = "Yesterday"
        else:
            date_text = msg_date.strftime("%B %d, %Y")

        return ft.Container(
            content=ft.Container(
                bgcolor=ft.Colors.WHITE,
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=12,
                content=ft.Text(
                    date_text, size=12, color=TEXT_SECONDARY, weight=ft.FontWeight.W_500),
            ),
            padding=ft.padding.symmetric(vertical=12),
            alignment=ft.alignment.Alignment(0, 0),
        )

    def _build_message_bubble(self, msg: ChatMessageVM) -> ft.Container:
        """Create a WhatsApp-style chat bubble with proper alignment"""
        # Determine alignment based on message ownership
        is_own = msg.is_own

        # Bubble colors
        bubble_color = BUBBLE_SENT if is_own else BUBBLE_RECEIVED

        # Text colors
        text_color = TEXT_PRIMARY
        time_color = TEXT_SECONDARY

        try:
            timestamp = msg.created_at.strftime("%H:%M")
        except Exception:
            timestamp = ""

        # Status icon for sent messages
        status_icon = None
        status_color = TEXT_SECONDARY
        if is_own:
            status_icon = ft.Icons.DONE_ALL if msg.is_read else ft.Icons.DONE
            status_color = PRIMARY_LIGHTER if msg.is_read else TEXT_TERTIARY

        # Build content
        content_parts = []

        # Show sender name for group messages (received)
        if self.is_group_chat and not is_own:
            content_parts.append(
                ft.Text(msg.sender_name, size=12,
                        weight=ft.FontWeight.W_600, color=PRIMARY_LIGHT)
            )

        # Check if this is a file attachment
        has_attachment = bool(msg.attachment_name and msg.attachment_path)
        # Check if attachment_path is a valid URL (http)
        is_url = msg.attachment_path and msg.attachment_path.startswith('http')
        # Check if it's an image file (only if URL exists)
        is_image_file = is_url and msg.is_image

        # Show image preview if it's an image and we have a valid URL
        if is_image_file:
            try:
                content_parts.append(
                    ft.Container(
                        margin=ft.margin.only(bottom=4),
                        content=ft.Image(
                            src=msg.attachment_path,
                            width=200,
                            height=150,
                            fit="contain",
                            border_radius=8,
                        )
                    )
                )
            except Exception as e:
                print(f"[Chat] Error loading image: {e}")
                # Will fall through to show as file attachment below

        # Show file attachment as downloadable link (for all attachments including images)
        if has_attachment:
            # Determine file icon based on extension
            file_ext = msg.attachment_name.lower().split(
                '.')[-1] if msg.attachment_name else ''
            file_icon = ft.Icons.INSERT_DRIVE_FILE
            if file_ext in ['pdf']:
                file_icon = ft.Icons.PICTURE_AS_PDF
            elif file_ext in ['doc', 'docx']:
                file_icon = ft.Icons.DESCRIPTION
            elif file_ext in ['xls', 'xlsx']:
                file_icon = ft.Icons.TABLE_CHART
            elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                file_icon = ft.Icons.IMAGE
            elif file_ext in ['zip', 'rar', '7z']:
                file_icon = ft.Icons.FOLDER_ZIP

            # Create clickable file attachment container
            def download_file(e):
                """Open the file URL in browser for download"""
                import webbrowser
                if msg.attachment_path and msg.attachment_path.startswith('http'):
                    webbrowser.open(msg.attachment_path)
                else:
                    print(f"[Chat] Invalid file URL: {msg.attachment_path}")

            file_attachment = ft.Container(
                margin=ft.margin.only(bottom=4),
                padding=ft.padding.all(8),
                bgcolor="#F0F0F0",
                border_radius=8,
                on_click=download_file,
                content=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(
                            width=40,
                            height=40,
                            bgcolor=PRIMARY_LIGHT,
                            border_radius=8,
                            content=ft.Icon(file_icon, color="white", size=20),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    msg.attachment_name or "File",
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    color=PRIMARY,
                                    selectable=True
                                ),
                                ft.Text(
                                    "Tap to download",
                                    size=10,
                                    color=TEXT_SECONDARY
                                )
                            ],
                            expand=True
                        ),
                        ft.Icon(ft.Icons.DOWNLOAD,
                                color=PRIMARY_LIGHT, size=20)
                    ]
                )
            )
            content_parts.append(file_attachment)

        # Message content
        content_parts.append(
            ft.Text(msg.content, size=14.5, color=text_color, selectable=True)
        )

        # Timestamp and status row
        time_row = ft.Row(
            spacing=4,
            controls=[
                ft.Text(timestamp, size=11, color=time_color),
            ],
        )

        if is_own and status_icon:
            time_row.controls.append(
                ft.Icon(status_icon, size=14, color=status_color)
            )

        content_parts.append(time_row)

        # Create the bubble container with proper border radius
        bubble = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=bubble_color,
            border_radius=ft.border_radius.only(
                top_left=16, top_right=16,
                bottom_left=4 if is_own else 16,
                bottom_right=16 if is_own else 4,
            ),
            content=ft.Column(
                spacing=2, controls=content_parts, tight=True),
        )

        # Return with proper alignment - left for received, right for sent
        if is_own:
            # Sent messages - align right
            return ft.Container(
                alignment=ft.alignment.Alignment(1, 0),  # Right alignment
                content=bubble,
                margin=ft.margin.only(left=60, right=0),
                padding=ft.padding.only(left=50),
            )
        else:
            # Received messages - align left
            return ft.Container(
                alignment=ft.alignment.Alignment(-1, 0),  # Left alignment
                content=bubble,
                margin=ft.margin.only(right=60, left=0),
                padding=ft.padding.only(right=50),
            )

    def _update_header_for_selection(self) -> None:
        """Update header based on selection"""
        if not (self._header_title and self._header_subtitle):
            return

        if self.is_group_chat and self.selected_group:
            self._header_title.value = self.selected_group.name
            self._header_subtitle.value = f"{self.selected_group.member_count} members"
            return

        if not self.selected_contact:
            self._header_title.value = "Drop"
            self._header_subtitle.value = ""
            return

        c = self.selected_contact
        self._header_title.value = c.username

        # Get fresh online status and last_seen from database
        db = get_db_session()
        try:
            user = db.query(User).filter(User.id == c.id).first()
            if user:
                c.is_online = bool(getattr(user, "is_online", False))
                c.last_seen = getattr(user, "last_seen", None)
        except Exception:
            pass
        finally:
            db.close()

        if c.is_online:
            self._header_subtitle.value = "online"
        else:
            if c.last_seen:
                self._header_subtitle.value = self._format_last_seen(
                    c.last_seen)
            else:
                self._header_subtitle.value = "offline"

    def _on_contact_selected(self, contact: Contact) -> None:
        """Handle contact selection"""
        self.selected_contact = contact
        self.selected_group = None
        self.is_group_chat = False
        self._load_messages_for_selected()
        self._update_header_for_selection()

        search_val = self._search_field.value if self._search_field else ""
        self._refresh_contacts_ui(search_text=search_val)
        self._refresh_messages_ui()
        try:
            self._page.update()
        except Exception:
            pass

    def _on_group_selected(self, group: ChatGroupVM) -> None:
        """Handle group selection"""
        self.selected_group = group
        self.selected_contact = None
        self.is_group_chat = True
        self.messages = []
        self._load_group_messages()
        self._update_header_for_selection()

        search_val = self._search_field.value if self._search_field else ""
        self._refresh_contacts_ui(search_text=search_val)
        self._refresh_messages_ui()
        try:
            self._page.update()
        except Exception:
            pass

    def _on_send_clicked(self, e) -> None:
        """Send message"""
        if not self._input_field:
            return

        content = (self._input_field.value or "").strip()
        if not content:
            return

        if not self.selected_contact and not self.is_group_chat:
            self._show_snackbar("Select a person or group to chat with first.")
            return

        db = get_db_session()
        try:
            if self.is_group_chat and self.selected_group:
                # Send to group
                sent = send_chat_message(
                    db,
                    sender_id=self.current_user_id,
                    content=content,
                    group_id=self.selected_group.id,
                )
            elif self.selected_contact:
                # Send direct message
                sent = send_chat_message(
                    db,
                    sender_id=self.current_user_id,
                    content=content,
                    receiver_id=self.selected_contact.id,
                )
            else:
                return

            # Get message ID
            try:
                msg_id = int(getattr(sent, 'id', 0) or 0)
            except Exception:
                msg_id = 0

            if msg_id and msg_id in self._message_ids:
                self._input_field.value = ""
                try:
                    self._page.update()
                except Exception:
                    pass
                return

            created_at = getattr(sent, 'created_at', datetime.utcnow())

            vm = ChatMessageVM(
                id=msg_id or None,
                sender_id=self.current_user_id,
                sender_name=self.current_username,
                content=content,
                created_at=created_at,
                is_own=True,
                is_read=False,
                group_id=self.selected_group.id if self.is_group_chat else None
            )

            if vm.id:
                self._message_ids.add(vm.id)

            if not any(m.id == vm.id for m in self.messages):
                self.messages.append(vm)

        except Exception as exc:
            print(f"[ChatScreen] Error sending message: {exc}")
            self._show_error(f"Error sending message: {exc}")
        finally:
            db.close()

        self._input_field.value = ""
        self._refresh_messages_ui()
        try:
            self._page.update()
        except Exception:
            pass

    def _on_refresh_clicked(self, e) -> None:
        """Refresh messages"""
        if not self.selected_contact and not self.is_group_chat:
            self._show_snackbar("Select a person or group first.")
            return

        self._load_messages_for_selected()
        self._refresh_messages_ui()
        try:
            self._page.update()
        except Exception:
            pass

    def _show_snackbar(self, message: str) -> None:
        try:
            snack = ft.SnackBar(
                content=ft.Text(message),
                behavior=ft.SnackBarBehavior.FLOATING,
                margin=10,
                bgcolor=TEXT_PRIMARY,
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
        except Exception as exc:
            print(f"[ChatScreen] Snackbar failed: {exc}")

    def _show_error(self, message: str) -> None:
        self._show_snackbar(message)

    def _on_attach_file(self, e=None):
        """Handle file attachment - uploads to Supabase Storage for cloud sharing"""
        if not self.selected_contact and not self.is_group_chat:
            self._show_snackbar(
                "Select a contact or group first to share files")
            return

        # Check if file picker exists
        if not self._file_picker:
            self._show_error("File picker not initialized")
            return

        # Use async pick_files with run_task (Flet 0.80+)
        def handle_picked_files(files):
            """Process picked files after async selection - with Supabase upload"""
            try:
                if not files:
                    return

                file_info = files[0]
                file_path = file_info.path if hasattr(
                    file_info, 'path') else str(file_info)
                if not file_path:
                    return

                # Get filename from path
                file_name = file_path.split(
                    '/')[-1] if '/' in file_path else file_path

                # Show uploading message
                snack = ft.SnackBar(
                    content=ft.Text(f"Uploading {file_name} to cloud..."),
                    bgcolor=PRIMARY_LIGHT
                )
                self._page.overlay.append(snack)
                snack.open = True
                self._page.update()

                # Try to upload to Supabase Storage
                file_url = None
                upload_success = False
                upload_error = None

                try:
                    storage = get_storage()
                    if storage.available:
                        # Upload to Supabase Storage
                        success, url_or_error, bucket_path = upload_to_supabase(
                            file_path,
                            folder="chat_attachments",
                            custom_filename=f"{self.current_user_id}_{int(datetime.now().timestamp())}_{file_name}"
                        )

                        if success and url_or_error:
                            file_url = url_or_error
                            upload_success = True
                            print(
                                f"[Chat] File uploaded to Supabase: {file_url}")
                        else:
                            upload_error = url_or_error
                            print(
                                f"[Chat] Supabase upload failed: {url_or_error}")
                    else:
                        upload_error = "Cloud storage not configured"
                        print("[Chat] Supabase storage not available")
                except Exception as upload_err:
                    upload_error = str(upload_err)
                    print(f"[Chat] Upload error: {upload_err}")

                # If upload failed, show error
                if not upload_success:
                    error_msg = upload_error or "Upload failed"
                    snack = ft.SnackBar(
                        content=ft.Text(
                            f"Cloud upload failed: {error_msg}. File not attached."),
                        bgcolor=ERROR
                    )
                    self._page.overlay.append(snack)
                    snack.open = True
                    self._page.update()
                    return

                # Store the Supabase URL (cloud accessible) instead of local path
                db = get_db_session()
                try:
                    if self.is_group_chat and self.selected_group:
                        send_chat_message(
                            db,
                            sender_id=self.current_user_id,
                            content=f"📎 Shared file: {file_name}",
                            group_id=self.selected_group.id,
                            has_attachment=True,
                            attachment_path=file_url  # Store Supabase URL, not local path
                        )
                    elif self.selected_contact:
                        send_chat_message(
                            db,
                            sender_id=self.current_user_id,
                            content=f"📎 Shared file: {file_name}",
                            receiver_id=self.selected_contact.id,
                            has_attachment=True,
                            attachment_path=file_url  # Store Supabase URL, not local path
                        )
                finally:
                    db.close()

                self._load_messages_for_selected()
                self._refresh_messages_ui()
                self._page.update()
                self._show_success(f"File shared: {file_name}")

            except Exception as ex:
                print(f"[Chat] File pick error: {ex}")
                self._show_error(f"Error sharing file: {ex}")

        async def pick_and_handle():
            """Async function to pick files and handle result"""
            try:
                files = await self._file_picker.pick_files(
                    dialog_title="Choose a file to share",
                    file_type=ft.FilePickerFileType.ANY,
                )
                # Process the result
                handle_picked_files(files)
            except Exception as ex:
                print(f"[Chat] File picker exception: {ex}")
                self._show_error(f"Error opening file picker: {ex}")

        # Run the async function
        self._page.run_task(pick_and_handle)

    def _initiate_voice_call(self):
        """Initiate voice call via internet"""
        if not self.selected_contact and not self.is_group_chat:
            self._show_snackbar("Please select a contact or group first")
            return

        if self.is_group_chat:
            self._show_snackbar("Voice calls not available for groups")
            return

        def close_dlg(ev):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        def start_call(ev):
            self._page.pop_dialog()
            contact = self.selected_contact

            try:
                db = get_db_session()
                call = initiate_call(
                    db, self.current_user_id, contact.id, CallType.VOICE)
                db.close()
                self._show_call_active(contact, call.id, "voice")
            except Exception as ex:
                self._show_error(f"Error: {ex}")

        dlg = ft.AlertDialog(
            title=ft.Text("Voice Call"),
            content=ft.Column([
                ft.Container(height=10),
                ft.CircleAvatar(
                    content=ft.Text(self.selected_contact.username[:1].upper(
                    ), size=32, weight=ft.FontWeight.BOLD),
                    radius=40, bgcolor=PRIMARY,
                ),
                ft.Container(height=10),
                ft.Text(self.selected_contact.username, size=18,
                        weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("Voice Call (Internet)", size=14, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=5),
                ft.Text("Using internet connection", size=12, color=SUCCESS,
                        text_align=ft.TextAlign.CENTER),
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Start Call", icon=ft.Icons.PHONE,
                                  on_click=start_call, bgcolor=SUCCESS, color=ft.Colors.WHITE),
            ],
        )
        self._page.show_dialog(dlg)

    def _initiate_video_call(self):
        """Initiate video call via internet"""
        if not self.selected_contact and not self.is_group_chat:
            self._show_snackbar("Please select a contact or group first")
            return

        if self.is_group_chat:
            self._show_snackbar("Video calls not available for groups")
            return

        def close_dlg(ev):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        def start_call(ev):
            self._page.pop_dialog()
            contact = self.selected_contact

            try:
                db = get_db_session()
                call = initiate_call(
                    db, self.current_user_id, contact.id, CallType.VIDEO)
                db.close()
                self._show_call_active(contact, call.id, "video")
            except Exception as ex:
                self._show_error(f"Error: {ex}")

        dlg = ft.AlertDialog(
            title=ft.Text("Video Call"),
            content=ft.Column([
                ft.Container(height=10),
                ft.CircleAvatar(
                    content=ft.Text(self.selected_contact.username[:1].upper(
                    ), size=32, weight=ft.FontWeight.BOLD),
                    radius=40, bgcolor=PRIMARY,
                ),
                ft.Container(height=10),
                ft.Text(self.selected_contact.username, size=18,
                        weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("Video Call (Internet)", size=14, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=5),
                ft.Text("Using internet connection", size=12, color=SUCCESS,
                        text_align=ft.TextAlign.CENTER),
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Start Call", icon=ft.Icons.VIDEO_CALL,
                                  on_click=start_call, bgcolor=INFO, color=ft.Colors.WHITE),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_call_active(self, contact, call_id, call_type):
        """Show active call interface via internet"""
        call_type_icon = ft.Icons.PHONE if call_type == "voice" else ft.Icons.VIDEO_CALL
        call_type_color = SUCCESS if call_type == "voice" else INFO

        def end_call(ev):
            try:
                db = get_db_session()
                end_call(db, call_id, CallStatus.COMPLETED)
                db.close()
            except Exception as ex:
                print(f"Error ending call: {ex}")

            self._page.pop_dialog()
            self._show_snackbar(f"Call with {contact.username} ended")
            try:
                self._page.update()
            except Exception:
                pass

        call_time = ft.Text(
            "00:00", size=48, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

        def update_time():
            seconds = 0
            while True:
                time.sleep(1)
                seconds += 1
                mins, secs = divmod(seconds, 60)
                try:
                    call_time.value = f"{mins:02d}:{secs:02d}"
                    self._page.update()
                except:
                    break

        threading.Thread(target=update_time, daemon=True).start()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(call_type_icon, color=call_type_color),
                ft.Text(f"{call_type.title()} Call"),
            ]),
            content=ft.Column([
                ft.Container(height=20),
                ft.CircleAvatar(
                    content=ft.Text(contact.username[:1].upper(
                    ), size=40, weight=ft.FontWeight.BOLD),
                    radius=50, bgcolor=PRIMARY,
                ),
                ft.Container(height=10),
                ft.Text(contact.username, size=20, weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER),
                call_time,
                ft.Text("Call in progress via Internet...", size=14,
                        color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=5),
                ft.Text("🌐 Internet Call", size=12, color=SUCCESS,
                        text_align=ft.TextAlign.CENTER),
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.ElevatedButton("End Call", icon=ft.Icons.CALL_END,
                                  bgcolor=ERROR, color="white", on_click=end_call),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_success(self, msg):
        """Show success snackbar"""
        snack = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=SUCCESS,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=10,
        )
        self._page.overlay.append(snack)
        snack.open = True
        try:
            self._page.update()
        except Exception:
            pass

    def cleanup(self):
        """Cleanup when leaving the screen"""
        self._stop_threads = True
        try:
            db = get_db_session()
            update_user_presence(db, self.current_user_id, False)
            db.close()
        except Exception:
            pass

        if self._realtime_subscription:
            try:
                self._supabase_client.remove_channel(
                    self._realtime_subscription)
            except Exception:
                pass


def show_chat(page: ft.Page, user: Union[dict, User]) -> None:
    """Helper to show the chat screen full-screen."""
    page.clean()
    page.add(ChatScreen(page, user))
    try:
        page.update()
    except Exception as exc:
        print(f"[ChatScreen] Initial page update failed: {exc}")
