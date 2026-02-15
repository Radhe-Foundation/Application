"""
Vernika HRA - Internal Mail Screen
Industry-Level Human Resource Management System

This module provides the internal email/mail system for the organization.
Features:
- Compose and send internal emails
- Inbox, Sent, Drafts folders
- Reply and Forward functionality
- Search emails
- Announcement system
- Offer letter and official document sharing
- Document attachment support
"""

import flet as ft
from datetime import datetime
from typing import List, Optional
from database.connection import get_db_session
from database.models import (
    User, Employee, EmailMessage, EmailRecipient,
    EmailCategory, Document
)
from database.operations import (
    send_email, get_user_emails, get_email_by_id,
    mark_email_as_read, delete_email, get_unread_email_count,
    get_all_users, upload_document
)


# Theme colors
PRIMARY = "#2E86AB"
SECONDARY = "#A23B72"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"
INFO = "#2196F3"
BACKGROUND = "#F5F5F5"
SURFACE = "#FFFFFF"


class MailScreen(ft.Container):
    """
    Internal Mail Screen with compose, inbox, sent, drafts,
    announcement, and document sharing capabilities.
    """

    def __init__(self, page: ft.Page, user=None):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND

        # Get current user info
        self.current_user_id = None
        self.current_username = "User"
        if isinstance(user, dict):
            self.current_user_id = user.get('id')
            self.current_username = user.get('username', 'User')
        elif hasattr(user, 'id'):
            self.current_user_id = user.id
            self.current_username = getattr(user, 'username', 'User')

        # State
        self.current_folder = "inbox"
        self.emails = []
        self.draft_content = {}
        self.search_query = ""
        self.reply_to_email = None
        self.forward_email = None

        # Build UI
        self.content = self._build_content()

        # Load emails
        self._load_emails()

    def _build_content(self):
        """Build the main content"""
        return ft.Container(
            content=ft.Row([
                # Sidebar with folders
                self._build_sidebar(),
                ft.VerticalDivider(width=1, color="#E0E0E0"),
                # Main content area
                self._build_main_content(),
            ], expand=True),
            expand=True,
        )

    def _build_sidebar(self):
        """Build sidebar with folder navigation"""
        def create_folder_item(icon, label, folder, count=None):
            is_selected = self.current_folder == folder

            def handle_click(e):
                self.current_folder = folder
                self.content = self._build_content()
                self._load_emails()
                self._page.update()

            return ft.Container(
                on_click=handle_click,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=PRIMARY if is_selected else "transparent",
                border_radius=8,
                content=ft.Row([
                    ft.Icon(icon, size=20,
                            color="WHITE" if is_selected else "#666"),
                    ft.Text(label, size=14, color="WHITE" if is_selected else "#333",
                            weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL),
                    ft.Container(expand=True),
                    ft.Text(str(count), size=12,
                            color="WHITE" if is_selected else "#666")
                    if count is not None else ft.Container(),
                ]),
            )

        # Get unread counts
        unread_inbox = 0
        try:
            db = get_db_session()
            unread_inbox = get_unread_email_count(db, self.current_user_id)
            db.close()
        except:
            pass

        return ft.Container(
            width=220,
            bgcolor=SURFACE,
            padding=ft.padding.all(10),
            content=ft.Column([
                ft.Container(
                    padding=ft.padding.all(10),
                    content=ft.Row([
                        ft.Icon(ft.Icons.EMAIL, color=PRIMARY, size=28),
                        ft.Text("Internal Mail", size=18,
                                weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ]),
                ),
                ft.Divider(),
                ft.Container(height=5),
                create_folder_item(ft.Icons.INBOX_OUTLINED, "Inbox",
                                   "inbox", unread_inbox),
                create_folder_item(ft.Icons.SEND_OUTLINED, "Sent", "sent"),
                create_folder_item(ft.Icons.DRAFTS_OUTLINED,
                                   "Drafts", "drafts"),
                ft.Divider(),
                ft.Container(height=5),
                ft.Text("Compose & Share", size=12, color="#999",
                        weight=ft.FontWeight.W_500),
                create_folder_item(ft.Icons.EDIT_OUTLINED,
                                   "Compose", "compose"),
                create_folder_item(ft.Icons.CAMPAIGN,
                                   "Announcements", "announcement"),
                create_folder_item(ft.Icons.DESCRIPTION,
                                   "Offer Letters", "offer_letter"),
                create_folder_item(ft.Icons.FOLDER_OPEN,
                                   "Documents", "documents"),
            ], spacing=2),
        )

    def _build_main_content(self):
        """Build main content area"""
        if self.current_folder == "compose":
            return self._build_compose_view()
        elif self.current_folder == "reply":
            return self._build_compose_view(is_reply=True)
        elif self.current_folder == "forward":
            return self._build_compose_view(is_forward=True)
        elif self.current_folder == "announcement":
            return self._build_announcement_view()
        elif self.current_folder == "offer_letter":
            return self._build_offer_letter_view()
        elif self.current_folder in ["inbox", "sent", "drafts"]:
            return self._build_email_list_view()
        else:
            return self._build_email_list_view()

    def _build_compose_view(self):
        """Build compose email view"""
        # Get all users for recipients
        all_users = []
        try:
            db = get_db_session()
            all_users = get_all_users(db)
            db.close()
        except:
            pass

        user_options = [ft.dropdown.Option(str(u.id), f"{u.username} ({u.email})")
                        for u in all_users if u.id != self.current_user_id]

        to_field = ft.Dropdown(
            label="To *",
            width=400,
            options=user_options,
        )

        cc_field = ft.Dropdown(
            label="CC",
            width=400,
            options=user_options,
        )

        subject_field = ft.TextField(
            label="Subject *",
            width=500,
        )

        body_field = ft.TextField(
            label="Message",
            width=500,
            min_lines=10,
            multiline=True,
        )

        # Category dropdown
        category_options = [
            ft.dropdown.Option("general", "General"),
            ft.dropdown.Option("hr_communication", "HR Communication"),
            ft.dropdown.Option("meeting_request", "Meeting Request"),
            ft.dropdown.Option("announcement", "Announcement"),
        ]
        category_dropdown = ft.Dropdown(
            label="Category",
            width=200,
            options=category_options,
            value="general",
        )

        error_text = ft.Text("", color=ERROR, size=12, visible=False)

        def send_email_handler(e):
            if not to_field.value or not subject_field.value:
                error_text.value = "Please fill in required fields!"
                error_text.visible = True
                self._page.update()
                return

            try:
                db = get_db_session()
                recipient_ids = [int(to_field.value)]
                cc_ids = [int(cc_field.value)] if cc_field.value else None

                category = EmailCategory.GENERAL
                if category_dropdown.value:
                    category = EmailCategory(category_dropdown.value)

                send_email(
                    db,
                    sender_id=self.current_user_id,
                    subject=subject_field.value,
                    body=body_field.value,
                    recipient_ids=recipient_ids,
                    category=category,
                    cc_ids=cc_ids
                )
                db.close()

                self._show_success("Email sent successfully!")
                self.current_folder = "sent"
                self.content = self._build_content()
                self._load_emails()
                self._page.update()
            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self._page.update()

        def save_draft(e):
            try:
                self.draft_content = {
                    'to': to_field.value,
                    'cc': cc_field.value,
                    'subject': subject_field.value,
                    'body': body_field.value,
                    'category': category_dropdown.value,
                }
                self._show_success("Draft saved!")
            except Exception as ex:
                self._show_error(str(ex))
            self._page.update()

        return ft.Container(
            expand=True,
            padding=20,
            content=ft.Column([
                ft.Text("Compose Email", size=24,
                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Container(height=20),
                to_field,
                cc_field,
                subject_field,
                category_dropdown,
                body_field,
                error_text,
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        "Send",
                        icon=ft.Icons.SEND,
                        on_click=send_email_handler,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE"),
                    ),
                    ft.ElevatedButton(
                        "Save Draft",
                        icon=ft.Icons.DRAFTS_OUTLINED,
                        on_click=save_draft,
                        style=ft.ButtonStyle(bgcolor="#757575", color="WHITE"),
                    ),
                ]),
            ], scroll=ft.ScrollMode.AUTO),
        )

    def _build_announcement_view(self):
        """Build announcement creation view"""
        # Get all employees
        all_users = []
        try:
            db = get_db_session()
            all_users = get_all_users(db)
            db.close()
        except:
            pass

        user_options = [ft.dropdown.Option(str(u.id), f"{u.username} ({u.email})")
                        for u in all_users if u.id != self.current_user_id]

        title_field = ft.TextField(
            label="Announcement Title *",
            width=500,
        )

        content_field = ft.TextField(
            label="Announcement Content *",
            width=500,
            min_lines=8,
            multiline=True,
        )

        priority_options = [
            ft.dropdown.Option("normal", "Normal"),
            ft.dropdown.Option("important", "Important"),
            ft.dropdown.Option("high", "High Priority"),
        ]
        priority_dropdown = ft.Dropdown(
            label="Priority",
            width=200,
            options=priority_options,
            value="normal",
        )

        type_options = [
            ft.dropdown.Option("general", "General"),
            ft.dropdown.Option("event", "Event"),
            ft.dropdown.Option("policy", "Policy Update"),
            ft.dropdown.Option("meeting", "Meeting Notice"),
        ]
        type_dropdown = ft.Dropdown(
            label="Type",
            width=200,
            options=type_options,
            value="general",
        )

        error_text = ft.Text("", color=ERROR, size=12, visible=False)

        def send_announcement(e):
            if not title_field.value or not content_field.value:
                error_text.value = "Please fill in required fields!"
                error_text.visible = True
                self._page.update()
                return

            try:
                db = get_db_session()
                # Get all active users for announcement
                recipient_ids = [u.id for u in get_all_users(
                    db) if u.id != self.current_user_id]

                send_email(
                    db,
                    sender_id=self.current_user_id,
                    subject=title_field.value,
                    body=content_field.value,
                    recipient_ids=recipient_ids,
                    category=EmailCategory.ANNOUNCEMENT,
                )
                db.close()

                self._show_success("Announcement sent to all employees!")
                self.current_folder = "sent"
                self.content = self._build_content()
                self._load_emails()
                self._page.update()
            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self._page.update()

        return ft.Container(
            expand=True,
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CAMPAIGN, color=PRIMARY, size=28),
                    ft.Text("Create Announcement", size=24,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                ]),
                ft.Container(height=10),
                ft.Text("Send announcements to all employees",
                        size=14, color="#666"),
                ft.Container(height=20),
                title_field,
                ft.Row([type_dropdown, priority_dropdown], spacing=20),
                content_field,
                error_text,
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Publish Announcement",
                    icon=ft.Icons.CAMPAIGN,
                    on_click=send_announcement,
                    style=ft.ButtonStyle(bgcolor=ERROR, color="WHITE"),
                ),
            ], scroll=ft.ScrollMode.AUTO),
        )

    def _build_offer_letter_view(self):
        """Build offer letter creation view"""
        # Get all employees
        all_users = []
        try:
            db = get_db_session()
            all_users = get_all_users(db)
            db.close()
        except:
            pass

        user_options = [ft.dropdown.Option(str(u.id), f"{u.username} ({u.email})")
                        for u in all_users if u.id != self.current_user_id]

        to_field = ft.Dropdown(
            label="Send To (Employee) *",
            width=400,
            options=user_options,
        )

        position_field = ft.TextField(
            label="Position/Designation *",
            width=400,
        )

        salary_field = ft.TextField(
            label="Salary Package",
            width=200,
        )

        start_date_field = ft.TextField(
            label="Proposed Start Date",
            width=200,
            hint_text="YYYY-MM-DD",
        )

        terms_field = ft.TextField(
            label="Terms & Conditions",
            width=500,
            min_lines=6,
            multiline=True,
            value="1. Employment is subject to background verification.\n2. Notice period of 30 days applies.\n3. Company policies apply.",
        )

        error_text = ft.Text("", color=ERROR, size=12, visible=False)

        def send_offer_letter(e):
            if not to_field.value or not position_field.value:
                error_text.value = "Please fill in required fields!"
                error_text.visible = True
                self._page.update()
                return

            # Build offer letter content
            subject = f"Offer Letter - {position_field.value}"
            body = f"""
Dear Employee,

We are pleased to offer you the position of {position_field.value}.

{'Salary: ' + salary_field.value if salary_field.value else ''}
{'Proposed Start Date: ' + start_date_field.value if start_date_field.value else ''}

Terms and Conditions:
{terms_field.value}

Please sign and return the acceptance copy.

Best regards,
{self.current_username}
HR Department
            """

            try:
                db = get_db_session()
                send_email(
                    db,
                    sender_id=self.current_user_id,
                    subject=subject,
                    body=body,
                    recipient_ids=[int(to_field.value)],
                    category=EmailCategory.PROMOTION,
                )
                db.close()

                self._show_success("Offer letter sent successfully!")
                self.current_folder = "sent"
                self.content = self._build_content()
                self._load_emails()
                self._page.update()
            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self._page.update()

        return ft.Container(
            expand=True,
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.DESCRIPTION, color=PRIMARY, size=28),
                    ft.Text("Send Offer Letter", size=24,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                ]),
                ft.Container(height=10),
                ft.Text(
                    "Generate and send official offer letters to employees", size=14, color="#666"),
                ft.Container(height=20),
                to_field,
                position_field,
                ft.Row([salary_field, start_date_field], spacing=20),
                terms_field,
                error_text,
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Send Offer Letter",
                    icon=ft.Icons.SEND,
                    on_click=send_offer_letter,
                    style=ft.ButtonStyle(bgcolor=SUCCESS, color="WHITE"),
                ),
            ], scroll=ft.ScrollMode.AUTO),
        )

    def _build_email_list_view(self):
        """Build email list view for inbox/sent/drafts"""
        header_text = {
            "inbox": "Inbox",
            "sent": "Sent Messages",
            "drafts": "Drafts"
        }.get(self.current_folder, "Emails")

        # Search bar
        search_field = ft.TextField(
            hint_text="Search emails...",
            width=300,
            dense=True,
            prefix_icon=ft.Icons.SEARCH,
            value=self.search_query,
            on_change=self._handle_search,
        )

        if not self.emails:
            return ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Container(
                        padding=20,
                        content=ft.Column([
                            ft.Row([
                                ft.Text(
                                    header_text, size=24, weight=ft.FontWeight.BOLD, color=PRIMARY),
                                ft.Container(expand=True),
                                search_field,
                                ft.ElevatedButton(
                                    "Compose",
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    on_click=lambda e: self._go_to_compose(),
                                    style=ft.ButtonStyle(
                                        bgcolor=PRIMARY, color="WHITE"),
                                ),
                            ]),
                        ]),
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Icon(ft.Icons.INBOX_OUTLINED,
                                    size=64, color="#BDBDBD"),
                            ft.Text("No emails yet", size=16, color="#757575"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                ]),
            )

        # Build email cards
        email_cards = []
        for email in self.emails:
            card = self._build_email_card(email)
            email_cards.append(card)

        return ft.Container(
            expand=True,
            content=ft.Column([
                ft.Container(
                    padding=20,
                    content=ft.Row([
                        ft.Text(header_text, size=24,
                                weight=ft.FontWeight.BOLD, color=PRIMARY),
                        ft.Container(expand=True),
                        search_field,
                        ft.ElevatedButton(
                            "Compose",
                            icon=ft.Icons.EDIT_OUTLINED,
                            on_click=lambda e: self._go_to_compose(),
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="WHITE"),
                        ),
                    ]),
                ),
                ft.Column(email_cards, spacing=10, scroll=ft.ScrollMode.AUTO),
            ]),
        )

    def _build_email_card(self, email):
        """Build an email card"""
        is_unread = not getattr(email, 'is_read', False)

        # Get sender info
        sender = getattr(email, 'sender', None)
        sender_name = sender.username if sender else "Unknown"
        sender_email = sender.email if sender else ""

        # Get subject
        subject = getattr(email, 'subject', 'No Subject')

        # Get body preview
        body = getattr(email, 'body', '')
        body_preview = body[:100] + '...' if len(body) > 100 else body

        def handle_reply(e):
            self.reply_to_email = email
            self.current_folder = "reply"
            self.content = self._build_content()
            self._page.update()

        def handle_forward(e):
            self.forward_email = email
            self.current_folder = "forward"
            self.content = self._build_content()
            self._page.update()

        def handle_delete(e):
            self._delete_email(email)

        def handle_card_click(e):
            self._view_email(email.id)

        # Build card content
        card_content = ft.Container(
            padding=15,
            on_click=handle_card_click,
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(
                            sender_name,
                            size=14, weight=ft.FontWeight.BOLD if is_unread else ft.FontWeight.NORMAL,
                        ),
                        ft.Text(
                            sender_email,
                            size=11, color="#999",
                        ),
                    ], expand=True),
                    ft.Column([
                        ft.Text(
                            getattr(email, 'created_at', datetime.now()
                                    ).strftime('%Y-%m-%d %H:%M'),
                            size=11, color="#999",
                        ),
                        ft.Container(height=5),
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.REPLY,
                                icon_size=18,
                                tooltip="Reply",
                                on_click=handle_reply,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.FORWARD,
                                icon_size=18,
                                tooltip="Forward",
                                on_click=handle_forward,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=18,
                                tooltip="Delete",
                                icon_color=ERROR,
                                on_click=handle_delete,
                            ),
                        ], spacing=0),
                    ]),
                ]),
                ft.Text(
                    subject,
                    size=14, weight=ft.FontWeight.BOLD if is_unread else ft.FontWeight.NORMAL,
                ),
                ft.Text(
                    body_preview,
                    size=12, color="#666",
                ),
            ]),
        )

        return ft.Card(
            content=card_content,
            elevation=1 if is_unread else 0,
        )

    def _go_to_compose(self):
        """Go to compose view"""
        self.current_folder = "compose"
        self.content = self._build_content()
        self._page.update()

    def _handle_search(self, e):
        """Handle search input"""
        self.search_query = e.control.value.lower()
        self._load_emails()
        self._refresh_email_list()

    def _refresh_email_list(self):
        """Refresh email list"""
        if self.emails and self.search_query:
            # Filter emails by search query
            filtered = []
            for email in self.emails:
                subject = getattr(email, 'subject', '').lower()
                body = getattr(email, 'body', '').lower()
                sender = getattr(getattr(email, 'sender', None), 'username', '').lower(
                ) if hasattr(email, 'sender') else ''
                if self.search_query in subject or self.search_query in body or self.search_query in sender:
                    filtered.append(email)
            self.emails = filtered
        self.content = self._build_content()
        self._page.update()

    def _load_emails(self):
        """Load emails for current folder"""
        self.emails = []
        try:
            db = get_db_session()
            self.emails = get_user_emails(
                db, self.current_user_id, self.current_folder)
            db.close()
        except Exception as e:
            print(f"Error loading emails: {e}")

    def _view_email(self, email_id):
        """View email details"""
        try:
            db = get_db_session()
            email = get_email_by_id(db, email_id)

            # Mark as read
            if email and not email.is_read:
                mark_email_as_read(db, email_id, self.current_user_id)

            db.close()

            # Show email detail
            if email:
                self._show_email_detail(email)
        except Exception as e:
            print(f"Error viewing email: {e}")

    def _delete_email(self, email):
        """Delete an email"""
        try:
            db = get_db_session()
            delete_email(db, email.id)
            db.close()
            self._show_success("Email deleted!")
            self._load_emails()
            self.content = self._build_content()
            self._page.update()
        except Exception as e:
            self._show_error(f"Error deleting email: {e}")

    def _show_email_detail(self, email):
        """Show email in detail dialog"""
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        detail_content = ft.Container(
            width=500,
            content=ft.Column([
                ft.Text(getattr(email, 'subject', 'No Subject'),
                        size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    ft.Text("From: ", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        getattr(email, 'sender', None).username if hasattr(
                            email, 'sender') else "Unknown",
                        size=12,
                    ),
                ]),
                ft.Row([
                    ft.Text("Date: ", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        getattr(email, 'created_at', datetime.now()
                                ).strftime('%Y-%m-%d %H:%M'),
                        size=12,
                    ),
                ]),
                ft.Divider(),
                ft.Text(getattr(email, 'body', ''), size=14),
            ], scroll=ft.ScrollMode.AUTO),
            height=400,
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Email"),
            content=detail_content,
            actions=[
                ft.TextButton("Close", on_click=close_dlg),
            ],
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

        # Reload emails to reflect read status
        self._load_emails()
        self.content = self._build_content()
        self._page.update()

    def _show_success(self, message):
        """Show success message"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True

    def _show_error(self, message):
        """Show error message"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=ERROR)
        self._page.overlay.append(snack)
        snack.open = True


def show_mail(page: ft.Page, user=None):
    """Helper function to show mail screen"""
    page.clean()
    page.add(MailScreen(page, user))
    page.update()
