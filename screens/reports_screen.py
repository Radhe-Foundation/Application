"""
Vernika HRA - Reports Screen
Industry-Level Human Resource Management System

This module provides the reports and analytics screen.
"""

from typing import Optional, List, Dict, Any
import flet as ft
from flet import (
    Container, Column, Row, Text, ElevatedButton, OutlinedButton,
    Card, Dropdown, DataTable, DataColumn, DataRow, DataCell, Icon, IconButton
)
from core.theme import theme
from core.colors_compat import colors
from database.connection import get_session
from datetime import datetime, timedelta


class ReportsScreen(Container):
    """
    Screen for reports and analytics.
    """

    def __init__(self, page: ft.Page, **kwargs):
        """
        Initialize reports screen.

        Args:
            page: Flet page object
            **kwargs: Additional arguments
        """
        super().__init__(**kwargs)
        self._page = page
        self.report_types = [
            "Employee Summary",
            "Attendance Report",
            "Leave Report",
            "Department Summary",
            "Performance Overview",
        ]

        self.spacing = 20
        self.expand = True

        # Set the content directly instead of using build()
        self.content = self._build_content()

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
                    self._build_report_selector(),
                    self._build_dashboard_stats(),
                    self._build_charts_section(),
                    self._build_recent_reports(),
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
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
                            "Reports & Analytics",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=theme.primary,
                        ),
                        Text(
                            "Generate and view HR reports",
                            size=14,
                            color=colors.SECONDARY,
                        ),
                    ],
                ),
            ],
        )

    def _build_report_selector(self) -> Card:
        """Build report type selector"""
        return Card(
            content=Container(
                padding=15,
                content=Column(
                    controls=[
                        Row(
                            controls=[
                                Dropdown(
                                    label="Select Report",
                                    width=250,
                                    options=[
                                        ft.dropdown.Option(
                                            key=opt.lower().replace(" ", "_"), text=opt)
                                        for opt in self.report_types
                                    ],
                                ),
                                Row(
                                    controls=[
                                        OutlinedButton(
                                            "Last 7Days",
                                            on_click=lambda e: self._set_date_range(
                                                "7days"),
                                        ),
                                        OutlinedButton(
                                            "Last 30 Days",
                                            on_click=lambda e: self._set_date_range(
                                                "30days"),
                                        ),
                                        OutlinedButton(
                                            "This Year",
                                            on_click=lambda e: self._set_date_range(
                                                "year"),
                                        ),
                                    ],
                                    spacing=10,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            wrap=True,
                        ),
                        Row(
                            controls=[
                                ElevatedButton(
                                    "Generate Report",
                                    on_click=self._generate_report,
                                    style=ft.ButtonStyle(
                                        bgcolor=theme.primary,
                                        color=colors.ON_PRIMARY,
                                    ),
                                ),
                                OutlinedButton(
                                    "Export",
                                    on_click=self._export_report,
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=15,
                ),
            )
        )

    def _build_dashboard_stats(self) -> Row:
        """Build dashboard statistics cards"""
        return Row(
            controls=[
                self._create_stat_card(
                    "Total Employees", "156", ft.Icons.PERSON, colors.BLUE),
                self._create_stat_card(
                    "Present Today", "142", ft.Icons.CHECK, colors.GREEN),
                self._create_stat_card(
                    "On Leave", "8", ft.Icons.TIMELAPSE, colors.ORANGE),
                self._create_stat_card(
                    "Absent", "6", ft.Icons.CLOSE, colors.RED),
            ],
            spacing=15,
        )

    def _create_stat_card(self, title: str, value: str, icon_name, color: str) -> Card:
        """Create a statistic card"""
        return Card(
            content=Container(
                padding=15,
                content=Row(
                    controls=[
                        Container(
                            content=Icon(icon_name, size=32, color=color),
                            bgcolor=f"{color}20",
                            padding=10,
                            border_radius=10,
                        ),
                        Column(
                            controls=[
                                Text(value, size=24, weight=ft.FontWeight.BOLD),
                                Text(title, size=12, color=colors.GREY),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=15,
                    alignment=ft.MainAxisAlignment.START,
                ),
            ),
            width=200,
        )

    def _build_charts_section(self) -> Row:
        """Build charts section"""
        return Row(
            controls=[
                self._build_attendance_card(),
                self._build_department_card(),
                self._build_leave_card(),
            ],
            spacing=15,
            wrap=True,
        )

    def _build_attendance_card(self) -> Card:
        """Build attendance placeholder card"""
        return Card(
            content=Container(
                padding=15,
                content=Column(
                    controls=[
                        Text("Attendance Trend", size=16,
                             weight=ft.FontWeight.BOLD),
                        Container(
                            content=Column(
                                controls=[
                                    Text("Mon: 95%", size=12),
                                    Text("Tue: 92%", size=12),
                                    Text("Wed: 88%", size=12),
                                    Text("Thu: 90%", size=12),
                                    Text("Fri: 94%", size=12),
                                    Text("Sat: 85%", size=12),
                                    Text("Sun: 78%", size=12),
                                ],
                            ),
                            height=200,
                        ),
                    ],
                    spacing=10,
                ),
            ),
            width=300,
        )

    def _build_department_card(self) -> Card:
        """Build department placeholder card"""
        return Card(
            content=Container(
                padding=15,
                content=Column(
                    controls=[
                        Text("Employees by Department", size=16,
                             weight=ft.FontWeight.BOLD),
                        Container(
                            content=Column(
                                controls=[
                                    Row([Icon(ft.Icons.SETTINGS, color=colors.BLUE), Text(
                                        "Engineering: 40%")], spacing=5),
                                    Row([Icon(ft.Icons.TRENDING_UP, color=colors.GREEN), Text(
                                        "Sales: 25%")], spacing=5),
                                    Row([Icon(ft.Icons.CAMPAIGN, color=colors.ORANGE), Text(
                                        "Marketing: 20%")], spacing=5),
                                    Row([Icon(ft.Icons.PEOPLE, color=colors.PURPLE), Text(
                                        "HR: 15%")], spacing=5),
                                ],
                            ),
                            height=200,
                        ),
                    ],
                    spacing=10,
                ),
            ),
            width=300,
        )

    def _build_leave_card(self) -> Card:
        """Build leave placeholder card"""
        return Card(
            content=Container(
                padding=15,
                content=Column(
                    controls=[
                        Text("Leave Types", size=16, weight=ft.FontWeight.BOLD),
                        Container(
                            content=Column(
                                controls=[
                                    Row([Icon(ft.Icons.BEACH_ACCESS, color=colors.BLUE), Text(
                                        "Annual Leave: 45 days")], spacing=5),
                                    Row([Icon(ft.Icons.HEALTH_AND_SAFETY, color=colors.GREEN), Text(
                                        "Sick Leave: 30 days")], spacing=5),
                                    Row([Icon(ft.Icons.PERSON, color=colors.ORANGE), Text(
                                        "Personal: 15 days")], spacing=5),
                                    Row([Icon(ft.Icons.MORE_VERT, color=colors.RED), Text(
                                        "Other: 8 days")], spacing=5),
                                ],
                            ),
                            height=200,
                        ),
                    ],
                    spacing=10,
                ),
            ),
            width=300,
        )

    def _build_recent_reports(self) -> Card:
        """Build recent reports table"""
        return Card(
            content=Container(
                padding=15,
                content=Column(
                    controls=[
                        Text("Recent Reports", size=16,
                             weight=ft.FontWeight.BOLD),
                        DataTable(
                            columns=[
                                DataColumn(Text("Report Name")),
                                DataColumn(Text("Type")),
                                DataColumn(Text("Generated By")),
                                DataColumn(Text("Date")),
                                DataColumn(Text("Actions")),
                            ],
                            rows=[
                                DataRow(
                                    cells=[
                                        DataCell(
                                            Text("Attendance Report - March 2024")),
                                        DataCell(Text("Attendance")),
                                        DataCell(Text("Admin")),
                                        DataCell(Text("2024-03-10")),
                                        DataCell(
                                            Row(
                                                controls=[
                                                    IconButton(
                                                        icon=ft.Icons.VISIBILITY,
                                                        tooltip="View",
                                                        on_click=lambda e: self.show_info(
                                                            "View report"),
                                                    ),
                                                    IconButton(
                                                        icon=ft.Icons.DOWNLOAD,
                                                        tooltip="Download",
                                                        on_click=lambda e: self.show_info(
                                                            "Download report"),
                                                    ),
                                                ],
                                            )
                                        ),
                                    ],
                                ),
                                DataRow(
                                    cells=[
                                        DataCell(
                                            Text("Employee Summary Q1 2024")),
                                        DataCell(Text("Employee")),
                                        DataCell(Text("HR Manager")),
                                        DataCell(Text("2024-03-05")),
                                        DataCell(
                                            Row(
                                                controls=[
                                                    IconButton(
                                                        icon=ft.Icons.VISIBILITY,
                                                        tooltip="View",
                                                        on_click=lambda e: self.show_info(
                                                            "View report"),
                                                    ),
                                                    IconButton(
                                                        icon=ft.Icons.DOWNLOAD,
                                                        tooltip="Download",
                                                        on_click=lambda e: self.show_info(
                                                            "Download report"),
                                                    ),
                                                ],
                                            )
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                    spacing=10,
                ),
            )
        )

    def _set_date_range(self, range_type: str):
        """Set date range for reports"""
        self.show_info(f"Date range set to {range_type}")

    def _generate_report(self, e: ft.ControlEvent):
        """Generate a new report"""
        self.show_success("Report generated successfully")

    def _export_report(self, e: ft.ControlEvent):
        """Export report"""
        self.show_info("Export options: PDF, CSV, Excel")

    def did_mount(self):
        """Called when screen is mounted"""
        pass


# Create singleton instance
_reports_screen = None


def get_reports_screen(page: ft.Page) -> ReportsScreen:
    """Get or create reports screen instance"""
    global _reports_screen
    if _reports_screen is None:
        _reports_screen = ReportsScreen(page)
    return _reports_screen
