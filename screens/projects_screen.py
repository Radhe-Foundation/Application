"""
Vernika HRA - Projects Management Screen
Enhanced with employee members, roles, task assignment, and budget tracking
"""

import flet as ft
from datetime import datetime
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Project, ProjectMember, Employee
from sqlalchemy.orm import joinedload


# Theme colors
PRIMARY = "#E65100"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"
BACKGROUND = "#F5F5F5"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"


def _safe_navigate_to_home(page, user=None):
    """Safely navigate to home screen"""
    try:
        from core.navigation import navigate_to_home
        navigate_to_home(page, user)
    except ImportError:
        try:
            from screens.admin_screen import AdminScreen
            from screens.employee_screen import EmployeeScreen
            page.clean()
            if user and isinstance(user, dict):
                role = user.get('role', 'employee').lower()
            elif user and hasattr(user, 'role'):
                role = user.role.name.lower() if user.role else 'employee'
            else:
                role = 'employee'
            if role == 'admin':
                page.add(AdminScreen(page, user))
            else:
                page.add(EmployeeScreen(page, user))
        except Exception as e:
            print(f"Navigation error: {e}")
            from screens.login_screen import LoginScreen
            page.clean()
            page.add(LoginScreen(page))


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
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)

    def on_create(self, e):
        self._show_create_dialog()

    def _get_projects(self):
        """Get all projects from database"""
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

    def _get_project_members(self, project_id):
        """Get project members with details"""
        db = get_db_session()
        try:
            members = db.query(ProjectMember).options(
                joinedload(ProjectMember.employee)
            ).filter(ProjectMember.project_id == project_id).all()
            return members
        except Exception as e:
            print(f"Error loading project members: {e}")
            return []
        finally:
            db.close()

    def _get_all_employees(self):
        """Get all active employees"""
        db = get_db_session()
        try:
            employees = db.query(Employee).filter(
                Employee.is_active == True
            ).order_by(Employee.first_name).all()
            return employees
        except Exception as e:
            print(f"Error loading employees: {e}")
            return []
        finally:
            db.close()

    def _build_projects_list(self):
        """Build projects list with member counts"""
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

            # Get member count
            member_count = 0
            try:
                db = get_db_session()
                member_count = db.query(ProjectMember).filter(
                    ProjectMember.project_id == project.id,
                    ProjectMember.is_active == True
                ).count()
                db.close()
            except Exception:
                pass

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
                        ft.DataCell(ft.Container(
                            content=ft.Text(
                                f"{member_count} members", size=12),
                            bgcolor=PRIMARY if member_count > 0 else "#9E9E9E",
                            padding=5,
                            border_radius=4,
                        )),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.GROUP_ADD,
                                    icon_color=SUCCESS,
                                    on_click=lambda e, proj_id=project.id: self._manage_members_dialog(
                                        proj_id),
                                    tooltip="Manage Team"
                                ),
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
                ft.DataColumn(label=ft.Text("Team")),
                ft.DataColumn(label=ft.Text("Actions")),
            ],
            rows=rows,
            expand=True,
        )

        return ft.Container(content=table, expand=True)

    def _manage_members_dialog(self, project_id):
        """Show dialog to manage project members"""
        db = get_db_session()
        try:
            project = db.query(Project).filter(
                Project.id == project_id).first()
            members = db.query(ProjectMember).options(
                joinedload(ProjectMember.employee)
            ).filter(ProjectMember.project_id == project_id).all()
            employees = db.query(Employee).filter(
                Employee.is_active == True).all()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not project:
            self._show_error("Project not found!")
            return

        # Employee options
        emp_options = []
        for emp in employees:
            name = f"{emp.first_name} {emp.last_name}"
            emp_options.append(ft.dropdown.Option(str(emp.id), name))

        # Role options
        role_options = [
            ft.dropdown.Option("project_manager", "Project Manager"),
            ft.dropdown.Option("team_lead", "Team Lead"),
            ft.dropdown.Option("developer", "Developer"),
            ft.dropdown.Option("designer", "Designer"),
            ft.dropdown.Option("tester", "Tester"),
            ft.dropdown.Option("consultant", "Consultant"),
        ]

        # Add member section
        emp_dropdown = ft.Dropdown(
            label="Select Employee", options=emp_options, width=250)
        role_dropdown = ft.Dropdown(
            label="Role", options=role_options, width=180, value="developer")
        hourly_rate = ft.TextField(label="Hourly Rate", width=120, value="0")

        def add_member(e):
            if not emp_dropdown.value:
                self._show_error("Please select an employee")
                return

            emp_id = int(emp_dropdown.value)

            db = get_db_session()
            try:
                existing = db.query(ProjectMember).filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.employee_id == emp_id
                ).first()

                if existing:
                    self._show_error("Employee is already in this project!")
                    return

                new_member = ProjectMember(
                    project_id=project_id,
                    employee_id=emp_id,
                    role=role_dropdown.value or "developer",
                    hourly_rate=float(
                        hourly_rate.value) if hourly_rate.value else 0
                )
                db.add(new_member)
                db.commit()

                self._show_success("Team member added!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        # Current members list
        members_list = ft.Column()
        for member in members:
            emp_name = f"{member.employee.first_name} {member.employee.last_name}" if member.employee else "Unknown"

            # Role color
            role_colors = {
                "project_manager": "#D32F2F",
                "team_lead": "#FF9800",
                "developer": "#2196F3",
                "designer": "#9C27B0",
                "tester": "#4CAF50",
                "consultant": "#607D8B"
            }
            role_color = role_colors.get(member.role, PRIMARY)

            members_list.controls.append(
                ft.Container(
                    padding=10,
                    bgcolor="#F5F5F5",
                    border_radius=8,
                    margin=ft.margin.only(bottom=5),
                    content=ft.Row([
                        ft.Container(
                            width=35, height=35,
                            bgcolor=role_color,
                            border_radius=17,
                            content=ft.Text(
                                emp_name[0], color="WHITE", weight=ft.FontWeight.BOLD),
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(
                                emp_name, weight=ft.FontWeight.BOLD, size=13),
                            ft.Text(
                                f"Role: {member.role.replace('_', ' ').title()}", size=11, color=TEXT_SECONDARY),
                            ft.Text(
                                f"Rate: ₹{member.hourly_rate}/hr" if member.hourly_rate else "Rate: N/A", size=10, color=TEXT_SECONDARY),
                        ], expand=True),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=PRIMARY,
                            on_click=lambda e, mid=member.id: self._edit_project_member_dialog(
                                mid),
                            scale=0.7
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ERROR,
                            on_click=lambda e, mid=member.id: self._remove_project_member(
                                mid),
                            scale=0.7
                        ),
                    ], spacing=10)
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Manage Project Team - {project.name}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Add Team Member", size=14,
                            weight=ft.FontWeight.BOLD),
                    ft.Row([emp_dropdown, role_dropdown,
                           hourly_rate], spacing=10),
                    ft.ElevatedButton("Add Member", on_click=add_member, style=ft.ButtonStyle(
                        bgcolor=SUCCESS, color="WHITE")),
                    ft.Divider(),
                    ft.Text("Current Team", size=14,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    members_list,
                ], scroll=ft.ScrollMode.AUTO),
                width=550,
                height=500,
            ),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _edit_project_member_dialog(self, member_id):
        """Edit project member details"""
        db = get_db_session()
        try:
            member = db.query(ProjectMember).filter(
                ProjectMember.id == member_id).first()
            if not member:
                self._show_error("Member not found")
                return
        finally:
            db.close()

        # Role options
        role_options = [
            ft.dropdown.Option("project_manager", "Project Manager"),
            ft.dropdown.Option("team_lead", "Team Lead"),
            ft.dropdown.Option("developer", "Developer"),
            ft.dropdown.Option("designer", "Designer"),
            ft.dropdown.Option("tester", "Tester"),
            ft.dropdown.Option("consultant", "Consultant"),
        ]

        role_dropdown = ft.Dropdown(
            label="Role", options=role_options, width=180, value=member.role)
        hourly_rate = ft.TextField(
            label="Hourly Rate", width=120, value=str(member.hourly_rate or 0))
        tasks_field = ft.TextField(
            label="Assigned Tasks", width=400, value=member.assigned_tasks or "", multiline=True)

        def save_changes(e):
            db = get_db_session()
            try:
                db.query(ProjectMember).filter(ProjectMember.id == member_id).update({
                    ProjectMember.role: role_dropdown.value,
                    ProjectMember.hourly_rate: float(hourly_rate.value) if hourly_rate.value else 0,
                    ProjectMember.assigned_tasks: tasks_field.value
                })
                db.commit()
                self._show_success("Member updated!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Team Member"),
            content=ft.Column(
                [role_dropdown, hourly_rate, tasks_field], spacing=10),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save_changes, style=ft.ButtonStyle(
                    bgcolor=SUCCESS, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _remove_project_member(self, member_id):
        """Remove member from project"""
        def confirm(e):
            db = get_db_session()
            try:
                db.query(ProjectMember).filter(
                    ProjectMember.id == member_id).delete()
                db.commit()
                self._show_success("Member removed!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Remove Member?"),
            content=ft.Text(
                "Are you sure you want to remove this member from the project?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Remove", on_click=confirm, style=ft.ButtonStyle(
                    bgcolor=ERROR, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

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
        description = ft.TextField(
            label="Description", width=400, multiline=True, value=project.description or "")
        client_name = ft.TextField(
            label="Client Name", width=300, value=project.client_name or "")
        start_date = ft.TextField(label="Start Date", width=200, value=project.start_date.strftime(
            '%Y-%m-%d') if project.start_date else "")
        end_date = ft.TextField(label="End Date", width=200, value=project.end_date.strftime(
            '%Y-%m-%d') if project.end_date else "")
        budget = ft.TextField(label="Budget (Rs.)",
                              width=150, value=str(project.budget or 0))

        status_options = [
            ft.dropdown.Option("planning", "Planning"),
            ft.dropdown.Option("active", "Active"),
            ft.dropdown.Option("on_hold", "On Hold"),
            ft.dropdown.Option("completed", "Completed"),
            ft.dropdown.Option("cancelled", "Cancelled"),
        ]
        status = ft.Dropdown(width=150, options=status_options,
                             label="Status", value=project.status or "planning")

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
                # Delete members first
                db.query(ProjectMember).filter(
                    ProjectMember.project_id == project_id).delete()
                # Delete project
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
            content=ft.Text(
                f"Delete '{project.name}'? This will also remove all team members."),
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
