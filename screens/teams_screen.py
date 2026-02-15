"""
Vernika HRA - Teams Management Screen
PostgreSQL/SQLAlchemy based teams management
"""

import flet as ft
from sqlalchemy.orm import Session
from database.connection import get_db_session
from database.models import Team


# Theme colors
PRIMARY = "#7B1FA2"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"
BACKGROUND = "#F5F5F5"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"


class TeamsScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.content = self._build_content()

    def _build_content(self):
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self.on_back
                ),
                ft.Text("Teams Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Create Team",
                    icon=ft.Icons.ADD,
                    on_click=self.on_create,
                    style=ft.ButtonStyle(bgcolor="#9C27B0", color="WHITE")
                ),
            ])
        )

        teams_list = self._build_teams_list()

        content = ft.Column([
            header,
            ft.Container(
                padding=20,
                content=teams_list,
                expand=True
            )
        ], expand=True)

        return content

    def on_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def on_create(self, e):
        self._show_create_dialog()

    def _get_teams(self):
        """Get all teams from PostgreSQL"""
        db = get_db_session()
        try:
            teams = db.query(Team).order_by(Team.name).all()
            return teams
        except Exception as e:
            print(f"Error loading teams: {e}")
            return []
        finally:
            db.close()

    def _build_teams_list(self):
        """Build teams list"""
        teams = self._get_teams()

        if not teams:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.GROUPS, size=64, color="#BDBDBD"),
                    ft.Text("No teams created yet.", size=14, color="#757575"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Create First Team",
                        on_click=self.on_create,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        rows = []
        for team in teams:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(team.id))),
                        ft.DataCell(ft.Text(team.name or "")),
                        ft.DataCell(ft.Text(team.description or "-")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color="#1976D2",
                                    on_click=lambda e, team_id=team.id: self._show_edit_dialog(
                                        team_id),
                                    tooltip="Edit"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color="#D32F2F",
                                    on_click=lambda e, team_id=team.id: self._show_delete_dialog(
                                        team_id),
                                    tooltip="Delete"
                                ),
                            ], spacing=2)
                        ),
                    ]
                )
            )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(label=ft.Text("ID")),
                ft.DataColumn(label=ft.Text("Team Name")),
                ft.DataColumn(label=ft.Text("Description")),
                ft.DataColumn(label=ft.Text("Actions")),
            ],
            rows=rows,
            expand=True,
        )

        return ft.Container(content=table, expand=True)

    def _show_create_dialog(self):
        """Show create team dialog"""
        name = ft.TextField(label="Team Name *", width=300)
        description = ft.TextField(
            label="Description", width=400, multiline=True)
        error = ft.Text("", color="#F44336", size=12, visible=False)

        def save(e):
            if not name.value:
                error.value = "Team name is required!"
                error.visible = True
                self._page.update()
                return

            db = get_db_session()
            try:
                # Check if team name exists
                existing = db.query(Team).filter(
                    Team.name == name.value).first()
                if existing:
                    error.value = "Team name already exists!"
                    error.visible = True
                    self._page.update()
                    return

                # Create new team
                new_team = Team(
                    name=name.value,
                    description=description.value or None
                )
                db.add(new_team)
                db.commit()

                self._close_dialog()
                self._show_success("Team created successfully!")
                self._refresh()
            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create Team"),
            content=ft.Column([name, description, error],
                              spacing=10, tight=True),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Create", on_click=save, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="WHITE"))
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_edit_dialog(self, team_id):
        """Show edit team dialog"""
        db = get_db_session()
        try:
            team = db.query(Team).filter(Team.id == team_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not team:
            self._show_error("Team not found!")
            return

        name = ft.TextField(label="Team Name *", width=300,
                            value=team.name or "")
        description = ft.TextField(label="Description", width=400, multiline=True,
                                   value=team.description or "")

        def update(e):
            db = get_db_session()
            try:
                db.query(Team).filter(Team.id == team_id).update({
                    Team.name: name.value,
                    Team.description: description.value or None
                })
                db.commit()

                self._close_dialog()
                self._show_success("Team updated successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Team"),
            content=ft.Column([name, description], spacing=10, tight=True),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Update", on_click=update, style=ft.ButtonStyle(
                    bgcolor="#1976D2", color="WHITE"))
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_delete_dialog(self, team_id):
        """Show delete confirmation dialog"""
        db = get_db_session()
        try:
            team = db.query(Team).filter(Team.id == team_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not team:
            self._show_error("Team not found!")
            return

        def confirm(e):
            db = get_db_session()
            try:
                db.query(Team).filter(Team.id == team_id).delete()
                db.commit()

                self._close_dialog()
                self._show_success("Team deleted!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Team?", color="#F44336"),
            content=ft.Text(f"Delete '{team.name}'?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm, style=ft.ButtonStyle(
                    bgcolor="#F44336", color="WHITE"))
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self):
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _refresh(self):
        self.content = self._build_content()
        self._page.update()

    def _show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#4CAF50")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#F44336")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_teams(page, user):
    """Helper function to show teams screen"""
    page.clean()
    page.add(TeamsScreen(page, user))
