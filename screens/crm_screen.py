"""
RadheFoundation HRA - CRM Screen (Unified Tabbed Interface)
Comprehensive CRM with Leads, Contacts, Calendar, Events, Vendors, Warehouses, Assets, Contracts, Invoices
"""

from sqlalchemy.exc import IntegrityError
import re
import calendar as cal
from components.forms import DatePickerField, TimePickerField
import flet as ft
import os
import logging
from datetime import datetime, date, timedelta
from database.session_manager import get_session
# Lazy model imports - prevents circular import issues during screen navigation
Lead = Contact = CalendarEvent = Warehouse = Asset = Contract = Invoice = InvoiceItem = Supplier = Employee = User = None
crm_repo = None


def lazy_import_models():
    """Lazy import models only when first data op called"""
    global Lead, Contact, CalendarEvent, Warehouse, Asset, Contract, Invoice, InvoiceItem, Supplier, Employee, User, crm_repo
    if Lead is None:
        from database import Lead, Contact, CalendarEvent, Warehouse, Asset, Contract, Invoice, InvoiceItem, Supplier, Employee, User
        from database.crm_repository import crm_repo


logger = logging.getLogger(__name__)


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

# Calendar event status colors (matching meetings_screen)
EVENT_STATUS_COLORS = {
    "scheduled": "#2196F3",  # INFO blue
    "in_progress": "#FF9800",  # WARNING
    "completed": "#4CAF50",  # SUCCESS
    "cancelled": "#F44336",  # ERROR
    "default": PRIMARY
}


