"""
Vernika HRA - Asset Management Screen (Rebuilt)
Company Asset Tracking & Management - Industry Level
"""

import flet as ft
from datetime import datetime, date, timedelta
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Asset, AssetAssignment, AssetMaintenance, Employee
from sqlalchemy import or_


# Theme colors - Professional palette
PRIMARY = "#1E3A5F"
PRIMARY_LIGHT = "#2E5A8F"
SECONDARY = "#E91E63"
SUCCESS = "#00C853"
WARNING = "#FF9100"
ERROR = "#FF1744"
INFO = "#2979FF"
BACKGROUND = "#F5F7FA"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1A2E"
TEXT_SECONDARY = "#6B7280"
BORDER_COLOR = "#E5E7EB"

# Asset status colors
STATUS_COLORS = {
    "available": SUCCESS,
    "assigned": INFO,
    "maintenance": WARNING,
    "retired": "#9E9E9E",
    "lost": ERROR,
}

# Category icons
CATEGORY_ICONS = {
    "hardware": ft.Icons.COMPUTER,
    "furniture": ft.Icons.CHAIR,
    "vehicle": ft.Icons.DIRECTIONS_CAR,
    "equipment": ft.Icons.BUILD,
    "software": ft.Icons.CODE,
    "other": ft.Icons.INVENTORY_2,
}


class AssetManagementScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.current_tab = "assets"  # assets, assignments, maintenance
        self.content = self._build_content()

    def refresh(self):
        """Refresh the asset content"""
        self.content = self._build_content()
        self.update()
        self._page.update()

    def _get_db(self):
        """Get database session"""
        return get_db_session()

    def _get_user_info(self):
        """Get current user info"""
        user_id = None
        if isinstance(self.user, dict):
            user_id = self.user.get('id')
        elif hasattr(self.user, 'id'):
            user_id = self.user.id
        return user_id

    def _build_content(self):
        """Build the asset management content"""
        # Header
        header = self._create_header()

        # Tab navigation
        tabs = self._create_tabs()

        # Content based on current tab
        if self.current_tab == "assets":
            content = self._build_assets_view()
        elif self.current_tab == "assignments":
            content = self._build_assignments_view()
        else:
            content = self._build_maintenance_view()

        return ft.ListView([
            header,
            tabs,
            ft.Container(
                content=content,
                expand=True,
            ),
        ], expand=True, spacing=0)

    def _create_header(self):
        """Create header"""
        return ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.INVENTORY_2, color="WHITE", size=28),
                    ft.Text("Asset Management", size=20, color="WHITE",
                            weight=ft.FontWeight.BOLD),
                ], spacing=15),
                ft.Container(expand=True),
                ft.Row([
                    ft.FilledButton(
                        "Add Asset",
                        icon=ft.Icons.ADD,
                        bgcolor=SUCCESS,
                        color="WHITE",
                        on_click=self._show_add_asset_dialog,
                    ),
                    ft.Container(width=10),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color="WHITE",
                        on_click=self.refresh,
                        tooltip="Refresh"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="WHITE",
                        on_click=self._go_back,
                        tooltip="Back to Dashboard"
                    ),
                ], spacing=5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        )

    def _create_tabs(self):
        """Create tab navigation"""
        tabs = [
            ("assets", "Assets", ft.Icons.INVENTORY_2),
            ("assignments", "Assignments", ft.Icons.ASSIGNMENT),
            ("maintenance", "Maintenance", ft.Icons.BUILD),
        ]

        return ft.Container(
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
            padding=ft.padding.symmetric(horizontal=20, vertical=8),
            content=ft.Row([
                self._create_tab_button(tab_id, label, icon)
                for tab_id, label, icon in tabs
            ], spacing=10),
        )

    def _create_tab_button(self, tab_id, label, icon):
        """Create a tab button"""
        is_selected = self.current_tab == tab_id
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=18,
                        color=PRIMARY if is_selected else TEXT_SECONDARY),
                ft.Text(label, size=14, weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.NORMAL,
                        color=PRIMARY if is_selected else TEXT_SECONDARY),
            ], spacing=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=8,
            bgcolor=PRIMARY + "15" if is_selected else "transparent",
            on_click=lambda e: self._switch_tab(tab_id),
            ink=True,
        )

    def _switch_tab(self, tab):
        """Switch between tabs"""
        self.current_tab = tab
        self.refresh()

    # ============ ASSETS VIEW ============

    def _build_assets_view(self):
        """Build assets list view"""
        assets = self._get_assets()

        # Stats
        total_value = sum(a.purchase_price or 0 for a in assets)
        available_count = len([a for a in assets if a.status == "available"])
        assigned_count = len([a for a in assets if a.status == "assigned"])
        maintenance_count = len(
            [a for a in assets if a.status == "maintenance"])

        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_kpi_card("Total Assets", len(
                    assets), ft.Icons.INVENTORY_2, INFO),
                self._create_kpi_card(
                    "Total Value", f"₹{total_value:,.0f}", ft.Icons.ATTACH_MONEY, WARNING),
                self._create_kpi_card(
                    "Available", available_count, ft.Icons.CHECK_CIRCLE, SUCCESS),
                self._create_kpi_card(
                    "In Use", assigned_count, ft.Icons.PERSON, INFO),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )

        # Filter bar
        filter_bar = self._create_assets_filter_bar()

        # Assets grid
        if assets:
            assets_grid = self._create_assets_grid(assets)
        else:
            assets_grid = self._create_empty_state(
                "No assets found", "Add your first asset",
                ft.Icons.INVENTORY_2, self._show_add_asset_dialog
            )

        return ft.Column([
            filter_bar,
            stats_row,
            ft.Container(content=assets_grid, expand=True),
        ], spacing=0, expand=True)

    def _create_assets_filter_bar(self):
        """Create assets filter bar"""
        search_field = ft.TextField(
            hint_text="Search assets...",
            prefix_icon=ft.Icons.SEARCH,
            width=300,
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY,
        )

        category_filter = ft.Dropdown(
            hint_text="Category",
            width=150,
            options=[
                ft.dropdown.Option("all", "All Categories"),
                ft.dropdown.Option("hardware", "Hardware"),
                ft.dropdown.Option("furniture", "Furniture"),
                ft.dropdown.Option("vehicle", "Vehicle"),
                ft.dropdown.Option("equipment", "Equipment"),
                ft.dropdown.Option("software", "Software"),
            ],
            value="all",
            border_color=BORDER_COLOR,
        )

        status_filter = ft.Dropdown(
            hint_text="Status",
            width=150,
            options=[
                ft.dropdown.Option("all", "All Status"),
                ft.dropdown.Option("available", "Available"),
                ft.dropdown.Option("assigned", "Assigned"),
                ft.dropdown.Option("maintenance", "Maintenance"),
                ft.dropdown.Option("retired", "Retired"),
            ],
            value="all",
            border_color=BORDER_COLOR,
        )

        return ft.Container(
            content=ft.Row([
                search_field,
                category_filter,
                status_filter,
                ft.Container(expand=True),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _create_assets_grid(self, assets):
        """Create assets grid"""
        return ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=15,
                controls=[
                    ft.Container(
                        content=ft.Wrap([
                            self._create_asset_card(asset) for asset in assets
                        ], spacing=15, run_spacing=15),
                        padding=15,
                    )
                ]
            ),
            expand=True,
        )

    def _create_asset_card(self, asset):
        """Create an asset card"""
        status_color = STATUS_COLORS.get(asset.status, "#666")
        category_icon = CATEGORY_ICONS.get(
            asset.category, ft.Icons.INVENTORY_2)

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(
                                category_icon, size=32, color=PRIMARY),
                            bgcolor=PRIMARY + "15",
                            width=50,
                            height=50,
                            border_radius=10,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(asset.name or "", size=16,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(asset.asset_code or "",
                                    size=12, color=TEXT_SECONDARY),
                        ], expand=True),
                        ft.Container(
                            content=ft.Text(asset.status.upper(
                            ) if asset.status else "", size=10, color="WHITE"),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(
                                horizontal=8, vertical=4),
                            border_radius=12,
                        ),
                    ]),
                    ft.Divider(height=15),
                    ft.Row([
                        ft.Icon(ft.Icons.CATEGORY, size=14,
                                color=TEXT_SECONDARY),
                        ft.Text(asset.category.title() if asset.category else "",
                                size=12, color=TEXT_SECONDARY, expand=True),
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.LOCATION_ON, size=14,
                                color=TEXT_SECONDARY),
                        ft.Text(asset.location or "No Location",
                                size=12, color=TEXT_SECONDARY, expand=True),
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.ATTACH_MONEY,
                                size=14, color=TEXT_SECONDARY),
                        ft.Text(f"₹{asset.purchase_price:,.0f}" if asset.purchase_price else "₹0",
                                size=12, color=TEXT_SECONDARY, expand=True),
                    ]),
                    ft.Container(height=10),
                    ft.Row([
                        ft.ElevatedButton("Assign", icon=ft.Icons.PERSON_ADD,
                                          bgcolor=PRIMARY, color="WHITE", height=32,
                                          on_click=lambda e: self._show_assign_asset_dialog(e, asset)),
                        ft.TextButton("Edit", icon=ft.Icons.EDIT,
                                      on_click=lambda a=asset: self._edit_asset(a)),
                        ft.TextButton("Delete", icon=ft.Icons.DELETE,
                                      on_click=lambda a=asset: self._delete_asset(a)),
                    ], alignment=ft.MainAxisAlignment.END),
                ], spacing=5),
                padding=15,
                width=320,
            ),
            elevation=2,
        )

    # ============ ASSIGNMENTS VIEW ============

    def _build_assignments_view(self):
        """Build assignments view"""
        assignments = self._get_assignments()

        # Stats
        active_count = len([a for a in assignments if not a.returned_date])
        returned_count = len([a for a in assignments if a.returned_date])

        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_kpi_card("Total Assignments", len(
                    assignments), ft.Icons.ASSIGNMENT, INFO),
                self._create_kpi_card(
                    "Active", active_count, ft.Icons.PERSON, SUCCESS),
                self._create_kpi_card(
                    "Returned", returned_count, ft.Icons.ASSIGNMENT_RETURN, WARNING),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )

        # Assignments table - scrollable
        if assignments:
            assignments_table = self._create_assignments_table(assignments)
        else:
            assignments_table = self._create_empty_state(
                "No assignments found", "Assign an asset to an employee",
                ft.Icons.ASSIGNMENT, lambda: self._show_assign_asset_dialog(
                    None, None)
            )

        return ft.Column([
            self._create_assignments_filter_bar(),
            stats_row,
            ft.Container(content=assignments_table, expand=True),
        ], spacing=0, expand=True)

    def _create_assignments_filter_bar(self):
        """Create assignments filter bar"""
        return ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.ElevatedButton("Assign Asset", icon=ft.Icons.PERSON_ADD, bgcolor=PRIMARY, color="WHITE",
                                  on_click=lambda e: self._show_assign_asset_dialog(e, None)),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _create_assignments_table(self, assignments):
        """Create assignments table"""
        return ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Asset")),
                    ft.DataColumn(ft.Text("Assigned To")),
                    ft.DataColumn(ft.Text("Date Assigned")),
                    ft.DataColumn(ft.Text("Condition")),
                    ft.DataColumn(ft.Text("Status")),
                    ft.DataColumn(ft.Text("Actions")),
                ],
                rows=[self._create_assignment_row(a) for a in assignments],
            ),
            bgcolor=SURFACE,
            padding=10,
            border_radius=10,
        )

    def _create_assignment_row(self, assignment):
        """Create assignment table row"""
        status = "Active" if not assignment.returned_date else "Returned"
        status_color = SUCCESS if status == "Active" else TEXT_SECONDARY

        return ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(assignment.asset.name if assignment.asset else "N/A")),
                ft.DataCell(ft.Text(
                    f"{assignment.employee.first_name} {assignment.employee.last_name}" if assignment.employee else "N/A")),
                ft.DataCell(ft.Text(assignment.assigned_date.strftime(
                    "%d %b %Y") if assignment.assigned_date else "N/A")),
                ft.DataCell(ft.Text(assignment.condition_on_issue or "Good")),
                ft.DataCell(ft.Container(
                    content=ft.Text(status, size=11, color="WHITE"),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=10,
                )),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.ASSIGNMENT_RETURN, icon_size=18, tooltip="Return",
                                  on_click=lambda a=assignment: self._return_asset(a)),
                    ft.IconButton(ft.Icons.DELETE, icon_size=18, tooltip="Delete",
                                  on_click=lambda a=assignment: self._delete_assignment(a)),
                ], spacing=0)),
            ],
        )

    # ============ MAINTENANCE VIEW ============

    def _build_maintenance_view(self):
        """Build maintenance view"""
        maintenance = self._get_maintenance()

        # Stats
        pending_count = len([m for m in maintenance if m.status == "pending"])
        completed_count = len(
            [m for m in maintenance if m.status == "completed"])
        total_cost = sum(m.cost or 0 for m in maintenance)

        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_kpi_card("Total Records", len(
                    maintenance), ft.Icons.BUILD, INFO),
                self._create_kpi_card(
                    "Pending", pending_count, ft.Icons.PENDING, WARNING),
                self._create_kpi_card(
                    "Completed", completed_count, ft.Icons.CHECK_CIRCLE, SUCCESS),
                self._create_kpi_card(
                    "Total Cost", f"₹{total_cost:,.0f}", ft.Icons.ATTACH_MONEY, ERROR),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )

        # Maintenance table - scrollable
        if maintenance:
            maintenance_table = self._create_maintenance_table(maintenance)
        else:
            maintenance_table = self._create_empty_state(
                "No maintenance records", "Log your first maintenance record",
                ft.Icons.BUILD, self._show_add_maintenance_dialog
            )

        return ft.Column([
            self._create_maintenance_filter_bar(),
            stats_row,
            ft.Container(content=maintenance_table, expand=True),
        ], spacing=0, expand=True)

    def _create_maintenance_filter_bar(self):
        """Create maintenance filter bar"""
        return ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.ElevatedButton("Add Maintenance", icon=ft.Icons.ADD, bgcolor=PRIMARY, color="WHITE",
                                  on_click=self._show_add_maintenance_dialog),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _create_maintenance_table(self, maintenance):
        """Create maintenance table"""
        return ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Asset")),
                    ft.DataColumn(ft.Text("Type")),
                    ft.DataColumn(ft.Text("Date")),
                    ft.DataColumn(ft.Text("Cost"), numeric=True),
                    ft.DataColumn(ft.Text("Vendor")),
                    ft.DataColumn(ft.Text("Status")),
                    ft.DataColumn(ft.Text("Actions")),
                ],
                rows=[self._create_maintenance_row(m) for m in maintenance],
            ),
            bgcolor=SURFACE,
            padding=10,
            border_radius=10,
        )

    def _create_maintenance_row(self, maintenance):
        """Create maintenance table row"""
        status_color = SUCCESS if maintenance.status == "completed" else WARNING

        return ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(maintenance.asset.name if maintenance.asset else "N/A")),
                ft.DataCell(ft.Text(maintenance.maintenance_type.title()
                            if maintenance.maintenance_type else "")),
                ft.DataCell(ft.Text(maintenance.maintenance_date.strftime(
                    "%d %b %Y") if maintenance.maintenance_date else "N/A")),
                ft.DataCell(
                    ft.Text(f"₹{maintenance.cost:,.0f}" if maintenance.cost else "₹0")),
                ft.DataCell(ft.Text(maintenance.vendor or "N/A")),
                ft.DataCell(ft.Container(
                    content=ft.Text(maintenance.status.upper(
                    ) if maintenance.status else "", size=11, color="WHITE"),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=10,
                )),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.EDIT, icon_size=18, tooltip="Edit",
                                  on_click=lambda m=maintenance: self._edit_maintenance(m)),
                    ft.IconButton(ft.Icons.DELETE, icon_size=18, tooltip="Delete",
                                  on_click=lambda m=maintenance: self._delete_maintenance(m)),
                ], spacing=0)),
            ],
        )

    # ============ HELPER METHODS ============

    def _create_kpi_card(self, title, value, icon_name, color):
        """Create a KPI card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(icon_name, size=28, color=color),
                        bgcolor=f"{color}15",
                        width=50,
                        height=50,
                        border_radius=25,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Container(height=8),
                    ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=12, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                padding=15,
                width=150,
            ),
            elevation=1,
        )

    def _create_empty_state(self, title, subtitle, icon, action):
        """Create empty state"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=64, color="#ccc"),
                ft.Text(title, size=18, weight=ft.FontWeight.W_500,
                        color=TEXT_SECONDARY),
                ft.Text(subtitle, size=14, color="#999"),
                ft.Container(height=15),
                ft.ElevatedButton("Add New", icon=ft.Icons.ADD,
                                  bgcolor=PRIMARY, color="WHITE", on_click=action),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=50,
            alignment=ft.alignment.Alignment(0, 0),
        )

    def _get_assets(self):
        """Get all assets"""
        session = self._get_db()
        try:
            assets = session.query(Asset).order_by(
                Asset.created_at.desc()).all()
            return assets
        except Exception as e:
            print(f"Error getting assets: {e}")
            return []
        finally:
            session.close()

    def _get_assignments(self):
        """Get all assignments"""
        session = self._get_db()
        try:
            assignments = session.query(AssetAssignment).order_by(
                AssetAssignment.assigned_date.desc()).all()
            return assignments
        except Exception as e:
            print(f"Error getting assignments: {e}")
            return []
        finally:
            session.close()

    def _get_maintenance(self):
        """Get all maintenance records"""
        session = self._get_db()
        try:
            maintenance = session.query(AssetMaintenance).order_by(
                AssetMaintenance.maintenance_date.desc()).all()
            return maintenance
        except Exception as e:
            print(f"Error getting maintenance: {e}")
            return []
        finally:
            session.close()

    def _get_employees(self):
        """Get all employees"""
        session = self._get_db()
        try:
            employees = session.query(Employee).filter(
                Employee.is_active == True).all()
            return employees
        except Exception as e:
            print(f"Error getting employees: {e}")
            return []
        finally:
            session.close()

    # ============ DIALOGS ============

    def _show_add_asset_dialog(self, e):
        """Show add asset dialog"""
        name_field = ft.TextField(
            label="Asset Name *", hint_text="Enter asset name", border_color=PRIMARY)
        code_field = ft.TextField(
            label="Asset Code *", hint_text="Enter unique asset code", border_color=PRIMARY)
        category_dropdown = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("hardware", "Hardware"),
                ft.dropdown.Option("furniture", "Furniture"),
                ft.dropdown.Option("vehicle", "Vehicle"),
                ft.dropdown.Option("equipment", "Equipment"),
                ft.dropdown.Option("software", "Software"),
                ft.dropdown.Option("other", "Other"),
            ],
            value="hardware",
            border_color=PRIMARY,
        )
        location_field = ft.TextField(
            label="Location", hint_text="Enter location", border_color=PRIMARY)
        serial_field = ft.TextField(
            label="Serial Number", hint_text="Enter serial number", border_color=PRIMARY)
        price_field = ft.TextField(
            label="Purchase Price", hint_text="Enter purchase price", value="0", border_color=PRIMARY)
        warranty_field = ft.TextField(
            label="Warranty Expiry (YYYY-MM-DD)", hint_text="YYYY-MM-DD", border_color=PRIMARY)
        description_field = ft.TextField(
            label="Description", hint_text="Enter description", multiline=True, min_lines=2, border_color=PRIMARY)

        def save_asset(e):
            if not name_field.value or not code_field.value:
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text("Name and Code are required")))
                return

            session = self._get_db()
            try:
                # Parse warranty date if provided
                warranty_expiry = None
                if warranty_field.value:
                    try:
                        warranty_expiry = datetime.strptime(
                            warranty_field.value, "%Y-%m-%d").date()
                    except Exception:
                        pass

                asset = Asset(
                    name=name_field.value,
                    asset_code=code_field.value,
                    category=category_dropdown.value,
                    location=location_field.value,
                    serial_number=serial_field.value,
                    purchase_price=float(price_field.value or 0),
                    warranty_expiry=warranty_expiry,
                    description=description_field.value,
                    status="available",
                )
                session.add(asset)
                session.commit()
                self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                    "Asset added successfully"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Add New Asset"),
            content=ft.Container(
                content=ft.Column([
                    name_field, code_field, category_dropdown,
                    location_field, serial_field, price_field, warranty_field, description_field
                ], tight=True, spacing=12),
                width=450,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Save", on_click=save_asset,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _show_assign_asset_dialog(self, e, asset=None):
        """Show assign asset dialog"""
        assets = self._get_assets()
        employees = self._get_employees()

        # Filter available assets
        available_assets = [a for a in assets if a.status == "available"]

        asset_dropdown = ft.Dropdown(
            label="Select Asset",
            options=[ft.dropdown.Option(str(a.id), f"{a.name} ({a.asset_code})")
                     for a in available_assets] if available_assets else [ft.dropdown.Option("", "No available assets")],
            border_color=PRIMARY,
        )

        # Pre-select asset if provided
        if asset and asset.status == "available":
            asset_dropdown.value = str(asset.id)

        employee_dropdown = ft.Dropdown(
            label="Assign To",
            options=[ft.dropdown.Option(str(e.id), f"{e.first_name} {e.last_name}")
                     for e in employees if e.is_active] if employees else [ft.dropdown.Option("", "No employees")],
            border_color=PRIMARY,
        )
        condition_field = ft.TextField(
            label="Condition at Issue", value="Good", border_color=PRIMARY)
        notes_field = ft.TextField(
            label="Notes", hint_text="Additional notes", multiline=True, border_color=PRIMARY)

        def assign_asset(e):
            if not asset_dropdown.value or not employee_dropdown.value:
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text("Asset and Employee are required")))
                return

            session = self._get_db()
            try:
                assignment = AssetAssignment(
                    asset_id=int(asset_dropdown.value),
                    employee_id=int(employee_dropdown.value),
                    assigned_date=date.today(),
                    condition_on_issue=condition_field.value,
                    notes=notes_field.value,
                )
                session.add(assignment)

                # Update asset status
                asset = session.query(Asset).get(int(asset_dropdown.value))
                if asset:
                    asset.status = "assigned"

                session.commit()
                self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                    "Asset assigned successfully"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Assign Asset"),
            content=ft.Container(
                content=ft.Column([
                    asset_dropdown, employee_dropdown, condition_field, notes_field
                ], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Assign", on_click=assign_asset,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _show_add_maintenance_dialog(self, e=None):
        """Show add maintenance dialog"""
        assets = self._get_assets()

        asset_dropdown = ft.Dropdown(
            label="Select Asset",
            options=[ft.dropdown.Option(str(a.id), f"{a.name} ({a.asset_code})") for a in assets] if assets else [
                ft.dropdown.Option("", "No assets")],
            border_color=PRIMARY,
        )

        type_dropdown = ft.Dropdown(
            label="Maintenance Type",
            options=[
                ft.dropdown.Option("repair", "Repair"),
                ft.dropdown.Option("service", "Service"),
                ft.dropdown.Option("inspection", "Inspection"),
                ft.dropdown.Option("upgrade", "Upgrade"),
            ],
            value="service",
            border_color=PRIMARY,
        )

        description_field = ft.TextField(
            label="Description *", hint_text="Describe the maintenance", multiline=True, min_lines=2, border_color=PRIMARY)
        date_field = ft.TextField(label="Maintenance Date", value=date.today(
        ).strftime("%Y-%m-%d"), hint_text="YYYY-MM-DD", border_color=PRIMARY)
        cost_field = ft.TextField(
            label="Cost", value="0", border_color=PRIMARY)
        vendor_field = ft.TextField(
            label="Vendor", hint_text="Vendor name", border_color=PRIMARY)

        def save_maintenance(e):
            if not description_field.value or not asset_dropdown.value:
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text("Description and Asset are required")))
                return

            session = self._get_db()
            try:
                maintenance_date = None
                if date_field.value:
                    try:
                        maintenance_date = datetime.strptime(
                            date_field.value, "%Y-%m-%d").date()
                    except Exception:
                        pass

                maintenance = AssetMaintenance(
                    asset_id=int(asset_dropdown.value),
                    maintenance_type=type_dropdown.value,
                    description=description_field.value,
                    maintenance_date=maintenance_date or date.today(),
                    cost=float(cost_field.value or 0),
                    vendor=vendor_field.value,
                    status="completed",
                )
                session.add(maintenance)
                session.commit()
                self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                    "Maintenance record added"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Add Maintenance Record"),
            content=ft.Container(
                content=ft.Column([
                    asset_dropdown, type_dropdown, description_field,
                    date_field, cost_field, vendor_field
                ], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Save", on_click=save_maintenance,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    # ============ CRUD OPERATIONS ============

    def _edit_asset(self, asset):
        """Edit asset"""
        name_field = ft.TextField(
            label="Name *", value=asset.name or "", border_color=PRIMARY)
        location_field = ft.TextField(
            label="Location", value=asset.location or "", border_color=PRIMARY)
        status_dropdown = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("available", "Available"),
                ft.dropdown.Option("assigned", "Assigned"),
                ft.dropdown.Option("maintenance", "Maintenance"),
                ft.dropdown.Option("retired", "Retired"),
            ],
            value=asset.status or "available",
            border_color=PRIMARY,
        )
        price_field = ft.TextField(label="Purchase Price", value=str(
            asset.purchase_price or 0), border_color=PRIMARY)

        def update_asset(e):
            if not name_field.value:
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text("Name is required")))
                return

            session = self._get_db()
            try:
                asset_obj = session.query(Asset).get(asset.id)
                if asset_obj:
                    asset_obj.name = name_field.value
                    asset_obj.location = location_field.value
                    asset_obj.status = status_dropdown.value
                    asset_obj.purchase_price = float(price_field.value or 0)
                    session.commit()
                    self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                        "Asset updated successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Asset"),
            content=ft.Container(
                content=ft.Column(
                    [name_field, location_field, status_dropdown, price_field], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Update", on_click=update_asset,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _delete_asset(self, asset):
        """Delete asset"""
        def confirm_delete(e):
            session = self._get_db()
            try:
                asset_obj = session.query(Asset).get(asset.id)
                if asset_obj:
                    session.delete(asset_obj)
                    session.commit()
                    self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                        "Asset deleted successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Asset"),
            content=ft.Text(
                f"Are you sure you want to delete '{asset.name}'?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Delete", on_click=confirm_delete,
                                bgcolor=ERROR, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _return_asset(self, assignment):
        """Return asset"""
        session = self._get_db()
        try:
            assignment.returned_date = date.today()

            # Update asset status
            asset = session.query(Asset).get(assignment.asset_id)
            if asset:
                asset.status = "available"

            session.commit()
            self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                "Asset returned successfully"), bgcolor=SUCCESS))
            self.refresh()
        except Exception as ex:
            session.rollback()
            self._page.show_snackbar(ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
        finally:
            session.close()

    def _delete_assignment(self, assignment):
        """Delete assignment"""
        def confirm_delete(e):
            session = self._get_db()
            try:
                # Update asset status
                asset = session.query(Asset).get(assignment.asset_id)
                if asset and not assignment.returned_date:
                    asset.status = "available"

                a = session.query(AssetAssignment).get(assignment.id)
                if a:
                    session.delete(a)
                session.commit()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text("Assignment deleted"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Assignment"),
            content=ft.Text(
                "Are you sure you want to delete this assignment?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Delete", on_click=confirm_delete,
                                bgcolor=ERROR, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _edit_maintenance(self, maintenance):
        """Edit maintenance"""
        description_field = ft.TextField(
            label="Description", value=maintenance.description or "", multiline=True, border_color=PRIMARY)
        cost_field = ft.TextField(label="Cost", value=str(
            maintenance.cost or 0), border_color=PRIMARY)
        status_dropdown = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("pending", "Pending"),
                ft.dropdown.Option("completed", "Completed"),
            ],
            value=maintenance.status or "completed",
            border_color=PRIMARY,
        )

        def update_maintenance(e):
            session = self._get_db()
            try:
                m = session.query(AssetMaintenance).get(maintenance.id)
                if m:
                    m.description = description_field.value
                    m.cost = float(cost_field.value or 0)
                    m.status = status_dropdown.value
                    session.commit()
                    self._page.show_snackbar(ft.SnackBar(
                        content=ft.Text("Maintenance updated"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Maintenance"),
            content=ft.Container(
                content=ft.Column(
                    [description_field, cost_field, status_dropdown], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Update", on_click=update_maintenance,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _delete_maintenance(self, maintenance):
        """Delete maintenance"""
        def confirm_delete(e):
            session = self._get_db()
            try:
                m = session.query(AssetMaintenance).get(maintenance.id)
                if m:
                    session.delete(m)
                session.commit()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text("Maintenance deleted"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Maintenance"),
            content=ft.Text(
                "Are you sure you want to delete this maintenance record?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Delete", on_click=confirm_delete,
                                bgcolor=ERROR, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _go_back(self, e):
        """Navigate back to home screen"""
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)


def show_asset_management(page, user):
    """Helper function to show asset management"""
    page.clean()
    page.add(AssetManagementScreen(page, user))
