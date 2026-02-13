"""
Vernika HRA - Form Components
Industry-Level Human Resource Management System

This module provides reusable form components for the application.
"""

from typing import Optional, Callable, Any
import flet as ft
from flet import (
    Column, TextField, Dropdown, Checkbox, DatePicker, TimePicker,
    ElevatedButton, OutlinedButton, Text, Container,
    Row, IconButton, Icons, InputBorder, SnackBar
)
from datetime import datetime


class DatePickerField(ft.Container):
    """
    Custom Date Picker Field with integrated picker.
    Reusable component for selecting dates in forms.
    """

    def __init__(self, label="Date", width=200, value=None, **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.date_value = value

        self.text_field = ft.TextField(
            label=label,
            width=width - 50,
            value=value if value else "",
            read_only=True,
            hint_text="YYYY-MM-DD"
        )

        self.picker_button = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=self._show_picker,
            tooltip="Select date"
        )

        self.content = ft.Row([
            self.text_field,
            self.picker_button
        ], spacing=0)

        # DatePicker control
        self.date_picker = ft.DatePicker(
            on_change=self._on_date_change,
            first_date=datetime(1950, 1, 1),
            last_date=datetime(2100, 12, 31),
        )

        # Add picker to page overlay when dialog opens
        self._page = None

    def _show_picker(self, e):
        if self._page:
            if self.date_value:
                # Set picker date if we have a value
                try:
                    dt = datetime.strptime(self.date_value, '%Y-%m-%d')
                    self.date_picker.value = dt
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid date format in picker: {e}")
            self._page.overlay.append(self.date_picker)
            self.date_picker.open = True
            self._page.update()

    def _on_date_change(self, e):
        if e.control.value:
            self.date_value = e.control.value.strftime('%Y-%m-%d')
            self.text_field.value = self.date_value
            if self._page:
                # Remove picker from overlay
                self._page.overlay.remove(self.date_picker)
                self._page.update()

    @property
    def value(self):
        return self.date_value

    @value.setter
    def value(self, val):
        self.date_value = val
        self.text_field.value = val if val else ""


