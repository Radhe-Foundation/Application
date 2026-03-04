"""
Vernika HRA - Data Entry Screen (Professional UI Redesign)
Modern, clean interface - Compatible with older Flet versions
"""

import flet as ft
import os
from datetime import datetime
from database.session_manager import get_db_session
from database.models import DataSheet, DataSheetColumn, DataSheetRow


# Professional color palette
PRIMARY_COLOR = "#1E88E5"
PRIMARY_DARK = "#1565C0"
SUCCESS_COLOR = "#43A047"
ERROR_COLOR = "#E53935"
WARNING_COLOR = "#FB8C00"
BG_COLOR = "#F5F7FA"
SURFACE_COLOR = "#FFFFFF"
TEXT_COLOR = "#212121"
TEXT_SECONDARY = "#757575"
BORDER_COLOR = "#E0E0E0"
HOVER_COLOR = "#F5F5F5"
SELECTED_COLOR = "#E3F2FD"
HEADER_BG = "#FAFAFA"


class DataEntryScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BG_COLOR

        # State
        self.current_tab = "sheets"
        self.current_sheet = None
        self.editing_cell = None
        self.selected_row_id = None
        self.selected_cell = None
        self.sort_column = None
        self.sort_ascending = True
        self.current_page = 1
        self.rows_per_page = 50
        self.total_rows = 0
        self.search_query = ""

        self.content = self._build_content()

    def _build_content(self):
        return ft.Column([
            self._build_header(),
            self._build_main_content(),
        ], expand=True, spacing=0)

    def _build_header(self):
        return ft.Container(
            padding=20,
            bgcolor=SURFACE_COLOR,
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.TABLE_CHART,
                                    color=PRIMARY_COLOR, size=32),
                            ft.Column([
                                ft.Text(
                                    "Data Entry", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                ft.Text("Manage your spreadsheets and data",
                                        size=12, color=TEXT_SECONDARY),
                            ], spacing=0),
                        ], spacing=15)
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "New Sheet",
                        icon=ft.Icons.ADD,
                        on_click=self.show_create_dialog,
                        bgcolor=PRIMARY_COLOR,
                        color="white",
                    ),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Divider(height=1, color=BORDER_COLOR),
            ], spacing=0)
        )

    def _build_main_content(self):
        if not self.current_sheet:
            return self._build_sheets_view()
        return self._build_spreadsheet_view()

    def _build_sheets_view(self):
        sheets = self._get_all_sheets()

        header = ft.Container(
            padding=20,
            content=ft.Row([
                ft.Text("My Sheets", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.TextField(
                    hint_text="Search sheets...",
                    width=250,
                    prefix_icon=ft.Icons.SEARCH,
                    border_color=BORDER_COLOR,
                    on_change=self._on_search
                ),
            ])
        )

        if not sheets:
            return ft.Container(
                content=ft.Column([
                    header,
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Icon(ft.Icons.FOLDER_OPEN,
                                    size=80, color="#BDBDBD"),
                            ft.Text("No sheets yet", size=18,
                                    color=TEXT_SECONDARY),
                            ft.Text(
                                "Create your first sheet to start managing data", size=14, color="#9E9E9E"),
                            ft.Container(height=20),
                            ft.ElevatedButton(
                                "Create Sheet",
                                icon=ft.Icons.ADD,
                                on_click=self.show_create_dialog,
                                bgcolor=PRIMARY_COLOR,
                                color="white",
                                height=45,
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                ], spacing=0),
                bgcolor=SURFACE_COLOR,
            )

        # Sheet cards in grid
        grid = []
        for i in range(0, len(sheets), 3):
            row_sheets = sheets[i:i+3]
            grid.append(
                ft.Row([
                    self._sheet_card(sheet) for sheet in row_sheets
                ], spacing=20)
            )

        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(
                    padding=20,
                    content=ft.Column(grid, spacing=20),
                ),
            ], spacing=0),
            bgcolor=SURFACE_COLOR,
        )

    def _sheet_card(self, sheet):
        cols = self._get_col_count(sheet.id)
        rows = self._get_row_count(sheet.id)

        return ft.Container(
            width=280,
            padding=20,
            border_radius=12,
            bgcolor=SURFACE_COLOR,
            on_click=lambda e, sid=sheet.id: self._open_sheet(sid),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        width=48, height=48,
                        bgcolor="#E3F2FD",
                        border_radius=10,
                        content=ft.Icon(ft.Icons.TABLE_CHART,
                                        color=PRIMARY_COLOR, size=24),
                    ),
                    ft.Column([
                        ft.Text(str(sheet.name) if sheet.name else "Untitled",
                                size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Text(f"Updated {sheet.updated_at.strftime('%d %b %Y') if sheet.updated_at else 'Never'}",
                                size=11, color=TEXT_SECONDARY),
                    ], spacing=2, expand=True),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=15),
                ft.Text(str(sheet.description) if sheet.description else "No description",
                        size=12, color=TEXT_SECONDARY, max_lines=2),
                ft.Container(height=15),
                ft.Row([
                    ft.Container(
                        padding=ft.padding.symmetric(
                            horizontal=10, vertical=5),
                        bgcolor="#E8F5E9",
                        border_radius=20,
                        content=ft.Text(
                            f"{cols} cols", size=11, color=SUCCESS_COLOR, weight=ft.FontWeight.W_500),
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(
                            horizontal=10, vertical=5),
                        bgcolor="#E3F2FD",
                        border_radius=20,
                        content=ft.Text(
                            f"{rows} rows", size=11, color=PRIMARY_COLOR, weight=ft.FontWeight.W_500),
                    ),
                ], spacing=10),
                ft.Container(height=15),
                ft.Row([
                    ft.TextButton("Open", on_click=lambda e, sid=sheet.id: self._open_sheet(sid),
                                  style=ft.ButtonStyle(color=PRIMARY_COLOR)),
                    ft.TextButton("Delete", on_click=lambda e, sid=sheet.id: self._delete_sheet(sheet.id),
                                  style=ft.ButtonStyle(color=ERROR_COLOR)),
                ], spacing=10),
            ], spacing=0)
        )

    def _build_spreadsheet_view(self):
        db = get_db_session()
        try:
            columns = db.query(DataSheetColumn).filter(
                DataSheetColumn.sheet_id == self.current_sheet.id
            ).order_by(DataSheetColumn.sort_order).all()

            self.total_rows = db.query(DataSheetRow).filter(
                DataSheetRow.sheet_id == self.current_sheet.id
            ).count()

            offset = (self.current_page - 1) * self.rows_per_page
            rows = db.query(DataSheetRow).filter(
                DataSheetRow.sheet_id == self.current_sheet.id
            ).order_by(DataSheetRow.created_at).offset(offset).limit(self.rows_per_page).all()
        finally:
            db.close()

        toolbar = self._build_toolbar(len(columns))
        table = self._build_table(columns, rows)
        pagination = self._build_pagination()

        return ft.Container(
            content=ft.Column([
                toolbar,
                table,
                pagination,
            ], spacing=0),
            bgcolor=SURFACE_COLOR,
        )

    def _build_toolbar(self, col_count):
        return ft.Container(
            padding=15,
            bgcolor=HEADER_BG,
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(self.current_sheet.name if self.current_sheet else "Sheet",
                                size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Text(f"{self.total_rows} rows • {col_count} columns",
                                size=11, color=TEXT_SECONDARY),
                    ], spacing=0),
                    ft.Container(width=30),
                    ft.ElevatedButton(
                        "+ Add Row",
                        on_click=self._add_row,
                        bgcolor=SUCCESS_COLOR, color="white",
                        height=36,
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "+ Add Column",
                        on_click=self._add_column,
                        bgcolor=PRIMARY_COLOR, color="white",
                        height=36,
                    ),
                    ft.Container(width=20),
                    ft.TextField(
                        hint_text="Search data...",
                        width=200, height=36,
                        prefix_icon=ft.Icons.SEARCH,
                        border_color=BORDER_COLOR,
                        on_change=self._on_filter
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Export Excel", icon=ft.Icons.DOWNLOAD,
                        on_click=self._export_excel,
                        bgcolor=PRIMARY_COLOR, color="white",
                        height=36,
                    ),
                ], spacing=0, alignment=ft.MainAxisAlignment.START),
                ft.Divider(height=1, color=BORDER_COLOR),
            ], spacing=0)
        )

    def _build_table(self, columns, rows):
        # Calculate auto column width based on content
        col_widths = {}
        for col in columns:
            name_len = len(str(col.column_name or "Column"))
            col_widths[col.id] = max(120, min(name_len * 14, 300))

        # Check data for wider content
        for row in rows:
            row_data = dict(row.row_data) if row.row_data else {}
            for col in columns:
                val = str(row_data.get(str(col.id), ""))
                col_widths[col.id] = max(
                    col_widths[col.id], min(len(val) * 12, 300))

        total_width = 50 + sum(col_widths.values()) + 120

        # Header row
        header_cells = [
            ft.Container(
                content=ft.Text(
                    "#", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
                width=50, height=45, padding=10,
                bgcolor=HEADER_BG,
                alignment=ft.alignment.Alignment(0, 0),
            )
        ]

        for col in columns:
            sort_icon = ""
            if self.sort_column == str(col.id):
                sort_icon = " ↑" if self.sort_ascending else " ↓"

            col_header = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"{col.column_name or 'Column'}{sort_icon}",
                                size=12, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.Icons.MORE_VERT, scale=0.6,
                                on_click=lambda e, cid=col.id: self._show_column_menu(
                                    e, cid),
                            ),
                            width=20,
                        ),
                    ], spacing=0),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=col_widths.get(col.id, 150), height=45, padding=5,
                bgcolor=HEADER_BG,
                alignment=ft.alignment.Alignment(0, 0),
                on_click=lambda e, cid=str(col.id): self._sort_by(cid),
            )

            header_cells.append(col_header)

        header_cells.append(
            ft.Container(
                content=ft.Text(
                    "Actions", size=11, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
                width=120, height=45, padding=10,
                bgcolor=HEADER_BG,
                alignment=ft.alignment.Alignment(0, 0),
            )
        )

        # Data rows
        data_rows = []
        row_offset = (self.current_page - 1) * self.rows_per_page

        for idx, row in enumerate(rows):
            row_num = row_offset + idx + 1
            row_data = dict(row.row_data) if row.row_data else {}

            bg = SELECTED_COLOR if self.selected_row_id == row.id else (
                "#FFFFFF" if idx % 2 == 0 else "#FAFAFA")

            cells = [
                ft.Container(
                    content=ft.Text(str(row_num), size=11,
                                    color=TEXT_SECONDARY),
                    width=50, padding=8,
                    bgcolor=bg,
                    alignment=ft.alignment.Alignment(0, 0),
                    on_click=lambda e, rid=row.id: self._select_row(rid),
                )
            ]

            for col in columns:
                col_id = str(col.id)
                val = row_data.get(col_id, "")
                col_width = col_widths.get(col.id, 150)

                is_editing = self.editing_cell == (row.id, col.id)

                if is_editing:
                    cells.append(
                        ft.Container(
                            content=ft.TextField(
                                value=str(val) if val else "",
                                dense=True, text_size=12,
                                border_color="transparent",
                                focused_border_color=PRIMARY_COLOR,
                                on_blur=lambda e, r=row.id, c=col.id: self._finish_edit(
                                    r, c, e.control.value),
                                autofocus=True,
                            ),
                            width=col_width, padding=4,
                            bgcolor=bg,
                        )
                    )
                else:
                    display_val = str(val) if val else ""
                    cells.append(
                        ft.Container(
                            content=ft.Text(
                                display_val, size=11, color=TEXT_COLOR),
                            width=col_width, padding=8,
                            bgcolor=bg,
                            on_click=lambda e, r=row.id, c=col.id: self._start_edit(
                                r, c),
                        )
                    )

            # Actions
            cells.append(
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(ft.Icons.SAVE, scale=0.7, icon_color=SUCCESS_COLOR,
                                      tooltip="Save", on_click=lambda e, rid=row.id: self._save_row(rid)),
                        ft.IconButton(ft.Icons.CONTENT_COPY, scale=0.7, icon_color=PRIMARY_COLOR,
                                      tooltip="Duplicate", on_click=lambda e, rid=row.id: self._duplicate_row(rid)),
                        ft.IconButton(ft.Icons.DELETE, scale=0.7, icon_color=ERROR_COLOR,
                                      tooltip="Delete", on_click=lambda e, rid=row.id: self._delete_row(rid)),
                    ], spacing=2),
                    width=120, padding=4,
                    bgcolor=bg,
                )
            )

            data_rows.append(
                ft.Container(content=ft.Row(cells, spacing=0), bgcolor=bg)
            )

        # Build table with horizontal scroll
        table_header = ft.Container(content=ft.Row(
            header_cells, spacing=0), bgcolor=HEADER_BG)
        table_data = ft.Column(data_rows, spacing=0)

        table_content = ft.Column([table_header, table_data], spacing=0)

        # Return with horizontal scrolling
        return ft.Container(
            height=500,
            expand=True,
            content=ft.ListView(
                controls=[
                    ft.Container(
                        content=ft.Row(header_cells, spacing=0),
                        bgcolor=HEADER_BG,
                    ),
                    ft.Container(
                        content=ft.Column(data_rows, spacing=0),
                    ),
                ],
                spacing=0,
            ),
        )

    def _build_pagination(self):
        total_pages = max(
            1, (self.total_rows + self.rows_per_page - 1) // self.rows_per_page)

        return ft.Container(
            padding=15,
            content=ft.Row([
                ft.Text(f"Showing {len(self._get_page_rows())} of {self.total_rows} rows",
                        size=12, color=TEXT_SECONDARY),
                ft.Container(expand=True),
                ft.Text(f"Page {self.current_page} of {total_pages}",
                        size=12, color=TEXT_SECONDARY),
                ft.Container(width=10),
                ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=lambda e: self._change_page(-1),
                              disabled=self.current_page == 1),
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=lambda e: self._change_page(1),
                              disabled=self.current_page >= total_pages),
            ], spacing=10),
            bgcolor=HEADER_BG,
        )

    def _get_page_rows(self):
        db = get_db_session()
        try:
            offset = (self.current_page - 1) * self.rows_per_page
            return db.query(DataSheetRow).filter(
                DataSheetRow.sheet_id == self.current_sheet.id
            ).offset(offset).limit(self.rows_per_page).all()
        finally:
            db.close()

    # Actions
    def _open_sheet(self, sheet_id):
        db = get_db_session()
        try:
            sheet = db.query(DataSheet).filter(
                DataSheet.id == sheet_id).first()
            if sheet:
                self.current_sheet = sheet
                self.current_page = 1
                self.content = self._build_content()
        finally:
            db.close()
        self._page.update()

    def _close_sheet(self, e=None):
        self.current_sheet = None
        self.content = self._build_content()
        self._page.update()

    def _start_edit(self, row_id, col_id):
        self.editing_cell = (row_id, col_id)
        self.content = self._build_content()
        self._page.update()

    def _finish_edit(self, row_id, col_id, value):
        if self.editing_cell == (row_id, col_id):
            self.editing_cell = None
            db = get_db_session()
            try:
                row = db.query(DataSheetRow).filter(
                    DataSheetRow.id == row_id).first()
                if row:
                    row_data = row.row_data or {}
                    row_data[str(col_id)] = value
                    row.row_data = row_data
                    row.updated_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
        self.content = self._build_content()
        self._page.update()

    def _select_row(self, row_id):
        self.selected_row_id = row_id if self.selected_row_id != row_id else None
        self.content = self._build_content()
        self._page.update()

    def _sort_by(self, col_id):
        if self.sort_column == col_id:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = col_id
            self.sort_ascending = True
        self.content = self._build_content()
        self._page.update()

    def _change_page(self, delta):
        total_pages = max(
            1, (self.total_rows + self.rows_per_page - 1) // self.rows_per_page)
        new_page = self.current_page + delta
        if 1 <= new_page <= total_pages:
            self.current_page = new_page
            self.content = self._build_content()
            self._page.update()

    def _change_rows_per_page(self, e):
        self.rows_per_page = int(e.control.value)
        self.current_page = 1
        self.content = self._build_content()
        self._page.update()

    def _add_row(self, e=None):
        if not self.current_sheet:
            return
        db = get_db_session()
        try:
            columns = db.query(DataSheetColumn).filter(
                DataSheetColumn.sheet_id == self.current_sheet.id
            ).all()

            row_data = {str(col.id): "" for col in columns}
            row = DataSheetRow(
                sheet_id=self.current_sheet.id, row_data=row_data)
            db.add(row)
            db.commit()

            self._show_success("Row added!")
            self.content = self._build_content()
        except Exception as ex:
            self._show_error(str(ex))
        finally:
            db.close()
        self._page.update()

    def _add_multiple_rows(self, e=None):
        """Add multiple rows at once"""
        if not self.current_sheet:
            return

        count_f = ft.TextField(
            label="Number of rows to add", width=200, value="1")

        def save(e):
            try:
                count = int(count_f.value or "1")
                if count < 1 or count > 100:
                    self._show_error("Enter between 1-100")
                    return
            except:
                self._show_error("Invalid number")
                return

            db = get_db_session()
            try:
                columns = db.query(DataSheetColumn).filter(
                    DataSheetColumn.sheet_id == self.current_sheet.id
                ).all()

                for _ in range(count):
                    row_data = {str(col.id): "" for col in columns}
                    row = DataSheetRow(
                        sheet_id=self.current_sheet.id, row_data=row_data)
                    db.add(row)
                db.commit()

                self._show_success(f"Added {count} rows!")
                self._close_dialog()
                self.content = self._build_content()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Multiple Rows"),
            content=ft.Column([count_f], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Add", on_click=save,
                                  bgcolor=SUCCESS_COLOR, color="white"),
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _add_multiple_columns(self, e=None):
        """Add multiple columns at once"""
        if not self.current_sheet:
            return

        count_f = ft.TextField(
            label="Number of columns to add", width=200, value="1")

        def save(e):
            try:
                count = int(count_f.value or "1")
                if count < 1 or count > 20:
                    self._show_error("Enter between 1-20")
                    return
            except:
                self._show_error("Invalid number")
                return

            db = get_db_session()
            try:
                max_order = db.query(DataSheetColumn).filter(
                    DataSheetColumn.sheet_id == self.current_sheet.id
                ).count()

                for i in range(count):
                    col = DataSheetColumn(
                        sheet_id=self.current_sheet.id,
                        column_name=f"Column {max_order + i + 1}",
                        column_type="text",
                        sort_order=max_order + i,
                        width=150
                    )
                    db.add(col)
                db.commit()

                self._show_success(f"Added {count} columns!")
                self._close_dialog()
                self.content = self._build_content()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Multiple Columns"),
            content=ft.Column([count_f], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Add", on_click=save,
                                  bgcolor=PRIMARY_COLOR, color="white"),
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _add_column(self, e=None):
        """Add a new column"""
        if not self.current_sheet:
            return

        name_f = ft.TextField(label="Column Name", width=300)

        def save(e):
            if not name_f.value:
                self._show_error("Column name required")
                return
            db = get_db_session()
            try:
                max_order = db.query(DataSheetColumn).filter(
                    DataSheetColumn.sheet_id == self.current_sheet.id
                ).count()

                col = DataSheetColumn(
                    sheet_id=self.current_sheet.id,
                    column_name=name_f.value,
                    column_type="text",
                    sort_order=max_order,
                    width=150
                )
                db.add(col)
                db.commit()

                self._show_success("Column added!")
                self._close_dialog()
                self.content = self._build_content()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Column"),
            content=ft.Column([name_f], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Add", on_click=save,
                                  bgcolor=PRIMARY_COLOR, color="white"),
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _rename_column(self, col_id):
        """Show dialog to rename a column"""
        db = get_db_session()
        try:
            col = db.query(DataSheetColumn).filter(
                DataSheetColumn.id == col_id).first()
            if not col:
                return

            name_f = ft.TextField(label="Column Name",
                                  width=300, value=col.column_name)

            def save(e):
                if not name_f.value:
                    self._show_error("Column name required")
                    return
                db = get_db_session()
                try:
                    col = db.query(DataSheetColumn).filter(
                        DataSheetColumn.id == col_id).first()
                    if col:
                        col.column_name = name_f.value
                        db.commit()
                        self._show_success("Column renamed!")
                        self._close_dialog()
                        self.content = self._build_content()
                except Exception as ex:
                    self._show_error(str(ex))
                finally:
                    db.close()
                self._page.update()

            dlg = ft.AlertDialog(
                title=ft.Text("Rename Column"),
                content=ft.Column([name_f], spacing=15),
                actions=[
                    ft.TextButton(
                        "Cancel", on_click=lambda _: self._close_dialog()),
                    ft.ElevatedButton("Save", on_click=save,
                                      bgcolor=PRIMARY_COLOR, color="white"),
                ]
            )
            self._page.overlay.append(dlg)
            dlg.open = True
        finally:
            db.close()
        self._page.update()

    def _delete_column(self, col_id):
        """Delete a column"""
        def confirm(e):
            db = get_db_session()
            try:
                # Delete column
                db.query(DataSheetColumn).filter(
                    DataSheetColumn.id == col_id).delete()
                db.commit()
                self._show_success("Column deleted")
                self._close_dialog()
                self.content = self._build_content()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Column?"),
            content=ft.Text("This will delete the column and all its data."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm,
                                  bgcolor=ERROR_COLOR, color="white"),
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_column_menu(self, e, col_id):
        """Show column actions menu"""
        # Get column info
        db = get_db_session()
        try:
            col = db.query(DataSheetColumn).filter(
                DataSheetColumn.id == col_id).first()
            col_name = col.column_name if col else "Column"
        finally:
            db.close()

        def rename(e):
            self._close_dialog()
            self._rename_column(col_id)

        def delete(e):
            self._close_dialog()
            self._delete_column(col_id)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Column: {col_name}"),
            content=ft.Column([
                ft.ElevatedButton("Rename Column", icon=ft.Icons.EDIT, width=200,
                                  bgcolor=PRIMARY_COLOR, color="white", on_click=rename),
                ft.Container(height=10),
                ft.ElevatedButton("Delete Column", icon=ft.Icons.DELETE, width=200,
                                  bgcolor=ERROR_COLOR, color="white", on_click=delete),
            ], spacing=10),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _duplicate_row(self, row_id):
        db = get_db_session()
        try:
            row = db.query(DataSheetRow).filter(
                DataSheetRow.id == row_id).first()
            if row:
                new_row = DataSheetRow(
                    sheet_id=self.current_sheet.id,
                    row_data=dict(row.row_data) if row.row_data else {}
                )
                db.add(new_row)
                db.commit()
                self._show_success("Row duplicated!")
                self.content = self._build_content()
        finally:
            db.close()
        self._page.update()

    def _save_row(self, row_id):
        db = get_db_session()
        try:
            row = db.query(DataSheetRow).filter(
                DataSheetRow.id == row_id).first()
            if row:
                row.updated_at = datetime.utcnow()
                db.commit()
                self._show_success("Row saved!")
        finally:
            db.close()
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
            finally:
                db.close()
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Row?"),
            content=ft.Text("This action cannot be undone."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm,
                                  bgcolor=ERROR_COLOR, color="white"),
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
            finally:
                db.close()
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Sheet?"),
            content=ft.Text("All data will be permanently deleted."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm,
                                  bgcolor=ERROR_COLOR, color="white"),
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _undo(self, e=None):
        self._show_success("Undo")

    def _redo(self, e=None):
        self._show_success("Redo")

    def _on_search(self, e):
        self.search_query = e.control.value
        self._page.update()

    def _on_filter(self, e):
        self.search_query = e.control.value
        self.content = self._build_content()
        self._page.update()

    def _export_excel(self, e=None):
        try:
            import pandas as pd
        except ImportError:
            self._show_error("pandas required")
            return

        db = get_db_session()
        try:
            columns = db.query(DataSheetColumn).filter(
                DataSheetColumn.sheet_id == self.current_sheet.id
            ).order_by(DataSheetColumn.sort_order).all()

            rows = db.query(DataSheetRow).filter(
                DataSheetRow.sheet_id == self.current_sheet.id
            ).all()
        finally:
            db.close()

        data = []
        for row in rows:
            row_dict = {}
            row_data = row.row_data or {}
            for col in columns:
                row_dict[col.column_name or "Column"] = row_data.get(
                    str(col.id), "")
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
            self._show_error(str(ex))

    def show_create_dialog(self, e):
        name_f = ft.TextField(label="Sheet Name", width=350)
        desc_f = ft.TextField(label="Description", width=350, multiline=True)

        # Column and row count selection
        col_count = ft.Dropdown(
            label="Number of Columns",
            width=350,
            value="4",
            options=[
                ft.dropdown.Option("2", "2 Columns"),
                ft.dropdown.Option("3", "3 Columns"),
                ft.dropdown.Option("4", "4 Columns"),
                ft.dropdown.Option("5", "5 Columns"),
                ft.dropdown.Option("6", "6 Columns"),
                ft.dropdown.Option("8", "8 Columns"),
                ft.dropdown.Option("10", "10 Columns"),
            ]
        )

        row_count = ft.Dropdown(
            label="Initial Rows",
            width=350,
            value="10",
            options=[
                ft.dropdown.Option("5", "5 Rows"),
                ft.dropdown.Option("10", "10 Rows"),
                ft.dropdown.Option("20", "20 Rows"),
                ft.dropdown.Option("50", "50 Rows"),
                ft.dropdown.Option("100", "100 Rows"),
            ]
        )

        def save(e):
            if not name_f.value:
                self._show_error("Name required")
                return
            db = get_db_session()
            try:
                sheet = DataSheet(name=name_f.value,
                                  description=desc_f.value or "")
                db.add(sheet)
                db.commit()

                # Create columns based on selection
                num_cols = int(col_count.value)
                num_rows = int(row_count.value)

                for i in range(num_cols):
                    col = DataSheetColumn(
                        sheet_id=sheet.id,
                        column_name=f"Column {i+1}",
                        column_type="text",
                        sort_order=i,
                        width=150
                    )
                    db.add(col)
                db.commit()

                # Create initial rows
                columns = db.query(DataSheetColumn).filter(
                    DataSheetColumn.sheet_id == sheet.id
                ).all()

                for _ in range(num_rows):
                    row_data = {str(col.id): "" for col in columns}
                    row = DataSheetRow(sheet_id=sheet.id, row_data=row_data)
                    db.add(row)
                db.commit()

                self._show_success(
                    f"Sheet created with {num_cols} columns and {num_rows} rows!")
                self._close_dialog()
                self.content = self._build_content()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Create New Sheet"),
            content=ft.Column(
                [name_f, desc_f, col_count, row_count], spacing=15),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Create", on_click=save,
                                  bgcolor=PRIMARY_COLOR, color="white"),
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

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

    def _get_all_sheets(self):
        db = get_db_session()
        try:
            return db.query(DataSheet).order_by(DataSheet.updated_at.desc()).all()
        except:
            return []
        finally:
            db.close()

    def _get_col_count(self, sheet_id):
        db = get_db_session()
        try:
            return db.query(DataSheetColumn).filter(DataSheetColumn.sheet_id == sheet_id).count()
        except:
            return 0
        finally:
            db.close()

    def _get_row_count(self, sheet_id):
        db = get_db_session()
        try:
            return db.query(DataSheetRow).filter(DataSheetRow.sheet_id == sheet_id).count()
        except:
            return 0
        finally:
            db.close()


def show_data_entry(page, user):
    page.clean()
    page.add(DataEntryScreen(page, user))
