"""
Vernika HRA - Holidays Screen
Industry-Level Human Resource Management System

This module provides holiday management functionality.
"""

from typing import List, Dict
import flet as ft
from datetime import datetime, date
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Holiday


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
ERROR = "#F44336"
INFO = "#2196F3"


class HolidaysScreen(ft.Container):
    """Holiday management screen"""

    def __init__(self, page, current_user=None):
        super().__init__()
        self._page = page
        self.current_user = current_user
        self.expand = True
        self.bgcolor = "#F5F5F5"

        # Get holidays from database
        self.holidays = self._get_holidays_from_db()

        # Build UI
        self.content = self._build_content()

    def _get_holidays_from_db(self) -> List:
        """Get holidays from database"""
        current_year = datetime.now().year
        db = get_db_session()
        try:
            holidays = db.query(Holiday).filter(
                Holiday.is_active == True,
                Holiday.year == current_year
            ).order_by(Holiday.date).all()
            return holidays
        except Exception as e:
            print(f"Error loading holidays: {e}")
            return []
        finally:
            db.close()

    def _get_default_holidays(self) -> List:
        """Get default holiday list and save to database"""
        defaults = [
            {"name": "New Year's Day", "date": "2025-01-01",
                "day": "Wednesday", "type": "national", "optional": False},
            {"name": "Republic Day", "date": "2025-01-26",
                "day": "Sunday", "type": "national", "optional": False},
            {"name": "Maha Shivaratri", "date": "2025-02-26",
                "day": "Wednesday", "type": "festival", "optional": False},
            {"name": "Holi", "date": "2025-03-14", "day": "Friday",
                "type": "festival", "optional": False},
            {"name": "Good Friday", "date": "2025-04-18",
                "day": "Friday", "type": "national", "optional": False},
            {"name": "Easter", "date": "2025-04-20", "day": "Sunday",
                "type": "festival", "optional": False},
            {"name": "Ramzan/Eid", "date": "2025-03-31",
                "day": "Monday", "type": "festival", "optional": False},
            {"name": "May Day", "date": "2025-05-01", "day": "Thursday",
                "type": "national", "optional": False},
            {"name": "Independence Day", "date": "2025-08-15",
                "day": "Friday", "type": "national", "optional": False},
            {"name": "Ganesh Chaturthi", "date": "2025-08-27",
                "day": "Wednesday", "type": "festival", "optional": False},
            {"name": "Diwali", "date": "2025-10-20", "day": "Monday",
                "type": "festival", "optional": False},
            {"name": "Christmas", "date": "2025-12-25",
                "day": "Thursday", "type": "national", "optional": False},
            {"name": "Company Foundation Day", "date": "2025-06-15",
                "day": "Sunday", "type": "company", "optional": True},
            {"name": "Annual Day", "date": "2025-12-01",
                "day": "Monday", "type": "company", "optional": True},
        ]

        # Save defaults to database
        db = get_db_session()
        try:
            for h in defaults:
                # Check if already exists
                existing = db.query(Holiday).filter(
                    Holiday.name == h["name"],
                    Holiday.year == 2025
                ).first()

                if not existing:
                    holiday = Holiday(
                        name=h["name"],
                        date=datetime.strptime(h["date"], "%Y-%m-%d").date(),
                        day=h["day"],
                        holiday_type=h["type"],
                        is_optional=h["optional"],
                        year=2025,
                        is_active=True
                    )
                    db.add(holiday)
            db.commit()
        except Exception as e:
            print(f"Error saving default holidays: {e}")
            db.rollback()
        finally:
            db.close()

        return self._get_holidays_from_db()

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
        # Initialize year to current year if not exists
        current_year = datetime.now().year
        if not hasattr(self, 'selected_year'):
            self.selected_year = {"value": str(current_year)}

        def create_year_button(year):
            is_selected = self.selected_year["value"] == year
            return ft.Container(
                content=ft.ElevatedButton(
                    year,
                    on_click=lambda e, y=year: self._change_year(y),
                    style=ft.ButtonStyle(
                        bgcolor=PRIMARY if is_selected else "#E0E0E0",
                        color="WHITE" if is_selected else "#333",
                    ),
                ),
                padding=5,
            )

        # Generate years dynamically
        years = [str(current_year - 1), str(current_year),
                 str(current_year + 1)]

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH, color=PRIMARY),
                ft.Text("Year:", size=14),
                ft.Container(width=10),
            ] + [create_year_button(y) for y in years] + [
                ft.Container(expand=True),
                ft.Text("Click on a holiday to see details",
                        size=12, color="#999"),
            ]),
            padding=ft.padding.only(bottom=15),
        )

    def _change_year(self, year):
        """Change year"""
        self.selected_year["value"] = year
        self._show_info(f"Showing holidays for {year}")
        self.content = self._build_content()
        self._page.update()

    def _build_stats(self):
        """Build statistics cards"""
        # Filter holidays by selected year
        current_year = int(self.selected_year.get(
            "value", datetime.now().year))
        year_holidays = []
        for holiday in self.holidays:
            try:
                if isinstance(holiday.date, str):
                    dt = datetime.strptime(holiday.date, "%Y-%m-%d")
                else:
                    dt = holiday.date
                if dt.year == current_year:
                    year_holidays.append(holiday)
            except Exception:
                pass

        total = len(year_holidays)
        national = sum(
            1 for h in year_holidays if h.holiday_type == "national")
        festival = sum(
            1 for h in year_holidays if h.holiday_type == "festival")
        company = sum(1 for h in year_holidays if h.holiday_type == "company")

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
        # Get current year and filter holidays
        current_year = int(self.selected_year.get(
            "value", datetime.now().year))

        # Filter holidays by selected year
        filtered_holidays = []
        for holiday in self.holidays:
            try:
                if isinstance(holiday.date, str):
                    dt = datetime.strptime(holiday.date, "%Y-%m-%d")
                else:
                    dt = holiday.date
                if dt.year == current_year:
                    filtered_holidays.append(holiday)
            except Exception:
                pass

        if not filtered_holidays:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=64, color="#BDBDBD"),
                    ft.Text(f"No holidays configured for {current_year}",
                            size=16, color="#757575"),
                    ft.Text("Click 'Add Holiday' to add holidays",
                            size=12, color="#999"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                padding=50,
            )

        # Group by month
        months = {}
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]

        for holiday in filtered_holidays:
            try:
                if isinstance(holiday.date, str):
                    dt = datetime.strptime(holiday.date, "%Y-%m-%d")
                else:
                    dt = holiday.date
                month = dt.month
                if month not in months:
                    months[month] = []
                months[month].append(holiday)
            except Exception:
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
                    ft.Text(f"{month_name} {current_year}", size=16,
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
        # Handle both holiday_type and type fields
        holiday_type = getattr(holiday, 'holiday_type', None) or getattr(
            holiday, 'type', 'national') or 'national'
        color = type_colors.get(holiday_type, PRIMARY)

        # Type icons
        type_icons = {
            "national": ft.Icons.FLAG,
            "festival": ft.Icons.CELEBRATION,
            "company": ft.Icons.BUSINESS,
        }
        icon = type_icons.get(holiday_type, ft.Icons.EVENT)

        # Handle date - can be string or date object
        try:
            if isinstance(holiday.date, str):
                date_parts = holiday.date.split("-")
                day_str = date_parts[2] if len(date_parts) >= 3 else "??"
                date_str = holiday.date
            else:
                day_str = str(holiday.date.day).zfill(2)
                date_str = str(holiday.date)
        except:
            day_str = "??"
            date_str = str(holiday.date)

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    # Date box
                    ft.Container(
                        content=ft.Column([
                            ft.Text(day_str, size=20,
                                    weight=ft.FontWeight.BOLD, color=color),
                            ft.Text((holiday.day or "")[
                                    :3], size=11, color="#666"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=50,
                        padding=10,
                        bgcolor=f"{color}15",
                        border_radius=8,
                    ),
                    # Holiday info
                    ft.Column([
                        ft.Text(holiday.name or "Unnamed Holiday", size=15,
                                weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Icon(icon, size=14, color=color),
                            ft.Text(holiday_type.title(),
                                    size=12, color=color),
                            ft.Container(width=15),
                            ft.Icon(ft.Icons.CALENDAR_TODAY,
                                    size=14, color="#666"),
                            ft.Text(date_str, size=12, color="#666"),
                        ], spacing=5),
                    ], expand=True),
                    # Optional badge
                    ft.Container(
                        content=ft.Text("Optional", size=10, color="#666"),
                        visible=bool(getattr(holiday, 'is_optional', False) or getattr(
                            holiday, 'optional', False)),
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

    def _show_add_dialog(self, e=None):
        """Show add holiday dialog"""
        name_field = ft.TextField(label="Holiday Name *", width=300)
        date_field = ft.TextField(label="Date (YYYY-MM-DD) *", width=200)
        day_field = ft.TextField(label="Day *", width=150)

        # Use RadioGroup for holiday type selection
        type_group = ft.RadioGroup(
            value="national",
            content=ft.Column([
                ft.Radio(value="national", label="National Holiday"),
                ft.Radio(value="festival", label="Festival"),
                ft.Radio(value="company", label="Company Holiday"),
            ], spacing=5)
        )

        optional_switch = ft.Switch(label="Optional Holiday", value=False)

        def save(e):
            if not name_field.value or not date_field.value or not day_field.value:
                self._show_error("All fields are required!")
                return

            # Validate and parse date
            try:
                holiday_date = datetime.strptime(
                    date_field.value, "%Y-%m-%d").date()
            except ValueError:
                self._show_error("Invalid date format! Use YYYY-MM-DD")
                return

            # Get current year
            current_year = datetime.now().year

            # Save to database
            db = get_db_session()
            try:
                new_holiday = Holiday(
                    name=name_field.value,
                    date=holiday_date,
                    day=day_field.value,
                    holiday_type=type_group.value or "national",
                    is_optional=optional_switch.value,
                    year=current_year,
                    is_active=True
                )
                db.add(new_holiday)
                db.commit()

                # Refresh holidays list
                self.holidays = self._get_holidays_from_db()

                self._show_success(f"Holiday '{name_field.value}' added!")
                self._close_dialog()
                # Refresh the UI
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error saving holiday: {str(ex)}")
                db.rollback()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Add Holiday"),
            content=ft.Column([
                name_field,
                date_field,
                day_field,
                ft.Text("Type", size=12, weight=ft.FontWeight.W_500),
                type_group,
                optional_switch,
            ], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Add", on_click=save, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="WHITE")),
            ],
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _edit_holiday(self, holiday: Holiday):
        """Edit a holiday - opens edit dialog"""
        name_field = ft.TextField(
            label="Holiday Name *", width=300, value=holiday.name)
        date_field = ft.TextField(
            label="Date (YYYY-MM-DD) *", width=200, value=str(holiday.date))
        day_field = ft.TextField(label="Day *", width=150, value=holiday.day)

        # Use RadioGroup for holiday type selection
        type_group = ft.RadioGroup(
            value=holiday.holiday_type or "national",
            content=ft.Column([
                ft.Radio(value="national", label="National Holiday"),
                ft.Radio(value="festival", label="Festival"),
                ft.Radio(value="company", label="Company Holiday"),
            ], spacing=5)
        )

        optional_switch = ft.Switch(
            label="Optional Holiday", value=holiday.is_optional or False)

        def update(e):
            if not name_field.value or not date_field.value or not day_field.value:
                self._show_error("All fields are required!")
                return

            # Validate and parse date
            try:
                holiday_date = datetime.strptime(
                    date_field.value, "%Y-%m-%d").date()
            except ValueError:
                self._show_error("Invalid date format! Use YYYY-MM-DD")
                return

            # Update in database
            db = get_db_session()
            try:
                db_holiday = db.query(Holiday).filter(
                    Holiday.id == holiday.id).first()
                if db_holiday:
                    db_holiday.name = name_field.value
                    db_holiday.date = holiday_date
                    db_holiday.day = day_field.value
                    db_holiday.holiday_type = type_group.value
                    db_holiday.is_optional = optional_switch.value
                    db.commit()

                    # Refresh holidays list
                    self.holidays = self._get_holidays_from_db()

                self._show_success(f"Holiday '{name_field.value}' updated!")
                self._close_dialog()
                # Refresh the UI
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error updating holiday: {str(ex)}")
                db.rollback()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Holiday"),
            content=ft.Column([
                name_field,
                date_field,
                day_field,
                ft.Text("Type", size=12, weight=ft.FontWeight.W_500),
                type_group,
                optional_switch,
            ], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Update", on_click=update, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="WHITE")),
            ],
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _delete_holiday(self, holiday: Holiday):
        """Delete a holiday"""
        def confirm(e):
            # Delete from database
            db = get_db_session()
            try:
                db_holiday = db.query(Holiday).filter(
                    Holiday.id == holiday.id).first()
                if db_holiday:
                    db.delete(db_holiday)
                    db.commit()

                    # Refresh holidays list
                    self.holidays = self._get_holidays_from_db()

                self._show_success(f"Holiday '{holiday.name}' deleted!")
                self._close_dialog()
                # Refresh the UI
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error deleting holiday: {str(ex)}")
                db.rollback()
            finally:
                db.close()

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

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self):
        """Close dialog"""
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
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
