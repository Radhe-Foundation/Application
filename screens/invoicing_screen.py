"""
Vernika HRA - Invoicing Screen (Rebuilt)
Invoice & Billing Management System - Industry Level
"""

import flet as ft
from datetime import datetime, date, timedelta
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Invoice, InvoiceItem, Payment, CRMCustomer, CRMDeal
from sqlalchemy import func


# Theme colors - Professional palette
PRIMARY = "#1E3A5F"  # Deep navy blue
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

# Invoice status colors
STATUS_COLORS = {
    "draft": "#9E9E9E",
    "sent": INFO,
    "viewed": "#7C4DFF",
    "paid": SUCCESS,
    "partial": WARNING,
    "overdue": ERROR,
    "cancelled": "#757575",
}


class InvoicingScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.current_view = "list"  # list, create, view, edit
        self.selected_invoice = None
        self.invoice_items = []  # For creating/editing invoices
        self.content = self._build_content()

    def refresh(self):
        """Refresh the invoicing content"""
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
        """Build the invoicing content"""
        # Header
        header = self._create_header()

        # Content based on current view
        if self.current_view == "list":
            content = self._build_invoices_list()
        elif self.current_view == "create":
            content = self._build_invoice_form()
        elif self.current_view == "view":
            content = self._build_invoice_detail()
        elif self.current_view == "edit":
            content = self._build_invoice_form(edit=True)
        else:
            content = self._build_invoices_list()

        return ft.ListView([
            header,
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
                    ft.Icon(ft.Icons.RECEIPT_LONG, color="WHITE", size=28),
                    ft.Text("Invoicing & Billing", size=20, color="WHITE",
                            weight=ft.FontWeight.BOLD),
                ], spacing=15),
                ft.Container(expand=True),
                ft.Row([
                    ft.FilledButton(
                        "New Invoice",
                        icon=ft.Icons.ADD,
                        bgcolor=SUCCESS,
                        color="WHITE",
                        on_click=self._show_create_invoice,
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

    # ============ INVOICES LIST ============

    def _build_invoices_list(self):
        """Build invoices list view"""
        invoices = self._get_invoices()

        # Stats
        total_issued = sum(i.total_amount for i in invoices)
        total_paid = sum(i.paid_amount for i in invoices)
        total_due = total_issued - total_paid
        overdue_count = len([i for i in invoices if i.status == "overdue"])

        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_kpi_card("Total Invoices", len(
                    invoices), ft.Icons.RECEIPT, INFO),
                self._create_kpi_card(
                    "Total Issued", f"₹{total_issued:,.0f}", ft.Icons.ATTACH_MONEY, WARNING),
                self._create_kpi_card(
                    "Total Paid", f"₹{total_paid:,.0f}", ft.Icons.CHECK_CIRCLE, SUCCESS),
                self._create_kpi_card(
                    "Total Due", f"₹{total_due:,.0f}", ft.Icons.WARNING, ERROR),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )

        # Filter bar
        filter_bar = self._create_filter_bar()

        # Invoices table
        if invoices:
            invoices_table = self._create_invoices_table(invoices)
        else:
            invoices_table = self._create_empty_state(
                "No invoices found", "Create your first invoice",
                ft.Icons.RECEIPT_LONG, self._show_create_invoice
            )

        return ft.Column([
            filter_bar,
            stats_row,
            ft.Container(content=invoices_table, expand=True),
        ], spacing=0, expand=True)

    def _create_filter_bar(self):
        """Create filter bar"""
        search_field = ft.TextField(
            hint_text="Search invoices...",
            prefix_icon=ft.Icons.SEARCH,
            width=300,
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY,
        )

        status_filter = ft.Dropdown(
            hint_text="Status",
            width=150,
            options=[
                ft.dropdown.Option("all", "All"),
                ft.dropdown.Option("draft", "Draft"),
                ft.dropdown.Option("sent", "Sent"),
                ft.dropdown.Option("paid", "Paid"),
                ft.dropdown.Option("partial", "Partial"),
                ft.dropdown.Option("overdue", "Overdue"),
            ],
            value="all",
            border_color=BORDER_COLOR,
        )

        return ft.Container(
            content=ft.Row([
                search_field,
                status_filter,
                ft.Container(expand=True),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _create_invoices_table(self, invoices):
        """Create invoices table using ListView for scrolling"""
        if not invoices:
            return self._create_empty_state(
                "No invoices found", "Create your first invoice",
                ft.Icons.RECEIPT_LONG, self._show_create_invoice
            )

        return ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=10,
                padding=15,
                controls=[
                    self._create_invoice_card(inv) for inv in invoices
                ]
            ),
            bgcolor=SURFACE,
            padding=10,
            border_radius=10,
            expand=True,
        )

    def _create_invoice_row(self, invoice):
        """Create invoice table row"""
        status_color = STATUS_COLORS.get(invoice.status, "#666")
        due = invoice.total_amount - invoice.paid_amount

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(invoice.invoice_number or "",
                            weight=ft.FontWeight.W_500)),
                ft.DataCell(
                    ft.Text(invoice.customer.name if invoice.customer else "N/A")),
                ft.DataCell(ft.Text(invoice.invoice_date.strftime(
                    "%d %b %Y") if invoice.invoice_date else "N/A")),
                ft.DataCell(ft.Text(invoice.due_date.strftime(
                    "%d %b %Y") if invoice.due_date else "N/A")),
                ft.DataCell(ft.Text(f"₹{invoice.total_amount:,.0f}")),
                ft.DataCell(ft.Text(f"₹{invoice.paid_amount:,.0f}")),
                ft.DataCell(ft.Container(
                    content=ft.Text(invoice.status.upper(
                    ) if invoice.status else "DRAFT", size=10, color="WHITE"),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=10,
                )),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.VISIBILITY, icon_size=18, tooltip="View",
                                  on_click=lambda e: self._view_invoice(invoice)),
                    ft.IconButton(ft.Icons.EDIT, icon_size=18, tooltip="Edit",
                                  on_click=lambda e: self._edit_invoice(invoice)),
                    ft.IconButton(ft.Icons.PAYMENT, icon_size=18, tooltip="Record Payment",
                                  on_click=lambda e: self._show_payment_dialog(invoice)),
                    ft.IconButton(ft.Icons.DELETE, icon_size=18, tooltip="Delete",
                                  on_click=lambda e: self._delete_invoice(invoice)),
                ], spacing=0)),
            ],
        )

    def _create_invoice_card(self, invoice):
        """Create invoice card for scrollable list view"""
        status_color = STATUS_COLORS.get(invoice.status, "#666")

        invoice_num = invoice.invoice_number or "N/A"
        customer_name = invoice.customer.name if invoice.customer else "N/A"
        invoice_date = invoice.invoice_date.strftime(
            "%d %b %Y") if invoice.invoice_date else "N/A"
        due_date = invoice.due_date.strftime(
            "%d %b %Y") if invoice.due_date else "N/A"
        total = f"₹{invoice.total_amount:,.0f}"
        paid = f"₹{invoice.paid_amount:,.0f}"
        status = invoice.status.upper() if invoice.status else "DRAFT"

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(invoice_num, size=14,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(customer_name, size=12, color=TEXT_SECONDARY),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text("Date", size=10, color=TEXT_SECONDARY),
                        ft.Text(invoice_date, size=12),
                    ], spacing=0),
                    ft.Column([
                        ft.Text("Due", size=10, color=TEXT_SECONDARY),
                        ft.Text(due_date, size=12),
                    ], spacing=0),
                    ft.Column([
                        ft.Text("Total", size=10, color=TEXT_SECONDARY),
                        ft.Text(total, size=14, weight=ft.FontWeight.BOLD),
                    ], spacing=0),
                    ft.Column([
                        ft.Text("Paid", size=10, color=TEXT_SECONDARY),
                        ft.Text(paid, size=14,
                                weight=ft.FontWeight.BOLD, color=SUCCESS),
                    ], spacing=0),
                    ft.Container(
                        content=ft.Text(status, size=10, color="WHITE"),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(
                            horizontal=12, vertical=6),
                        border_radius=15,
                    ),
                    ft.Row([
                        ft.IconButton(ft.Icons.VISIBILITY, icon_size=20, tooltip="View",
                                      on_click=lambda e: self._view_invoice(invoice)),
                        ft.IconButton(ft.Icons.EDIT, icon_size=20, tooltip="Edit",
                                      on_click=lambda e: self._edit_invoice(invoice)),
                        ft.IconButton(ft.Icons.PAYMENT, icon_size=20, tooltip="Record Payment",
                                      on_click=lambda e: self._show_payment_dialog(invoice)),
                        ft.IconButton(ft.Icons.DELETE, icon_size=20, tooltip="Delete",
                                      on_click=lambda e: self._delete_invoice(invoice)),
                    ], spacing=5),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
            ),
            elevation=2,
        )

    def _create_invoice_item_row(self, item):
        """Create invoice item row for scrollable list"""
        desc = item.description or "N/A"
        qty = str(item.quantity) if item.quantity else "0"
        unit_price = f"₹{item.unit_price:,.2f}" if item.unit_price else "₹0.00"
        tax = f"{item.tax_rate}%" if item.tax_rate else "0%"
        amount = f"₹{item.amount:,.2f}" if item.amount else "₹0.00"

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(desc, size=13),
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(qty, size=13, weight=ft.FontWeight.BOLD),
                    width=50,
                ),
                ft.Container(
                    content=ft.Text(unit_price, size=13),
                    width=100,
                ),
                ft.Container(
                    content=ft.Text(tax, size=12),
                    width=60,
                ),
                ft.Container(
                    content=ft.Text(amount, size=13,
                                    weight=ft.FontWeight.BOLD, color=PRIMARY),
                    width=100,
                ),
            ], spacing=10),
            padding=12,
            bgcolor="#F9FAFB",
            border_radius=8,
        )

    # ============ INVOICE FORM ============

    def _build_invoice_form(self, edit=False):
        """Build invoice creation/edit form"""
        customers = self._get_customers()

        # Pre-fill data if editing
        selected_customer = None
        invoice_number_val = ""
        invoice_date_val = date.today().strftime("%Y-%m-%d")
        due_date_val = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        notes_val = ""
        terms_val = "Payment due within 30 days"

        if edit and self.selected_invoice:
            invoice = self.selected_invoice
            selected_customer = invoice.customer_id
            invoice_number_val = invoice.invoice_number or ""
            invoice_date_val = invoice.invoice_date.strftime(
                "%Y-%m-%d") if invoice.invoice_date else ""
            due_date_val = invoice.due_date.strftime(
                "%Y-%m-%d") if invoice.due_date else ""
            notes_val = invoice.notes or ""
            terms_val = invoice.terms or "Payment due within 30 days"
            # Load existing items
            self.invoice_items = []
            for item in invoice.items:
                self.invoice_items.append({
                    'description': item.description,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'tax_rate': item.tax_rate,
                    'amount': item.amount,
                })
        elif not edit:
            invoice_number_val = self._generate_invoice_number()

        # Form fields
        invoice_number = ft.TextField(
            label="Invoice Number",
            value=invoice_number_val,
            read_only=True,
            border_color=PRIMARY,
        )

        customer_dropdown = ft.Dropdown(
            label="Customer *",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in customers] if customers else [
                ft.dropdown.Option("", "No customers")],
            value=str(selected_customer) if selected_customer else None,
            border_color=PRIMARY,
        )

        invoice_date = ft.TextField(
            label="Invoice Date",
            value=invoice_date_val,
            hint_text="YYYY-MM-DD",
            border_color=PRIMARY,
        )

        due_date = ft.TextField(
            label="Due Date",
            value=due_date_val,
            hint_text="YYYY-MM-DD",
            border_color=PRIMARY,
        )

        notes = ft.TextField(
            label="Notes",
            value=notes_val,
            multiline=True,
            min_lines=2,
            border_color=PRIMARY,
        )

        terms = ft.TextField(
            label="Terms & Conditions",
            value=terms_val,
            multiline=True,
            min_lines=2,
            border_color=PRIMARY,
        )

        # Items section
        items_header = ft.Container(
            content=ft.Row([
                ft.Text("Invoice Items", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton("Add Item", icon=ft.Icons.ADD,
                                  on_click=self._add_item, bgcolor=PRIMARY, color="WHITE"),
            ], spacing=10),
            margin=ft.margin.only(top=20),
        )

        # Items table
        items_list = ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Description")),
                    ft.DataColumn(ft.Text("Qty"), numeric=True),
                    ft.DataColumn(ft.Text("Unit Price"), numeric=True),
                    ft.DataColumn(ft.Text("Tax %"), numeric=True),
                    ft.DataColumn(ft.Text("Amount"), numeric=True),
                    ft.DataColumn(ft.Text("")),
                ],
                rows=self._get_items_rows(),
            ),
            bgcolor="white",
            padding=10,
            border_radius=8,
        )

        # Totals
        subtotal = sum(item['amount'] for item in self.invoice_items)
        tax_total = sum(item['amount'] * item['tax_rate'] /
                        100 for item in self.invoice_items)
        total = subtotal + tax_total

        totals = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Subtotal:", size=14),
                    ft.Container(expand=True),
                    ft.Text(f"₹{subtotal:,.2f}", size=14,
                            weight=ft.FontWeight.BOLD),
                ]),
                ft.Row([
                    ft.Text("Tax:", size=14),
                    ft.Container(expand=True),
                    ft.Text(f"₹{tax_total:,.2f}", size=14,
                            weight=ft.FontWeight.BOLD),
                ]),
                ft.Divider(),
                ft.Row([
                    ft.Text("Total:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Text(f"₹{total:,.2f}", size=20,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                ]),
            ], spacing=8),
            padding=20,
            bgcolor="white",
            border_radius=8,
            margin=ft.margin.only(top=10),
            width=300,
            alignment=ft.alignment.Alignment(1, 0),
        )

        # Buttons
        buttons = ft.Row([
            ft.ElevatedButton(
                "Save as Draft", on_click=lambda e: self._save_invoice("draft"), bgcolor=PRIMARY, color="WHITE"),
            ft.ElevatedButton("Save & Send", on_click=lambda e: self._save_invoice(
                "sent"), bgcolor=SUCCESS, color="WHITE"),
            ft.TextButton("Cancel", on_click=self._cancel_form),
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([invoice_number, invoice_date,
                               due_date], spacing=15),
                        customer_dropdown,
                        notes,
                        terms,
                    ], spacing=15),
                    bgcolor="white",
                    padding=25,
                    border_radius=10,
                ),
                items_header,
                items_list,
                totals,
                ft.Container(height=20),
                buttons,
            ]),
            padding=25,
        )

    def _get_items_rows(self):
        """Get rows for items table"""
        rows = []
        for i, item in enumerate(self.invoice_items):
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item['description'])),
                        ft.DataCell(ft.Text(str(item['quantity']))),
                        ft.DataCell(ft.Text(f"₹{item['unit_price']:,.2f}")),
                        ft.DataCell(ft.Text(f"{item['tax_rate']}%")),
                        ft.DataCell(ft.Text(f"₹{item['amount']:,.2f}")),
                        ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_size=18,
                                                  on_click=lambda e, idx=i: self._remove_item(idx))),
                    ],
                )
            )
        return rows

    # ============ INVOICE DETAIL ============

    def _build_invoice_detail(self):
        """Build invoice detail view"""
        if not self.selected_invoice:
            return ft.Container()

        invoice = self.selected_invoice
        status_color = STATUS_COLORS.get(invoice.status, "#666")

        # Invoice header
        header_section = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("INVOICE", size=28,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Text(f"#{invoice.invoice_number}",
                            size=16, color=TEXT_SECONDARY),
                ]),
                ft.Container(expand=True),
                ft.Column([
                    ft.Text("Status:", size=12, color=TEXT_SECONDARY),
                    ft.Container(
                        content=ft.Text(invoice.status.upper(
                        ) if invoice.status else "", size=12, color="WHITE"),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(
                            horizontal=12, vertical=6),
                        border_radius=15,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.END),
            ], spacing=10),
        )

        # Customer & Date info
        info_section = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Bill To:", size=12, color=TEXT_SECONDARY),
                    ft.Text(invoice.customer.name if invoice.customer else "N/A",
                            size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(invoice.customer.company if invoice.customer and invoice.customer.company else "",
                            size=14, color=TEXT_SECONDARY),
                    ft.Text(invoice.customer.email if invoice.customer and invoice.customer.email else "",
                            size=13, color=TEXT_SECONDARY),
                ], spacing=2),
                ft.Container(expand=True),
                ft.Column([
                    ft.Row([
                        ft.Text("Invoice Date: ", size=12,
                                color=TEXT_SECONDARY),
                        ft.Text(invoice.invoice_date.strftime("%d %b %Y")
                                if invoice.invoice_date else "N/A", size=12),
                    ]),
                    ft.Row([
                        ft.Text("Due Date: ", size=12, color=TEXT_SECONDARY),
                        ft.Text(invoice.due_date.strftime("%d %b %Y")
                                if invoice.due_date else "N/A", size=12),
                    ]),
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
            ], spacing=10),
            bgcolor="white",
            padding=25,
            border_radius=10,
        )

        # Items table
        items = self._get_invoice_items(invoice.id)
        # Items table - using ListView for scrolling
        items_list = ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=10,
                padding=15,
                controls=[
                    self._create_invoice_item_row(item) for item in items
                ] if items else [
                    ft.Container(
                        content=ft.Text("No items", size=12,
                                        color=TEXT_SECONDARY),
                        padding=10,
                    )
                ]
            ),
            bgcolor="white",
            padding=10,
            border_radius=10,
            expand=True,
        )

        # Totals
        due_amount = invoice.total_amount - invoice.paid_amount
        totals_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Subtotal:", size=14),
                    ft.Container(expand=True),
                    ft.Text(f"₹{invoice.subtotal:,.2f}", size=14),
                ]),
                ft.Row([
                    ft.Text("Tax:", size=14),
                    ft.Container(expand=True),
                    ft.Text(f"₹{invoice.tax_amount:,.2f}", size=14),
                ]),
                ft.Divider(),
                ft.Row([
                    ft.Text("Total:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Text(f"₹{invoice.total_amount:,.2f}", size=20,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                ]),
                ft.Row([
                    ft.Text("Paid:", size=14),
                    ft.Container(expand=True),
                    ft.Text(f"₹{invoice.paid_amount:,.2f}",
                            size=14, color=SUCCESS),
                ]),
                ft.Divider(),
                ft.Row([
                    ft.Text("Due:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Text(f"₹{due_amount:,.2f}", size=20, weight=ft.FontWeight.BOLD,
                            color=ERROR if due_amount > 0 else SUCCESS),
                ]),
            ], spacing=8),
            padding=20,
            bgcolor="white",
            border_radius=10,
            width=300,
            alignment=ft.alignment.Alignment(1, 0),
        )

        # Actions
        actions = ft.Row([
            ft.ElevatedButton("Record Payment", icon=ft.Icons.PAYMENT, bgcolor=SUCCESS, color="WHITE",
                              on_click=lambda e: self._show_payment_dialog(invoice)),
            ft.ElevatedButton("Edit Invoice", icon=ft.Icons.EDIT, bgcolor=PRIMARY, color="WHITE",
                              on_click=lambda e: self._edit_invoice(invoice)),
            ft.TextButton("Back to List", on_click=self._back_to_list),
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                header_section,
                info_section,
                items_list,
                totals_section,
                ft.Container(height=20),
                actions,
            ]),
            padding=25,
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
                ft.ElevatedButton("Create Invoice", icon=ft.Icons.ADD,
                                  bgcolor=PRIMARY, color="WHITE", on_click=action),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=50,
            alignment=ft.alignment.Alignment(0, 0),
        )

    def _get_invoices(self):
        """Get all invoices"""
        session = self._get_db()
        try:
            invoices = session.query(Invoice).order_by(
                Invoice.created_at.desc()).all()
            return invoices
        except Exception as e:
            print(f"Error getting invoices: {e}")
            return []
        finally:
            session.close()

    def _get_customers(self):
        """Get all customers"""
        session = self._get_db()
        try:
            customers = session.query(CRMCustomer).filter(
                CRMCustomer.category.in_(["customer", "prospect"])
            ).all()
            return customers
        except Exception as e:
            print(f"Error getting customers: {e}")
            return []
        finally:
            session.close()

    def _get_invoice_items(self, invoice_id):
        """Get invoice items"""
        session = self._get_db()
        try:
            items = session.query(InvoiceItem).filter_by(
                invoice_id=invoice_id).all()
            return items
        except Exception as e:
            print(f"Error getting invoice items: {e}")
            return []
        finally:
            session.close()

    def _generate_invoice_number(self):
        """Generate invoice number"""
        session = self._get_db()
        try:
            count = session.query(Invoice).count()
            return f"INV-{datetime.now().year}-{str(count + 1).zfill(4)}"
        finally:
            session.close()

    # ============ ACTIONS ============

    def _show_create_invoice(self, e):
        """Show create invoice view"""
        self.invoice_items = []
        self.current_view = "create"
        self.selected_invoice = None
        self.refresh()

    def _edit_invoice(self, invoice):
        """Edit invoice"""
        self.selected_invoice = invoice
        self.current_view = "edit"
        self.refresh()

    def _view_invoice(self, invoice):
        """View invoice details"""
        self.selected_invoice = invoice
        self.current_view = "view"
        self.refresh()

    def _back_to_list(self):
        """Back to invoices list"""
        self.selected_invoice = None
        self.current_view = "list"
        self.refresh()

    def _cancel_form(self):
        """Cancel form and go back"""
        self.invoice_items = []
        self.selected_invoice = None
        self.current_view = "list"
        self.refresh()

    def _add_item(self, e):
        """Add new item to invoice"""
        desc_field = ft.TextField(
            label="Description *", hint_text="Item description", border_color=PRIMARY)
        qty_field = ft.TextField(
            label="Quantity", value="1", border_color=PRIMARY)
        price_field = ft.TextField(
            label="Unit Price", value="0", border_color=PRIMARY)
        tax_field = ft.TextField(
            label="Tax Rate %", value="0", border_color=PRIMARY)

        def add(e):
            if not desc_field.value:
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text("Description is required")))
                return

            qty = float(qty_field.value or 1)
            price = float(price_field.value or 0)
            tax = float(tax_field.value or 0)
            amount = qty * price

            self.invoice_items.append({
                'description': desc_field.value,
                'quantity': qty,
                'unit_price': price,
                'tax_rate': tax,
                'amount': amount,
            })
            self._page.close(dialog)
            self.refresh()

        dialog = ft.AlertDialog(
            title=ft.Text("Add Item"),
            content=ft.Column(
                [desc_field, qty_field, price_field, tax_field], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Add", on_click=add,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _remove_item(self, index):
        """Remove item from invoice"""
        if 0 <= index < len(self.invoice_items):
            self.invoice_items.pop(index)
            self.refresh()

    def _save_invoice(self, status):
        """Save invoice"""
        if not self.invoice_items:
            self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                "Please add at least one item"), bgcolor=ERROR))
            return

        # Get form values - we need to rebuild the form to get values
        # For simplicity, use stored items and defaults
        session = self._get_db()
        try:
            customers = self._get_customers()
            if not customers:
                self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                    "No customers found. Please add a customer first."), bgcolor=ERROR))
                return

            # If editing, use existing invoice
            if self.current_view == "edit" and self.selected_invoice:
                invoice = self.selected_invoice
                invoice.status = status
                invoice.invoice_date = date.today()
                invoice.due_date = date.today() + timedelta(days=30)
                invoice.notes = ""
                invoice.terms = "Payment due within 30 days"

                # Clear existing items
                for item in invoice.items:
                    session.delete(item)
                session.flush()
            else:
                # Create new invoice
                customer_id = customers[0].id
                subtotal = sum(item['amount'] for item in self.invoice_items)
                tax_total = sum(
                    item['amount'] * item['tax_rate'] / 100 for item in self.invoice_items)
                total = subtotal + tax_total

                invoice = Invoice(
                    invoice_number=self._generate_invoice_number(),
                    customer_id=customer_id,
                    invoice_date=date.today(),
                    due_date=date.today() + timedelta(days=30),
                    subtotal=subtotal,
                    tax_amount=tax_total,
                    total_amount=total,
                    status=status,
                    notes="",
                    terms="Payment due within 30 days",
                )
                session.add(invoice)
                session.flush()

            # Add items
            for item in self.invoice_items:
                invoice_item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=item['description'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    tax_rate=item['tax_rate'],
                    amount=item['amount'],
                )
                session.add(invoice_item)

            session.commit()
            self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                "Invoice saved successfully"), bgcolor=SUCCESS))
            self.current_view = "list"
            self.invoice_items = []
            self.selected_invoice = None
            self.refresh()
        except Exception as e:
            session.rollback()
            self._page.show_snackbar(ft.SnackBar(
                content=ft.Text(f"Error: {str(e)}"), bgcolor=ERROR))
        finally:
            session.close()

    def _delete_invoice(self, invoice):
        """Delete invoice"""
        def confirm_delete(e):
            session = self._get_db()
            try:
                # Delete items first
                session.query(InvoiceItem).filter_by(
                    invoice_id=invoice.id).delete()
                # Delete payments
                session.query(Payment).filter_by(
                    invoice_id=invoice.id).delete()
                # Delete invoice
                inv = session.query(Invoice).get(invoice.id)
                if inv:
                    session.delete(inv)
                session.commit()
                self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                    "Invoice deleted successfully"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Invoice"),
            content=ft.Text(
                f"Are you sure you want to delete invoice '{invoice.invoice_number}'?"),
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

    def _show_payment_dialog(self, invoice):
        """Show payment recording dialog"""
        amount_field = ft.TextField(
            label="Amount",
            value=str(invoice.total_amount - invoice.paid_amount),
            border_color=PRIMARY,
        )
        method_dropdown = ft.Dropdown(
            label="Payment Method",
            options=[
                ft.dropdown.Option("cash", "Cash"),
                ft.dropdown.Option("bank_transfer", "Bank Transfer"),
                ft.dropdown.Option("upi", "UPI"),
                ft.dropdown.Option("card", "Card"),
                ft.dropdown.Option("cheque", "Cheque"),
            ],
            value="bank_transfer",
            border_color=PRIMARY,
        )
        ref_field = ft.TextField(
            label="Reference Number", border_color=PRIMARY)

        def record_payment(e):
            if not amount_field.value:
                return

            session = self._get_db()
            try:
                amount = float(amount_field.value)

                # Create payment
                payment = Payment(
                    invoice_id=invoice.id,
                    payment_number=f"PAY-{datetime.now().year}-{invoice.id}",
                    amount=amount,
                    payment_date=date.today(),
                    payment_method=method_dropdown.value,
                    reference_number=ref_field.value,
                )
                session.add(payment)

                # Update invoice
                invoice.paid_amount += amount
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = "paid"
                    invoice.paid_at = datetime.utcnow()
                else:
                    invoice.status = "partial"

                session.commit()
                self._page.show_snackbar(ft.SnackBar(content=ft.Text(
                    "Payment recorded successfully"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._page.show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Record Payment"),
            content=ft.Column(
                [amount_field, method_dropdown, ref_field], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton(
                    "Record Payment", on_click=record_payment, bgcolor=SUCCESS, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _go_back(self, e):
        """Navigate back to home screen"""
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)


def show_invoicing(page, user):
    """Helper function to show invoicing"""
    page.clean()
    page.add(InvoicingScreen(page, user))
