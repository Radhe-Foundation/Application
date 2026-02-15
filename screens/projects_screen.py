"""
Vernika HRA - Projects Management Screen
PostgreSQL/SQLAlchemy based projects management
"""

import flet as ft
from datetime import datetime
from database.connection import get_db_session
from database.models import Project


# Theme colors
PRIMARY = "#E65100"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"
BACKGROUND = "#F5F5F5"
SURFACE = "#FFFFFF"


class ProjectsScreen(ft.Container):
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
                ft.Text("Projects Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Create Project",
                    icon=ft.Icons.ADD,
                    on_click=self.on_create,
                    style=ft.ButtonStyle(bgcolor="#FF6D00", color="WHITE")
                ),
            ])
        )

        projects_list = self._build_projects_list()

        content = ft.Column([
            header,
            ft.Container(
                padding=20,
                content=projects_list,
                expand=True
            )
        ], expand=True)

        return content

    def on_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def on_create(self, e):
        self._show_create_dialog()

    def _get_projects(self):
        """Get all projects from PostgreSQL"""
        db = get_db_session()
        try:
            projects = db.query(Project).order_by(
                Project.created_at.desc()).all()
            return projects
        except Exception as e:
            print(f"Error loading projects: {e}")
            return []
        finally:
            db.close()

    def _build_projects_list(self):
        """Build projects list"""
        projects = self._get_projects()

        if not projects:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FOLDER_SPECIAL, size=64, color="#BDBDBD"),
                    ft.Text("No projects created yet.",
                            size=14, color="#757575"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Create First Project",
                        on_click=self.on_create,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        rows = []
        for project in projects:
            status_colors = {
                "planning": "#FF9800",
                "active": "#4CAF50",
                "on_hold": "#FFC107",
                "completed": "#2196F3",
                "cancelled": "#F44336"
            }
            status = project.status or "planning"
            color = status_colors.get(status, "#9E9E9E")

            start_date_str = project.start_date.strftime(
                '%Y-%m-%d') if project.start_date else "-"
            end_date_str = project.end_date.strftime(
                '%Y-%m-%d') if project.end_date else "-"

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(project.id))),
                        ft.DataCell(ft.Text(project.name or "")),
                        ft.DataCell(ft.Text(project.client_name or "-")),
                        ft.DataCell(ft.Text(start_date_str)),
                        ft.DataCell(ft.Text(end_date_str)),
                        ft.DataCell(
                            ft.Container(
                                ft.Text(status.replace("_", " ").title(),
                                        size=11, color="WHITE"),
                                bgcolor=color, padding=5, border_radius=4
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color="#1976D2",
                                    on_click=lambda e, proj_id=project.id: self._show_edit_dialog(
                                        proj_id),
                                    tooltip="Edit"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color="#D32F2F",
                                    on_click=lambda e, proj_id=project.id: self._show_delete_dialog(
                                        proj_id),
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
                ft.DataColumn(label=ft.Text("Project Name")),
                ft.DataColumn(label=ft.Text("Client")),
                ft.DataColumn(label=ft.Text("Start")),
                ft.DataColumn(label=ft.Text("End")),
                ft.DataColumn(label=ft.Text("Status")),
                ft.DataColumn(label=ft.Text("Actions")),
            ],
            rows=rows,
            expand=True,
        )

        return ft.Container(content=table, expand=True)

    def _show_create_dialog(self):
        """Show create project dialog"""
        name = ft.TextField(label="Project Name *", width=300)
        description = ft.TextField(
            label="Description", width=400, multiline=True)
        client_name = ft.TextField(label="Client Name", width=300)
        start_date = ft.TextField(label="Start Date (YYYY-MM-DD)", width=200)
        end_date = ft.TextField(label="End Date (YYYY-MM-DD)", width=200)
        budget = ft.TextField(label="Budget (Rs.)", width=150, value="0")

        status_options = [
            ft.dropdown.Option("planning", "Planning"),
            ft.dropdown.Option("active", "Active"),
            ft.dropdown.Option("on_hold", "On Hold"),
            ft.dropdown.Option("completed", "Completed"),
            ft.dropdown.Option("cancelled", "Cancelled"),
        ]
        status = ft.Dropdown(width=150, options=status_options,
                             label="Status", value="planning")

        error = ft.Text("", color="#F44336", size=12, visible=False)

        def save(e):
            if not name.value:
                error.value = "Project name is required!"
                error.visible = True
                self._page.update()
                return

            db = get_db_session()
            try:
                budget_val = 0
                try:
                    budget_val = float(budget.value) if budget.value else 0
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid budget value: {e}")

                # Parse dates
                start_date_val = None
                end_date_val = None
                try:
                    if start_date.value:
                        start_date_val = datetime.strptime(
                            start_date.value, '%Y-%m-%d').date()
                except ValueError:
                    pass
                try:
                    if end_date.value:
                        end_date_val = datetime.strptime(
                            end_date.value, '%Y-%m-%d').date()
                except ValueError:
                    pass

                # Create new project
                new_project = Project(
                    name=name.value,
                    description=description.value or None,
                    client_name=client_name.value or None,
                    start_date=start_date_val,
                    end_date=end_date_val,
                    budget=budget_val,
                    status=status.value or "planning"
                )
                db.add(new_project)
                db.commit()

                self._close_dialog()
                self._show_success("Project created successfully!")
                self._refresh()
            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create Project"),
            content=ft.Column([
                name, description, client_name,
                ft.Row([start_date, end_date], spacing=10),
                ft.Row([budget, status], spacing=10),
                error
            ], spacing=10, tight=True),
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

    def _show_edit_dialog(self, project_id):
        """Show edit project dialog"""
        db = get_db_session()
        try:
            project = db.query(Project).filter(
                Project.id == project_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not project:
            self._show_error("Project not found!")
            return

        name = ft.TextField(label="Project Name *",
                            width=300, value=project.name or "")
        description = ft.TextField(label="Description", width=400, multiline=True,
                                   value=project.description or "")
        client_name = ft.TextField(
            label="Client Name", width=300, value=project.client_name or "")
        start_date = ft.TextField(label="Start Date", width=200,
                                  value=project.start_date.strftime('%Y-%m-%d') if project.start_date else "")
        end_date = ft.TextField(label="End Date", width=200,
                                value=project.end_date.strftime('%Y-%m-%d') if project.end_date else "")
        budget = ft.TextField(label="Budget (Rs.)", width=150,
                              value=str(project.budget or 0))

        status_options = [
            ft.dropdown.Option("planning", "Planning"),
            ft.dropdown.Option("active", "Active"),
            ft.dropdown.Option("on_hold", "On Hold"),
            ft.dropdown.Option("completed", "Completed"),
            ft.dropdown.Option("cancelled", "Cancelled"),
        ]
        status = ft.Dropdown(width=150, options=status_options, label="Status",
                             value=project.status or "planning")

        def update(e):
            db = get_db_session()
            try:
                budget_val = 0
                try:
                    budget_val = float(budget.value) if budget.value else 0
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid budget value: {e}")

                # Parse dates
                start_date_val = None
                end_date_val = None
                try:
                    if start_date.value:
                        start_date_val = datetime.strptime(
                            start_date.value, '%Y-%m-%d').date()
                except ValueError:
                    pass
                try:
                    if end_date.value:
                        end_date_val = datetime.strptime(
                            end_date.value, '%Y-%m-%d').date()
                except ValueError:
                    pass

                db.query(Project).filter(Project.id == project_id).update({
                    Project.name: name.value,
                    Project.description: description.value or None,
                    Project.client_name: client_name.value or None,
                    Project.start_date: start_date_val,
                    Project.end_date: end_date_val,
                    Project.budget: budget_val,
                    Project.status: status.value
                })
                db.commit()

                self._close_dialog()
                self._show_success("Project updated successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Project"),
            content=ft.Column([
                name, description, client_name,
                ft.Row([start_date, end_date], spacing=10),
                ft.Row([budget, status], spacing=10),
            ], spacing=10, tight=True),
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

    def _show_delete_dialog(self, project_id):
        """Show delete confirmation dialog"""
        db = get_db_session()
        try:
            project = db.query(Project).filter(
                Project.id == project_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not project:
            self._show_error("Project not found!")
            return

        def confirm(e):
            db = get_db_session()
            try:
                db.query(Project).filter(Project.id == project_id).delete()
                db.commit()

                self._close_dialog()
                self._show_success("Project deleted!")
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Project?", color="#F44336"),
            content=ft.Text(f"Delete '{project.name}'?"),
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


def show_projects(page, user):
    """Helper function to show projects screen"""
    page.clean()
    page.add(ProjectsScreen(page, user))
