"""
Vernika HRA - Holidays Screen
Industry-Level Human Resource Management System

This module provides holiday management functionality.
"""

from typing import List, Dict
import flet as ft
from datetime import datetime, date
from database.connection import get_db_session


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
ERROR = "#F44336"
INFO = "#2196F3"


class Holiday:
    """Holiday data class"""

    def __init__(self, id: int, name: str, date_str: str, day: str, type: str, optional: bool = False):
        self.id = id
        self.name = name
        self.date = date_str
        self.day = day
        self.type = type  # national, festival, company
        self.optional = optional


class HolidaysScreen(ft.Container):
    """Holiday management screen"""

    def __init__(self, page, current_user=None):
        super().__init__()
        self._page = page
        self.current_user = current_user
        self.expand = True
        self.bgcolor = "#F5F5F5"

        # Default holidays for 2024-2025
        self.holidays = self._get_default_holidays()

        # Build UI
        self.content = self._build_content()

    def _get_default_holidays(self) -> List[Holiday]:
        """Get default holiday list (would come from DB in production)"""
        return [
            Holiday(1, "New Year's Day", "2025-01-01",
                    "Wednesday", "national"),
            Holiday(2, "Republic Day", "2025-01-26", "Sunday", "national"),
            Holiday(3, "Maha Shivaratri", "2025-02-26",
                    "Wednesday", "festival"),
            Holiday(4, "Holi", "2025-03-14", "Friday", "festival"),
            Holiday(5, "Good Friday", "2025-04-18", "Friday", "national"),
            Holiday(6, "Easter", "2025-04-20", "Sunday", "festival"),
            Holiday(7, "Ramzan/Eid", "2025-03-31", "Monday", "festival"),
            Holiday(8, "May Day", "2025-05-01", "Thursday", "national"),
            Holiday(9, "Independence Day", "2025-08-15", "Friday", "national"),
            Holiday(10, "Ganesh Chaturthi", "2025-08-27",
                    "Wednesday", "festival"),
            Holiday(11, "Diwali", "2025-10-20", "Monday", "festival"),
            Holiday(12, "Christmas", "2025-12-25", "Thursday", "national"),
            Holiday(13, "Company Foundation Day", "2025-06-15",
                    "Sunday", "company", optional=True),
            Holiday(14, "Annual Day", "2025-12-01",
                    "Monday", "company", optional=True),
        ]

    def _build_content(self):
        """Build main content"""
        return ft.Container(
            content=ft.Column([
                self._build_header(),
                self._build_year_selector(),
                self._build_stats(),
                self._build_holidays_list(),
            ], expand=True, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
        )

    def _build_header(self):
        """Build header"""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Company Holidays", size=24,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Text("Manage company holidays and calendar",
                            size=14, color="#666"),
                ]),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Add Holiday",
                    icon=ft.Icons.ADD,
                    on_click=self._show_add_dialog,
                    style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE"),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=20),
        )

    def _build_year_selector(self):
        """Build year selector"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH, color=PRIMARY),
                ft.Text("Year:", size=14),
                ft.Container(width=10),
                ft.Dropdown(
                    width=120,
                    value="2025",
                    options=[
                        ft.dropdown.Option("2024", "2024"),
                        ft.dropdown.Option("2025", "2025"),
                        ft.dropdown.Option("2026", "2026"),
                    ],
                ),
                ft.Container(expand=True),
                ft.Text("Click on a holiday to see details",
                        size=12, color="#999"),
            ]),
            padding=ft.padding.only(bottom=15),
        )

    def _build_stats(self):
        """Build statistics cards"""
        total = len(self.holidays)
        national = sum(1 for h in self.holidays if h.type == "national")
        festival = sum(1 for h in self.holidays if h.type == "festival")
        company = sum(1 for h in self.holidays if h.type == "company")

        return ft.Container(
            content=ft.Row([
                self._create_stat_card("Total Holidays", str(
                    total), ft.Icons.EVENT, PRIMARY),
                self._create_stat_card("National", str(
                    national), ft.Icons.FLAG, SUCCESS),
                self._create_stat_card("Festivals", str(
                    festival), ft.Icons.CELEBRATION, WARNING),
                self._create_stat_card("Company", str(
                    company), ft.Icons.BUSINESS, INFO),
            ], spacing=15),
            padding=ft.padding.only(bottom=20),
        )

    def _create_stat_card(self, title: str, value: str, icon, color: str):
        """Create a stat card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=24, color=color),
                    ft.Column([
                        ft.Text(value, size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(title, size=11, color="#666"),
                    ], spacing=0),
                ], spacing=10),
                padding=15,
            ),
            width=150,
        )

    def _build_holidays_list(self):
        """Build holidays list"""
        if not self.holidays:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=64, color="#BDBDBD"),
                    ft.Text("No holidays configured",
                            size=16, color="#757575"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                padding=50,
            )

        # Group by month
        months = {}
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]

        for holiday in self.holidays:
            try:
                dt = datetime.strptime(holiday.date, "%Y-%m-%d")
                month = dt.month
                if month not in months:
                    months[month] = []
                months[month].append(holiday)
            except:
                pass

        # Build month sections
        month_sections = []
        for month_num in sorted(months.keys()):
            holidays = months[month_num]
            month_name = month_names[month_num]

            holiday_rows = []
            for h in holidays:
                card = self._create_holiday_card(h)
                holiday_rows.append(card)

            month_sections.append(
                ft.Column([
                    ft.Text(f"{month_name} 2025", size=16,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Container(height=8),
                    ft.Column(holiday_rows, spacing=8),
                    ft.Container(height=15),
                ])
            )

        return ft.Column(month_sections, spacing=0)

    def _create_holiday_card(self, holiday: Holiday):
        """Create a holiday card"""
        # Type colors
        type_colors = {
            "national": PRIMARY,
            "festival": WARNING,
            "company": INFO,
        }
        color = type_colors.get(holiday.type, PRIMARY)

        # Type icons
        type_icons = {
            "national": ft.Icons.FLAG,
            "festival": ft.Icons.CELEBRATION,
            "company": ft.Icons.BUSINESS,
        }
        icon = type_icons.get(holiday.type, ft.Icons.EVENT)

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    # Date box
                    ft.Container(
                        content=ft.Column([
                            ft.Text(holiday.date.split(
                                "-")[2], size=20, weight=ft.FontWeight.BOLD, color=color),
                            ft.Text(holiday.day[:3], size=11, color="#666"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=50,
                        padding=10,
                        bgcolor=f"{color}15",
                        border_radius=8,
                    ),
                    # Holiday info
                    ft.Column([
                        ft.Text(holiday.name, size=15,
                                weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Icon(icon, size=14, color=color),
                            ft.Text(holiday.type.title(),
                                    size=12, color=color),
                            ft.Container(width=15),
                            ft.Icon(ft.Icons.CALENDAR_TODAY,
                                    size=14, color="#666"),
                            ft.Text(holiday.date, size=12, color="#666"),
                        ], spacing=5),
                    ], expand=True),
                    # Optional badge
                    ft.Container(
                        content=ft.Text("Optional", size=10, color="#666"),
                        visible=holiday.optional,
                        bgcolor="#FFF3E0",
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=10,
                    ),
                    # Actions
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=PRIMARY,
                            tooltip="Edit",
                            on_click=lambda e, h=holiday: self._edit_holiday(
                                h),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ERROR,
                            tooltip="Delete",
                            on_click=lambda e, h=holiday: self._delete_holiday(
                                h),
                        ),
                    ], spacing=0),
                ], spacing=15),
                padding=15,
            ),
            elevation=1,
        )

    def _change_year(self, e):
        """Change year"""
        self._show_info(f"Showing holidays for {e.control.value}")

    def _show_add_dialog(self, e=None):
        """Show add holiday dialog"""
        name_field = ft.TextField(label="Holiday Name *", width=300)
        date_field = ft.TextField(label="Date (YYYY-MM-DD) *", width=200)
        day_field = ft.TextField(label="Day *", width=150)

        type_dropdown = ft.Dropdown(
            label="Type",
            width=200,
            options=[
                ft.dropdown.Option("national", "National Holiday"),
                ft.dropdown.Option("festival", "Festival"),
                ft.dropdown.Option("company", "Company Holiday"),
            ],
        )

        optional_switch = ft.Switch(label="Optional Holiday", value=False)

        def save(e):
            if not name_field.value or not date_field.value or not day_field.value:
                self._show_error("All fields are required!")
                return

            self._show_success(f"Holiday '{name_field.value}' added!")
            self._close_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("Add Holiday"),
            content=ft.Column([
                name_field,
                date_field,
                day_field,
                type_dropdown,
                optional_switch,
            ], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Add", on_click=save, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="WHITE")),
            ],
        )

        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _edit_holiday(self, holiday: Holiday):
        """Edit a holiday"""
        self._show_info(f"Edit: {holiday.name}")

    def _delete_holiday(self, holiday: Holiday):
        """Delete a holiday"""
        def confirm(e):
            self._show_success(f"Holiday '{holiday.name}' deleted!")
            self._close_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Holiday?"),
            content=ft.Text(
                f"Are you sure you want to delete '{holiday.name}'?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm, style=ft.ButtonStyle(
                    bgcolor=ERROR, color="WHITE")),
            ],
        )

        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _close_dialog(self):
        """Close dialog"""
        if self._page.dialog:
            self._page.dialog.open = False
        self._page.update()

    def _show_success(self, message):
        """Show success message"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, message):
        """Show error message"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=ERROR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_info(self, message):
        """Show info message"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=INFO)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_holidays(page, user=None):
    """Helper to show holidays screen"""
    page.clean()
    page.add(HolidaysScreen(page, user))
    page.update()
