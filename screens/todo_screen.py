"""
Vernika HRA - Todo/Task List Screen
Complete todo list functionality with database persistence
"""

import flet as ft
from dataclasses import dataclass
from typing import Callable, Optional
from database.session_manager import get_db_session
from database.models import TodoItem


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


class TaskWidget(ft.Container):
    def __init__(self, task: TodoItem, on_toggle: Callable, on_delete: Callable, on_edit: Callable, parent):
        super().__init__()
        self.task = task
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        self.on_edit = on_edit
        self.parent = parent

        self.checkbox = ft.Checkbox(
            value=task.completed,
            on_change=self.toggle_status,
        )

        self.task_name = ft.Text(
            task.name,
            size=14,
            color=ft.Colors.GREY_400 if task.completed else ft.Colors.BLACK,
            width=200,
        )

        self.padding = 5
        self.border_radius = 8
        self.bgcolor = ft.Colors.SURFACE

        self.content = ft.Row([
            self.checkbox,
            self.task_name,
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_size=18,
                icon_color=ft.Colors.BLUE_400,
                on_click=self.edit_clicked,
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_size=18,
                icon_color=ft.Colors.RED_400,
                on_click=self.delete_clicked,
            ),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def toggle_status(self, e):
        self.task.completed = self.checkbox.value
        self.task_name.color = ft.Colors.GREY_400 if self.task.completed else ft.Colors.BLACK
        # Save to database
        self._save_to_db()
        self.on_toggle()

    def _save_to_db(self):
        """Save task status to database"""
        db = get_db_session()
        try:
            db.query(TodoItem).filter(TodoItem.id == self.task.id).update({
                TodoItem.completed: self.task.completed
            })
            db.commit()
        except Exception as e:
            print(f"Error saving task: {e}")
            db.rollback()
        finally:
            db.close()

    def edit_clicked(self, e):
        self.on_edit(self.task)

    def delete_clicked(self, e):
        self.on_delete(self.task)


class TodoScreen(ft.Container):
    def __init__(self, page: ft.Page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.tasks = []

        # Get user ID
        self.user_id = None
        if isinstance(user, dict):
            self.user_id = user.get('id')
        elif hasattr(user, 'id'):
            self.user_id = user.id

        # Load tasks from database
        self._load_tasks()

        self.content = self.build_ui()

    def _load_tasks(self):
        """Load tasks from database"""
        if not self.user_id:
            return

        db = get_db_session()
        try:
            tasks = db.query(TodoItem).filter(
                TodoItem.user_id == self.user_id
            ).order_by(TodoItem.created_at.desc()).all()
            self.tasks = tasks
        except Exception as e:
            print(f"Error loading tasks: {e}")
            self.tasks = []
        finally:
            db.close()

    def build_ui(self):
        # Input area
        self.new_task = ft.TextField(
            hint_text="Add a new task...",
            expand=True,
            content_padding=10,
            on_submit=self.add_clicked,
        )

        add_btn = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.CYAN_600,
            on_click=self.add_clicked,
        )

        input_row = ft.Container(
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            content=ft.Row([self.new_task, add_btn], spacing=10),
        )

        # Filter tabs
        self.filter_tabs = ft.SegmentedButton(
            segments=[
                ft.Segment(value="all", label=ft.Text("All")),
                ft.Segment(value="active", label=ft.Text("Active")),
                ft.Segment(value="completed", label=ft.Text("Done")),
            ],
            selected=["all"],
            on_change=self.filter_changed,
        )

        # Task list
        self.tasks_list = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
        )

        # Scrollable content
        content = ft.Column([
            input_row,
            ft.Container(
                padding=ft.padding.symmetric(horizontal=15),
                content=self.filter_tabs,
            ),
            ft.Divider(),
            ft.Container(expand=True, content=self.tasks_list),
        ])

        return ft.Column([
            content,
        ], spacing=0)

    def build_stats(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.completed)
        return ft.Text(f"{completed}/{total}", size=14, color=ft.Colors.WHITE)

    def add_clicked(self, e):
        if self.new_task.value.strip() and self.user_id:
            # Save to database
            db = get_db_session()
            try:
                new_task = TodoItem(
                    user_id=self.user_id,
                    name=self.new_task.value.strip(),
                    completed=False,
                    filter_type="all"
                )
                db.add(new_task)
                db.commit()
                # Reload tasks
                self._load_tasks()
                self.new_task.value = ""
                self.update_list()
            except Exception as ex:
                print(f"Error adding task: {ex}")
                self._show_error(str(ex))
            finally:
                db.close()

    def toggle_task(self, task: TodoItem):
        pass  # Update is handled by widget

    def delete_task(self, task: TodoItem):
        # Delete from database
        db = get_db_session()
        try:
            db.query(TodoItem).filter(TodoItem.id == task.id).delete()
            db.commit()
            self._load_tasks()
            self.update_list()
        except Exception as e:
            print(f"Error deleting task: {e}")
        finally:
            db.close()

    def edit_task(self, task: TodoItem):
        # Show edit dialog
        edit_field = ft.TextField(value=task.name, width=300)

        def save_edit(e):
            if edit_field.value.strip():
                # Update in database
                db = get_db_session()
                try:
                    db.query(TodoItem).filter(TodoItem.id == task.id).update({
                        TodoItem.name: edit_field.value.strip()
                    })
                    db.commit()
                    self._load_tasks()
                    self.update_list()
                except Exception as ex:
                    print(f"Error updating task: {ex}")
                finally:
                    db.close()
            dlg.open = False
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Task"),
            content=edit_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(
                    dlg, 'open', False) or self._page.update()),
                ft.TextButton("Save", on_click=save_edit),
            ],
        )
        self._page.dialog = dlg
        dlg.open = True
        self._page.update()

    def filter_changed(self, e):
        self.update_list()

    def update_list(self):
        self.tasks_list.controls.clear()
        selected_list = self.filter_tabs.selected if hasattr(
            self.filter_tabs, 'selected') else []
        filter_val = selected_list[0] if selected_list and len(
            selected_list) > 0 else "all"

        for task in self.tasks:
            if filter_val == "all":
                show = True
            elif filter_val == "active":
                show = not task.completed
            else:  # completed
                show = task.completed

            if show:
                widget = TaskWidget(
                    task,
                    on_toggle=self.update_list,
                    on_delete=self.delete_task,
                    on_edit=self.edit_task,
                    parent=self
                )
                self.tasks_list.controls.append(widget)

        self._page.update()

    def _show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=ft.Colors.RED_700)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def go_back(self, e):
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)
