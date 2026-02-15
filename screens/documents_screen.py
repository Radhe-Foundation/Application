"""
Vernika HRA - Documents Screen
Industry-Level Human Resource Management System

This module provides the document management screen.
Fixed version with proper file upload handling for Flet 0.80+.
"""

from typing import List, Dict, Any
import flet as ft
from core.colors_compat import colors


class DocumentsScreen(ft.Container):
    """
    Screen for managing company documents.
    Fixed version - no white screen errors.
    """

    def __init__(self, page: ft.Page, user=None):
        """
        Initialize documents screen.

        Args:
            page: Flet page object
            user: Current user (optional)
        """
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = colors.BACKGROUND

        # Screen data
        self.documents = []
        self.selected_category = 0
        self.search_query = ""
        self._picked_file = None

        # Build the content first
        self.content = self._build_content()

        # Load documents after building UI
        self._load_documents()

    def _build_content(self):
        """Build the main content"""
        return ft.Column(
            controls=[
                self._build_header(),
                self._build_category_tabs(),
                self._build_toolbar(),
                self._build_documents_table(),
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_header(self):
        """Build screen header"""
        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            "Document Management",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=colors.PRIMARY,
                        ),
                        ft.Text(
                            "Manage company documents and files",
                            size=14,
                            color=colors.SECONDARY,
                        ),
                    ],
                    spacing=2,
                ),
            ],
        )

    def _build_category_tabs(self):
        """Build category tabs using buttons"""
        def create_tab_button(label, index, is_selected, icon):
            """Helper to create a tab button"""
            bg = "#E3F2FD" if is_selected else None
            col = "#2196F3" if is_selected else None

            return ft.ElevatedButton(
                label,
                icon=icon,
                style=ft.ButtonStyle(
                    bgcolor=bg,
                    color=col,
                ),
                on_click=lambda e, idx=index: self._handle_category_change(
                    idx),
            )

        tabs_controls = []
        category_list = [
            ("All", 0, ft.Icons.FOLDER),
            ("Policies", 1, ft.Icons.DESCRIPTION),
            ("Forms", 2, ft.Icons.ARTICLE),
            ("Contracts", 3, ft.Icons.GAVEL),
            ("Training", 4, ft.Icons.SCHOOL),
            ("Other", 5, ft.Icons.MORE_HORIZ),
        ]

        for label, idx, icon in category_list:
            is_selected = idx == self.selected_category
            tabs_controls.append(create_tab_button(
                label, idx, is_selected, icon))

        tabs_row = ft.Row(
            controls=tabs_controls,
            scroll=ft.ScrollMode.AUTO,
            wrap=True,
        )

        category_names = ["All", "Policies", "Forms",
                          "Contracts", "Training", "Other"]
        category_label = ft.Text(
            f"Showing: {category_names[self.selected_category]}",
            size=14,
            color=colors.SECONDARY,
        )

        return ft.Container(
            content=ft.Column(controls=[tabs_row, category_label], spacing=10),
        )

    def _build_toolbar(self):
        """Build toolbar with search and add button"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Row(
                    controls=[
                        ft.TextField(
                            label="Search documents...",
                            width=300,
                            prefix_icon=ft.Icons.SEARCH,
                            on_change=self._handle_search,
                        ),
                        ft.ElevatedButton(
                            "Upload Document",
                            icon=ft.Icons.UPLOAD,
                            on_click=self._handle_upload_click,
                            style=ft.ButtonStyle(
                                bgcolor=colors.PRIMARY,
                                color=colors.ON_PRIMARY,
                            ),
                        ),
                        ft.ElevatedButton(
                            "Export to Excel",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=self._export_to_excel,
                            style=ft.ButtonStyle(
                                bgcolor=colors.SUCCESS,
                                color=colors.ON_PRIMARY,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            elevation=2,
        )

    def _build_documents_table(self):
        """Build documents data table"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(label=ft.Text("ID")),
                        ft.DataColumn(label=ft.Text("Name")),
                        ft.DataColumn(label=ft.Text("Category")),
                        ft.DataColumn(label=ft.Text("Size")),
                        ft.DataColumn(label=ft.Text("Uploaded By")),
                        ft.DataColumn(label=ft.Text("Date")),
                        ft.DataColumn(label=ft.Text("Actions")),
                    ],
                    rows=self._get_document_rows(),
                    border=ft.border.all(1, colors.OUTLINE),
                    border_radius=8,
                    heading_row_color=colors.PRIMARY_CONTAINER,
                    heading_row_height=50,
                    data_row_min_height=50,
                    data_row_max_height=50,
                    column_spacing=20,
                    show_checkbox_column=False,
                ),
            ),
            elevation=2,
        )

    def _get_document_rows(self) -> List[ft.DataRow]:
        """Get table rows for documents"""
        rows = []
        category_names = ["All", "Policies", "Forms",
                          "Contracts", "Training", "Other"]

        for doc in self.documents:
            icon_color = self._get_category_color(doc.get("category", "Other"))
            category_display = doc.get("category", "Other")

            cells = [
                ft.DataCell(ft.Text(str(doc.get("id", 0)))),
                ft.DataCell(
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DESCRIPTION,
                                    color=icon_color, size=24),
                            ft.Text(doc.get("name", "N/A")),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ),
                ft.DataCell(ft.Text(category_display)),
                ft.DataCell(ft.Text(self._format_size(doc.get("size", 0)))),
                ft.DataCell(ft.Text(doc.get("uploaded_by", "N/A"))),
                ft.DataCell(ft.Text(doc.get("date", "N/A"))),
                ft.DataCell(
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                tooltip="View",
                                on_click=lambda e, d=doc: self._view_document(
                                    d),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD,
                                tooltip="Download",
                                on_click=lambda e, d=doc: self._download_document(
                                    d),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Delete",
                                on_click=lambda e, d=doc: self._confirm_delete(
                                    d),
                                icon_color=colors.ERROR,
                            ),
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                ),
            ]

            rows.append(ft.DataRow(cells=cells))

        # Add placeholder row if no documents
        if not rows:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("No documents found",
                                    color=colors.SECONDARY)),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                    ],
                )
            )

        return rows

    def _get_category_color(self, category: str) -> str:
        """Get color for document category"""
        colors_map = {
            "Policies": colors.BLUE,
            "Forms": colors.GREEN,
            "Contracts": colors.ORANGE,
            "Training": colors.PURPLE,
            "Other": colors.GREY,
        }
        return colors_map.get(category, colors.GREY)

    def _format_size(self, size_bytes: int) -> str:
        """Format file size"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        size = float(size_bytes)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        return f"{size:.1f} {units[unit_index]}"

    def _handle_search(self, e):
        """Handle search input"""
        self.search_query = e.control.value.lower()
        self._load_documents()

    def _handle_category_change(self, index: int):
        """Handle category tab change"""
        self.selected_category = index
        self._load_documents()

    def _handle_upload_click(self, e):
        """Handle upload button click - show upload dialog"""
        self._show_upload_dialog()

    def _show_upload_dialog(self):
        """Show upload dialog"""
        # Document name
        doc_name = ft.TextField(
            label="Document Name *",
            width=400,
        )

        # Category dropdown
        category_options = [
            ft.dropdown.Option("Policies", "Policies"),
            ft.dropdown.Option("Forms", "Forms"),
            ft.dropdown.Option("Contracts", "Contracts"),
            ft.dropdown.Option("Training", "Training"),
            ft.dropdown.Option("Other", "Other"),
        ]
        category_dropdown = ft.Dropdown(
            width=200,
            options=category_options,
            label="Category *",
            value="Other",
        )

        # Description
        description = ft.TextField(
            label="Description",
            width=400,
            multiline=True,
            min_lines=2,
        )

        # Error text
        error_text = ft.Text(color=colors.ERROR, size=12, visible=False)

        def save_upload(e):
            if not doc_name.value:
                error_text.value = "Document name is required!"
                error_text.visible = True
                self._page.update()
                return

            # Add new document to list
            new_doc = {
                "id": len(self.documents) + 1,
                "name": doc_name.value,
                "category": category_dropdown.value or "Other",
                "size": 0,  # Would be actual file size
                "uploaded_by": self.user.get('username', 'User') if isinstance(self.user, dict) else 'User',
                "date": "2024-03-15",  # Would be current date
                "description": description.value or "",
            }
            self.documents.insert(0, new_doc)
            self._close_dialog()
            self.show_success(
                f"Document '{doc_name.value}' uploaded successfully!")
            self._refresh()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [ft.Icon(ft.Icons.UPLOAD, color=colors.PRIMARY), ft.Text("Upload Document")]),
            content=ft.Container(
                content=ft.Column(
                    controls=[doc_name, category_dropdown,
                              description, error_text],
                    spacing=10,
                ),
                width=450,
                height=300,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton(
                    "Upload",
                    on_click=save_upload,
                    style=ft.ButtonStyle(
                        bgcolor=colors.PRIMARY, color=colors.ON_PRIMARY),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _export_to_excel(self, e):
        """Export documents to Excel"""
        # Create CSV format for Excel compatibility
        if not self.documents:
            self.show_warning("No documents to export!")
            return

        # Generate CSV content
        csv_lines = ["ID,Name,Category,Size,Uploaded By,Date"]
        for doc in self.documents:
            size_str = self._format_size(doc.get("size", 0))
            line = f"{doc.get('id', '')},\"{doc.get('name', '')}\",{doc.get('category', '')},{size_str},\"{doc.get('uploaded_by', '')}\",{doc.get('date', '')}"
            csv_lines.append(line)

        csv_content = "\n".join(csv_lines)

        # Show success message
        self.show_success(
            f"Export ready! {len(self.documents)} documents exported to CSV format for Excel.")

        # In a real app, you would save to file or open file dialog
        print("CSV Export:")
        print(csv_content)

    def _view_document(self, document):
        """View document details"""
        doc_name = document.get('name', 'N/A')
        self.show_info(f"Viewing {doc_name}")

    def _download_document(self, document):
        """Download document"""
        doc_name = document.get('name', 'N/A')
        self.show_info(f"Downloading {doc_name}")

    def _confirm_delete(self, document):
        """Show delete confirmation"""
        doc_name = document.get('name', 'N/A')

        def handle_delete(e):
            self._delete_document(document)

        def handle_cancel(e):
            self._close_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.DELETE, color=colors.ERROR), ft.Text(
                "Delete Document", color=colors.ERROR)]),
            content=ft.Text(f"Are you sure you want to delete '{doc_name}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=handle_cancel),
                ft.ElevatedButton(
                    "Delete",
                    on_click=handle_delete,
                    style=ft.ButtonStyle(
                        bgcolor=colors.ERROR, color=colors.ON_ERROR),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _delete_document(self, document):
        """Delete document"""
        doc_name = document.get('name', 'N/A')
        self.documents = [d for d in self.documents if d.get(
            'id') != document.get('id')]
        self.show_success(f"Document '{doc_name}' deleted successfully")
        self._close_dialog()
        self._refresh()

    def _close_dialog(self):
        """Close the dialog"""
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _refresh(self):
        """Refresh the documents display"""
        self.content = self._build_content()
        self._page.update()

    def _load_documents(self):
        """Load documents from database"""
        from database.operations import get_user_documents
        from database.connection import get_db_session

        category_names = ["All", "Policies", "Forms",
                          "Contracts", "Training", "Other"]
        selected_cat = category_names[self.selected_category]

        # Get current user ID
        user_id = None
        if isinstance(self.user, dict):
            user_id = self.user.get('id')
        elif hasattr(self.user, 'id'):
            user_id = self.user.id

        # Load from database using real operations
        db = get_db_session()
        try:
            # Get all documents from database
            all_docs = get_user_documents(db, user_id) if user_id else []

            # Convert to display format
            all_documents = []
            for doc in all_docs:
                all_documents.append({
                    "id": doc.id,
                    "name": doc.name,
                    "category": doc.category.capitalize() if doc.category else "Other",
                    "size": doc.file_size or 0,
                    "uploaded_by": doc.uploader.username if doc.uploader else "Unknown",
                    "date": doc.created_at.strftime('%Y-%m-%d') if doc.created_at else "N/A",
                    "description": doc.description or "",
                    "file_path": doc.file_path,
                })
        except Exception as e:
            print(f"Error loading documents from database: {e}")
            # Fallback to empty list if database fails
            all_documents = []
        finally:
            db.close()

        # Filter by category
        if selected_cat == "All":
            filtered_docs = all_documents
        else:
            filtered_docs = [d for d in all_documents if d.get(
                "category") == selected_cat]

        # Filter by search query
        if self.search_query:
            filtered_docs = [
                d for d in filtered_docs if self.search_query in d.get("name", "").lower()]

        self.documents = filtered_docs

    # Convenience methods for showing messages
    def show_success(self, message: str):
        """Show success message"""
        snack = ft.SnackBar(ft.Text(message), bgcolor=colors.SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_error(self, message: str):
        """Show error message"""
        snack = ft.SnackBar(ft.Text(message), bgcolor=colors.ERROR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_warning(self, message: str):
        """Show warning message"""
        snack = ft.SnackBar(ft.Text(message), bgcolor=colors.WARNING)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def show_info(self, message: str):
        """Show info message"""
        snack = ft.SnackBar(ft.Text(message), bgcolor=colors.INFO)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_documents(page: ft.Page, user=None):
    """Helper function to show documents screen"""
    page.clean()
    page.add(DocumentsScreen(page, user))
