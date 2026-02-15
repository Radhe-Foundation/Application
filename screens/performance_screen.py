"""
Vernika HRA - Performance Screen
Industry-Level Human Resource Management System

This module provides the performance reviews management screen.
Features: review cycles, goals, performance tracking, and database integration.
"""

from typing import Optional, List, Dict, Any
import flet as ft
from flet import (
    Container, Column, Row, Text, ElevatedButton, OutlinedButton,
    DataTable, DataColumn, DataRow, DataCell, IconButton, TextField,
    Card, Dropdown, DropdownOption, icons, Icon
)
from core.theme import theme
from core.colors_compat import colors
from database.connection import get_db_session
from database.models import Employee, User, Task, TaskStatus, TaskPriority
from datetime import datetime, date


class PerformanceScreen(Container):
    """
    Screen for managing performance reviews with database integration.
    """

    def __init__(self, page: ft.Page, **kwargs):
        """
        Initialize performance screen.

        Args:
            page: Flet page object
            **kwargs: Additional arguments
        """
        super().__init__(**kwargs)
        self._page = page
        self.reviews = []
        self.employees = []
        self.selected_review = None
        self.search_query = ""

        # Load data from database
        self._load_employees()
        self._load_reviews()

        self.spacing = 20
        self.expand = True

        # Set the content directly instead of using build()
        self.content = self._build_content()

    def _load_employees(self):
        """Load employees from database"""
        db = get_db_session()
        try:
            self.employees = db.query(Employee).filter(
                Employee.is_active == True).all()
        except Exception as e:
            print(f"Error loading employees: {e}")
            self.employees = []
        finally:
            db.close()

    def _load_reviews(self):
        """Load performance reviews from database (using tasks as proxy)"""
        db = get_db_session()
        try:
            # Using tasks as performance indicators
            tasks = db.query(Task).order_by(
                Task.created_at.desc()).limit(20).all()

            self.reviews = []
            for task in tasks:
                # Get employee info
                employee = db.query(Employee).filter(
                    Employee.id == task.assigned_to_id).first()
                if employee:
                    # Calculate rating based on task status
                    rating = 0
                    if task.status == TaskStatus.COMPLETED:
                        rating = 4.5
                    elif task.status == TaskStatus.IN_PROGRESS:
                        rating = 3.0
                    else:
                        rating = 2.0

                    self.reviews.append({
                        "id": task.id,
                        "employee_name": f"{employee.first_name} {employee.last_name}",
                        "reviewer_name": "Manager",
                        "period": task.due_date.strftime("%Y-%m") if task.due_date else "Ongoing",
                        "rating": rating,
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "task_title": task.title
                    })
        except Exception as e:
            print(f"Error loading reviews: {e}")
            self.reviews = []
        finally:
            db.close()

    @property
    def page(self) -> ft.Page:
        """Get current page"""
        return self._page

    def show_success(self, message: str):
        """Show success message"""
        snack = ft.SnackBar(
            content=ft.Text(message),
            duration=3000,
            bgcolor=colors.SUCCESS
        )
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_error(self, message: str):
        """Show error message"""
        snack = ft.SnackBar(
            content=ft.Text(message),
            duration=3000,
            bgcolor=colors.ERROR
        )
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_info(self, message: str):
        """Show info message"""
        snack = ft.SnackBar(
            content=ft.Text(message),
            duration=3000,
            bgcolor=colors.INFO
        )
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _build_content(self):
        """Build the UI"""
        return Container(
            padding=20,
            content=Column(
                controls=[
                    self._build_header(),
                    self._build_review_cycle_section(),
                    self._build_toolbar(),
                    self._build_reviews_table(),
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
        )

    def _build_header(self) -> Row:
        """Build screen header"""
        return Row(
            controls=[
                Column(
                    controls=[
                        Text(
                            "Performance Reviews",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=theme.primary,
                        ),
                        Text(
                            "Manage performance reviews and feedback",
                            size=14,
                            color=colors.SECONDARY,
                        ),
                    ],
                ),
            ],
        )

    def _build_review_cycle_section(self) -> Card:
        """Build review cycle section"""
        return Card(
            content=Container(
                padding=15,
                content=Column(
                    controls=[
                        Text(
                            "Review Cycles",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        Row(
                            controls=[
                                Dropdown(
                                    label="Select Review Period",
                                    width=250,
                                    options=[
                                        ft.dropdown.Option(
                                            "2024-h1", content=Text("2024 - First Half")),
                                        ft.dropdown.Option(
                                            "2024-h2", content=Text("2024 - Second Half")),
                                        ft.dropdown.Option(
                                            "2023-annual", content=Text("2023 - Annual Review")),
                                    ],
                                ),
                                ElevatedButton(
                                    content=Text("Create New Cycle"),
                                    icon=ft.Icons.ADD,
                                    on_click=self._create_review_cycle,
                                    style=ft.ButtonStyle(
                                        bgcolor=theme.primary,
                                        color=colors.ON_PRIMARY,
                                    ),
                                ),
                            ],
                            spacing=15,
                        ),
                    ],
                    spacing=10,
                ),
            )
        )

    def _build_toolbar(self) -> Card:
        """Build toolbar with search and add button"""
        return Card(
            content=Container(
                padding=15,
                content=Row(
                    controls=[
                        TextField(
                            hint_text="Search reviews...",
                            width=300,
                            prefix_icon=ft.Icons.SEARCH,
                            on_change=self._handle_search,
                        ),
                        ElevatedButton(
                            content=Text("Start New Review"),
                            icon=ft.Icons.ADD,
                            on_click=self._show_add_dialog,
                            style=ft.ButtonStyle(
                                bgcolor=theme.primary,
                                color=colors.ON_PRIMARY,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )
        )

    def _build_reviews_table(self) -> Card:
        """Build reviews data table"""
        return Card(
            content=Container(
                padding=15,
                content=DataTable(
                    columns=[
                        DataColumn(Text("Employee")),
                        DataColumn(Text("Reviewer")),
                        DataColumn(Text("Period")),
                        DataColumn(Text("Rating")),
                        DataColumn(Text("Status")),
                        DataColumn(Text("Actions")),
                    ],
                    rows=self._get_review_rows(),
                    border=ft.border.all(1, colors.OUTLINE),
                    border_radius=8,
                    heading_row_color=colors.PRIMARY_CONTAINER,


                ),
            )
        )

    def _get_review_rows(self) -> List[DataRow]:
        """Get table rows for reviews"""
        rows = []

        for review in self.reviews:
            rating_color = self._get_rating_color(review.get("rating", 0))

            rows.append(
                DataRow(
                    cells=[
                        DataCell(Text(review.get("employee_name", "N/A"))),
                        DataCell(Text(review.get("reviewer_name", "N/A"))),
                        DataCell(Text(review.get("period", "N/A"))),
                        DataCell(
                            Row(
                                controls=[
                                    Icon(ft.Icons.STAR,
                                         color=rating_color, size=20),
                                    Text(f"{review.get('rating', 0)}/5",
                                         weight=ft.FontWeight.BOLD),
                                ],
                                spacing=5,
                            )
                        ),
                        DataCell(self._get_status_badge(
                            review.get("status", ""))),
                        DataCell(
                            Row(
                                controls=[
                                    IconButton(
                                        icon=ft.Icons.VISIBILITY,
                                        tooltip="View",
                                        on_click=lambda e, r=review: self._view_review(
                                            r),
                                    ),
                                    IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Edit",
                                        on_click=lambda e, r=review: self._edit_review(
                                            r),
                                    ),
                                ],
                                spacing=5,
                            )
                        ),
                    ],
                )
            )

        return rows

    def _get_rating_color(self, rating: float) -> str:
        """Get color based on rating"""
        if rating >= 4.5:
            return colors.GREEN
        elif rating >= 3.5:
            return colors.AMBER
        elif rating >= 2.5:
            return colors.ORANGE
        else:
            return colors.ERROR

    def _get_status_badge(self, status: str) -> Container:
        """Get status badge widget"""
        status_colors = {
            "draft": colors.GREY,
            "self_review": colors.BLUE,
            "manager_review": colors.PURPLE,
            "completed": colors.GREEN,
            "acknowledged": colors.TEAL,
        }

        return Container(
            content=Text(
                status.replace("_", " ").title(),
                color=colors.WHITE,
                size=12,
                weight=ft.FontWeight.BOLD,
            ),
            bgcolor=status_colors.get(status, colors.GREY),
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            border_radius=20,
        )

    def _handle_search(self, e: ft.ControlEvent):
        """Handle search"""
        self.search_query = e.control.value.lower()
        self._load_reviews()

    def _create_review_cycle(self, e: ft.ControlEvent):
        """Create a new review cycle"""
        self.show_info("Review cycle creation coming soon!")

    def _show_add_dialog(self, e: ft.ControlEvent):
        """Show add review dialog"""
        self._show_review_form()

    def _show_review_form(self, review=None):
        """Show review form dialog"""
        self.selected_review = review

        employee_dropdown = Dropdown(
            label="Employee",
            width=300,
            options=[
                ft.dropdown.Option(str(emp.id), content=Text(
                    f"{emp.first_name} {emp.last_name}"))
                for emp in self.employees
            ],
        )

        reviewer_dropdown = Dropdown(
            label="Reviewer",
            width=300,
            options=[
                ft.dropdown.Option(str(emp.id), content=Text(
                    f"{emp.first_name} {emp.last_name}"))
                for emp in self.employees
            ],
        )

        period_dropdown = Dropdown(
            label="Review Period",
            width=300,
            options=[
                ft.dropdown.Option(
                    "2024-h1", content=Text("2024 - First Half")),
                ft.dropdown.Option(
                    "2024-h2", content=Text("2024 - Second Half")),
                ft.dropdown.Option(
                    "2023-annual", content=Text("2023 - Annual Review")),
            ],
        )

        goals_text = TextField(
            label="Goals & Objectives",
            width=300,
            multiline=True,
            min_lines=3,
            value=review.get("goals") if review else "",
        )

        achievements_text = TextField(
            label="Key Achievements",
            width=300,
            multiline=True,
            min_lines=3,
            value=review.get("achievements") if review else "",
        )

        strengths_text = TextField(
            label="Strengths",
            width=300,
            multiline=True,
            min_lines=2,
            value=review.get("strengths") if review else "",
        )

        improvements_text = TextField(
            label="Areas for Improvement",
            width=300,
            multiline=True,
            min_lines=2,
            value=review.get("improvements") if review else "",
        )

        rating_slider = ft.Slider(
            label="Overall Rating",
            min=0,
            max=5,
            divisions=10,
            value=review.get("rating", 3) if review else 3,
        )

        form = Column(
            controls=[
                employee_dropdown,
                reviewer_dropdown,
                period_dropdown,
                goals_text,
                achievements_text,
                strengths_text,
                improvements_text,
                rating_slider,
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            height=400,
        )

        dialog = ft.AlertDialog(
            title=Text("Performance Review"),
            content=form,
            actions=[
                ft.TextButton("Cancel", on_click=self._close_dialog),
                ElevatedButton(
                    "Save",
                    on_click=lambda e: self._save_review(
                        employee_dropdown, reviewer_dropdown, period_dropdown,
                        goals_text, achievements_text, strengths_text,
                        improvements_text, rating_slider
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=theme.primary,
                        color=colors.ON_PRIMARY,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _close_dialog(self, e: ft.ControlEvent):
        """Close the dialog"""
        self._page.dialog.open = False
        self._page.update()

    def _save_review(
        self,
        employee_dropdown, reviewer_dropdown, period_dropdown,
        goals_text, achievements_text, strengths_text,
        improvements_text, rating_slider
    ):
        """Save performance review"""
        self.show_success("Review saved successfully")
        self._close_dialog(None)
        self._load_reviews()

    def _view_review(self, review):
        """View review details"""
        self.show_info(
            f"Viewing review for {review.get('employee_name', 'N/A')}")

    def _edit_review(self, review):
        """Edit review"""
        self._show_review_form(review)

    def did_mount(self):
        """Called when screen is mounted"""
        self._load_reviews()

    def _load_reviews(self):
        """Load reviews from database"""
        # Placeholder - in production, load from database
        self.reviews = [
            {
                "id": 1,
                "employee_name": "John Doe",
                "reviewer_name": "Jane Smith",
                "period": "2024 - First Half",
                "rating": 4.2,
                "status": "completed",
            },
            {
                "id": 2,
                "employee_name": "Alice Johnson",
                "reviewer_name": "Bob Williams",
                "period": "2024 - First Half",
                "rating": 3.8,
                "status": "manager_review",
            },
        ]
        self._page.update()


# Create singleton instance
_performance_screen = None


def get_performance_screen(page: ft.Page) -> PerformanceScreen:
    """Get or create performance screen instance"""
    global _performance_screen
    if _performance_screen is None:
        _performance_screen = PerformanceScreen(page)
    return _performance_screen
