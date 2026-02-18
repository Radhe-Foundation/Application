"""
Vernika HRA - Inventory/Stock Management Screen (Redesigned)
Multi-Tab Professional Interface with Advanced Features
"""

import flet as ft
from datetime import datetime
from database.connection import get_db_session
from database.models import InventoryCategory, Product, InventoryTransaction


# Theme colors
PRIMARY_COLOR = "#2E86AB"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"
WARNING_COLOR = "#FF9800"
BG_COLOR = "#F5F7FA"
SURFACE_COLOR = "#FFFFFF"
TEXT_COLOR = "#2C3E50"
TEXT_MUTED = "#7F8C8D"


class InventoryScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BG_COLOR

        # Tab state
        # dashboard, products, categories, transactions, suppliers, reports, settings
        self.current_tab = "dashboard"
        self.view_mode = "grid"  # grid or list
        self.search_query = ""
        self.selected_category = None
        self.selected_product = None

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
                ft.Icon(ft.Icons.INVENTORY_2, color="white", size=28),
                ft.Text("Inventory Management", size=22,
                        color="white", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Add Product",
                    icon=ft.Icons.ADD,
                    on_click=self.show_add_product_dialog,
                    style=ft.ButtonStyle(bgcolor=WARNING_COLOR, color="white"),
                ),
            ])
        )

    def _build_tabs(self):
        tabs = [
            ("dashboard", "Dashboard", ft.Icons.DASHBOARD),
            ("products", "Products", ft.Icons.INVENTORY_2),
            ("categories", "Categories", ft.Icons.CATEGORY),
            ("transactions", "Transactions", ft.Icons.SWAP_HORIZ),
            ("suppliers", "Suppliers", ft.Icons.LOCAL_SHIPPING),
            ("reports", "Reports", ft.Icons.ASSESSMENT),
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
        elif self.current_tab == "products":
            return self._build_products()
        elif self.current_tab == "categories":
            return self._build_categories()
        elif self.current_tab == "transactions":
            return self._build_transactions()
        elif self.current_tab == "suppliers":
            return self._build_suppliers()
        elif self.current_tab == "reports":
            return self._build_reports()
        elif self.current_tab == "settings":
            return self._build_settings()
        return self._build_dashboard()

    def _build_dashboard(self):
        stats = self._get_stats()

        return ft.Column([
            # Stats cards
            ft.Row([
                self._stat_card("Total Products", str(
                    stats['total']), ft.Icons.INVENTORY_2, "#3498DB"),
                self._stat_card("Low Stock", str(
                    stats['low']), ft.Icons.WARNING, WARNING_COLOR),
                self._stat_card("Out of Stock", str(
                    stats['out']), ft.Icons.ERROR_OUTLINE, ERROR_COLOR),
                self._stat_card("Categories", str(
                    stats['cats']), ft.Icons.CATEGORY, "#9B59B6"),
                self._stat_card(
                    "Total Value", f"₹{stats['value']:,.0f}", ft.Icons.ATTACH_MONEY, SUCCESS_COLOR),
            ], spacing=20),
            ft.Container(height=30),
            # Alerts section
            ft.Row([
                # Low stock alerts
                ft.Container(
                    expand=1,
                    content=ft.Column([
                        ft.Text("Low Stock Alerts", size=16,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Container(
                            expand=True,
                            content=ft.ListView(
                                expand=True,
                                spacing=8,
                                controls=self._get_low_stock_alerts()
                            )
                        )
                    ], spacing=10)
                ),
                ft.Container(width=20),
                # Recent transactions
                ft.Container(
                    expand=1,
                    content=ft.Column([
                        ft.Text("Recent Transactions", size=16,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Container(
                            expand=True,
                            content=ft.ListView(
                                expand=True,
                                spacing=8,
                                controls=self._get_recent_transactions()
                            )
                        )
                    ], spacing=10)
                ),
            ], spacing=20)
        ], spacing=0)

    def _stat_card(self, title, value, icon, color):
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Icon(icon, color=color, size=28),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=12, color=TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                width=150,
            ),
            elevation=2,
        )

    def _get_low_stock_alerts(self):
        db = get_db_session()
        try:
            products = db.query(Product).filter(
                Product.is_active == True,
                Product.current_stock <= Product.min_stock
            ).limit(5).all()

            if not products:
                return [ft.Text("No low stock alerts", size=12, color=TEXT_MUTED)]

            alerts = []
            for p in products:
                status = "Out of Stock" if p.current_stock == 0 else "Low Stock"
                color = ERROR_COLOR if p.current_stock == 0 else WARNING_COLOR
                alerts.append(
                    ft.Container(
                        padding=10,
                        bgcolor="#FFF5F5" if p.current_stock == 0 else "#FFF8E1",
                        border_radius=8,
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING, color=color, size=18),
                            ft.Column([
                                ft.Text(str(p.name), size=12,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"Stock: {p.current_stock} {p.unit or 'pcs'} | Min: {p.min_stock}", size=10, color=TEXT_MUTED),
                            ], spacing=2, expand=True),
                            ft.Text(status, size=10, color=color,
                                    weight=ft.FontWeight.BOLD),
                        ], spacing=10)
                    )
                )
            return alerts
        finally:
            db.close()

    def _get_recent_transactions(self):
        db = get_db_session()
        try:
            transactions = db.query(InventoryTransaction).order_by(
                InventoryTransaction.created_at.desc()
            ).limit(5).all()

            if not transactions:
                return [ft.Text("No recent transactions", size=12, color=TEXT_MUTED)]

            items = []
            for t in transactions:
                product = db.query(Product).filter(
                    Product.id == t.product_id).first()
                product_name = product.name if product else "Unknown"

                color = SUCCESS_COLOR if t.transaction_type == "purchase" else ERROR_COLOR if t.transaction_type == "sale" else WARNING_COLOR
                icon = ft.Icons.ADD if t.transaction_type == "purchase" else ft.Icons.REMOVE if t.transaction_type == "sale" else ft.Icons.SWAP_HORIZ

                items.append(
                    ft.Container(
                        padding=10,
                        bgcolor=SURFACE_COLOR,
                        border_radius=8,
                        border=ft.border.all(1, "#E0E0E0"),
                        content=ft.Row([
                            ft.Container(
                                width=30, height=30,
                                bgcolor=f"{color}20",
                                border_radius=15,
                                content=ft.Icon(icon, color=color, size=16),
                                alignment=ft.alignment.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text(product_name, size=12,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"{t.transaction_type.capitalize()}: {t.quantity} units", size=10, color=TEXT_MUTED),
                            ], spacing=2, expand=True),
                            ft.Text(t.created_at.strftime(
                                "%d %b") if t.created_at else "", size=10, color=TEXT_MUTED),
                        ], spacing=10)
                    )
                )
            return items
        finally:
            db.close()

    def _build_products(self):
        products = self._get_all_products()

        return ft.Column([
            # Toolbar
            ft.Container(
                padding=10,
                bgcolor=SURFACE_COLOR,
                border_radius=8,
                content=ft.Row([
                    ft.TextField(
                        label="Search products...",
                        width=300,
                        prefix_icon=ft.Icons.SEARCH,
                        on_change=self._on_search
                    ),
                    ft.Container(width=20),
                    # Category filter
                    self._build_category_dropdown(),
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
            # Products grid/list
            ft.Container(
                expand=True,
                content=self._build_products_content(products)
            )
        ], spacing=0)

    def _build_category_dropdown(self):
        db = get_db_session()
        try:
            categories = db.query(InventoryCategory).filter(
                InventoryCategory.is_active == True
            ).all()

            # Build category filter options using buttons
            options = [
                ft.Container(
                    content=ft.Text(
                        "All Categories" if cat is None else (
                            cat.name if cat else "All"),
                        color=PRIMARY_COLOR if (self.selected_category is None and cat is None) or (
                            cat and self.selected_category == cat.id) else TEXT_MUTED,
                        weight=ft.FontWeight.BOLD if (self.selected_category is None and cat is None) or (
                            cat and self.selected_category == cat.id) else ft.FontWeight.NORMAL
                    ),
                    padding=10,
                    bgcolor=PRIMARY_COLOR if (self.selected_category is None and cat is None) or (
                        cat and self.selected_category == cat.id) else "transparent",
                    border_radius=5,
                    on_click=lambda e, cid=None: self._filter_by_category(cid)
                ) for cat in [None] + categories
            ]

            return ft.Container(
                content=ft.Row(options, spacing=5),
            )
        finally:
            db.close()

    def _build_products_content(self, products):
        if not products:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INVENTORY_2_OUTLINED,
                            size=64, color="#BDC3C7"),
                    ft.Text("No products found", size=16, color=TEXT_MUTED),
                    ft.ElevatedButton("Add First Product", on_click=self.show_add_product_dialog,
                                      bgcolor=PRIMARY_COLOR, color="white"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        if self.view_mode == "grid":
            rows = []
            for i in range(0, len(products), 4):
                row_products = products[i:i+4]
                rows.append(
                    ft.Row([
                        self._product_grid_card(p) for p in row_products
                    ], spacing=15)
                )
            return ft.ListView(expand=True, spacing=15, controls=rows)
        else:
            return ft.ListView(
                expand=True,
                spacing=10,
                controls=[self._product_list_card(p) for p in products]
            )

    def _product_grid_card(self, product):
        # Stock status
        if product.current_stock == 0:
            status_color = ERROR_COLOR
            status_text = "Out of Stock"
        elif product.current_stock <= (product.min_stock or 0):
            status_color = WARNING_COLOR
            status_text = "Low Stock"
        else:
            status_color = SUCCESS_COLOR
            status_text = "In Stock"

        cat_name = "Uncategorized"
        try:
            if product.category:
                cat_name = product.category.name
        except:
            pass

        return ft.Card(
            content=ft.Container(
                padding=15,
                width=200,
                content=ft.Column([
                    ft.Container(
                        width=60, height=60,
                        bgcolor="#ECF0F1",
                        border_radius=8,
                        content=ft.Icon(ft.Icons.INVENTORY_2,
                                        size=30, color="#95A5A6"),
                        alignment=ft.alignment.Alignment(0, 0)
                    ),
                    ft.Text(str(product.name) if product.name else "Unknown",
                            size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, max_lines=1),
                    ft.Text(f"SKU: {product.sku or 'N/A'}",
                            size=10, color=TEXT_MUTED),
                    ft.Text(cat_name, size=10, color=TEXT_MUTED),
                    ft.Container(height=5),
                    ft.Text(f"Stock: {product.current_stock or 0} {product.unit or 'pcs'}",
                            size=12, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text(f"₹{product.sale_price or 0}", size=14,
                                color=PRIMARY_COLOR, weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        bgcolor=status_color,
                        content=ft.Text(status_text, size=10, color="white"),
                        border_radius=10,
                    ),
                    ft.Container(height=5),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY_COLOR, scale=0.7,
                                      tooltip="Edit", on_click=lambda e, pid=product.id: self._edit_product(pid)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR_COLOR, scale=0.7,
                                      tooltip="Delete", on_click=lambda e, pid=product.id: self._delete_product(pid)),
                    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            elevation=2
        )

    def _product_list_card(self, product):
        # Stock status
        if product.current_stock == 0:
            status_color = ERROR_COLOR
            status_text = "Out of Stock"
        elif product.current_stock <= (product.min_stock or 0):
            status_color = WARNING_COLOR
            status_text = "Low Stock"
        else:
            status_color = SUCCESS_COLOR
            status_text = "In Stock"

        cat_name = "Uncategorized"
        try:
            if product.category:
                cat_name = product.category.name
        except:
            pass

        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Row([
                    ft.Container(
                        width=50, height=50,
                        bgcolor="#ECF0F1",
                        border_radius=8,
                        content=ft.Icon(ft.Icons.INVENTORY_2,
                                        size=25, color="#95A5A6"),
                    ),
                    ft.Column([
                        ft.Text(str(product.name) if product.name else "Unknown",
                                size=15, weight=ft.FontWeight.BOLD),
                        ft.Text(f"SKU: {product.sku or 'N/A'} | {cat_name}",
                                size=12, color=TEXT_MUTED),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(f"Stock: {product.current_stock or 0} {product.unit or 'pcs'}",
                                size=13, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            padding=ft.padding.symmetric(
                                horizontal=8, vertical=3),
                            bgcolor=status_color,
                            content=ft.Text(
                                status_text, size=10, color="white"),
                            border_radius=10,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    ft.Text(f"₹{product.sale_price or 0}", size=16,
                            color=PRIMARY_COLOR, weight=ft.FontWeight.BOLD),
                    ft.Text(f"₹{product.purchase_price or 0}",
                            size=12, color=TEXT_MUTED),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY_COLOR,
                                      tooltip="Edit", on_click=lambda e, pid=product.id: self._edit_product(pid)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR_COLOR,
                                      tooltip="Delete", on_click=lambda e, pid=product.id: self._delete_product(pid)),
                    ], spacing=5),
                ], alignment=ft.MainAxisAlignment.START)
            ),
            elevation=2
        )

    def _build_categories(self):
        categories = self._get_all_categories()

        return ft.Column([
            ft.Row([
                ft.Text("Categories", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton("Add Category", icon=ft.Icons.ADD, on_click=self.show_add_category_dialog,
                                  bgcolor=PRIMARY_COLOR, color="white"),
            ]),
            ft.Container(height=20),
            ft.Container(
                expand=True,
                content=ft.ListView(
                    expand=True,
                    spacing=10,
                    controls=[
                        self._category_card(cat) for cat in categories
                    ] if categories else [
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.CATEGORY_OUTLINED,
                                        size=48, color="#BDC3C7"),
                                ft.Text("No categories yet",
                                        size=14, color=TEXT_MUTED),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=30,
                            alignment=ft.alignment.Alignment(0, 0)
                        )
                    ]
                )
            )
        ], spacing=10)

    def _category_card(self, category):
        db = get_db_session()
        try:
            product_count = db.query(Product).filter(
                Product.category_id == category.id,
                Product.is_active == True
            ).count()
        finally:
            db.close()

        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Row([
                    ft.Container(
                        width=50, height=50,
                        bgcolor="#E8F4F8",
                        border_radius=8,
                        content=ft.Icon(ft.Icons.FOLDER, size=25,
                                        color=PRIMARY_COLOR),
                    ),
                    ft.Column([
                        ft.Text(str(category.name) if category.name else "Unknown",
                                size=15, weight=ft.FontWeight.BOLD),
                        ft.Text(str(category.description) if category.description else "No description",
                                size=12, color=TEXT_MUTED, max_lines=1),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(f"{product_count}", size=18,
                                weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                        ft.Text("Products", size=10, color=TEXT_MUTED),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY_COLOR,
                                      tooltip="Edit", on_click=lambda e, cid=category.id: self._edit_category(cid)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR_COLOR,
                                      tooltip="Delete", on_click=lambda e, cid=category.id: self._delete_category(cid)),
                    ], spacing=5),
                ], alignment=ft.MainAxisAlignment.START)
            ),
            elevation=2
        )

    def _build_transactions(self):
        transactions = self._get_all_transactions()

        return ft.Column([
            ft.Row([
                ft.Text("Stock Transactions", size=20,
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton("Add Transaction", icon=ft.Icons.ADD, on_click=self.show_add_transaction_dialog,
                                  bgcolor=PRIMARY_COLOR, color="white"),
            ]),
            ft.Container(height=15),
            # Filter bar - simplified without dropdown on_change
            ft.Container(
                padding=10,
                bgcolor=SURFACE_COLOR,
                border_radius=8,
                content=ft.Text(
                    "Filter by transaction type in toolbar coming soon", size=12, color=TEXT_MUTED)
            ),
            ft.Container(height=15),
            # Transactions table
            ft.Container(
                expand=True,
                content=ft.ListView(
                    expand=True,
                    spacing=8,
                    controls=[
                        self._transaction_card(t) for t in transactions
                    ] if transactions else [
                        ft.Container(
                            content=ft.Text("No transactions yet",
                                            size=14, color=TEXT_MUTED),
                            padding=30,
                            alignment=ft.alignment.Alignment(0, 0)
                        )
                    ]
                )
            )
        ], spacing=10)

    def _transaction_card(self, transaction):
        db = get_db_session()
        product = None
        try:
            product = db.query(Product).filter(
                Product.id == transaction.product_id).first()
        finally:
            db.close()

        product_name = product.name if product else "Unknown"

        type_colors = {
            "purchase": SUCCESS_COLOR,
            "sale": ERROR_COLOR,
            "adjustment": WARNING_COLOR,
            "return": PRIMARY_COLOR
        }
        type_icons = {
            "purchase": ft.Icons.ADD,
            "sale": ft.Icons.REMOVE,
            "adjustment": ft.Icons.SWAP_HORIZ,
            "return": ft.Icons.REPLAY
        }

        color = type_colors.get(transaction.transaction_type, TEXT_MUTED)
        icon = type_icons.get(
            transaction.transaction_type, ft.Icons.SWAP_HORIZ)

        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Row([
                    ft.Container(
                        width=40, height=40,
                        bgcolor=f"{color}20",
                        border_radius=20,
                        content=ft.Icon(icon, color=color, size=20),
                        alignment=ft.alignment.Alignment(0, 0)
                    ),
                    ft.Column([
                        ft.Text(f"{transaction.transaction_type.capitalize()}",
                                size=14, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(product_name, size=12),
                    ], spacing=2, expand=True),
                    ft.Text(f"{'+' if transaction.transaction_type in ['purchase', 'return'] else '-'}{transaction.quantity}",
                            size=14, weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(f"₹{transaction.quantity * (product.sale_price if product else 0):.0f}",
                            size=12, color=TEXT_MUTED),
                    ft.Text(transaction.created_at.strftime("%d %b %Y %H:%M") if transaction.created_at else "",
                            size=11, color=TEXT_MUTED),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR_COLOR, scale=0.7,
                                  tooltip="Delete", on_click=lambda e, tid=transaction.id: self._delete_transaction(tid)),
                ], alignment=ft.MainAxisAlignment.START)
            ),
            elevation=1
        )

    def _build_suppliers(self):
        return ft.Column([
            ft.Row([
                ft.Text("Suppliers", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton("Add Supplier", icon=ft.Icons.ADD, on_click=self._show_add_supplier,
                                  bgcolor=PRIMARY_COLOR, color="white"),
            ]),
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCAL_SHIPPING_OUTLINED,
                            size=48, color="#BDC3C7"),
                    ft.Text("Supplier management coming soon",
                            size=14, color=TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30,
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )
        ], spacing=10)

    def _build_reports(self):
        return ft.Column([
            ft.Text("Reports", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.GridView(
                expand=True,
                runs_count=2,
                spacing=20,
                controls=[
                    self._report_card("Stock Valuation", "View total inventory value",
                                      ft.Icons.ATTACH_MONEY, PRIMARY_COLOR),
                    self._report_card("Low Stock Report", "Products below minimum stock",
                                      ft.Icons.WARNING, WARNING_COLOR),
                    self._report_card("Stock Movement", "Transaction history report",
                                      ft.Icons.SWAP_HORIZ, SUCCESS_COLOR),
                    self._report_card("Category Report", "Products by category",
                                      ft.Icons.CATEGORY, "#9B59B6"),
                ]
            )
        ], spacing=10)

    def _report_card(self, title, description, icon, color):
        return ft.Card(
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Icon(icon, size=40, color=color),
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(description, size=12, color=TEXT_MUTED),
                    ft.Container(height=10),
                    ft.ElevatedButton("Generate", on_click=lambda e: self._show_success(f"Generating {title}..."),
                                      bgcolor=color, color="white", height=35),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
            ),
            elevation=2
        )

    def _build_settings(self):
        return ft.Column([
            ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text("Inventory Defaults", size=16,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(height=15),
                        ft.Text("Default Low Stock Threshold", size=14),
                        ft.Slider(min=1, max=100, value=10,
                                  divisions=9, label="10 units"),
                        ft.Container(height=15),
                        ft.Text("Default Unit of Measurement", size=14),
                        ft.Dropdown(
                            width=200,
                            options=[
                                ft.dropdown.Option("pcs", "Pieces (pcs)"),
                                ft.dropdown.Option("kg", "Kilograms (kg)"),
                                ft.dropdown.Option("liter", "Liters"),
                                ft.dropdown.Option("meter", "Meters"),
                            ],
                            value="pcs"
                        ),
                    ], spacing=15)
                ),
                elevation=2
            )
        ], spacing=10)

    # Database operations
    def _get_stats(self):
        db = get_db_session()
        try:
            total = db.query(Product).filter(Product.is_active == True).count()
            low = db.query(Product).filter(Product.is_active == True,
                                           Product.current_stock <= Product.min_stock).count()
            out = db.query(Product).filter(Product.is_active == True,
                                           Product.current_stock == 0).count()
            cats = db.query(InventoryCategory).filter(
                InventoryCategory.is_active == True).count()

            # Calculate total value
            products = db.query(Product).filter(
                Product.is_active == True).all()
            total_value = sum(
                [(p.current_stock or 0) * (p.sale_price or 0) for p in products])

            return {'total': total, 'low': low, 'out': out, 'cats': cats, 'value': total_value}
        except:
            return {'total': 0, 'low': 0, 'out': 0, 'cats': 0, 'value': 0}
        finally:
            db.close()

    def _get_all_products(self):
        db = get_db_session()
        try:
            query = db.query(Product).filter(Product.is_active == True)
            if self.selected_category:
                query = query.filter(Product.category_id ==
                                     self.selected_category)
            return query.order_by(Product.name).all()
        except:
            return []
        finally:
            db.close()

    def _get_all_categories(self):
        db = get_db_session()
        try:
            return db.query(InventoryCategory).filter(
                InventoryCategory.is_active == True
            ).order_by(InventoryCategory.name).all()
        except:
            return []
        finally:
            db.close()

    def _get_all_transactions(self):
        db = get_db_session()
        try:
            return db.query(InventoryTransaction).order_by(
                InventoryTransaction.created_at.desc()
            ).limit(50).all()
        except:
            return []
        finally:
            db.close()

    # Actions
    def go_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def _set_view_mode(self, mode):
        self.view_mode = mode
        self.content = self._build_content()
        self._page.update()

    def _on_search(self, e):
        self.search_query = e.control.value
        self._page.update()

    def _filter_by_category(self, category_id):
        if category_id is None:
            self.selected_category = None
        else:
            self.selected_category = category_id
        self.content = self._build_content()
        self._page.update()

    def _filter_transactions(self, e):
        self._page.update()

    def show_add_product_dialog(self, e):
        name_f = ft.TextField(label="Product Name", width=350)
        sku_f = ft.TextField(label="SKU", width=200)
        desc_f = ft.TextField(label="Description", width=350, multiline=True)

        # Category dropdown
        db = get_db_session()
        try:
            categories = db.query(InventoryCategory).filter(
                InventoryCategory.is_active == True).all()
            cat_options = [ft.dropdown.Option("", "No Category")]
            for cat in categories:
                cat_options.append(ft.dropdown.Option(str(cat.id), cat.name))
        finally:
            db.close()

        cat_dd = ft.Dropdown(label="Category", width=200, options=cat_options)

        unit_f = ft.TextField(label="Unit", width=100, value="pcs")
        stock_f = ft.TextField(label="Current Stock", width=120, value="0")
        min_stock_f = ft.TextField(label="Min Stock", width=120, value="10")
        max_stock_f = ft.TextField(label="Max Stock", width=120, value="100")
        purchase_f = ft.TextField(label="Purchase Price", width=150, value="0")
        sale_f = ft.TextField(label="Sale Price", width=150, value="0")

        def save(e):
            if not name_f.value or not sku_f.value:
                self._show_error("Name and SKU required")
                return
            db = get_db_session()
            try:
                p = Product(
                    name=name_f.value,
                    sku=sku_f.value,
                    description=desc_f.value,
                    category_id=int(cat_dd.value) if cat_dd.value else None,
                    unit=unit_f.value or "pcs",
                    current_stock=int(
                        stock_f.value) if stock_f.value.isdigit() else 0,
                    min_stock=int(
                        min_stock_f.value) if min_stock_f.value.isdigit() else 10,
                    max_stock=int(
                        max_stock_f.value) if max_stock_f.value.isdigit() else 100,
                    purchase_price=float(purchase_f.value) if purchase_f.value.replace(
                        '.', '', 1).isdigit() else 0,
                    sale_price=float(sale_f.value) if sale_f.value.replace(
                        '.', '', 1).isdigit() else 0,
                )
                db.add(p)
                db.commit()
                self._show_success("Product added!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Product"),
            content=ft.Column([name_f, sku_f, desc_f, cat_dd,
                               ft.Row(
                                   [unit_f, stock_f, min_stock_f, max_stock_f]),
                               ft.Row([purchase_f, sale_f])],
                              spacing=12),
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

    def _edit_product(self, product_id):
        db = get_db_session()
        try:
            product = db.query(Product).filter(
                Product.id == product_id).first()
            if product:
                self._show_edit_product_dialog(product)
        finally:
            db.close()

    def _show_edit_product_dialog(self, product):
        name_f = ft.TextField(label="Product Name",
                              width=350, value=product.name)
        sku_f = ft.TextField(label="SKU", width=200, value=product.sku)
        desc_f = ft.TextField(label="Description", width=350,
                              multiline=True, value=product.description or "")

        # Category dropdown
        db = get_db_session()
        try:
            categories = db.query(InventoryCategory).filter(
                InventoryCategory.is_active == True).all()
            cat_options = [ft.dropdown.Option("", "No Category")]
            for cat in categories:
                cat_options.append(ft.dropdown.Option(str(cat.id), cat.name))
            selected_cat = str(
                product.category_id) if product.category_id else ""
        finally:
            db.close()

        cat_dd = ft.Dropdown(label="Category", width=200,
                             options=cat_options, value=selected_cat)

        unit_f = ft.TextField(label="Unit", width=100,
                              value=product.unit or "pcs")
        stock_f = ft.TextField(label="Current Stock",
                               width=120, value=str(product.current_stock or 0))
        min_stock_f = ft.TextField(
            label="Min Stock", width=120, value=str(product.min_stock or 0))
        max_stock_f = ft.TextField(
            label="Max Stock", width=120, value=str(product.max_stock or 0))
        purchase_f = ft.TextField(
            label="Purchase Price", width=150, value=str(product.purchase_price or 0))
        sale_f = ft.TextField(label="Sale Price", width=150,
                              value=str(product.sale_price or 0))

        def save(e):
            if not name_f.value or not sku_f.value:
                self._show_error("Name and SKU required")
                return
            db = get_db_session()
            try:
                p = db.query(Product).filter(Product.id == product.id).first()
                if p:
                    p.name = name_f.value
                    p.sku = sku_f.value
                    p.description = desc_f.value
                    p.category_id = int(cat_dd.value) if cat_dd.value else None
                    p.unit = unit_f.value or "pcs"
                    p.current_stock = int(
                        stock_f.value) if stock_f.value.isdigit() else 0
                    p.min_stock = int(
                        min_stock_f.value) if min_stock_f.value.isdigit() else 0
                    p.max_stock = int(
                        max_stock_f.value) if max_stock_f.value.isdigit() else 100
                    p.purchase_price = float(purchase_f.value) if purchase_f.value.replace(
                        '.', '', 1).isdigit() else 0
                    p.sale_price = float(sale_f.value) if sale_f.value.replace(
                        '.', '', 1).isdigit() else 0
                    db.commit()
                self._show_success("Product updated!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Product"),
            content=ft.Column([name_f, sku_f, desc_f, cat_dd,
                               ft.Row(
                                   [unit_f, stock_f, min_stock_f, max_stock_f]),
                               ft.Row([purchase_f, sale_f])],
                              spacing=12),
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

    def _delete_product(self, product_id):
        def confirm(e):
            db = get_db_session()
            try:
                db.query(Product).filter(Product.id == product_id).update(
                    {Product.is_active: False})
                db.commit()
                self._show_success("Product deleted")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Product?"),
            content=ft.Text("Are you sure? This action can be reversed."),
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

    def show_add_category_dialog(self, e):
        name_f = ft.TextField(label="Category Name", width=350)
        desc_f = ft.TextField(label="Description", width=350, multiline=True)

        def save(e):
            if not name_f.value:
                self._show_error("Category name required")
                return
            db = get_db_session()
            try:
                cat = InventoryCategory(
                    name=name_f.value,
                    description=desc_f.value
                )
                db.add(cat)
                db.commit()
                self._show_success("Category added!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Category"),
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

    def _edit_category(self, category_id):
        db = get_db_session()
        try:
            category = db.query(InventoryCategory).filter(
                InventoryCategory.id == category_id).first()
            if category:
                self._show_edit_category_dialog(category)
        finally:
            db.close()

    def _show_edit_category_dialog(self, category):
        name_f = ft.TextField(label="Category Name",
                              width=350, value=category.name)
        desc_f = ft.TextField(label="Description", width=350,
                              multiline=True, value=category.description or "")

        def save(e):
            if not name_f.value:
                self._show_error("Category name required")
                return
            db = get_db_session()
            try:
                cat = db.query(InventoryCategory).filter(
                    InventoryCategory.id == category.id).first()
                if cat:
                    cat.name = name_f.value
                    cat.description = desc_f.value
                    db.commit()
                self._show_success("Category updated!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Category"),
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

    def _delete_category(self, category_id):
        def confirm(e):
            db = get_db_session()
            try:
                db.query(InventoryCategory).filter(InventoryCategory.id == category_id).update(
                    {InventoryCategory.is_active: False})
                db.commit()
                self._show_success("Category deleted")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Category?"),
            content=ft.Text(
                "Products in this category will become uncategorized."),
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

    def show_add_transaction_dialog(self, e):
        # Get products
        db = get_db_session()
        try:
            products = db.query(Product).filter(
                Product.is_active == True).all()
            product_options = [ft.dropdown.Option(
                str(p.id), f"{p.name} (Stock: {p.current_stock})") for p in products]
        finally:
            db.close()

        product_dd = ft.Dropdown(
            label="Product", width=300, options=product_options)
        type_dd = ft.Dropdown(
            label="Transaction Type",
            width=200,
            options=[
                ft.dropdown.Option("purchase", "Purchase (Stock In)"),
                ft.dropdown.Option("sale", "Sale (Stock Out)"),
                ft.dropdown.Option("adjustment", "Adjustment"),
                ft.dropdown.Option("return", "Return"),
            ],
            value="purchase"
        )
        quantity_f = ft.TextField(label="Quantity", width=150, value="1")
        notes_f = ft.TextField(label="Notes", width=350, multiline=True)

        def save(e):
            if not product_dd.value or not quantity_f.value:
                self._show_error("Product and quantity required")
                return

            db = get_db_session()
            try:
                product_id = int(product_dd.value)
                quantity = int(
                    quantity_f.value) if quantity_f.value.isdigit() else 0
                trans_type = type_dd.value

                product = db.query(Product).filter(
                    Product.id == product_id).first()
                if not product:
                    self._show_error("Product not found")
                    return

                # Calculate new stock
                quantity_before = product.current_stock or 0
                if trans_type in ["purchase", "return"]:
                    quantity_after = quantity_before + quantity
                elif trans_type in ["sale", "adjustment"]:
                    quantity_after = max(0, quantity_before - quantity)
                else:
                    quantity_after = quantity_before

                # Update product stock
                product.current_stock = quantity_after

                # Create transaction
                trans = InventoryTransaction(
                    product_id=product_id,
                    transaction_type=trans_type,
                    quantity=quantity,
                    quantity_before=quantity_before,
                    quantity_after=quantity_after,
                    notes=notes_f.value,
                    created_by_id=self.user.id if hasattr(
                        self.user, 'id') else None
                )
                db.add(trans)
                db.commit()

                self._show_success("Transaction recorded!")
                self._close_dialog()
                self.content = self._build_content()
                self._page.update()
            except Exception as ex:
                self._show_error(f"Error: {ex}")
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Transaction"),
            content=ft.Column(
                [product_dd, type_dd, quantity_f, notes_f], spacing=15),
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

    def _delete_transaction(self, transaction_id):
        def confirm(e):
            self._show_success("Transaction deletion - contact admin")
            self._close_dialog()
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Transaction?"),
            content=ft.Text(
                "This will also reverse the stock change. Contact admin for this action."),
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

    def _show_add_supplier(self, e):
        self._show_success("Supplier management coming soon")

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


def show_inventory(page, user):
    """Main entry point"""
    page.clean()
    page.add(InventoryScreen(page, user))
