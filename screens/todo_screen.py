"""
Vernika HRA - Todo/Task List Screen
Complete todo list functionality
"""

import flet as ft
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class TaskItem:
    id: int
    name: str
    completed: bool = False


class TaskWidget(ft.Container):
    def __init__(self, task: TaskItem, on_toggle: Callable, on_delete: Callable, on_edit: Callable):
        super().__init__()
        self.task = task
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        self.on_edit = on_edit

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
        self.on_toggle()

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
        self.next_id = 1

        self.content = self.build_ui()

    def build_ui(self):
        # Header
        header = ft.Container(
            padding=15,
            bgcolor=ft.Colors.CYAN_600,
            content=ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE,
                              on_click=self.go_back),
                ft.Text("My Tasks", size=18, color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.build_stats(),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

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
            header,
            content,
        ], spacing=0)

    def build_stats(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.completed)
        return ft.Text(f"{completed}/{total}", size=14, color=ft.Colors.WHITE)

    def add_clicked(self, e):
        if self.new_task.value.strip():
            task = TaskItem(id=self.next_id, name=self.new_task.value.strip())
            self.next_id += 1
            self.tasks.append(task)
            self.new_task.value = ""
            self.update_list()

    def toggle_task(self, task: TaskItem):
        pass  # Update is handled by widget

    def delete_task(self, task: TaskItem):
        self.tasks = [t for t in self.tasks if t.id != task.id]
        self.update_list()

    def edit_task(self, task: TaskItem):
        # Show edit dialog
        edit_field = ft.TextField(value=task.name, width=300)

        def save_edit(e):
            task.name = edit_field.value
            self.update_list()
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
                )
                self.tasks_list.controls.append(widget)

        self._page.update()

    def go_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)
