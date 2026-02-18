"""
Vernika HRA - Organization Tree Screen
Visual hierarchical organization chart with edit capabilities
"""

import flet as ft
from database.connection import get_db_session
from database.models import Employee, Department, Position, OrgHierarchy
from sqlalchemy.orm import joinedload


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


class OrganizationTreeScreen(ft.Container):
    """Organization Tree/Chart Display Screen"""

    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.content = self._build_content()

    def _build_content(self):
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self.on_back
                ),
                ft.Icon(ft.Icons.ACCOUNT_TREE, color="WHITE", size=28),
                ft.Text("Organization Tree", size=20,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Edit Hierarchy",
                    icon=ft.Icons.EDIT,
                    on_click=self._show_edit_hierarchy,
                    style=ft.ButtonStyle(bgcolor="#FF9800", color="WHITE"),
                    visible=self._is_admin()
                ),
            ])
        )

        # Build org tree
        tree_view = self._build_org_tree()

        content = ft.Column([
            header,
            ft.Container(
                padding=20,
                content=tree_view,
                expand=True
            )
        ], expand=True)

        return content

    def _is_admin(self):
        """Check if current user is admin"""
        if isinstance(self.user, dict):
            role = self.user.get('role', '').lower()
            return role == 'admin'
        return False

    def on_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

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
        """Build the organization tree visualization"""
        employees = self._get_all_employees()
        hierarchy = self._get_org_hierarchy()

        if not employees:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED,
                            size=64, color="#BDBDBD"),
                    ft.Text("No employees found.", size=14, color="#757575"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        # Build employee lookup
        emp_dict = {emp.id: emp for emp in employees}

        # Build hierarchy tree
        # Group employees by their manager
        root_employees = []  # CEO level (no manager)
        manager_employees = {}  # employee_id -> list of direct reports

        for emp in employees:
            h = hierarchy.get(emp.id)
            if h and h.reports_to_id:
                if h.reports_to_id not in manager_employees:
                    manager_employees[h.reports_to_id] = []
                manager_employees[h.reports_to_id].append(emp)
            else:
                # No hierarchy entry or no manager = root
                root_employees.append(emp)

        # If no hierarchy, use department heads
        if not root_employees:
            # Find employees with no department or are heads
            root_employees = [
                emp for emp in employees if not emp.department_id or emp.position_id]

        # Build tree nodes
        def build_tree_node(emp, level=0):
            children = manager_employees.get(emp.id, [])
            reports = [e for e in employees if hierarchy.get(
                e.id) and hierarchy.get(e.id).reports_to_id == emp.id]

            if reports:
                children = reports

            level_colors = {
                0: "#D32F2F",  # CEO - Red
                1: "#FF9800",  # Head - Orange
                2: "#2196F3",  # Manager - Blue
                3: "#9C27B0",  # Team Lead - Purple
                4: "#4CAF50",  # Employee - Green
            }

            level_labels = {
                0: "CEO",
                1: "Head",
                2: "Manager",
                3: "Team Lead",
                4: "Employee",
            }

            h = hierarchy.get(emp.id)
            emp_level = h.hierarchy_level if h else 4
            level_color = level_colors.get(emp_level, "#4CAF50")
            level_label = level_labels.get(emp_level, "Employee")

            # Employee card
            emp_card = ft.Container(
                width=200,
                padding=10,
                bgcolor=SURFACE,
                border_radius=10,
                border=ft.border.all(2, level_color),
                shadow=ft.BoxShadow(
                    spread_radius=1, blur_radius=5, color="#00000010"),
                content=ft.Column([
                    ft.Container(
                        width=50, height=50,
                        bgcolor=level_color,
                        border_radius=25,
                        content=ft.Text(
                            f"{emp.first_name[0] if emp.first_name else ''}{emp.last_name[0] if emp.last_name else ''}",
                            size=18, color="WHITE", weight=ft.FontWeight.BOLD
                        ),
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Text(
                        f"{emp.first_name or ''} {emp.last_name or ''}",
                        size=13, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        emp.position.title if emp.position else "Employee",
                        size=11, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(
                        content=ft.Text(level_label, size=9, color="WHITE"),
                        bgcolor=level_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=10,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
            )

            if children:
                # Build children nodes
                child_nodes = ft.Row(
                    # Limit children display
                    [build_tree_node(child, level+1)
                     for child in children[:5]],
                    spacing=15,
                    alignment=ft.MainAxisAlignment.CENTER
                )

                return ft.Column([
                    emp_card,
                    ft.Container(
                        width=2, height=20, bgcolor=level_color
                    ),
                    child_nodes,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            else:
                return emp_card

        # Build the tree display
        if root_employees:
            tree_rows = []
            for root_emp in root_employees[:3]:  # Show top 3 roots
                tree_rows.append(build_tree_node(root_emp))

            tree_display = ft.Column(
                tree_rows, spacing=30, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            # Fallback: show all employees in a grid
            tree_display = ft.Column(
                [build_tree_node(emp) for emp in employees[:12]],
                spacing=15,
            )

        # Add legend
        legend = ft.Container(
            padding=15,
            bgcolor=SURFACE,
            border_radius=10,
            content=ft.Column([
                ft.Text("Hierarchy Levels", size=14,
                        weight=ft.FontWeight.BOLD),
                ft.Row([
                    self._create_legend_item("CEO", "#D32F2F"),
                    self._create_legend_item("Head", "#FF9800"),
                    self._create_legend_item("Manager", "#2196F3"),
                    self._create_legend_item("Team Lead", "#9C27B0"),
                    self._create_legend_item("Employee", "#4CAF50"),
                ], spacing=20),
            ], spacing=5)
        )

        return ft.Column([
            legend,
            ft.Container(height=20),
            ft.Container(
                content=tree_display,
                expand=True
            ),
        ], expand=True)

    def _create_legend_item(self, label, color):
        """Create a legend item"""
        return ft.Row([
            ft.Container(width=15, height=15, bgcolor=color, border_radius=3),
            ft.Text(label, size=11),
        ], spacing=5)

    def _show_edit_hierarchy(self, e):
        """Show edit hierarchy dialog"""
        self._show_hierarchy_dialog()

    def _show_hierarchy_dialog(self):
        """Show hierarchy management dialog"""
        employees = self._get_all_employees()
        hierarchy = self._get_org_hierarchy()

        # Create employee options
        emp_options = []
        for emp in employees:
            name = f"{emp.first_name or ''} {emp.last_name or ''} ({emp.employee_code or 'N/A'})"
            emp_options.append(ft.dropdown.Option(str(emp.id), name))

        if not emp_options:
            self._show_error("No employees available")
            return

        # Level options
        level_options = [
            ft.dropdown.Option("1", "CEO"),
            ft.dropdown.Option("2", "Head"),
            ft.dropdown.Option("3", "Manager"),
            ft.dropdown.Option("4", "Team Lead"),
            ft.dropdown.Option("5", "Employee"),
        ]

        # Employee dropdown
        emp_dropdown = ft.Dropdown(
            label="Select Employee",
            options=emp_options,
            width=300
        )

        # Manager dropdown (optional)
        manager_options = [ft.dropdown.Option(
            "", "-- No Manager (Root) --")] + emp_options
        manager_dropdown = ft.Dropdown(
            label="Reports To (Manager)",
            options=manager_options,
            width=300
        )

        # Level dropdown
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
                # Check if hierarchy entry exists
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

        # Current hierarchy list
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
                        content=hierarchy_list,
                        height=300,
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
        self.content = self._build_content()
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


def show_org_tree(page, user):
    """Helper function to show organization tree screen"""
    page.clean()
    page.add(OrganizationTreeScreen(page, user))
