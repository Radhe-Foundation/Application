"""
Vernika HRA - Announcements Screen
Company announcements management
"""

import flet as ft
import sqlite3
from datetime import datetime


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"


class AnnouncementsScreen(ft.Container):
    """
    Screen for managing company announcements.
    """

    def __init__(self, page, user=None):
        """
        Initialize announcements screen.

        Args:
            page: Flet page object
            user: Current user object (optional)
        """
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = "#F5F5F5"
        self.announcements = []
        self.content = self._build_content()
        self._load_announcements()

    def _get_db(self):
        """Get database connection"""
        conn = sqlite3.connect('vernika.db')
        conn.row_factory = sqlite3.Row
        return conn

    def _build_content(self):
        """Build the UI"""
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self._on_back
                ),
                ft.Text("Company Announcements", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "New Announcement",
                    icon=ft.Icons.ADD,
                    on_click=self._show_create_dialog,
                    style=ft.ButtonStyle(bgcolor="#1976D2", color="WHITE")
                ),
            ])
        )

        return ft.Column([
            header,
            ft.Container(
                padding=20,
                content=self._build_announcements_list(),
                expand=True
            ),
        ], expand=True)

    def _on_back(self, e):
        """Go back to dashboard"""
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def _build_announcements_list(self):
        """Build announcements list"""
        if not self.announcements:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CAMPAIGN, size=64, color="#BDBDBD"),
                    ft.Text("No announcements yet", size=14, color="#757575"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Create First Announcement",
                        on_click=self._show_create_dialog,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        # Build cards for each announcement
        cards = []
        for ann in self.announcements:
            priority_color = self._get_priority_color(
                ann.get('priority', 'normal'))

            card = ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(ann.get('title', 'N/A'), size=16,
                                    weight=ft.FontWeight.BOLD, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    ann.get('type', 'General'), size=10, color="WHITE"),
                                bgcolor=priority_color,
                                padding=ft.padding.symmetric(
                                    horizontal=8, vertical=4),
                                border_radius=15,
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(ann.get('content', ''), size=13, color="#666"),
                        ft.Divider(),
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON,
                                        size=14, color="#999"),
                                ft.Text(ann.get('author', 'Admin'),
                                        size=11, color="#666"),
                            ], spacing=5),
                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_TODAY,
                                        size=14, color="#999"),
                                ft.Text(ann.get('date', ''),
                                        size=11, color="#666"),
                            ], spacing=5),
                            ft.Row([
                                ft.Icon(ft.Icons.VISIBILITY,
                                        size=14, color="#999"),
                                ft.Text(f"{ann.get('views', 0)} views",
                                        size=11, color="#666"),
                            ], spacing=5),
                        ], spacing=20),
                        ft.Container(height=10),
                        ft.Row([
                            ft.ElevatedButton(
                                "Edit", icon=ft.Icons.EDIT, height=32,
                                on_click=lambda e, a=ann: self._edit_announcement(
                                    a),
                                style=ft.ButtonStyle(
                                    bgcolor="#1976D2", color="WHITE")
                            ),
                            ft.ElevatedButton(
                                "Delete", icon=ft.Icons.DELETE, height=32,
                                on_click=lambda e, a=ann: self._confirm_delete(
                                    a),
                                style=ft.ButtonStyle(
                                    bgcolor=ERROR, color="WHITE")
                            ),
                        ], spacing=10),
                    ], spacing=5)
                )
            )
            cards.append(card)

        return ft.Column(cards, spacing=15, scroll=ft.ScrollMode.AUTO)

    def _get_priority_color(self, priority: str) -> str:
        """Get color for announcement priority"""
        colors_map = {
            "high": ERROR,
            "important": WARNING,
            "normal": PRIMARY,
            "low": "#9E9E9E",
        }
        return colors_map.get(priority.lower(), PRIMARY)

    def _load_announcements(self):
        """Load announcements from database or use defaults"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, content, type, priority, author, created_at as date, views
                FROM announcements ORDER BY created_at DESC LIMIT 50
            """)
            results = cursor.fetchall()
            conn.close()

            if results:
                self.announcements = [dict(r) for r in results]
                return
        except Exception as e:
            print(f"Error loading announcements: {e}")

        # Default sample announcements
        self.announcements = [
            {
                "id": 1,
                "title": "Office Closure - Holiday Notice",
                "content": "The office will be closed on Friday for a company-wide holiday.",
                "type": "important",
                "priority": "high",
                "author": "Admin",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "views": 45,
            },
            {
                "id": 2,
                "title": "New Health Insurance Plan",
                "content": "We are pleased to announce an improved health insurance plan.",
                "type": "policy",
                "priority": "important",
                "author": "HR Manager",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "views": 78,
            },
        ]

    def _show_create_dialog(self, e=None):
        """Show create announcement dialog"""
        title_field = ft.TextField(label="Title", width=450)

        type_dropdown = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("general", "General"),
                ft.dropdown.Option("important", "Important"),
                ft.dropdown.Option("event", "Event"),
                ft.dropdown.Option("policy", "Policy"),
            ],
            value="general",
            label="Type"
        )

        priority_dropdown = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("low", "Low"),
                ft.dropdown.Option("normal", "Normal"),
                ft.dropdown.Option("important", "Important"),
                ft.dropdown.Option("high", "High"),
            ],
            value="normal",
            label="Priority"
        )

        content_field = ft.TextField(
            label="Content", width=450, multiline=True, min_lines=4
        )

        error = ft.Text("", color=ERROR, size=12, visible=False)

        def save(e):
            if not title_field.value or not content_field.value:
                error.value = "Title and Content are required!"
                error.visible = True
                self._page.update()
                return

            try:
                conn = self._get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO announcements (title, content, type, priority, author, created_at, views)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (title_field.value, content_field.value,
                      type_dropdown.value, priority_dropdown.value,
                      "Admin", datetime.now().strftime('%Y-%m-%d')))
                conn.commit()
                conn.close()

                self._close_dialog()
                self._show_success("Announcement published!")
                self._load_announcements()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()

        form = ft.Column([
            title_field,
            ft.Row([type_dropdown, priority_dropdown], spacing=15),
            content_field,
            error,
        ], spacing=10)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("New Announcement"),
            content=ft.Container(content=form, width=500, height=300),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Publish", on_click=save,
                                  style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE"))
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _edit_announcement(self, announcement):
        """Edit announcement"""
        self._show_announcement_form(announcement)

    def _show_announcement_form(self, announcement=None):
        """Show announcement form dialog"""
        title_field = ft.TextField(
            label="Title", width=450,
            value=announcement.get('title') if announcement else ""
        )

        type_dropdown = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("general", "General"),
                ft.dropdown.Option("important", "Important"),
                ft.dropdown.Option("event", "Event"),
                ft.dropdown.Option("policy", "Policy"),
            ],
            value=announcement.get('type') if announcement else "general",
            label="Type"
        )

        priority_dropdown = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("low", "Low"),
                ft.dropdown.Option("normal", "Normal"),
                ft.dropdown.Option("important", "Important"),
                ft.dropdown.Option("high", "High"),
            ],
            value=announcement.get('priority') if announcement else "normal",
            label="Priority"
        )

        content_field = ft.TextField(
            label="Content", width=450, multiline=True, min_lines=4,
            value=announcement.get('content') if announcement else ""
        )

        def update(e):
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE announcements SET title=?, content=?, type=?, priority=?
                WHERE id=?
            """, (title_field.value, content_field.value,
                  type_dropdown.value, priority_dropdown.value,
                  announcement['id']))
            conn.commit()
            conn.close()

            self._close_dialog()
            self._show_success("Announcement updated!")
            self._load_announcements()
            self.content = self._build_content()
            self._page.update()

        form = ft.Column([
            title_field,
            ft.Row([type_dropdown, priority_dropdown], spacing=15),
            content_field,
        ], spacing=10)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Announcement"),
            content=ft.Container(content=form, width=500, height=300),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Update", on_click=update,
                                  style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE"))
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _confirm_delete(self, announcement):
        """Show delete confirmation"""
        def confirm(e):
            try:
                conn = self._get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM announcements WHERE id=?", (announcement['id'],))
                conn.commit()
                conn.close()

                self._close_dialog()
                self._show_success("Announcement deleted!")
                self._load_announcements()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(str(ex))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Announcement?", color=ERROR),
            content=ft.Text(f"Delete '{announcement.get('title', '')}'?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm,
                                  style=ft.ButtonStyle(bgcolor=ERROR, color="WHITE"))
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self):
        """Close all open dialogs"""
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _show_success(self, msg):
        """Show success message"""
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        """Show error message"""
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=ERROR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_announcements(page, user=None):
    """Helper function to show announcements screen"""
    page.clean()
    page.add(AnnouncementsScreen(page, user))