class CRMScreen(ft.Container):
    """Unified CRM Screen with Tabbed Interface"""

    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND

        lazy_import_models()  # Load CRM repo and models

        # Tab state
        self.current_tab = "leads"
        self.search_query = ""
        self.selected_item = None

        # Calendar state
        self.current_calendar_month = date.today().replace(day=1)

        self.content = self._build_content()

    def _build_content(self):
        return ft.Column([
            self._build_header(),
            self._build_tabs(),
            self._build_tab_content(),
        ], expand=True, spacing=0)

    def _build_header(self):
        """FIXED: Add Test Data + Refresh buttons."""
        return ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Icon(ft.Icons.PEOPLE, color="white", size=28),
                ft.Text("CRM Dashboard", size=22, color="white",
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "🔄 Refresh", icon=ft.Icons.REFRESH, on_click=lambda _: self._refresh(),
                    style=ft.ButtonStyle(bgcolor=INFO, color="white")
                ),
                ft.ElevatedButton(
                    "🧪 Test Data", icon=ft.Icons.SCIENCE, on_click=self._generate_test_data,
                    style=ft.ButtonStyle(bgcolor=WARNING, color="white")
                ),
                ft.ElevatedButton(
                    "➕ Add New", icon=ft.Icons.ADD, on_click=self._show_add_dialog,
                    style=ft.ButtonStyle(bgcolor=SUCCESS, color="white")
                ),
            ], alignment=ft.MainAxisAlignment.END)
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
        # Show loading during tab switch
        self._show_loading("Switching tab...")
        self.content = self._build_content()
        self._page.update()
        self._refresh()

    def _refresh(self):
        """Enhanced refresh with loading states + error handling."""
        def refresh_click(e):
            # Show loading immediately
            self._show_loading("Refreshing data...")

            try:
                # Clear caches
                if hasattr(crm_repo, 'get_all_leads_cached'):
                    crm_repo.get_all_leads_cached.cache_clear()

                # Rebuild UI with fresh data
                self.content = self._build_content()
                self._page.update()

                self._show_success("✅ Data refreshed successfully!")

            except Exception as err:
                logger.error(f"CRM refresh error: {err}")
                self._show_error(f"❌ Refresh failed: {str(err)[:100]}")
            finally:
                self._hide_loading()

        refresh_click(None)  # Trigger immediately

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

    def _get_leads_dropdown(self):
        """Get leads as dropdown options."""
        try:
            with get_session() as db:
                leads = db.query(Lead).order_by(Lead.name).limit(50).all()
                return ft.Dropdown(
                    label="Related Lead (optional)",
                    options=[ft.dropdown.Option(
                        str(lead.id), lead.name) for lead in leads] + [ft.dropdown.Option("", "No Lead")],
                    value="",
                    width=350
                )
        except Exception as ex:
            print(f"Error loading leads dropdown: {ex}")
            return ft.Dropdown(label="Related Lead (optional)", value="", width=350)

    def _get_contacts_dropdown(self):
        """Get contacts as dropdown options."""
        try:
            with get_session() as db:
                contacts = db.query(Contact).order_by(
                    Contact.first_name, Contact.last_name).limit(50).all()
                return ft.Dropdown(
                    label="Related Contact (optional)",
                    options=[ft.dropdown.Option(str(contact.id), f"{contact.first_name} {contact.last_name or ''}".strip(
                    ) or "Unnamed") for contact in contacts] + [ft.dropdown.Option("", "No Contact")],
                    value="",
                    width=350
                )
        except Exception as ex:
            print(f"Error loading contacts dropdown: {ex}")
            return ft.Dropdown(label="Related Contact (optional)", value="", width=350)

    def _get_contracts_dropdown(self):
        """Get contracts as dropdown options."""
        try:
            with get_session() as db:
                contracts = db.query(Contract).order_by(
                    Contract.title).limit(30).all()
                return ft.Dropdown(
                    label="Related Contract (optional)",
                    options=[ft.dropdown.Option(str(contract.id), f"{contract.title[:30]}...") for contract in contracts] + [
                        ft.dropdown.Option("", "No Contract")],
                    value="",
                    width=350
                )
        except Exception as ex:
            print(f"Error loading contracts dropdown: {ex}")
            return ft.Dropdown(label="Related Contract (optional)", value="", width=350)

    def _get_invoices_dropdown(self):
        """Get invoices as dropdown options."""
        try:
            with get_session() as db:
                invoices = db.query(Invoice).order_by(
                    Invoice.invoice_number).limit(30).all()
                return ft.Dropdown(
                    label="Related Invoice (optional)",
                    options=[ft.dropdown.Option(str(invoice.id), invoice.invoice_number)
                             for invoice in invoices] + [ft.dropdown.Option("", "No Invoice")],
                    value="",
                    width=350
                )
        except Exception as ex:
            print(f"Error loading invoices dropdown: {ex}")
            return ft.Dropdown(label="Related Invoice (optional)", value="", width=350)

    def _get_all_leads(self):
        """Safe leads load with fallback."""
        if crm_repo is None:
            logger.warning("CRM repo not loaded")
            self._show_error("CRM repository not available. Refresh page.")
            return []
        try:
            leads = crm_repo.get_all_leads()
            if not leads:
                self._show_warning("📭 No leads yet. Try '🧪 Test Data'!")
            logger.info(f"Loaded {len(leads)} leads")
            return leads
        except Exception as e:
            logger.error(f"Leads load error: {e}")
            self._show_error(f"Failed to load leads: {str(e)[:80]}")
            return []

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
        """Safe contacts load."""
        if crm_repo is None:
            logger.warning("CRM repo not loaded")
            self._show_error("CRM repository not available. Refresh page.")
            return []
        try:
            contacts = crm_repo.get_all_contacts()
            if not contacts:
                self._show_warning("📇 No contacts yet. Try Test Data!")
            return contacts
        except Exception as e:
            logger.error(f"Contacts load error: {e}")
            self._show_error(f"Contacts load failed: {str(e)[:80]}")
            return []

    # ==================== CALENDAR ====================

    def _build_calendar_view(self):
        events = self._get_all_events()
        month_start = self.current_calendar_month
        month_end = (month_start.replace(day=28) + timedelta(days=4)
                     ).replace(day=1) - timedelta(days=1)
        month_events = crm_repo.get_events_by_date_range(
            month_start, month_end)
        event_count_text = ft.Text(
            f"Month: {len(month_events)} | Total: {len(events)}", size=14, color=TEXT_SECONDARY)

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Calendar & Events", size=20,
                            weight=ft.FontWeight.BOLD),
                    event_count_text,
                    ft.Container(expand=True),
                    # Add Event moved to header
                ]),
                ft.Container(height=10),
                self._build_calendar_header(),
                ft.Container(height=15),
                # Modern calendar grid - scrollable
                ft.Container(
                    height=400,
                    content=ft.ListView(
                        controls=[self._build_month_calendar(
                            month_events, self.current_calendar_month)],
                        spacing=0
                    ),
                    border_radius=10,
                    bgcolor=SURFACE
                ),
                ft.Container(height=20),
                ft.Text("Recent Events", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    height=300,
                    content=ft.ListView(
                        controls=self._build_event_cards(events[:15]),
                        spacing=8
                    )
                ),
            ], expand=True, scroll=ft.ScrollMode.AUTO)
        )

    def _build_calendar_header(self):
        """Modern header matching meetings_screen"""
        month_year = self.current_calendar_month.strftime("%B %Y")

        return ft.Row([
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                icon_color=PRIMARY,
                tooltip="Previous Month",
                on_click=self._prev_month
            ),
            ft.Container(
                content=ft.Text(
                    month_year,
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY
                ),
                padding=ft.padding.symmetric(horizontal=20)
            ),
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                icon_color=PRIMARY,
                tooltip="Next Month",
                on_click=self._next_month
            ),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "Today",
                icon=ft.Icons.TODAY_ROUNDED,
                style=ft.ButtonStyle(bgcolor=PRIMARY, color="white"),
                on_click=self._go_today,
                width=90,
                height=40
            ),
            ft.Container(width=10),
            ft.ElevatedButton(
                "Add Event",
                icon=ft.Icons.ADD,
                style=ft.ButtonStyle(bgcolor=PRIMARY, color="white"),
                on_click=self._show_add_event_dialog
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _prev_month(self, e):
        # Go to previous month
        if self.current_calendar_month.month == 1:
            self.current_calendar_month = self.current_calendar_month.replace(
                year=self.current_calendar_month.year-1, month=12, day=1)
        else:
            self.current_calendar_month = self.current_calendar_month.replace(
                month=self.current_calendar_month.month-1, day=1)
        self._refresh_calendar()

    def _next_month(self, e):
        # Go to next month
        if self.current_calendar_month.month == 12:
            self.current_calendar_month = self.current_calendar_month.replace(
                year=self.current_calendar_month.year+1, month=1, day=1)
        else:
            self.current_calendar_month = self.current_calendar_month.replace(
                month=self.current_calendar_month.month+1, day=1)
        self._refresh_calendar()

    def _go_today(self, e):
        self.current_calendar_month = date.today().replace(day=1)
        self._refresh_calendar()

    def _refresh_calendar(self):
        """Refresh just the calendar view"""
        self.content = self._build_content()
        self._page.update()

    def _build_month_calendar(self, events, target_month):
        """Modern month calendar matching meetings_screen style.
        Uses cal.monthrange(), Mon-Sun headers, up to 6 rows."""
        year = target_month.year
        month = target_month.month

        first_day = target_month.replace(day=1)
        _, days_in_month = cal.monthrange(year, month)

        today = date.today()

        # Day headers Mon-Sun (meeting_screen style)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        header_row = ft.Row([
            ft.Container(
                content=ft.Text(
                    d,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color="#999" if i >= 5 else PRIMARY  # Weekend gray
                ),
                width=100,
                height=35,
                alignment=ft.alignment.Alignment.CENTER
            ) for i, d in enumerate(days)
        ], spacing=0)

        # Build calendar rows
        calendar_rows = []
        # Padding for days before month start (Mon=0)
        start_padding = first_day.weekday()
        current_row = [ft.Container(width=100)] * start_padding

        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            day_events = [e for e in events if e.start_time.date()
                          == current_date]
            is_weekend = current_date.weekday() >= 5
            is_today = current_date == today

            day_cell = self._build_calendar_day_cell(
                current_date, day_events, is_today, is_weekend
            )
            current_row.append(day_cell)

            # Complete row of 7, add to grid
            if len(current_row) == 7:
                calendar_rows.append(ft.Row(current_row, spacing=2))
                current_row = []

        # Pad final row
        if current_row:
            current_row += [ft.Container(width=100)] * (7 - len(current_row))
            calendar_rows.append(ft.Row(current_row, spacing=2))

        # Max 6 rows
        calendar_container = ft.Container(
            content=ft.Column(
                [header_row] + calendar_rows[:6],
                spacing=2
            ),
            bgcolor=SURFACE,
            padding=15,
            border_radius=10,
            expand=True
        )
        return calendar_container

    def _build_calendar_day_cell(self, current_date, day_events, is_today, is_weekend):
        """Modern day cell: prominent date circle + event chips (+more)."""
        display_events = day_events[:3]
        more_count = len(day_events) - 3

        # Event chips
        event_chips = []
        for event in display_events:
            # Use status or fallback
            status = getattr(event, 'status', 'default')
            chip_color = EVENT_STATUS_COLORS.get(
                str(status), EVENT_STATUS_COLORS["default"])
            chip_text = event.title[:12]
            event_chips.append(
                ft.Container(
                    content=ft.Text(
                        chip_text,
                        size=9,
                        color="WHITE",
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    bgcolor=chip_color,
                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                    border_radius=4,
                    margin=ft.margin.only(bottom=1)
                )
            )

        if more_count > 0:
            event_chips.append(
                ft.Text(f"+{more_count} more", size=9, color=PRIMARY)
            )

        # Date circle (prominent, always top)
        date_color = "WHITE" if is_today else PRIMARY
        date_circle = ft.Container(
            content=ft.Text(
                str(current_date.day),
                size=16 if is_today else 14,
                weight=ft.FontWeight.BOLD,
                color=date_color,
                text_align=ft.TextAlign.CENTER
            ),
            width=32,
            height=32,
            bgcolor=PRIMARY if is_today else "transparent",
            border_radius=16,
            alignment=ft.alignment.Alignment.CENTER
        )

        cell_content = ft.Column(
            [date_circle] + event_chips,
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        # Cell styling (meetings-like)
        cell_bg = "#E3F2FD" if is_today else (
            SURFACE if not is_weekend else "#F8F9FA")
        cell = ft.Container(
            width=100,
            height=100,
            bgcolor=cell_bg,
            border=ft.border.all(1, "#EDEDED"),
            content=cell_content,
            border_radius=12,
            padding=5,
            ink=True,
            tooltip=f"{current_date.strftime('%B %d')} ({len(day_events)} events)",
            on_click=lambda e, d=current_date: self._show_day_events(d)
        )
        return cell

    def _get_all_events(self):
        """Safe events load (no limit)."""
        if crm_repo is None:
            logger.warning("CRM repo not loaded")
            self._show_error("CRM repository not available. Refresh page.")
            return []
        try:
            events = crm_repo.get_all_events(limit=None)
            if not events:
                self._show_warning("📅 No events. Generate test data!")
            logger.info(f"Loaded {len(events)} events")
            return events
        except Exception as e:
            logger.error(f"Events load error: {e}")
            self._show_error(f"Events load failed: {str(e)[:80]}")
            return []

    def _show_day_events(self, date_obj):
        """Show day events with FRESH data fetch."""
        from datetime import date
        dlg_date = date_obj.date() if hasattr(date_obj, 'date') else date_obj

        # Fetch FRESH events for this day
        day_events = crm_repo.get_events_by_date_range(dlg_date, dlg_date)

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_TODAY, color=PRIMARY),
                ft.Text(f"Events on {dlg_date.strftime('%A, %Y-%m-%d')}"),
                ft.Text(f" ({len(day_events)} events)",
                        color=TEXT_SECONDARY, size=14)
            ]),
            content=ft.Column([
                ft.Container(height=10),
                ft.ListView(
                    controls=self._build_event_cards(day_events),
                    height=350,
                    spacing=8
                )
            ], scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.ElevatedButton("🔄 Refresh", on_click=lambda _: self._show_day_events(date_obj),
                                  bgcolor=INFO, color="white"),
                ft.TextButton("Close", on_click=lambda _: self._close_dialog())
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _build_event_cards(self, events):
        cards = []
        for event in events:
            start_str = event.start_time.strftime(
                "%H:%M") if event.start_time else "N/A"
            end_str = event.end_time.strftime(
                "%H:%M") if event.end_time else "N/A"

            # Linked info
            linked_info = []
            if event.lead:
                linked_info.append(f"Lead: {event.lead.name}")
            if event.contact:
                linked_info.append(
                    f"Contact: {event.contact.first_name} {event.contact.last_name or ''}".strip())
            if event.agenda:
                linked_info.append("📋 Agenda")
            if event.related_contract:
                linked_info.append(
                    f"Contract: {event.related_contract.title[:20]}...")
            if event.related_invoice:
                linked_info.append(
                    f"Invoice: {event.related_invoice.invoice_number}")

            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Column([
                            ft.Text(event.title, size=15,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(f"{start_str} - {end_str}",
                                    size=12, color=TEXT_SECONDARY),
                            ft.Text(event.description or event.location or "",
                                    size=11, color=TEXT_SECONDARY, max_lines=1),
                            ft.Column([
                                ft.Text(item, size=10, color=PRIMARY,
                                        weight=ft.FontWeight.W_500)
                                for item in linked_info[:2]  # Show top 2
                            ], spacing=1) if linked_info else ft.Container(),
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, scale=0.7,
                                              on_click=lambda e, ev=event: self._edit_event(ev)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR, scale=0.7,
                                              on_click=lambda e, ev=event: self._delete_event(ev.id)),
                            ], spacing=0),
                        ], spacing=4)
                    ),
                    elevation=1
                )
            )
        return cards

    def _edit_event(self, event):
        title_f = ft.TextField(label="Title *", width=350,
                               value=event.title or "")
        desc_f = ft.TextField(label="Description", width=350,
                              multiline=True, max_lines=3, value=event.description or "")
        location_f = ft.TextField(
            label="Location", width=350, value=event.location or "")

        # New fields with current values
        lead_dd = self._get_leads_dropdown()
        if event.lead_id:
            lead_dd.value = str(event.lead_id)
        contact_dd = self._get_contacts_dropdown()
        if event.contact_id:
            contact_dd.value = str(event.contact_id)
        agenda_f = ft.TextField(label="Agenda (optional)", width=350,
                                multiline=True, max_lines=2, value=event.agenda or "")
        contract_dd = self._get_contracts_dropdown()
        if event.related_contract_id:
            contract_dd.value = str(event.related_contract_id)
        invoice_dd = self._get_invoices_dropdown()
        if event.related_invoice_id:
            invoice_dd.value = str(event.related_invoice_id)

        start_date_picker = DatePickerField(label="Start Date *", width=250)
        start_date_picker._page = self._page
        if event.start_time:
            start_date_picker.value = event.start_time.strftime('%Y-%m-%d')
        start_time_picker = TimePickerField(label="Start Time *", width=200)
        start_time_picker._page = self._page
        if event.start_time:
            start_time_picker.value = event.start_time.strftime('%H:%M')
        end_date_picker = DatePickerField(label="End Date *", width=250)
        end_date_picker._page = self._page
        if event.end_time:
            end_date_picker.value = event.end_time.strftime('%Y-%m-%d')
        end_time_picker = TimePickerField(label="End Time *", width=200)
        end_time_picker._page = self._page
        if event.end_time:
            end_time_picker.value = event.end_time.strftime('%H:%M')

        def save(e):
            if not title_f.value or not start_date_picker.value or not start_time_picker.value:
                self._show_error("Title, Start Date and Time required")
                return
            try:
                from datetime import datetime
                start_dt = datetime.strptime(
                    start_date_picker.value, '%Y-%m-%d').date()
                start_time = datetime.strptime(
                    start_time_picker.value, '%H:%M').time()
                end_dt = datetime.strptime(
                    end_date_picker.value, '%Y-%m-%d').date()
                end_time = datetime.strptime(
                    end_time_picker.value, '%H:%M').time()

                start_datetime = datetime.combine(start_dt, start_time)
                end_datetime = datetime.combine(end_dt, end_time)

                update_data = {
                    CalendarEvent.title: title_f.value.strip(),
                    CalendarEvent.description: desc_f.value.strip() if desc_f.value.strip() else None,
                    CalendarEvent.location: location_f.value.strip() if location_f.value.strip() else None,
                    CalendarEvent.start_time: start_datetime,
                    CalendarEvent.end_time: end_datetime,
                    CalendarEvent.agenda: agenda_f.value.strip() if agenda_f.value.strip() else None,
                }

                if lead_dd.value and lead_dd.value != "":
                    update_data[CalendarEvent.lead_id] = int(lead_dd.value)
                else:
                    update_data[CalendarEvent.lead_id] = None

                if contact_dd.value and contact_dd.value != "":
                    update_data[CalendarEvent.contact_id] = int(
                        contact_dd.value)
                else:
                    update_data[CalendarEvent.contact_id] = None

                if contract_dd.value and contract_dd.value != "":
                    update_data[CalendarEvent.related_contract_id] = int(
                        contract_dd.value)
                else:
                    update_data[CalendarEvent.related_contract_id] = None

                if invoice_dd.value and invoice_dd.value != "":
                    update_data[CalendarEvent.related_invoice_id] = int(
                        invoice_dd.value)
                else:
                    update_data[CalendarEvent.related_invoice_id] = None

                with get_session() as db:
                    db.query(CalendarEvent).filter(
                        CalendarEvent.id == event.id).update(update_data)
                    db.commit()

                # Clear cache + refresh
                if hasattr(crm_repo, 'refresh_events_cache'):
                    crm_repo.refresh_events_cache()

                self._show_success("✅ Event updated! Calendar refreshed.")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Update failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Event"),
            content=ft.Column([
                title_f, desc_f, location_f,
                lead_dd, contact_dd, agenda_f, contract_dd, invoice_dd,
                ft.Row([start_date_picker, start_time_picker], spacing=10),
                ft.Row([end_date_picker, end_time_picker], spacing=10)
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
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

    def _delete_event(self, event_id):
        def confirm(e):
            try:
                with get_session() as db:
                    db.query(CalendarEvent).filter(
                        CalendarEvent.id == event_id).delete()
                    db.commit()
                    self._show_success("Event deleted!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Delete failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Event?"),
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
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, scale=0.7,
                                              on_click=lambda e, v=vendor: self._edit_vendor(v)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR, scale=0.7,
                                              on_click=lambda e, v=vendor: self._delete_vendor(v.id)),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_vendors(self):
        """Safe vendors load."""
        if crm_repo is None:
            logger.warning("CRM repo not loaded")
            self._show_error("CRM repository not available. Refresh page.")
            return []
        try:
            vendors = crm_repo.get_all_vendors()
            if not vendors:
                self._show_warning("🏢 No vendors. Try Test Data!")
            return vendors
        except Exception as e:
            logger.error(f"Vendors load error: {e}")
            self._show_error(f"Vendors load failed: {str(e)[:80]}")
            return []

    def _edit_vendor(self, vendor):
        name_f = ft.TextField(label="Name *", width=350,
                              value=vendor.name or "")
        contact_f = ft.TextField(
            label="Contact Person", width=350, value=vendor.contact_person or "")
        email_f = ft.TextField(label="Email", width=350,
                               value=vendor.email or "")
        phone_f = ft.TextField(label="Phone", width=350,
                               value=vendor.phone or "")
        gst_f = ft.TextField(label="GST Number", width=350,
                             value=vendor.gst_number or "")
        active_cb = ft.Checkbox(label="Active", value=vendor.is_active)

        def save(e):
            try:
                with get_session() as db:
                    db.query(Supplier).filter(Supplier.id == vendor.id).update({
                        Supplier.name: name_f.value.strip(),
                        Supplier.contact_person: contact_f.value.strip() if contact_f.value else None,
                        Supplier.email: email_f.value.strip() if email_f.value else None,
                        Supplier.phone: phone_f.value.strip() if phone_f.value else None,
                        Supplier.gst_number: gst_f.value.strip() if gst_f.value else None,
                        Supplier.is_active: active_cb.value,
                    })
                    db.commit()
                    self._show_success("Vendor updated!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Update failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Vendor"),
            content=ft.Column([name_f, contact_f, email_f,
                              phone_f, gst_f, active_cb], spacing=12),
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

    def _delete_vendor(self, vendor_id):
        def confirm(e):
            try:
                with get_session() as db:
                    db.query(Supplier).filter(Supplier.id == vendor_id).update(
                        {Supplier.is_active: False})
                    db.commit()
                    self._show_success("Vendor deactivated!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Delete failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Deactivate Vendor?"),
            content=ft.Text("This will deactivate the vendor (soft delete)."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Deactivate", on_click=confirm,
                                  bgcolor=ERROR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

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
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, scale=0.7,
                                              on_click=lambda e, w=wh: self._edit_warehouse(w)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR, scale=0.7,
                                              on_click=lambda e, w=wh: self._delete_warehouse(w.id)),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_warehouses(self):
        """Safe warehouses load."""
        if crm_repo is None:
            logger.warning("CRM repo not loaded")
            self._show_error("CRM repository not available. Refresh page.")
            return []
        try:
            warehouses = crm_repo.get_all_warehouses()
            if not warehouses:
                self._show_warning("🏭 No warehouses. Test data needed!")
            return warehouses
        except Exception as e:
            logger.error(f"Warehouses load error: {e}")
            self._show_error(f"Warehouses load failed: {str(e)[:80]}")
            return []

    def _edit_warehouse(self, warehouse):
        name_f = ft.TextField(label="Name *", width=350,
                              value=warehouse.name or "")
        code_f = ft.TextField(label="Code *", width=200,
                              value=warehouse.code or "")
        city_f = ft.TextField(label="City", width=350,
                              value=warehouse.city or "")
        state_f = ft.TextField(label="State", width=350,
                               value=warehouse.state or "")
        capacity_f = ft.TextField(
            label="Capacity", width=200, value=str(warehouse.capacity or 0))
        active_cb = ft.Checkbox(label="Active", value=warehouse.is_active)

        def save(e):
            try:
                capacity_num = 0
                if capacity_f.value:
                    capacity_num = int(capacity_f.value)

                with get_session() as db:
                    db.query(Warehouse).filter(Warehouse.id == warehouse.id).update({
                        Warehouse.name: name_f.value.strip(),
                        Warehouse.code: code_f.value.strip().upper(),
                        Warehouse.city: city_f.value.strip() if city_f.value else None,
                        Warehouse.state: state_f.value.strip() if state_f.value else None,
                        Warehouse.capacity: capacity_num,
                        Warehouse.is_active: active_cb.value,
                    })
                    db.commit()
                    self._show_success("Warehouse updated!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Update failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Warehouse"),
            content=ft.Column([name_f, code_f, city_f, state_f,
                              capacity_f, active_cb], spacing=12),
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

    def _delete_warehouse(self, warehouse_id):
        def confirm(e):
            try:
                with get_session() as db:
                    db.query(Warehouse).filter(Warehouse.id == warehouse_id).update(
                        {Warehouse.is_active: False})
                    db.commit()
                    self._show_success("Warehouse deactivated!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Delete failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Deactivate Warehouse?"),
            content=ft.Text(
                "This will deactivate the warehouse (soft delete)."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Deactivate", on_click=confirm,
                                  bgcolor=ERROR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

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
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, scale=0.7,
                                              on_click=lambda e, a=asset: self._edit_asset(a)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR, scale=0.7,
                                              on_click=lambda e, a=asset: self._delete_asset(a.id)),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_assets(self):
        """Safe assets load."""
        if crm_repo is None:
            logger.warning("CRM repo not loaded")
            self._show_error("CRM repository not available. Refresh page.")
            return []
        try:
            assets = crm_repo.get_all_assets()
            if not assets:
                self._show_warning("💻 No assets. Generate test data!")
            return assets
        except Exception as e:
            logger.error(f"Assets load error: {e}")
            self._show_error(f"Assets load failed: {str(e)[:80]}")
            return []

    def _edit_asset(self, asset):
        name_f = ft.TextField(label="Name *", width=350,
                              value=asset.name or "")
        code_f = ft.TextField(label="Asset Code *",
                              width=200, value=asset.asset_code or "")
        category_dd = ft.Dropdown(
            label="Category", width=200, value=asset.category,
            options=[
                ft.dropdown.Option("electronics", "Electronics"),
                ft.dropdown.Option("furniture", "Furniture"),
                ft.dropdown.Option("vehicle", "Vehicle"),
                ft.dropdown.Option("machinery", "Machinery"),
                ft.dropdown.Option("software", "Software"),
                ft.dropdown.Option("other", "Other"),
            ]
        )
        value_f = ft.TextField(label="Current Value (₹)",
                               width=200, value=str(asset.current_value or 0))
        status_dd = ft.Dropdown(
            label="Status", width=200, value=asset.status,
            options=[
                ft.dropdown.Option("available"),
                ft.dropdown.Option("in_use"),
                ft.dropdown.Option("maintenance"),
                ft.dropdown.Option("retired"),
            ]
        )
        sn_f = ft.TextField(label="Serial Number", width=350,
                            value=asset.serial_number or "")

        def save(e):
            try:
                value_num = 0
                if value_f.value:
                    value_num = float(value_f.value.replace(',', ''))

                with get_session() as db:
                    db.query(Asset).filter(Asset.id == asset.id).update({
                        Asset.name: name_f.value.strip(),
                        Asset.asset_code: code_f.value.strip().upper(),
                        Asset.category: category_dd.value,
                        Asset.current_value: value_num,
                        Asset.status: status_dd.value,
                        Asset.serial_number: sn_f.value.strip() if sn_f.value else None,
                    })
                    db.commit()
                    self._show_success("Asset updated!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Update failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Asset"),
            content=ft.Column([name_f, code_f, category_dd,
                              value_f, status_dd, sn_f], spacing=12),
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

    def _delete_asset(self, asset_id):
        def confirm(e):
            try:
                with get_session() as db:
                    db.query(Asset).filter(Asset.id == asset_id).update(
                        {Asset.status: "retired"})
                    db.commit()
                    self._show_success("Asset marked as retired!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Delete failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Retire Asset?"),
            content=ft.Text(
                "This will mark the asset as retired (soft delete)."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Retire", on_click=confirm,
                                  bgcolor=ERROR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

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
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, scale=0.7,
                                              on_click=lambda e, c=contract: self._edit_contract(c)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR, scale=0.7,
                                              on_click=lambda e, c=contract: self._delete_contract(c.id)),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _get_all_contracts(self):
        """FIXED: CRM repo."""
        if crm_repo is None:
            logger.warning("CRM repo not loaded")
            self._show_error("CRM repository not available. Refresh page.")
            return []
        try:
            contracts = crm_repo.get_all_contracts()
            if not contracts:
                self._show_warning("No contracts found!")
            return contracts
        except Exception as e:
            logger.error(f"Contracts load error: {e}")
            self._show_error(f"Contracts failed: {str(e)[:80]}")
            return []

    def _edit_contract(self, contract):
        title_f = ft.TextField(label="Title *", width=400,
                               value=contract.title or "")
        number_f = ft.TextField(label="Contract Number *",
                                width=200, value=contract.contract_number or "")
        type_dd = ft.Dropdown(
            label="Type", width=200, value=contract.contract_type,
            options=[
                ft.dropdown.Option("vendor", "Vendor"),
                ft.dropdown.Option("client", "Client"),
                ft.dropdown.Option("employee", "Employee"),
                ft.dropdown.Option("lease", "Lease"),
            ]
        )
        value_f = ft.TextField(label="Value (₹)", width=200,
                               value=str(contract.value or 0))
        status_dd = ft.Dropdown(
            label="Status", width=200, value=contract.status,
            options=[
                ft.dropdown.Option("draft"),
                ft.dropdown.Option("active"),
                ft.dropdown.Option("expired"),
                ft.dropdown.Option("terminated"),
                ft.dropdown.Option("renewed"),
            ]
        )
        start_date_f = ft.TextField(label="Start Date (YYYY-MM-DD)", width=200,
                                    value=str(contract.start_date) if contract.start_date else "")
        end_date_f = ft.TextField(label="End Date (YYYY-MM-DD)", width=200,
                                  value=str(contract.end_date) if contract.end_date else "")

        def save(e):
            try:
                value_num = 0
                if value_f.value:
                    value_num = float(value_f.value.replace(',', ''))

                with get_session() as db:
                    db.query(Contract).filter(Contract.id == contract.id).update({
                        Contract.title: title_f.value.strip(),
                        Contract.contract_number: number_f.value.strip().upper(),
                        Contract.contract_type: type_dd.value,
                        Contract.value: value_num,
                        Contract.status: status_dd.value,
                        Contract.start_date: date.fromisoformat(start_date_f.value) if start_date_f.value else date.today(),
                        Contract.end_date: date.fromisoformat(end_date_f.value) if end_date_f.value else date.today(),
                    })
                    db.commit()
                    self._show_success("Contract updated!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Update failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Contract"),
            content=ft.Column([title_f, number_f, type_dd, value_f,
                               status_dd, start_date_f, end_date_f], spacing=12),
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

    def _delete_contract(self, contract_id):
        def confirm(e):
            try:
                with get_session() as db:
                    db.query(Contract).filter(Contract.id == contract_id).update(
                        {Contract.status: "terminated"})
                    db.commit()
                    self._show_success("Contract terminated!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Delete failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Terminate Contract?"),
            content=ft.Text(
                "This will mark the contract as terminated (soft delete)."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton("Terminate", on_click=confirm,
                                  bgcolor=ERROR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

    def _get_all_invoices(self):
        """Get all invoices."""
        try:
            with get_session() as db:
                stmt = db.query(Invoice).options().order_by(
                    Invoice.created_at.desc()).limit(50)
                return stmt.all()
        except Exception as ex:
            print(f"Invoice query error: {ex}")
            return []

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
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, scale=0.7,
                                              on_click=lambda e, i=inv: self._edit_invoice(i)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ERROR, scale=0.7,
                                              on_click=lambda e, i=inv: self._delete_invoice(i.id)),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.START)
                    ),
                    elevation=2
                )
            )
        return cards

    def _edit_invoice(self, invoice):
        customer_f = ft.TextField(
            label="Customer *", width=350, value=invoice.customer_name or "")
        number_f = ft.TextField(label="Invoice Number *",
                                width=200, value=invoice.invoice_number or "")
        amount_f = ft.TextField(label="Total Amount (₹)",
                                width=200, value=str(invoice.total_amount or 0))
        status_dd = ft.Dropdown(
            label="Status", width=200, value=invoice.status,
            options=[
                ft.dropdown.Option("draft"),
                ft.dropdown.Option("sent"),
                ft.dropdown.Option("paid"),
                ft.dropdown.Option("overdue"),
                ft.dropdown.Option("cancelled"),
            ]
        )

        def save(e):
            try:
                amount_num = 0
                if amount_f.value:
                    amount_num = float(amount_f.value.replace(',', ''))

                with get_session() as db:
                    db.query(Invoice).filter(Invoice.id == invoice.id).update({
                        Invoice.customer_name: customer_f.value.strip(),
                        Invoice.invoice_number: number_f.value.strip().upper(),
                        Invoice.total_amount: amount_num,
                        Invoice.status: status_dd.value,
                    })
                    db.commit()
                    self._show_success("Invoice updated!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Update failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Invoice"),
            content=ft.Column(
                [customer_f, number_f, amount_f, status_dd], spacing=12),
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

    def _delete_invoice(self, invoice_id):
        def confirm(e):
            try:
                with get_session() as db:
                    db.query(Invoice).filter(Invoice.id == invoice_id).update(
                        {Invoice.status: "cancelled"})
                    db.commit()
                    self._show_success("Invoice cancelled!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Delete failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Cancel Invoice?"),
            content=ft.Text("This will mark the invoice as cancelled."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton(
                    "Cancel Invoice", on_click=confirm, bgcolor=ERROR, color="white")
            ]
        )
        self._page.overlay.append(dlg)
        dlg.open = True
        self._page.update()

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
            try:
                value_num = 0
                if value_f.value:
                    try:
                        value_num = float(value_f.value.replace(',', ''))
                    except ValueError:
                        self._show_error("Invalid value format")
                        return

                with get_session() as db:
                    lead = Lead(
                        name=name_f.value.strip(),
                        company=company_f.value.strip() if company_f.value else None,
                        email=email_f.value.strip() if email_f.value else None,
                        phone=phone_f.value.strip() if phone_f.value else None,
                        value=value_num,
                        source=source_dd.value,
                    )
                    db.add(lead)
                    db.commit()
                    self._show_success("Lead added!")
                    self._close_dialog()
                    self._refresh()
            except IntegrityError:
                self._show_error("Lead with this name already exists")
            except Exception as ex:
                self._show_error(f"Save failed: {str(ex)[:100]}")

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
            try:
                value_num = 0
                if value_f.value:
                    try:
                        value_num = float(value_f.value.replace(',', ''))
                    except ValueError:
                        self._show_error("Invalid value format")
                        return

                with get_session() as db:
                    db.query(Lead).filter(Lead.id == lead.id).update({
                        Lead.name: name_f.value.strip(),
                        Lead.company: company_f.value.strip() if company_f.value else None,
                        Lead.email: email_f.value.strip() if email_f.value else None,
                        Lead.phone: phone_f.value.strip() if phone_f.value else None,
                        Lead.value: value_num,
                    })
                    db.commit()
                    self._show_success("Lead updated!")
                    self._close_dialog()
                    self._refresh()
            except IntegrityError:
                self._show_error("Lead update conflict")
            except Exception as ex:
                self._show_error(f"Update failed: {str(ex)[:100]}")

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
            try:
                with get_session() as db:
                    db.query(Lead).filter(Lead.id == lead_id).delete()
                    db.commit()
                    self._show_success("Lead deleted!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Delete failed: {str(ex)[:100]}")

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
            if email_f.value and not re.match(r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$', email_f.value):
                self._show_error("Invalid email format")
                return
            try:
                with get_session() as db:
                    contact = Contact(
                        first_name=first_f.value.strip(),
                        last_name=last_f.value.strip() if last_f.value else None,
                        company=company_f.value.strip() if company_f.value else None,
                        email=email_f.value.strip() if email_f.value else None,
                        phone=phone_f.value.strip() if phone_f.value else None,
                    )
                    db.add(contact)
                    db.commit()
                    self._show_success("Contact added!")
                    self._close_dialog()
                    self._refresh()
            except IntegrityError:
                self._show_error("Contact already exists")
            except Exception as ex:
                self._show_error(f"Save failed: {str(ex)[:100]}")

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
            if email_f.value and not re.match(r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$', email_f.value):
                self._show_error("Invalid email format")
                return
            try:
                with get_session() as db:
                    db.query(Contact).filter(Contact.id == contact.id).update({
                        Contact.first_name: first_f.value.strip(),
                        Contact.last_name: last_f.value.strip() if last_f.value else None,
                        Contact.company: company_f.value.strip() if company_f.value else None,
                        Contact.email: email_f.value.strip() if email_f.value else None,
                        Contact.phone: phone_f.value.strip() if phone_f.value else None,
                    })
                    db.commit()
                    self._show_success("Contact updated!")
                    self._close_dialog()
                    self._refresh()
            except IntegrityError:
                self._show_error("Contact update conflict")
            except Exception as ex:
                self._show_error(f"Update failed: {str(ex)[:100]}")

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
            try:
                with get_session() as db:
                    db.query(Contact).filter(Contact.id == contact_id).delete()
                    db.commit()
                    self._show_success("Contact deleted!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Delete failed: {str(ex)[:100]}")

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

    def _show_add_event_dialog(self, e=None):
        title_f = ft.TextField(label="Event Title *", width=350)
        desc_f = ft.TextField(label="Description",
                              width=350, multiline=True, max_lines=3)
        location_f = ft.TextField(label="Location", width=350)

        # New fields
        lead_dd = self._get_leads_dropdown()
        contact_dd = self._get_contacts_dropdown()
        agenda_f = ft.TextField(label="Agenda (optional)",
                                width=350, multiline=True, max_lines=2)
        contract_dd = self._get_contracts_dropdown()
        invoice_dd = self._get_invoices_dropdown()

        start_date_picker = DatePickerField(label="Start Date *", width=250)
        start_date_picker._page = self._page
        start_time_picker = TimePickerField(label="Start Time *", width=200)
        start_time_picker._page = self._page
        end_date_picker = DatePickerField(label="End Date *", width=250)
        end_date_picker._page = self._page
        end_time_picker = TimePickerField(label="End Time *", width=200)
        end_time_picker._page = self._page

        def save(e):
            if not title_f.value or not start_date_picker.value or not start_time_picker.value:
                self._show_error("Title, Start Date and Time required")
                return
            try:
                from datetime import datetime
                start_dt = datetime.strptime(
                    start_date_picker.value, '%Y-%m-%d').date()
                start_time = datetime.strptime(
                    start_time_picker.value, '%H:%M').time()
                end_dt = datetime.strptime(
                    end_date_picker.value, '%Y-%m-%d').date()
                end_time = datetime.strptime(
                    end_time_picker.value, '%H:%M').time()

                start_datetime = datetime.combine(start_dt, start_time)
                end_datetime = datetime.combine(end_dt, end_time)

                with get_session() as db:
                    event = CalendarEvent(
                        title=title_f.value.strip(),
                        description=desc_f.value.strip() if desc_f.value.strip() else None,
                        location=location_f.value.strip() if location_f.value else None,
                        lead_id=int(
                            lead_dd.value) if lead_dd.value and lead_dd.value != "" else None,
                        contact_id=int(
                            contact_dd.value) if contact_dd.value and contact_dd.value != "" else None,
                        agenda=agenda_f.value.strip() if agenda_f.value.strip() else None,
                        related_contract_id=int(
                            contract_dd.value) if contract_dd.value and contract_dd.value != "" else None,
                        related_invoice_id=int(
                            invoice_dd.value) if invoice_dd.value and invoice_dd.value != "" else None,
                        start_time=start_datetime,
                        end_time=end_datetime,
                    )
                    db.add(event)
                    db.commit()
                    self._show_success("Event added with links!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Save failed: {str(ex)[:100]}")

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Event"),
            content=ft.Column([
                title_f, desc_f, location_f,
                lead_dd, contact_dd, agenda_f, contract_dd, invoice_dd,
                ft.Row([start_date_picker, start_time_picker], spacing=10),
                ft.Row([end_date_picker, end_time_picker], spacing=10)
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
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
            try:
                capacity_num = 0
                if capacity_f.value:
                    capacity_num = int(capacity_f.value)

                with get_session() as db:
                    wh = Warehouse(
                        name=name_f.value.strip(),
                        code=code_f.value.strip().upper(),
                        city=city_f.value.strip() if city_f.value else None,
                        state=state_f.value.strip() if state_f.value else None,
                        capacity=capacity_num,
                    )
                    db.add(wh)
                    db.commit()
                    self._show_success("Warehouse added!")
                    self._close_dialog()
                    self._refresh()
            except IntegrityError:
                self._show_error("Warehouse code already exists")
            except Exception as ex:
                self._show_error(f"Save failed: {str(ex)[:100]}")

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
            try:
                value_num = 0
                if value_f.value:
                    try:
                        value_num = float(value_f.value.replace(',', ''))
                    except ValueError:
                        self._show_error("Invalid value format")
                        return

                with get_session() as db:
                    asset = Asset(
                        name=name_f.value.strip(),
                        asset_code=code_f.value.strip().upper(),
                        category=category_dd.value,
                        current_value=value_num,
                    )
                    db.add(asset)
                    db.commit()
                    self._show_success("Asset added!")
                    self._close_dialog()
                    self._refresh()
            except IntegrityError:
                self._show_error("Asset code already exists")
            except Exception as ex:
                self._show_error(f"Save failed: {str(ex)[:100]}")

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
            try:
                value_num = 0
                if value_f.value:
                    try:
                        value_num = float(value_f.value.replace(',', ''))
                    except ValueError:
                        self._show_error("Invalid value format")
                        return

                with get_session() as db:
                    contract = Contract(
                        title=title_f.value.strip(),
                        contract_number=number_f.value.strip().upper(),
                        contract_type=type_dd.value,
                        value=value_num,
                        start_date=date.today(),
                        end_date=date.today().replace(year=date.today().year + 1),
                    )
                    db.add(contract)
                    db.commit()
                    self._show_success("Contract added!")
                    self._close_dialog()
                    self._refresh()
            except IntegrityError:
                self._show_error("Contract number already exists")
            except Exception as ex:
                self._show_error(f"Save failed: {str(ex)[:100]}")

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
        amount_f = ft.TextField(
            label="Total Amount (₹) *", width=200, value="0")

        def save(e):
            if not customer_f.value or not number_f.value:
                self._show_error("Customer and Number required")
                return
            try:
                amount_num = 0
                if amount_f.value:
                    amount_num = float(amount_f.value.replace(',', ''))

                with get_session() as db:
                    invoice = Invoice(
                        invoice_number=number_f.value.strip().upper(),
                        customer_name=customer_f.value.strip(),
                        total_amount=amount_num,
                        invoice_date=date.today(),
                        status="draft",
                    )
                    db.add(invoice)
                    db.commit()
                    self._show_success("Invoice created (draft)!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(
                    f"Save failed (DB columns pending): {str(ex)[:100]}. Run scripts/fix_invoices_db.py")

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
    def _generate_test_data(self, e):
        """Enhanced test data with detailed feedback."""
        def test_data_click(e):
            self._show_loading("🧪 Creating test data...")
            try:
                result = crm_repo.create_test_data()
                total = sum(result.values())
                self._show_success(
                    f"✅ Created {total} records across {len(result)} tables!")
                logger.info(f"Test data created: {result}")
                self._refresh()
            except Exception as ex:
                logger.error(f"Test data error: {ex}")
                self._show_error(
                    f"❌ Test data failed: {str(ex)[:100]}. Tables may be missing.")
            finally:
                self._hide_loading()

        test_data_click(None)

    def _show_loading(self, msg="Loading..."):
        self.loading_snack = ft.SnackBar(
            content=ft.Row([ft.ProgressRing(), ft.Text(msg)],
                           alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=TEXT_SECONDARY
        )
        self._page.snack_bar = self.loading_snack
        self.loading_snack.open = True
        self._page.update()

    def _hide_loading(self):
        if hasattr(self, 'loading_snack'):
            self.loading_snack.open = False
            self._page.update()

    def _show_warning(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=WARNING)
        self._page.snack_bar = snack
        snack.open = True
        self._page.update()

    def _on_search(self, e):
        self.search_query = e.control.value
        self._page.update()

    def _close_dialog(self):
        for overlay in self._page.overlay:
            if isinstance(overlay, (ft.AlertDialog, ft.SnackBar)) and overlay.open:
                overlay.open = False
        self._page.update()

    def _show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(f"✅ {msg}"), bgcolor=SUCCESS)
        self._page.snack_bar = snack
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(f"❌ {msg}"), bgcolor=ERROR)
        self._page.snack_bar = snack
        snack.open = True
        self._page.update()


def show_crm(page, user):
    """Main entry point"""
    page.clean()
    page.add(CRMScreen(page, user))
