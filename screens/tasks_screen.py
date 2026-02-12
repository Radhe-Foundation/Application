"""
Vernika HRA - Enhanced Tasks Screen - Fixed for Flet 0.80+
Updated to use SQLAlchemy operations instead of direct SQLite
"""

import flet as ft
from datetime import datetime, date
from database.connection import get_db_session
from database.models import Task, Employee, TaskStatus, TaskPriority
from database.operations import (
    get_all_employees, create_task, get_task_by_id, update_task, delete_task,
    get_all_tasks, add_task_comment, get_task_comments
)

# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#28A745"
ERROR = "#DC3545"
WARNING = "#FFC107"
BACKGROUND = "#F8F9FA"


class TasksScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = "#F5F5F5"
        self.content = self._build_content()

    def _build_content(self):
        # Check user role to determine header
        user_role = ""
        if isinstance(self.user, dict):
            user_role = self.user.get('role', '').lower()
        else:
            user_role = getattr(self.user, 'role', '').lower(
            ) if hasattr(self.user, 'role') else ''

        is_admin = user_role == 'admin'

        header = ft.Container(
            padding=15,
            bgcolor="#009688",
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self.on_back
                ) if is_admin else ft.Container(),
                ft.Text("Task Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Create Task",
                    icon=ft.Icons.ADD,
                    on_click=self.on_add,
                    style=ft.ButtonStyle(bgcolor="#00796B", color="WHITE")
                ) if is_admin else ft.Container(),
            ])
        )

        task_list = self._build_task_list()

        content = ft.Column([
            header,
            ft.Container(
                padding=20,
                content=task_list,
                expand=True
            )
        ], expand=True)

        return content

    def on_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def on_add(self, e):
        self._show_add_dialog()

    def _get_employees(self):
        """Get list of employees for dropdown using SQLAlchemy"""
        try:
            session = get_db_session()
            employees = get_all_employees(session)
            session.close()
            return employees
        except Exception as e:
            print(f"Error loading employees: {e}")
            return []

    def _build_task_list(self):
        try:
            session = get_db_session()
            tasks = get_all_tasks(session, limit=100)
            session.close()
        except Exception as e:
            print(f"Error loading tasks: {e}")
            tasks = []

        if not tasks:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.TASK, size=64, color="#BDBDBD"),
                    ft.Text("No tasks. Create one!", size=14, color="#757575"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Create First Task",
                        on_click=self.on_add,
                        style=ft.ButtonStyle(bgcolor="#009688", color="WHITE")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        rows = []
        for t in tasks:
            priority_colors = {
                "urgent": "#F44336", "high": "#FF9800", "medium": "#FFC107", "low": "#4CAF50"
            }
            status_colors = {
                "completed": "#4CAF50", "in_progress": "#2196F3",
                "todo": "#9E9E9E", "cancelled": "#F44336"
            }
            type_colors = {
                "feature": "#2196F3", "bug": "#F44336", "improvement": "#FF9800"
            }

            # Safely get values from SQLAlchemy model
            priority_val = str(t.priority.value) if hasattr(
                t.priority, 'value') else str(t.priority) if t.priority else "medium"
            status_val = str(t.status.value) if hasattr(
                t.status, 'value') else str(t.status) if t.status else "todo"
            task_type_val = getattr(t, 'task_type', None) or "feature"

            p_color = priority_colors.get(priority_val, "#4CAF50")
            s_color = status_colors.get(status_val, "#9E9E9E")
            type_color = type_colors.get(task_type_val, "#9E9E9E")

            est_hours = getattr(t, 'estimated_hours', 0) or 0
            act_hours = getattr(t, 'actual_hours', 0) or 0
            hours_text = f"{act_hours}/{est_hours}h" if est_hours else f"{act_hours}h"

            # Get assignee name
            assignee_name = "Unassigned"
            if t.assigned_to:
                assignee_name = f"{t.assigned_to.first_name or ''} {t.assigned_to.last_name or ''}".strip(
                ) or "Unknown"

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(t.title[:30] + "..." if len(t.title) > 30 else t.title)),
                        ft.DataCell(
                            ft.Text(getattr(t, 'project_name', None) or "-")),
                        ft.DataCell(
                            ft.Text(getattr(t, 'category', None) or "-")),
                        ft.DataCell(ft.Text(assignee_name)),
                        ft.DataCell(ft.Container(
                            ft.Text(priority_val, size=11, color="WHITE"),
                            bgcolor=p_color, padding=5, border_radius=4
                        )),
                        ft.DataCell(ft.Container(
                            ft.Text(task_type_val, size=11, color="WHITE"),
                            bgcolor=type_color, padding=5, border_radius=4
                        )),
                        ft.DataCell(ft.Container(
                            ft.Text(status_val.replace(
                                "_", " ").title(), size=11, color="WHITE"),
                            bgcolor=s_color, padding=5, border_radius=4
                        )),
                        ft.DataCell(ft.Text(hours_text)),
                        ft.DataCell(
                            ft.Text(str(t.start_date) if t.start_date else "-")),
                        ft.DataCell(
                            ft.Text(str(t.due_date) if t.due_date else "-")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.TIMER, icon_color="#4CAF50",
                                    on_click=lambda e, task_id=t.id: self._show_time_tracking_dialog(
                                        task_id),
                                    tooltip="Time Tracking"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.COMMENT, icon_color="#9C27B0",
                                    on_click=lambda e, task_id=t.id: self._show_comments_dialog(
                                        task_id),
                                    tooltip="Comments"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT, icon_color="#1976D2",
                                    on_click=lambda e, task_id=t.id: self._show_edit_dialog(
                                        task_id),
                                    tooltip="Edit"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE, icon_color="#D32F2F",
                                    on_click=lambda e, task_id=t.id: self._show_delete_dialog(
                                        task_id),
                                    tooltip="Delete"
                                ),
                            ], spacing=2)
                        ),
                    ]
                )
            )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(label=ft.Text("Task")),
                ft.DataColumn(label=ft.Text("Project")),
                ft.DataColumn(label=ft.Text("Category")),
                ft.DataColumn(label=ft.Text("Assignee")),
                ft.DataColumn(label=ft.Text("Priority")),
                ft.DataColumn(label=ft.Text("Type")),
                ft.DataColumn(label=ft.Text("Status")),
                ft.DataColumn(label=ft.Text("Hours")),
                ft.DataColumn(label=ft.Text("Start")),
                ft.DataColumn(label=ft.Text("Due")),
                ft.DataColumn(label=ft.Text("Actions"))
            ],
            rows=rows,
            expand=True,
        )

        return ft.Container(content=table, expand=True)

    def _show_add_dialog(self):
        employees = self._get_employees()

        emp_options = [ft.dropdown.Option(
            key=str(e.id), text=f"{e.first_name or ''} {e.last_name or ''}".strip() or "Unknown") for e in employees]

        priority_options = [
            ft.dropdown.Option(key="low", text="Low"),
            ft.dropdown.Option(key="medium", text="Medium"),
            ft.dropdown.Option(key="high", text="High"),
            ft.dropdown.Option(key="urgent", text="Urgent"),
        ]
        status_options = [
            ft.dropdown.Option(key="todo", text="To Do"),
            ft.dropdown.Option(key="in_progress", text="In Progress"),
            ft.dropdown.Option(key="completed", text="Completed"),
            ft.dropdown.Option(key="cancelled", text="Cancelled"),
        ]
        task_type_options = [
            ft.dropdown.Option(key="feature", text="Feature"),
            ft.dropdown.Option(key="bug", text="Bug"),
            ft.dropdown.Option(key="improvement", text="Improvement"),
        ]
        category_options = [
            ft.dropdown.Option(key="development", text="Development"),
            ft.dropdown.Option(key="testing", text="Testing"),
            ft.dropdown.Option(key="documentation", text="Documentation"),
            ft.dropdown.Option(key="research", text="Research"),
            ft.dropdown.Option(key="maintenance", text="Maintenance"),
            ft.dropdown.Option(key="other", text="Other"),
        ]

        # Basic Info
        title = ft.TextField(label="Title *", width=450)
        desc = ft.TextField(label="Description", width=450,
                            multiline=True, min_lines=2)

        # Assignment
        assignee = ft.Dropdown(
            width=250, options=emp_options, label="Assignee *")
        category = ft.Dropdown(
            width=180, options=category_options, label="Category")
        task_type = ft.Dropdown(
            width=150, options=task_type_options, label="Task Type", value="feature")

        # Priority & Status
        priority = ft.Dropdown(
            width=150, options=priority_options, label="Priority", value="medium")
        status = ft.Dropdown(
            width=150, options=status_options, label="Status", value="todo")

        # Dates
        start_date = ft.TextField(label="Start Date (YYYY-MM-DD)", width=180)
        due_date = ft.TextField(label="Due Date (YYYY-MM-DD)", width=180)

        # Time Tracking
        project_name = ft.TextField(label="Project Name", width=250)
        estimated_hours = ft.TextField(
            label="Est. Hours", width=100, value="0")

        error = ft.Text("", color="#F44336", size=12, visible=False)

        def save(e):
            if not title.value or not assignee.value:
                error.value = "Title and Assignee required!"
                error.visible = True
                self._page.update()
                return

            try:
                est_hours = float(
                    estimated_hours.value) if estimated_hours.value else 0

                # Parse dates
                start_date_obj = None
                due_date_obj = None
                if start_date.value:
                    try:
                        start_date_obj = datetime.strptime(
                            start_date.value, "%Y-%m-%d").date()
                    except:
                        pass
                if due_date.value:
                    try:
                        due_date_obj = datetime.strptime(
                            due_date.value, "%Y-%m-%d").date()
                    except:
                        pass

                # Get priority and status enums
                priority_enum = TaskPriority.MEDIUM
                if priority.value == "low":
                    priority_enum = TaskPriority.LOW
                elif priority.value == "high":
                    priority_enum = TaskPriority.HIGH
                elif priority.value == "urgent":
                    priority_enum = TaskPriority.URGENT

                status_enum = TaskStatus.TODO
                if status.value == "in_progress":
                    status_enum = TaskStatus.IN_PROGRESS
                elif status.value == "completed":
                    status_enum = TaskStatus.COMPLETED
                elif status.value == "cancelled":
                    status_enum = TaskStatus.CANCELLED

                # Get current user ID for created_by
                # Use assignee as created_by for now
                created_by_id = int(assignee.value)

                session = get_db_session()
                try:
                    create_task(
                        session,
                        title=title.value,
                        description=desc.value,
                        assigned_to_id=int(assignee.value),
                        created_by_id=created_by_id,
                        priority=priority_enum,
                        due_date=due_date_obj,
                        status=status_enum
                    )
                    self._close_dialog()
                    self._show_success("Task created successfully!")
                    self._refresh()
                except Exception as ex:
                    error.value = str(ex)
                    error.visible = True
                    self._page.update()
                finally:
                    session.close()

            except Exception as ex:
                error.value = str(ex)
                error.visible = True
                self._page.update()

        # Build form content with scroll support
        tab_content = ft.Column([
            ft.Text("Basic Information", size=14,
                    weight=ft.FontWeight.BOLD, color=PRIMARY),
            title, desc,
            ft.Divider(),
            ft.Text("Assignment", size=14,
                    weight=ft.FontWeight.BOLD, color="#9C27B0"),
            ft.Row([assignee, category, task_type], spacing=10),
            ft.Divider(),
            ft.Text("Details", size=14,
                    weight=ft.FontWeight.BOLD, color=SUCCESS),
            ft.Row([project_name, priority, status], spacing=10),
            ft.Row([start_date, due_date, estimated_hours], spacing=10),
            error,
            ft.Container(height=20),
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create Task"),
            content=ft.Container(
                content=tab_content,
                width=550,
                height=450,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Create", on_click=save, style=ft.ButtonStyle(
                    bgcolor="#009688", color="WHITE"))
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_edit_dialog(self, task_id):
        session = get_db_session()
        try:
            t = get_task_by_id(session, task_id)
            if not t:
                self._show_error("Task not found!")
                return
        finally:
            session.close()

        employees = self._get_employees()

        emp_options = [ft.dropdown.Option(
            key=str(e.id), text=f"{e.first_name or ''} {e.last_name or ''}".strip() or "Unknown") for e in employees]

        priority_options = [
            ft.dropdown.Option(key="low", text="Low"),
            ft.dropdown.Option(key="medium", text="Medium"),
            ft.dropdown.Option(key="high", text="High"),
            ft.dropdown.Option(key="urgent", text="Urgent"),
        ]
        status_options = [
            ft.dropdown.Option(key="todo", text="To Do"),
            ft.dropdown.Option(key="in_progress", text="In Progress"),
            ft.dropdown.Option(key="completed", text="Completed"),
            ft.dropdown.Option(key="cancelled", text="Cancelled"),
        ]
        task_type_options = [
            ft.dropdown.Option(key="feature", text="Feature"),
            ft.dropdown.Option(key="bug", text="Bug"),
            ft.dropdown.Option(key="improvement", text="Improvement"),
        ]
        category_options = [
            ft.dropdown.Option(key="development", text="Development"),
            ft.dropdown.Option(key="testing", text="Testing"),
            ft.dropdown.Option(key="documentation", text="Documentation"),
            ft.dropdown.Option(key="research", text="Research"),
            ft.dropdown.Option(key="maintenance", text="Maintenance"),
            ft.dropdown.Option(key="other", text="Other"),
        ]

        # Basic Info
        title = ft.TextField(label="Title", width=450, value=t.title or "")
        desc = ft.TextField(label="Description", width=450,
                            value=t.description or "", multiline=True, min_lines=2)

        # Assignment
        assignee = ft.Dropdown(width=250, options=emp_options, label="Assignee",
                               value=str(t.assigned_to_id) if t.assigned_to_id else None)
        category = ft.Dropdown(width=180, options=category_options, label="Category",
                               value=getattr(t, 'category', None))
        task_type = ft.Dropdown(width=150, options=task_type_options, label="Task Type",
                                value=getattr(t, 'task_type', "feature"))

        # Priority & Status
        current_priority = str(t.priority.value) if hasattr(
            t.priority, 'value') else str(t.priority) if t.priority else "medium"
        current_status = str(t.status.value) if hasattr(
            t.status, 'value') else str(t.status) if t.status else "todo"

        priority = ft.Dropdown(width=150, options=priority_options, label="Priority",
                               value=current_priority)
        status = ft.Dropdown(width=150, options=status_options, label="Status",
                             value=current_status)

        # Dates
        start_date = ft.TextField(label="Start Date", width=180,
                                  value=str(t.start_date) if t.start_date else "")
        due_date = ft.TextField(label="Due Date", width=180,
                                value=str(t.due_date) if t.due_date else "")

        # Time Tracking
        project_name = ft.TextField(
            label="Project Name", width=250, value=getattr(t, 'project_name', "") or "")
        estimated_hours = ft.TextField(label="Est. Hours", width=100,
                                       value=str(getattr(t, 'estimated_hours', 0) or 0))
        actual_hours = ft.TextField(label="Actual Hours", width=100,
                                    value=str(getattr(t, 'actual_hours', 0) or 0))

        def update(e):
            try:
                est_hours = float(
                    estimated_hours.value) if estimated_hours.value else 0
                act_hours = float(
                    actual_hours.value) if actual_hours.value else 0

                # Parse dates
                start_date_obj = None
                due_date_obj = None
                if start_date.value:
                    try:
                        start_date_obj = datetime.strptime(
                            start_date.value, "%Y-%m-%d").date()
                    except:
                        pass
                if due_date.value:
                    try:
                        due_date_obj = datetime.strptime(
                            due_date.value, "%Y-%m-%d").date()
                    except:
                        pass

                # Get priority and status enums
                priority_enum = TaskPriority.MEDIUM
                if priority.value == "low":
                    priority_enum = TaskPriority.LOW
                elif priority.value == "high":
                    priority_enum = TaskPriority.HIGH
                elif priority.value == "urgent":
                    priority_enum = TaskPriority.URGENT

                status_enum = TaskStatus.TODO
                if status.value == "in_progress":
                    status_enum = TaskStatus.IN_PROGRESS
                elif status.value == "completed":
                    status_enum = TaskStatus.COMPLETED
                elif status.value == "cancelled":
                    status_enum = TaskStatus.CANCELLED

                session = get_db_session()
                try:
                    update_task(
                        session,
                        task_id=task_id,
                        title=title.value,
                        description=desc.value,
                        assigned_to_id=int(
                            assignee.value) if assignee.value else None,
                        priority=priority_enum,
                        status=status_enum,
                        due_date=due_date_obj
                    )
                    self._close_dialog()
                    self._show_success("Task updated successfully!")
                    self._refresh()
                except Exception as ex:
                    self._show_error(str(ex))
                finally:
                    session.close()

            except Exception as ex:
                self._show_error(str(ex))

        # Build form content with scroll support
        tab_content = ft.Column([
            ft.Text("Basic Information", size=14,
                    weight=ft.FontWeight.BOLD, color=PRIMARY),
            title, desc,
            ft.Divider(),
            ft.Text("Assignment", size=14,
                    weight=ft.FontWeight.BOLD, color="#9C27B0"),
            ft.Row([assignee, category, task_type], spacing=10),
            ft.Divider(),
            ft.Text("Details", size=14,
                    weight=ft.FontWeight.BOLD, color=SUCCESS),
            ft.Row([project_name, priority, status], spacing=10),
            ft.Row([start_date, due_date], spacing=10),
            ft.Row([estimated_hours, actual_hours], spacing=10),
            ft.Container(height=20),
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Task"),
            content=ft.Container(
                content=tab_content,
                width=550,
                height=450,
            ),
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

    def _show_time_tracking_dialog(self, task_id):
        """Show time tracking dialog"""
        session = get_db_session()
        try:
            t = get_task_by_id(session, task_id)
            if not t:
                self._show_error("Task not found!")
                return

            title = t.title
            est_hours = getattr(t, 'estimated_hours', 0) or 0
            act_hours = getattr(t, 'actual_hours', 0) or 0
        finally:
            session.close()

        hours_input = ft.TextField(label="Add Hours", width=100, value="0")

        def add_hours(e):
            try:
                hours = float(hours_input.value) if hours_input.value else 0
                if hours <= 0:
                    self._show_error("Please enter valid hours!")
                    return

                session = get_db_session()
                try:
                    # Update actual hours
                    new_actual = act_hours + hours
                    update_task(session, task_id=task_id,
                                actual_hours=new_actual)
                    self._close_dialog()
                    self._show_success(f"Added {hours} hours!")
                    self._refresh()
                except Exception as ex:
                    self._show_error(str(ex))
                finally:
                    session.close()

            except Exception as ex:
                self._show_error(str(ex))

        content = ft.Column([
            ft.Text(f"Task: {title[:40]}", size=14, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text(f"Estimated: {est_hours}h", size=12, color="#757575"),
                ft.Text(f"Actual: {act_hours}h", size=12, color="#4CAF50"),
            ], spacing=20),
            ft.Divider(),
            ft.Row([hours_input, ft.ElevatedButton("Add Hours", on_click=add_hours,
                                                   style=ft.ButtonStyle(bgcolor="#009688", color="WHITE"))], spacing=10),
        ], spacing=10)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Time Tracking"),
            content=ft.Container(content=content, height=150, width=350),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_comments_dialog(self, task_id):
        """Show task comments dialog"""
        session = get_db_session()
        try:
            t = get_task_by_id(session, task_id)
            if not t:
                self._show_error("Task not found!")
                return

            task_title = t.title
            comments = get_task_comments(session, task_id)
        finally:
            session.close()

        # Get current user ID
        current_user_id = self.user.get('id') if isinstance(
            self.user, dict) else getattr(self.user, 'id', 1)

        comment_input = ft.TextField(
            label="Add Comment", width=450, multiline=True, min_lines=2)

        def add_comment(e):
            if not comment_input.value.strip():
                self._show_error("Please enter a comment!")
                return

            try:
                session = get_db_session()
                try:
                    # Find employee ID for current user
                    from database.operations import get_employee_by_user_id
                    employee = get_employee_by_user_id(
                        session, current_user_id)
                    employee_id = employee.id if employee else current_user_id

                    add_task_comment(session, task_id=task_id, employee_id=employee_id,
                                     content=comment_input.value)
                    self._close_dialog()
                    self._show_success("Comment added!")
                    self._refresh()
                except Exception as ex:
                    self._show_error(str(ex))
                finally:
                    session.close()

            except Exception as ex:
                self._show_error(str(ex))

        if not comments:
            comments_list = ft.Column([
                ft.Icon(ft.Icons.COMMENT_OUTLINED, size=32, color="#BDBDBD"),
                ft.Text("No comments yet", size=12, color="#757575"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            comment_rows = []
            for c in comments:
                author_name = "Unknown"
                if c.employee:
                    author_name = f"{c.employee.first_name or ''} {c.employee.last_name or ''}".strip(
                    ) or "Unknown"

                comment_rows.append(
                    ft.Container(
                        bgcolor="#F5F5F5",
                        padding=10,
                        border_radius=8,
                        content=ft.Column([
                            ft.Row([
                                ft.Text(author_name, size=12,
                                        weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                ft.Text(str(c.created_at)[
                                        :16] if c.created_at else "", size=10, color="#757575"),
                            ]),
                            ft.Text(c.content or "", size=11),
                        ], spacing=3)
                    )
                )
            comments_list = ft.Column(
                comment_rows, spacing=8, scroll=ft.ScrollMode.AUTO)

        dialog_content = ft.Column([
            ft.Text(f"Task: {task_title[:30]}",
                    size=14, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Container(content=comments_list, height=250, width=500),
            ft.Divider(),
            comment_input,
            ft.ElevatedButton("Add Comment", on_click=add_comment,
                              style=ft.ButtonStyle(bgcolor="#009688", color="WHITE")),
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Task Comments"),
            content=ft.Container(content=dialog_content,
                                 height=400, width=550),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_delete_dialog(self, task_id):
        session = get_db_session()
        try:
            t = get_task_by_id(session, task_id)
            if not t:
                self._show_error("Task not found!")
                return
            task_title = t.title
        finally:
            session.close()

        def confirm(e):
            try:
                session = get_db_session()
                try:
                    delete_task(session, task_id)
                    self._close_dialog()
                    self._show_success("Task deleted!")
                    self._refresh()
                except Exception as ex:
                    self._show_error(str(ex))
                finally:
                    session.close()
            except Exception as ex:
                self._show_error(str(ex))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Task?", color="#F44336"),
            content=ft.Text(f"Delete '{task_title[:30]}...'?"),
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


def show_tasks(page, user):
    page.clean()
    page.add(TasksScreen(page, user))
