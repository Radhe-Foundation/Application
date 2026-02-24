"""
Vernika HRA - CRM Screen (Enhanced Production Level)
Customer Relationship Management Module
Leads, Contacts, Deals, Quotes, Products, Reports, Calendar - Industry Level
"""

import flet as ft
from datetime import datetime, date, timedelta
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import (
    CRMLead, CRMCustomer, CRMDeal, CRMActivity, CRMProduct, CRMProductCategory,
    CRMQuote, CRMQuoteItem, CRMTask, User
)
from sqlalchemy import or_, and_, func


# Theme colors - Professional palette
PRIMARY = "#1E3A5F"  # Deep navy blue
PRIMARY_LIGHT = "#2E5A8F"
SECONDARY = "#E91E63"  # Pink accent
SUCCESS = "#00C853"  # Bright green
WARNING = "#FF9100"  # Orange
ERROR = "#FF1744"  # Red
INFO = "#2979FF"  # Blue
BACKGROUND = "#F5F7FA"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1A2E"
TEXT_SECONDARY = "#6B7280"
BORDER_COLOR = "#E5E7EB"

# Lead status colors
STATUS_COLORS = {
    "new": INFO,
    "contacted": "#7C4DFF",
    "qualified": "#00BFA5",
    "proposal": WARNING,
    "negotiation": "#00BCD4",
    "won": SUCCESS,
    "lost": ERROR,
}

# Deal stage colors
STAGE_COLORS = {
    "qualification": INFO,
    "meeting_scheduled": "#7C4DFF",
    "proposal_sent": "#00BFA5",
    "negotiation": "#00BCD4",
    "closed_won": SUCCESS,
    "closed_lost": ERROR,
}


class CRMScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        # dashboard, leads, contacts, deals, activities, quotes, products, reports, calendar
        self.current_tab = "dashboard"

        # Search and filter state
        self.search_query = ""
        self.status_filter = "all"

        # Contact search and filter state
        self.contact_search_query = ""
        self.contact_category_filter = "all"

        # Calendar state
        self.calendar_year = datetime.now().year
        self.calendar_month = datetime.now().month

        self.content = self._build_content()

    def _show_snackbar(self, message, bgcolor=SUCCESS):
        """Show a snackbar notification"""
        # Handle both old style (ft.SnackBar object) and new style (message string)
        if isinstance(message, ft.SnackBar):
            snack = message
        else:
            snack = ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def refresh(self):
        """Refresh the CRM content"""
        self.content = self._build_content()
        self.update()
        self._page.update()

    def _get_db(self):
        """Get database session"""
        return get_db_session()

    def _get_user_info(self):
        """Get current user info"""
        username = "User"
        user_id = None
        if isinstance(self.user, dict):
            username = self.user.get('username', 'User')
            user_id = self.user.get('id')
        elif hasattr(self.user, 'username'):
            username = self.user.username
            if hasattr(self.user, 'id'):
                user_id = self.user.id
        return username, user_id

    def _build_content(self):
        """Build the CRM content"""
        username, user_id = self._get_user_info()

        # Header
        header = self._create_header(username)

        # Navigation tabs
        nav_tabs = self._create_nav_tabs()

        # Content based on current tab
        if self.current_tab == "dashboard":
            content = self._build_dashboard_view()
        elif self.current_tab == "leads":
            content = self._build_leads_view()
        elif self.current_tab == "contacts":
            content = self._build_contacts_view()
        elif self.current_tab == "deals":
            content = self._build_deals_view()
        elif self.current_tab == "activities":
            content = self._build_activities_view()
        elif self.current_tab == "quotes":
            content = self._build_quotes_view()
        elif self.current_tab == "products":
            content = self._build_products_view()
        elif self.current_tab == "reports":
            content = self._build_reports_view()
        elif self.current_tab == "calendar":
            content = self._build_calendar_view()
        else:
            content = self._build_dashboard_view()

        # Use ListView with expand for proper scrolling
        return ft.ListView(
            controls=[
                header,
                nav_tabs,
                ft.Container(
                    content=content,
                    expand=True,
                    padding=10,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _create_header(self, username):
        """Create header"""
        return ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.PEOPLE_ALT, color="WHITE", size=28),
                    ft.Text("CRM Dashboard", size=20, color="WHITE",
                            weight=ft.FontWeight.BOLD),
                ], spacing=15),
                ft.Container(expand=True),
                ft.Row([
                    ft.FilledButton(
                        "Add New",
                        icon=ft.Icons.ADD,
                        bgcolor=SUCCESS,
                        color="WHITE",
                        on_click=self._show_add_dialog,
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

    def _create_nav_tabs(self):
        """Create navigation tabs"""
        tabs = [
            ("dashboard", "Dashboard", ft.Icons.DASHBOARD),
            ("leads", "Leads", ft.Icons.LEADERBOARD),
            ("contacts", "Contacts", ft.Icons.CONTACTS),
            ("deals", "Deals", ft.Icons.BUSINESS_CENTER),
            ("quotes", "Quotes", ft.Icons.DESCRIPTION),
            ("products", "Products", ft.Icons.INVENTORY),
            ("activities", "Activities", ft.Icons.EVENT),
            ("calendar", "Calendar", ft.Icons.CALENDAR_MONTH),
            ("reports", "Reports", ft.Icons.ANALYTICS),
        ]

        return ft.Container(
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            content=ft.Row([
                self._create_tab_button(tab_id, label, icon)
                for tab_id, label, icon in tabs
            ], spacing=2, scroll=ft.ScrollMode.AUTO),
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

    # ============ DASHBOARD ============

    def _build_dashboard_view(self):
        """Build dashboard view"""
        leads = self._get_leads()
        contacts = self._get_contacts()
        deals = self._get_deals()
        activities = self._get_activities()

        # Calculate stats
        total_leads = len(leads)
        new_leads = len([l for l in leads if l.status == "new"])
        qualified_leads = len([l for l in leads if l.status in [
                              "qualified", "proposal", "negotiation"]])

        total_contacts = len(contacts)
        customers = len([c for c in contacts if c.category == "customer"])

        total_deals = len(deals)
        won_deals = len([d for d in deals if d.stage == "closed_won"])
        total_pipeline = sum(d.value for d in deals)
        won_value = sum(d.value for d in deals if d.stage == "closed_won")

        # Recent activities
        recent_activities = activities[:5] if activities else []

        return ft.Container(
            padding=20,
            content=ft.Column([
                # KPI Cards
                ft.Text("Overview", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Row([
                    self._create_kpi_card("Total Leads", str(
                        total_leads), ft.Icons.LEADERBOARD, INFO),
                    self._create_kpi_card("New Leads", str(
                        new_leads), ft.Icons.NEW_RELEASES, WARNING),
                    self._create_kpi_card("Qualified", str(
                        qualified_leads), ft.Icons.CHECK_CIRCLE, SUCCESS),
                    self._create_kpi_card("Contacts", str(
                        total_contacts), ft.Icons.CONTACTS, SECONDARY),
                ], spacing=15),
                ft.Container(height=20),

                ft.Row([
                    ft.Container(expand=True, content=ft.Column([
                        ft.Text("Deal Pipeline", size=18,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Container(height=10),
                        ft.Row([
                            self._create_kpi_card("Total Deals", str(
                                total_deals), ft.Icons.BUSINESS_CENTER, INFO),
                            self._create_kpi_card("Won", str(
                                won_deals), ft.Icons.STAR, SUCCESS),
                            self._create_kpi_card(
                                "Pipeline Value", f"₹{total_pipeline:,.0f}", ft.Icons.ATTACH_MONEY, WARNING),
                            self._create_kpi_card(
                                "Won Value", f"₹{won_value:,.0f}", ft.Icons.TRENDING_UP, SUCCESS),
                        ], spacing=15),
                    ])),
                ]),
                ft.Container(height=20),

                # Quick Actions
                ft.Text("Quick Actions", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton("Add Lead", icon=ft.Icons.PERSON_ADD, bgcolor=PRIMARY, color="WHITE",
                                      on_click=lambda e: self._show_add_lead_dialog()),
                    ft.ElevatedButton("Add Contact", icon=ft.Icons.CONTACT_PHONE, bgcolor=INFO, color="WHITE",
                                      on_click=lambda e: self._show_add_contact_dialog()),
                    ft.ElevatedButton("Add Deal", icon=ft.Icons.BUSINESS_CENTER, bgcolor=SUCCESS, color="WHITE",
                                      on_click=lambda e: self._show_add_deal_dialog()),
                ], spacing=10),
                ft.Container(height=20),

                # Recent Activity
                ft.Text("Recent Activities", size=18,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                self._build_recent_activities(recent_activities),

            ]),
        )

    def _create_kpi_card(self, title, value, icon_name, color):
        """Create a KPI card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(icon_name, size=32, color=color),
                        alignment=ft.alignment.Alignment(0, 0),
                        padding=10,
                        bgcolor=color + "15",
                        border_radius=30,
                    ),
                    ft.Container(height=10),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY),
                    ft.Text(title, size=12, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                padding=15,
                width=140,
            ),
            elevation=1,
        )

    def _build_recent_activities(self, activities):
        """Build recent activities list"""
        if not activities:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.EVENT_NOTE, size=48, color="#ccc"),
                    ft.Text("No recent activities", size=14, color="#999"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30,
                bgcolor=SURFACE,
                border_radius=10,
            )

        return ft.Container(
            content=ft.Column([
                self._create_activity_item(activity) for activity in activities
            ], spacing=8),
            bgcolor=SURFACE,
            padding=15,
            border_radius=10,
        )

    def _create_activity_item(self, activity):
        """Create activity item"""
        icon_map = {
            "call": ft.Icons.CALL,
            "meeting": ft.Icons.GROUP,
            "task": ft.Icons.TASK,
            "email": ft.Icons.EMAIL,
            "note": ft.Icons.NOTE,
        }
        icon = icon_map.get(activity.activity_type, ft.Icons.EVENT)

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=20, color=PRIMARY),
                    bgcolor=PRIMARY + "15",
                    width=40,
                    height=40,
                    border_radius=20,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(activity.title, size=14,
                            weight=ft.FontWeight.W_500),
                    ft.Text(activity.description or "",
                            size=12, color=TEXT_SECONDARY),
                ], expand=True),
                ft.Text(activity.created_at.strftime("%d %b") if activity.created_at else "",
                        size=11, color=TEXT_SECONDARY),
            ], spacing=10),
            padding=10,
            bgcolor="#F9FAFB",
            border_radius=8,
        )

    # ============ LEADS ============

    def _build_leads_view(self):
        """Build leads management view"""
        leads = self._get_leads()

        # Search and filter bar
        filter_bar = self._create_leads_filter_bar()

        # Stats
        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_stat_card("Total Leads", len(
                    leads), ft.Icons.LEADERBOARD, INFO),
                self._create_stat_card("New", len(
                    [l for l in leads if l.status == "new"]), ft.Icons.NEW_RELEASES, WARNING),
                self._create_stat_card("Qualified", len(
                    [l for l in leads if l.status == "qualified"]), ft.Icons.CHECK_CIRCLE, SUCCESS),
                self._create_stat_card("Won", len(
                    [l for l in leads if l.status == "won"]), ft.Icons.STAR, "#4CAF50"),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )

        # Leads table - use ListView for proper scrolling
        if leads:
            leads_table = self._create_leads_table(leads)
        else:
            leads_table = self._create_empty_state(
                "No leads found", "Add your first lead to get started",
                ft.Icons.LEADERBOARD, lambda: self._show_add_lead_dialog()
            )

        # Use Column with expand for scrollable content
        return ft.Column(
            controls=[
                filter_bar,
                stats_row,
                ft.Container(content=leads_table, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    def _create_leads_filter_bar(self):
        """Create leads filter bar"""
        # Search field with actual search functionality
        search_field = ft.TextField(
            hint_text="Search leads...",
            prefix_icon=ft.Icons.SEARCH,
            width=300,
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY,
            on_change=self._on_lead_search,
            value=self.search_query,
        )

        # Status filter with actual filter functionality
        status_filter = ft.Dropdown(
            hint_text="Status",
            width=150,
            options=[
                ft.dropdown.Option("all", "All Status"),
                ft.dropdown.Option("new", "New"),
                ft.dropdown.Option("contacted", "Contacted"),
                ft.dropdown.Option("qualified", "Qualified"),
                ft.dropdown.Option("proposal", "Proposal"),
                ft.dropdown.Option("negotiation", "Negotiation"),
                ft.dropdown.Option("won", "Won"),
                ft.dropdown.Option("lost", "Lost"),
            ],
            value=self.status_filter,
            on_select=self._on_lead_filter_change,
            border_color=BORDER_COLOR,
        )

        return ft.Container(
            content=ft.Row([
                search_field,
                status_filter,
                ft.Container(expand=True),
                ft.ElevatedButton("Add Lead", icon=ft.Icons.ADD, bgcolor=PRIMARY, color="WHITE",
                                  on_click=self._show_add_lead_dialog),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _on_lead_search(self, e):
        """Handle lead search"""
        self.search_query = e.control.value.lower()
        self.refresh()

    def _on_lead_filter_change(self, e):
        """Handle lead filter change"""
        # Handle both on_change and on_select events
        if hasattr(e, 'control'):
            self.status_filter = e.control.value
        else:
            self.status_filter = e.value if hasattr(e, 'value') else str(e)
        self.refresh()

    def _on_contact_search(self, e):
        """Handle contact search"""
        self.contact_search_query = e.control.value.lower() if hasattr(e.control,
                                                                       'value') else ""
        self.refresh()

    def _on_contact_filter_change(self, e):
        """Handle contact filter change"""
        # Handle both on_change and on_select events
        if hasattr(e, 'control'):
            self.contact_category_filter = e.control.value
        else:
            self.contact_category_filter = e.value if hasattr(
                e, 'value') else str(e)
        self.refresh()

    def _create_leads_table(self, leads):
        """Create leads table using scrollable ListView instead of DataTable"""
        rows = []
        for lead in leads:
            rows.append(self._create_lead_row(lead))

        return ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=10,
                padding=10,
                controls=rows if rows else [
                    self._create_empty_table_row("No leads found")]
            ),
            bgcolor=SURFACE,
            padding=10,
            border_radius=10,
            expand=True,
        )

    def _create_empty_table_row(self, message):
        """Create empty table row message"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INBOX, size=48, color="#ccc"),
                ft.Text(message, size=14, color="#999"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
            alignment=ft.alignment.Alignment(0, 0),
        )

    def _create_lead_row(self, lead):
        """Create lead table row using Container instead of DataRow for better scrolling"""
        status_color = STATUS_COLORS.get(lead.status, INFO)

        return ft.Container(
            content=ft.Row([
                # Name
                ft.Container(
                    content=ft.Text(lead.name or "",
                                    weight=ft.FontWeight.W_500, size=14),
                    width=150,
                ),
                # Company
                ft.Container(
                    content=ft.Text(lead.company or "-", size=13),
                    width=120,
                ),
                # Email
                ft.Container(
                    content=ft.Text(lead.email or "-", size=12),
                    width=150,
                    expand=True,
                ),
                # Phone
                ft.Container(
                    content=ft.Text(lead.phone or "-", size=12),
                    width=100,
                ),
                # Status
                ft.Container(
                    content=ft.Text(
                        lead.status.upper() if lead.status else "NEW", size=10, color="WHITE"),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                    width=80,
                ),
                # Priority
                ft.Container(
                    content=ft.Text(lead.priority.upper()
                                    if lead.priority else "MEDIUM", size=11),
                    width=70,
                ),
                # Value
                ft.Container(
                    content=ft.Text(
                        f"₹{lead.expected_value:,.0f}" if lead.expected_value else "₹0", size=12),
                    width=90,
                ),
                # Actions
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_size=18, tooltip="Edit",
                                      on_click=lambda e, l=lead: self._edit_lead(l)),
                        ft.IconButton(ft.Icons.DELETE, icon_size=18, tooltip="Delete",
                                      on_click=lambda e, l=lead: self._delete_lead(l)),
                        ft.IconButton(ft.Icons.SWAP_HORIZ, icon_size=18, tooltip="Convert to Customer",
                                      on_click=lambda e, l=lead: self._convert_lead(l)),
                    ], spacing=0),
                    width=120,
                ),
            ], spacing=10, alignment=ft.MainAxisAlignment.START),
            padding=12,
            bgcolor=SURFACE,
            border_radius=8,
            border=ft.border.all(1, BORDER_COLOR),
        )

    # ============ CONTACTS ============

    def _build_contacts_view(self):
        """Build contacts management view"""
        contacts = self._get_contacts()

        # Filter bar
        filter_bar = self._create_contacts_filter_bar()

        # Stats
        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_stat_card("Total Contacts", len(
                    contacts), ft.Icons.CONTACTS, INFO),
                self._create_stat_card("Customers", len(
                    [c for c in contacts if c.category == "customer"]), ft.Icons.SHOPPING_CART, SUCCESS),
                self._create_stat_card("Prospects", len(
                    [c for c in contacts if c.category == "prospect"]), ft.Icons.FIND_IN_PAGE, WARNING),
                self._create_stat_card("Partners", len(
                    [c for c in contacts if c.category == "partner"]), ft.Icons.BUSINESS_CENTER, SECONDARY),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )

        # Contacts grid
        if contacts:
            contacts_grid = self._create_contacts_grid(contacts)
        else:
            contacts_grid = self._create_empty_state(
                "No contacts found", "Add your first contact",
                ft.Icons.CONTACTS, lambda: self._show_add_contact_dialog()
            )

        # Use Column with expand for scrollable content
        return ft.Column(
            controls=[
                filter_bar,
                stats_row,
                ft.Container(content=contacts_grid, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    def _create_contacts_filter_bar(self):
        """Create contacts filter bar"""
        # Search field with actual functionality
        search_field = ft.TextField(
            hint_text="Search contacts...",
            prefix_icon=ft.Icons.SEARCH,
            width=300,
            on_change=lambda e: self._on_contact_search(e),
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY,
        )

        # Category filter with actual functionality
        category_filter = ft.Dropdown(
            hint_text="Category",
            width=150,
            options=[
                ft.dropdown.Option("all", "All"),
                ft.dropdown.Option("customer", "Customer"),
                ft.dropdown.Option("prospect", "Prospect"),
                ft.dropdown.Option("partner", "Partner"),
                ft.dropdown.Option("vendor", "Vendor"),
            ],
            value="all",
            on_select=lambda e: self._on_contact_filter_change(e),
            border_color=BORDER_COLOR,
        )

        return ft.Container(
            content=ft.Row([
                search_field,
                category_filter,
                ft.Container(expand=True),
                ft.ElevatedButton("Add Contact", icon=ft.Icons.ADD, bgcolor=PRIMARY, color="WHITE",
                                  on_click=self._show_add_contact_dialog),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _create_contacts_grid(self, contacts):
        """Create contacts grid with scrollable ListView"""
        if not contacts:
            return self._create_empty_state(
                "No contacts found", "Add your first contact",
                ft.Icons.CONTACTS, lambda: self._show_add_contact_dialog()
            )

        return ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=15,
                padding=15,
                controls=[
                    ft.Container(
                        content=ft.Row([
                            self._create_contact_card(contact) for contact in contacts[i:i+3] if i+3 <= len(contacts)
                        ], spacing=15) if i+3 <= len(contacts) else ft.Row([
                            self._create_contact_card(c) for c in contacts[i:]
                        ], spacing=15)
                    ) for i in range(0, len(contacts), 3)
                ] if len(contacts) > 0 else []
            ),
            expand=True,
        )

    def _create_contact_card(self, contact):
        """Create contact card"""
        category_color = SUCCESS if contact.category == "customer" else WARNING if contact.category == "prospect" else INFO

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(contact.name[0].upper(
                            ) if contact.name else "?", size=24),
                            bgcolor=PRIMARY,
                            color="WHITE",
                            radius=28,
                        ),
                        ft.Column([
                            ft.Text(contact.name or "", size=16,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(contact.designation or "",
                                    size=12, color=TEXT_SECONDARY),
                        ], expand=True),
                        ft.Container(
                            content=ft.Text(contact.category.upper(
                            ) if contact.category else "", size=9, color="WHITE"),
                            bgcolor=category_color,
                            padding=ft.padding.symmetric(
                                horizontal=8, vertical=4),
                            border_radius=10,
                        ),
                    ]),
                    ft.Divider(height=15),
                    ft.Text(contact.company or "No Company",
                            size=13, color=TEXT_SECONDARY),
                    ft.Container(height=5),
                    ft.Row([
                        ft.Icon(ft.Icons.EMAIL, size=14, color=TEXT_SECONDARY),
                        ft.Text(contact.email or "-", size=12,
                                color=TEXT_SECONDARY, expand=True),
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.PHONE, size=14, color=TEXT_SECONDARY),
                        ft.Text(contact.phone or "-", size=12,
                                color=TEXT_SECONDARY, expand=True),
                    ]),
                    ft.Container(height=10),
                    ft.Row([
                        ft.TextButton(
                            "Edit", icon=ft.Icons.EDIT, on_click=lambda e, c=contact: self._edit_contact(c)),
                        ft.TextButton("Delete", icon=ft.Icons.DELETE,
                                      on_click=lambda e, c=contact: self._delete_contact(c)),
                    ], alignment=ft.MainAxisAlignment.END),
                ], spacing=5),
                padding=15,
                width=300,
            ),
            elevation=2,
        )

    # ============ DEALS ============

    def _build_deals_view(self):
        """Build deals pipeline view"""
        deals = self._get_deals()

        # Stats
        total_value = sum(d.value for d in deals)
        won_value = sum(d.value for d in deals if d.stage == "closed_won")
        avg_deal = total_value / len(deals) if deals else 0

        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_stat_card("Total Deals", len(
                    deals), ft.Icons.BUSINESS_CENTER, INFO),
                self._create_stat_card(
                    "Total Value", f"₹{total_value:,.0f}", ft.Icons.ATTACH_MONEY, WARNING),
                self._create_stat_card(
                    "Won Value", f"₹{won_value:,.0f}", ft.Icons.CHECK_CIRCLE, SUCCESS),
                self._create_stat_card(
                    "Avg Deal", f"₹{avg_deal:,.0f}", ft.Icons.TRENDING_UP, PRIMARY),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )

        # Pipeline view
        pipeline = self._create_pipeline_view(deals)

        # Use Column with expand for scrollable content
        return ft.Column(
            controls=[
                self._create_deals_filter_bar(),
                stats_row,
                ft.Container(content=pipeline, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    def _create_deals_filter_bar(self):
        """Create deals filter bar"""
        return ft.Container(
            content=ft.Row([
                ft.TextField(
                    hint_text="Search deals...",
                    prefix_icon=ft.Icons.SEARCH,
                    width=300,
                    border_color=BORDER_COLOR,
                    focused_border_color=PRIMARY,
                ),
                ft.Container(expand=True),
                ft.ElevatedButton("Add Deal", icon=ft.Icons.ADD, bgcolor=PRIMARY, color="WHITE",
                                  on_click=self._show_add_deal_dialog),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _create_pipeline_view(self, deals):
        """Create pipeline kanban view with scrollable columns"""
        stages = [
            ("qualification", "Qualification"),
            ("meeting_scheduled", "Meeting"),
            ("proposal_sent", "Proposal"),
            ("negotiation", "Negotiation"),
            ("closed_won", "Won"),
        ]

        return ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=10,
                padding=15,
                controls=[
                    ft.Row([
                        self._create_pipeline_stage(
                            stage_id, title, [d for d in deals if d.stage == stage_id])
                        for stage_id, title in stages
                    ], spacing=10)
                ],
                auto_scroll=False,
            ),
            expand=True,
        )

    def _create_pipeline_stage(self, stage, title, deals):
        """Create a pipeline stage column"""
        stage_value = sum(d.value for d in deals)
        stage_color = STAGE_COLORS.get(stage, INFO)

        return ft.Container(
            width=220,
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text(title, size=14,
                                weight=ft.FontWeight.BOLD, color="WHITE"),
                        ft.Text(
                            f"{len(deals)} deals • ₹{stage_value:,.0f}", size=11, color="WHITE"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=stage_color,
                    padding=12,
                    border_radius=ft.border_radius.only(
                        top_left=10, top_right=10),
                ),
                ft.Container(
                    content=ft.ListView(
                        expand=True,
                        spacing=8,
                        padding=10,
                        controls=[
                            self._create_deal_card(deal) for deal in deals
                        ] if deals else [
                            ft.Container(
                                content=ft.Text(
                                    "No deals", size=11, color=TEXT_SECONDARY),
                                padding=10,
                            )
                        ]
                    ),
                    bgcolor="#F9FAFB",
                    padding=5,
                    border_radius=ft.border_radius.only(
                        bottom_left=10, bottom_right=10),
                    expand=True,
                ),
            ], spacing=0),
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=10,
        )

    def _create_deal_card(self, deal):
        """Create deal card"""
        return ft.Container(
            content=ft.Column([
                ft.Text(deal.title or "", size=13, weight=ft.FontWeight.W_500),
                ft.Text(f"₹{deal.value:,.0f}" if deal.value else "₹0",
                        size=12, color=SUCCESS, weight=ft.FontWeight.BOLD),
                ft.Text(deal.customer.name if deal.customer else "",
                        size=11, color=TEXT_SECONDARY),
            ], spacing=2),
            padding=10,
            bgcolor=SURFACE,
            border_radius=8,
            border=ft.border.all(1, BORDER_COLOR),
            ink=True,
            on_click=lambda e: self._edit_deal(deal),
        )

    # ============ ACTIVITIES ============

    def _build_activities_view(self):
        """Build activities view"""
        activities = self._get_activities()

        # Filter bar
        filter_bar = self._create_activities_filter_bar()

        # Activities list - use ListView for proper scrolling
        if activities:
            activities_list = self._create_activities_list(activities)
        else:
            activities_list = self._create_empty_state(
                "No activities found", "Add your first activity",
                ft.Icons.EVENT_NOTE, lambda: self._show_add_activity_dialog()
            )

        # Use Column with expand for scrollable content
        return ft.Column(
            controls=[
                filter_bar,
                ft.Container(content=activities_list, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    def _create_activities_filter_bar(self):
        """Create activities filter bar"""
        return ft.Container(
            content=ft.Row([
                ft.Dropdown(
                    hint_text="Type",
                    width=150,
                    options=[
                        ft.dropdown.Option("all", "All Types"),
                        ft.dropdown.Option("call", "Call"),
                        ft.dropdown.Option("meeting", "Meeting"),
                        ft.dropdown.Option("task", "Task"),
                        ft.dropdown.Option("email", "Email"),
                        ft.dropdown.Option("note", "Note"),
                    ],
                    value="all",
                    border_color=BORDER_COLOR,
                ),
                ft.Container(expand=True),
                ft.ElevatedButton("Add Activity", icon=ft.Icons.ADD, bgcolor=PRIMARY, color="WHITE",
                                  on_click=self._show_add_activity_dialog),
            ], spacing=10),
            padding=15,
            bgcolor=SURFACE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, BORDER_COLOR)),
        )

    def _create_activities_list(self, activities):
        """Create activities list with scrollable ListView"""
        if not activities:
            return self._create_empty_state(
                "No activities found", "Add your first activity",
                ft.Icons.EVENT_NOTE, lambda: self._show_add_activity_dialog()
            )

        return ft.Container(
            content=ft.ListView(
                expand=True,
                spacing=10,
                padding=15,
                controls=[
                    self._create_activity_row(activity) for activity in activities
                ]
            ),
            expand=True,
        )

    def _create_activity_row(self, activity):
        """Create activity row"""
        icon_map = {
            "call": ft.Icons.CALL,
            "meeting": ft.Icons.GROUP,
            "task": ft.Icons.TASK,
            "email": ft.Icons.EMAIL,
            "note": ft.Icons.NOTE,
        }
        icon = icon_map.get(activity.activity_type, ft.Icons.EVENT)

        status_icon = ft.Icons.CHECK_CIRCLE if activity.is_completed else ft.Icons.RADIO_BUTTON_UNCHECKED
        status_color = SUCCESS if activity.is_completed else TEXT_SECONDARY

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=PRIMARY),
                        bgcolor=PRIMARY + "15",
                        width=45,
                        height=45,
                        border_radius=22,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(activity.title or "", size=15,
                                weight=ft.FontWeight.W_500),
                        ft.Text(activity.description or "",
                                size=12, color=TEXT_SECONDARY),
                        ft.Text(f"Due: {activity.due_date.strftime('%d %b %Y') if activity.due_date else 'No due date'}",
                                size=11, color=TEXT_SECONDARY),
                    ], expand=True),
                    ft.Container(
                        content=ft.Icon(status_icon, color=status_color),
                        on_click=lambda e: self._toggle_activity_complete(
                            activity),
                    ),
                    ft.IconButton(ft.Icons.EDIT, icon_size=18,
                                  on_click=lambda a=activity: self._edit_activity(a)),
                    ft.IconButton(ft.Icons.DELETE, icon_size=18,
                                  on_click=lambda a=activity: self._delete_activity(a)),
                ], spacing=15),
                padding=15,
            ),
            elevation=1,
        )

    # ============ QUOTES ============

    def _get_quotes(self):
        """Get all quotes"""
        try:
            from database.models import CRMQuote
            session = self._get_db()
            try:
                return session.query(CRMQuote).order_by(CRMQuote.created_at.desc()).all()
            except Exception as e:
                print(f"Error getting quotes: {e}")
                return []
            finally:
                session.close()
        except:
            return []

    def _build_quotes_view(self):
        """Build quotes/proposals view"""
        quotes = self._get_quotes()
        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_stat_card("Total Quotes", len(
                    quotes), ft.Icons.DESCRIPTION, INFO),
                self._create_stat_card("Draft", len(
                    [q for q in quotes if q.status == "draft"]), ft.Icons.EDIT, TEXT_SECONDARY),
                self._create_stat_card("Sent", len(
                    [q for q in quotes if q.status == "sent"]), ft.Icons.SEND, INFO),
                self._create_stat_card("Accepted", len(
                    [q for q in quotes if q.status == "accepted"]), ft.Icons.CHECK_CIRCLE, SUCCESS),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )
        quotes_list = self._create_quotes_list(quotes) if quotes else self._create_empty_state(
            "No quotes found", "Create your first quote", ft.Icons.DESCRIPTION, lambda: self._show_add_quote_dialog())
        return ft.Column(controls=[self._create_quotes_filter_bar(), stats_row, ft.Container(content=quotes_list, expand=True)], spacing=0, expand=True)

    def _create_quotes_filter_bar(self):
        return ft.Container(content=ft.Row([ft.TextField(hint_text="Search quotes...", prefix_icon=ft.Icons.SEARCH, width=250, border_color=BORDER_COLOR, focused_border_color=PRIMARY), ft.Container(expand=True), ft.ElevatedButton("Create Quote", icon=ft.Icons.ADD, bgcolor=PRIMARY, color="WHITE", on_click=self._show_add_quote_dialog)], spacing=10), padding=15, bgcolor=SURFACE, border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER_COLOR)))

    def _create_quotes_list(self, quotes):
        return ft.Container(content=ft.ListView(expand=True, spacing=10, padding=15, controls=[self._create_quote_row(q) for q in quotes]), expand=True)

    def _create_quote_row(self, quote):
        status_colors = {"draft": TEXT_SECONDARY, "sent": INFO,
                         "accepted": SUCCESS, "rejected": ERROR, "declined": ERROR}
        return ft.Card(content=ft.Container(content=ft.Row([ft.Column([ft.Text(quote.title or "", size=15, weight=ft.FontWeight.W_500), ft.Text(f"Quote #{quote.quote_number}" if hasattr(quote, 'quote_number') and quote.quote_number else "Draft Quote", size=12, color=TEXT_SECONDARY)], expand=True), ft.Container(content=ft.Text((quote.status or "draft").upper(), size=10, color="WHITE"), bgcolor=status_colors.get(quote.status, TEXT_SECONDARY), padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=10), ft.Text(f"₹{quote.total_amount:,.0f}" if quote.total_amount else "₹0", size=16, weight=ft.FontWeight.BOLD, color=SUCCESS), ft.IconButton(ft.Icons.EDIT, icon_size=18, on_click=lambda q=quote: self._edit_quote(q))], spacing=15), padding=15), elevation=1)

    def _show_add_quote_dialog(self):
        """Show add quote dialog"""
        contacts = self._get_contacts()
        title_field = ft.TextField(
            label="Quote Title *", hint_text="Enter quote title", border_color=PRIMARY)
        customer_dropdown = ft.Dropdown(label="Customer *", options=[ft.dropdown.Option(str(
            c.id), c.name) for c in contacts] if contacts else [ft.dropdown.Option("", "No contacts")], border_color=PRIMARY)
        value_field = ft.TextField(
            label="Amount", hint_text="Enter amount", value="0", border_color=PRIMARY)

        def save_quote(e):
            if not title_field.value or not customer_dropdown.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Title and Customer are required")))
                return
            try:
                from database.models import CRMQuote
                session = self._get_db()
                try:
                    _, user_id = self._get_user_info()
                    quote = CRMQuote(title=title_field.value, customer_id=int(customer_dropdown.value), total_amount=float(
                        value_field.value or 0), status="draft", created_by_id=user_id)
                    session.add(quote)
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Quote created successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
                except Exception as ex:
                    session.rollback()
                    self._show_snackbar(ft.SnackBar(
                        content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
                finally:
                    session.close()
            except Exception as e:
                self._show_snackbar(ft.SnackBar(content=ft.Text(
                    "Please add customer data first"), bgcolor=WARNING))

        dialog = ft.AlertDialog(title=ft.Text("Create Quote"), content=ft.Container(content=ft.Column([title_field, customer_dropdown, value_field], tight=True, spacing=12), width=400), actions=[
                                ft.TextButton("Cancel", on_click=lambda e: self._page.close(dialog)), ft.FilledButton("Save", on_click=save_quote, bgcolor=PRIMARY, color="WHITE")])
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _edit_quote(self, quote):
        self._show_snackbar(ft.SnackBar(content=ft.Text(
            "Quote editing coming soon"), bgcolor=INFO))

    # ============ PRODUCTS ============

    def _get_products(self):
        """Get all products"""
        try:
            from database.models import CRMProduct
            session = self._get_db()
            try:
                return session.query(CRMProduct).order_by(CRMProduct.name).all()
            except Exception as e:
                print(f"Error getting products: {e}")
                return []
            finally:
                session.close()
        except:
            return []

    def _build_products_view(self):
        """Build products/services catalog view"""
        products = self._get_products()
        stats_row = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_stat_card("Total Products", len(
                    products), ft.Icons.INVENTORY, INFO),
                self._create_stat_card("Active", len(
                    [p for p in products if p.is_active]), ft.Icons.CHECK_CIRCLE, SUCCESS),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        )
        products_grid = self._create_products_grid(products) if products else self._create_empty_state(
            "No products found", "Add your first product", ft.Icons.INVENTORY, lambda: self._show_add_product_dialog())
        return ft.Column(controls=[self._create_products_filter_bar(), stats_row, ft.Container(content=products_grid, expand=True)], spacing=0, expand=True)

    def _create_products_filter_bar(self):
        return ft.Container(content=ft.Row([ft.TextField(hint_text="Search products...", prefix_icon=ft.Icons.SEARCH, width=250, border_color=BORDER_COLOR, focused_border_color=PRIMARY), ft.Container(expand=True), ft.ElevatedButton("Add Product", icon=ft.Icons.ADD, bgcolor=PRIMARY, color="WHITE", on_click=self._show_add_product_dialog)], spacing=10), padding=15, bgcolor=SURFACE, border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER_COLOR)))

    def _create_products_grid(self, products):
        return ft.Container(content=ft.ListView(expand=True, spacing=10, padding=15, controls=[self._create_product_card(p) for p in products]), expand=True)

    def _create_product_card(self, product):
        return ft.Card(content=ft.Container(content=ft.Row([ft.Container(content=ft.Icon(ft.Icons.INVENTORY, size=32, color=PRIMARY), bgcolor=PRIMARY + "15", width=60, height=60, border_radius=30, alignment=ft.alignment.Alignment(0, 0)), ft.Column([ft.Text(product.name or "", size=15, weight=ft.FontWeight.W_500), ft.Text(f"SKU: {product.sku}" if hasattr(product, 'sku') and product.sku else "No SKU", size=12, color=TEXT_SECONDARY)], expand=True), ft.Text(f"₹{product.unit_price:,.0f}" if hasattr(product, 'unit_price') and product.unit_price else "₹0", size=18, weight=ft.FontWeight.BOLD, color=SUCCESS)], spacing=15), padding=15), elevation=1)

    def _show_add_product_dialog(self):
        """Show add product dialog"""
        name_field = ft.TextField(
            label="Product Name *", hint_text="Enter product name", border_color=PRIMARY)
        sku_field = ft.TextField(
            label="SKU", hint_text="Enter SKU", border_color=PRIMARY)
        price_field = ft.TextField(
            label="Unit Price", hint_text="Enter price", value="0", border_color=PRIMARY)

        def save_product(e):
            if not name_field.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Product name is required")))
                return
            try:
                from database.models import CRMProduct
                session = self._get_db()
                try:
                    product = CRMProduct(name=name_field.value, sku=sku_field.value, unit_price=float(
                        price_field.value or 0), is_active=True)
                    session.add(product)
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Product added successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
                except Exception as ex:
                    session.rollback()
                    self._show_snackbar(ft.SnackBar(
                        content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
                finally:
                    session.close()
            except Exception as e:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Error adding product"), bgcolor=ERROR))

        dialog = ft.AlertDialog(title=ft.Text("Add Product"), content=ft.Container(content=ft.Column([name_field, sku_field, price_field], tight=True, spacing=12), width=400), actions=[
                                ft.TextButton("Cancel", on_click=lambda e: self._page.close(dialog)), ft.FilledButton("Save", on_click=save_product, bgcolor=PRIMARY, color="WHITE")])
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    # ============ CALENDAR ============

    def _build_calendar_view(self):
        """Build calendar view for activities"""
        activities = self._get_activities()
        return ft.Container(padding=20, content=ft.Column([
            ft.Row([ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=self._prev_month), ft.Text(f"{datetime(self.calendar_year, self.calendar_month, 1).strftime('%B %Y')}", size=20, weight=ft.FontWeight.BOLD), ft.IconButton(
                ft.Icons.CHEVRON_RIGHT, on_click=self._next_month), ft.Container(expand=True), ft.ElevatedButton("Today", on_click=self._go_to_today), ft.Container(width=10), ft.ElevatedButton("Add Activity", icon=ft.Icons.ADD, bgcolor=PRIMARY, color="WHITE", on_click=self._show_add_activity_dialog)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
            self._build_calendar_grid(
                activities, self.calendar_year, self.calendar_month),
            ft.Container(height=20),
            ft.Text("Upcoming Activities", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            self._build_upcoming_activities(activities)
        ]))

    def _build_calendar_grid(self, activities, year, month):
        first_day = date(year, month, 1)
        days_in_month = (date(year, month % 12 + 1, 1) - timedelta(days=1)).day
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        rows = [ft.Container(content=ft.Row([ft.Text(day, size=12, weight=ft.FontWeight.BOLD, expand=True, text_align=ft.TextAlign.CENTER)
                             for day in day_names]), padding=10, bgcolor=PRIMARY, border_radius=ft.border_radius.only(top_left=10, top_right=10))]
        start_offset = first_day.weekday()
        current_day = 1
        for week in range(6):
            week_controls = []
            for day in range(7):
                cell_index = week * 7 + day
                if cell_index < start_offset or current_day > days_in_month:
                    week_controls.append(ft.Container(expand=True, height=80))
                else:
                    day_activities = [a for a in activities if a.due_date and a.due_date.day ==
                                      current_day and a.due_date.month == month and a.due_date.year == year]
                    week_controls.append(self._create_calendar_day(
                        current_day, day_activities))
                    current_day += 1
            if current_day > days_in_month and week >= 4:
                break
            rows.append(ft.Container(content=ft.Row(week_controls,
                        spacing=2), border=ft.border.all(1, BORDER_COLOR)))
        return ft.Container(content=ft.Column(rows, spacing=0), border=ft.border.all(1, BORDER_COLOR), border_radius=10)

    def _create_calendar_day(self, day, activities):
        is_today = day == datetime.now().day and self.calendar_month == datetime.now(
        ).month and self.calendar_year == datetime.now().year
        return ft.Container(content=ft.Column([ft.Text(str(day), size=14, weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL, color=PRIMARY if is_today else TEXT_PRIMARY), *[ft.Container(content=ft.Text(a.title[:12] + ".." if len(a.title) > 12 else a.title, size=9, color="WHITE"), bgcolor=INFO, padding=2, border_radius=3, margin=ft.margin.only(bottom=1)) for a in activities[:2]]], spacing=0), padding=5, height=80, expand=True, bgcolor=PRIMARY + "10" if is_today else "transparent", border=ft.border.all(1, PRIMARY if is_today else BORDER_COLOR))

    def _build_upcoming_activities(self, activities):
        upcoming = [
            a for a in activities if a.due_date and a.due_date >= datetime.now()]
        upcoming = sorted(upcoming, key=lambda x: x.due_date)[:5]
        if not upcoming:
            return ft.Container(content=ft.Text("No upcoming activities", size=14, color=TEXT_SECONDARY), padding=20)
        return ft.Container(content=ft.Column([self._create_activity_item(a) for a in upcoming], spacing=8), bgcolor=SURFACE, padding=15, border_radius=10)

    def _prev_month(self, e):
        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1
        self.refresh()

    def _next_month(self, e):
        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1
        self.refresh()

    def _go_to_today(self, e):
        self.calendar_year = datetime.now().year
        self.calendar_month = datetime.now().month
        self.refresh()

    # ============ REPORTS ============

    def _build_reports_view(self):
        """Build reports view"""
        leads = self._get_leads()
        deals = self._get_deals()
        quotes = self._get_quotes()
        total_leads = len(leads)
        won_leads = len([l for l in leads if l.status == "won"])
        lead_conversion = (won_leads / total_leads *
                           100) if total_leads > 0 else 0
        total_deals = len(deals)
        won_deals = len([d for d in deals if d.stage == "closed_won"])
        won_value = sum(d.value for d in deals if d.stage == "closed_won")

        # Quick Actions for Reports
        return ft.Container(padding=20, content=ft.Column([
            ft.Row([ft.Text("CRM Analytics & Reports", size=22, weight=ft.FontWeight.BOLD), ft.Container(expand=True), ft.ElevatedButton("Add Lead", icon=ft.Icons.PERSON_ADD, bgcolor=PRIMARY, color="WHITE", on_click=lambda e: (self._switch_tab("leads"), self._show_add_lead_dialog(
            ))), ft.Container(width=5), ft.ElevatedButton("Add Deal", icon=ft.Icons.BUSINESS_CENTER, bgcolor=SUCCESS, color="WHITE", on_click=lambda e: (self._switch_tab("deals"), self._show_add_deal_dialog()))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=20),
            ft.Text("Lead Performance", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Row([self._create_report_card("Total Leads", str(total_leads), ft.Icons.LEADERBOARD, INFO), self._create_report_card("Converted", str(
                won_leads), ft.Icons.CHECK_CIRCLE, SUCCESS), self._create_report_card("Conversion", f"{lead_conversion:.1f}%", ft.Icons.TRENDING_UP, PRIMARY)], spacing=15),
            ft.Container(height=20),
            ft.Text("Deal Pipeline", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Row([self._create_report_card("Total Deals", str(total_deals), ft.Icons.BUSINESS_CENTER, INFO), self._create_report_card("Won", str(
                won_deals), ft.Icons.STAR, SUCCESS), self._create_report_card("Won Value", f"₹{won_value:,.0f}", ft.Icons.ATTACH_MONEY, WARNING)], spacing=15),
            ft.Container(height=20),
            ft.Text("Pipeline Overview", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            self._build_pipeline_chart(deals)
        ], scroll=ft.ScrollMode.AUTO))

    def _create_report_card(self, title, value, icon_name, color):
        return ft.Card(content=ft.Container(content=ft.Column([ft.Container(content=ft.Icon(icon_name, size=28, color=color), alignment=ft.alignment.Alignment(0, 0), padding=10, bgcolor=color + "15", border_radius=30), ft.Container(height=10), ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), ft.Text(title, size=11, color=TEXT_SECONDARY)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2), padding=15, width=150), elevation=1)

    def _build_pipeline_chart(self, deals):
        stages = [("qualification", "Qualification"), ("meeting_scheduled", "Meeting"),
                  ("proposal_sent", "Proposal"), ("negotiation", "Negotiation"), ("closed_won", "Won")]
        return ft.Container(content=ft.Column([ft.Container(content=ft.Row([ft.Text(title, size=12, weight=ft.FontWeight.W_500), ft.Container(expand=True), ft.Text(f"₹{sum(d.value for d in deals if d.stage == stage_id):,.0f}", size=12, weight=ft.FontWeight.BOLD, color=STAGE_COLORS.get(stage_id, INFO))], spacing=10), bgcolor=STAGE_COLORS.get(stage_id, INFO) + "20", padding=10, border_radius=8, margin=ft.margin.only(bottom=5)) for stage_id, title in stages]), bgcolor=SURFACE, padding=15, border_radius=10)

    # ============ HELPER METHODS ============

    def _create_stat_card(self, title, value, icon_name, color):
        """Create a statistics card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon_name, size=28, color=color),
                        bgcolor=f"{color}15",
                        width=50,
                        height=50,
                        border_radius=25,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(str(value), size=22,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(title, size=12, color=TEXT_SECONDARY),
                    ], spacing=0),
                ], spacing=15),
                padding=15,
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

    def _get_leads(self):
        """Get all leads with search and filter"""
        session = self._get_db()
        try:
            query = session.query(CRMLead).order_by(CRMLead.created_at.desc())

            # Apply search filter
            if self.search_query:
                search = f"%{self.search_query}%"
                query = query.filter(
                    or_(
                        CRMLead.name.ilike(search),
                        CRMLead.email.ilike(search),
                        CRMLead.company.ilike(search),
                        CRMLead.phone.ilike(search)
                    )
                )

            # Apply status filter
            if self.status_filter and self.status_filter != "all":
                query = query.filter(CRMLead.status == self.status_filter)

            leads = query.all()
            return leads
        except Exception as e:
            print(f"Error getting leads: {e}")
            return []
        finally:
            session.close()

    def _get_contacts(self):
        """Get all contacts with search and filter"""
        session = self._get_db()
        try:
            query = session.query(CRMCustomer).order_by(
                CRMCustomer.created_at.desc())

            # Apply search filter
            if self.contact_search_query:
                search = f"%{self.contact_search_query}%"
                query = query.filter(
                    or_(
                        CRMCustomer.name.ilike(search),
                        CRMCustomer.email.ilike(search),
                        CRMCustomer.company.ilike(search),
                        CRMCustomer.phone.ilike(search)
                    )
                )

            # Apply category filter
            if self.contact_category_filter and self.contact_category_filter != "all":
                query = query.filter(CRMCustomer.category ==
                                     self.contact_category_filter)

            contacts = query.all()
            return contacts
        except Exception as e:
            print(f"Error getting contacts: {e}")
            return []
        finally:
            session.close()

    def _get_deals(self):
        """Get all deals"""
        session = self._get_db()
        try:
            deals = session.query(CRMDeal).order_by(
                CRMDeal.created_at.desc()).all()
            return deals
        except Exception as e:
            print(f"Error getting deals: {e}")
            return []
        finally:
            session.close()

    def _get_activities(self):
        """Get all activities"""
        session = self._get_db()
        try:
            activities = session.query(CRMActivity).order_by(
                CRMActivity.due_date.desc()).limit(50).all()
            return activities
        except Exception as e:
            print(f"Error getting activities: {e}")
            return []
        finally:
            session.close()

# ============ DIALOGS ============

    def _show_add_dialog(self, e=None):
        """Show add dialog based on current tab"""
        try:
            if self.current_tab == "leads" or self.current_tab == "dashboard":
                self._show_add_lead_dialog()
            elif self.current_tab == "contacts":
                self._show_add_contact_dialog()
            elif self.current_tab == "deals":
                self._show_add_deal_dialog()
            elif self.current_tab == "activities":
                self._show_add_activity_dialog()
            elif self.current_tab == "quotes":
                self._show_add_quote_dialog()
            elif self.current_tab == "products":
                self._show_add_product_dialog()
            elif self.current_tab == "calendar":
                self._show_add_activity_dialog()
            elif self.current_tab == "reports":
                # Reports tab - show a menu to choose what to add
                self._show_reports_add_menu()
            else:
                # Default to activity dialog
                self._show_add_activity_dialog()
        except Exception as ex:
            print(f"Error in _show_add_dialog: {ex}")
            import traceback
            traceback.print_exc()

    def _show_add_lead_dialog(self, e=None):
        """Show add lead dialog"""
        name_field = ft.TextField(
            label="Name *", hint_text="Enter lead name", border_color=PRIMARY)
        email_field = ft.TextField(
            label="Email", hint_text="Enter email address", border_color=PRIMARY)
        phone_field = ft.TextField(
            label="Phone", hint_text="Enter phone number", border_color=PRIMARY)
        company_field = ft.TextField(
            label="Company", hint_text="Enter company name", border_color=PRIMARY)
        designation_field = ft.TextField(
            label="Designation", hint_text="Enter designation", border_color=PRIMARY)
        source_dropdown = ft.Dropdown(
            label="Source",
            options=[
                ft.dropdown.Option("website", "Website"),
                ft.dropdown.Option("referral", "Referral"),
                ft.dropdown.Option("social_media", "Social Media"),
                ft.dropdown.Option("cold_call", "Cold Call"),
                ft.dropdown.Option("trade_show", "Trade Show"),
                ft.dropdown.Option("advertisement", "Advertisement"),
                ft.dropdown.Option("other", "Other"),
            ],
            value="website",
            border_color=PRIMARY,
        )
        priority_dropdown = ft.Dropdown(
            label="Priority",
            options=[
                ft.dropdown.Option("low", "Low"),
                ft.dropdown.Option("medium", "Medium"),
                ft.dropdown.Option("high", "High"),
                ft.dropdown.Option("urgent", "Urgent"),
            ],
            value="medium",
            border_color=PRIMARY,
        )
        expected_value_field = ft.TextField(
            label="Expected Value", hint_text="Enter expected value", value="0", border_color=PRIMARY)

        def save_lead(e):
            if not name_field.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Name is required")))
                return

            session = self._get_db()
            try:
                _, user_id = self._get_user_info()

                lead = CRMLead(
                    name=name_field.value,
                    email=email_field.value,
                    phone=phone_field.value,
                    company=company_field.value,
                    designation=designation_field.value,
                    source=source_dropdown.value,
                    priority=priority_dropdown.value,
                    expected_value=float(expected_value_field.value or 0),
                    status="new",
                    created_by_id=user_id,
                )
                session.add(lead)
                session.commit()
                self._show_snackbar(ft.SnackBar(content=ft.Text(
                    "Lead added successfully"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Add New Lead"),
            content=ft.Container(
                content=ft.Column([
                    name_field, email_field, phone_field, company_field,
                    designation_field, source_dropdown, priority_dropdown, expected_value_field
                ], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Save", on_click=save_lead,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _show_add_contact_dialog(self, e=None):
        """Show add contact dialog"""
        name_field = ft.TextField(
            label="Name *", hint_text="Enter contact name", border_color=PRIMARY)
        email_field = ft.TextField(
            label="Email", hint_text="Enter email address", border_color=PRIMARY)
        phone_field = ft.TextField(
            label="Phone", hint_text="Enter phone number", border_color=PRIMARY)
        company_field = ft.TextField(
            label="Company", hint_text="Enter company name", border_color=PRIMARY)
        designation_field = ft.TextField(
            label="Designation", hint_text="Enter designation", border_color=PRIMARY)
        category_dropdown = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("customer", "Customer"),
                ft.dropdown.Option("prospect", "Prospect"),
                ft.dropdown.Option("partner", "Partner"),
                ft.dropdown.Option("vendor", "Vendor"),
                ft.dropdown.Option("other", "Other"),
            ],
            value="prospect",
            border_color=PRIMARY,
        )

        def save_contact(e):
            if not name_field.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Name is required")))
                return

            session = self._get_db()
            try:
                _, user_id = self._get_user_info()

                contact = CRMCustomer(
                    name=name_field.value,
                    email=email_field.value,
                    phone=phone_field.value,
                    company=company_field.value,
                    designation=designation_field.value,
                    category=category_dropdown.value,
                    created_by_id=user_id,
                )
                session.add(contact)
                session.commit()
                self._show_snackbar(ft.SnackBar(content=ft.Text(
                    "Contact added successfully"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Add New Contact"),
            content=ft.Container(
                content=ft.Column([
                    name_field, email_field, phone_field, company_field,
                    designation_field, category_dropdown
                ], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Save", on_click=save_contact,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _show_add_deal_dialog(self, e=None):
        """Show add deal dialog"""
        # Get contacts first before using them
        contacts = self._get_contacts()

        title_field = ft.TextField(
            label="Deal Title *", hint_text="Enter deal title", border_color=PRIMARY)
        customer_dropdown = ft.Dropdown(
            label="Customer *",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in contacts] if contacts else [
                ft.dropdown.Option("", "No contacts")],
            border_color=PRIMARY,
        )
        value_field = ft.TextField(
            label="Value *", hint_text="Enter deal value", value="0", border_color=PRIMARY)
        stage_dropdown = ft.Dropdown(
            label="Stage",
            options=[
                ft.dropdown.Option("qualification", "Qualification"),
                ft.dropdown.Option("meeting_scheduled", "Meeting Scheduled"),
                ft.dropdown.Option("proposal_sent", "Proposal Sent"),
                ft.dropdown.Option("negotiation", "Negotiation"),
                ft.dropdown.Option("closed_won", "Closed Won"),
                ft.dropdown.Option("closed_lost", "Closed Lost"),
            ],
            value="qualification",
            border_color=PRIMARY,
        )

        def save_deal(e):
            if not title_field.value or not customer_dropdown.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Title and Customer are required")))
                return

            session = self._get_db()
            try:
                _, user_id = self._get_user_info()

                deal = CRMDeal(
                    title=title_field.value,
                    customer_id=int(customer_dropdown.value),
                    value=float(value_field.value or 0),
                    stage=stage_dropdown.value,
                    created_by_id=user_id,
                )
                session.add(deal)
                session.commit()
                self._show_snackbar(ft.SnackBar(content=ft.Text(
                    "Deal added successfully"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Add New Deal"),
            content=ft.Container(
                content=ft.Column([
                    title_field, customer_dropdown, value_field, stage_dropdown
                ], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Save", on_click=save_deal,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _show_add_activity_dialog(self):
        """Show add activity dialog"""
        title_field = ft.TextField(
            label="Title *", hint_text="Enter activity title", border_color=PRIMARY)
        activity_type_dropdown = ft.Dropdown(
            label="Activity Type",
            options=[
                ft.dropdown.Option("call", "Call"),
                ft.dropdown.Option("meeting", "Meeting"),
                ft.dropdown.Option("task", "Task"),
                ft.dropdown.Option("email", "Email"),
                ft.dropdown.Option("note", "Note"),
            ],
            value="task",
            border_color=PRIMARY,
        )
        description_field = ft.TextField(
            label="Description", hint_text="Enter description", multiline=True, min_lines=3, border_color=PRIMARY)

        def save_activity(e):
            if not title_field.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Title is required")))
                return

            session = self._get_db()
            try:
                _, user_id = self._get_user_info()

                activity = CRMActivity(
                    title=title_field.value,
                    activity_type=activity_type_dropdown.value,
                    description=description_field.value,
                    created_by_id=user_id,
                    due_date=datetime.utcnow(),
                )
                session.add(activity)
                session.commit()
                self._show_snackbar(ft.SnackBar(content=ft.Text(
                    "Activity added successfully"), bgcolor=SUCCESS))
                self._page.close(dialog)
                self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Add New Activity"),
            content=ft.Container(
                content=ft.Column([
                    title_field, activity_type_dropdown, description_field
                ], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Save", on_click=save_activity,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _show_reports_add_menu(self):
        """Show a menu dialog to choose what to add from Reports tab"""
        def close_dialog(e):
            self._page.close(dialog)
            self._page.update()

        def add_lead(e):
            self._page.close(dialog)
            self._page.update()
            self._switch_tab("leads")
            self._show_add_lead_dialog()

        def add_contact(e):
            self._page.close(dialog)
            self._page.update()
            self._switch_tab("contacts")
            self._show_add_contact_dialog()

        def add_deal(e):
            self._page.close(dialog)
            self._page.update()
            self._switch_tab("deals")
            self._show_add_deal_dialog()

        def add_activity(e):
            self._page.close(dialog)
            self._page.update()
            self._switch_tab("activities")
            self._show_add_activity_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("Add New"),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PERSON_ADD, color=PRIMARY),
                            ft.Text("Add Lead", size=14),
                        ], spacing=10),
                        padding=15,
                        on_click=add_lead,
                        ink=True,
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CONTACT_PHONE, color=INFO),
                            ft.Text("Add Contact", size=14),
                        ], spacing=10),
                        padding=15,
                        on_click=add_contact,
                        ink=True,
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.BUSINESS_CENTER, color=SUCCESS),
                            ft.Text("Add Deal", size=14),
                        ], spacing=10),
                        padding=15,
                        on_click=add_deal,
                        ink=True,
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.EVENT, color=WARNING),
                            ft.Text("Add Activity", size=14),
                        ], spacing=10),
                        padding=15,
                        on_click=add_activity,
                        ink=True,
                    ),
                ], spacing=0),
                width=250,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    # ============ CRUD OPERATIONS ============

    def _edit_lead(self, lead):
        """Edit lead"""
        # Pre-fill dialog
        name_field = ft.TextField(
            label="Name *", value=lead.name or "", border_color=PRIMARY)
        email_field = ft.TextField(
            label="Email", value=lead.email or "", border_color=PRIMARY)
        phone_field = ft.TextField(
            label="Phone", value=lead.phone or "", border_color=PRIMARY)
        company_field = ft.TextField(
            label="Company", value=lead.company or "", border_color=PRIMARY)
        status_dropdown = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("new", "New"),
                ft.dropdown.Option("contacted", "Contacted"),
                ft.dropdown.Option("qualified", "Qualified"),
                ft.dropdown.Option("proposal", "Proposal"),
                ft.dropdown.Option("negotiation", "Negotiation"),
                ft.dropdown.Option("won", "Won"),
                ft.dropdown.Option("lost", "Lost"),
            ],
            value=lead.status or "new",
            border_color=PRIMARY,
        )
        value_field = ft.TextField(label="Value", value=str(
            lead.expected_value or 0), border_color=PRIMARY)

        def update_lead(e):
            if not name_field.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Name is required")))
                return

            session = self._get_db()
            try:
                lead_obj = session.query(CRMLead).get(lead.id)
                if lead_obj:
                    lead_obj.name = name_field.value
                    lead_obj.email = email_field.value
                    lead_obj.phone = phone_field.value
                    lead_obj.company = company_field.value
                    lead_obj.status = status_dropdown.value
                    lead_obj.expected_value = float(value_field.value or 0)
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Lead updated successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Lead"),
            content=ft.Container(
                content=ft.Column([name_field, email_field, phone_field, company_field,
                                  status_dropdown, value_field], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Update", on_click=update_lead,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _delete_lead(self, lead):
        """Delete lead"""
        def confirm_delete(e):
            session = self._get_db()
            try:
                lead_obj = session.query(CRMLead).get(lead.id)
                if lead_obj:
                    session.delete(lead_obj)
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Lead deleted successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Lead"),
            content=ft.Text(f"Are you sure you want to delete '{lead.name}'?"),
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

    def _edit_contact(self, contact):
        """Edit contact"""
        name_field = ft.TextField(
            label="Name *", value=contact.name or "", border_color=PRIMARY)
        email_field = ft.TextField(
            label="Email", value=contact.email or "", border_color=PRIMARY)
        phone_field = ft.TextField(
            label="Phone", value=contact.phone or "", border_color=PRIMARY)
        company_field = ft.TextField(
            label="Company", value=contact.company or "", border_color=PRIMARY)
        category_dropdown = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("customer", "Customer"),
                ft.dropdown.Option("prospect", "Prospect"),
                ft.dropdown.Option("partner", "Partner"),
                ft.dropdown.Option("vendor", "Vendor"),
            ],
            value=contact.category or "prospect",
            border_color=PRIMARY,
        )

        def update_contact(e):
            if not name_field.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Name is required")))
                return

            session = self._get_db()
            try:
                contact_obj = session.query(CRMCustomer).get(contact.id)
                if contact_obj:
                    contact_obj.name = name_field.value
                    contact_obj.email = email_field.value
                    contact_obj.phone = phone_field.value
                    contact_obj.company = company_field.value
                    contact_obj.category = category_dropdown.value
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Contact updated successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Contact"),
            content=ft.Container(
                content=ft.Column([name_field, email_field, phone_field,
                                  company_field, category_dropdown], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Update", on_click=update_contact,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _delete_contact(self, contact):
        """Delete contact"""
        def confirm_delete(e):
            session = self._get_db()
            try:
                contact_obj = session.query(CRMCustomer).get(contact.id)
                if contact_obj:
                    session.delete(contact_obj)
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Contact deleted successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Contact"),
            content=ft.Text(
                f"Are you sure you want to delete '{contact.name}'?"),
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

    def _edit_deal(self, deal):
        """Edit deal"""
        contacts = self._get_contacts()

        title_field = ft.TextField(
            label="Title *", value=deal.title or "", border_color=PRIMARY)
        customer_dropdown = ft.Dropdown(
            label="Customer",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in contacts],
            value=str(deal.customer_id) if deal.customer_id else None,
            border_color=PRIMARY,
        )
        value_field = ft.TextField(label="Value", value=str(
            deal.value or 0), border_color=PRIMARY)
        stage_dropdown = ft.Dropdown(
            label="Stage",
            options=[
                ft.dropdown.Option("qualification", "Qualification"),
                ft.dropdown.Option("meeting_scheduled", "Meeting Scheduled"),
                ft.dropdown.Option("proposal_sent", "Proposal Sent"),
                ft.dropdown.Option("negotiation", "Negotiation"),
                ft.dropdown.Option("closed_won", "Closed Won"),
                ft.dropdown.Option("closed_lost", "Closed Lost"),
            ],
            value=deal.stage or "qualification",
            border_color=PRIMARY,
        )

        def update_deal(e):
            if not title_field.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Title is required")))
                return

            session = self._get_db()
            try:
                deal_obj = session.query(CRMDeal).get(deal.id)
                if deal_obj:
                    deal_obj.title = title_field.value
                    deal_obj.customer_id = int(
                        customer_dropdown.value) if customer_dropdown.value else None
                    deal_obj.value = float(value_field.value or 0)
                    deal_obj.stage = stage_dropdown.value
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Deal updated successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Deal"),
            content=ft.Container(
                content=ft.Column([title_field, customer_dropdown,
                                  value_field, stage_dropdown], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Update", on_click=update_deal,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _edit_activity(self, activity):
        """Edit activity"""
        title_field = ft.TextField(
            label="Title *", value=activity.title or "", border_color=PRIMARY)
        description_field = ft.TextField(
            label="Description", value=activity.description or "", multiline=True, min_lines=3, border_color=PRIMARY)
        type_dropdown = ft.Dropdown(
            label="Type",
            options=[
                ft.dropdown.Option("call", "Call"),
                ft.dropdown.Option("meeting", "Meeting"),
                ft.dropdown.Option("task", "Task"),
                ft.dropdown.Option("email", "Email"),
                ft.dropdown.Option("note", "Note"),
            ],
            value=activity.activity_type or "task",
            border_color=PRIMARY,
        )

        def update_activity(e):
            if not title_field.value:
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text("Title is required")))
                return

            session = self._get_db()
            try:
                activity_obj = session.query(CRMActivity).get(activity.id)
                if activity_obj:
                    activity_obj.title = title_field.value
                    activity_obj.description = description_field.value
                    activity_obj.activity_type = type_dropdown.value
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Activity updated successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Activity"),
            content=ft.Container(
                content=ft.Column(
                    [title_field, type_dropdown, description_field], tight=True, spacing=12),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.FilledButton("Update", on_click=update_activity,
                                bgcolor=PRIMARY, color="WHITE"),
            ],
        )
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _delete_activity(self, activity):
        """Delete activity"""
        def confirm_delete(e):
            session = self._get_db()
            try:
                activity_obj = session.query(CRMActivity).get(activity.id)
                if activity_obj:
                    session.delete(activity_obj)
                    session.commit()
                    self._show_snackbar(ft.SnackBar(content=ft.Text(
                        "Activity deleted successfully"), bgcolor=SUCCESS))
                    self._page.close(dialog)
                    self.refresh()
            except Exception as ex:
                session.rollback()
                self._show_snackbar(ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
            finally:
                session.close()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Activity"),
            content=ft.Text(
                f"Are you sure you want to delete '{activity.title}'?"),
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

    def _toggle_activity_complete(self, activity):
        """Toggle activity completion"""
        session = self._get_db()
        try:
            activity_obj = session.query(CRMActivity).get(activity.id)
            if activity_obj:
                activity_obj.is_completed = not activity_obj.is_completed
                if activity_obj.is_completed:
                    activity_obj.completed_at = datetime.utcnow()
                session.commit()
                self.refresh()
        except Exception as ex:
            session.rollback()
            self._show_snackbar(ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
        finally:
            session.close()

    def _convert_lead(self, lead):
        """Convert lead to customer"""
        session = self._get_db()
        try:
            # Check if customer already exists
            existing = session.query(CRMCustomer).filter_by(
                email=lead.email).first()
            if existing:
                self._show_snackbar(ft.SnackBar(content=ft.Text(
                    "Customer with this email already exists!"), bgcolor=WARNING))
                return

            # Create customer from lead
            customer = CRMCustomer(
                name=lead.name,
                email=lead.email,
                phone=lead.phone,
                company=lead.company,
                designation=lead.designation,
                category="customer",
                source=lead.source,
            )
            session.add(customer)
            session.flush()

            # Update lead status
            lead.status = "won"
            lead.converted_to_customer_id = customer.id
            lead.converted_at = datetime.utcnow()

            session.commit()
            self._show_snackbar(ft.SnackBar(content=ft.Text(
                "Lead converted to customer successfully!"), bgcolor=SUCCESS))
            self.refresh()
        except Exception as ex:
            session.rollback()
            self._show_snackbar(ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"), bgcolor=ERROR))
        finally:
            session.close()

    def _go_back(self, e):
        """Navigate back to home screen"""
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)


def show_crm(page, user):
    """Helper function to show CRM"""
    page.clean()
    page.add(CRMScreen(page, user))
