"""
Vernika HRA - ETL & Data Entry Screen
PostgreSQL based Excel import/export and Power BI integration interface
"""

import flet as ft
from datetime import datetime
import json
import os
from typing import Dict, List, Optional, Any
from sqlalchemy import inspect, text
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import ETLJob, ETLJobStatus
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

        # File picker - initialize properly for Flet 0.80+
        self._file_picker: Optional[ft.FilePicker] = None
        try:
            self._file_picker = ft.FilePicker()
            self._page.services.append(self._file_picker)
        except Exception as e:
            print(f"[ETL] FilePicker init error: {e}")

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

    def _get_all_tables(self) -> List[str]:
        """Get all table names from PostgreSQL"""
        db = get_db_session()
        try:
            inspector = inspect(db.bind)
            tables = inspector.get_table_names()
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
        finally:
            db.close()

    def _get_etl_jobs(self) -> List[Dict]:
        """Get recent ETL jobs from PostgreSQL"""
        db = get_db_session()
        try:
            jobs = db.query(ETLJob).order_by(
                ETLJob.created_at.desc()).limit(20).all()
            result = []
            for job in jobs:
                result.append({
                    "id": f"JOB-{job.id:03d}",
                    "job_name": job.job_name,
                    "job_type": job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type),
                    "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
                    "success_rows": job.success_rows or 0,
                    "failed_rows": job.failed_rows or 0,
                    "created_at": job.created_at.strftime('%Y-%m-%d %H:%M') if job.created_at else ''
                })
            return result
        except Exception as e:
            print(f"Error getting ETL jobs: {e}")
            return []
        finally:
            db.close()

    def _get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        db = get_db_session()
        try:
            inspector = inspect(db.bind)
            columns = inspector.get_columns(table_name)
            return [col['name'] for col in columns]
        except Exception as e:
            print(f"Error getting columns: {e}")
            return []
        finally:
            db.close()

    def _build_content(self):
        """Build the main UI content"""
        return ft.Column(
            controls=[
                self._build_header(),
                ft.Divider(height=10),
                self._build_data_entry_section(),
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
                            "Import/export data, manual entry, and Power BI integration",
                            size=12,
                            color=colors.SECONDARY,
                        ),
                    ],
                ),
            ],
        )

    def _build_data_entry_section(self) -> ft.Card:
        """Build manual data entry section"""
        # Get available tables for data entry
        tables = [
            ("employees", "Employee"),
            ("departments", "Department"),
            ("positions", "Position"),
            ("users", "User"),
        ]

        # Create table selection buttons
        table_buttons = []
        for table_key, table_name in tables:
            table_buttons.append(
                ft.ElevatedButton(
                    table_name,
                    icon=ft.Icons.ADD,
                    on_click=lambda e, t=table_key, n=table_name: self._show_data_entry_dialog(
                        t, n),
                    style=ft.ButtonStyle(
                        bgcolor=colors.SUCCESS,
                        color="white",
                    ),
                    height=40,
                )
            )

        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.EDIT, size=24,
                                        color=colors.SUCCESS),
                                ft.Text(
                                    "Manual Data Entry",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme.primary,
                                ),
                            ],
                        ),
                        ft.Divider(height=10),
                        ft.Text("Click a button to add new records manually:",
                                size=12, color=colors.SECONDARY),
                        ft.Container(height=10),
                        ft.Row(table_buttons, wrap=True, spacing=10),
                        ft.Container(height=10),
                        ft.Text("Note: User creation requires password and role selection",
                                size=10, color=colors.GREY),
                    ],
                    spacing=10,
                ),
            )
        )

    def _show_data_entry_dialog(self, table_name: str, table_label: str):
        """Show dialog for manual data entry"""
        fields = {}

        if table_name == "employees":
            fields = {
                'employee_code': ft.TextField(label="Employee Code *", width=250),
                'first_name': ft.TextField(label="First Name *", width=250),
                'last_name': ft.TextField(label="Last Name *", width=250),
                'email': ft.TextField(label="Email", width=250),
                'phone': ft.TextField(label="Phone", width=250),
            }
        elif table_name == "departments":
            fields = {
                'name': ft.TextField(label="Department Name *", width=250),
                'code': ft.TextField(label="Code *", width=250),
                'description': ft.TextField(label="Description", width=250),
            }
        elif table_name == "positions":
            fields = {
                'title': ft.TextField(label="Position Title *", width=250),
                'code': ft.TextField(label="Code *", width=250),
                'description': ft.TextField(label="Description", width=250),
            }
        elif table_name == "users":
            fields = {
                'username': ft.TextField(label="Username *", width=250),
                'email': ft.TextField(label="Email *", width=250),
                'password': ft.TextField(label="Password *", width=250, password=True),
            }

        def close_dlg(e):
            self._close_dialog()

        def save_entry(e):
            data = {}
            for key, field in fields.items():
                if field.value:
                    data[key] = field.value.strip()

            # Validate required fields
            if table_name == "employees":
                if not data.get('employee_code') or not data.get('first_name'):
                    self.show_error(
                        "Employee Code and First Name are required!")
                    return
            elif table_name == "departments":
                if not data.get('name') or not data.get('code'):
                    self.show_error("Name and Code are required!")
                    return
            elif table_name == "positions":
                if not data.get('title') or not data.get('code'):
                    self.show_error("Title and Code are required!")
                    return
            elif table_name == "users":
                if not data.get('username') or not data.get('email') or not data.get('password'):
                    self.show_error(
                        "Username, Email and Password are required!")
                    return

            # Save to database
            db = get_db_session()
            try:
                if table_name == "employees":
                    from database.models import Employee
                    emp = Employee(**data)
                    db.add(emp)
                elif table_name == "departments":
                    from database.models import Department
                    dept = Department(**data)
                    db.add(dept)
                elif table_name == "positions":
                    from database.models import Position
                    pos = Position(**data)
                    db.add(pos)
                elif table_name == "users":
                    import bcrypt
                    from database.models import User, UserStatus
                    user = User(
                        username=data['username'],
                        email=data['email'],
                        password_hash=bcrypt.hashpw(
                            data['password'].encode(), bcrypt.gensalt()).decode(),
                        role_id=2,  # Default to employee role
                        status=UserStatus.ACTIVE
                    )
                    db.add(user)

                db.commit()
                self.show_success(f"{table_label} added successfully!")
                self._close_dialog()
            except Exception as ex:
                db.rollback()
                self.show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        # Build form fields list
        field_list = list(fields.values())

        dialog = ft.AlertDialog(
            title=ft.Text(f"Add New {table_label}"),
            content=ft.Container(
                content=ft.Column(
                    controls=field_list,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=350,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_entry,
                    style=ft.ButtonStyle(
                        bgcolor=colors.SUCCESS, color="white"),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

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
        """Show file selection dialog with file picker"""
        # File picker should already be initialized in __init__
        if not self._file_picker:
            self.show_error("File picker not available")
            return

        def pick_file(e):
            """Pick file using file picker"""
            async def pick_and_set():
                try:
                    files = await self._file_picker.pick_files(
                        dialog_title="Choose Excel file",
                        file_type=ft.FilePickerFileType.ANY,
                    )
                    if files and files[0]:
                        path = files[0].path
                        if path:
                            input_field.value = path
                            self.selected_file_name = path
                            self.selected_file_path = path
                            self.show_success(f"File selected: {path}")
                            self._page.update()
                except Exception as ex:
                    print(f"Error picking file: {ex}")
                    self.show_error(f"Error selecting file: {ex}")

            self._page.run_task(pick_and_set)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [ft.Icon(ft.Icons.FOLDER_OPEN, color=theme.primary), ft.Text("Select File")]),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Click Browse to select your Excel file:",
                                size=12, color=colors.SECONDARY),
                        ft.Text("Or enter the full path manually below:",
                                size=11, color=colors.GREY),
                        input_field,
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
                    "Browse",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=pick_file,
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
                                    "Attendance", "attendances"),
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
            db_columns = self._get_table_columns(self.selected_table)

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

            df = pd.read_excel(file_path, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]

            db = get_db_session()

            success_count = 0
            failed_count = 0

            # Get DB columns
            db_columns = self._get_table_columns(self.selected_table)

            # Map columns
            valid_mapping = {}
            for excel_col in df.columns:
                excel_norm = excel_col.lower().replace(' ', '_')
                for db_col in db_columns:
                    if excel_norm == db_col.lower():
                        valid_mapping[excel_col] = db_col
                        break

            if not valid_mapping:
                self.show_error("No matching columns found")
                db.close()
                return

            # Get the model class for the table
            table_name = self.selected_table

            # Insert rows using raw SQL
            for idx, row in df.iterrows():
                try:
                    values = {}
                    for excel_col, db_col in valid_mapping.items():
                        val = row[excel_col]
                        if hasattr(val, 'isoformat'):
                            values[db_col] = val.strftime('%Y-%m-%d')
                        elif pd.isna(val):
                            values[db_col] = None
                        else:
                            values[db_col] = val

                    # Build insert statement
                    columns_str = ', '.join(values.keys())
                    placeholders = ', '.join([f':{k}' for k in values.keys()])
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

                    db.execute(text(sql), values)
                    success_count += 1
                except Exception as row_error:
                    failed_count += 1

            db.commit()
            db.close()

            # Log the job
            self._log_etl_job("import", success_count, failed_count)

            self.show_success(
                f"Import: {success_count} success, {failed_count} failed")
            self._refresh()

        except Exception as ex:
            self.show_error(f"Import failed: {ex}")

    def _log_etl_job(self, job_type: str, success_rows: int, failed_rows: int):
        """Log ETL job to database"""
        db = get_db_session()
        try:
            from database.models import ETLJobType
            job = ETLJob(
                job_name=f"Data {job_type.title()}",
                job_type=ETLJobType.IMPORT if job_type == "import" else ETLJobType.EXPORT,
                target_table=self.selected_table if job_type == "import" else None,
                source_table=self.selected_table if job_type == "export" else None,
                source_file=self.selected_file_path if job_type == "import" else None,
                status=ETLJobStatus.COMPLETED,
                success_rows=success_rows,
                failed_rows=failed_rows
            )
            db.add(job)
            db.commit()
        except Exception as e:
            print(f"Error logging ETL job: {e}")
        finally:
            db.close()

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
            db = get_db_session()
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", db.bind)
            db.close()

            df.to_excel(output_path, index=False, engine='openpyxl')

            self.show_success(f"Exported {len(df)} rows to {output_path}")
            self._log_etl_job("export", len(df), 0)

        except Exception as ex:
            self.show_error(f"Export failed: {ex}")

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
