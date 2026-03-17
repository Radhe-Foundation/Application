"""
RadheFoundation HRA - Announcements Screen
PostgreSQL/SQLAlchemy based announcements management
"""

import flet as ft
from datetime import datetime
from database.session_manager import get_db_session
from database.models import Announcement


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
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = "#F5F5F5"
        self.announcements = []
        self.content = self._build_content()
        self._load_announcements()

    def _build_content(self):
        """Build the UI - No back button since this is accessed from admin panel tabs"""
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Text("Company Announcements", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Export to Excel",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=self._export_announcements,
                    style=ft.ButtonStyle(bgcolor=SUCCESS, color="WHITE")
                ),
                ft.Container(width=10),
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
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def _get_announcements(self):
        """Get all announcements from PostgreSQL"""
        db = get_db_session()
        try:
            announcements = db.query(Announcement).order_by(
                Announcement.created_at.desc()).limit(50).all()
            return announcements
        except Exception as e:
            print(f"Error loading announcements: {e}")
            return []
        finally:
            db.close()

    def _load_announcements(self):
        """Load announcements from database"""
        self.announcements = self._get_announcements()

    def _export_announcements(self, e):
        """Export announcements to Excel/CSV"""
        if not self.announcements:
            self._show_error("No announcements to export!")
            return

        import os

        # Create reports directory if not exists
        export_dir = "reports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_dir}/announcements_{timestamp}.csv"

        csv_lines = [
            "ID,Title,Type,Priority,Author,Views,Target Audience,Created Date"]
        for ann in self.announcements:
            created_date = ann.created_at.strftime(
                '%Y-%m-%d') if ann.created_at else ''
            target = ann.target_audience or 'all'
            line = f"{ann.id},\"{ann.title or ''}\",{ann.type or 'general'},{ann.priority or 'normal'},{ann.author or 'Admin'},{ann.views or 0},{target},{created_date}"
            csv_lines.append(line)

        csv_content = "\n".join(csv_lines)

        # Save to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            self._show_success(f"Exported {len(self.announcements)} announcements to {filename}")
        except Exception as ex:
            self._show_error(f"Export failed: {str(ex)}")

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

        cards = []
        for ann in self.announcements:
            priority_color = self._get_priority_color(ann.priority or 'normal')
            created_date = ann.created_at.strftime(
                '%Y-%m-%d') if ann.created_at else ''

            card = ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(ann.title or 'N/A', size=16,
                                    weight=ft.FontWeight.BOLD, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    ann.type or 'General', size=10, color="WHITE"),
                                bgcolor=priority_color,
                                padding=ft.padding.symmetric(
                                    horizontal=8, vertical=4),
                                border_radius=15,
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(ann.content or '', size=13, color="#666"),
                        ft.Divider(),
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON,
                                        size=14, color="#999"),
                                ft.Text(ann.author or 'Admin',
                                        size=11, color="#666"),
                            ], spacing=5),
                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_TODAY,
                                        size=14, color="#999"),
                                ft.Text(created_date,
                                        size=11, color="#666"),
                            ], spacing=5),
                            ft.Row([
                                ft.Icon(ft.Icons.VISIBILITY,
                                        size=14, color="#999"),
                                ft.Text(f"{ann.views or 0} views",
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

        return ft.Container(
            content=ft.Column(cards, spacing=15, scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def _get_priority_color(self, priority: str) -> str:
        """Get color for announcement priority"""
        colors_map = {
            "high": ERROR,
            "important": WARNING,
            "normal": PRIMARY,
            "low": "#9E9E9E",
        }
        return colors_map.get(priority.lower(), PRIMARY)

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

            db = get_db_session()
            try:
                new_announcement = Announcement(
                    title=title_field.value,
                    content=content_field.value,
                    type=type_dropdown.value,
                    priority=priority_dropdown.value,
                    author="Admin",
                    views=0,
                    target_audience="all"
                )
                db.add(new_announcement)
                db.commit()

                self._close_dialog()
                self._show_success("Announcement published!")
                self._load_announcements()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()
            finally:
                db.close()

        form = ft.Column([
            title_field,
            ft.Row([type_dropdown, priority_dropdown], spacing=15),
            content_field,
            error,
        ], spacing=10)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("New Announcement"),
            content=ft.Container(content=form, width=500, height=350),
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
        self._show_edit_dialog(announcement)

    def _show_edit_dialog(self, announcement):
        """Show edit announcement dialog"""
        title_field = ft.TextField(
            label="Title", width=450,
            value=announcement.title if announcement else ""
        )
        type_dropdown = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("general", "General"),
                ft.dropdown.Option("important", "Important"),
                ft.dropdown.Option("event", "Event"),
                ft.dropdown.Option("policy", "Policy"),
            ],
            value=announcement.type if announcement else "general",
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
            value=announcement.priority if announcement else "normal",
            label="Priority"
        )
        content_field = ft.TextField(
            label="Content", width=450, multiline=True, min_lines=4,
            value=announcement.content if announcement else ""
        )

        def update(e):
            db = get_db_session()
            try:
                db.query(Announcement).filter(Announcement.id == announcement.id).update({
                    Announcement.title: title_field.value,
                    Announcement.content: content_field.value,
                    Announcement.type: type_dropdown.value,
                    Announcement.priority: priority_dropdown.value
                })
                db.commit()

                self._close_dialog()
                self._show_success("Announcement updated!")
                self._load_announcements()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

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
            db = get_db_session()
            try:
                db.query(Announcement).filter(
                    Announcement.id == announcement.id).delete()
                db.commit()

                self._close_dialog()
                self._show_success("Announcement deleted!")
                self._load_announcements()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Announcement?", color=ERROR),
            content=ft.Text(f"Delete '{announcement.title}'?"),
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
