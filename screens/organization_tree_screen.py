"""
Vernika HRA - Organization Tree Screen
Visual hierarchical organization chart with proper connections and improved UI
"""

import flet as ft
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Employee, Department, Position, OrgHierarchy
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
                # Header - removed self._create_header(is_admin)
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
                            on_click=self._show_edit_hierarchy,
                            style=ft.ButtonStyle(
                                bgcolor="#FF9800",
                                color="WHITE"
                            ),
                            visible=is_admin,
                            height=32,
                        ) if is_admin else ft.Container(),
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
        # Update the tree container - layout is Column with [Toolbar, Content]
        self.content.content.controls[1].content = tree_view
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

    def on_back(self, e):
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)

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
        except Exception as e:
            print(f"Error loading hierarchy: {e}")
            return {}
        finally:
            db.close()

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

                if (search_lower in full_name or
                    search_lower in dept_name.lower() or
                    search_lower in pos_title.lower() or
                        search_lower in (emp.employee_code or '').lower()):
                    filtered_employees.append(emp)
            employees = filtered_employees

        # If department view is enabled, show department-based view
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

        # Build hierarchy tree - group employees by their manager
        root_employees = []  # Employees at the top (CEO level)
        children_map = {}   # manager_id -> list of employees
        no_hierarchy_employees = []  # Employees without hierarchy defined

        # First, try to use hierarchy data
        has_hierarchy = False
        for emp in employees:
            h = hierarchy.get(emp.id)
            if h and h.reports_to_id:
                has_hierarchy = True
                if h.reports_to_id not in children_map:
                    children_map[h.reports_to_id] = []
                children_map[h.reports_to_id].append({
                    'employee': emp,
                    'hierarchy': h
                })
            else:
                # No hierarchy or no reports_to_id
                no_hierarchy_employees.append({
                    'employee': emp,
                    'hierarchy': h
                })

        # If we have hierarchy data, find root employees (those who are managers but don't report to anyone)
        if has_hierarchy:
            # Find all employees who have someone reporting to them
            manager_ids = set(children_map.keys())

            # Root employees are those who have hierarchy but no reports_to_id
            for emp_data in no_hierarchy_employees:
                emp = emp_data['employee']
                h = emp_data['hierarchy']
                if h and h.reports_to_id is None:
                    root_employees.append(emp_data)

            # Also add employees who are managers but not in hierarchy as reports
            for emp in employees:
                h = hierarchy.get(emp.id)
                if h and h.reports_to_id is None and emp.id not in manager_ids:
                    # This is a root-level employee
                    root_employees.append({
                        'employee': emp,
                        'hierarchy': h
                    })

        # If no hierarchy data or no root employees found, use department-based grouping
        if not root_employees:
            # Group by department head
            dept_heads = {}
            for emp in employees:
                if emp.department and emp.department.head_id:
                    if emp.department.head_id not in dept_heads:
                        dept_heads[emp.department.head_id] = []
                    dept_heads[emp.department.head_id].append(emp)

            # Use department grouping if available
            if dept_heads:
                for head_id, dept_employees in dept_heads.items():
                    head_emp = next(
                        (e for e in employees if e.id == head_id), None)
                    if head_emp:
                        root_employees.append({
                            'employee': head_emp,
                            'hierarchy': None
                        })
                        # Add remaining employees as children
                        for emp in dept_employees:
                            if emp.id != head_id:
                                if head_id not in children_map:
                                    children_map[head_id] = []
                                children_map[head_id].append({
                                    'employee': emp,
                                    'hierarchy': hierarchy.get(emp.id)
                                })
                has_hierarchy = True

        # If still no hierarchy, treat all employees as having no hierarchy
        if not root_employees and no_hierarchy_employees:
            # All employees without hierarchy - will be shown under "Intern" node
            pass

        # ==================== COMPANY CARD ====================
        def create_company_card():
            """Create the company card at the top of the org tree"""
            return ft.Container(
                width=220,
                padding=15,
                bgcolor=SURFACE,
                border_radius=12,
                border=ft.border.all(3, PRIMARY),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=8,
                    color="rgba(46,134,171,0.3)"
                ),
                content=ft.Column([
                    # Company Logo Icon
                    ft.Container(
                        width=60, height=60,
                        bgcolor=PRIMARY,
                        border_radius=30,
                        content=ft.Icon(
                            ft.Icons.BUSINESS,
                            size=35, color="WHITE"
                        ),
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Container(height=8),
                    # Company Name
                    ft.Text(
                        "Vernika Technologies",
                        size=14, weight=ft.FontWeight.BOLD,
                        color=PRIMARY, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Organization",
                        size=11, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=5),
                    ft.Divider(height=1),
                    ft.Container(height=5),
                    # Employee count
                    ft.Row([
                        ft.Icon(ft.Icons.PEOPLE, size=14,
                                color=TEXT_SECONDARY),
                        ft.Text(f"{len(employees)} Employees",
                                size=10, color=TEXT_SECONDARY),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            )

        # ==================== CONNECTION LINE ====================
        def create_connection_line(color=PRIMARY, height=25):
            """Create a vertical connection line"""
            return ft.Container(
                width=3,
                height=height,
                bgcolor=color,
            )

        # ==================== EMPLOYEE CARD ====================
        # DESIGNED TO MATCH COMPANY CARD STYLE
        def create_emp_card(emp_data, emp_level=5, is_root=False, is_collapsed=False):
            """Create a single employee card with proper connections and collapse button - MATCHING COMPANY CARD DESIGN"""
            emp = emp_data['employee'] if isinstance(
                emp_data, dict) else emp_data
            h = emp_data.get('hierarchy') if isinstance(
                emp_data, dict) else None

            color = LEVEL_COLORS.get(emp_level, "#4CAF50")
            label = LEVEL_LABELS.get(emp_level, "Employee")

            if is_root:
                color = "#D32F2F"  # Root nodes are red
                label = "Root"

            position_title = getattr(
                getattr(emp, 'position', None), 'title', None) or "Employee"

            department_name = getattr(
                getattr(emp, 'department', None), 'name', None) or ""

            # Get initials or profile photo
            first_name = emp.first_name or ""
            last_name = emp.last_name or ""
            initials = f"{first_name[0:1]}{last_name[0:1]}".upper()

            # Check for profile photo - validate path
            import os
            from pathlib import Path
            profile_photo_url = getattr(emp, 'profile_photo', None) or None
            profile_photo_valid = False
            profile_photo_to_show = None

            if profile_photo_url:
                # Check if profile photo path is valid
                if profile_photo_url.startswith('http'):
                    profile_photo_valid = True
                    profile_photo_to_show = profile_photo_url
                else:
                    # Check if local path exists as-is
                    if os.path.exists(profile_photo_url):
                        profile_photo_valid = True
                        profile_photo_to_show = profile_photo_url
                    else:
                        # Try relative to assets/profile_photos directory
                        base_dir = Path(__file__).parent.parent
                        assets_path = base_dir / "assets" / "profile_photos" / \
                            os.path.basename(profile_photo_url)
                        if assets_path.exists():
                            profile_photo_valid = True
                            profile_photo_to_show = str(assets_path)
                        else:
                            # Try just the basename in profile_photos
                            basename = os.path.basename(profile_photo_url)
                            assets_path2 = base_dir / "assets" / "profile_photos" / basename
                            if assets_path2.exists():
                                profile_photo_valid = True
                                profile_photo_to_show = str(assets_path2)

            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name[:20] + \
                "..." if len(full_name) > 20 else full_name

            # Check if this employee has children
            has_children = emp.id in children_map and len(
                children_map.get(emp.id, [])) > 0

            # Create collapse/expand button
            collapse_btn = ft.Container()
            if has_children:
                is_node_collapsed = emp.id in self._collapsed_nodes
                collapse_btn = ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.EXPAND_MORE if is_node_collapsed else ft.Icons.EXPAND_LESS,
                        icon_size=16,
                        on_click=lambda e, emp_id=emp.id: self._toggle_collapse(
                            emp_id),
                        tooltip="Expand/Collapse" if not is_node_collapsed else "Click to expand",
                        style=ft.ButtonStyle(
                            bgcolor="transparent",
                            padding=0,
                        ),
                    ),
                    width=20,
                    height=20,
                )

            # Create avatar - show profile photo if available and valid, otherwise initials
            if profile_photo_valid and profile_photo_to_show:
                avatar_content = ft.Container(
                    width=50,
                    height=50,
                    border_radius=25,
                    content=ft.Image(
                        src=profile_photo_to_show,
                        width=50,
                        height=50,
                        fit=ft.BoxFit.COVER,
                    ),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                )
            else:
                avatar_content = ft.Container(
                    width=50,
                    height=50,
                    bgcolor=color,
                    border_radius=25,
                    content=ft.Text(
                        initials if initials else "?",
                        size=16, color="WHITE", weight=ft.FontWeight.BOLD
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                )

            # Create employee card with COMPANY CARD STYLE DESIGN
            # Matching the exact design of company card
            return ft.Container(
                width=200,
                padding=12,
                bgcolor=SURFACE,
                border_radius=12,
                border=ft.border.all(2, color),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=8,
                    color=color + "30"
                ),
                content=ft.Column([
                    # Avatar - centered at top - matching company card style
                    ft.Container(
                        content=avatar_content,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Container(height=8),
                    # Name - centered - matching company card
                    ft.Text(
                        display_name,
                        size=12, weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    # Position - centered below name - matching company card
                    ft.Text(
                        position_title[:25] +
                        "..." if len(position_title) > 25 else position_title,
                        size=10, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    ft.Container(height=5),
                    # Divider - matching company card style
                    ft.Divider(height=1),
                    ft.Container(height=5),
                    # Department badge - centered - matching company card style
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PEOPLE, size=10, color="WHITE"),
                            ft.Text(
                                department_name[:18] if department_name else "No Dept",
                                size=8, color="WHITE"
                            ),
                        ], spacing=3, alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor=PRIMARY,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=10,
                        alignment=ft.alignment.Alignment(0, 0),
                    ) if department_name else ft.Container(height=0),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            )

        def build_tree_recursive(emp_data, level=0, visited=None, parent_color=None):
            """Recursively build tree with proper connection lines and collapsible branches"""
            if visited is None:
                visited = set()

            emp = emp_data['employee'] if isinstance(
                emp_data, dict) else emp_data
            h = emp_data.get('hierarchy') if isinstance(
                emp_data, dict) else None

            # Prevent infinite recursion
            if emp.id in visited:
                return create_emp_card(emp_data, 5, True)
            visited.add(emp.id)

            emp_level = h.hierarchy_level if h else 5
            children_list = children_map.get(emp.id, [])

            # Check if this node is collapsed
            is_collapsed = emp.id in self._collapsed_nodes

            # Get color for this level
            color = LEVEL_COLORS.get(emp_level, "#4CAF50")
            if parent_color:
                color = parent_color

            emp_card = create_emp_card(
                emp_data, emp_level, not children_list, is_collapsed)

            if not children_list:
                return emp_card

            # If collapsed, show indicator
            if is_collapsed:
                collapsed_indicator = ft.Container(
                    content=ft.Text(
                        f"+{len(children_list)} more",
                        size=9, color=TEXT_SECONDARY, weight=ft.FontWeight.W_500
                    ),
                    padding=ft.padding.symmetric(vertical=4),
                )
                return ft.Column([
                    emp_card,
                    collapsed_indicator
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

            # Build child cards
            child_widgets = []
            for child_data in children_list[:8]:  # Max 8 children
                child_emp = child_data['employee']
                if child_emp.id not in visited:
                    child_widgets.append(
                        build_tree_recursive(child_data, level + 1, visited, color))

            if not child_widgets:
                return emp_card

            # Create proper connectors for multiple children
            # Vertical line from parent
            connector = ft.Container(
                width=2,
                height=20,
                bgcolor=color
            )

            # Children container with proper alignment
            if len(child_widgets) == 1:
                # Single child - simple vertical connection
                child_container = ft.Column([
                    connector,
                    child_widgets[0]
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            else:
                # Multiple children - proper tree-style connector
                # Create individual vertical connectors for each child
                child_columns = []
                for child_widget in child_widgets:
                    # Each child gets its own vertical connector from the horizontal bar
                    child_columns.append(
                        ft.Column([
                            ft.Container(width=2, height=15, bgcolor=color),
                            child_widget
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
                    )

                # Horizontal bar at the top of children
                # Calculate proper spacing
                total_width = len(child_columns) * 170
                horizontal_bar = ft.Container(
                    width=total_width,
                    height=2,
                    bgcolor=color
                )

                # Row with all children
                children_row = ft.Row(
                    child_columns,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER
                )

                # Combine: connector from parent -> horizontal bar -> children
                child_container = ft.Column([
                    connector,
                    horizontal_bar,
                    children_row
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

            return ft.Column([
                emp_card,
                child_container
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

        # Build the main tree structure with Company Card at top
        tree_nodes = []

        # First, add root employees with hierarchy
        for emp_data in root_employees[:5]:  # Max 5 top-level nodes
            tree_nodes.append(build_tree_recursive(emp_data, 0))

        # ==================== CREATE MAIN DISPLAY WITH COMPANY CARD ====================
        # Company card at top with connection to hierarchy
        company_card = create_company_card()

        # If there are root employees, show connection line from company to them
        if tree_nodes:
            # Create horizontal connector bar from company to first level
            if len(tree_nodes) == 1:
                # Single root - simple vertical connection
                tree_with_company = ft.Column([
                    company_card,
                    create_connection_line(height=20),
                    tree_nodes[0]
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            else:
                # Multiple roots - create proper horizontal connector bar
                # Each root gets its own vertical connector from the main horizontal bar

                # First, create a horizontal bar that spans all roots
                root_spacing = 40
                total_roots_width = len(
                    tree_nodes) * 160 + (len(tree_nodes) - 1) * root_spacing
                main_horizontal_bar = ft.Container(
                    width=total_roots_width,
                    height=2,
                    bgcolor=PRIMARY
                )

                # Create vertical connectors for each root node
                root_columns = []
                for tree_node in tree_nodes:
                    root_columns.append(
                        ft.Column([
                            create_connection_line(height=15),
                            tree_node
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
                    )

                # Row with all root nodes and their vertical connectors
                roots_row = ft.Row(
                    root_columns,
                    spacing=root_spacing,
                    alignment=ft.MainAxisAlignment.CENTER
                )

                # Vertical line from company to horizontal bar
                main_connector = create_connection_line(height=20)

                # Combine everything: company -> main -> horizontal bar -> roots
                tree_with_company = ft.Column([
                    company_card,
                    main_connector,
                    main_horizontal_bar,
                    roots_row
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        else:
            # No root employees - show company card with interns/employees
            tree_with_company = company_card

        # If we have employees without hierarchy, create "Intern" node
        if no_hierarchy_employees:
            # Filter out employees that are already in the tree
            all_tree_emp_ids = set()

            def collect_emp_ids(emp_data):
                emp = emp_data['employee'] if isinstance(
                    emp_data, dict) else emp_data
                all_tree_emp_ids.add(emp.id)
                for child_data in children_map.get(emp.id, []):
                    collect_emp_ids(child_data)

            for root in root_employees:
                collect_emp_ids(root)

            # Get remaining employees not in tree
            remaining_employees = [
                e for e in no_hierarchy_employees
                if e['employee'].id not in all_tree_emp_ids
            ]

            if remaining_employees:
                # Create "Intern" node with remaining employees
                intern_card = ft.Container(
                    width=160,
                    padding=8,
                    bgcolor=SURFACE,
                    border_radius=8,
                    border=ft.border.all(2, LEVEL_COLORS[5]),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=4,
                        color="rgba(0,0,0,0.2)"
                    ),
                    content=ft.Column([
                        ft.Container(
                            width=40, height=40,
                            bgcolor=LEVEL_COLORS[5],
                            border_radius=20,
                            content=ft.Icon(
                                ft.Icons.SCHOOL,
                                size=20, color="WHITE"
                            ),
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Text(
                            "Interns",
                            size=10, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            f"{len(remaining_employees)} Employees",
                            size=8, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                )

                # Create cards for remaining employees
                intern_children = []
                for emp_data in remaining_employees[:8]:  # Max 8 shown
                    intern_children.append(create_emp_card(emp_data, 5, False))

                if intern_children:
                    # Horizontal connector
                    intern_connector = ft.Container(
                        width=2,
                        height=15,
                        bgcolor=LEVEL_COLORS[5]
                    )

                    intern_row = ft.Row(
                        intern_children,
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER
                    )

                    intern_node = ft.Column([
                        intern_card,
                        intern_connector,
                        intern_row
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

                    tree_nodes.append(intern_node)

        # ==================== CREATE FINAL TREE DISPLAY ====================
        # If only one root and has no children, show all employees in a grid with company card
        if len(tree_nodes) == 1 and not children_map and not no_hierarchy_employees:
            # Show all employees as a grid with company card at top
            all_cards = []
            for emp in employees:
                all_cards.append(create_emp_card(
                    {'employee': emp, 'hierarchy': hierarchy.get(emp.id)}, 4, True))

            # Arrange in rows
            card_rows = []
            for i in range(0, len(all_cards), 4):
                card_rows.append(
                    ft.Row(all_cards[i:i+4], spacing=15, alignment=ft.MainAxisAlignment.CENTER))

            # Grid with company card on top
            grid_with_company = ft.Column([
                company_card,
                create_connection_line(height=20),
                ft.Column(card_rows, spacing=20,
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

            tree_display = grid_with_company
        else:
            # Use tree with company card for other cases
            tree_display = ft.Column([
                tree_with_company
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # Add legend
        legend = ft.Container(
            padding=12,
            bgcolor=SURFACE,
            border_radius=8,
            margin=ft.margin.only(bottom=10),
            content=ft.Row([
                ft.Container(content=ft.Row([
                    ft.Container(width=10, height=10,
                                 bgcolor="#D32F2F", border_radius=2),
                    ft.Text("CEO/Root", size=9),
                ], spacing=3)),
                ft.Container(content=ft.Row([
                    ft.Container(width=10, height=10,
                                 bgcolor="#FF9800", border_radius=2),
                    ft.Text("Head", size=9),
                ], spacing=3)),
                ft.Container(content=ft.Row([
                    ft.Container(width=10, height=10,
                                 bgcolor="#2196F3", border_radius=2),
                    ft.Text("Manager", size=9),
                ], spacing=3)),
                ft.Container(content=ft.Row([
                    ft.Container(width=10, height=10,
                                 bgcolor="#9C27B0", border_radius=2),
                    ft.Text("Team Lead", size=9),
                ], spacing=3)),
                ft.Container(content=ft.Row([
                    ft.Container(width=10, height=10,
                                 bgcolor="#4CAF50", border_radius=2),
                    ft.Text("Employee", size=9),
                ], spacing=3)),
                ft.Container(content=ft.Row([
                    ft.Container(width=10, height=10,
                                 bgcolor="#607D8B", border_radius=2),
                    ft.Text("Intern", size=9),
                ], spacing=3)),
            ], spacing=20)
        )

        # Employee count info
        info_text = ft.Container(
            padding=10,
            content=ft.Text(
                f"Total Employees: {len(employees)} | With Hierarchy: {len([e for e in employees if hierarchy.get(e.id) and hierarchy.get(e.id).reports_to_id])} | Without Hierarchy: {len(no_hierarchy_employees)}",
                size=11, color=TEXT_SECONDARY
            )
        )

        # Wrap in scrollable container
        return ft.Column([
            legend,
            info_text,
            ft.Container(
                content=ft.ListView([
                    tree_display
                ], spacing=20, padding=20, expand=True),
                expand=True
            ),
        ], expand=True)

    def _show_edit_hierarchy(self, e):
        """Show edit hierarchy dialog"""
        self._show_hierarchy_dialog()

    def _show_hierarchy_dialog(self):
        """Show hierarchy management dialog"""
        employees = self._get_all_employees()
        hierarchy = self._get_org_hierarchy()

        emp_options = []
        for emp in employees:
            name = f"{emp.first_name or ''} {emp.last_name or ''} ({emp.employee_code or 'N/A'})"
            emp_options.append(ft.dropdown.Option(str(emp.id), name))

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
            label="Select Employee",
            options=emp_options,
            width=300
        )

        manager_options = [ft.dropdown.Option(
            "", "-- No Manager (Root) --")] + emp_options
        manager_dropdown = ft.Dropdown(
            label="Reports To (Manager)",
            options=manager_options,
            width=300
        )

        level_dropdown = ft.Dropdown(
            label="Hierarchy Level",
            options=level_options,
            width=200,
            value="5"
        )

        def save_hierarchy(e):
            if not emp_dropdown.value:
                self._show_error("Please select an employee")
                return

            emp_id = int(emp_dropdown.value)
            manager_id = int(
                manager_dropdown.value) if manager_dropdown.value else None
            level = int(level_dropdown.value) if level_dropdown.value else 5

            db = get_db_session()
            try:
                existing = db.query(OrgHierarchy).filter(
                    OrgHierarchy.employee_id == emp_id
                ).first()

                if existing:
                    existing.reports_to_id = manager_id
                    existing.hierarchy_level = level
                else:
                    new_hierarchy = OrgHierarchy(
                        employee_id=emp_id,
                        reports_to_id=manager_id,
                        hierarchy_level=level
                    )
                    db.add(new_hierarchy)

                db.commit()
                self._show_success("Hierarchy updated successfully!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        hierarchy_list = ft.Column([
            ft.Text("Current Hierarchy Assignments",
                    size=14, weight=ft.FontWeight.BOLD),
            ft.Divider()
        ])

        for emp_id, h in hierarchy.items():
            emp = next((e for e in employees if e.id == emp_id), None)
            if emp:
                manager = next(
                    (e for e in employees if e.id == h.reports_to_id), None)
                manager_name = f"{manager.first_name} {manager.last_name}" if manager else "None (Root)"

                level_names = {1: "CEO", 2: "Head",
                               3: "Manager", 4: "Team Lead", 5: "Employee"}

                hierarchy_list.controls.append(
                    ft.Container(
                        padding=10,
                        bgcolor="#F5F5F5",
                        border_radius=8,
                        margin=ft.margin.only(bottom=5),
                        content=ft.Row([
                            ft.Text(f"{emp.first_name} {emp.last_name}",
                                    weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(f"→ {manager_name}", size=12,
                                    color=TEXT_SECONDARY),
                            ft.Container(
                                content=ft.Text(level_names.get(
                                    h.hierarchy_level, "Employee"), size=10),
                                bgcolor=PRIMARY,
                                padding=5,
                                border_radius=4,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ERROR,
                                on_click=lambda e, eid=emp_id: self._delete_hierarchy(
                                    eid),
                                scale=0.7
                            ),
                        ])
                    )
                )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.ACCOUNT_TREE, color=PRIMARY), ft.Text(
                "Edit Organization Hierarchy")]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Add/Update Employee Hierarchy",
                            size=14, weight=ft.FontWeight.BOLD),
                    emp_dropdown,
                    manager_dropdown,
                    level_dropdown,
                    ft.ElevatedButton("Save", on_click=save_hierarchy, style=ft.ButtonStyle(
                        bgcolor=SUCCESS, color="WHITE")),
                    ft.Divider(),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.ListView(
                            [hierarchy_list],
                            spacing=5,
                            padding=10,
                            auto_scroll=True,
                        ),
                        height=280,
                        width=450,
                    ),
                ], scroll=ft.ScrollMode.AUTO),
                width=500,
                height=550,
            ),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
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
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _refresh(self):
        """Refresh the org tree to reflect database changes"""
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


def show_org_tree(page, user):
    """Helper function to show organization tree screen"""
    page.clean()
    page.add(OrganizationTreeScreen(page, user))
