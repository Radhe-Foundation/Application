"""
Vernika HRA - Dialog Components
Industry-Level Human Resource Management System

This module provides reusable dialog components for the application.
"""

from typing import Optional, Callable
import flet as ft


class ConfirmDialog(ft.AlertDialog):
    """
    Confirmation dialog with title, content, and confirm/cancel buttons.
    """

    def __init__(
        self,
        title: str,
        content: str,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_color: str = "#2E86AB",
        cancel_color: str = "#6C757D",
    ):
        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Icon(ft.Icons.HELP_OUTLINE, size=48, color=confirm_color),
                ft.Container(height=10),
                ft.Text(content),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=self._handle_cancel,
                ),
                ft.ElevatedButton(
                    confirm_text,
                    on_click=self._handle_confirm,
                    bgcolor=confirm_color,
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

    def _handle_confirm(self, e: ft.ControlEvent):
        """Handle confirm action."""
        self.open = False
        self.page.update()
        if self._on_confirm:
            self._on_confirm(e)

    def _handle_cancel(self, e: ft.ControlEvent):
        """Handle cancel action."""
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)


class AlertDialog(ft.AlertDialog):
    """
    Alert dialog with a single OK button.
    """

    def __init__(
        self,
        title: str,
        content: str,
        on_ok: Optional[Callable] = None,
        ok_text: str = "OK",
    ):
        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Icon(ft.Icons.INFO, size=48, color="#2E86AB"),
                ft.Container(height=10),
                ft.Text(content),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            actions=[
                ft.ElevatedButton(
                    ok_text,
                    on_click=self._handle_ok,
                    bgcolor="#2E86AB",
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        self._on_ok = on_ok

    def _handle_ok(self, e: ft.ControlEvent):
        """Handle OK action."""
        self.open = False
        self.page.update()
        if self._on_ok:
            self._on_ok(e)


class InputDialog(ft.AlertDialog):
    """
    Dialog with input field.
    """

    def __init__(
        self,
        title: str,
        label: str,
        placeholder: str = "",
        default_value: str = "",
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        submit_text: str = "Submit",
        cancel_text: str = "Cancel",
        multiline: bool = False,
        password: bool = False,
        width: int = 400,
    ):
        self.input_field = ft.TextField(
            label=label,
            hint_text=placeholder,
            value=default_value,
            multiline=multiline,
            password=password,
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            width=width - 40,
        )

        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=self.input_field,
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=self._handle_cancel,
                ),
                ft.ElevatedButton(
                    submit_text,
                    on_click=self._handle_submit,
                    bgcolor="#2E86AB",
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._on_submit = on_submit
        self._on_cancel = on_cancel

    def _handle_submit(self, e: ft.ControlEvent):
        """Handle submit action."""
        value = self.input_field.value
        self.open = False
        self.page.update()
        if self._on_submit:
            self._on_submit(value, e)

    def _handle_cancel(self, e: ft.ControlEvent):
        """Handle cancel action."""
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)

    def get_value(self) -> str:
        """Get the input value."""
        return self.input_field.value or ""


class LoadingDialog(ft.AlertDialog):
    """
    Loading dialog with progress indicator.
    """

    def __init__(
        self,
        message: str = "Loading...",
        title: str = "Please Wait",
    ):
        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.ProgressRing(width=40, height=40, color="#2E86AB"),
                ft.Container(height=15),
                ft.Text(message),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            actions=[],
        )


class SelectionDialog(ft.AlertDialog):
    """
    Dialog for selecting from a list of options.
    """

    def __init__(
        self,
        title: str,
        options: list,
        on_select: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        display_property: str = "name",
        key_property: str = "id",
    ):
        self.options = options
        self._on_select = on_select
        self._on_cancel = on_cancel

        tiles = []
        for opt in options:
            key = opt.get(key_property, str(opt))
            display = opt.get(display_property, str(opt))
            tiles.append(
                ft.ListTile(
                    title=ft.Text(display),
                    on_click=lambda e, k=key: self._handle_select(k),
                )
            )

        list_view = ft.ListView(
            controls=tiles,
            height=300,
            width=400,
        )

        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=list_view,
                border_radius=8,
                border=ft.border.all(1, "#E0E0E0"),
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self._handle_cancel,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_select(self, key):
        """Handle selection."""
        self.open = False
        self.page.update()
        if self._on_select:
            self._on_select(key)

    def _handle_cancel(self, e: ft.ControlEvent):
        """Handle cancel."""
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)


class FormDialog(ft.AlertDialog):
    """
    Dialog for displaying forms with multiple fields.
    """

    def __init__(
        self,
        title: str,
        fields: list,
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        submit_text: str = "Submit",
        cancel_text: str = "Cancel",
        width: int = 400,
        height: int = 400,
    ):
        self.fields = fields

        form_fields = ft.Column(
            controls=fields,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=form_fields,
                width=width,
                height=height,
            ),
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=self._handle_cancel,
                ),
                ft.ElevatedButton(
                    submit_text,
                    on_click=self._handle_submit,
                    bgcolor="#2E86AB",
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._on_submit = on_submit
        self._on_cancel = on_cancel

    def _handle_submit(self, e: ft.ControlEvent):
        """Handle submit action."""
        values = {}
        for field in self.fields:
            if hasattr(field, 'value'):
                values[field.label if hasattr(
                    field, 'label') else 'field'] = field.value

        self.open = False
        self.page.update()
        if self._on_submit:
            self._on_submit(values, e)

    def _handle_cancel(self, e: ft.ControlEvent):
        """Handle cancel action."""
        self.open = False
        self.page.update()
        if self._on_cancel:
            self._on_cancel(e)


def show_confirm(
    page: ft.Page,
    title: str,
    content: str,
    on_confirm: Callable,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
):
    """Show a confirmation dialog."""
    dialog = ConfirmDialog(
        title=title,
        content=content,
        on_confirm=on_confirm,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
    )
    page.dialog = dialog
    dialog.open = True
    page.update()


def show_alert(
    page: ft.Page,
    title: str,
    content: str,
    on_ok: Callable = None,
    ok_text: str = "OK",
):
    """Show an alert dialog."""
    dialog = AlertDialog(
        title=title,
        content=content,
        on_ok=on_ok,
        ok_text=ok_text,
    )
    page.dialog = dialog
    dialog.open = True
    page.update()


def show_input(
    page: ft.Page,
    title: str,
    label: str,
    on_submit: Callable,
    placeholder: str = "",
    default_value: str = "",
    submit_text: str = "Submit",
    cancel_text: str = "Cancel",
    multiline: bool = False,
):
    """Show an input dialog."""
    dialog = InputDialog(
        title=title,
        label=label,
        placeholder=placeholder,
        default_value=default_value,
        on_submit=on_submit,
        submit_text=submit_text,
        cancel_text=cancel_text,
        multiline=multiline,
    )
    page.dialog = dialog
    dialog.open = True
    page.update()


def show_loading(
    page: ft.Page,
    message: str = "Loading...",
) -> "LoadingDialog":
    """Show a loading dialog."""
    dialog = LoadingDialog(message=message)
    page.dialog = dialog
    dialog.open = True
    page.update()
    return dialog


def close_loading(page: ft.Page, dialog: "LoadingDialog" = None):
    """Close the loading dialog."""
    d = dialog or page.dialog
    if d:
        d.open = False
        page.update()
