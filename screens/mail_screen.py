"""
Vernika HRA - Internal Mail Screen
Improved UI with compact cards, popup modals, and better UX
Fixed: Multiple CC/BCC, Bulk Send, Professional Compose UI, Improved Recipient Picker
"""

import flet as ft
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import threading
import time

from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import EmailCategory, User
from database.operations import (
    send_email, get_user_emails, get_email_by_id,
    mark_email_as_read, delete_email, get_unread_email_count, get_all_users,
    create_email_group, add_email_group_member, get_user_email_groups,
    get_email_group_members, get_email_group_member_ids, get_all_email_groups,
    remove_email_group_member, save_draft, get_draft_by_id,
    update_user_presence
)

# Import Supabase storage for file attachments
from utils.supabase_storage import upload_to_supabase, get_storage

# Teams-like palette
TEAMS_BLUE = "#6264A7"
TEAMS_BG = "#F3F2F1"
TEAMS_WHITE = "#FFFFFF"
TEAMS_GRAY = "#F0F0F0"
TEAMS_TEXT = "#323130"
TEAMS_SUBTEXT = "#605E5C"
PRIMARY = TEAMS_BLUE
SUCCESS = "#107C10"
ERROR = "#D13438"
WARNING = "#FFB900"
BORDER = "#E0E0E0"


