"""
Vernika HRA - Organization Tree Screen
Visual hierarchical organization chart with proper connections and improved UI
"""

import flet as ft
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Employee, Department, Position, OrgHierarchy
from utils.ui_helpers import resolve_profile_photo_path
import os
from pathlib import Path
from sqlalchemy.orm import joinedload
import threading
import time


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
PURPLE = "#9C27B0"
ORANGE = "#FF9800"
TEAL = "#009688"

# Level colors
LEVEL_COLORS = {
    0: "#D32F2F",  # CEO - Red
    1: "#FF9800",   # Head - Orange
    2: "#2196F3",   # Manager - Blue
    3: "#9C27B0",   # Team Lead - Purple
    4: "#4CAF50",   # Employee - Green
    5: "#607D8B",   # Intern - Grey
}

LEVEL_LABELS = {
    0: "CEO",
    1: "Head",
    2: "Manager",
    3: "Team Lead",
    4: "Employee",
    5: "Intern",
}


def _safe_navigate_to_home(page, user=None):
    """Safely navigate to home screen"""
    try:
        from core.navigation import navigate_to_home
        navigate_to_home(page, user)
    except ImportError:
        # Fallback navigation
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


class OrganizationTreeScreen(ft.Container):
    """Organization Tree/Chart Display Screen with improved UI"""

    @staticmethod
    def create_connection_line(color=PRIMARY, height=25):
        """Create a vertical connection line"""
        return ft.Container(width=3, height=height, bgcolor=color)

    @staticmethod
    def create_company_card(total_employees):
        """Create company card - UNIVERSAL PARENT for ALL employees"""
        from config import SUPABASE_URL, SUPABASE_STORAGE_BUCKET

        if SUPABASE_URL and SUPABASE_STORAGE_BUCKET:
            logo_src = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/logo/Radhefoundation.jpeg"
        else:
            logo_src = "/assets/logo/Vernikalogo.png"

        logo_image = ft.Image(
            src=logo_src,
            width=70,
            height=70,
            fit=ft.BoxFit.COVER
        )
        return ft.Container(
            width=240,
            padding=16,
            bgcolor=SURFACE,
            border_radius=12,
            border=ft.border.all(4, PRIMARY),
            shadow=ft.BoxShadow(
                spread_radius=3, blur_radius=12, color="rgba(46,134,171,0.4)"),
            content=ft.Column([
                ft.Container(
                    content=logo_image,
                    width=70,
                    height=70,
                    border_radius=35,
                    alignment=ft.alignment.Alignment(0, 0)
                ),
                ft.Container(height=10),
                ft.Text("VERNIKA TECHNOLOGIES", size=15, weight=ft.FontWeight.BOLD,
                        color=PRIMARY, text_align=ft.TextAlign.CENTER),
                ft.Text("Organization", size=12, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.Divider(height=1),
                ft.Container(height=8),
                ft.Row([
                    ft.Icon(ft.Icons.PEOPLE_OUTLINE,
                            size=16, color=TEXT_SECONDARY),
                    ft.Text(f"{total_employees} Total Employees",
                            size=11, color=TEXT_SECONDARY)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        )

    @staticmethod
    def create_emp_card(emp_data, emp_level=5, is_root=False, children_map=None, collapsed_nodes=None):
        """
        Unified employee card with photo support and collapse functionality.
        """
        emp = emp_data['employee'] if isinstance(emp_data, dict) else emp_data
        h = emp_data.get('hierarchy') if isinstance(emp_data, dict) else None

        color = LEVEL_COLORS.get(emp_level, "#4CAF50")
        if is_root:
            color = "#D32F2F"

        position_title = getattr(
            getattr(emp, 'position', None), 'title', None) or "Employee"
        department_name = getattr(
            getattr(emp, 'department', None), 'name', None) or ""

        first_name = emp.first_name or ""
        last_name = emp.last_name or ""
        initials = f"{first_name[0:1]}{last_name[0:1]}".upper()
        full_name = f"{first_name} {last_name}".strip()
        display_name = full_name[:20] + \
            "..." if len(full_name) > 20 else full_name

        # Profile photo - web-safe paths, centered
        profile_photo_url = getattr(emp, 'profile_photo', None)
        profile_photo_path = resolve_profile_photo_path(
            profile_photo_url or "")
        photo_src = profile_photo_path or "/assets/profile_photos/shashank.jpg"

        avatar_img = ft.Image(src=photo_src, width=52,
                              height=52, fit=ft.BoxFit.COVER)

        avatar_content = ft.Container(
            width=52,
            height=52,
            border_radius=26,
            content=avatar_img,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ) if photo_src else ft.Container(
            width=52,
            height=52,
            bgcolor=color,
            border_radius=26,
            content=ft.Text(
                initials if initials else "?", size=18, color="WHITE", weight=ft.FontWeight.BOLD
            ),
            alignment=ft.alignment.Alignment(0, 0),
        )

        # Check children for collapse button
        has_children = children_map and hasattr(emp, 'id') and emp.id in children_map and len(
            children_map[emp.id]) > 0 if children_map else False
        collapse_btn = ft.Container(width=0, height=0)
        if has_children and collapsed_nodes:
            is_collapsed = emp.id in collapsed_nodes
            collapse_btn = ft.IconButton(
                icon=ft.Icons.EXPAND_MORE if is_collapsed else ft.Icons.EXPAND_LESS,
                icon_size=16,
                tooltip="Toggle subordinates",
                style=ft.ButtonStyle(bgcolor="transparent", padding=0),
            )

        return ft.Container(
            width=200,
            padding=12,
            bgcolor=SURFACE,
            border_radius=12,
            border=ft.border.all(2, color),
            shadow=ft.BoxShadow(
                spread_radius=2, blur_radius=8, color=color + "30"),

            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=avatar_content,
                        alignment=ft.alignment.Alignment(0, 0),
                        expand=True,
                    ),
                    collapse_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.Text(display_name, size=12, weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER),
                ft.Text(
                    position_title[:25] +
                    "..." if len(position_title) > 25 else position_title,
                    size=10,
                    color=TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=5),
                ft.Divider(height=1),
                ft.Container(height=5),
                ft.Container(
                    content=ft.Text(
                        department_name[:18] if department_name else "No Dept", size=9, color="WHITE"),

                    bgcolor=PRIMARY,
                    padding=ft.padding.symmetric(horizontal=10, vertical=3),
                    border_radius=8,
                ) if department_name else ft.Container(height=0),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
        )

    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self._nav_rail_visible = True
        self._refresh_interval = 30  # seconds
        self._last_refresh = time.time()

        # Get user ID
        self.user_id = None
        if isinstance(user, dict):
            self.user_id = user.get('id')

        # New state variables for improved UI
        self._search_query = ""
        self._department_view = False  # Toggle between hierarchy and department view
        self._collapsed_nodes = set()  # Track collapsed branch nodes
        self._all_employees = []  # Cache all employees
        self._all_hierarchy = {}  # Cache hierarchy data

        # Build content
        self.content = self._build_content()

    def _build_content(self):
        """Build the organization tree content"""
        # Check if user is admin
        is_admin = self._is_admin()

        # Navigation button - goes back to home/dashboard
        def go_back_to_home(e):
            _safe_navigate_to_home(self._page, self.user)

        # Build org tree in scrollable container
        tree_view = self._build_org_tree()

        # Main layout - full screen, adaptive
        return ft.Container(
            expand=True,
            content=ft.Column([
                # Header
                self._create_header(is_admin),
                # Toolbar with search
                self._create_toolbar(),
                # Content area with tree - expand to fill available space
                ft.Container(
                    padding=20,
                    content=tree_view,
                    expand=True,
                )
            ], expand=True),
        )

    def _create_toolbar(self):
        """Create toolbar with search field"""
        # Search field for filtering employees - moved out of header
        self.search_field = ft.TextField(
            hint_text="Search employees...",
            prefix_icon=ft.Icons.SEARCH,
            width=300,
            on_change=self._on_search_change,
            border_color=PRIMARY,
            focused_border_color=PRIMARY,
            content_padding=10,
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=SURFACE,
            border=ft.border.all(1, "#E0E0E0"),
            content=ft.Row([
                self.search_field,
                # Clear search button
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip="Clear Search",
                    on_click=self._clear_search,
                ),
                ft.Container(expand=True),
            ])
        )

    def _create_header(self, is_admin):
        """Create header with navigation, company name, welcome text, and logout"""
        # Back button to navigate to home
        back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="Back to Dashboard",
            on_click=lambda e: _safe_navigate_to_home(self._page, self.user),
            icon_color="WHITE"
        )

        # View toggle button (Hierarchy vs Department)
        view_toggle = ft.Container(
            content=ft.SegmentedButton(
                segments=[
                    ft.Segment(
                        value="hierarchy",
                        label=ft.Text("Hierarchy", size=12),
                    ),
                    ft.Segment(
                        value="department",
                        label=ft.Text("Department", size=12),
                    ),
                ],
                selected=["hierarchy"],
                on_change=self._on_view_toggle,
            ),
            bgcolor="white12",
            border_radius=8,
            padding=3,
        )

        # View-only message for non-admin
        view_only_badge = ft.Container(
            content=ft.Text("View Only", size=11, color="WHITE"),
            bgcolor="#FF5722",
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        ) if not is_admin else ft.Container()

        return ft.Container(
            content=ft.Row([
                # Left section - Back button and title
                ft.Container(
                    content=ft.Row([
                        back_btn,
                        ft.Container(width=5),
                        ft.Icon(ft.Icons.ACCOUNT_TREE, color="WHITE", size=28),
                        ft.Container(width=10),
                        ft.Text("Organization Tree", size=18,
                                color="WHITE", weight=ft.FontWeight.BOLD),
                    ], spacing=0),
                ),
                # Center section - View toggle
                ft.Container(
                    content=ft.Row([
                        view_toggle,
                        ft.Container(width=10),
                        view_only_badge,
                    ], spacing=0),
                    expand=False,
                ),
                # Right section - Actions and user info
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Refresh",
                            on_click=lambda e: self._refresh(),
                            icon_color="WHITE"
                        ),
                        ft.ElevatedButton(
                            "Edit",
                            icon=ft.Icons.EDIT,
                            on_click=self._show_edit_hierarchy if is_admin else None,
                            style=ft.ButtonStyle(
                                bgcolor="#FF9800",
                                color="WHITE"
                            ),
                            visible=is_admin,
                            height=32,
                        ),
                        ft.Container(width=5),
                        ft.Text(
                            f"Welcome, {self.user.get('username', 'User') if isinstance(self.user, dict) else 'User'}",
                            size=14,
                            color="WHITE"
                        ),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            tooltip="Logout",
                            on_click=self._handle_logout,
                            icon_color="WHITE"
                        ),
                    ], spacing=5),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            bgcolor=PRIMARY,
        )

    def _on_search_change(self, e):
        """Handle search query change"""
        # Get the search value safely
        search_value = e.control.value if e.control else ""
        self._search_query = search_value.strip().lower() if search_value else ""
        self._refresh_tree()

    def _clear_search(self, e):
        """Clear search and show all employees"""
        self._search_query = ""
        if self.search_field:
            self.search_field.value = ""
        self._refresh_tree()

    def _on_view_toggle(self, e):
        """Handle view toggle change"""
        selected = e.control.selected
        if isinstance(selected, list) and selected:
            self._department_view = selected[0] == "department"
        elif isinstance(selected, str):
            self._department_view = selected == "department"
        self._refresh_tree()

    def _refresh_tree(self):
        """Refresh the tree view only (without rebuilding entire screen)"""
        # Rebuild tree view
        tree_view = self._build_org_tree()
        # Update the tree container - layout is now Column with [Header, Toolbar, Content]
        self.content.content.controls[2].content = tree_view
        self._page.update()

    def _toggle_collapse(self, emp_id):
        """Toggle collapse state for a node"""
        if emp_id in self._collapsed_nodes:
            self._collapsed_nodes.discard(emp_id)
        else:
            self._collapsed_nodes.add(emp_id)
        self._refresh_tree()

    def _build_department_view(self, employees, hierarchy):
        """Build department-based view of employees"""
        # Group employees by department
        departments = {}
        no_dept = []

        for emp in employees:
            dept = getattr(emp, 'department', None)
            if dept and dept.name:
                if dept.name not in departments:
                    departments[dept.name] = {
                        'department': dept,
                        'employees': []
                    }
                departments[dept.name]['employees'].append(emp)
            else:
                no_dept.append(emp)

        if not departments and not no_dept:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SUPERVISED_USER_CIRCLE_OUTLINED,
                            size=64, color="#BDBDBD"),
                    ft.Text("No employees found.", size=14, color="#757575"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        # Create department cards
        department_colors = [
            "#2E86AB", "#4CAF50", "#9C27B0", "#FF9800", "#2196F3",
            "#E91E63", "#00BCD4", "#795548", "#607D8B", "#F44336"
        ]

        dept_cards = []
        for idx, (dept_name, dept_data) in enumerate(departments.items()):
            dept = dept_data['department']
            dept_employees = dept_data['employees']
            color = department_colors[idx % len(department_colors)]

            # Create employee cards for this department
            emp_cards = []
            for emp in dept_employees[:8]:  # Max 8 per row
                first_name = emp.first_name or ""
                last_name = emp.last_name or ""
                initials = f"{first_name[0:1]}{last_name[0:1]}".upper()
                full_name = f"{first_name} {last_name}".strip()
                display_name = full_name[:18] + \
                    "..." if len(full_name) > 18 else full_name
                position_title = getattr(
                    getattr(emp, 'position', None), 'title', None) or "Employee"

                emp_card = ft.Container(
                    width=150,
                    padding=8,
                    bgcolor=SURFACE,
                    border_radius=8,
                    border=ft.border.all(2, color),
                    content=ft.Column([
                        ft.Container(
                            width=36, height=36,
                            bgcolor=color,
                            border_radius=18,
                            content=ft.Text(
                                initials, size=11, color="WHITE", weight=ft.FontWeight.BOLD),
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Text(display_name, size=9, weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(
                            position_title[:20], size=7, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                )
                emp_cards.append(emp_card)

            # Department head (if available)
            head_name = ""
            if dept.head_id:
                for emp in dept_employees:
                    if emp.id == dept.head_id:
                        head_name = f"{emp.first_name or ''} {emp.last_name or ''}".strip(
                        )
                        break

            dept_card = ft.Container(
                padding=15,
                bgcolor=SURFACE,
                border_radius=12,
                border=ft.border.all(1, color),
                content=ft.Column([
                    # Department header
                    ft.Container(
                        bgcolor=color + "15",
                        padding=10,
                        border_radius=8,
                        content=ft.Row([
                            ft.Container(
                                width=40, height=40,
                                bgcolor=color,
                                border_radius=20,
                                content=ft.Icon(
                                    ft.Icons.SUPERVISED_USER_CIRCLE, color="WHITE", size=22),
                                alignment=ft.alignment.Alignment(0, 0),
                            ),
                            ft.Column([
                                ft.Text(dept_name, size=14,
                                        weight=ft.FontWeight.BOLD, color=color),
                                ft.Text(f"{len(dept_employees)} employees" + (f" | Head: {head_name}" if head_name else ""),
                                        size=10, color=TEXT_SECONDARY),
                            ], spacing=0),
                        ], spacing=10),
                    ),
                    ft.Container(height=10),
                    # Employee grid
                    ft.Row(emp_cards, wrap=True, spacing=8,
                           alignment=ft.MainAxisAlignment.START),
                    # Show more indicator if needed
                    ft.Container(
                        content=ft.Text(
                            f"+{len(dept_employees) - 8} more employees", size=10, color=color),
                        visible=len(dept_employees) > 8,
                    ) if len(dept_employees) > 8 else ft.Container(),
                ], spacing=0),
            )
            dept_cards.append(dept_card)

        # Add "No Department" section if any
        if no_dept:
            no_dept_cards = []
            for emp in no_dept[:8]:
                first_name = emp.first_name or ""
                last_name = emp.last_name or ""
                initials = f"{first_name[0:1]}{last_name[0:1]}".upper()
                full_name = f"{first_name} {last_name}".strip()
                display_name = full_name[:18] + \
                    "..." if len(full_name) > 18 else full_name
                position_title = getattr(
                    getattr(emp, 'position', None), 'title', None) or "Employee"

                emp_card = ft.Container(
                    width=150,
                    padding=8,
                    bgcolor=SURFACE,
                    border_radius=8,
                    border=ft.border.all(2, "#9E9E9E"),
                    content=ft.Column([
                        ft.Container(
                            width=36, height=36,
                            bgcolor="#9E9E9E",
                            border_radius=18,
                            content=ft.Text(
                                initials, size=11, color="WHITE", weight=ft.FontWeight.BOLD),
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Text(display_name, size=9, weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(
                            position_title[:20], size=7, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                )
                no_dept_cards.append(emp_card)

            no_dept_card = ft.Container(
                padding=15,
                bgcolor=SURFACE,
                border_radius=12,
                border=ft.border.all(1, "#9E9E9E"),
                content=ft.Column([
                    ft.Container(
                        bgcolor="#9E9E9E15",
                        padding=10,
                        border_radius=8,
                        content=ft.Row([
                            ft.Container(
                                width=40, height=40,
                                bgcolor="#9E9E9E",
                                border_radius=20,
                                content=ft.Icon(
                                    ft.Icons.PERSON_OUTLINE, color="WHITE", size=22),
                                alignment=ft.alignment.Alignment(0, 0),
                            ),
                            ft.Column([
                                ft.Text("No Department", size=14,
                                        weight=ft.FontWeight.BOLD, color="#9E9E9E"),
                                ft.Text(f"{len(no_dept)} employees",
                                        size=10, color=TEXT_SECONDARY),
                            ], spacing=0),
                        ], spacing=10),
                    ),
                    ft.Container(height=10),
                    ft.Row(no_dept_cards, wrap=True, spacing=8,
                           alignment=ft.MainAxisAlignment.START),
                ], spacing=0),
            )
            dept_cards.append(no_dept_card)

        # Create view title
        view_title = ft.Container(
            padding=15,
            bgcolor=SURFACE,
            border_radius=8,
            margin=ft.margin.only(bottom=10),
            content=ft.Row([
                ft.Icon(ft.Icons.SUPERVISED_USER_CIRCLE,
                        color=PRIMARY, size=24),
                ft.Text("Department View", size=16,
                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Text(f" - {len(departments)} departments, {len(employees)} employees",
                        size=12, color=TEXT_SECONDARY),
            ], spacing=10),
        )

        return ft.Column([
            view_title,
            ft.Container(
                content=ft.ListView(dept_cards, spacing=15,
                                    padding=20, expand=True),
                expand=True
            ),
        ], expand=True)

    def _handle_logout(self, e):
        """Handle logout"""
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))

    def _is_admin(self):
        """Check if current user is admin"""
        if isinstance(self.user, dict):
            role = self.user.get('role', '').lower()
            return role == 'admin'
        return False

    def _get_all_employees(self):
        """Get all employees for org tree"""
        db = get_db_session()
        try:
            employees = db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            ).filter(Employee.is_active == True).all()
            return employees
        except Exception as e:
            print(f"Error loading employees: {e}")
            return []
        finally:
            db.close()

    def _get_org_hierarchy(self):
        """Get organization hierarchy data"""
        db = get_db_session()
        try:
            hierarchy = db.query(OrgHierarchy).all()
            return {h.employee_id: h for h in hierarchy}
        finally:
            db.close()

    def _build_hierarchy_tree(self, employees, hierarchy):
        """Build proper hierarchy tree recursively from reports_to_id"""
        # Build children map: manager_id -> list of direct reports
        children_map = {}
        all_employee_ids = {emp.id for emp in employees}
        has_hierarchy = {}

        for emp in employees:
            h = hierarchy.get(emp.id)
            has_hierarchy[emp.id] = h is not None

            if h and h.reports_to_id and h.reports_to_id in all_employee_ids:
                manager_id = h.reports_to_id
                if manager_id not in children_map:
                    children_map[manager_id] = []
                children_map[manager_id].append({
                    'employee': emp,
                    'hierarchy': h
                })

        # Find true roots
        incoming_reports = set()
        for manager_id in children_map:
            incoming_reports.add(manager_id)

        roots = []
        orphans = []
        for emp in employees:
            h = hierarchy.get(emp.id)
            is_manager = emp.id in children_map
            has_incoming = emp.id in incoming_reports

            # Root: has hierarchy record OR is manager, but no incoming reports
            if (h or is_manager) and not has_incoming:
                roots.append({
                    'employee': emp,
                    'hierarchy': h,
                    'children': children_map.get(emp.id, [])
                })
            elif not h:  # No hierarchy record → orphan
                orphans.append({
                    'employee': emp,
                    'hierarchy': None
                })

        return {
            'roots': roots,
            'orphans': orphans,
            'children_map': children_map,
            'has_hierarchy': has_hierarchy
        }

    def _build_org_tree(self):
        """Build the organization tree visualization with proper connection lines"""
        # Get employees and hierarchy data
        employees = self._get_all_employees()
        hierarchy = self._get_org_hierarchy()

        # Cache data for later use
        self._all_employees = employees
        self._all_hierarchy = hierarchy

        # Apply search filter if query exists
        if self._search_query:
            search_lower = self._search_query.lower()
            filtered_employees = []
            for emp in employees:
                full_name = f"{emp.first_name or ''} {emp.last_name or ''}".lower()
                dept_name = getattr(
                    getattr(emp, 'department', None), 'name', '') or ''
                pos_title = getattr(
                    getattr(emp, 'position', None), 'title', '') or ''
                code = getattr(emp, 'employee_code', '') or ''

                if (search_lower in full_name or search_lower in dept_name.lower() or
                        search_lower in pos_title.lower() or search_lower in code.lower()):
                    filtered_employees.append(emp)
            employees = filtered_employees

        # If department view enabled, show department-based view
        if self._department_view:
            return self._build_department_view(employees, hierarchy)

        if not employees:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED,
                            size=64, color="#BDBDBD"),
                    ft.Text("No employees found.", size=14, color="#757575"),
                    ft.Text("Try adjusting your search query",
                            size=12, color="#9E9E9E"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        # Build hierarchy tree structure
        tree_structure = self._build_hierarchy_tree(employees, hierarchy)
        root_employees = tree_structure.get('roots', [])
        children_map = tree_structure.get('children_map', {})

        # Build tree nodes
        tree_nodes = []
        for root_node in root_employees:
            tree_nodes.append(self._build_tree_node_recursive(root_node, 0))

        # Company card at top
        company_card = self.create_company_card(len(employees))

        # Connect company to roots
        if tree_nodes:
            if len(tree_nodes) == 1:
                tree_display = ft.Column([
                    company_card,
                    self.create_connection_line(height=20),
                    tree_nodes[0]
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            else:
                root_spacing = 40
                total_width = len(tree_nodes) * 160 + \
                    (len(tree_nodes) - 1) * root_spacing
                main_horizontal_bar = ft.Container(
                    width=total_width, height=2, bgcolor=PRIMARY)

                root_columns = []
                for tree_node in tree_nodes:
                    root_columns.append(ft.Column([
                        self.create_connection_line(height=15),
                        tree_node
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0))

                roots_row = ft.Row(
                    root_columns, spacing=root_spacing, alignment=ft.MainAxisAlignment.CENTER)
                tree_display = ft.Column([
                    company_card,
                    self.create_connection_line(height=20),
                    main_horizontal_bar,
                    roots_row
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        else:
            tree_display = company_card

        # Handle orphan employees
        orphan_employees = tree_structure.get('orphans', [])
        if orphan_employees:
            orphan_cards = [self.create_emp_card(emp_data, 5, True, children_map, self._collapsed_nodes)
                            for emp_data in orphan_employees[:10]]

            # Distinct unassigned section with better hierarchy
            unassigned_section = ft.Container(
                padding=25,
                bgcolor="#FFF3E0",
                border_radius=16,
                border=ft.border.all(3, "#FF9800"),
                shadow=ft.BoxShadow(
                    spread_radius=4, blur_radius=16, color="rgba(255,152,0,0.4)"),
                content=ft.Column([
                    ft.Container(
                        padding=15,
                        bgcolor="#FF9800",
                        border_radius=12,
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED,
                                    size=32, color="WHITE"),
                            ft.Container(width=12),
                            ft.Column([
                                ft.Text("Unassigned Employees", size=16,
                                        weight=ft.FontWeight.BOLD, color="WHITE"),
                                ft.Text(
                                    f"{len(orphan_employees)} employees without hierarchy", size=12, color="WHITE70"),
                            ])
                        ], alignment=ft.MainAxisAlignment.START),
                    ),
                    ft.Container(height=16),
                    ft.Row(
                        orphan_cards[:6],  # Show top 6
                        spacing=16,
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True
                    ),
                    ft.Container(height=8),
                    ft.Text(f"+{len(orphan_employees)-6} more..." if len(orphan_employees) > 6 else "",
                            size=12, color=ORANGE, weight=ft.FontWeight.W_500),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            )

            tree_display = ft.Column([
                tree_display,
                ft.Container(height=40),
                unassigned_section
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

        # Legend
        legend = ft.Container(
            padding=12,
            bgcolor=SURFACE,
            border_radius=8,
            margin=ft.margin.only(bottom=10),
            content=ft.Row([
                *[ft.Container(content=ft.Row([ft.Container(width=10, height=10, bgcolor=c, border_radius=2),
                                              ft.Text(label, size=9)], spacing=3)) for c, label in [
                    ("#D32F2F", "CEO"), ("#FF9800",
                                         "Head"), ("#2196F3", "Manager"),
                    ("#9C27B0", "Team Lead"), ("#4CAF50", "Employee"), ("#607D8B", "Intern")]]
            ], spacing=20)
        )

        # Stats
        orphan_count = len(orphan_employees)
        hierarchy_count = len(
            [emp for emp in employees if hierarchy.get(emp.id)])
        info_text = ft.Container(
            padding=10,
            content=ft.Text(f"Total: {len(employees)} | Hierarchy: {hierarchy_count} | Unassigned: {orphan_count} | Roots: {len(root_employees)}",
                            size=11, color=TEXT_SECONDARY)
        )

        return ft.Column([
            legend,
            info_text,
            ft.Container(content=ft.ListView(
                [tree_display], spacing=20, padding=20, expand=True), expand=True)
        ], expand=True)

    def _build_tree_node_recursive(self, node_data, level=0, visited=None, parent_color=None):
        if visited is None:
            visited = set()

        if isinstance(node_data, dict) and 'employee' in node_data:
            emp = node_data['employee']
            h = node_data.get('hierarchy')
            children = node_data.get('children', [])
        else:
            emp = node_data
            h = None
            children = []

        emp_id = emp.id

        if emp_id in visited:
            return self.create_emp_card({'employee': emp, 'hierarchy': h}, 5, True)
        visited.add(emp_id)

        emp_level = h.hierarchy_level if h else 5
        color = LEVEL_COLORS.get(emp_level, "#4CAF50") or parent_color

        emp_card_widget = self.create_emp_card({'employee': emp, 'hierarchy': h}, emp_level,
                                               children_map={}, collapsed_nodes=self._collapsed_nodes)

        if not children:
            return emp_card_widget

        is_collapsed = emp_id in self._collapsed_nodes

        if is_collapsed:
            return ft.Column([
                emp_card_widget,
                ft.Container(content=ft.Text(f"+{len(children)} subordinates", size=9, color=TEXT_SECONDARY,
                                             weight=ft.FontWeight.W_500), padding=ft.padding.symmetric(vertical=4))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

        child_widgets = [self._build_tree_node_recursive(
            child_data, level + 1, visited, color) for child_data in children[:12]]

        if not child_widgets:
            return emp_card_widget

        connector = ft.Container(width=2, height=20, bgcolor=color)

        if len(child_widgets) == 1:
            child_container = ft.Column(
                [connector, child_widgets[0]], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        else:
            total_width = len(child_widgets) * 170
            horizontal_bar = ft.Container(
                width=total_width, height=2, bgcolor=color)
            child_columns = [ft.Column([ft.Container(width=2, height=15, bgcolor=color), child],
                                       horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
                             for child in child_widgets]
            children_row = ft.Row(child_columns, spacing=10,
                                  alignment=ft.MainAxisAlignment.CENTER)
            child_container = ft.Column([connector, horizontal_bar, children_row],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

        return ft.Column([emp_card_widget, child_container], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

    def _show_edit_hierarchy(self, e):
        """Show edit hierarchy dialog - FIX FOR AttributeError"""
        self._show_hierarchy_dialog()

    def _show_hierarchy_dialog(self):
        """Show hierarchy management dialog"""
        employees = self._get_all_employees()
        hierarchy = self._get_org_hierarchy()

        emp_options = [ft.dropdown.Option(str(emp.id), f"{emp.first_name or ''} {emp.last_name or ''} ({emp.employee_code or 'N/A'})")
                       for emp in employees]

        if not emp_options:
            self._show_error("No employees available")
            return

        level_options = [
            ft.dropdown.Option("1", "CEO"),
            ft.dropdown.Option("2", "Head"),
            ft.dropdown.Option("3", "Manager"),
            ft.dropdown.Option("4", "Team Lead"),
            ft.dropdown.Option("5", "Employee"),
        ]

        emp_dropdown = ft.Dropdown(
            label="Select Employee", options=emp_options, width=300)
        manager_options = [ft.dropdown.Option(
            "", "-- No Manager (Root) --")] + emp_options
        manager_dropdown = ft.Dropdown(
            label="Reports To", options=manager_options, width=300)
        level_dropdown = ft.Dropdown(
            label="Hierarchy Level", options=level_options, width=200, value="5")

        def save_hierarchy(e):
            if not emp_dropdown.value:
                self._show_error("Please select an employee")
                return

            emp_id = int(emp_dropdown.value)
            manager_id = int(
                manager_dropdown.value) if manager_dropdown.value else None
            level = int(level_dropdown.value) or 5

            db = get_db_session()
            try:
                existing = db.query(OrgHierarchy).filter(
                    OrgHierarchy.employee_id == emp_id).first()
                if existing:
                    existing.reports_to_id = manager_id
                    existing.hierarchy_level = level
                else:
                    new_hierarchy = OrgHierarchy(
                        employee_id=emp_id, reports_to_id=manager_id, hierarchy_level=level)
                    db.add(new_hierarchy)
                db.commit()
                self._show_success("Hierarchy updated!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.ACCOUNT_TREE, color=PRIMARY), ft.Text(
                "Edit Organization Hierarchy")]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Add/Update Employee Hierarchy",
                            size=14, weight=ft.FontWeight.BOLD),
                    emp_dropdown, manager_dropdown, level_dropdown,
                    ft.ElevatedButton("Save", on_click=save_hierarchy, style=ft.ButtonStyle(
                        bgcolor=SUCCESS, color="WHITE")),
                ], scroll=ft.ScrollMode.AUTO),
                width=500, height=300
            ),
            actions=[ft.TextButton(
                "Close", on_click=lambda e: self._close_dialog())]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _delete_hierarchy(self, emp_id):
        """Delete hierarchy entry"""
        db = get_db_session()
        try:
            db.query(OrgHierarchy).filter(
                OrgHierarchy.employee_id == emp_id).delete()
            db.commit()
            self._show_success("Hierarchy entry removed!")
            self._refresh()
        except Exception as ex:
            self._show_error(f"Error: {str(ex)}")
        finally:
            db.close()

    def _close_dialog(self):
        for overlay in self._page.overlay[:]:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _refresh(self):
        """Refresh the org tree"""
        self._last_refresh = time.time()
        self.content = self._build_content()
        self._page.update()
        self._show_success("Organization tree refreshed!")

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

    def on_back(self, e):
        _safe_navigate_to_home(self._page, self.user)


def show_org_tree(page, user):
    """Helper function to show organization tree screen"""
    page.clean()
    page.add(OrganizationTreeScreen(page, user))
