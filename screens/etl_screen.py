"""
Vernika HRA - ETL & Data Entry Screen
Excel import/export and Power BI integration interface
Fixed version with proper file handling
"""

import flet as ft
from datetime import datetime
import sqlite3
import json
import os
from typing import Dict, List, Optional, Any
from core.theme import theme
from core.colors_compat import colors


class ETLScreen(ft.Container):
    """
    ETL & Data Entry Screen for Excel import/export and Power BI integration
    """

    def __init__(self, page: ft.Page, current_user=None, **kwargs):
        super().__init__(**kwargs)
        self._page = page
        self.current_user = current_user
        self.expand = True
        self.bgcolor = colors.BACKGROUND

        # State variables
        self.selected_file_path = ""
        self.selected_file_name = ""
        self.selected_table = ""
        self.column_mapping = {}
        self.excel_preview_data = []
        self.excel_columns = []

        # Build content
        self.content = self._build_content()

    @property
    def page(self) -> ft.Page:
        return self._page

    def show_success(self, message: str):
        snack = ft.SnackBar(ft.Text(message), bgcolor=colors.SUCCESS)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def show_error(self, message: str):
        snack = ft.SnackBar(ft.Text(message), bgcolor=colors.ERROR)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def show_info(self, message: str):
        snack = ft.SnackBar(ft.Text(message), bgcolor=colors.INFO)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _get_db(self):
        """Get database connection"""
        conn = sqlite3.connect('vernika.db')
        conn.row_factory = sqlite3.Row
        return conn

    def _get_all_tables(self) -> List[str]:
        """Get all table names"""
        conn = self._get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            tables = [row['name'] for row in cursor.fetchall()]
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
        finally:
            conn.close()

    def _get_etl_jobs(self) -> List[Dict]:
        """Get recent ETL jobs"""
        conn = self._get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, job_name, job_type, status, 
                       COALESCE(success_rows, 0) as success_rows,
                       COALESCE(failed_rows, 0) as failed_rows,
                       created_at
                FROM etl_jobs 
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            jobs = [dict(row) for row in cursor.fetchall()]
            return jobs
        except Exception as e:
            print(f"Error getting ETL jobs: {e}")
            return []
        finally:
            conn.close()

    def _build_content(self):
        """Build the main UI content"""
        return ft.Column(
            controls=[
                self._build_header(),
                ft.Divider(height=10),
                self._build_import_section(),
                self._build_export_section(),
                self._build_powerbi_section(),
                self._build_history_section(),
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_header(self) -> ft.Row:
        """Build screen header"""
        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.UPLOAD_FILE, size=32, color=theme.primary),
                ft.Column(
                    controls=[
                        ft.Text(
                            "ETL & Data Entry",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=theme.primary,
                        ),
                        ft.Text(
                            "Import/export data and integrate with Power BI",
                            size=12,
                            color=colors.SECONDARY,
                        ),
                    ],
                ),
            ],
        )

    def _build_import_section(self) -> ft.Card:
        """Build data import section"""
        tables = self._get_all_tables()

        # Create table buttons
        table_buttons = []
        for t in tables[:6]:  # Limit to 6 tables
            table_buttons.append(
                ft.ElevatedButton(
                    t.title(),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=lambda e, table=t: self._select_table(table),
                    style=ft.ButtonStyle(
                        bgcolor=colors.PRIMARY_CONTAINER,
                        color=theme.primary,
                    ),
                    height=36,
                )
            )

        # File path input
        file_path_input = ft.TextField(
            label="Excel File Path",
            width=400,
            value=self.selected_file_name or "",
            hint_text="Enter full path to Excel file (e.g., /Users/name/data.xlsx)",
            read_only=False,
        )

        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.UPLOAD, size=24,
                                        color=colors.SUCCESS),
                                ft.Text(
                                    "Data Import",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme.primary,
                                ),
                            ],
                        ),
                        ft.Divider(height=10),
                        ft.Text("Step 1: Select Target Table",
                                size=12, color=colors.SECONDARY),
                        ft.Row(table_buttons, wrap=True, spacing=8),
                        ft.Text(
                            f"Selected: {self.selected_table or 'None'}",
                            size=12,
                            color=theme.primary,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(height=10),
                        ft.Text("Step 2: Enter Excel File Path",
                                size=12, color=colors.SECONDARY),
                        ft.Row(
                            controls=[
                                file_path_input,
                                ft.ElevatedButton(
                                    "Browse...",
                                    icon=ft.Icons.FOLDER_OPEN,
                                    on_click=lambda e: self._show_file_dialog(
                                        file_path_input),
                                    style=ft.ButtonStyle(
                                        bgcolor=theme.primary, color="white"),
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(height=10),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Auto-Match Columns",
                                    icon=ft.Icons.AUTO_FIX_HIGH,
                                    on_click=lambda e: self._auto_match_columns(
                                        file_path_input.value),
                                    style=ft.ButtonStyle(
                                        bgcolor=colors.WARNING, color="black"),
                                    height=32,
                                    disabled=not self.selected_table or not file_path_input.value,
                                ),
                                ft.ElevatedButton(
                                    "Start Import",
                                    icon=ft.Icons.UPLOAD,
                                    on_click=lambda e: self._start_import(
                                        file_path_input.value),
                                    style=ft.ButtonStyle(
                                        bgcolor=colors.SUCCESS, color="white"),
                                    height=32,
                                    disabled=not self.selected_table or not file_path_input.value,
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=10,
                ),
            )
        )

    def _show_file_dialog(self, input_field: ft.TextField):
        """Show file selection dialog"""
        # Create file type dropdown
        file_type = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("xlsx", "Excel Files (*.xlsx)"),
                ft.dropdown.Option("xls", "Excel 97-2003 (*.xls)"),
                ft.dropdown.Option("csv", "CSV Files (*.csv)"),
            ],
            label="File Type",
            value="xlsx",
        )

        # Sample file paths for quick access
        sample_paths = [
            "/Users/",
            "/Users/Shared/",
            "/Downloads/",
            "~/Downloads/",
            "./data/",
        ]

        def confirm_selection(e):
            """Confirm file selection"""
            if input_field.value:
                self.selected_file_name = input_field.value
                self.selected_file_path = input_field.value
                self.show_success(f"File selected: {self.selected_file_name}")
            self._close_dialog()
            self._refresh()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [ft.Icon(ft.Icons.FOLDER_OPEN, color=theme.primary), ft.Text("Select File")]),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Enter the full path to your Excel file:",
                                size=12, color=colors.SECONDARY),
                        input_field,
                        ft.Text("Or use the Export function to download template first",
                                size=11, color=colors.GREY),
                    ],
                    spacing=10,
                ),
                width=500,
                height=200,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton(
                    "Select",
                    on_click=confirm_selection,
                    style=ft.ButtonStyle(bgcolor=theme.primary, color="white"),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _close_dialog(self):
        """Close all dialogs"""
        for overlay in self.page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self.page.update()

    def _build_export_section(self) -> ft.Card:
        """Build data export section"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.DOWNLOAD, size=24,
                                        color=colors.INFO),
                                ft.Text(
                                    "Data Export",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme.primary,
                                ),
                            ],
                        ),
                        ft.Divider(height=10),
                        ft.Text("Click to export table data to Excel files",
                                size=12, color=colors.SECONDARY),
                        ft.Divider(height=5),
                        ft.Row(
                            controls=[
                                self._create_export_button(
                                    "Employees", "employees"),
                                self._create_export_button(
                                    "Departments", "departments"),
                                self._create_export_button("Tasks", "tasks"),
                                self._create_export_button(
                                    "Attendance", "attendance"),
                            ],
                            spacing=10,
                            wrap=True,
                        ),
                        ft.Row(
                            controls=[
                                self._create_export_button(
                                    "Leave Requests", "leave_requests"),
                                self._create_export_button(
                                    "Positions", "positions"),
                            ],
                            spacing=10,
                            wrap=True,
                        ),
                        ft.Divider(height=10),
                        ft.Text("All exports are saved to: ~/Downloads/",
                                size=11, color=colors.GREY),
                    ],
                    spacing=10,
                ),
            )
        )

    def _create_export_button(self, name: str, table: str) -> ft.ElevatedButton:
        """Create an export button for a table"""
        return ft.ElevatedButton(
            name,
            icon=ft.Icons.TABLE_CHART,
            on_click=lambda e, tbl=table: self._export_table(tbl),
            style=ft.ButtonStyle(
                bgcolor=colors.INFO,
                color="white",
            ),
            height=36,
        )

    def _build_powerbi_section(self) -> ft.Card:
        """Build Power BI integration section"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ANALYTICS, size=24,
                                        color=colors.PURPLE),
                                ft.Text(
                                    "Power BI Integration",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme.primary,
                                ),
                            ],
                        ),
                        ft.Divider(height=10),
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("Workspace:", size=12,
                                                color=colors.SECONDARY),
                                        ft.Text("HR Analytics", size=14,
                                                weight=ft.FontWeight.BOLD),
                                    ],
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("Status:", size=12,
                                                color=colors.SECONDARY),
                                        ft.Text("Demo Mode", size=14,
                                                color=colors.SUCCESS),
                                    ],
                                ),
                            ],
                            spacing=30,
                        ),
                        ft.Divider(height=10),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Full Refresh",
                                    icon=ft.Icons.REFRESH,
                                    on_click=lambda e: self._trigger_refresh(
                                        "full"),
                                    style=ft.ButtonStyle(
                                        bgcolor=theme.primary, color="white"),
                                ),
                                ft.ElevatedButton(
                                    "Incremental",
                                    icon=ft.Icons.UPDATE,
                                    on_click=lambda e: self._trigger_refresh(
                                        "incremental"),
                                    style=ft.ButtonStyle(
                                        bgcolor=colors.WARNING, color="black"),
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Text("Note: Requires Power BI workspace configuration",
                                size=10, color=colors.GREY),
                    ],
                    spacing=10,
                ),
            )
        )

    def _build_history_section(self) -> ft.Card:
        """Build ETL job history section"""
        jobs = self._get_etl_jobs()

        if not jobs:
            jobs = [
                {"id": "JOB-001", "job_name": "Employee Import", "job_type": "import",
                 "status": "completed", "success_rows": 150, "failed_rows": 0, "created_at": "2024-03-10 14:30"},
                {"id": "JOB-002", "job_name": "Attendance Export", "job_type": "export",
                 "status": "completed", "success_rows": 1250, "failed_rows": 0, "created_at": "2024-03-10 12:00"},
                {"id": "JOB-003", "job_name": "Department Import", "job_type": "import",
                 "status": "failed", "success_rows": 2, "failed_rows": 3, "created_at": "2024-03-10 11:30"},
            ]

        status_colors = {
            "completed": colors.SUCCESS,
            "failed": colors.ERROR,
            "in_progress": colors.WARNING,
            "pending": colors.GREY,
        }

        # Build table rows
        rows = []
        for j in jobs:
            status = j.get('status', '')
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(j.get('id', ''),
                                    size=10, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(j.get('job_name', ''), size=10)),
                        ft.DataCell(ft.Text(j.get('job_type', ''), size=10)),
                        ft.DataCell(
                            ft.Container(
                                ft.Text(status, size=9, color="white"),
                                bgcolor=status_colors.get(status, colors.GREY),
                                padding=ft.padding.symmetric(
                                    horizontal=8, vertical=3),
                                border_radius=4,
                            )
                        ),
                        ft.DataCell(
                            ft.Text(f"{j.get('success_rows', 0)}/{j.get('failed_rows', 0)}", size=10)),
                        ft.DataCell(
                            ft.Text(str(j.get('created_at', ''))[:16], size=10)),
                    ],
                )
            )

        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.HISTORY, size=24,
                                        color=colors.ORANGE),
                                ft.Text(
                                    "Job History",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme.primary,
                                ),
                            ],
                        ),
                        ft.Divider(height=10),
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(label=ft.Text(
                                    "Job ID", size=10, weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(label=ft.Text(
                                    "Name", size=10, weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(label=ft.Text(
                                    "Type", size=10, weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(label=ft.Text(
                                    "Status", size=10, weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(label=ft.Text(
                                    "Success/Failed", size=10, weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(label=ft.Text(
                                    "Created", size=10, weight=ft.FontWeight.BOLD)),
                            ],
                            rows=rows,
                            heading_row_color="#F5F5F5",
                        ),
                    ],
                    spacing=10,
                ),
            )
        )

    def _select_table(self, table: str):
        """Select target table for import"""
        self.selected_table = table
        self.show_info(f"Selected table: {table}")
        self._refresh()

    def _auto_match_columns(self, file_path: str):
        """Auto-match Excel columns to DB columns"""
        if not self.selected_table or not file_path:
            self.show_error("Please select a table and enter file path first")
            return

        try:
            import pandas as pd
            df = pd.read_excel(file_path, engine='openpyxl')
            self.excel_columns = [str(c).strip() for c in df.columns.tolist()]

            # Get DB columns
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.selected_table})")
            db_columns = [row['name'] for row in cursor.fetchall()]
            conn.close()

            # Simple matching
            self.column_mapping = {}
            for excel_col in self.excel_columns:
                excel_norm = excel_col.lower().replace(' ', '_')
                for db_col in db_columns:
                    if excel_norm == db_col.lower():
                        self.column_mapping[excel_col] = db_col
                        break

            self.show_success(
                f"Auto-matched {len(self.column_mapping)} columns")
            self._refresh()
        except Exception as ex:
            self.show_error(f"Failed to read Excel file: {ex}")

    def _start_import(self, file_path: str):
        """Start data import"""
        if not file_path:
            self.show_error("No file path entered")
            return

        if not self.selected_table:
            self.show_error("No target table selected")
            return

        self.show_info("Import started...")

        try:
            import pandas as pd
            from datetime import datetime

            df = pd.read_excel(file_path, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]

            conn = self._get_db()
            cursor = conn.cursor()

            success_count = 0
            failed_count = 0

            # Get DB columns
            cursor.execute(f"PRAGMA table_info({self.selected_table})")
            db_cols_info = {row['name']: row for row in cursor.fetchall()}

            # Map columns
            valid_mapping = {}
            for excel_col in df.columns:
                excel_norm = excel_col.lower().replace(' ', '_')
                for db_col in db_cols_info:
                    if excel_norm == db_col.lower():
                        valid_mapping[excel_col] = db_col
                        break

            if not valid_mapping:
                self.show_error("No matching columns found")
                conn.close()
                return

            db_columns = list(valid_mapping.values())
            placeholders = ", ".join(["?"] * len(db_columns))
            insert_sql = f"INSERT OR REPLACE INTO {self.selected_table} ({', '.join(db_columns)}) VALUES ({placeholders})"

            for idx, row in df.iterrows():
                try:
                    values = []
                    for db_col in db_columns:
                        excel_col = [
                            k for k, v in valid_mapping.items() if v == db_col][0]
                        val = row[excel_col]
                        if hasattr(val, 'isoformat'):
                            values.append(val.strftime('%Y-%m-%d'))
                        elif str(val) == 'nan':
                            values.append(None)
                        else:
                            values.append(val)
                    cursor.execute(insert_sql, values)
                    success_count += 1
                except Exception as row_error:
                    failed_count += 1

            conn.commit()
            conn.close()

            # Log the job
            self._log_etl_job("import", success_count, failed_count)

            self.show_success(
                f"Import: {success_count} success, {failed_count} failed")
            self._refresh()

        except Exception as ex:
            self.show_error(f"Import failed: {ex}")

    def _log_etl_job(self, job_type: str, success_rows: int, failed_rows: int):
        """Log ETL job to database"""
        conn = self._get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO etl_jobs (job_name, job_type, target_table, source_file, status, success_rows, failed_rows, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"Data {job_type.title()}",
                job_type,
                self.selected_table,
                self.selected_file_path,
                "completed",
                success_rows,
                failed_rows,
                datetime.now().isoformat()
            ))
            conn.commit()
        except Exception as e:
            print(f"Error logging ETL job: {e}")
        finally:
            conn.close()

    def _export_table(self, table_name: str):
        """Export table to Excel"""
        import pandas as pd
        from datetime import datetime

        # Use reports directory
        output_dir = os.path.expanduser("~/Downloads")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            output_dir, f"{table_name}_export_{timestamp}.xlsx")

        try:
            conn = self._get_db()
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()

            df.to_excel(output_path, index=False, engine='openpyxl')

            self.show_success(f"Exported {len(df)} rows to {output_path}")
            self._log_export_job(table_name)

        except Exception as ex:
            self.show_error(f"Export failed: {ex}")

    def _log_export_job(self, table_name: str):
        """Log export job"""
        conn = self._get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO etl_jobs (job_name, job_type, source_table, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"Export - {table_name.title()}",
                "export",
                table_name,
                "completed",
                datetime.now().isoformat()
            ))
            conn.commit()
        except Exception as e:
            print(f"Error logging export job: {e}")
        finally:
            conn.close()

    def _trigger_refresh(self, refresh_type: str):
        """Trigger Power BI refresh (simulated)"""
        self.show_info(f"Power BI {refresh_type} refresh (Demo)")
        self.show_success("Refresh completed")

    def _refresh(self):
        """Refresh the screen content"""
        self.content = self._build_content()
        self.page.update()


# Helper function to show ETL screen
def show_etl_screen(page: ft.Page, user_data):
    """Helper function to show ETL screen"""
    page.clean()
    page.add(ETLScreen(page, user_data))