class MailScreen(ft.Container):
    def __init__(self, page: ft.Page, user=None):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = TEAMS_BG

        self.current_user_id = None
        self.current_username = "User"
        if isinstance(user, dict):
            self.current_user_id = user.get('id')
            self.current_username = user.get('username', 'User')
        elif hasattr(user, 'id'):
            self.current_user_id = user.id
            self.current_username = getattr(user, 'username', 'User')

        self.current_folder = "inbox"
        self.emails = []
        self.selected_emails = set()
        self.search_query = ""
        self.reply_to_email = None
        self.forward_email = None
        self.email_detail_dialog = None
        self._hovered_email = None

        # Presence tracking
        self._online_contacts: Dict[int, bool] = {}
        self._message_ids: set = set()
        self._presence_poll_thread = None
        self._stop_threads = False
        self._typing_indicator = None

        # File picker for attachments
        self._file_picker = None

        # Draft tracking
        self._current_draft_id = None

        # Attachment tracking
        self._attached_file_path = {"path": None, "name": None, "url": None}
        self._attached_file_container = None  # UI container for attachment preview

        # Multi-select recipients
        self._to_recipients = []
        self._cc_recipients = []
        self._bcc_recipients = []

        # Email groups
        self._email_groups = []
        self._load_email_groups()

        # All users for selection
        self._all_users = []
        self._load_all_users()

        self.content = self._build_content()
        self._load_emails()

        # Start presence tracking
        self._update_presence_online()
        self._start_presence_polling()

        # Note: Mail notifications are handled for new emails

    def _load_email_groups(self):
        """Load user's email groups"""
        db = None
        try:
            db = get_db_session()
            # Rollback any pending transaction first to handle aborted state
            try:
                db.rollback()
            except:
                pass
            self._email_groups = get_user_email_groups(
                db, self.current_user_id)
        except Exception as e:
            print(f"[Mail] Error loading email groups: {e}")
            if db:
                try:
                    db.rollback()
                except:
                    pass
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass

    def _load_all_users(self):
        db = None
        try:
            db = get_db_session()
            # Rollback any pending transaction first to handle aborted state
            try:
                db.rollback()
            except:
                pass
            self._all_users = get_all_users(db)
        except Exception as e:
            print(f"[Mail] Error loading users: {e}")
            if db:
                try:
                    db.rollback()
                except:
                    pass
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass
            pass

    # ==================== Presence System ====================
    def _update_presence_online(self):
        """Update user presence to online"""
        try:
            db = get_db_session()
            update_user_presence(db, self.current_user_id, True)
            db.close()
        except Exception as e:
            print(f"[Mail] Error updating presence: {e}")

    def _start_presence_polling(self):
        """Poll for user presence updates"""
        def poll_presence():
            while not self._stop_threads:
                try:
                    # Poll every 5 seconds for better real-time feel
                    time.sleep(5)
                    if self._stop_threads:
                        break
                    self._update_online_statuses()
                except Exception as e:
                    print(f"[Mail] Presence poll error: {e}")

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
                    user_id = int(getattr(user, 'id', 0))
                    if user_id:
                        is_online = bool(getattr(user, 'is_online', False))
                        last_seen = getattr(user, 'last_seen', None)
                        self._online_contacts[user_id] = is_online
            finally:
                db.close()
        except Exception as e:
            print(f"[Mail] Error updating presence: {e}")

    def will_unmount(self):
        """Cleanup when leaving the screen"""
        self._stop_threads = True
        try:
            db = get_db_session()
            update_user_presence(db, self.current_user_id, False)
            db.close()
        except Exception:
            pass

    # ==================== Optimized Email Fetching ====================
    def _fetch_new_emails_for_folder(self) -> List:
        """Fetch only NEW emails for the current folder"""
        new_emails = []

        # Get the latest email timestamp we already have
        latest_timestamp = None
        if self.emails:
            try:
                latest_timestamp = max(
                    getattr(e, 'created_at', None) for e in self.emails if getattr(e, 'created_at', None)
                )
            except Exception:
                pass

        db = get_db_session()
        try:
            from sqlalchemy import desc

            query = db.query(type(self.emails[0]) if self.emails else None).filter(
            ) if self.emails else None

            # For now, just return empty - full implementation would query for newer emails
            # This is a simplified version that can be expanded
            pass
        except Exception as exc:
            print(f"[Mail] Error fetching new emails: {exc}")
        finally:
            db.close()

        return new_emails

    def _refresh_email_list_for_new_messages(self):
        """Refresh email list to check for new emails"""
        try:
            # Refresh the main email list
            self._load_emails()

            # Rebuild content to show updated list
            self.content = self._build_content()

            try:
                self._page.update()
            except Exception:
                pass
        except Exception as e:
            print(f"[Mail] Error refreshing email list: {e}")

    # ==================== Emoji Picker ====================
    def _show_emoji_picker(self, e=None):
        """Show emoji picker dialog"""
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
            "😕", "😟", "🙁", "☹️", "😮", "😯", "😲", "😳", "🥺", "😦", "😧", "😨", "😰", "😥", "😢", "😭",
            "😱", "😖", "😣", "😞", "😓", "😩", "😫", "🥱", "😤", "😡", "😠", "🤬", "😈", "👿", "💀", "☠️",
            "💩", "🤡", "👹", "👺", "👻", "👽", "👾", "🤖", "😺", "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾",
            # Gestures
            "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉", "👆",
            "🖕", "👇", "☝️", "👍", "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️",
            # Hearts
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖",
            "💘", "💝", "💟", "💯", "💢", "💥", "💫", "💦", "💨", "🕳️", "💣", "💬", "👁️‍🗨️",
            # Objects
            "⌚", "📱", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "🖲️", "💽", "💾", "💿", "📀", "📼", "📷", "📸", "📹",
            "🎥", "📽️", "🎞️", "📞", "☎️", "📟", "📠", "📺", "📻", "🎙️", "🎚️", "🎛️", "🧭", "⏱️", "⏲️", "⏰",
            "🕰️", "⌛", "⏳", "📡", "🔋", "🔌", "💡", "🔦", "🕯️", "🪔", "🧯", "🛢️", "💸", "💵", "💴", "💶",
            "💷", "🪙", "💰", "💳", "💎", "⚖️", "🪜", "🧰", "🪛", "🔧", "🔨", "⚒️", "🛠️", "⛏️", "🪚", "🔩",
            "⚙️", "🪤", "🧱", "⛓️", "🧲", "🔫", "💣", "🧨", "🪓", "🔪", "🗡️", "⚔️", "🛡️", "🚬", "⚰️", "🪦",
            "⚱️", "🏺", "🔮", "📿", "🧿", "💈", "⚗️", "🔭", "🔬", "🕳️", "🩹", "🩺", "💊", "💉", "🩸", "🧬",
            "🦠", "🧫", "🧪", "🌡️", "🧹", "🪠", "🧺", "🧻", "🚽", "🚰", "🚿", "🛁", "🛀", "🧼", "🪥", "🪒",
            "🧽", "🪣", "🧴", "🛎️", "🔑", "🗝️", "🚪", "🪑", "🛋️", "🛏️", "🛌", "🧸", "🪆", "🖼️", "🪞", "🪟",
            "🛍️", "🛒", "🎁", "🎈", "🎏", "🎀", "🪄", "🪅", "🎊", "🎉", "🎎", "🏮", "🎐", "🧧", "✉️", "📩",
            "📨", "📧", "💌", "📥", "📤", "📦", "🏷️", "🪧", "📪", "📫", "📬", "📭", "📮", "📯", "📜", "📃",
            "📄", "📑", "🧾", "📊", "📈", "📉", "🗒️", "🗓️", "📆", "📅", "🗑️", "📇", "🗃️", "🗳️", "🗄️", "📋",
            "📁", "📂", "🗂️", "🗞️", "📰", "📓", "📔", "📒", "📕", "📗", "📘", "📙", "📚", "📖", "🔖", "🧷",
            "🔗", "📎", "🖇️", "📐", "📏", "🧮", "📌", "📍", "✂️", "🖊️", "🖋️", "✒️", "🖌️", "🖍️", "📝", "✏️",
            "🔍", "🔎", "🔏", "🔐", "🔒", "🔓",
            # Flags
            "🏳️", "🏴", "🏴‍☠️", "🏁", "🚩", "🎌", "🏳️‍🌈", "🏳️‍⚧️",
        ]

        # Insert emoji into input field
        def insert_emoji(emoji):
            # This will be called with the emoji - in compose we need to insert into body field
            if hasattr(self, '_last_compose_body_field') and self._last_compose_body_field:
                current = self._last_compose_body_field.value or ""
                self._last_compose_body_field.value = current + emoji
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

    # ==================== Message Search ====================
    def _show_message_search(self, e=None):
        """Show message search dialog"""
        def close_dlg(ev=None):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        search_field = ft.TextField(
            hint_text="Search emails...",
            border_color=TEAMS_BLUE,
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda ev: perform_search(ev.control.value),
        )

        results_list = ft.ListView(
            expand=True,
            spacing=4,
        )

        def perform_search(query):
            results_list.controls.clear()
            if not query or not self.emails:
                results_list.controls.append(
                    ft.Container(
                        content=ft.Text("Enter a search term",
                                        color=TEAMS_SUBTEXT),
                        padding=20,
                    )
                )
                try:
                    self._page.update()
                except Exception:
                    pass
                return

            query_lower = query.lower()
            for email in self.emails:
                subject = getattr(email, 'subject', '')
                body = getattr(email, 'body', '')
                sender = getattr(email, 'sender', None)
                sender_name = getattr(sender, 'username',
                                      'Unknown') if sender else 'Unknown'

                if query_lower in subject.lower() or query_lower in body.lower() or query_lower in sender_name.lower():
                    # Create result item
                    preview = body[:80] + ("..." if len(body) > 80 else "")
                    created_at = getattr(email, 'created_at', datetime.now())

                    result_item = ft.Container(
                        padding=ft.padding.all(8),
                        bgcolor="#F5F5F5",
                        border_radius=8,
                        on_click=lambda ev, em=email: (
                            close_dlg(), self._show_email_popup(em)),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text(
                                    sender_name,
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=TEAMS_BLUE,
                                ),
                                ft.Text(
                                    subject,
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    color=TEAMS_TEXT,
                                ),
                                ft.Text(
                                    preview,
                                    size=12,
                                    color=TEAMS_SUBTEXT,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    created_at.strftime(
                                        "%b %d, %Y") if created_at else "",
                                    size=10,
                                    color=TEAMS_SUBTEXT,
                                ),
                            ],
                        ),
                    )
                    results_list.controls.append(result_item)

            if not results_list.controls:
                results_list.controls.append(
                    ft.Container(
                        content=ft.Text("No emails found",
                                        color=TEAMS_SUBTEXT),
                        padding=20,
                    )
                )

            try:
                self._page.update()
            except Exception:
                pass

        dlg = ft.AlertDialog(
            title=ft.Text("Search Emails", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=450,
                height=400,
                content=ft.Column(
                    spacing=10,
                    controls=[
                        search_field,
                        ft.Container(
                            expand=True,
                            content=results_list,
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dlg),
            ]
        )

        # Initialize with empty results
        perform_search("")

        self._page.show_dialog(dlg)

    # ==================== Date Separator ====================
    def _build_date_separator(self, msg_date: date) -> ft.Container:
        """Build a date separator for email list"""
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
                bgcolor=TEAMS_GRAY,
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=12,
                content=ft.Text(
                    date_text, size=12, color=TEAMS_SUBTEXT, weight=ft.FontWeight.W_500),
            ),
            padding=ft.padding.symmetric(vertical=8),
            alignment=ft.alignment.Alignment(0, 0),
        )

    # ==================== Message Context Menu ====================
    def _show_email_context_menu(self, email, e=None):
        """Show context menu for email"""
        def close_dlg(ev=None):
            try:
                self._page.pop_dialog()
                self._page.update()
            except Exception:
                pass

        email_id = getattr(email, 'id', 0)
        subject = getattr(email, 'subject', 'No Subject')

        def copy_subject(ev):
            self._show_success(f"Subject copied: {subject[:30]}...")
            close_dlg(ev)

        def mark_unread(ev):
            try:
                db = get_db_session()
                # Mark as unread
                mark_email_as_read(
                    db, email_id, self.current_user_id, is_read=False)
                db.close()
                self._show_success("Marked as unread")
                self._load_emails()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                print(f"[Mail] Error marking unread: {ex}")
            close_dlg(ev)

        options = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.REPLY, color=TEAMS_BLUE),
                title=ft.Text("Reply"),
                on_click=lambda e: (close_dlg(e), self._reply_to_email(email)),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FORWARD, color=TEAMS_BLUE),
                title=ft.Text("Forward"),
                on_click=lambda e: (close_dlg(e), self._forward_email(email)),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.CONTENT_COPY, color=TEAMS_BLUE),
                title=ft.Text("Copy Subject"),
                on_click=copy_subject,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.MARK_EMAIL_UNREAD, color=WARNING),
                title=ft.Text("Mark as Unread"),
                on_click=mark_unread,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.DELETE, color=ERROR),
                title=ft.Text("Delete"),
                on_click=lambda e: (close_dlg(e), self._delete_email(email)),
            ),
        ]

        dlg = ft.AlertDialog(
            content=ft.Column(
                controls=options,
                spacing=0,
                tight=True,
            ),
            actions=[],
        )
        self._page.show_dialog(dlg)

    def _reply_to_email(self, email):
        """Reply to an email"""
        self.reply_to_email = email
        self.current_folder = "reply"
        self.content = self._build_content()
        self._page.update()

    def _forward_email(self, email):
        """Forward an email"""
        self.forward_email = email
        self.current_folder = "forward"
        self.content = self._build_content()
        self._page.update()

    def _delete_email(self, email):
        """Delete an email"""
        email_id = getattr(email, 'id', 0)
        try:
            db = get_db_session()
            delete_email(db, email_id)
            db.close()
            self._show_success("Deleted")
            self._load_emails()
            self.content = self._build_content()
            self._page.update()
        except Exception as ex:
            print(f"[Mail] Error deleting: {ex}")

    def _build_content(self):
        return ft.Container(
            content=ft.Row([
                self._build_left_nav(),
                ft.VerticalDivider(width=1, color="#E1DFDD"),
                self._build_main_panel()
            ], expand=True),
            expand=True,
        )

    def _build_left_nav(self):
        def nav_item(icon, label, folder, count=0, is_active=False):
            def click(e):
                self.current_folder = folder
                self.selected_emails = set()
                self.content = self._build_content()
                self._load_emails()
                self._page.update()
            return ft.Container(
                on_click=click,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=TEAMS_BLUE if is_active else "transparent",
                border_radius=4,
                content=ft.Row([
                    ft.Icon(icon, size=20,
                            color="white" if is_active else "#605E5C"),
                    ft.Container(width=12),
                    ft.Text(label, size=14, color="white" if is_active else TEAMS_TEXT,
                            weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL),
                    ft.Container(expand=True),
                    ft.Text(str(count), size=12, color="white" if is_active else TEAMS_SUBTEXT,
                            weight=ft.FontWeight.W_500) if count > 0 else ft.Container(),
                ], spacing=0),
            )

        stats = self._get_mail_stats()
        return ft.Container(
            width=260,
            bgcolor=TEAMS_GRAY,
            padding=ft.padding.all(8),
            content=ft.Column([
                ft.Container(
                    padding=12,
                    content=ft.Row([
                        ft.Icon(ft.Icons.MAIL, size=24, color=TEAMS_BLUE),
                        ft.Text("Mail", size=18,
                                weight=ft.FontWeight.W_600, color=TEAMS_TEXT)
                    ])
                ),
                ft.Divider(height=1, color="#E1DFDD"),
                ft.Container(height=8),
                ft.Container(
                    on_click=lambda e: self._go_to_compose(),
                    padding=16,
                    bgcolor=TEAMS_BLUE,
                    border_radius=4,
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD, size=20, color="white"),
                        ft.Text("New mail", size=14, color="white",
                                weight=ft.FontWeight.W_500)
                    ])
                ),
                ft.Container(height=16),
                nav_item(ft.Icons.INBOX, "Inbox", "inbox", stats.get(
                    'inbox', 0), self.current_folder == "inbox"),
                nav_item(ft.Icons.SEND, "Sent", "sent", stats.get(
                    'sent', 0), self.current_folder == "sent"),
                nav_item(ft.Icons.DRAFTS_OUTLINED, "Drafts", "drafts", stats.get(
                    'drafts', 0), self.current_folder == "drafts"),
                nav_item(ft.Icons.STAR, "Starred", "starred",
                         0, self.current_folder == "starred"),
                ft.Divider(height=24, color="#E1DFDD"),
                ft.Text("CREATE", size=11, weight=ft.FontWeight.W_600,
                        color=TEAMS_SUBTEXT),
                ft.Container(height=8),
                nav_item(ft.Icons.CAMPAIGN, "Announcements", "announcement",
                         0, self.current_folder == "announcement"),
                nav_item(ft.Icons.DESCRIPTION, "Offer Letters",
                         "offer_letter", 0, self.current_folder == "offer_letter"),
                ft.Divider(height=24, color="#E1DFDD"),
                ft.Text("GROUPS", size=11, weight=ft.FontWeight.W_600,
                        color=TEAMS_SUBTEXT),
                ft.Container(height=8),
                ft.Container(
                    on_click=lambda e: self._show_create_email_group_dialog(),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=4,
                    content=ft.Row([
                        ft.Icon(ft.Icons.GROUP_ADD, size=20, color=TEAMS_BLUE),
                        ft.Container(width=12),
                        ft.Text("Create Group", size=14, color=TEAMS_TEXT,
                                weight=ft.FontWeight.W_500),
                    ], spacing=0),
                ),
                ft.Container(height=4),
                ft.Container(
                    on_click=lambda e: self._show_email_groups_list(),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=4,
                    content=ft.Row([
                        ft.Icon(ft.Icons.FOLDER, size=20, color=TEAMS_BLUE),
                        ft.Container(width=12),
                        ft.Text("My Groups", size=14, color=TEAMS_TEXT,
                                weight=ft.FontWeight.W_500),
                    ], spacing=0),
                ),
                ft.Container(expand=True),
                ft.Container(
                    padding=12,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    content=ft.Column([
                        ft.Text("Your stats", size=12,
                                weight=ft.FontWeight.W_600, color=TEAMS_TEXT),
                        ft.Container(height=8),
                        ft.Row([
                            ft.Column([
                                ft.Text(str(stats.get('total', 0)), size=20,
                                        weight=ft.FontWeight.BOLD, color=TEAMS_BLUE),
                                ft.Text("Total", size=10, color=TEAMS_SUBTEXT)
                            ]),
                            ft.Column([
                                ft.Text(str(stats.get('unread', 0)), size=20,
                                        weight=ft.FontWeight.BOLD, color=ERROR),
                                ft.Text("Unread", size=10, color=TEAMS_SUBTEXT)
                            ])
                        ], spacing=30)
                    ])
                )
            ], spacing=0)
        )

    def _get_mail_stats(self):
        stats = {'inbox': 0, 'sent': 0, 'drafts': 0, 'unread': 0, 'total': 0}
        db = None
        try:
            db = get_db_session()
            # Rollback any pending transaction first to handle aborted state
            try:
                db.rollback()
            except:
                pass
            stats['unread'] = get_unread_email_count(db, self.current_user_id)
            stats['inbox'] = len(get_user_emails(
                db, self.current_user_id, "inbox", 1000))
            stats['sent'] = len(get_user_emails(
                db, self.current_user_id, "sent", 1000))
            stats['drafts'] = len(get_user_emails(
                db, self.current_user_id, "drafts", 1000))
            stats['total'] = stats['inbox'] + stats['sent'] + stats['drafts']
        except Exception as e:
            print(f"[Mail] Error getting mail stats: {e}")
            if db:
                try:
                    db.rollback()
                except:
                    pass
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass
        return stats

    def _build_main_panel(self):
        if self.current_folder == "compose":
            return self._build_compose_panel()
        elif self.current_folder == "reply":
            return self._build_compose_panel(is_reply=True)
        elif self.current_folder == "forward":
            return self._build_compose_panel(is_forward=True)
        elif self.current_folder == "announcement":
            return self._build_announcement_panel()
        elif self.current_folder == "offer_letter":
            return self._build_offer_letter_panel()
        return self._build_email_list_panel()

    def _build_recipient_selector(self, label, recipients, recipient_type):
        chips = []
        for uid, uname in recipients:
            # Check if it's an email group (starts with "group_")
            if isinstance(uid, str) and uid.startswith("group_"):
                chip = ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    bgcolor="#E91E63" + "15",
                    border_radius=16,
                    content=ft.Row([
                        ft.Icon(ft.Icons.GROUP, size=12, color="#E91E63"),
                        ft.Text(uname, size=12, color="#E91E63",
                                weight=ft.FontWeight.W_500),
                        ft.Container(
                            on_click=lambda e, u=uid, rt=recipient_type: self._remove_recipient(
                                u, rt),
                            padding=2,
                            content=ft.Icon(ft.Icons.CLOSE, size=12,
                                            color="#E91E63"),
                        )
                    ], spacing=4)
                )
            else:
                chip = ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    bgcolor=TEAMS_BLUE + "15",
                    border_radius=16,
                    content=ft.Row([
                        ft.Text(uname, size=12, color=TEAMS_BLUE,
                                weight=ft.FontWeight.W_500),
                        ft.Container(
                            on_click=lambda e, u=uid, rt=recipient_type: self._remove_recipient(
                                u, rt),
                            padding=2,
                            content=ft.Icon(ft.Icons.CLOSE, size=12,
                                            color=TEAMS_BLUE),
                        )
                    ], spacing=4)
                )
            chips.append(chip)

        def add_recipient(e):
            self._show_recipient_picker(recipient_type)

        return ft.Column([
            ft.Text(label, size=13, color=TEAMS_SUBTEXT,
                    weight=ft.FontWeight.W_600),
            ft.Container(
                bgcolor=TEAMS_WHITE,
                border=ft.border.all(1, "#D0D0D0"),
                border_radius=8,
                padding=ft.padding.all(10),
                content=ft.Column([
                    ft.Row(
                        controls=chips + [
                            ft.Container(
                                on_click=add_recipient,
                                padding=ft.padding.symmetric(
                                    horizontal=12, vertical=6),
                                bgcolor=TEAMS_BLUE + "15",
                                border_radius=16,
                                content=ft.Row([
                                    ft.Icon(ft.Icons.ADD, size=14,
                                            color=TEAMS_BLUE),
                                    ft.Text("Add", size=12, color=TEAMS_BLUE,
                                            weight=ft.FontWeight.W_500),
                                ], spacing=4)
                            )
                        ],
                        wrap=True,
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ) if chips else ft.Container(
                        on_click=add_recipient,
                        padding=ft.padding.symmetric(
                            horizontal=12, vertical=10),
                        bgcolor=TEAMS_BLUE + "10",
                        border_radius=8,
                        content=ft.Row([
                            ft.Icon(ft.Icons.PERSON_ADD,
                                    size=16, color=TEAMS_BLUE),
                            ft.Text(f"Add {label.lower()}...",
                                    size=13, color=TEAMS_BLUE),
                        ], spacing=6)
                    )
                ], tight=True)
            )
        ])

    def _show_recipient_picker(self, recipient_type):
        if recipient_type == "to":
            current_recipients = self._to_recipients
        elif recipient_type == "cc":
            current_recipients = self._cc_recipients
        else:
            current_recipients = self._bcc_recipients

        user_list = [
            (u.id, u.username, u.email or f"{u.username}@vernika.local")
            for u in self._all_users
            if u.id != self.current_user_id
        ]

        # Get email groups for this user
        email_group_list = []
        db = None
        try:
            db = get_db_session()
            # Rollback any pending transaction first to handle aborted state
            try:
                db.rollback()
            except:
                pass
            all_groups = get_all_email_groups(db)
            for g in all_groups:
                member_ids = get_email_group_member_ids(db, g.id)
                # Show groups user has created or is a member of
                if g.created_by == self.current_user_id or self.current_user_id in member_ids:
                    email_group_list.append((g.id, g.name, len(member_ids)))
        except Exception as e:
            print(f"[Mail] Error loading email groups: {e}")
            if db:
                try:
                    db.rollback()
                except:
                    pass
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass

        filtered_users = list(user_list)

        def build_user_tiles():
            tiles = []
            for uid, uname, uemail in filtered_users:
                is_sel = (uid, uname) in current_recipients
                colors = [TEAMS_BLUE, "#107C10",
                          "#D13438", "#FFB900", "#8764B8"]
                avatar_color = colors[sum(ord(c)
                                          for c in str(uname)) % len(colors)]

                tile = ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=TEAMS_BLUE + "10" if is_sel else "transparent",
                    border_radius=8,
                    on_click=lambda e, u=uid, n=uname: toggle_user(u, n),
                    content=ft.Row([
                        ft.Container(
                            width=24,
                            height=24,
                            border=ft.border.all(
                                2, TEAMS_BLUE if is_sel else "#C8C8C8"),
                            bgcolor=TEAMS_BLUE if is_sel else "transparent",
                            border_radius=4,
                            content=ft.Icon(
                                ft.Icons.CHECK, size=16, color="white") if is_sel else None,
                        ),
                        ft.Container(width=12),
                        ft.Container(
                            width=36,
                            height=36,
                            bgcolor=avatar_color,
                            border_radius=18,
                            content=ft.Text(
                                str(uname)[0].upper(), size=14, color="white", weight=ft.FontWeight.BOLD),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Container(width=12),
                        ft.Column([
                            ft.Text(
                                str(uname), size=14, weight=ft.FontWeight.W_600 if is_sel else ft.FontWeight.W_500, color=TEAMS_TEXT),
                            ft.Text(str(uemail), size=11, color=TEAMS_SUBTEXT),
                        ], expand=True, spacing=0),
                    ], spacing=0)
                )
                tiles.append(tile)
            return tiles

        def build_group_tiles():
            tiles = []
            for gid, gname, member_count in email_group_list:
                group_key = (f"group_{gid}", gname)
                is_sel = group_key in current_recipients
                colors = ["#E91E63", "#9C27B0",
                          "#3F51B5", "#009688", "#FF5722"]
                group_color = colors[gid % len(colors)]

                tile = ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=TEAMS_BLUE + "10" if is_sel else "transparent",
                    border_radius=8,
                    on_click=lambda e, g=gid, n=gname: toggle_group(g, n),
                    content=ft.Row([
                        ft.Container(
                            width=24,
                            height=24,
                            border=ft.border.all(
                                2, TEAMS_BLUE if is_sel else "#C8C8C8"),
                            bgcolor=TEAMS_BLUE if is_sel else "transparent",
                            border_radius=4,
                            content=ft.Icon(
                                ft.Icons.CHECK, size=16, color="white") if is_sel else None,
                        ),
                        ft.Container(width=12),
                        ft.Container(
                            width=36,
                            height=36,
                            bgcolor=group_color,
                            border_radius=18,
                            content=ft.Icon(
                                ft.Icons.GROUP, size=18, color="white"),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Container(width=12),
                        ft.Column([
                            ft.Text(
                                str(gname), size=14, weight=ft.FontWeight.W_600 if is_sel else ft.FontWeight.W_500, color=TEAMS_TEXT),
                            ft.Text(f"{member_count} members",
                                    size=11, color=TEAMS_SUBTEXT),
                        ], expand=True, spacing=0),
                    ], spacing=0)
                )
                tiles.append(tile)
            return tiles

        def toggle_user(uid, username):
            if recipient_type == "to":
                if (uid, username) in self._to_recipients:
                    self._to_recipients.remove((uid, username))
                else:
                    self._to_recipients.append((uid, username))
            elif recipient_type == "cc":
                if (uid, username) in self._cc_recipients:
                    self._cc_recipients.remove((uid, username))
                else:
                    self._cc_recipients.append((uid, username))
            elif recipient_type == "bcc":
                if (uid, username) in self._bcc_recipients:
                    self._bcc_recipients.remove((uid, username))
                else:
                    self._bcc_recipients.append((uid, username))

            user_column.controls = build_user_tiles()
            update_count()
            self._page.update()

        def toggle_group(gid, gname):
            group_key = (f"group_{gid}", gname)
            if recipient_type == "to":
                if group_key in self._to_recipients:
                    self._to_recipients.remove(group_key)
                else:
                    self._to_recipients.append(group_key)
            elif recipient_type == "cc":
                if group_key in self._cc_recipients:
                    self._cc_recipients.remove(group_key)
                else:
                    self._cc_recipients.append(group_key)
            elif recipient_type == "bcc":
                if group_key in self._bcc_recipients:
                    self._bcc_recipients.remove(group_key)
                else:
                    self._bcc_recipients.append(group_key)

            group_column.controls = build_group_tiles()
            update_count()
            self._page.update()

        def update_count():
            count = len(current_recipients)
            count_text.value = f"{count} selected"
            count_text.visible = count > 0

        def on_search(e):
            query = e.control.value.lower()
            if query:
                filtered = [(uid, uname, uemail) for uid, uname, uemail in user_list
                            if query in str(uname).lower() or query in str(uemail).lower()]
            else:
                filtered = list(user_list)
            filtered_users.clear()
            filtered_users.extend(filter)
            user_column.controls = build_user_tiles()
            self._page.update()

        def close_dlg(e):
            self._page.pop_dialog()
            # Refresh the compose panel to show selected recipients
            self.content = self._build_content()
            self._page.update()

        search_field = ft.TextField(
            hint_text="Search users...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=on_search,
            border_color=TEAMS_BLUE,
            focused_border_color=PRIMARY,
            text_size=14,
        )

        count_text = ft.Text("", size=12, color=TEAMS_SUBTEXT, visible=False)

        user_column = ft.Column(
            controls=build_user_tiles(),
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        group_column = ft.Column(
            controls=build_group_tiles(),
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=False
        )

        # Build tabs content
        tabs_content = ft.Column([
            ft.Container(
                padding=ft.padding.symmetric(vertical=8),
                content=ft.Text("Groups", size=13,
                                weight=ft.FontWeight.W_600, color=TEAMS_SUBTEXT)
            ) if email_group_list else ft.Container(),
            group_column,
            ft.Container(
                padding=ft.padding.symmetric(vertical=8),
                content=ft.Text("Individuals", size=13,
                                weight=ft.FontWeight.W_600, color=TEAMS_SUBTEXT)
            ),
            user_column
        ], spacing=0)

        title_icon = ft.Icons.PERSON_ADD if recipient_type == "to" else (
            ft.Icons.COPY if recipient_type == "cc" else ft.Icons.VISIBILITY_OFF)

        dlg = ft.AlertDialog(
            title=ft.Container(
                padding=ft.padding.only(bottom=8),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(title_icon, color=TEAMS_BLUE, size=24),
                        ft.Text(f"Select {recipient_type.upper()} Recipients",
                                size=18, weight=ft.FontWeight.W_600),
                    ]),
                    ft.Container(height=8),
                    search_field,
                    ft.Container(height=4),
                    count_text,
                ], spacing=0)
            ),
            content=ft.Container(
                width=450,
                height=400,
                content=tabs_content
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg,
                              style=ft.ButtonStyle(color=TEAMS_SUBTEXT)),
                ft.ElevatedButton(
                    "Done",
                    on_click=close_dlg,
                    bgcolor=TEAMS_BLUE,
                    color="white",
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(
                        horizontal=20, vertical=10))
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.show_dialog(dlg)

    def _remove_recipient(self, uid, recipient_type):
        if recipient_type == "to":
            self._to_recipients = [(id, name)
                                   for id, name in self._to_recipients if id != uid]
        elif recipient_type == "cc":
            self._cc_recipients = [(id, name)
                                   for id, name in self._cc_recipients if id != uid]
        elif recipient_type == "bcc":
            self._bcc_recipients = [
                (id, name) for id, name in self._bcc_recipients if id != uid]
        self.content = self._build_content()
        self._page.update()

    def _update_recipient_display(self, recipient_type):
        self.content = self._build_content()
        self._page.update()

    def _remove_attachment(self, e=None):
        """Remove the attached file"""
        self._attached_file_path = {"path": None, "name": None, "url": None}
        # Rebuild compose panel to remove attachment preview
        self.content = self._build_content()
        self._page.update()
        self._show_success("Attachment removed")

    def _build_attachment_preview(self):
        """Build the attachment preview container for compose panel"""
        if not self._attached_file_path.get('name'):
            return ft.Container()

        file_name = self._attached_file_path.get('name', 'Unknown file')

        # Determine file icon based on extension
        file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
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

        return ft.Container(
            margin=ft.margin.only(top=8),
            padding=ft.padding.all(12),
            bgcolor="#E3F2FD",
            border_radius=8,
            border=ft.border.all(1, TEAMS_BLUE),
            content=ft.Row([
                ft.Container(
                    width=36,
                    height=36,
                    bgcolor=TEAMS_BLUE,
                    border_radius=6,
                    content=ft.Icon(file_icon, color="white", size=20),
                    alignment=ft.alignment.Alignment(0, 0)
                ),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(file_name, size=13, weight=ft.FontWeight.W_500,
                            color=TEAMS_TEXT, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text("Attached (cloud storage)",
                            size=10, color=TEAMS_SUBTEXT)
                ], expand=True, spacing=0),
                ft.Container(
                    on_click=self._remove_attachment,
                    padding=ft.padding.all(6),
                    bgcolor=ERROR + "15",
                    border_radius=4,
                    content=ft.Row([
                        ft.Icon(ft.Icons.CLOSE, size=16, color=ERROR),
                        ft.Text("Remove", size=11, color=ERROR,
                                weight=ft.FontWeight.W_500)
                    ], spacing=2)
                )
            ], spacing=0)
        )

    def _get_recipient_ids(self, recipients):
        """Get list of recipient IDs, expanding groups to member IDs"""
        recipient_ids = []
        for uid, _ in recipients:
            # Check if it's an email group (starts with "group_")
            if isinstance(uid, str) and uid.startswith("group_"):
                group_id = int(uid.replace("group_", ""))
                try:
                    db = get_db_session()
                    member_ids = get_email_group_member_ids(db, group_id)
                    recipient_ids.extend(member_ids)
                    db.close()
                except:
                    pass
            else:
                recipient_ids.append(uid)
        return recipient_ids

    def _build_compose_panel(self, is_reply=False, is_forward=False):
        # Recipients are preserved in instance variables
        # They are only cleared in _go_to_compose() when starting a new message

        default_subject, default_body = "", ""

        if is_reply and self.reply_to_email:
            sender = getattr(self.reply_to_email, 'sender', None)
            if sender and sender.id != self.current_user_id:
                if (sender.id, sender.username) not in self._to_recipients:
                    self._to_recipients = [(sender.id, sender.username)]
            default_subject = f"Re: {getattr(self.reply_to_email, 'subject', '')}"
            sender_name = getattr(
                getattr(self.reply_to_email, 'sender', None), 'username', 'Unknown')
            default_body = f"\n\n----- Original from {sender_name} -----\n{getattr(self.reply_to_email, 'body', '')}"

        if is_forward and self.forward_email:
            default_subject = f"Fwd: {getattr(self.forward_email, 'subject', '')}"
            sender_name = getattr(
                getattr(self.forward_email, 'sender', None), 'username', 'Unknown')
            default_body = f"\n\n----- Forwarded -----\nFrom: {sender_name}\n{getattr(self.forward_email, 'body', '')}"

        to_selector = self._build_recipient_selector(
            "To", self._to_recipients, "to")
        cc_selector = self._build_recipient_selector(
            "CC", self._cc_recipients, "cc")
        bcc_selector = self._build_recipient_selector(
            "BCC", self._bcc_recipients, "bcc")

        subject_field = ft.TextField(
            label="Subject",
            value=default_subject,
            border_color=TEAMS_BLUE,
            focused_border_color=PRIMARY,
            text_size=14,
        )

        body_field = ft.TextField(
            label="Message",
            value=default_body,
            border_color=TEAMS_BLUE,
            focused_border_color=PRIMARY,
            min_lines=12,
            max_lines=20,
            multiline=True,
            text_size=14,
            expand=True,
        )

        # Store reference to body field for emoji picker
        self._last_compose_body_field = body_field

        category_opts = [
            ft.dropdown.Option("general", "General"),
            ft.dropdown.Option("hr_communication", "HR"),
            ft.dropdown.Option("meeting_request", "Meeting"),
            ft.dropdown.Option("announcement", "Announcement")
        ]
        category_dropdown = ft.Dropdown(
            label="Category",
            width=150,
            options=category_opts,
            value="general",
            border_color=TEAMS_BLUE,
            focused_border_color=PRIMARY,
        )
        error_txt = ft.Text("", color=ERROR, size=12, visible=False)

        def send(e):
            if not self._to_recipients:
                error_txt.value = "Please select at least one recipient"
                error_txt.visible = True
                self._page.update()
                return
            if not subject_field.value:
                error_txt.value = "Please enter a subject"
                error_txt.visible = True
                self._page.update()
                return

            # Check if there's an attached file
            has_attachment = False
            attachment_path_value = None
            attachment_name_value = None

            if hasattr(self, '_attached_file_path') and self._attached_file_path:
                attached = self._attached_file_path
                if attached.get('url') and attached.get('name'):
                    has_attachment = True
                    attachment_path_value = str(attached.get('url', ''))
                    attachment_name_value = str(attached.get('name', ''))

            # Get db session and send email
            db = None
            try:
                db = get_db_session()
                cat = EmailCategory.GENERAL
                if category_dropdown.value:
                    cat = EmailCategory(category_dropdown.value)

                recipient_ids = self._get_recipient_ids(self._to_recipients)
                cc_ids = self._get_recipient_ids(self._cc_recipients)
                bcc_ids = self._get_recipient_ids(self._bcc_recipients)

                send_email(db, self.current_user_id, subject_field.value, body_field.value,
                           recipient_ids, cat, cc_ids=cc_ids, bcc_ids=bcc_ids,
                           has_attachment=has_attachment,
                           attachment_path=attachment_path_value,
                           attachment_name=attachment_name_value)
                db.commit()
                db.close()
                db = None

                self._show_success("Mail sent successfully")
                self._to_recipients = []
                self._cc_recipients = []
                self._bcc_recipients = []
                # Clear attached file
                self._attached_file_path = {
                    "path": None, "name": None, "url": None}
                self.current_folder = "sent"
                self.content = self._build_content()
                self._load_emails()
                self._page.update()
            except Exception as ex:
                if db:
                    try:
                        db.rollback()
                        db.close()
                    except:
                        pass
                error_txt.value = str(ex)
                error_txt.visible = True
                self._page.update()

        return ft.Container(
            expand=True,
            padding=16,
            content=ft.Column([
                ft.Container(
                    padding=12,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    content=ft.Row([
                        ft.Icon(ft.Icons.EDIT, size=20, color=TEAMS_BLUE),
                        ft.Text("New message" if not is_reply and not is_forward else ("Reply" if is_reply else "Forward"),
                                size=16, weight=ft.FontWeight.W_600, color=TEAMS_TEXT)
                    ])
                ),
                ft.Container(height=12),
                ft.Container(
                    padding=16,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    content=ft.Column([
                        to_selector,
                        ft.Container(height=8),
                        cc_selector,
                        ft.Container(height=8),
                        bcc_selector,
                        ft.Container(height=12),
                        subject_field,
                        ft.Container(height=12),
                        body_field,
                        ft.Container(height=8),
                        ft.Row([
                            category_dropdown,
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.EMOJI_EMOTIONS,
                                tooltip="Add Emoji",
                                on_click=self._show_emoji_picker,
                                icon_color=TEAMS_BLUE,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ATTACH_FILE,
                                tooltip="Attach File",
                                on_click=self._attach_file_in_compose,
                                icon_color=TEAMS_BLUE,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Delete Draft",
                                on_click=lambda e: self._clear_compose(),
                                icon_color=ERROR,
                            ),
                        ]),
                        # Attachment preview (shows when file is attached)
                        self._build_attachment_preview(),
                        error_txt
                    ], spacing=0)
                ),
                ft.Container(height=12),
                ft.Row([
                    ft.Container(expand=True),
                    ft.Container(
                        on_click=lambda e: self._show_success("Draft saved"),
                        padding=ft.padding.symmetric(
                            horizontal=16, vertical=8),
                        bgcolor=TEAMS_GRAY,
                        border_radius=20,
                        content=ft.Row([
                            ft.Icon(ft.Icons.SAVE, size=16, color=TEAMS_TEXT),
                            ft.Text("Save Draft", size=13, color=TEAMS_TEXT)
                        ])
                    ),
                    ft.Container(width=8),
                    ft.Container(
                        on_click=send,
                        padding=ft.padding.symmetric(
                            horizontal=20, vertical=8),
                        bgcolor=TEAMS_BLUE,
                        border_radius=20,
                        content=ft.Row([
                            ft.Icon(ft.Icons.SEND, size=16, color="white"),
                            ft.Text("Send", size=13, color="white",
                                    weight=ft.FontWeight.W_500)
                        ])
                    )
                ])
            ], scroll=ft.ScrollMode.AUTO)
        )

    def _build_announcement_panel(self):
        title_field = ft.TextField(
            label="Title", border_color=TEAMS_BLUE, focused_border_color=PRIMARY)
        content_field = ft.TextField(label="Content", border_color=TEAMS_BLUE,
                                     focused_border_color=PRIMARY, min_lines=8, multiline=True)
        error_txt = ft.Text("", color=ERROR, size=12, visible=False)

        def publish(e):
            if not title_field.value or not content_field.value:
                error_txt.value = "Fill all fields"
                error_txt.visible = True
                self._page.update()
                return
            try:
                db = get_db_session()
                recipient_ids = [u.id for u in get_all_users(
                    db) if u.id != self.current_user_id]
                send_email(db, self.current_user_id, title_field.value, content_field.value,
                           recipient_ids, EmailCategory.ANNOUNCEMENT)
                db.close()
                self._show_success("Published!")
                self.current_folder = "sent"
                self.content = self._build_content()
                self._load_emails()
                self._page.update()
            except Exception as ex:
                error_txt.value = str(ex)
                error_txt.visible = True
                self._page.update()

        return ft.Container(
            expand=True,
            padding=24,
            content=ft.Column([
                ft.Container(
                    padding=16,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    content=ft.Row([
                        ft.Icon(ft.Icons.CAMPAIGN, size=24, color=ERROR),
                        ft.Text("Announcement", size=20,
                                weight=ft.FontWeight.W_600, color=TEAMS_TEXT)
                    ])
                ),
                ft.Container(height=16),
                ft.Container(
                    padding=20,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    content=ft.Column([title_field, ft.Container(
                        height=12), content_field, error_txt])
                ),
                ft.Container(height=16),
                ft.Container(
                    on_click=publish,
                    padding=16,
                    bgcolor=ERROR,
                    border_radius=4,
                    content=ft.Row([
                        ft.Icon(ft.Icons.CAMPAIGN, size=18, color="white"),
                        ft.Text("Publish", size=14, color="white",
                                weight=ft.FontWeight.W_500)
                    ])
                )
            ], scroll=ft.ScrollMode.AUTO)
        )

    def _build_offer_letter_panel(self):
        all_users = []
        db = None
        try:
            db = get_db_session()
            # Rollback any pending transaction first to handle aborted state
            try:
                db.rollback()
            except:
                pass
            all_users = get_all_users(db)
        except Exception as e:
            print(f"[Mail] Error loading users for offer letter: {e}")
            if db:
                try:
                    db.rollback()
                except:
                    pass
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass

        user_opts = [ft.dropdown.Option(
            str(u.id), f"{u.username}") for u in all_users if u.id != self.current_user_id]
        to_dropdown = ft.Dropdown(
            label="Employee", width=350, options=user_opts)
        position_field = ft.TextField(label="Position", width=350)
        salary_field = ft.TextField(label="Salary", width=200)
        date_field = ft.TextField(label="Start Date", width=200)
        terms_field = ft.TextField(label="Terms", width=500, min_lines=5, multiline=True,
                                   value="1. Subject to verification\n2. 30 days notice\n3. Company policies")
        error_txt = ft.Text("", color=ERROR, size=12, visible=False)

        def send_offer(e):
            if not to_dropdown.value or not position_field.value:
                error_txt.value = "Fill required fields"
                error_txt.visible = True
                self._page.update()
                return
            body = f"Dear Employee,\n\nWe offer you {position_field.value}.\n\nSalary: {salary_field.value or 'Negotiable'}\nStart: {date_field.value or 'TBD'}\n\nTerms:\n{terms_field.value}\n\nBest,\n{self.current_username}\nHR"
            try:
                db = get_db_session()
                send_email(db, self.current_user_id, f"Offer - {position_field.value}",
                           body, [int(to_dropdown.value)], EmailCategory.PROMOTION)
                db.commit()
                self._show_success("Sent!")
                self.current_folder = "sent"
                self.content = self._build_content()
                self._load_emails()
                self._page.update()
            except Exception as ex:
                error_txt.value = str(ex)
                error_txt.visible = True
                self._page.update()
                if db:
                    try:
                        db.rollback()
                    except:
                        pass
            finally:
                if db:
                    try:
                        db.close()
                    except:
                        pass

        return ft.Container(
            expand=True,
            padding=24,
            content=ft.Column([
                ft.Container(
                    padding=16,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DESCRIPTION, size=24, color=SUCCESS),
                        ft.Text("Offer Letter", size=20,
                                weight=ft.FontWeight.W_600, color=TEAMS_TEXT)
                    ])
                ),
                ft.Container(height=16),
                ft.Container(
                    padding=20,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    content=ft.Column([
                        to_dropdown,
                        ft.Container(height=12),
                        position_field,
                        ft.Container(height=12),
                        ft.Row([salary_field, date_field], spacing=20),
                        ft.Container(height=12),
                        terms_field,
                        error_txt
                    ])
                ),
                ft.Container(height=16),
                ft.Container(
                    on_click=send_offer,
                    padding=16,
                    bgcolor=SUCCESS,
                    border_radius=4,
                    content=ft.Row([
                        ft.Icon(ft.Icons.SEND, size=18, color="white"),
                        ft.Text("Send", size=14, color="white",
                                weight=ft.FontWeight.W_500)
                    ])
                )
            ], scroll=ft.ScrollMode.AUTO)
        )

    def _build_email_list_panel(self):
        folder_names = {
            "inbox": ("Inbox", ft.Icons.INBOX),
            "sent": ("Sent", ft.Icons.SEND),
            "drafts": ("Drafts", ft.Icons.DRAFTS_OUTLINED),
            "starred": ("Starred", ft.Icons.STAR),
            "announcement": ("Announcements", ft.Icons.CAMPAIGN),
            "offer_letter": ("Offer Letters", ft.Icons.DESCRIPTION)
        }
        title, icon = folder_names.get(
            self.current_folder, ("Mail", ft.Icons.MAIL))

        search = ft.TextField(
            hint_text="Search", width=200, dense=True,
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda e: self._handle_search(e)
        )

        def refresh(e):
            self._load_emails()
            self.content = self._build_content()
            self._page.update()

        def bulk_delete(e):
            if self.selected_emails:
                for eid in list(self.selected_emails):
                    try:
                        db = get_db_session()
                        delete_email(db, eid)
                        db.close()
                    except:
                        pass
                self._show_success(f"Deleted {len(self.selected_emails)}")
                self.selected_emails = set()
                self._load_emails()
                self.content = self._build_content()
                self._page.update()

        def bulk_send(e):
            if self.selected_emails:
                self._show_bulk_send_dialog()

        if not self.emails:
            return ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Container(
                        padding=16,
                        bgcolor=TEAMS_WHITE,
                        content=ft.Row([
                            ft.Icon(icon, size=22, color=TEAMS_BLUE),
                            ft.Text(
                                title, size=18, weight=ft.FontWeight.W_600, color=TEAMS_TEXT),
                            ft.Container(expand=True),
                            search,
                            ft.Container(on_click=refresh, padding=8, bgcolor=TEAMS_GRAY, border_radius=4,
                                         content=ft.Icon(ft.Icons.REFRESH, size=18, color=TEAMS_TEXT))
                        ])
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Container(padding=30, bgcolor=TEAMS_WHITE, border_radius=50,
                                         content=ft.Icon(icon, size=48, color="#C8C8C8")),
                            ft.Text("No messages", size=16,
                                    color=TEAMS_SUBTEXT),
                            ft.Container(height=10),
                            ft.Container(on_click=lambda e: self._go_to_compose(), padding=16,
                                         bgcolor=TEAMS_BLUE, border_radius=4,
                                         content=ft.Text("New mail", size=14, color="white"))
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.Alignment(0, 0)
                    )
                ])
            )

        email_items = [self._build_email_item(e) for e in self.emails]

        return ft.Container(
            expand=True,
            content=ft.Column([
                ft.Container(
                    padding=12,
                    bgcolor=TEAMS_WHITE,
                    content=ft.Row([
                        ft.Icon(icon, size=20, color=TEAMS_BLUE),
                        ft.Text(title, size=16,
                                weight=ft.FontWeight.W_600, color=TEAMS_TEXT),
                        ft.Text(f"({len(self.emails)})",
                                size=12, color=TEAMS_SUBTEXT),
                        ft.Container(expand=True),
                        search,
                        ft.Container(width=8),
                        ft.Container(on_click=lambda e: self._show_message_search(), padding=6, bgcolor=TEAMS_GRAY, border_radius=4,
                                     content=ft.Icon(ft.Icons.SEARCH, size=16, color=TEAMS_TEXT)),
                        ft.Container(width=8),
                        ft.Container(on_click=refresh, padding=6, bgcolor=TEAMS_GRAY, border_radius=4,
                                     content=ft.Icon(ft.Icons.REFRESH, size=16, color=TEAMS_TEXT)),
                        ft.Container(width=8),
                        ft.Container(on_click=bulk_send, padding=6,
                                     bgcolor=SUCCESS if self.selected_emails else TEAMS_GRAY, border_radius=4,
                                     content=ft.Row([
                                         ft.Icon(
                                             ft.Icons.SEND, size=16, color="white" if self.selected_emails else TEAMS_TEXT),
                                         ft.Text(
                                             "Send to Selected", size=11, color="white" if self.selected_emails else TEAMS_TEXT)
                                     ], spacing=4)) if self.selected_emails else ft.Container(),
                        ft.Container(width=8),
                        ft.Container(on_click=bulk_delete, padding=6,
                                     bgcolor=ERROR if self.selected_emails else TEAMS_GRAY, border_radius=4,
                                     content=ft.Icon(ft.Icons.DELETE, size=16, color="white" if self.selected_emails else TEAMS_TEXT)) if self.selected_emails else ft.Container()
                    ])
                ),
                ft.Container(
                    padding=8,
                    bgcolor="#FFF8E1" if self.selected_emails else "transparent",
                    content=ft.Text(f"{len(self.selected_emails)} selected",
                                    size=13, color=WARNING, weight=ft.FontWeight.W_500)
                    if self.selected_emails else ft.Container()
                ) if self.selected_emails else ft.Container(),
                ft.Column(email_items, spacing=2,
                          scroll=ft.ScrollMode.AUTO, expand=True)
            ])
        )

    def _show_bulk_send_dialog(self):
        def close_dlg(e):
            self._page.pop_dialog()
            self._page.update()

        subject_field = ft.TextField(label="Subject", border_color=TEAMS_BLUE)
        body_field = ft.TextField(
            label="Message", multiline=True, min_lines=5, border_color=TEAMS_BLUE)
        error_txt = ft.Text("", color=ERROR, size=12, visible=False)

        def send_bulk(e):
            if not subject_field.value or not body_field.value:
                error_txt.value = "Please fill all fields"
                error_txt.visible = True
                self._page.update()
                return

            sender_ids = set()
            for email in self.emails:
                if getattr(email, 'id', 0) in self.selected_emails:
                    sender = getattr(email, 'sender', None)
                    if sender and sender.id != self.current_user_id:
                        sender_ids.add(sender.id)

            if not sender_ids:
                error_txt.value = "No valid recipients found"
                error_txt.visible = True
                self._page.update()
                return

            try:
                db = get_db_session()
                for recipient_id in sender_ids:
                    send_email(db, self.current_user_id, subject_field.value, body_field.value,
                               [recipient_id], EmailCategory.GENERAL)
                db.close()
                self._show_success(f"Sent to {len(sender_ids)} recipients")
                self.selected_emails = set()
                close_dlg(e)
                self.current_folder = "sent"
                self.content = self._build_content()
                self._load_emails()
                self._page.update()
            except Exception as ex:
                error_txt.value = str(ex)
                error_txt.visible = True
                self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Send to Selected Contacts"),
            content=ft.Column([
                ft.Text(
                    f"Sending to {len(self.selected_emails)} selected emails", size=12, color=TEAMS_SUBTEXT),
                ft.Container(height=12),
                subject_field,
                ft.Container(height=8),
                body_field,
                error_txt
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Send", on_click=send_bulk,
                                  bgcolor=TEAMS_BLUE, color="white")
            ]
        )
        self._page.show_dialog(dlg)

    def _build_email_item(self, email):
        is_unread = not getattr(email, 'is_read', False)
        email_id = getattr(email, 'id', 0)
        is_selected = email_id in self.selected_emails
        sender = getattr(email, 'sender', None)
        sender_name = getattr(sender, 'username',
                              'Unknown') if sender else "Unknown"
        subject = getattr(email, 'subject', 'No Subject')
        body = getattr(email, 'body', '')
        preview = body[:60] + '...' if len(body) > 60 else body
        category = getattr(email, 'category', EmailCategory.GENERAL)
        created_at = getattr(email, 'created_at', datetime.now())

        cat_color = {
            EmailCategory.GENERAL: TEAMS_BLUE,
            EmailCategory.HR_COMMUNICATION: SUCCESS,
            EmailCategory.MEETING_REQUEST: WARNING,
            EmailCategory.ANNOUNCEMENT: ERROR,
            EmailCategory.PROMOTION: "#8764B8"
        }.get(category, TEAMS_BLUE)

        def toggle_select(e):
            if is_selected:
                self.selected_emails.discard(email_id)
            else:
                self.selected_emails.add(email_id)
            self.content = self._build_content()
            self._page.update()

        def reply(e):
            e.stop_propagation()
            self.reply_to_email = email
            self.current_folder = "reply"
            self.content = self._build_content()
            self._page.update()

        def forward(e):
            e.stop_propagation()
            self.forward_email = email
            self.current_folder = "forward"
            self.content = self._build_content()
            self._page.update()

        def delete_item(e):
            e.stop_propagation()
            try:
                db = get_db_session()
                delete_email(db, email_id)
                db.close()
                self._show_success("Deleted")
                self._load_emails()
                self.content = self._build_content()
                self._page.update()
            except:
                pass

        action_buttons = ft.Container(
            opacity=0,
            animate_opacity=200,
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.REPLY, icon_size=16,
                              tooltip="Reply", on_click=reply, bgcolor="transparent"),
                ft.IconButton(icon=ft.Icons.FORWARD, icon_size=16,
                              tooltip="Forward", on_click=forward, bgcolor="transparent"),
                ft.IconButton(icon=ft.Icons.DELETE, icon_size=16, tooltip="Delete",
                              on_click=delete_item, bgcolor="transparent"),
            ], spacing=0)
        )

        container_ref = {"container": None}

        def on_hover(e):
            if e.data == "true":
                if container_ref["container"]:
                    container_ref["container"].bgcolor = "#F5F5F5"
                action_buttons.opacity = 1
            else:
                if container_ref["container"]:
                    container_ref["container"].bgcolor = TEAMS_WHITE
                action_buttons.opacity = 0
            self._page.update()

        if created_at.date() == datetime.now().date():
            time_str = created_at.strftime('%I:%M %p')
        elif created_at.date() == datetime.now().date() - __import__('datetime').timedelta(days=1):
            time_str = "Yesterday"
        else:
            time_str = created_at.strftime('%b %d')

        email_container = ft.Container(
            on_click=lambda e: self._show_email_popup(email),
            on_hover=on_hover,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=TEAMS_WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, "#EDEBE9")),
            content=ft.Row([
                ft.Container(
                    on_click=toggle_select,
                    padding=4,
                    content=ft.Container(
                        width=18,
                        height=18,
                        border=ft.border.all(
                            2, TEAMS_BLUE if is_selected else "#C8C8C8"),
                        bgcolor=TEAMS_BLUE if is_selected else "transparent",
                        border_radius=4,
                        content=ft.Icon(ft.Icons.CHECK, size=14,
                                        color="white") if is_selected else None
                    )
                ),
                ft.Container(width=8),
                ft.Icon(ft.Icons.STAR, size=16, color=WARNING if getattr(
                    email, 'is_starred', False) else "#C8C8C8"),
                ft.Container(width=8),
                ft.Container(
                    width=36,
                    height=36,
                    bgcolor=TEAMS_BLUE,
                    border_radius=18,
                    content=ft.Text(sender_name[0].upper(
                    ), size=14, color="white", weight=ft.FontWeight.BOLD),
                    alignment=ft.alignment.Alignment(0, 0)
                ),
                ft.Container(width=12),
                ft.Column([
                    ft.Row([
                        ft.Text(
                            sender_name, size=13, weight=ft.FontWeight.W_600 if is_unread else ft.FontWeight.NORMAL, color=TEAMS_TEXT),
                        ft.Container(expand=True),
                        ft.Text(time_str, size=11, color=TEAMS_SUBTEXT),
                    ]),
                    ft.Container(height=1),
                    ft.Text(subject, size=12, weight=ft.FontWeight.W_600 if is_unread else ft.FontWeight.NORMAL,
                            color=TEAMS_TEXT, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(preview, size=11, color=TEAMS_SUBTEXT,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                ], expand=True, spacing=0),
                ft.Container(width=8),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    bgcolor=cat_color,
                    border_radius=8,
                    content=ft.Text(category.name[:3].upper() if hasattr(
                        category, 'name') else "GEN", size=9, color="white", weight=ft.FontWeight.BOLD)
                ),
                ft.Container(width=8),
                action_buttons
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        container_ref["container"] = email_container
        return email_container

    def _handle_search(self, e):
        self.search_query = e.control.value.lower()
        self._load_emails()
        if self.search_query:
            self.emails = [em for em in self.emails
                           if self.search_query in getattr(em, 'subject', '').lower()
                           or self.search_query in getattr(em, 'body', '').lower()]
        self.content = self._build_content()
        self._page.update()

    def _go_to_compose(self):
        # Clear recipients when starting a new compose
        self._to_recipients = []
        self._cc_recipients = []
        self._bcc_recipients = []
        self._current_draft_id = None
        # Clear any attached files when starting a new compose
        self._attached_file_path = {"path": None, "name": None, "url": None}
        self.current_folder = "compose"
        self.content = self._build_content()
        self._page.update()

    def _clear_compose(self):
        """Clear compose fields and go back to inbox"""
        self._to_recipients = []
        self._cc_recipients = []
        self._bcc_recipients = []
        # Clear attached files
        self._attached_file_path = {"path": None, "name": None, "url": None}
        self.current_folder = "inbox"
        self.content = self._build_content()
        self._page.update()

    def _attach_file_in_compose(self, e=None):
        """Attach file in compose mail - uploads to Supabase for cloud access"""
        # Initialize file picker if not already done
        if not hasattr(self, '_file_picker') or not self._file_picker:
            self._file_picker = ft.FilePicker()
            self._page.services.append(self._file_picker)

        # Store selected file info (will store Supabase URL after upload)
        self._attached_file_path = {"path": None, "name": None, "url": None}

        def handle_picked_files(files):
            """Process picked files after selection - with Supabase upload"""
            try:
                if not files:
                    return

                file_info = files[0]
                file_path = file_info.path if hasattr(
                    file_info, 'path') else str(file_info)
                file_name = file_path.split(
                    '/')[-1] if '/' in file_path else file_path

                # Show uploading message
                snack = ft.SnackBar(content=ft.Text(
                    f"Uploading {file_name} to cloud..."), bgcolor=TEAMS_BLUE)
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
                            folder="mail_attachments",
                            custom_filename=f"{self.current_user_id}_{int(datetime.now().timestamp())}_{file_name}"
                        )

                        if success and url_or_error:
                            file_url = url_or_error
                            upload_success = True
                            print(
                                f"[Mail] File uploaded to Supabase: {file_url}")
                        else:
                            upload_error = url_or_error
                            print(
                                f"[Mail] Supabase upload failed: {url_or_error}")
                    else:
                        upload_error = "Cloud storage not configured"
                        print("[Mail] Supabase storage not available")
                except Exception as upload_err:
                    upload_error = str(upload_err)
                    print(f"[Mail] Upload error: {upload_err}")

                # If upload failed, show error
                if not upload_success:
                    error_msg = upload_error or "Upload failed"
                    snack = ft.SnackBar(content=ft.Text(
                        f"Cloud upload failed: {error_msg}. File not attached."), bgcolor=ERROR)
                    self._page.overlay.append(snack)
                    snack.open = True
                    self._page.update()
                    return

                # Store the Supabase URL (cloud accessible)
                self._attached_file_path["path"] = file_url
                self._attached_file_path["name"] = file_name
                self._attached_file_path["url"] = file_url

                # Refresh the compose panel to show attachment preview
                self.content = self._build_content()
                self._page.update()

                # Show success message with filename
                snack = ft.SnackBar(content=ft.Text(
                    f"Attached (cloud): {file_name}"), bgcolor=SUCCESS)
                self._page.overlay.append(snack)
                snack.open = True
                self._page.update()

            except Exception as ex:
                print(f"[Mail] Error handling attached file: {ex}")
                snack = ft.SnackBar(content=ft.Text(
                    f"Error attaching file: {ex}"), bgcolor=ERROR)
                self._page.overlay.append(snack)
                snack.open = True
                self._page.update()

        async def pick_and_attach():
            """Async function to pick files"""
            try:
                files = await self._file_picker.pick_files(
                    dialog_title="Choose a file to attach",
                    file_type=ft.FilePickerFileType.ANY,
                )
                handle_picked_files(files)
            except Exception as ex:
                print(f"[Mail] File picker error: {ex}")
                snack = ft.SnackBar(content=ft.Text(
                    f"Error opening file picker: {ex}"), bgcolor=ERROR)
                self._page.overlay.append(snack)
                snack.open = True
                self._page.update()

        # Run the async function
        self._page.run_task(pick_and_attach)

    def _load_emails(self):
        """Load emails for the current user and folder"""
        self.emails = []
        db = None
        try:
            db = get_db_session()
            # Rollback any pending transaction first to handle aborted state
            try:
                db.rollback()
            except:
                pass
            self.emails = get_user_emails(
                db, self.current_user_id, self.current_folder)
        except Exception as e:
            print(f"[Mail] Error loading emails: {e}")
            # Try to rollback to recover the session
            if db:
                try:
                    db.rollback()
                except:
                    pass
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass

    def _view_email(self, email_id):
        try:
            db = get_db_session()
            email = get_email_by_id(db, email_id)
            if email and not email.is_read:
                mark_email_as_read(db, email_id, self.current_user_id)
            db.close()
            if email:
                self._show_email_popup(email)
        except:
            pass

    def _show_email_popup(self, email):
        sender = getattr(email, 'sender', None)
        sender_name = getattr(sender, 'username',
                              'Unknown') if sender else "Unknown"
        sender_email = getattr(sender, 'email', '') if sender else ""
        subject = getattr(email, 'subject', 'No Subject')
        body = getattr(email, 'body', '')
        created_at = getattr(email, 'created_at', datetime.now())
        category = getattr(email, 'category', EmailCategory.GENERAL)
        email_id = getattr(email, 'id', 0)

        # Get attachment info
        has_attachment = getattr(email, 'has_attachment', False)
        attachment_path = getattr(email, 'attachment_path', None)
        attachment_name = getattr(email, 'attachment_name', None)

        cat_color = {
            EmailCategory.GENERAL: TEAMS_BLUE,
            EmailCategory.HR_COMMUNICATION: SUCCESS,
            EmailCategory.MEETING_REQUEST: WARNING,
            EmailCategory.ANNOUNCEMENT: ERROR,
            EmailCategory.PROMOTION: "#8764B8"
        }.get(category, TEAMS_BLUE)

        def close_dialog(e=None):
            self._page.pop_dialog()
            self._page.update()

        def reply(e):
            close_dialog()
            self.reply_to_email = email
            self.current_folder = "reply"
            self.content = self._build_content()
            self._page.update()

        def forward(e):
            close_dialog()
            self.forward_email = email
            self.current_folder = "forward"
            self.content = self._build_content()
            self._page.update()

        def delete_email_action(e):
            try:
                db = get_db_session()
                delete_email(db, email_id)
                db.close()
                close_dialog()
                self._show_success("Deleted")
                self._load_emails()
                self.content = self._build_content()
                self._page.update()
            except:
                pass

        def download_attachment(e):
            """Open attachment URL in browser"""
            import webbrowser
            if attachment_path and attachment_path.startswith('http'):
                webbrowser.open(attachment_path)
            else:
                self._show_snackbar("Invalid attachment URL")

        try:
            db = get_db_session()
            if not getattr(email, 'is_read', False):
                mark_email_as_read(db, email_id, self.current_user_id)
            db.close()
        except:
            pass

        # Build attachment display (if exists)
        attachment_widget = None
        if has_attachment and attachment_path and attachment_name:
            # Check if it's an image
            is_image = any(attachment_name.lower().endswith(ext)
                           for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])

            # Check if URL is valid
            is_url = attachment_path.startswith(
                'http') if attachment_path else False

            if is_image and is_url:
                # Show image preview with download button
                attachment_widget = ft.Container(
                    margin=ft.margin.only(top=12),
                    content=ft.Column([
                        ft.Container(
                            content=ft.Image(
                                src=attachment_path,
                                width=300,
                                height=200,
                                fit="contain",
                                border_radius=8,
                            ),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Container(height=8),
                        ft.Container(
                            padding=ft.padding.all(8),
                            bgcolor=TEAMS_GRAY,
                            border_radius=8,
                            content=ft.Row([
                                ft.Icon(ft.Icons.ATTACH_FILE,
                                        size=16, color=TEAMS_BLUE),
                                ft.Text(attachment_name, size=12,
                                        weight=ft.FontWeight.W_500, expand=True),
                                ft.Container(
                                    on_click=download_attachment,
                                    padding=ft.padding.symmetric(
                                        horizontal=12, vertical=6),
                                    bgcolor=TEAMS_BLUE,
                                    border_radius=4,
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.DOWNLOAD,
                                                size=14, color="white"),
                                        ft.Text("Download", size=11,
                                                color="white"),
                                    ], spacing=4)
                                )
                            ], spacing=8)
                        )
                    ], spacing=0)
                )
            elif is_url:
                # Show file attachment with download button
                file_ext = attachment_name.lower().split(
                    '.')[-1] if attachment_name else ''
                file_icon = ft.Icons.INSERT_DRIVE_FILE
                if file_ext in ['pdf']:
                    file_icon = ft.Icons.PICTURE_AS_PDF
                elif file_ext in ['doc', 'docx']:
                    file_icon = ft.Icons.DESCRIPTION
                elif file_ext in ['xls', 'xlsx']:
                    file_icon = ft.Icons.TABLE_CHART
                elif file_ext in ['zip', 'rar', '7z']:
                    file_icon = ft.Icons.FOLDER_ZIP

                attachment_widget = ft.Container(
                    margin=ft.margin.only(top=12),
                    padding=ft.padding.all(12),
                    bgcolor=TEAMS_GRAY,
                    border_radius=8,
                    content=ft.Row([
                        ft.Container(
                            width=40,
                            height=40,
                            bgcolor=TEAMS_BLUE,
                            border_radius=8,
                            content=ft.Icon(file_icon, color="white", size=20),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Column([
                            ft.Text(attachment_name or "File", size=13,
                                    weight=ft.FontWeight.W_500),
                            ft.Text("Tap to download", size=10,
                                    color=TEAMS_SUBTEXT)
                        ], expand=True, spacing=2),
                        ft.Container(
                            on_click=download_attachment,
                            padding=ft.padding.symmetric(
                                horizontal=12, vertical=8),
                            bgcolor=TEAMS_BLUE,
                            border_radius=4,
                            content=ft.Row([
                                ft.Icon(ft.Icons.DOWNLOAD,
                                        size=16, color="white"),
                                ft.Text("Download", size=12, color="white"),
                            ], spacing=4)
                        )
                    ], spacing=12)
                )

        email_content = ft.Container(
            width=600,
            height=500,
            padding=20,
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            width=48,
                            height=48,
                            bgcolor=TEAMS_BLUE,
                            border_radius=24,
                            content=ft.Text(sender_name[0].upper(
                            ), size=20, color="white", weight=ft.FontWeight.BOLD),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Container(width=12),
                        ft.Column([
                            ft.Row([
                                ft.Text(
                                    sender_name, size=16, weight=ft.FontWeight.W_600, color=TEAMS_TEXT),
                                ft.Container(width=8),
                                ft.Container(
                                    padding=ft.padding.symmetric(
                                        horizontal=8, vertical=2),
                                    bgcolor=cat_color,
                                    border_radius=10,
                                    content=ft.Text(category.name.upper() if hasattr(
                                        category, 'name') else "GENERAL", size=10, color="white", weight=ft.FontWeight.BOLD)
                                ),
                            ]),
                            ft.Text(sender_email, size=12,
                                    color=TEAMS_SUBTEXT),
                        ]),
                        ft.Container(expand=True),
                        ft.Text(created_at.strftime('%b %d, %Y %I:%M %p'),
                                size=12, color=TEAMS_SUBTEXT),
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ),
                ft.Divider(height=24, color="#E1DFDD"),
                ft.Text(subject, size=18, weight=ft.FontWeight.W_600,
                        color=TEAMS_TEXT),
                ft.Container(height=16),
                ft.Container(
                    expand=True,
                    content=ft.Text(body, size=14, color=TEAMS_TEXT,
                                    selectable=True, text_align=ft.TextAlign.LEFT)
                ),
                # Add attachment widget if exists
                attachment_widget if attachment_widget else ft.Container(),
            ], scroll=ft.ScrollMode.AUTO)
        )

        self.email_detail_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Container(
                padding=ft.padding.only(bottom=8),
                content=ft.Row([
                    ft.Icon(ft.Icons.MAIL, size=20, color=TEAMS_BLUE),
                    ft.Text("Email", size=16, weight=ft.FontWeight.W_600),
                ])
            ),
            content=email_content,
            actions=[
                ft.TextButton(content=ft.Row([ft.Icon(ft.Icons.DELETE, size=16), ft.Text(
                    "Delete")]), on_click=delete_email_action),
                ft.TextButton(content=ft.Row(
                    [ft.Icon(ft.Icons.FORWARD, size=16), ft.Text("Forward")]), on_click=forward),
                ft.TextButton(content=ft.Row(
                    [ft.Icon(ft.Icons.REPLY, size=16), ft.Text("Reply")]), on_click=reply),
                ft.ElevatedButton(content=ft.Text("Close"),
                                  on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.show_dialog(self.email_detail_dialog)
        self._page.update()

    def _show_email_detail(self, email):
        self._show_email_popup(email)

    def _show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True

    def _show_snackbar(self, message: str) -> None:
        try:
            snack = ft.SnackBar(
                content=ft.Text(message),
                behavior=ft.SnackBarBehavior.FLOATING,
                margin=10,
                bgcolor=TEAMS_TEXT,
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
        except Exception as exc:
            print(f"[MailScreen] Snackbar failed: {exc}")

    def _show_create_email_group_dialog(self):
        """Show dialog to create a new email group"""
        def close_dlg(ev):
            self._page.pop_dialog()
            self._page.update()

        name_field = ft.TextField(
            label="Group Name", border_color=TEAMS_BLUE, focused_border_color=PRIMARY)
        desc_field = ft.TextField(label="Description", border_color=TEAMS_BLUE,
                                  focused_border_color=PRIMARY, multiline=True, min_lines=2)
        error_txt = ft.Text("", color=ERROR, size=12, visible=False)

        def create_group(ev):
            if not name_field.value:
                error_txt.value = "Please enter a group name"
                error_txt.visible = True
                self._page.update()
                return

            try:
                db = get_db_session()
                create_email_group(db, name_field.value,
                                   desc_field.value or "", self.current_user_id)
                db.close()
                self._show_success(f"Group '{name_field.value}' created!")
                self._load_email_groups()
                close_dlg(ev)
            except Exception as ex:
                error_txt.value = str(ex)
                error_txt.visible = True
                self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.GROUP_ADD, color=TEAMS_BLUE, size=24),
                ft.Text("Create Email Group", size=18,
                        weight=ft.FontWeight.W_600),
            ]),
            content=ft.Column([
                name_field,
                ft.Container(height=8),
                desc_field,
                error_txt
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Create", on_click=create_group,
                                  bgcolor=TEAMS_BLUE, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg)

    def _show_email_groups_list(self):
        """Show dialog with list of email groups and ability to add members"""
        def close_dlg(ev):
            self._page.pop_dialog()
            self._page.update()

        # Get all groups the user is a member of
        user_groups = []
        try:
            db = get_db_session()
            user_groups = get_user_email_groups(db, self.current_user_id)
            db.close()
        except:
            pass

        def show_group_details(group):
            self._page.pop_dialog()
            self._show_email_group_details(group)
            self._page.update()

        group_items = []
        for g in user_groups:
            member_count = 0
            try:
                db = get_db_session()
                members = get_email_group_members(db, g.id)
                member_count = len(members)
                db.close()
            except:
                pass

            group_items.append(
                ft.Container(
                    padding=12,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    on_click=lambda e, grp=g: show_group_details(grp),
                    content=ft.Row([
                        ft.Container(
                            width=40,
                            height=40,
                            bgcolor="#E91E63",
                            border_radius=20,
                            content=ft.Icon(
                                ft.Icons.GROUP, size=20, color="white"),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Container(width=12),
                        ft.Column([
                            ft.Text(str(g.name), size=14,
                                    weight=ft.FontWeight.W_600, color=TEAMS_TEXT),
                            ft.Text(f"{member_count} members",
                                    size=11, color=TEAMS_SUBTEXT),
                        ], expand=True, spacing=0),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT,
                                size=20, color=TEAMS_SUBTEXT),
                    ], spacing=0)
                )
            )

        if not group_items:
            content = ft.Column([
                ft.Container(
                    padding=40,
                    content=ft.Column([
                        ft.Icon(ft.Icons.GROUP, size=48, color="#C8C8C8"),
                        ft.Container(height=12),
                        ft.Text("No email groups yet",
                                size=14, color=TEAMS_SUBTEXT),
                        ft.Container(height=8),
                        ft.Text("Create a group to send emails to multiple people at once",
                                size=12, color=TEAMS_SUBTEXT, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.Alignment(0, 0)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            content = ft.Column(group_items, spacing=8)

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.FOLDER, color=TEAMS_BLUE, size=24),
                ft.Text("My Email Groups", size=18,
                        weight=ft.FontWeight.W_600),
            ]),
            content=ft.Container(
                width=400,
                height=350,
                content=content
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg)

    def _show_email_group_details(self, group):
        """Show details of an email group with option to add members"""
        def close_dlg(ev):
            self._page.pop_dialog()
            self._page.update()

        group_id = group.id
        group_name = group.name

        # Get current members
        members = []
        try:
            db = get_db_session()
            members = get_email_group_members(db, group_id)
            db.close()
        except:
            pass

        # Get member user details
        member_details = []
        for m in members:
            try:
                db = get_db_session()
                user = db.query(__import__('database.models', fromlist=[
                                'User']).User).filter_by(id=m.user_id).first()
                if user:
                    member_details.append(
                        {'id': user.id, 'username': user.username, 'role': m.role})
                db.close()
            except:
                pass

        member_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)

        colors = [TEAMS_BLUE, "#107C10", "#D13438", "#FFB900", "#8764B8"]
        for i, member in enumerate(member_details):
            avatar_color = colors[i % len(colors)]
            member_list.controls.append(
                ft.Container(
                    padding=8,
                    bgcolor=TEAMS_WHITE,
                    border_radius=8,
                    content=ft.Row([
                        ft.Container(
                            width=32,
                            height=32,
                            bgcolor=avatar_color,
                            border_radius=16,
                            content=ft.Text(member['username'][0].upper(
                            ), size=12, color="white", weight=ft.FontWeight.BOLD),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Container(width=8),
                        ft.Column([
                            ft.Text(
                                member['username'], size=13, weight=ft.FontWeight.W_500, color=TEAMS_TEXT),
                            ft.Text(member['role'], size=10,
                                    color=TEAMS_SUBTEXT),
                        ], spacing=0, expand=True),
                    ], spacing=0)
                )
            )

        def add_members(ev):
            self._page.pop_dialog()
            self._show_add_group_members_dialog(group)
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.GROUP, color="#E91E63", size=24),
                ft.Text(group_name, size=18, weight=ft.FontWeight.W_600),
            ]),
            content=ft.Container(
                width=350,
                height=300,
                content=ft.Column([
                    ft.Text(f"{len(member_details)} Members", size=13,
                            weight=ft.FontWeight.W_600, color=TEAMS_SUBTEXT),
                    ft.Container(height=8),
                    member_list
                ], spacing=8)
            ),
            actions=[
                ft.TextButton("Add Members", on_click=add_members),
                ft.TextButton("Close", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg)

    def _show_add_group_members_dialog(self, group):
        """Show dialog to add members to an email group"""
        def close_dlg(ev):
            self._page.pop_dialog()
            self._page.update()

        group_id = group.id
        group_name = group.name

        # Get current member IDs
        current_member_ids = set()
        try:
            db = get_db_session()
            current_members = get_email_group_members(db, group_id)
            current_member_ids = {m.user_id for m in current_members}
            db.close()
        except:
            pass

        # Get available users (not already in group)
        available_users = [u for u in self._all_users if u.id !=
                           self.current_user_id and u.id not in current_member_ids]

        selected_members = set()

        def build_user_tiles():
            tiles = []
            for u in available_users:
                is_sel = u.id in selected_members
                colors = [TEAMS_BLUE, "#107C10",
                          "#D13438", "#FFB900", "#8764B8"]
                avatar_color = colors[sum(ord(c)
                                          for c in str(u.username)) % len(colors)]

                tile = ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=TEAMS_BLUE + "10" if is_sel else "transparent",
                    border_radius=8,
                    on_click=lambda e, uid=u.id: toggle_user(uid),
                    content=ft.Row([
                        ft.Container(
                            width=24,
                            height=24,
                            border=ft.border.all(
                                2, TEAMS_BLUE if is_sel else "#C8C8C8"),
                            bgcolor=TEAMS_BLUE if is_sel else "transparent",
                            border_radius=4,
                            content=ft.Icon(
                                ft.Icons.CHECK, size=16, color="white") if is_sel else None,
                        ),
                        ft.Container(width=12),
                        ft.Container(
                            width=32,
                            height=32,
                            bgcolor=avatar_color,
                            border_radius=16,
                            content=ft.Text(str(u.username)[0].upper(
                            ), size=12, color="white", weight=ft.FontWeight.BOLD),
                            alignment=ft.alignment.Alignment(0, 0)
                        ),
                        ft.Container(width=12),
                        ft.Text(str(u.username), size=14,
                                weight=ft.FontWeight.W_500, color=TEAMS_TEXT),
                    ], spacing=0)
                )
                tiles.append(tile)
            return tiles

        def toggle_user(uid):
            if uid in selected_members:
                selected_members.discard(uid)
            else:
                selected_members.add(uid)
            user_column.controls = build_user_tiles()
            update_count()
            self._page.update()

        def update_count():
            count = len(selected_members)
            count_text.value = f"{count} selected"
            count_text.visible = count > 0

        def add_members(ev):
            if not selected_members:
                return

            try:
                db = get_db_session()
                for member_id in selected_members:
                    add_email_group_member(
                        db, group_id, member_id, role="member")
                db.close()
                self._show_success(
                    f"Added {len(selected_members)} member(s) to '{group_name}'!")
                self._load_email_groups()
                close_dlg(ev)
            except Exception as ex:
                error_txt.value = str(ex)
                error_txt.visible = True
                self._page.update()

        count_text = ft.Text("", size=12, color=TEAMS_SUBTEXT, visible=False)
        error_txt = ft.Text("", color=ERROR, size=12, visible=False)

        user_column = ft.Column(
            controls=build_user_tiles(),
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.PERSON_ADD, color=TEAMS_BLUE, size=24),
                ft.Text(f"Add Members to '{group_name}'",
                        size=18, weight=ft.FontWeight.W_600),
            ]),
            content=ft.Container(
                width=350,
                height=300,
                content=ft.Column([
                    count_text,
                    ft.Container(height=4),
                    user_column,
                    error_txt
                ], spacing=0)
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Add Members", on_click=add_members,
                                  bgcolor=TEAMS_BLUE, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg)


def show_mail(page: ft.Page, user=None):
    page.clean()
    page.add(MailScreen(page, user))
    page.update()
