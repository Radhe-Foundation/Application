"""
Vernika HRA - Teams Management Screen
Enhanced with employee members, roles, work status, and task assignment
"""

import flet as ft
from sqlalchemy.orm import Session
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Team, TeamMember, Employee
from sqlalchemy.orm import joinedload
import json


# Theme colors
PRIMARY = "#7B1FA2"
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
        # Fallback navigation
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
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)

    def on_create(self, e):
        self._show_create_dialog()

    def _get_teams(self):
        """Get all teams from database"""
        db = get_db_session()
        try:
            teams = db.query(Team).order_by(Team.name).all()
            return teams
        except Exception as e:
            print(f"Error loading teams: {e}")
            return []
        finally:
            db.close()

    def _get_team_members(self, team_id):
        """Get team members with details"""
        db = get_db_session()
        try:
            members = db.query(TeamMember).options(
                joinedload(TeamMember.employee)
            ).filter(TeamMember.team_id == team_id).all()
            return members
        except Exception as e:
            print(f"Error loading team members: {e}")
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

    def _build_teams_list(self):
        """Build teams list with member counts"""
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
            # Get member count
            member_count = 0
            try:
                db = get_db_session()
                member_count = db.query(TeamMember).filter(
                    TeamMember.team_id == team.id,
                    TeamMember.is_active == True
                ).count()
                db.close()
            except Exception:
                pass

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(team.id))),
                        ft.DataCell(ft.Text(team.name or "")),
                        ft.DataCell(ft.Text(team.description or "-")),
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
                                    on_click=lambda e, team_id=team.id: self._manage_members_dialog(
                                        team_id),
                                    tooltip="Manage Members"
                                ),
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
                ft.DataColumn(label=ft.Text("Members")),
                ft.DataColumn(label=ft.Text("Actions")),
            ],
            rows=rows,
            expand=True,
        )

        return ft.Container(content=table, expand=True)

    def _manage_members_dialog(self, team_id):
        """Show dialog to manage team members"""
        db = get_db_session()
        try:
            team = db.query(Team).filter(Team.id == team_id).first()
            members = db.query(TeamMember).options(
                joinedload(TeamMember.employee)
            ).filter(TeamMember.team_id == team_id).all()
            employees = db.query(Employee).filter(
                Employee.is_active == True
            ).all()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            db.close()

        if not team:
            self._show_error("Team not found!")
            return

        # Employee options
        emp_options = []
        for emp in employees:
            name = f"{emp.first_name} {emp.last_name}"
            emp_options.append(ft.dropdown.Option(str(emp.id), name))

        # Role options
        role_options = [
            ft.dropdown.Option("team_lead", "Team Lead"),
            ft.dropdown.Option("member", "Member"),
            ft.dropdown.Option("developer", "Developer"),
            ft.dropdown.Option("designer", "Designer"),
            ft.dropdown.Option("tester", "Tester"),
        ]

        # Work status options
        status_options = [
            ft.dropdown.Option("active", "Active"),
            ft.dropdown.Option("on_break", "On Break"),
            ft.dropdown.Option("on_leave", "On Leave"),
            ft.dropdown.Option("offline", "Offline"),
        ]

        # Add member section
        emp_dropdown = ft.Dropdown(
            label="Select Employee", options=emp_options, width=250)
        role_dropdown = ft.Dropdown(
            label="Role", options=role_options, width=150, value="member")
        status_dropdown = ft.Dropdown(
            label="Work Status", options=status_options, width=150, value="active")

        def add_member(e):
            if not emp_dropdown.value:
                self._show_error("Please select an employee")
                return

            emp_id = int(emp_dropdown.value)

            db = get_db_session()
            try:
                # Check if already a member
                existing = db.query(TeamMember).filter(
                    TeamMember.team_id == team_id,
                    TeamMember.employee_id == emp_id
                ).first()

                if existing:
                    self._show_error("Employee is already a member!")
                    return

                new_member = TeamMember(
                    team_id=team_id,
                    employee_id=emp_id,
                    role=role_dropdown.value or "member",
                    work_status=status_dropdown.value or "active"
                )
                db.add(new_member)
                db.commit()

                self._show_success("Member added!")
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

            # Status color
            status_colors = {
                "active": SUCCESS,
                "on_break": WARNING,
                "on_leave": "#2196F3",
                "offline": "#9E9E9E"
            }
            status_color = status_colors.get(member.work_status, "#9E9E9E")

            # Role color
            role_colors = {
                "team_lead": "#D32F2F",
                "member": PRIMARY,
                "developer": "#2196F3",
                "designer": "#FF9800",
                "tester": "#4CAF50"
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
                            ft.Text(f"Role: {member.role}",
                                    size=11, color=TEXT_SECONDARY),
                        ], expand=True),
                        ft.Container(
                            content=ft.Text(member.work_status.replace(
                                "_", " ").title(), size=10, color="WHITE"),
                            bgcolor=status_color,
                            padding=5,
                            border_radius=4,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=PRIMARY,
                            on_click=lambda e, mid=member.id: self._edit_member_dialog(
                                mid),
                            scale=0.7
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ERROR,
                            on_click=lambda e, mid=member.id: self._remove_member(
                                mid),
                            scale=0.7
                        ),
                    ], spacing=10)
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Manage Members - {team.name}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Add New Member", size=14,
                            weight=ft.FontWeight.BOLD),
                    ft.Row([emp_dropdown, role_dropdown,
                           status_dropdown], spacing=10),
                    ft.ElevatedButton("Add Member", on_click=add_member, style=ft.ButtonStyle(
                        bgcolor=SUCCESS, color="WHITE")),
                    ft.Divider(),
                    ft.Text("Current Members", size=14,
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

    def _edit_member_dialog(self, member_id):
        """Edit member details"""
        db = get_db_session()
        try:
            member = db.query(TeamMember).filter(
                TeamMember.id == member_id).first()
            if not member:
                self._show_error("Member not found")
                return
        finally:
            db.close()

        # Role options
        role_options = [
            ft.dropdown.Option("team_lead", "Team Lead"),
            ft.dropdown.Option("member", "Member"),
            ft.dropdown.Option("developer", "Developer"),
            ft.dropdown.Option("designer", "Designer"),
            ft.dropdown.Option("tester", "Tester"),
        ]

        # Work status options
        status_options = [
            ft.dropdown.Option("active", "Active"),
            ft.dropdown.Option("on_break", "On Break"),
            ft.dropdown.Option("on_leave", "On Leave"),
            ft.dropdown.Option("offline", "Offline"),
        ]

        role_dropdown = ft.Dropdown(
            label="Role", options=role_options, width=150, value=member.role)
        status_dropdown = ft.Dropdown(
            label="Work Status", options=status_options, width=150, value=member.work_status)
        tasks_field = ft.TextField(
            label="Assigned Tasks", width=400, value=member.assigned_tasks or "", multiline=True)

        def save_changes(e):
            db = get_db_session()
            try:
                db.query(TeamMember).filter(TeamMember.id == member_id).update({
                    TeamMember.role: role_dropdown.value,
                    TeamMember.work_status: status_dropdown.value,
                    TeamMember.assigned_tasks: tasks_field.value
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
            title=ft.Text("Edit Member"),
            content=ft.Column(
                [role_dropdown, status_dropdown, tasks_field], spacing=10),
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

    def _remove_member(self, member_id):
        """Remove member from team"""
        def confirm(e):
            db = get_db_session()
            try:
                db.query(TeamMember).filter(
                    TeamMember.id == member_id).delete()
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
                "Are you sure you want to remove this member from the team?"),
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
                existing = db.query(Team).filter(
                    Team.name == name.value).first()
                if existing:
                    error.value = "Team name already exists!"
                    error.visible = True
                    self._page.update()
                    return

                new_team = Team(name=name.value,
                                description=description.value or None)
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
        description = ft.TextField(
            label="Description", width=400, multiline=True, value=team.description or "")

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
                # Delete members first
                db.query(TeamMember).filter(
                    TeamMember.team_id == team_id).delete()
                # Delete team
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
            content=ft.Text(
                f"Delete '{team.name}'? This will also remove all members."),
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
