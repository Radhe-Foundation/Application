"""
Vernika HRA - CRM Screen (Unified Tabbed Interface)
Comprehensive CRM with Leads, Contacts, Calendar, Events, Vendors, Warehouses, Assets, Contracts, Invoices
"""

import flet as ft
import os
from datetime import datetime, date, timedelta
from database.session_manager import get_db_session
from database.models import (
    Lead, Contact, CalendarEvent, Warehouse, Asset, Contract, Invoice, InvoiceItem,
    Supplier, Employee, User
)


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"
INFO = "#17A2B8"
BACKGROUND = "#F8F9FA"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"


class CRMScreen(ft.Container):
    """Unified CRM Screen with Tabbed Interface"""

    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND

        # Tab state
        self.current_tab = "leads"
        self.search_query = ""
        self.selected_item = None

        self.content = self._build_content()

    def _build_content(self):
        return ft.Column([
            self._build_header(),
            self._build_tabs(),
            self._build_tab_content(),
        ], expand=True, spacing=0)

    def _build_header(self):
        return ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Icon(ft.Icons.PEOPLE, color="white", size=28),
                ft.Text("CRM Dashboard", size=22, color="white",
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Add New",
                    icon=ft.Icons.ADD,
                    on_click=self._show_add_dialog,
                    style=ft.ButtonStyle(bgcolor=WARNING, color="white"),
                ),
            ])
        )

    def _build_tabs(self):
        tabs = [
            ("leads", "Leads", ft.Icons.LEADERBOARD),
            ("contacts", "Contacts", ft.Icons.CONTACTS),
            ("calendar", "Calendar", ft.Icons.CALENDAR_MONTH),
            ("vendors", "Vendors", ft.Icons.LOCAL_SHIPPING),
            ("warehouses", "Warehouses", ft.Icons.WAREHOUSE),
            ("assets", "Assets", ft.Icons.DEVICES),
            ("contracts", "Contracts", ft.Icons.DESCRIPTION),
            ("invoices", "Invoices", ft.Icons.RECEIPT),
        ]

        return ft.Container(
            bgcolor=SURFACE,
            padding=ft.padding.only(left=10, top=5, bottom=5),
            content=ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(
                                label,
                                size=13,
                                color=PRIMARY if self.current_tab == key else TEXT_SECONDARY,
                                weight=ft.FontWeight.BOLD if self.current_tab == key else ft.FontWeight.NORMAL
                            ),
                            padding=ft.padding.symmetric(
                                horizontal=15, vertical=8),
                            bgcolor=PRIMARY if self.current_tab == key else "transparent",
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
        if self.current_tab == "leads":
            return self._build_leads_view()
        elif self.current_tab == "contacts":
            return self._build_contacts_view()
        elif self.current_tab == "calendar":
            return self._build_calendar_view()
        elif self.current_tab == "vendors":
            return self._build_vendors_view()
        elif self.current_tab == "warehouses":
            return self._build_warehouses_view()
        elif self.current_tab == "assets":
            return self._build_assets_view()
        elif self.current_tab == "contracts":
            return self._build_contracts_view()
        elif self.current_tab == "invoices":
            return self._build_invoices_view()
        return self._build_leads_view()

    # ==================== LEADS ====================
    def _build_leads_view(self):
        leads = self._get_all_leads()

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Leads Management", size=20,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.TextField(
                        hint_text="Search leads...",
                        width=250,
                        prefix_icon=ft.Icons.SEARCH,
                        on_change=self._on_search
                    ),
                ]),
                ft.Container(height=15),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        expand=True,
                        spacing=10,
                        controls=self._build_lead_cards(leads) if leads else [
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.LEADERBOARD_OUTLINED,
                                            size=64, color="#BDC3C7"),
                                    ft.Text("No leads yet", size=14,
                                            color=TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                                alignment=ft.alignment.Alignment(0, 0)
                            )
                        ]
                    )
                )
            ], expand=True)
        )

    def _build_lead_cards(self, leads):
        cards = []
        for lead in leads:
            status_colors = {
                "new": INFO, "contacted": WARNING, "qualified": PRIMARY,
                "proposal": "#9C27B0", "negotiation": "#FF9800",
                "won": SUCCESS, "lost": ERROR
            }
            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Row([
                            ft.Container(
                                width=50, height=50,
                                bgcolor=f"{status_colors.get(lead.status, INFO)}20",
                                border_radius=25,
                                content=ft.Icon(ft.Icons.PERSON, color=status_colors.get(
                                    lead.status, INFO), size=25),
                                alignment=ft.alignment.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text(str(lead.name), size=15,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"{lead.company or 'No Company'} | {lead.email or 'No Email'}", size=11, color=TEXT_SECONDARY),
                                ft.Text(
                                    f"Value: ₹{lead.value:,.0f} | Source: {lead.source}", size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    lead.status.upper(), size=10, color="white"),
                                bgcolor=status_colors.get(lead.status, INFO),
                                padding=ft.padding.symmetric(
                                    horizontal=10, vertical=4),
                                border_radius=10,
                            ),
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, scale=0.7,
                                              on_click=lambda e, l=lead: self._edit_lead(l)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR, scale=0.7,
                                              on_click=lambda e, l=lead: self._delete_lead(l.id)),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_leads(self):
        db = get_db_session()
        try:
            return db.query(Lead).order_by(Lead.created_at.desc()).limit(50).all()
        except:
            return []
        finally:
            db.close()

    # ==================== CONTACTS ====================
    def _build_contacts_view(self):
        contacts = self._get_all_contacts()

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Contacts Management", size=20,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.TextField(
                        hint_text="Search contacts...",
                        width=250,
                        prefix_icon=ft.Icons.SEARCH,
                        on_change=self._on_search
                    ),
                ]),
                ft.Container(height=15),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        expand=True,
                        spacing=10,
                        controls=self._build_contact_cards(contacts) if contacts else [
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.CONTACTS_OUTLINED,
                                            size=64, color="#BDC3C7"),
                                    ft.Text("No contacts yet", size=14,
                                            color=TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                                alignment=ft.alignment.Alignment(0, 0)
                            )
                        ]
                    )
                )
            ], expand=True)
        )

    def _build_contact_cards(self, contacts):
        cards = []
        for contact in contacts:
            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Row([
                            ft.Container(
                                width=50, height=50,
                                bgcolor="#E3F2FD",
                                border_radius=25,
                                content=ft.Icon(
                                    ft.Icons.CONTACT_MAIL, color=PRIMARY, size=25),
                                alignment=ft.alignment.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text(
                                    f"{contact.first_name} {contact.last_name or ''}", size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"{contact.company or 'No Company'} | {contact.position or ''}", size=11, color=TEXT_SECONDARY),
                                ft.Text(
                                    f"{contact.email or ''} | {contact.phone or ''}", size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    "Customer" if contact.is_customer else "Contact", size=10, color="white"),
                                bgcolor=SUCCESS if contact.is_customer else INFO,
                                padding=ft.padding.symmetric(
                                    horizontal=10, vertical=4),
                                border_radius=10,
                            ),
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, scale=0.7,
                                              on_click=lambda e, c=contact: self._edit_contact(c)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR, scale=0.7,
                                              on_click=lambda e, c=contact: self._delete_contact(c.id)),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_contacts(self):
        db = get_db_session()
        try:
            return db.query(Contact).order_by(Contact.created_at.desc()).limit(50).all()
        except:
            return []
        finally:
            db.close()

    # ==================== CALENDAR ====================
    def _build_calendar_view(self):
        events = self._get_all_events()

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Calendar & Events", size=20,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton("Add Event", icon=ft.Icons.ADD, on_click=self._show_add_event_dialog,
                                      bgcolor=PRIMARY, color="white"),
                ]),
                ft.Container(height=15),
                # Calendar grid
                self._build_calendar_grid(events),
            ], expand=True)
        )

    def _build_calendar_grid(self, events):
        # Simple calendar view - current month
        today = datetime.now()
        first_day = today.replace(day=1)
        last_day = (first_day + timedelta(days=32)
                    ).replace(day=1) - timedelta(days=1)

        # Day headers
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        header_row = ft.Row([
            ft.Container(
                content=ft.Text(
                    d, size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
                width=100, alignment=ft.alignment.Alignment(0, 0)
            ) for d in days
        ], spacing=5)

        # Build calendar cells
        calendar_rows = []
        current_day = first_day
        while current_day <= last_day:
            row_cells = []
            for i in range(7):
                if current_day.month == today.month:
                    day_events = [
                        e for e in events if e.start_time.date() == current_day.date()]
                    is_today = current_day.date() == today.date()

                    cell = ft.Container(
                        width=100, height=80,
                        bgcolor=PRIMARY if is_today else SURFACE,
                        border=ft.border.all(1, "#E0E0E0"),
                        content=ft.Column([
                            ft.Text(str(current_day.day), size=14,
                                    weight=ft.FontWeight.BOLD, color="white" if is_today else TEXT_PRIMARY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        on_click=lambda e, d=current_day: self._show_day_events(
                            d, day_events)
                    )
                    row_cells.append(cell)
                else:
                    row_cells.append(ft.Container(
                        width=100, height=80, bgcolor="#F5F5F5"))

                current_day += timedelta(days=1)

            calendar_rows.append(ft.Row(row_cells, spacing=5))

        return ft.Column([header_row] + calendar_rows, spacing=5)

    def _get_all_events(self):
        db = get_db_session()
        try:
            return db.query(CalendarEvent).order_by(CalendarEvent.start_time).limit(100).all()
        except:
            return []
        finally:
            db.close()

    def _show_day_events(self, date, events):
        pass  # Show events for the day

    # ==================== VENDORS ====================
    def _build_vendors_view(self):
        vendors = self._get_all_vendors()

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Vendors", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                ]),
                ft.Container(height=15),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        expand=True,
                        spacing=10,
                        controls=self._build_vendor_cards(vendors) if vendors else [
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.LOCAL_SHIPPING_OUTLINED,
                                            size=64, color="#BDC3C7"),
                                    ft.Text("No vendors yet", size=14,
                                            color=TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                                alignment=ft.alignment.Alignment(0, 0)
                            )
                        ]
                    )
                )
            ], expand=True)
        )

    def _build_vendor_cards(self, vendors):
        cards = []
        for vendor in vendors:
            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Row([
                            ft.Container(
                                width=50, height=50,
                                bgcolor="#E8F4F8",
                                border_radius=8,
                                content=ft.Icon(
                                    ft.Icons.LOCAL_SHIPPING, color=PRIMARY, size=25),
                                alignment=ft.alignment.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text(str(vendor.name), size=15,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"{vendor.contact_person or 'No Contact'} | {vendor.email or ''}", size=11, color=TEXT_SECONDARY),
                                ft.Text(
                                    f"{vendor.phone or ''} | GST: {vendor.gst_number or 'N/A'}", size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    "Active" if vendor.is_active else "Inactive", size=10, color="white"),
                                bgcolor=SUCCESS if vendor.is_active else ERROR,
                                padding=ft.padding.symmetric(
                                    horizontal=10, vertical=4),
                                border_radius=10,
                            ),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_vendors(self):
        db = get_db_session()
        try:
            return db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.name).limit(50).all()
        except:
            return []
        finally:
            db.close()

    # ==================== WAREHOUSES ====================
    def _build_warehouses_view(self):
        warehouses = self._get_all_warehouses()

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Warehouses", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton("Add Warehouse", icon=ft.Icons.ADD, on_click=self._show_add_warehouse_dialog,
                                      bgcolor=PRIMARY, color="white"),
                ]),
                ft.Container(height=15),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        expand=True,
                        spacing=10,
                        controls=self._build_warehouse_cards(warehouses) if warehouses else [
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.WAREHOUSE_OUTLINED,
                                            size=64, color="#BDC3C7"),
                                    ft.Text("No warehouses yet",
                                            size=14, color=TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                                alignment=ft.alignment.Alignment(0, 0)
                            )
                        ]
                    )
                )
            ], expand=True)
        )

    def _build_warehouse_cards(self, warehouses):
        cards = []
        for wh in warehouses:
            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Row([
                            ft.Container(
                                width=50, height=50,
                                bgcolor="#FFF3E0",
                                border_radius=8,
                                content=ft.Icon(
                                    ft.Icons.WAREHOUSE, color=WARNING, size=25),
                                alignment=ft.alignment.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text(f"{wh.name} ({wh.code})",
                                        size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{wh.city or ''}, {wh.state or ''}",
                                        size=11, color=TEXT_SECONDARY),
                                ft.Text(
                                    f"Capacity: {wh.capacity or 0} units", size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    "Active" if wh.is_active else "Inactive", size=10, color="white"),
                                bgcolor=SUCCESS if wh.is_active else ERROR,
                                padding=ft.padding.symmetric(
                                    horizontal=10, vertical=4),
                                border_radius=10,
                            ),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_warehouses(self):
        db = get_db_session()
        try:
            return db.query(Warehouse).filter(Warehouse.is_active == True).order_by(Warehouse.name).limit(50).all()
        except:
            return []
        finally:
            db.close()

    # ==================== ASSETS ====================
    def _build_assets_view(self):
        assets = self._get_all_assets()

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Assets Management", size=20,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton("Add Asset", icon=ft.Icons.ADD, on_click=self._show_add_asset_dialog,
                                      bgcolor=PRIMARY, color="white"),
                ]),
                ft.Container(height=15),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        expand=True,
                        spacing=10,
                        controls=self._build_asset_cards(assets) if assets else [
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.DEVICES_OUTLINED,
                                            size=64, color="#BDC3C7"),
                                    ft.Text("No assets yet", size=14,
                                            color=TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                                alignment=ft.alignment.Alignment(0, 0)
                            )
                        ]
                    )
                )
            ], expand=True)
        )

    def _build_asset_cards(self, assets):
        cards = []
        for asset in assets:
            status_colors = {
                "available": SUCCESS, "in_use": INFO, "maintenance": WARNING, "retired": ERROR
            }
            category_icons = {
                "electronics": ft.Icons.COMPUTER, "furniture": ft.Icons.CHAIR,
                "vehicle": ft.Icons.DIRECTIONS_CAR, "machinery": ft.Icons.CONSTRUCTION,
                "software": ft.Icons.CODE, "other": ft.Icons.INVENTORY_2
            }
            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Row([
                            ft.Container(
                                width=50, height=50,
                                bgcolor="#E8F5E9",
                                border_radius=8,
                                content=ft.Icon(category_icons.get(asset.category, ft.Icons.INVENTORY_2),
                                                color=SUCCESS, size=25),
                                alignment=ft.alignment.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text(f"{asset.name} ({asset.asset_code})",
                                        size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"Category: {asset.category} | Value: ₹{asset.current_value:,.0f}", size=11, color=TEXT_SECONDARY),
                                ft.Text(
                                    f"SN: {asset.serial_number or 'N/A'}", size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    asset.status.upper(), size=10, color="white"),
                                bgcolor=status_colors.get(asset.status, INFO),
                                padding=ft.padding.symmetric(
                                    horizontal=10, vertical=4),
                                border_radius=10,
                            ),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_assets(self):
        db = get_db_session()
        try:
            return db.query(Asset).order_by(Asset.created_at.desc()).limit(50).all()
        except:
            return []
        finally:
            db.close()

    # ==================== CONTRACTS ====================
    def _build_contracts_view(self):
        contracts = self._get_all_contracts()

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Contracts Management", size=20,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton("Add Contract", icon=ft.Icons.ADD, on_click=self._show_add_contract_dialog,
                                      bgcolor=PRIMARY, color="white"),
                ]),
                ft.Container(height=15),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        expand=True,
                        spacing=10,
                        controls=self._build_contract_cards(contracts) if contracts else [
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED,
                                            size=64, color="#BDC3C7"),
                                    ft.Text("No contracts yet", size=14,
                                            color=TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                                alignment=ft.alignment.Alignment(0, 0)
                            )
                        ]
                    )
                )
            ], expand=True)
        )

    def _build_contract_cards(self, contracts):
        cards = []
        status_colors = {"draft": INFO, "active": SUCCESS,
                         "expired": ERROR, "terminated": "#9C27B0", "renewed": PRIMARY}
        for contract in contracts:
            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Row([
                            ft.Container(
                                width=50, height=50,
                                bgcolor="#F3E5F5",
                                border_radius=8,
                                content=ft.Icon(
                                    ft.Icons.DESCRIPTION, color="#9C27B0", size=25),
                                alignment=ft.alignment.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text(
                                    f"{contract.title} ({contract.contract_number})", size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"Type: {contract.contract_type} | Value: ₹{contract.value:,.0f}", size=11, color=TEXT_SECONDARY),
                                ft.Text(
                                    f"{contract.start_date} to {contract.end_date}", size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    contract.status.upper(), size=10, color="white"),
                                bgcolor=status_colors.get(
                                    contract.status, INFO),
                                padding=ft.padding.symmetric(
                                    horizontal=10, vertical=4),
                                border_radius=10,
                            ),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_contracts(self):
        db = get_db_session()
        try:
            return db.query(Contract).order_by(Contract.created_at.desc()).limit(50).all()
        except:
            return []
        finally:
            db.close()

    # ==================== INVOICES ====================
    def _build_invoices_view(self):
        invoices = self._get_all_invoices()

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Invoices Management", size=20,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton("Create Invoice", icon=ft.Icons.ADD, on_click=self._show_add_invoice_dialog,
                                      bgcolor=PRIMARY, color="white"),
                ]),
                ft.Container(height=15),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        expand=True,
                        spacing=10,
                        controls=self._build_invoice_cards(invoices) if invoices else [
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.RECEIPT_OUTLINED,
                                            size=64, color="#BDC3C7"),
                                    ft.Text("No invoices yet", size=14,
                                            color=TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                                alignment=ft.alignment.Alignment(0, 0)
                            )
                        ]
                    )
                )
            ], expand=True)
        )

    def _build_invoice_cards(self, invoices):
        cards = []
        status_colors = {"draft": INFO, "sent": WARNING,
                         "paid": SUCCESS, "overdue": ERROR, "cancelled": TEXT_SECONDARY}
        for inv in invoices:
            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Row([
                            ft.Container(
                                width=50, height=50,
                                bgcolor="#E3F2FD",
                                border_radius=8,
                                content=ft.Icon(
                                    ft.Icons.RECEIPT, color=PRIMARY, size=25),
                                alignment=ft.alignment.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text(
                                    f"{inv.invoice_number} - {inv.customer_name}", size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"Date: {inv.invoice_date} | Due: {inv.due_date or 'N/A'}", size=11, color=TEXT_SECONDARY),
                                ft.Text(
                                    f"Total: ₹{inv.total_amount:,.2f}", size=12, weight=ft.FontWeight.BOLD, color=PRIMARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    inv.status.upper(), size=10, color="white"),
                                bgcolor=status_colors.get(inv.status, INFO),
                                padding=ft.padding.symmetric(
                                    horizontal=10, vertical=4),
                                border_radius=10,
                            ),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_invoices(self):
        db = get_db_session()
        try:
            return db.query(Invoice).order_by(Invoice.created_at.desc()).limit(50).all()
        except:
            return []
        finally:
            db.close()

    # ==================== DIALOGS ====================
    def _show_add_dialog(self, e):
        if self.current_tab == "leads":
            self._show_add_lead_dialog()
        elif self.current_tab == "contacts":
            self._show_add_contact_dialog()
        elif self.current_tab == "warehouses":
            self._show_add_warehouse_dialog()
        elif self.current_tab == "assets":
            self._show_add_asset_dialog()
        elif self.current_tab == "contracts":
            self._show_add_contract_dialog()
        elif self.current_tab == "invoices":
            self._show_add_invoice_dialog()

    def _show_add_lead_dialog(self):
        name_f = ft.TextField(label="Name *", width=350)
        company_f = ft.TextField(label="Company", width=350)
        email_f = ft.TextField(label="Email", width=350)
        phone_f = ft.TextField(label="Phone", width=350)
        value_f = ft.TextField(label="Value (₹)", width=200, value="0")

        source_dd = ft.Dropdown(
            label="Source",
            width=200,
            options=[
                ft.dropdown.Option("website", "Website"),
                ft.dropdown.Option("referral", "Referral"),
                ft.dropdown.Option("social_media", "Social Media"),
                ft.dropdown.Option("cold_call", "Cold Call"),
                ft.dropdown.Option("other", "Other"),
            ],
            value="website"
        )

        def save(e):
            if not name_f.value:
                self._show_error("Name required")
                return
            db = get_db_session()
            try:
                lead = Lead(
                    name=name_f.value,
                    company=company_f.value,
                    email=email_f.value,
                    phone=phone_f.value,
                    value=float(
                        value_f.value) if value_f.value.isdigit() else 0,
                    source=source_dd.value,
                )
                db.add(lead)
                db.commit()
                self._show_success("Lead added!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Lead"),
            content=ft.Column([name_f, company_f, email_f,
                              phone_f, value_f, source_dd], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _edit_lead(self, lead):
        name_f = ft.TextField(label="Name *", width=350, value=lead.name)
        company_f = ft.TextField(
            label="Company", width=350, value=lead.company)
        email_f = ft.TextField(label="Email", width=350, value=lead.email)
        phone_f = ft.TextField(label="Phone", width=350, value=lead.phone)
        value_f = ft.TextField(
            label="Value (₹)", width=200, value=str(lead.value))

        def save(e):
            if not name_f.value:
                self._show_error("Name required")
                return
            db = get_db_session()
            try:
                db.query(Lead).filter(Lead.id == lead.id).update({
                    Lead.name: name_f.value,
                    Lead.company: company_f.value,
                    Lead.email: email_f.value,
                    Lead.phone: phone_f.value,
                    Lead.value: float(value_f.value) if value_f.value.isdigit() else 0,
                })
                db.commit()
                self._show_success("Lead updated!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Lead"),
            content=ft.Column([name_f, company_f, email_f,
                              phone_f, value_f], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _delete_lead(self, lead_id):
        def confirm(e):
            db = get_db_session()
            try:
                db.query(Lead).filter(Lead.id == lead_id).delete()
                db.commit()
                self._show_success("Lead deleted!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Lead?"),
            content=ft.Text("This action cannot be undone."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm,
                                  bgcolor=ERROR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_add_contact_dialog(self):
        first_f = ft.TextField(label="First Name *", width=350)
        last_f = ft.TextField(label="Last Name", width=350)
        company_f = ft.TextField(label="Company", width=350)
        email_f = ft.TextField(label="Email", width=350)
        phone_f = ft.TextField(label="Phone", width=350)

        def save(e):
            if not first_f.value:
                self._show_error("First name required")
                return
            db = get_db_session()
            try:
                contact = Contact(
                    first_name=first_f.value,
                    last_name=last_f.value,
                    company=company_f.value,
                    email=email_f.value,
                    phone=phone_f.value,
                )
                db.add(contact)
                db.commit()
                self._show_success("Contact added!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Contact"),
            content=ft.Column([first_f, last_f, company_f,
                              email_f, phone_f], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _edit_contact(self, contact):
        first_f = ft.TextField(label="First Name *",
                               width=350, value=contact.first_name)
        last_f = ft.TextField(label="Last Name", width=350,
                              value=contact.last_name)
        company_f = ft.TextField(
            label="Company", width=350, value=contact.company)
        email_f = ft.TextField(label="Email", width=350, value=contact.email)
        phone_f = ft.TextField(label="Phone", width=350, value=contact.phone)

        def save(e):
            if not first_f.value:
                self._show_error("First name required")
                return
            db = get_db_session()
            try:
                db.query(Contact).filter(Contact.id == contact.id).update({
                    Contact.first_name: first_f.value,
                    Contact.last_name: last_f.value,
                    Contact.company: company_f.value,
                    Contact.email: email_f.value,
                    Contact.phone: phone_f.value,
                })
                db.commit()
                self._show_success("Contact updated!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Contact"),
            content=ft.Column([first_f, last_f, company_f,
                              email_f, phone_f], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _delete_contact(self, contact_id):
        def confirm(e):
            db = get_db_session()
            try:
                db.query(Contact).filter(Contact.id == contact_id).delete()
                db.commit()
                self._show_success("Contact deleted!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Contact?"),
            content=ft.Text("This action cannot be undone."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm,
                                  bgcolor=ERROR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_add_event_dialog(self, e):
        title_f = ft.TextField(label="Event Title *", width=400)
        desc_f = ft.TextField(label="Description", width=400, multiline=True)
        location_f = ft.TextField(label="Location", width=400)

        def save(e):
            if not title_f.value:
                self._show_error("Title required")
                return
            self._show_success("Event added!")
            self._close_dialog()
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Event"),
            content=ft.Column([title_f, desc_f, location_f], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_add_warehouse_dialog(self, e=None):
        name_f = ft.TextField(label="Warehouse Name *", width=350)
        code_f = ft.TextField(label="Code *", width=150)
        city_f = ft.TextField(label="City", width=200)
        state_f = ft.TextField(label="State", width=200)
        capacity_f = ft.TextField(label="Capacity", width=150, value="0")

        def save(e):
            if not name_f.value or not code_f.value:
                self._show_error("Name and Code required")
                return
            db = get_db_session()
            try:
                wh = Warehouse(
                    name=name_f.value,
                    code=code_f.value,
                    city=city_f.value,
                    state=state_f.value,
                    capacity=int(
                        capacity_f.value) if capacity_f.value.isdigit() else 0,
                )
                db.add(wh)
                db.commit()
                self._show_success("Warehouse added!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Warehouse"),
            content=ft.Column(
                [name_f, code_f, city_f, state_f, capacity_f], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_add_asset_dialog(self, e=None):
        name_f = ft.TextField(label="Asset Name *", width=350)
        code_f = ft.TextField(label="Asset Code *", width=200)
        category_dd = ft.Dropdown(
            label="Category",
            width=200,
            options=[
                ft.dropdown.Option("electronics", "Electronics"),
                ft.dropdown.Option("furniture", "Furniture"),
                ft.dropdown.Option("vehicle", "Vehicle"),
                ft.dropdown.Option("machinery", "Machinery"),
                ft.dropdown.Option("software", "Software"),
                ft.dropdown.Option("other", "Other"),
            ],
            value="other"
        )
        value_f = ft.TextField(label="Value (₹)", width=200, value="0")

        def save(e):
            if not name_f.value or not code_f.value:
                self._show_error("Name and Code required")
                return
            db = get_db_session()
            try:
                asset = Asset(
                    name=name_f.value,
                    asset_code=code_f.value,
                    category=category_dd.value,
                    current_value=float(value_f.value) if value_f.value.replace(
                        '.', '', 1).isdigit() else 0,
                )
                db.add(asset)
                db.commit()
                self._show_success("Asset added!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Asset"),
            content=ft.Column(
                [name_f, code_f, category_dd, value_f], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_add_contract_dialog(self, e=None):
        title_f = ft.TextField(label="Contract Title *", width=400)
        number_f = ft.TextField(label="Contract Number *", width=200)
        type_dd = ft.Dropdown(
            label="Type",
            width=200,
            options=[
                ft.dropdown.Option("vendor", "Vendor"),
                ft.dropdown.Option("client", "Client"),
                ft.dropdown.Option("employee", "Employee"),
                ft.dropdown.Option("lease", "Lease"),
            ],
            value="vendor"
        )
        value_f = ft.TextField(label="Value (₹)", width=200, value="0")

        def save(e):
            if not title_f.value or not number_f.value:
                self._show_error("Title and Number required")
                return
            db = get_db_session()
            try:
                contract = Contract(
                    title=title_f.value,
                    contract_number=number_f.value,
                    contract_type=type_dd.value,
                    value=float(value_f.value) if value_f.value.replace(
                        '.', '', 1).isdigit() else 0,
                    start_date=date.today(),
                    end_date=date.today().replace(year=date.today().year + 1),
                )
                db.add(contract)
                db.commit()
                self._show_success("Contract added!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Contract"),
            content=ft.Column(
                [title_f, number_f, type_dd, value_f], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _show_add_invoice_dialog(self, e=None):
        customer_f = ft.TextField(label="Customer Name *", width=350)
        number_f = ft.TextField(label="Invoice Number *", width=200)
        amount_f = ft.TextField(label="Amount (₹) *", width=200, value="0")

        def save(e):
            if not customer_f.value or not number_f.value:
                self._show_error("Customer and Number required")
                return
            db = get_db_session()
            try:
                invoice = Invoice(
                    invoice_number=number_f.value,
                    customer_name=customer_f.value,
                    total_amount=float(amount_f.value) if amount_f.value.replace(
                        '.', '', 1).isdigit() else 0,
                    invoice_date=date.today(),
                    status="draft",
                )
                db.add(invoice)
                db.commit()
                self._show_success("Invoice created!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(str(ex))
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("Create New Invoice"),
            content=ft.Column([number_f, customer_f, amount_f], spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Create", on_click=save,
                                  bgcolor=SUCCESS, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    # ==================== HELPERS ====================
    def _on_search(self, e):
        self.search_query = e.control.value
        self._page.update()

    def _refresh(self):
        self.content = self._build_content()
        self._page.update()

    def _close_dialog(self):
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=ERROR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_crm(page, user):
    """Main entry point"""
    page.clean()
    page.add(CRMScreen(page, user))