class TimePickerField(ft.Container):
    """
    Custom Time Picker Field with integrated picker.
    Reusable component for selecting times in forms.
    """

    def __init__(self, label="Time", width=150, value=None, **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.time_value = value

        self.text_field = ft.TextField(
            label=label,
            width=width - 50,
            value=value if value else "",
            read_only=True,
            hint_text="HH:MM"
        )

        self.picker_button = ft.IconButton(
            icon=ft.Icons.ACCESS_TIME,
            on_click=self._show_picker,
            tooltip="Select time"
        )

        self.content = ft.Row([
            self.text_field,
            self.picker_button
        ], spacing=0)

        # TimePicker control
        self.time_picker = ft.TimePicker(
            on_change=self._on_time_change,
        )

        # Add picker to page overlay when dialog opens
        self._page = None

    def _show_picker(self, e):
        if self._page:
            self._page.overlay.append(self.time_picker)
            self.time_picker.open = True
            self._page.update()

    def _on_time_change(self, e):
        if e.control.value:
            # time_picker.value is a datetime.time object
            time_obj = e.control.value
            self.time_value = time_obj.strftime('%H:%M')
            self.text_field.value = self.time_value
            if self._page:
                # Remove picker from overlay
                self._page.overlay.remove(self.time_picker)
                self._page.update()

    @property
    def value(self):
        return self.time_value

    @value.setter
    def value(self, val):
        self.time_value = val
        self.text_field.value = val if val else ""


class VernikaTextField(TextField):
    """
    Custom text field with Vernika styling.
    """

    def __init__(
        self,
        label: str = "",
        placeholder: str = "",
        value: str = "",
        password: bool = False,
        can_reveal_password: bool = False,
        multiline: bool = False,
        min_lines: int = 1,
        max_lines: int = 1,
        readonly: bool = False,
        on_change: Optional[Callable] = None,
        error_text: str = "",
        **kwargs
    ):
        super().__init__(
            label=label,
            value=value,
            password=password,
            can_reveal_password=can_reveal_password,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
            readonly=readonly,
            on_change=on_change,
            error_text=error_text,
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            cursor_color="#2E86AB",
            **kwargs
        )
        if placeholder:
            self.hint_text = placeholder


class VernikaPasswordField(VernikaTextField):
    """
    Password field with show/hide functionality.
    """

    def __init__(
        self,
        label: str = "Password",
        value: str = "",
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(
            label=label,
            value=value,
            password=True,
            can_reveal_password=True,
            on_change=on_change,
            **kwargs
        )


class VernikaDropdown(Dropdown):
    """
    Custom dropdown with Vernika styling.
    """

    def __init__(
        self,
        label: str = "",
        options: list = None,
        value: str = "",
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(
            label=label,
            value=value,
            on_change=on_change,
            border_radius=8,
            border_color="#2E86AB",
            focused_border_color="#2E86AB",
            **kwargs
        )

        if options:
            for opt in options:
                if isinstance(opt, tuple):
                    self.options.append(ft.dropdown.Option(opt[0], opt[1]))
                else:
                    self.options.append(ft.dropdown.Option(opt))


class VernikaCheckbox(Checkbox):
    """
    Custom checkbox with Vernika styling.
    """

    def __init__(
        self,
        label: str = "",
        value: bool = False,
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(
            label=label,
            value=value,
            on_change=on_change,
            check_color="#FFFFFF",
            active_color="#2E86AB",
            **kwargs
        )


class VernikaButton(ElevatedButton):
    """
    Custom elevated button with Vernika styling.
    """

    def __init__(
        self,
        text: str = "",
        icon: str = "",
        on_click: Optional[Callable] = None,
        disabled: bool = False,
        expand: bool = False,
        bgcolor: str = "#2E86AB",
        color: str = "#FFFFFF",
        **kwargs
    ):
        super().__init__(
            text=text,
            icon=icon,
            on_click=on_click,
            disabled=disabled,
            expand=expand,
            bgcolor=bgcolor,
            color=color,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
            **kwargs
        )


class VernikaOutlinedButton(OutlinedButton):
    """
    Custom outlined button with Vernika styling.
    """

    def __init__(
        self,
        text: str = "",
        icon: str = "",
        on_click: Optional[Callable] = None,
        disabled: bool = False,
        expand: bool = False,
        **kwargs
    ):
        super().__init__(
            text=text,
            icon=icon,
            on_click=on_click,
            disabled=disabled,
            expand=expand,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
            **kwargs
        )


class FormContainer(Container):
    """
    Container for form fields with consistent spacing and styling.
    """

    def __init__(
        self,
        fields: list = None,
        spacing: int = 15,
        padding: int = 20,
        **kwargs
    ):
        super().__init__(
            padding=padding,
            border_radius=12,
            bgcolor="#FFFFFF",
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color="#00000010",
            ),
            **kwargs
        )

        self.form_fields = Column(
            controls=fields or [],
            spacing=spacing,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.content = self.form_fields

    def add_field(self, field):
        """Add a field to the form."""
        self.form_fields.controls.append(field)
        self.form_fields.update()

    def remove_field(self, field):
        """Remove a field from the form."""
        if field in self.form_fields.controls:
            self.form_fields.controls.remove(field)
            self.form_fields.update()

    def clear_fields(self):
        """Clear all fields from the form."""
        self.form_fields.controls.clear()
        self.form_fields.update()

    def get_values(self) -> dict:
        """Get values from all fields."""
        values = {}
        for field in self.form_fields.controls:
            if hasattr(field, 'value'):
                values[field.label] = field.value
        return values

    def validate(self) -> bool:
        """Validate all fields."""
        is_valid = True
        for field in self.form_fields.controls:
            if hasattr(field, 'validate'):
                if not field.validate():
                    is_valid = False
        return is_valid
