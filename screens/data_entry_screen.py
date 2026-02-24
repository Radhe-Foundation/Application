"""
Vernika HRA - Data Entry/Spreadsheet Screen (Redesigned)
Tab-based Multi-View Interface with Advanced Features
"""

import flet as ft
import os
from datetime import datetime
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import DataSheet, DataSheetColumn, DataSheetRow


# Theme colors
PRIMARY_COLOR = "#2E86AB"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"
WARNING_COLOR = "#FF9800"
BG_COLOR = "#F5F7FA"
SURFACE_COLOR = "#FFFFFF"
TEXT_COLOR = "#2C3E50"
TEXT_MUTED = "#7F8C8D"


def _safe_navigate_to_home(page, user=None):
    """Safely navigate to home screen"""
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


# Import navigate_to_home for compatibility (wrapped)
try:
    from core.navigation import navigate_to_home
except ImportError:
    navigate_to_home = _safe_navigate_to_home


class DataEntryScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BG_COLOR

        # Tab state
        # dashboard, sheets, data, templates, import_export, settings
        self.current_tab = "dashboard"
        self.current_sheet = None
        self.view_mode = "grid"  # grid or list
        self.search_query = ""
        self.auto_save_timer = None
        self.unsaved_changes = False

        # Undo/Redo stacks
        self.undo_stack = []
        self.redo_stack = []

        self.content = self._build_content()

    def _build_content(self):
        return ft.Column([
            # Header
            self._build_header(),
            # Tab navigation
            self._build_tabs(),
            # Main content area
            ft.Container(
                content=self._build_tab_content(),
                expand=True,
                padding=20
            )
        ], expand=True, spacing=0)

    def _build_header(self):
        return ft.Container(
            padding=15,
            bgcolor=PRIMARY_COLOR,
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="white",
                    on_click=self.go_back
                ),
                ft.Icon(ft.Icons.TABLE_ROWS, color="white", size=28),
                ft.Text("Data Entry", size=22, color="white",
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                # Auto-save indicator
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CLOUD_DONE, size=16,
                                color="white" if not self.unsaved_changes else WARNING_COLOR),
                        ft.Text("Auto-save on" if not self.unsaved_changes else "Unsaved changes",
                                size=11, color="white"),
                    ], spacing=5),
                    visible=False
                ),
                ft.ElevatedButton(
                    "New Sheet",
                    icon=ft.Icons.ADD,
                    on_click=self.show_create_dialog,
                    style=ft.ButtonStyle(
                        bgcolor=WARNING_COLOR, color="white"),
                ),
            ])
        )

    def _build_tabs(self):
        tabs = [
            ("dashboard", "Dashboard", ft.Icons.DASHBOARD),
            ("sheets", "My Sheets", ft.Icons.FOLDER),
            ("data", "Data Entry", ft.Icons.TABLE_CHART),
            ("templates", "Templates", ft.Icons.WIDGETS),
            ("import_export", "Import/Export", ft.Icons.IMPORT_EXPORT),
            ("settings", "Settings", ft.Icons.SETTINGS),
        ]

        return ft.Container(
            bgcolor=SURFACE_COLOR,
            padding=ft.padding.only(left=10, top=5, bottom=5),
            content=ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(
                                label,
                                size=13,
                                color=PRIMARY_COLOR if self.current_tab == key else TEXT_MUTED,
                                weight=ft.FontWeight.BOLD if self.current_tab == key else ft.FontWeight.NORMAL
                            ),
                            padding=ft.padding.symmetric(
                                horizontal=15, vertical=8),
                            bgcolor=PRIMARY_COLOR if self.current_tab == key else "transparent",
                            border_radius=20,
                            on_click=lambda e, k=key: self._switch_tab(k)
                        ) for key, label, icon in tabs
                    ], spacing=5)
                ),
                ft.Container(expand=True),
            ], alignment=ft.MainAxisAlignment.START)
        )

    def _switch_tab(self, tab_key):
        self.current_tab = tab_key
        self.content = self._build_content()
        self._page.update()

    def _build_tab_content(self):
        if self.current_tab == "dashboard":
            return self._build_dashboard()
        elif self.current_tab == "sheets":
            return self._build_sheets_view()
        elif self.current_tab == "data":
            return self._build_data_entry()
        elif self.current_tab == "templates":
            return self._build_templates()
        elif self.current_tab == "import_export":
            return self._build_import_export()
        elif self.current_tab == "settings":
            return self._build_settings()
        return self._build_dashboard()

    def _build_dashboard(self):
        stats = self._get_dashboard_stats()
        recent_sheets = self._get_recent_sheets(5)

        return ft.Row([
            # Left panel - Stats
            ft.Container(
                width=280,
                content=ft.Column([
                    ft.Text("Overview", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=20),
                    self._stat_card("Total Sheets", str(stats['total_sheets']),
                                    ft.Icons.FOLDER, PRIMARY_COLOR),
                    self._stat_card("Total Rows", str(stats['total_rows']),
                                    ft.Icons.LIST, SUCCESS_COLOR),
                    self._stat_card("This Week", str(stats['this_week']),
                                    ft.Icons.CALENDAR_TODAY, WARNING_COLOR),
                    ft.Container(height=30),
                    ft.Text("Quick Actions", size=16,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.ElevatedButton("Create New Sheet", icon=ft.Icons.ADD,
                                      on_click=self.show_create_dialog,
                                      bgcolor=PRIMARY_COLOR, color="white", width=200),
                    ft.Container(height=10),
                    ft.ElevatedButton("Import Data", icon=ft.Icons.UPLOAD,
                                      on_click=lambda e: self._switch_tab(
                                          "import_export"),
                                      bgcolor=SURFACE_COLOR, color=PRIMARY_COLOR, width=200),
                ], spacing=10)
            ),
            # Right panel - Recent activity
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Text("Recent Sheets", size=18,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            expand=True,
                            spacing=10,
                            controls=[
                                self._recent_sheet_card(sheet) for sheet in recent_sheets
                            ] if recent_sheets else [
                                ft.Container(
                                    content=ft.Text(
                                        "No sheets created yet", color=TEXT_MUTED),
                                    padding=20
                                )
                            ]
                        )
                    )
                ], spacing=10)
            )
        ], spacing=20)

    def _stat_card(self, title, value, icon, color):
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Row([
                    ft.Container(
                        width=40, height=40,
                        bgcolor=f"{color}20",
                        border_radius=8,
                        content=ft.Icon(icon, color=color, size=22),
                    ),
                    ft.Column([
                        ft.Text(value, size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(title, size=12, color=TEXT_MUTED),
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.START)
            ),
            elevation=1
        )

    def _recent_sheet_card(self, sheet):
        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Row([
                    ft.Container(
                        width=40, height=40,
                        bgcolor="#E8F4F8",
                        border_radius=8,
                        content=ft.Icon(ft.Icons.TABLE_CHART,
                                        color=PRIMARY_COLOR, size=22),
                    ),
                    ft.Column([
                        ft.Text(str(sheet.name) if sheet.name else "Untitled",
                                size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Updated: {sheet.updated_at.strftime('%d %b %Y') if sheet.updated_at else 'N/A'}",
                                size=11, color=TEXT_MUTED),
                    ], spacing=2, expand=True),
                    ft.IconButton(icon=ft.Icons.OPEN_IN_NEW, icon_color=PRIMARY_COLOR, scale=0.7,
                                  tooltip="Open", on_click=lambda e, sid=sheet.id: self._open_sheet(sid)),
                ], alignment=ft.MainAxisAlignment.START)
            ),
            elevation=1
        )

    def _build_sheets_view(self):
        sheets = self._get_all_sheets()

        return ft.Column([
            # Toolbar
            ft.Container(
                padding=10,
                bgcolor=SURFACE_COLOR,
                border_radius=8,
                content=ft.Row([
                    ft.TextField(
                        label="Search sheets...",
                        width=300,
                        prefix_icon=ft.Icons.SEARCH,
                        on_change=self._on_search
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Text("View:", size=12, color=TEXT_MUTED),
                            ft.IconButton(icon=ft.Icons.GRID_VIEW, icon_color=PRIMARY_COLOR if self.view_mode == "grid" else TEXT_MUTED,
                                          on_click=lambda e: self._set_view_mode("grid")),
                            ft.IconButton(icon=ft.Icons.LIST, icon_color=PRIMARY_COLOR if self.view_mode == "list" else TEXT_MUTED,
                                          on_click=lambda e: self._set_view_mode("list")),
                        ], spacing=5)
                    ),
                ], alignment=ft.MainAxisAlignment.START)
            ),
            ft.Container(height=15),
            # Sheets grid/list
            ft.Container(
                expand=True,
                content=self._build_sheets_content(sheets)
            )
        ], spacing=0)

    def _build_sheets_content(self, sheets):
        if not sheets:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color="#BDC3C7"),
                    ft.Text("No sheets found", size=16, color=TEXT_MUTED),
                    ft.ElevatedButton("Create First Sheet", on_click=self.show_create_dialog,
                                      bgcolor=PRIMARY_COLOR, color="white"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        if self.view_mode == "grid":
            # Grid view
            rows = []
            for i in range(0, len(sheets), 3):
                row_sheets = sheets[i:i+3]
                rows.append(
                    ft.Row([
                        self._sheet_grid_card(sheet) for sheet in row_sheets
                    ], spacing=15)
                )
            return ft.ListView(expand=True, spacing=15, controls=rows)
        else:
            # List view
            return ft.ListView(
                expand=True,
                spacing=10,
                controls=[self._sheet_list_card(sheet) for sheet in sheets]
            )

    def _sheet_grid_card(self, sheet):
        cols = self._get_col_count(sheet.id)
        rows = self._get_row_count(sheet.id)

        return ft.Card(
            content=ft.Container(
                padding=15,
                width=220,
                content=ft.Column([
                    ft.Container(
                        width=50, height=50,
                        bgcolor="#E8F4F8",
                        border_radius=8,
                        content=ft.Icon(ft.Icons.TABLE_CHART,
                                        size=28, color=PRIMARY_COLOR),
                        alignment=ft.alignment.Alignment(0, 0)
                    ),
                    ft.Text(str(sheet.name) if sheet.name else "Untitled",
                            size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(sheet.description) if sheet.description else "No description",
                            size=11, color=TEXT_MUTED, max_lines=2),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Column([
                            ft.Text(
                                f"{cols}", size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                            ft.Text("Cols", size=10, color=TEXT_MUTED),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([
                            ft.Text(
                                f"{rows}", size=16, weight=ft.FontWeight.BOLD, color=SUCCESS_COLOR),
                            ft.Text("Rows", size=10, color=TEXT_MUTED),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=10),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.OPEN_IN_NEW, icon_color=PRIMARY_COLOR, scale=0.7,
                                      tooltip="Open", on_click=lambda e, sid=sheet.id: self._open_sheet(sid)),
                        ft.IconButton(icon=ft.Icons.EDIT, icon_color=WARNING_COLOR, scale=0.7,
                                      tooltip="Edit", on_click=lambda e, sid=sheet.id: self._edit_sheet(sheet.id)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR_COLOR, scale=0.7,
                                      tooltip="Delete", on_click=lambda e, sid=sheet.id: self._delete_sheet(sheet.id)),
                    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=5)
            ),
            elevation=2
        )

    def _sheet_list_card(self, sheet):
        cols = self._get_col_count(sheet.id)
        rows = self._get_row_count(sheet.id)

        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Row([
                    ft.Container(
                        width=50, height=50,
                        bgcolor="#E8F4F8",
                        border_radius=8,
                        content=ft.Icon(ft.Icons.TABLE_CHART,
                                        size=28, color=PRIMARY_COLOR),
                    ),
                    ft.Column([
                        ft.Text(str(sheet.name) if sheet.name else "Untitled",
                                size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(str(sheet.description) if sheet.description else "No description",
                                size=12, color=TEXT_MUTED),
                        ft.Text(f"Created: {sheet.created_at.strftime('%d %b %Y') if sheet.created_at else 'N/A'}",
                                size=11, color=TEXT_MUTED),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(
                            f"{cols}", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                        ft.Text("Columns", size=10, color=TEXT_MUTED),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([
                        ft.Text(
                            f"{rows}", size=18, weight=ft.FontWeight.BOLD, color=SUCCESS_COLOR),
                        ft.Text("Rows", size=10, color=TEXT_MUTED),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.OPEN_IN_NEW, icon_color=PRIMARY_COLOR,
                                      tooltip="Open", on_click=lambda e, sid=sheet.id: self._open_sheet(sid)),
                        ft.IconButton(icon=ft.Icons.EDIT, icon_color=WARNING_COLOR,
                                      tooltip="Edit", on_click=lambda e, sid=sheet.id: self._edit_sheet(sheet.id)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR_COLOR,
                                      tooltip="Delete", on_click=lambda e, sid=sheet.id: self._delete_sheet(sheet.id)),
                    ], spacing=5),
                ], alignment=ft.MainAxisAlignment.START)
            ),
            elevation=2
        )

    def _build_data_entry(self):
        if not self.current_sheet:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.TABLE_CHART_OUTLINED,
                            size=64, color="#BDC3C7"),
                    ft.Text("Select a sheet to start entering data",
                            size=16, color=TEXT_MUTED),
                    ft.ElevatedButton("Go to My Sheets", on_click=lambda e: self._switch_tab("sheets"),
                                      bgcolor=PRIMARY_COLOR, color="white"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        return self._build_spreadsheet()

    def _build_spreadsheet(self):
        db = get_db_session()
        try:
            columns = db.query(DataSheetColumn).filter(
                DataSheetColumn.sheet_id == self.current_sheet.id).order_by(DataSheetColumn.sort_order).all()
            rows = db.query(DataSheetRow).filter(DataSheetRow.sheet_id ==
                                                 self.current_sheet.id).order_by(DataSheetRow.created_at).all()
        finally:
            db.close()

        # Toolbar
        toolbar = ft.Container(
            padding=10,
            bgcolor=SURFACE_COLOR,
            border_radius=8,
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Back to sheets",
                              on_click=lambda e: self._close_sheet()),
                ft.Text(f"Sheet: {self.current_sheet.name}",
                        size=16, weight=ft.FontWeight.BOLD),
                ft.Container(width=20),
                ft.ElevatedButton("Add Row", icon=ft.Icons.ADD, on_click=lambda e: self._add_row(),
                                  bgcolor=SUCCESS_COLOR, color="white"),
                ft.ElevatedButton("Add Column", icon=ft.Icons.ADD, on_click=lambda e: self._add_column(),
                                  bgcolor=PRIMARY_COLOR, color="white"),
                ft.Container(width=10),
                ft.IconButton(icon=ft.Icons.UNDO, tooltip="Undo",
                              on_click=lambda e: self._undo()),
                ft.IconButton(icon=ft.Icons.REDO, tooltip="Redo",
                              on_click=lambda e: self._redo()),
                ft.Container(expand=True),
                ft.ElevatedButton("Export Excel", icon=ft.Icons.DOWNLOAD, on_click=lambda e: self._export_excel(),
                                  bgcolor=PRIMARY_COLOR, color="white"),
            ], spacing=10)
        )

        # Table header
        header_row = []
        for col in columns:
            col_name = "Column"
            col_width = 150
            try:
                if col.column_name:
                    col_name = col.column_name
                if col.width:
                    col_width = col.width
            except Exception:
                pass

            header_row.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(col_name, size=12, weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(height=2),
                        ft.Container(
                            height=3, width=col_width-20, bgcolor=PRIMARY_COLOR
                        )
                    ], spacing=0),
                    width=col_width,
                    padding=10,
                    bgcolor="#E8F4F8",
                    border=ft.border.all(1, "#E0E0E0"),
                )
            )

        header_row.append(
            ft.Container(content=ft.Text("Actions", size=11, weight=ft.FontWeight.BOLD),
                         width=100, padding=10, bgcolor="#E8F4F8",
                         border=ft.border.all(1, "#E0E0E0"))
        )

        # Data rows
        data_rows = []
        for idx, row in enumerate(rows):
            row_data = {}
            try:
                if row.row_data:
                    row_data = row.row_data
            except Exception:
                pass

            bg = "#FFFFFF" if idx % 2 == 0 else "#FAFAFA"

            cells = []
            for col in columns:
                col_id = str(col.id)
                val = row_data.get(col_id, "")
                col_width = 150
                try:
                    if col.width:
                        col_width = col.width
                except Exception:
                    pass

                # Inline editable cell - using Container with Text instead of TextField for compatibility
                cells.append(
                    ft.Container(
                        content=ft.Text(
                            str(val) if val else "",
                            size=12,
                            color=TEXT_COLOR
                        ),
                        width=col_width,
                        padding=8,
                        bgcolor=bg,
                        border=ft.border.all(1, "#E0E0E0"),
                        alignment=ft.alignment.Alignment(-1, 0)
                    )
                )

            # Action buttons
            cells.append(
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(icon=ft.Icons.SAVE, icon_color=SUCCESS_COLOR,
                                      scale=0.6, tooltip="Save row",
                                      on_click=lambda e, rid=row.id: self._save_row(rid)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR_COLOR,
                                      scale=0.6, tooltip="Delete row",
                                      on_click=lambda e, rid=row.id: self._delete_row(rid)),
                    ], spacing=0),
                    width=100,
                    padding=2,
                    bgcolor=bg,
                    border=ft.border.all(1, "#E0E0E0"),
                )
            )

            data_rows.append(
                ft.Container(content=ft.Row(cells, spacing=0), bgcolor=bg)
            )

        # Build table
        return ft.Column([
            toolbar,
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    # Header
                    ft.Container(content=ft.Row(
                        header_row, spacing=0), bgcolor="#E8F4F8"),
                    # Data
                    ft.Column(data_rows, spacing=0)
                ], spacing=0),
                border=ft.border.all(1, "#E0E0E0"),
                border_radius=8
            ),
            ft.Container(height=10),
            ft.Text(f"{len(rows)} rows | {len(columns)} columns | Click on cells to edit",
                    size=12, color=TEXT_MUTED)
        ], spacing=0)

    def _build_templates(self):
        templates = [
            {"name": "Employee Tracker",
                "description": "Track employee information", "icon": ft.Icons.PEOPLE},
            {"name": "Project Tasks", "description": "Manage project tasks",
                "icon": ft.Icons.TASK},
            {"name": "Inventory List", "description": "Simple inventory tracking",
                "icon": ft.Icons.INVENTORY},
            {"name": "Expense Tracker", "description": "Track expenses",
                "icon": ft.Icons.ATTACH_MONEY},
        ]

        return ft.Column([
            ft.Text("Templates", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.GridView(
                expand=True,
                runs_count=3,
                spacing=20,
                controls=[
                    self._template_card(t) for t in templates
                ]
            )
        ], spacing=10)

    def _template_card(self, template):
        return ft.Card(
            content=ft.Container(
                padding=20,
                width=200,
                content=ft.Column([
                    ft.Icon(template["icon"], size=40, color=PRIMARY_COLOR),
                    ft.Text(template["name"], size=14,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(template["description"],
                            size=11, color=TEXT_MUTED),
                    ft.Container(height=10),
                    ft.ElevatedButton("Use Template", on_click=self.show_create_dialog,
                                      bgcolor=PRIMARY_COLOR, color="white", height=30),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
            ),
            elevation=2
        )

    def _build_import_export(self):
        return ft.Column([
            ft.Text("Import / Export", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Row([
                # Import section
                ft.Card(
                    content=ft.Container(
                        padding=30,
                        width=300,
                        content=ft.Column([
                            ft.Icon(ft.Icons.UPLOAD_FILE,
                                    size=50, color=PRIMARY_COLOR),
                            ft.Text("Import Data", size=18,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text("Import from Excel or CSV file",
                                    size=12, color=TEXT_MUTED),
                            ft.Container(height=15),
                            ft.ElevatedButton("Choose File", on_click=self._import_data,
                                              bgcolor=PRIMARY_COLOR, color="white"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
                    ),
                    elevation=2
                ),
                # Export section
                ft.Card(
                    content=ft.Container(
                        padding=30,
                        width=300,
                        content=ft.Column([
                            ft.Icon(ft.Icons.DOWNLOAD, size=50,
                                    color=SUCCESS_COLOR),
                            ft.Text("Export Data", size=18,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text("Export to Excel or CSV file",
                                    size=12, color=TEXT_MUTED),
                            ft.Container(height=15),
                            ft.ElevatedButton("Export All Sheets", on_click=self._export_all,
                                              bgcolor=SUCCESS_COLOR, color="white"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
                    ),
                    elevation=2
                ),
            ], spacing=30),
            ft.Container(height=30),
            ft.Text("Recent Exports", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Text("No recent exports", size=12, color=TEXT_MUTED),
        ], spacing=10)

    def _build_settings(self):
        return ft.Column([
            ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text("Sheet Preferences", size=16,
                                weight=ft.FontWeight.BOLD),
                        ft.Switch("Auto-save", value=True,
                                  on_change=lambda e: self._toggle_autosave(e)),
                        ft.Text("Auto-save your changes every 30 seconds",
                                size=12, color=TEXT_MUTED),
                        ft.Container(height=15),
                        ft.Text("Default Column Width", size=14),
                        ft.Slider(min=50, max=300, value=150,
                                  divisions=5, label="150px"),
                        ft.Container(height=15),
                        ft.Text("Default View Mode", size=14),
                        ft.Container(
                            content=ft.Row([
                                ft.ElevatedButton("Grid",
                                                  bgcolor=PRIMARY_COLOR if self.view_mode == "grid" else SURFACE_COLOR,
                                                  color="white" if self.view_mode == "grid" else TEXT_COLOR,
                                                  on_click=lambda e: self._set_view_mode("grid")),
                                ft.ElevatedButton("List",
                                                  bgcolor=PRIMARY_COLOR if self.view_mode == "list" else SURFACE_COLOR,
                                                  color="white" if self.view_mode == "list" else TEXT_COLOR,
                                                  on_click=lambda e: self._set_view_mode("list")),
                            ], spacing=10)
                        ),
                    ], spacing=15)
                ),
                elevation=2
            )
        ], spacing=10)

    def _toggle_autosave(self, e):
        self._show_success(
            f"Auto-save {'enabled' if e.control.value else 'disabled'}")

    # Database operations
    def _get_dashboard_stats(self):
        db = get_db_session()
        try:
            total_sheets = db.query(DataSheet).count()
            total_rows = db.query(DataSheetRow).count()

            from datetime import timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            this_week = db.query(DataSheet).filter(
                DataSheet.created_at >= week_ago).count()

            return {'total_sheets': total_sheets, 'total_rows': total_rows, 'this_week': this_week}
        except Exception:
            return {'total_sheets': 0, 'total_rows': 0, 'this_week': 0}
        finally:
            db.close()

    def _get_recent_sheets(self, limit=5):
        db = get_db_session()
        try:
            return db.query(DataSheet).order_by(DataSheet.updated_at.desc()).limit(limit).all()
        except Exception:
            return []
        finally:
            db.close()

    def _get_all_sheets(self):
        db = get_db_session()
        try:
            return db.query(DataSheet).order_by(DataSheet.created_at.desc()).all()
        except Exception:
            return []
        finally:
            db.close()

    def _get_col_count(self, sheet_id):
        db = get_db_session()
        try:
            return db.query(DataSheetColumn).filter(DataSheetColumn.sheet_id == sheet_id).count()
        except Exception:
            return 0
        finally:
            db.close()

    def _get_row_count(self, sheet_id):
        db = get_db_session()
        try:
            return db.query(DataSheetRow).filter(DataSheetRow.sheet_id == sheet_id).count()
        except Exception:
            return 0
        finally:
            db.close()

    # Actions
    def go_back(self, e):
        try:
            # Navigation - handled locally to avoid import errors
            _safe_navigate_to_home(self._page, self.user)
        except Exception as e:
            print(f"Go back error: {e}")
            from screens.login_screen import LoginScreen
            self._page.clean()
            self._page.add(LoginScreen(self._page))

    def _set_view_mode(self, mode):
        self.view_mode = mode
        self.content = self._build_content()
        self._page.update()

    def _on_search(self, e):
        self.search_query = e.control.value
        # Filter implementation
        self._page.update()

    def _switch_tab(self, tab_key):
        self.current_tab = tab_key
        self.content = self._build_content()
        self._page.update()

    def _open_sheet(self, sheet_id):
        db = get_db_session()
        try:
            sheet = db.query(DataSheet).filter(
                DataSheet.id == sheet_id).first()
            if sheet:
                self.current_sheet = sheet
                self.current_tab = "data"
                self.content = self._build_content()
        finally:
            db.close()
        self._page.update()

    def _close_sheet(self):
        self.current_sheet = None
        self.current_tab = "sheets"
        self.content = self._build_content()
        self._page.update()

    def _edit_sheet(self, sheet_id):
        db = get_db_session()
        try:
            sheet = db.query(DataSheet).filter(
                DataSheet.id == sheet_id).first()
            if sheet:
                self._show_edit_sheet_dialog(sheet)
        finally:
            db.close()

    def _show_edit_sheet_dialog(self, sheet):
        name_f = ft.TextField(label="Sheet Name", width=350, value=sheet.name)
        desc_f = ft.TextField(label="Description", width=350,
                              multiline=True, value=sheet.description)

        def save(e):
            if not name_f.value:
                self._show_error("Sheet name required")
                return
            db = get_db_session()
            try:
                sheet.name = name_f.value
                sheet.description = desc_f.value
                sheet.updated_at = datetime.utcnow()
                db.commit()
                self._show_success("Sheet updated!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Sheet"),
            content=ft.Column([name_f, desc_f], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS_COLOR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def show_create_dialog(self, e):
        name_f = ft.TextField(label="Sheet Name", width=350)
        desc_f = ft.TextField(label="Description", width=350, multiline=True)

        def save(e):
            if not name_f.value:
                self._show_error("Sheet name required")
                return
            db = get_db_session()
            try:
                sheet = DataSheet(name=name_f.value, description=desc_f.value)
                db.add(sheet)
                db.commit()

                # Add default columns
                default_cols = ["Column 1", "Column 2", "Column 3"]
                for i, col_name in enumerate(default_cols):
                    col = DataSheetColumn(
                        sheet_id=sheet.id,
                        column_name=col_name,
                        column_type="text",
                        sort_order=i
                    )
                    db.add(col)
                db.commit()

                self._show_success("Sheet created with default columns!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Create Data Sheet"),
            content=ft.Column([name_f, desc_f], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Create", on_click=save,
                                  bgcolor=SUCCESS_COLOR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _delete_sheet(self, sheet_id):
        def confirm(e):
            db = get_db_session()
            try:
                db.query(DataSheetRow).filter(
                    DataSheetRow.sheet_id == sheet_id).delete()
                db.query(DataSheetColumn).filter(
                    DataSheetColumn.sheet_id == sheet_id).delete()
                db.query(DataSheet).filter(DataSheet.id == sheet_id).delete()
                db.commit()
                self._show_success("Sheet deleted")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Sheet?"),
            content=ft.Text("This will delete all data in this sheet."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm,
                                  bgcolor=ERROR_COLOR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _add_row(self):
        if not self.current_sheet:
            return

        db = get_db_session()
        try:
            columns = db.query(DataSheetColumn).filter(
                DataSheetColumn.sheet_id == self.current_sheet.id).order_by(DataSheetColumn.sort_order).all()
        finally:
            db.close()

        if not columns:
            self._show_error("Please add columns first")
            return

        # Create fields for each column
        fields = {}
        for col in columns:
            col_name = "Column"
            try:
                if col.column_name:
                    col_name = col.column_name
            except Exception:
                pass
            fields[col.id] = ft.TextField(label=col_name, width=250)

        def save(e):
            row_data = {}
            for col_id, field in fields.items():
                row_data[str(col_id)] = field.value or ""

            if not any(row_data.values()):
                self._show_error("Enter at least one value")
                return

            db = get_db_session()
            try:
                row = DataSheetRow(
                    sheet_id=self.current_sheet.id, row_data=row_data)
                db.add(row)
                db.commit()

                # Update sheet timestamp
                self.current_sheet.updated_at = datetime.utcnow()
                db.commit()

                self._show_success("Row added!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Row"),
            content=ft.Container(
                content=ft.Column(list(fields.values()),
                                  spacing=10, scroll=ft.ScrollMode.AUTO),
                width=350, height=350
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS_COLOR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _add_column(self):
        if not self.current_sheet:
            return

        name_f = ft.TextField(label="Column Name", width=300)
        type_dd = ft.Dropdown(
            label="Column Type",
            width=300,
            options=[
                ft.dropdown.Option("text", "Text"),
                ft.dropdown.Option("number", "Number"),
                ft.dropdown.Option("date", "Date"),
                ft.dropdown.Option("dropdown", "Dropdown"),
            ],
            value="text"
        )

        def save(e):
            if not name_f.value:
                self._show_error("Column name required")
                return

            db = get_db_session()
            try:
                # Get max sort order
                max_order = db.query(DataSheetColumn).filter(
                    DataSheetColumn.sheet_id == self.current_sheet.id
                ).count()

                col = DataSheetColumn(
                    sheet_id=self.current_sheet.id,
                    column_name=name_f.value,
                    column_type=type_dd.value,
                    sort_order=max_order
                )
                db.add(col)
                db.commit()

                # Update sheet timestamp
                self.current_sheet.updated_at = datetime.utcnow()
                db.commit()

                self._show_success("Column added!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Column"),
            content=ft.Column([name_f, type_dd], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Add", on_click=save,
                                  bgcolor=SUCCESS_COLOR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _on_cell_change(self, e, row_id, col_id):
        self.unsaved_changes = True
        # Could implement auto-save here
        self.content = self._build_content()
        self._page.update()

    def _save_row(self, row_id):
        # Get updated values from the UI
        db = get_db_session()
        try:
            row = db.query(DataSheetRow).filter(
                DataSheetRow.id == row_id).first()
            if row:
                # For now, just mark as saved - in full implementation would extract values from UI
                row.updated_at = datetime.utcnow()
                db.commit()
                self.unsaved_changes = False
                self._show_success("Row saved!")
        finally:
            db.close()
        self.content = self._build_content()
        self._page.update()

    def _delete_row(self, row_id):
        def confirm(e):
            db = get_db_session()
            try:
                db.query(DataSheetRow).filter(
                    DataSheetRow.id == row_id).delete()
                db.commit()
                self._show_success("Row deleted")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Row?"),
            content=ft.Text("Are you sure?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm,
                                  bgcolor=ERROR_COLOR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.undo_stack.pop())
            self._show_success("Undo")

    def _redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.redo_stack.pop())
            self._show_success("Redo")

    def _import_data(self, e):
        self._show_success("Import feature - file picker coming soon")

    def _export_excel(self):
        if not self.current_sheet:
            return

        try:
            import pandas as pd
        except ImportError:
            self._show_error("pandas required: pip install pandas")
            return

        db = get_db_session()
        try:
            columns = db.query(DataSheetColumn).filter(
                DataSheetColumn.sheet_id == self.current_sheet.id).order_by(DataSheetColumn.sort_order).all()
            rows = db.query(DataSheetRow).filter(
                DataSheetRow.sheet_id == self.current_sheet.id).all()
        finally:
            db.close()

        if not rows:
            self._show_error("No data to export")
            return

        data = []
        for row in rows:
            row_dict = {}
            row_data = {}
            try:
                if row.row_data:
                    row_data = row.row_data
            except Exception:
                pass
            for col in columns:
                col_name = "Column"
                try:
                    if col.column_name:
                        col_name = col.column_name
                except Exception:
                    pass
                row_dict[col_name] = row_data.get(str(col.id), "")
            data.append(row_dict)

        try:
            df = pd.DataFrame(data)
            output_dir = os.path.expanduser("~/Downloads")
            os.makedirs(output_dir, exist_ok=True)
            filename = f"{self.current_sheet.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(output_dir, filename)
            df.to_excel(filepath, index=False)
            self._show_success(f"Exported to {filepath}")
        except Exception as ex:
            self._show_error(f"Export error: {ex}")

    def _export_all(self, e):
        self._show_success("Export all sheets - feature coming soon")

    def _close_dialog(self):
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=SUCCESS_COLOR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=ERROR_COLOR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_data_entry(page, user):
    """Main entry point"""
    page.clean()
    page.add(DataEntryScreen(page, user))
