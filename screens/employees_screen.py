"""
Vernika HRA - Enhanced Employees Screen with ID/PASS Creation, Full Details, and Document Generation
"""

from utils.supabase_storage import upload_to_supabase
from components.forms import DatePickerField
from database.operations import get_all_employees, get_employee_by_id, delete_employee_complete
from database.session_manager import get_db_session
from database.models import Employee, User, Department, Position, Role
from database.session_manager import get_session, get_db_session, check_db_connection
import os
import string
import random
from sqlalchemy import func
from datetime import datetime, date
import bcrypt
import flet as ft
from flet import padding

# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"
INFO = "#2196F3"
BACKGROUND = "#F5F5F5"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"


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


class EmployeesScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = "#F5F5F5"
        self._dialog = None
        self._nav_rail_visible = True
        self._file_picker = None
        self.content = self._build_content()

    def _get_db(self):
        """Get database connection using SQLAlchemy"""
        return get_db_session()

    def _init_file_picker(self):
        """Initialize file picker for profile photos - using page.services (Flet 0.80+)"""
        if not self._file_picker:
            self._file_picker = ft.FilePicker()
            # Use page.services for Service objects (Flet 0.80+)
            # FilePicker is a Service, not a Control
            try:
                if self._file_picker not in self._page.services:
                    self._page.services.append(self._file_picker)
            except AttributeError:
                # Fallback for older Flet versions or if services doesn't exist
                if self._file_picker not in self._page.overlay:
                    self._page.overlay.append(self._file_picker)

    def _build_content(self):
        """Build the full content with header"""
        # Build header with Add Employee button
        header = self._create_header()

        # Build employee list
        employee_list = self._build_employee_list()

        content = ft.Column([
            header,
            ft.Container(
                padding=20,
                content=employee_list,
                expand=True
            )
        ], expand=True)

        return content

    def _create_header(self):
        """Create header with Add Employee button"""
        return ft.Container(
            content=ft.Row([
                ft.Container(width=10),
                ft.Icon(ft.Icons.BADGE, color="WHITE", size=28),
                ft.Text("Vernika HRA - Employees Management", size=18,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                # Add Employee button in header
                ft.ElevatedButton(
                    "Add Employee",
                    icon=ft.Icons.PERSON_ADD,
                    on_click=self.on_add_employee,
                    style=ft.ButtonStyle(
                        bgcolor="WHITE",
                        color=PRIMARY,
                    ),
                ),
                ft.Container(width=10),
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
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=PRIMARY,
        )

    def _handle_logout(self, e):
        """Handle logout"""
        from screens.login_screen import LoginScreen
        self._page.clean()
        self._page.add(LoginScreen(self._page))

    def on_back(self, e):
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)

    def on_add_employee(self, e):
        self._show_add_dialog()

    def _build_employee_list(self):
        """Build employee list with PostgreSQL"""
        from sqlalchemy.orm import joinedload

        db = None
        try:
            db = get_db_session()
            # Query employees with eager loading of relationships using SQLAlchemy
            employees = db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            ).all()
        except Exception as e:
            print(f"Error loading employees: {e}")
            employees = []
        finally:
            if db:
                db.close()

        if not employees:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=64, color="#BDBDBD"),
                    ft.Text("No employees found.", size=14, color="#757575"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Add First Employee",
                        on_click=self.on_add_employee,
                        style=ft.ButtonStyle(bgcolor="#4CAF50", color="WHITE")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        rows = []
        for emp in employees:
            status_color = "#4CAF50" if emp.is_active else "#F44336"
            status_text = "Active" if emp.is_active else "Inactive"
            emp_id = emp.id

            emp_type = emp.employment_type or "Full-time"
            type_color = "#2196F3" if emp_type == "Full-time" else "#FF9800"

            # Get department and position names
            dept_name = emp.department.name if emp.department else "General"
            pos_title = emp.position.title if emp.position else "-"

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(emp.id))),
                        ft.DataCell(
                            ft.Text(emp.employee_code or f"EMP{emp.id:03d}")),
                        ft.DataCell(
                            ft.Text(f"{emp.first_name or ''} {emp.last_name or ''}")),
                        ft.DataCell(ft.Text(emp.email or "-")),
                        ft.DataCell(ft.Text(dept_name)),
                        ft.DataCell(ft.Text(pos_title)),
                        ft.DataCell(
                            ft.Container(
                                ft.Text(status_text, size=11, color="WHITE"),
                                bgcolor=status_color,
                                padding=padding.all(5),
                                border_radius=4
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color="#1976D2",
                                    on_click=lambda e, emp_id=emp_id: self._show_edit_dialog(
                                        emp_id),
                                    tooltip="Edit"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.PERSON,
                                    icon_color="#4CAF50",
                                    on_click=lambda e, emp_id=emp_id: self._show_details_dialog(
                                        emp_id),
                                    tooltip="View Full Details"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.BADGE,
                                    icon_color="#FF9800",
                                    on_click=lambda e, emp_id=emp_id: self._generate_id_card_dialog(
                                        emp_id),
                                    tooltip="Generate ID Card"
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color="#D32F2F",
                                    on_click=lambda e, emp_id=emp_id: self._show_delete_dialog(
                                        emp_id),
                                    tooltip="Delete"
                                ),
                            ], spacing=1)
                        ),
                    ]
                )
            )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(label=ft.Text("ID")),
                ft.DataColumn(label=ft.Text("Code")),
                ft.DataColumn(label=ft.Text("Name")),
                ft.DataColumn(label=ft.Text("Email")),
                ft.DataColumn(label=ft.Text("Department")),
                ft.DataColumn(label=ft.Text("Position")),
                ft.DataColumn(label=ft.Text("Status")),
                ft.DataColumn(label=ft.Text("Actions")),
            ],
            rows=rows,
            expand=True,
        )

        return ft.Container(content=table, expand=True)

    def _generate_password(self, length=8):
        """Generate a random password"""
        characters = string.ascii_letters + string.digits + "!@#$"
        return ''.join(random.choice(characters) for _ in range(length))

    def _generate_username(self, first_name, last_name):
        """Generate a unique username"""
        base = f"{first_name.lower()}.{last_name.lower()}" if last_name else first_name.lower()
        base = ''.join(c for c in base if c.isalnum() or c == '.')
        return base[:50]

    def _show_add_dialog(self):
        db = None
        try:
            db = get_db_session()
            departments = db.query(Department).all()
            positions = db.query(Position).all()
            roles = db.query(Role).all()
        except Exception as e:
            print(f"Error loading departments/positions: {e}")
            departments = []
            positions = []
            roles = []
        finally:
            if db:
                db.close()

        # Personal Info Section
        first_name = ft.TextField(label="First Name *", width=200)
        last_name = ft.TextField(label="Last Name *", width=200)
        email = ft.TextField(label="Email *", width=420)
        phone = ft.TextField(label="Phone", width=200)

        # Profile Photo Section
        profile_photo = ft.TextField(label="Profile Photo URL", width=320,
                                     hint_text="Enter image URL or file path")

        # File picker button for profile photo
        profile_photo_path = [None]  # Use list to store reference

        def pick_profile_photo(e):
            """Pick profile photo using file picker and upload to Supabase"""
            self._init_file_picker()

            async def pick_and_set():
                try:
                    files = await self._file_picker.pick_files(
                        dialog_title="Choose Profile Photo",
                        file_type=ft.FilePickerFileType.IMAGE,
                    )
                    if files and files[0]:
                        path = files[0].path
                        profile_photo_path[0] = path

                        # Upload to Supabase Storage for multi-device access
                        try:
                            success, file_url, bucket_path = upload_to_supabase(
                                file_path=path,
                                folder="profiles",
                                custom_filename=os.path.basename(path)
                            )
                            if success and file_url:
                                # Save the Supabase URL instead of local path
                                profile_photo.value = file_url
                                print(f"Profile photo uploaded: {file_url}")
                            else:
                                # Fallback to local path if upload fails
                                profile_photo.value = path
                                print(
                                    f"Profile photo upload failed, using local path: {path}")
                        except Exception as upload_err:
                            print(
                                f"Error uploading profile photo: {upload_err}")
                            # Fallback to local path
                            profile_photo.value = path
                            self._show_error(
                                f"Upload failed: {str(upload_err)}")

                        self._page.update()
                except Exception as ex:
                    print(f"Error picking file: {ex}")
                    self._show_error(f"Error selecting file: {str(ex)}")

            self._page.run_task(pick_and_set)

        profile_pick_btn = ft.IconButton(
            icon=ft.Icons.IMAGE,
            tooltip="Browse for image",
            on_click=pick_profile_photo
        )

        # Date pickers for DOB and Date of Joining
        dob_picker = DatePickerField(label="Date of Birth", width=200)
        dob_picker._page = self._page

        gender = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("MALE", "Male"),
                ft.dropdown.Option("FEMALE", "Female"),
                ft.dropdown.Option("OTHER", "Other"),
            ],
            label="Gender",
            value="MALE"
        )
        address = ft.TextField(label="Address", width=420, multiline=True)
        city = ft.TextField(label="City", width=200)
        state = ft.TextField(label="State", width=200)
        pincode = ft.TextField(label="Pincode", width=100)

        # Emergency Contact Section
        emergency_contact_name = ft.TextField(
            label="Emergency Contact Name", width=250)
        emergency_phone = ft.TextField(label="Emergency Phone", width=200)
        emergency_relation = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("spouse", "Spouse"),
                ft.dropdown.Option("parent", "Parent"),
                ft.dropdown.Option("sibling", "Sibling"),
                ft.dropdown.Option("friend", "Friend"),
                ft.dropdown.Option("other", "Other"),
            ],
            label="Relationship"
        )

        # Bank Details Section
        bank_name = ft.TextField(label="Bank Name", width=250)
        account_number = ft.TextField(label="Account Number", width=200)
        ifsc_code = ft.TextField(label="IFSC Code", width=150)
        branch_name = ft.TextField(label="Branch", width=200)

        # Salary Info Section
        basic_salary = ft.TextField(label="Basic Salary", width=150, value="0")
        allowance = ft.TextField(label="Allowances", width=150, value="0")
        deduction = ft.TextField(label="Deductions", width=150, value="0")

        # Employment Info Section
        dept_options = [ft.dropdown.Option(
            key=str(d.id), text=d.name) for d in departments]
        dept_dropdown = ft.Dropdown(width=200, options=dept_options, label="Department",
                                    value=str(departments[0].id) if departments else None)

        pos_options = [ft.dropdown.Option(
            key=str(p.id), text=p.title) for p in positions]
        pos_dropdown = ft.Dropdown(width=200, options=pos_options, label="Position",
                                   value=str(positions[0].id) if positions else None)

        role_options = [ft.dropdown.Option(
            key=str(r.id), text=r.name) for r in roles]
        role_dropdown = ft.Dropdown(width=200, options=role_options, label="Role",
                                    value=str(roles[1].id) if len(roles) > 1 else None)

        employment_type = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("full_time", "Full-time"),
                ft.dropdown.Option("part_time", "Part-time"),
                ft.dropdown.Option("contract", "Contract"),
                ft.dropdown.Option("intern", "Intern"),
            ],
            label="Employment Type",
            value="full_time"
        )

        employment_status = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("active", "Active"),
                ft.dropdown.Option("on_probation", "On Probation"),
                ft.dropdown.Option("inactive", "Inactive"),
            ],
            label="Employment Status",
            value="active"
        )

        # Date picker for Date of Joining
        date_of_joining_picker = DatePickerField(
            label="Date of Joining", width=200)
        date_of_joining_picker._page = self._page

        # User Credentials Section
        username = ft.TextField(label="Username *", width=200)

        # Password field with show/hide toggle
        password = ft.TextField(label="Password *", width=170, password=True)
        password_toggle = ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            on_click=lambda e: self._toggle_password_visibility(
                password, password_toggle),
            tooltip="Show/Hide password"
        )

        def auto_generate_credentials(e):
            if first_name.value:
                gen_username = self._generate_username(
                    first_name.value, last_name.value if last_name.value else "")
                db = None
                try:
                    db = get_db_session()
                    existing_user = db.query(User).filter(
                        User.username == gen_username).first()
                    if existing_user:
                        gen_username = f"{gen_username}{random.randint(1, 99)}"
                except Exception as e:
                    print(f"Warning: Could not check username uniqueness: {e}")
                finally:
                    if db:
                        db.close()
                username.value = gen_username
                password.value = self._generate_password()
                # Show password temporarily after auto-generation
                password.password = False
                password_toggle.icon = ft.Icons.VISIBILITY
                self._page.update()

        auto_gen_btn = ft.TextButton(
            "Auto-Generate", on_click=auto_generate_credentials)

        error_text = ft.Text(color="#F44336", size=12, visible=False)

        def save_employee(e):
            # Get values first
            first_name_val = first_name.value.strip() if first_name.value else ""
            last_name_val = last_name.value.strip() if last_name.value else ""
            email_val = email.value.strip() if email.value else ""
            username_val = username.value.strip() if username.value else ""
            password_val = password.value.strip() if password.value else ""

            # Validate required fields
            if not first_name_val:
                error_text.value = "First Name is required!"
                error_text.visible = True
                self._page.update()
                return

            if not last_name_val:
                error_text.value = "Last Name is required!"
                error_text.visible = True
                self._page.update()
                return

            if not email_val:
                error_text.value = "Email is required!"
                error_text.visible = True
                self._page.update()
                return

            if not username_val:
                error_text.value = "Username is required!"
                error_text.visible = True
                self._page.update()
                return

            if not password_val:
                error_text.value = "Password is required!"
                error_text.visible = True
                self._page.update()
                return

            # Validate email format
            if '@' not in email_val or '.' not in email_val:
                error_text.value = "Please enter a valid email address!"
                error_text.visible = True
                self._page.update()
                return

            db = None
            try:
                db = get_db_session()

                # Check for duplicate username
                existing_user = db.query(User).filter(
                    User.username == username_val).first()
                if existing_user:
                    error_text.value = "Username already exists!"
                    error_text.visible = True
                    self._page.update()
                    return

                # Check for duplicate email
                existing_email = db.query(User).filter(
                    User.email == email_val).first()
                if existing_email:
                    error_text.value = "Email already registered!"
                    error_text.visible = True
                    self._page.update()
                    return

                # Hash password
                hashed_pw = bcrypt.hashpw(
                    password_val.encode(), bcrypt.gensalt()).decode()

                # Get role_id
                role_id = 2
                if role_dropdown.value:
                    try:
                        role_id = int(role_dropdown.value)
                    except (ValueError, TypeError) as e:
                        print(
                            f"Warning: Invalid role value '{role_dropdown.value}', using default: {e}")

                # Create user
                new_user = User(
                    username=username_val,
                    email=email_val,
                    password_hash=hashed_pw,
                    role_id=role_id
                )
                db.add(new_user)
                db.flush()  # Get the user ID

                # Get next employee code
                max_id = db.query(func.max(Employee.id)).scalar() or 0
                emp_code = f"EMP{max_id + 1:03d}"

                # Get department and position IDs
                dept_id = None
                if dept_dropdown.value:
                    try:
                        dept_id = int(dept_dropdown.value)
                    except (ValueError, TypeError) as e:
                        print(
                            f"Warning: Invalid department value '{dept_dropdown.value}': {e}")

                pos_id = None
                if pos_dropdown.value:
                    try:
                        pos_id = int(pos_dropdown.value)
                    except (ValueError, TypeError) as e:
                        print(
                            f"Warning: Invalid position value '{pos_dropdown.value}': {e}")

                # Get values
                dob_value = dob_picker.value if dob_picker.value else None
                doj_value = date_of_joining_picker.value if date_of_joining_picker.value else None
                emp_type = employment_type.value if employment_type.value else 'full_time'
                emp_status = employment_status.value if employment_status.value else 'active'

                # Create employee
                new_employee = Employee(
                    employee_code=emp_code,
                    user_id=new_user.id,
                    first_name=first_name_val,
                    last_name=last_name_val,
                    email=email_val,
                    phone=phone.value.strip() if phone.value else None,
                    profile_photo=profile_photo.value.strip() if profile_photo.value else None,
                    date_of_birth=dob_value,
                    gender=gender.value,
                    address=address.value.strip() if address.value else None,
                    city=city.value.strip() if city.value else None,
                    state=state.value.strip() if state.value else None,
                    pincode=pincode.value.strip() if pincode.value else None,
                    emergency_contact_name=emergency_contact_name.value.strip(
                    ) if emergency_contact_name.value else None,
                    emergency_phone=emergency_phone.value.strip() if emergency_phone.value else None,
                    emergency_relation=emergency_relation.value,
                    bank_name=bank_name.value.strip() if bank_name.value else None,
                    account_number=account_number.value.strip() if account_number.value else None,
                    ifsc_code=ifsc_code.value.strip() if ifsc_code.value else None,
                    branch_name=branch_name.value.strip() if branch_name.value else None,
                    basic_salary=float(
                        basic_salary.value) if basic_salary.value and basic_salary.value.strip() else 0,
                    allowance=float(
                        allowance.value) if allowance.value and allowance.value.strip() else 0,
                    deduction=float(
                        deduction.value) if deduction.value and deduction.value.strip() else 0,
                    department_id=dept_id,
                    position_id=pos_id,
                    employment_type=emp_type,
                    employment_status=emp_status,
                    date_of_joining=doj_value,
                    is_active=True
                )
                db.add(new_employee)
                db.commit()

                self._close_dialog()
                self._show_success(
                    f"Employee '{first_name_val} {last_name_val}' created successfully!")
                self._refresh()

            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self._page.update()
                print(f"Save error: {ex}")
                if db:
                    db.rollback()
            finally:
                if db:
                    db.close()

        # Build form with scroll support
        tab_content = ft.Container(
            content=ft.Column([
                ft.Text("Personal Information", size=14,
                        weight=ft.FontWeight.BOLD, color="#2E86AB"),
                ft.Row([first_name, last_name], spacing=10),
                email, phone,
                # Add profile photo field with picker
                ft.Row([profile_photo, profile_pick_btn], spacing=5),
                ft.Row([dob_picker, gender], spacing=10),
                address,
                ft.Row([city, state, pincode], spacing=10),
                ft.Divider(),
                ft.Text("Emergency Contact", size=14,
                        weight=ft.FontWeight.BOLD, color="#D32F2F"),
                ft.Row([emergency_contact_name, emergency_phone], spacing=10),
                emergency_relation,
                ft.Divider(),
                ft.Text("Bank Details", size=14,
                        weight=ft.FontWeight.BOLD, color="#4CAF50"),
                ft.Row([bank_name, branch_name], spacing=10),
                ft.Row([account_number, ifsc_code], spacing=10),
                ft.Divider(),
                ft.Text("Salary Information", size=14,
                        weight=ft.FontWeight.BOLD, color="#FF9800"),
                ft.Row([basic_salary, allowance, deduction], spacing=10),
                ft.Divider(),
                ft.Text("Employment Details", size=14,
                        weight=ft.FontWeight.BOLD, color="#9C27B0"),
                ft.Row([dept_dropdown, pos_dropdown], spacing=10),
                ft.Row([role_dropdown, employment_type], spacing=10),
                ft.Row([employment_status, date_of_joining_picker], spacing=10),
                ft.Divider(),
                ft.Text("System Access", size=14,
                        weight=ft.FontWeight.BOLD, color="#607D8B"),
                ft.Row([username, password, password_toggle,
                       auto_gen_btn], spacing=5),
                error_text,
            ], spacing=5, scroll=ft.ScrollMode.AUTO),
            height=420,  # Fixed height for scrollable content
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add New Employee"),
            content=ft.Column([
                tab_content,
                ft.Container(height=10),  # Spacing
            ], spacing=0),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Save Employee", on_click=save_employee,
                                  style=ft.ButtonStyle(bgcolor="#4CAF50", color="WHITE"))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_edit_dialog(self, emp_id: int):
        """Show edit dialog using PostgreSQL"""
        from sqlalchemy.orm import joinedload

        db = None
        try:
            db = get_db_session()
            # Query employee with relationships
            emp = db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            ).filter(Employee.id == emp_id).first()

            if not emp:
                self._show_error("Employee not found!")
                return

            departments = db.query(Department).all()
            positions = db.query(Position).all()
            roles = db.query(Role).all()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if db:
                db.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        # Edit form fields - use attribute access for SQLAlchemy objects
        first_name = ft.TextField(
            label="First Name *", width=200, value=emp.first_name or "")
        last_name = ft.TextField(
            label="Last Name *", width=200, value=emp.last_name or "")
        email = ft.TextField(label="Email *", width=420,
                             value=emp.email or "")
        phone = ft.TextField(label="Phone", width=200,
                             value=emp.phone or "")

        # Profile Photo Section - Add file picker for edit
        profile_photo = ft.TextField(
            label="Profile Photo URL", width=320,
            value=emp.profile_photo or "",
            hint_text="Enter image URL or file path"
        )

        # File picker button for profile photo in edit
        profile_photo_path = [
            emp.profile_photo] if emp.profile_photo else [None]

        def pick_profile_photo_edit(e):
            """Pick profile photo using file picker and upload to Supabase"""
            self._init_file_picker()

            async def pick_and_set():
                try:
                    files = await self._file_picker.pick_files(
                        dialog_title="Choose Profile Photo",
                        file_type=ft.FilePickerFileType.IMAGE,
                    )
                    if files and files[0]:
                        path = files[0].path
                        profile_photo_path[0] = path

                        # Upload to Supabase Storage for multi-device access
                        try:
                            success, file_url, bucket_path = upload_to_supabase(
                                file_path=path,
                                folder="profiles",
                                custom_filename=os.path.basename(path)
                            )
                            if success and file_url:
                                # Save the Supabase URL instead of local path
                                profile_photo.value = file_url
                                print(f"Profile photo uploaded: {file_url}")
                            else:
                                # Fallback to local path if upload fails
                                profile_photo.value = path
                                print(
                                    f"Profile photo upload failed, using local path: {path}")
                        except Exception as upload_err:
                            print(
                                f"Error uploading profile photo: {upload_err}")
                            # Fallback to local path
                            profile_photo.value = path
                            self._show_error(
                                f"Upload failed: {str(upload_err)}")

                        self._page.update()
                except Exception as ex:
                    print(f"Error picking file: {ex}")
                    self._show_error(f"Error selecting file: {str(ex)}")

            self._page.run_task(pick_and_set)

        profile_pick_btn = ft.IconButton(
            icon=ft.Icons.IMAGE,
            tooltip="Browse for image",
            on_click=pick_profile_photo_edit
        )

        # Date pickers with values
        dob_picker = DatePickerField(label="Date of Birth", width=200)
        dob_picker._page = self._page
        if emp.date_of_birth:
            dob_picker.value = str(emp.date_of_birth)

        gender = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("MALE", "Male"),
                ft.dropdown.Option("FEMALE", "Female"),
                ft.dropdown.Option("OTHER", "Other"),
            ],
            label="Gender",
            value=(emp.gender.upper() if emp.gender
                   else "MALE") if emp.gender else "MALE"
        )
        address = ft.TextField(label="Address", width=420,
                               value=emp.address or "", multiline=True)
        city = ft.TextField(label="City", width=200, value=emp.city or "")
        state = ft.TextField(label="State", width=200,
                             value=emp.state or "")
        pincode = ft.TextField(label="Pincode", width=100,
                               value=emp.pincode or "")

        dept_options = [ft.dropdown.Option(
            key=str(d.id), text=d.name) for d in departments]
        dept_dropdown = ft.Dropdown(width=200, options=dept_options, label="Department",
                                    value=str(emp.department_id) if emp.department_id else None)

        pos_options = [ft.dropdown.Option(
            key=str(p.id), text=p.title) for p in positions]
        pos_dropdown = ft.Dropdown(width=200, options=pos_options, label="Position",
                                   value=str(emp.position_id) if emp.position_id else None)

        employment_type = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("full_time", "Full-time"),
                ft.dropdown.Option("part_time", "Part-time"),
                ft.dropdown.Option("contract", "Contract"),
                ft.dropdown.Option("intern", "Intern"),
            ],
            label="Employment Type",
            value=emp.employment_type or "full_time"
        )

        employment_status = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("active", "Active"),
                ft.dropdown.Option("on_probation", "On Probation"),
                ft.dropdown.Option("inactive", "Inactive"),
            ],
            label="Employment Status",
            value=emp.employment_status or "active"
        )

        # Date picker for Date of Joining
        date_of_joining_picker = DatePickerField(
            label="Date of Joining", width=200)
        date_of_joining_picker._page = self._page
        if emp.date_of_joining:
            date_of_joining_picker.value = str(emp.date_of_joining)

        bank_name = ft.TextField(
            label="Bank Name", width=250, value=emp.bank_name or "")
        account_number = ft.TextField(
            label="Account Number", width=200, value=emp.account_number or "")
        ifsc_code = ft.TextField(
            label="IFSC Code", width=150, value=emp.ifsc_code or "")
        branch_name = ft.TextField(
            label="Branch", width=200, value=emp.branch_name or "")

        basic_salary = ft.TextField(
            label="Basic Salary", width=150, value=str(emp.basic_salary or 0))
        allowance = ft.TextField(
            label="Allowances", width=150, value=str(emp.allowance or 0))
        deduction = ft.TextField(
            label="Deductions", width=150, value=str(emp.deduction or 0))

        status_switch = ft.Switch(label="Active", value=bool(emp.is_active))

        def update_employee(e):
            """Update employee using PostgreSQL"""
            db = None
            try:
                db = get_db_session()

                # Get employee from PostgreSQL
                emp_to_update = db.query(Employee).filter(
                    Employee.id == emp_id).first()
                if not emp_to_update:
                    self._show_error("Employee not found!")
                    return

                # Update employee fields
                emp_to_update.first_name = first_name.value.strip() if first_name.value else ""
                emp_to_update.last_name = last_name.value.strip() if last_name.value else ""
                emp_to_update.email = email.value.strip() if email.value else ""

                emp_to_update.phone = phone.value.strip() if phone.value else None

                # Update profile photo - handle both setting and clearing
                profile_photo_value = profile_photo.value.strip() if profile_photo.value else None
                emp_to_update.profile_photo = profile_photo_value

                # Handle dates
                if dob_picker.value:
                    emp_to_update.date_of_birth = dob_picker.value
                if date_of_joining_picker.value:
                    emp_to_update.date_of_joining = date_of_joining_picker.value

                emp_to_update.gender = gender.value
                emp_to_update.address = address.value.strip() if address.value else None
                emp_to_update.city = city.value.strip() if city.value else None
                emp_to_update.state = state.value.strip() if state.value else None
                emp_to_update.pincode = pincode.value.strip() if pincode.value else None

                # Bank details
                emp_to_update.bank_name = bank_name.value.strip() if bank_name.value else None
                emp_to_update.account_number = account_number.value.strip(
                ) if account_number.value else None
                emp_to_update.ifsc_code = ifsc_code.value.strip() if ifsc_code.value else None
                emp_to_update.branch_name = branch_name.value.strip() if branch_name.value else None

                # Salary
                emp_to_update.basic_salary = float(
                    basic_salary.value) if basic_salary.value else 0
                emp_to_update.allowance = float(
                    allowance.value) if allowance.value else 0
                emp_to_update.deduction = float(
                    deduction.value) if deduction.value else 0

                # Employment details
                emp_to_update.department_id = int(
                    dept_dropdown.value) if dept_dropdown.value else None
                emp_to_update.position_id = int(
                    pos_dropdown.value) if pos_dropdown.value else None
                emp_to_update.employment_type = employment_type.value
                emp_to_update.employment_status = employment_status.value
                emp_to_update.is_active = status_switch.value

                db.commit()
                self._close_dialog()
                self._show_success("Employee updated successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
                if db:
                    db.rollback()
            finally:
                if db:
                    db.close()

        tab_content = ft.Column([
            ft.Text("Personal Information", size=14,
                    weight=ft.FontWeight.BOLD, color="#2E86AB"),
            ft.Row([first_name, last_name], spacing=10),
            email, phone,
            # Add profile photo field with picker in edit dialog
            ft.Row([profile_photo, profile_pick_btn], spacing=5),
            ft.Row([dob_picker, gender], spacing=10),
            address,
            ft.Row([city, state, pincode], spacing=10),
            ft.Divider(),
            ft.Text("Employment Details", size=14,
                    weight=ft.FontWeight.BOLD, color="#9C27B0"),
            ft.Row([dept_dropdown, pos_dropdown], spacing=10),
            ft.Row([employment_type, employment_status], spacing=10),
            date_of_joining_picker,
            ft.Divider(),
            ft.Text("Bank Details", size=14,
                    weight=ft.FontWeight.BOLD, color="#4CAF50"),
            ft.Row([bank_name, branch_name], spacing=10),
            ft.Row([account_number, ifsc_code], spacing=10),
            ft.Divider(),
            ft.Text("Salary Information", size=14,
                    weight=ft.FontWeight.BOLD, color="#FF9800"),
            ft.Row([basic_salary, allowance, deduction], spacing=10),
            ft.Divider(),
            status_switch,
            ft.Container(height=20),  # Extra space at bottom
        ], spacing=5, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Employee"),
            content=ft.Container(
                content=tab_content,
                width=520,
                height=500,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Update", on_click=update_employee,
                                  style=ft.ButtonStyle(bgcolor="#1976D2", color="WHITE"))
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_details_dialog(self, emp_id: int):
        """Show full employee details using PostgreSQL"""
        from sqlalchemy.orm import joinedload

        db = None
        try:
            db = get_db_session()
            # Query employee with relationships
            emp = db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            ).filter(Employee.id == emp_id).first()

            if not emp:
                self._show_error("Employee not found!")
                return

            # Get related user for username
            user = None
            if emp.user_id:
                user = db.query(User).filter(User.id == emp.user_id).first()

            # Get role name
            role_name = "Employee"
            if user and user.role_id:
                role = db.query(Role).filter(Role.id == user.role_id).first()
                if role:
                    role_name = role.name

        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if db:
                db.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        total_salary = (emp.basic_salary or 0) + \
            (emp.allowance or 0) - (emp.deduction or 0)

        # Get department and position names
        dept_name = emp.department.name if emp.department else "General"
        pos_title = emp.position.title if emp.position else "Employee"
        username = user.username if user else "-"

        def create_detail_row(label, value):
            return ft.Row([
                ft.Text(label, size=12, color="#757575", width=150),
                ft.Text(str(value) if value else "-",
                        size=13, weight=ft.FontWeight.W_500)
            ], spacing=10)

        details = ft.Column([
            ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(f"{emp.first_name or ''} {emp.last_name or ''}",
                                    size=20, weight=ft.FontWeight.BOLD, color="#2E86AB"),
                            ft.Text(
                                f"Employee Code: {emp.employee_code or 'N/A'}", size=12, color="#757575"),
                        ]),
                        ft.Container(expand=True),
                        ft.Container(
                            bgcolor="#4CAF50" if emp.is_active else "#F44336",
                            padding=padding.all(10),
                            border_radius=8,
                            content=ft.Text(
                                (emp.employment_status or 'Active').replace(
                                    '_', ' ').title(),
                                color="WHITE", weight=ft.FontWeight.BOLD
                            )
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Text("Personal Details", size=14,
                            weight=ft.FontWeight.BOLD, color="#2E86AB"),
                    create_detail_row("Email:", emp.email),
                    create_detail_row("Phone:", emp.phone),
                    create_detail_row("Date of Birth:", emp.date_of_birth),
                    create_detail_row(
                        "Gender:", emp.gender.title() if emp.gender else "-"),
                    create_detail_row("Address:", emp.address),
                    create_detail_row("City:", emp.city),
                    ft.Divider(),
                    ft.Text("Employment Details", size=14,
                            weight=ft.FontWeight.BOLD, color="#2E86AB"),
                    create_detail_row("Department:", dept_name),
                    create_detail_row("Position:", pos_title),
                    create_detail_row(
                        "Employment Type:", (emp.employment_type or 'Full-time').replace('_', ' ').title()),
                    create_detail_row("Date of Joining:",
                                      emp.date_of_joining),
                    create_detail_row("Username:", username),
                    create_detail_row("Role:", role_name),
                    ft.Divider(),
                    ft.Text("Emergency Contact", size=14,
                            weight=ft.FontWeight.BOLD, color="#D32F2F"),
                    create_detail_row("Name:", emp.emergency_contact_name),
                    create_detail_row("Phone:", emp.emergency_phone),
                    create_detail_row(
                        "Relationship:", emp.emergency_relation),
                    ft.Divider(),
                    ft.Text("Bank Details", size=14,
                            weight=ft.FontWeight.BOLD, color="#4CAF50"),
                    create_detail_row("Bank:", emp.bank_name),
                    create_detail_row("Account:", emp.account_number),
                    create_detail_row("IFSC:", emp.ifsc_code),
                    ft.Divider(),
                    ft.Text("Salary Information", size=14,
                            weight=ft.FontWeight.BOLD, color="#FF9800"),
                    create_detail_row(
                        "Basic:", f"Rs.{emp.basic_salary or 0:,.2f}"),
                    create_detail_row(
                        "Allowances:", f"Rs.{emp.allowance or 0:,.2f}"),
                    create_detail_row(
                        "Deductions:", f"Rs.{emp.deduction or 0:,.2f}"),
                    ft.Row([
                        ft.Text("Total:", size=12, color="#757575", width=150),
                        ft.Text(f"Rs.{total_salary:,.2f}", size=16,
                                weight=ft.FontWeight.BOLD, color="#4CAF50"),
                    ], spacing=10),
                ], spacing=5),
                padding=20,
            ),
        ], scroll=ft.ScrollMode.AUTO, spacing=0)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Employee Details - {emp.employee_code}"),
            content=ft.Container(content=details, height=500, width=550),
            actions=[
                ft.ElevatedButton("ID Card", on_click=lambda e, emp_id=emp_id: self._generate_id_card_dialog(emp_id),
                                  style=ft.ButtonStyle(bgcolor="#FF9800", color="WHITE")),
                ft.ElevatedButton("Offer Letter", on_click=lambda e, emp_id=emp_id: self._generate_offer_letter_dialog(emp_id),
                                  style=ft.ButtonStyle(bgcolor="#9C27B0", color="WHITE")),
                ft.ElevatedButton("Salary Slip", on_click=lambda e, emp_id=emp_id: self._generate_salary_slip_dialog(emp_id),
                                  style=ft.ButtonStyle(bgcolor="#2196F3", color="WHITE")),
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _generate_id_card_dialog(self, emp_id: int):
        """Generate ID Card dialog using PostgreSQL"""
        from sqlalchemy.orm import joinedload

        db = None
        try:
            db = get_db_session()
            # Query employee with relationships
            emp = db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            ).filter(Employee.id == emp_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if db:
                db.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        # Get department and position names
        dept_name = emp.department.name if emp.department else "General"
        pos_title = emp.position.title if emp.position else "Employee"

        # Get profile photo if available - check multiple locations
        profile_photo_url = emp.profile_photo if emp.profile_photo else None

        # Try to resolve profile photo path similar to profile_screen.py
        if profile_photo_url and not profile_photo_url.startswith('http'):
            import os
            from pathlib import Path

            # Check if path exists as-is
            if not os.path.exists(profile_photo_url):
                # Try relative to assets/profile_photos directory
                base_dir = Path(__file__).parent.parent
                basename = os.path.basename(profile_photo_url)
                assets_path = base_dir / "assets" / "profile_photos" / basename
                if assets_path.exists():
                    profile_photo_url = str(assets_path)
                else:
                    # Profile photo file doesn't exist - set to None
                    profile_photo_url = None

        # Create photo container - show profile photo if available
        if profile_photo_url:
            photo_content = ft.Image(
                src=profile_photo_url,
                width=70,
                height=90,
                fit=ft.BoxFit.COVER,
            )
        else:
            photo_content = ft.Column([
                ft.Icon(ft.Icons.PERSON, size=40,
                        color="#2E86AB"),
                ft.Text("PHOTO", size=9, color="#757575"),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # Employee full name
        emp_name = f"{emp.first_name or ''} {emp.last_name or ''}".strip()

        id_card = ft.Container(
            width=400,
            height=250,
            bgcolor="white",
            border=ft.border.all(3, "#2E86AB"),
            border_radius=12,
            content=ft.Column([
                # Header
                ft.Container(
                    bgcolor="#2E86AB",
                    padding=padding.all(10),
                    content=ft.Row([
                        ft.Container(
                            width=30,
                            height=30,
                            bgcolor="white",
                            border_radius=4,
                            content=ft.Icon(
                                ft.Icons.BADGE, color="#2E86AB", size=24)
                        ),
                        ft.Column([
                            ft.Text("VERNIKA TECHNOLOGIES", size=14,
                                    color="WHITE", weight=ft.FontWeight.BOLD),
                            ft.Text("Employee Identity Card",
                                    size=9, color="WHITE"),
                        ], expand=True, spacing=0),
                    ], spacing=10)
                ),
                # Body
                ft.Container(
                    padding=15,
                    content=ft.Row([
                        # Photo
                        ft.Container(
                            width=80,
                            height=95,
                            bgcolor="#E3F2FD",
                            border_radius=8,
                            border=ft.border.all(1, "#2E86AB"),
                            content=photo_content
                        ),
                        # Details
                        ft.Column([
                            ft.Text(emp_name or "Employee",
                                    size=15, weight=ft.FontWeight.BOLD, color="#1A1C1E"),
                            ft.Container(
                                content=ft.Text(
                                    pos_title or "Employee", size=10, color="WHITE", weight=ft.FontWeight.W_600),
                                bgcolor="#2E86AB",
                                padding=ft.padding.symmetric(
                                    horizontal=8, vertical=2),
                                border_radius=3,
                            ),
                            ft.Container(height=5),
                            ft.Text(
                                f"Dept: {dept_name}", size=11, color="#333333", weight=ft.FontWeight.W_500),
                            ft.Text(f"ID: {emp.employee_code or 'N/A'}",
                                    size=11, weight=ft.FontWeight.BOLD, color="#2E86AB"),
                        ], spacing=3, expand=True)
                    ], spacing=15, alignment=ft.MainAxisAlignment.START)
                ),
                # Footer
                ft.Container(
                    bgcolor="#F5F5F5",
                    padding=padding.all(8),
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.EMAIL, size=12,
                                        color="#1A1C1E"),
                                ft.Text(emp.email or '-', size=9,
                                        color="#1A1C1E", weight=ft.FontWeight.W_500),
                            ], spacing=3),
                            ft.Row([
                                ft.Icon(ft.Icons.PHONE, size=12,
                                        color="#1A1C1E"),
                                ft.Text(emp.phone or '-', size=9,
                                        color="#1A1C1E", weight=ft.FontWeight.W_500),
                            ], spacing=3),
                        ], spacing=2),
                        ft.Container(expand=True),
                        ft.Column([
                            ft.Text(f"Valid Till: Dec {datetime.now().year + 1}",
                                    size=9, color="#D32F2F", weight=ft.FontWeight.W_500),
                            ft.Text("Authorized Signature",
                                    size=8, color="#666666"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=0),
                    ], spacing=5)
                )
            ], spacing=0)
        )

        # Download function for ID Card
        def download_id_card(e):
            try:
                import io
                import os
                from reportlab.lib.pagesizes import landscape
                from reportlab.lib import colors
                from reportlab.pdfgen import canvas
                from reportlab.lib.units import inch, mm
                from reportlab.lib.utils import ImageReader
                try:
                    from PIL import Image
                except ImportError:
                    Image = None

                # CR80 Card Size: 3.375" x 2.125" (standard ID card)
                CARD_WIDTH = 3.375 * inch
                CARD_HEIGHT = 2.125 * inch

                # Create PDF with card size (landscape for better fit)
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=(CARD_WIDTH, CARD_HEIGHT))
                width = CARD_WIDTH
                height = CARD_HEIGHT

                # Background
                c.setFillColor(colors.white)
                c.rect(0, 0, width, height, fill=True)

                # Card Border - rounded corners simulation
                c.setStrokeColor(colors.HexColor("#2E86AB"))
                c.setLineWidth(3)
                c.rect(2, 2, width - 4, height - 4)

                # Header - Blue background with rounded corners
                header_height = 38
                c.setFillColor(colors.HexColor("#2E86AB"))
                c.roundRect(2, height - header_height, width - 4,
                            header_height, 6, fill=True, stroke=False)

                # Company Logo - fixed path to go up 2 directories from screens/
                import os
                project_root = os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__)))
                logo_path = os.path.join(
                    project_root, "assets", "logo", "Vernikalogo.png")
                logo_x = 8
                logo_y = height - header_height + 6
                logo_size = 22

                if os.path.exists(logo_path):
                    try:
                        c.drawImage(logo_path, logo_x, logo_y,
                                    width=logo_size, height=logo_size, mask='auto')
                    except Exception as e:
                        print(f"Logo load error: {e}")

                # Company Name in Header
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 11)
                c.drawString(logo_x + logo_size + 6, height -
                             16, "VERNIKA TECHNOLOGIES")
                c.setFont("Helvetica", 6)
                c.drawString(logo_x + logo_size + 6, height -
                             23, "Employee Identity Card")

                # Employee Photo Section - improved positioning
                photo_x = 10
                photo_y = height - header_height - 60
                photo_width = 50
                photo_height = 55

                # Photo background with border
                c.setFillColor(colors.HexColor("#E3F2FD"))
                c.setStrokeColor(colors.HexColor("#2E86AB"))
                c.setLineWidth(1)

                photo_loaded = False
                if profile_photo_url:
                    if Image:
                        try:
                            import urllib.request
                            from io import BytesIO
                            headers = {'User-Agent': 'Mozilla/5.0'}
                            req = urllib.request.Request(
                                profile_photo_url, headers=headers)
                            with urllib.request.urlopen(req, timeout=10) as response:
                                img_data = response.read()
                            img = Image.open(BytesIO(img_data))
                            img = img.convert('RGB')
                            # Save to temp buffer
                            temp_buf = BytesIO()
                            img.save(temp_buf, format='JPEG')
                            temp_buf.seek(0)
                            c.drawImage(ImageReader(temp_buf), photo_x + 2, photo_y + 2,
                                        width=photo_width - 4, height=photo_height - 4, mask='auto')
                            photo_loaded = True
                        except Exception as img_err:
                            # Skip logging for macOS Photos temporary files - they expire and are not accessible
                            temp_path_indicators = [
                                'TemporaryItems', 'NSItemProvider', 'Photos']
                            is_temp_photo = any(indicator in str(
                                profile_photo_url) for indicator in temp_path_indicators)
                            if not is_temp_photo:
                                print(f"URL image load error: {img_err}")
                            # Fallback: try as local file path
                            try:
                                local_path = profile_photo_url
                                # Check if it's a local path (starts with / or contains path separators)
                                if local_path and (local_path.startswith('/') or '\\' in local_path):
                                    if os.path.exists(local_path):
                                        c.drawImage(local_path, photo_x + 2, photo_y + 2,
                                                    width=photo_width - 4, height=photo_height - 4, mask='auto')
                                        photo_loaded = True
                                    else:
                                        # Try relative path from project root
                                        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                                                 local_path.lstrip('/'))
                                        if os.path.exists(full_path):
                                            c.drawImage(full_path, photo_x + 2, photo_y + 2,
                                                        width=photo_width - 4, height=photo_height - 4, mask='auto')
                                            photo_loaded = True
                            except Exception as draw_err:
                                # Only print local file errors for non-temp paths
                                if not is_temp_photo:
                                    print(f"Local file draw error: {draw_err}")
                    elif os.path.exists(profile_photo_url):
                        c.drawImage(profile_photo_url, photo_x + 2, photo_y + 2,
                                    width=photo_width - 4, height=photo_height - 4, mask='auto')
                        photo_loaded = True
                    else:
                        # Try as relative path from project root
                        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                                 profile_photo_url.lstrip('/'))
                        if os.path.exists(full_path):
                            c.drawImage(full_path, photo_x + 2, photo_y + 2,
                                        width=photo_width - 4, height=photo_height - 4, mask='auto')
                            photo_loaded = True

                if not photo_loaded:
                    # Draw placeholder icon
                    c.setFillColor(colors.HexColor("#2E86AB"))
                    c.setFont("Helvetica", 18)
                    c.drawCentredString(
                        photo_x + photo_width/2, photo_y + photo_height/2, "?")

                # Employee Details Section - improved positioning
                details_x = photo_x + photo_width + 8
                details_start_y = height - header_height - 8

                # Name - truncated if needed
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                name = emp_name if emp_name else "Employee"
                if len(name) > 22:
                    name = name[:22]
                c.drawString(details_x, details_start_y, name)

                # Position - with background
                pos_text = (pos_title or "Employee")[:20]
                c.setFillColor(colors.HexColor("#2E86AB"))
                c.rect(details_x, details_start_y - 12, 65, 11, fill=True)
                c.setFillColor(colors.white)
                c.setFont("Helvetica", 6)
                c.drawString(details_x + 2, details_start_y - 5, pos_text)

                # Employee Code
                c.setFillColor(colors.HexColor("#2E86AB"))
                c.setFont("Helvetica-Bold", 8)
                emp_code = emp.employee_code or f"EMP{emp_id}"
                c.drawString(details_x, details_start_y -
                             22, f"ID: {emp_code}")

                # Department
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 6)
                dept_text = (dept_name or "General")[:25]
                c.drawString(details_x, details_start_y -
                             30, f"Dept: {dept_text}")

                # Footer Section - improved
                footer_y = 18
                footer_height = 22

                c.setFillColor(colors.HexColor("#F5F5F5"))
                c.rect(0, footer_y - 2, width, footer_height, fill=True)

                # Email
                c.setFillColor(colors.HexColor("#1A1C1E"))
                c.setFont("Helvetica", 5)
                c.drawString(8, footer_y + 8, "Email:")
                c.setFont("Helvetica-Bold", 5)
                email_text = (emp.email or "-")[:30]
                c.drawString(22, footer_y + 8, email_text)

                # Phone
                c.setFont("Helvetica", 5)
                c.drawString(8, footer_y + 2, "Phone:")
                c.setFont("Helvetica-Bold", 5)
                phone_text = (emp.phone or "-")[:30]
                c.drawString(24, footer_y + 2, phone_text)

                # Valid Till
                valid_date = datetime.now().year + 1
                c.setFillColor(colors.HexColor("#D32F2F"))
                c.setFont("Helvetica-Bold", 5)
                c.drawRightString(width - 8, footer_y + 8,
                                  f"Valid Till: Dec {valid_date}")

                # Signature line
                c.setStrokeColor(colors.black)
                c.setLineWidth(0.5)
                c.line(width - 55, footer_y + 5, width - 15, footer_y + 5)
                c.setFont("Helvetica", 4)
                c.drawCentredString(width - 35, footer_y, "Authorized")

                # Save PDF
                c.save()
                buffer.seek(0)

                # Save to Downloads folder
                output_dir = os.path.expanduser("~/Downloads")
                os.makedirs(output_dir, exist_ok=True)
                filename = f"ID_Card_{emp.employee_code or emp_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'wb') as f:
                    f.write(buffer.read())

                self._show_success(f"ID Card saved to: {filepath}")

            except Exception as ex:
                print(f"Error generating PDF: {ex}")
                import traceback
                traceback.print_exc()
                self._show_error(f"Error generating PDF: {str(ex)}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Employee ID Card"),
            content=ft.Container(
                content=ft.ListView([
                    id_card
                ], spacing=0, padding=0, expand=True),
                width=400,
                height=250,
            ),
            actions=[
                ft.ElevatedButton(
                    "Download ID Card",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=download_id_card,
                    style=ft.ButtonStyle(bgcolor="#FF9800", color="WHITE")
                ),
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self):
        """Close all open dialogs"""
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _refresh(self):
        """Refresh the employee list"""
        self.content = self._build_content()
        self._page.update()

    def _show_success(self, msg):
        """Show success message"""
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#4CAF50")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        """Show error message"""
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#F44336")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _toggle_password_visibility(self, password_field, toggle_icon):
        """Toggle password visibility"""
        if password_field.password:
            password_field.password = False
            toggle_icon.icon = ft.Icons.VISIBILITY
        else:
            password_field.password = True
            toggle_icon.icon = ft.Icons.VISIBILITY_OFF
        self._page.update()

    def _manage_access_dialog(self, emp_id: int, user_id: int):
        """Show dialog to manage screen access for an employee"""
        from utils.screen_access import (
            SCREEN_ACCESS_CONFIG,
            get_user_screen_access,
            set_screen_access,
            reset_to_defaults
        )

        # Get current access
        current_access = get_user_screen_access(user_id)

        # Get employee name
        emp_name = f"Employee #{emp_id}"
        db = None
        try:
            db = get_db_session()
            emp = db.query(Employee).filter(Employee.id == emp_id).first()
            if emp:
                emp_name = f"{emp.first_name or ''} {emp.last_name or ''}".strip(
                ) or emp_name
        except Exception as e:
            print(f"Error getting employee name: {e}")
        finally:
            if db:
                db.close()

        # Create access cards
        access_controls = {}

        for screen_key, config in SCREEN_ACCESS_CONFIG.items():
            is_enabled = current_access.get(screen_key, False)

            switch = ft.Switch(
                value=is_enabled,
                active_color="#2E86AB",
                disabled=(screen_key == 'profile'),  # Profile always enabled
            )

            def make_handler(uk, sk, sw, conf):
                def handler(e):
                    admin_id = self.user.get('id') if isinstance(
                        self.user, dict) else None
                    set_screen_access(uk, sk, sw.value, granted_by=admin_id)
                    self._show_success(f"Updated {conf['name']} access")
                return handler

            switch.on_change = make_handler(
                user_id, screen_key, switch, config)
            access_controls[screen_key] = switch

        # Build content
        content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SECURITY, size=24, color="#2E86AB"),
                ft.Text(f"Screen Access for {emp_name}",
                        size=18, weight=ft.FontWeight.BOLD),
            ]),
            ft.Container(height=10),
            ft.Text("Manage which screens this employee can access:",
                    size=12, color="#757575"),
            ft.Divider(),
            ft.Container(height=10),
        ])

        for screen_key, config in SCREEN_ACCESS_CONFIG.items():
            content.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(config["name"], size=14,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(config["description"],
                                    size=11, color="#757575"),
                        ], expand=True),
                        access_controls[screen_key],
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#F5F5F5" if screen_key != "profile" else "#E3F2FD",
                    border_radius=8,
                    margin=5,
                )
            )

        content.controls.extend([
            ft.Container(height=20),
            ft.Row([
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Reset to Defaults",
                    icon=ft.Icons.RESTART_ALT,
                    on_click=lambda e: (reset_to_defaults(
                        user_id), self._close_dialog(), self._refresh()),
                    style=ft.ButtonStyle(bgcolor="#FFC107", color="white"),
                ),
            ]),
        ])

        dialog = ft.AlertDialog(
            title=ft.Text("Manage Screen Access"),
            content=ft.Container(
                content=ft.Column([
                    content
                ], scroll=ft.ScrollMode.AUTO),
                width=500,
                height=450,
            ),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.dialog = dialog
        dialog.open = True
        self._page.update()

    def _generate_offer_letter_dialog(self, emp_id: int):
        """Generate Offer Letter dialog using PostgreSQL - Professional Industry Standard Format"""
        from sqlalchemy.orm import joinedload

        db = None
        try:
            db = get_db_session()
            # Query employee with relationships
            emp = db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            ).filter(Employee.id == emp_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if db:
                db.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        # Get department and position names
        dept_name = emp.department.name if emp.department else "General"
        pos_title = emp.position.title if emp.position else "Employee"

        # Calculate salary details
        basic = emp.basic_salary or 0
        hra = basic * 0.40 if basic > 0 else 0  # 40% of basic as HRA
        conv = basic * 0.10 if basic > 0 else 0   # 10% as conveyance
        medical = 1250 if basic > 0 else 0         # Fixed medical allowance
        special = basic * 0.10 if basic > 0 else 0  # 10% as special allowance
        pf = basic * 0.12 if basic > 0 else 0     # 12% as PF
        pt = 200                                    # Professional Tax
        gross_salary = basic + hra + conv + medical + special
        net_salary = gross_salary - pf - pt

        # Format dates
        current_date = datetime.now().strftime('%d-%m-%Y')
        doj = datetime.strptime(str(emp.date_of_joining), '%Y-%m-%d').strftime(
            '%d-%m-%Y') if emp.date_of_joining else 'To be decided'

        # Employment type formatting
        emp_type = (
            emp.employment_type or 'Full-time').replace('_', ' ').title()

        # Employee name
        emp_name = f"{emp.first_name or ''} {emp.last_name or ''}".strip()

        # Build the offer letter preview
        offer_letter = ft.Container(
            width=680,
            height=900,
            bgcolor="white",
            content=ft.Column([
                # Company Header
                ft.Container(
                    bgcolor="#1A237E",
                    padding=padding.all(20),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.BUSINESS, color="WHITE", size=36),
                            ft.Column([
                                ft.Text("VERNIKA TECHNOLOGIES", size=22,
                                        color="WHITE", weight=ft.FontWeight.BOLD),
                                ft.Text("Registered Office: India",
                                        size=11, color="WHITE"),
                                ft.Text(
                                    "CIN: U72900XX2024PTC123456 | GST: 22ABCDE1234F1Z5", size=9, color="WHITE"),
                            ], expand=True),
                        ], alignment=ft.MainAxisAlignment.START),
                    ], horizontal_alignment=ft.CrossAxisAlignment.START)
                ),

                # Letter Content
                ft.Container(
                    padding=30,
                    content=ft.Column([
                        # Reference and Date
                        ft.Row([
                            ft.Text(f"Ref: VT/HR/Offer/{emp.employee_code or 'N/A'}/{datetime.now().year}",
                                    size=10, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Text(f"Date: {current_date}", size=10),
                        ]),
                        ft.Container(height=20),

                        # Salutation
                        ft.Text(f"To,", size=11),
                        ft.Container(height=5),
                        ft.Text(f"Mr./Ms. {emp_name}",
                                size=11, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{emp.address or 'India'}", size=10),
                        ft.Container(height=20),

                        # Subject
                        ft.Text("Subject: Appointment Letter for the post of {pos_title}".format(pos_title=pos_title),
                                size=12, weight=ft.FontWeight.BOLD),
                        ft.Container(height=15),

                        # Opening
                        ft.Text(f"Dear {emp_name},", size=11,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Text(
                            "We are pleased to offer you the position of {position} in our organization.".format(
                                position=pos_title),
                            size=11),
                        ft.Text(
                            "Your appointment is subject to the terms and conditions mentioned in this letter and the employment agreement.",
                            size=11),
                        ft.Container(height=20),

                        # Appointment Details
                        ft.Container(
                            padding=15,
                            bgcolor="#E8EAF6",
                            border_radius=8,
                            content=ft.Column([
                                ft.Text("1. APPOINTMENT DETAILS", size=12,
                                        weight=ft.FontWeight.BOLD, color="#1A237E"),
                                ft.Divider(height=10),
                                ft.Row([
                                    ft.Column([
                                        ft.Text("Position:", size=10,
                                                color="#424242"),
                                        ft.Text("Department:", size=10,
                                                color="#424242"),
                                        ft.Text("Employment Type:",
                                                size=10, color="#424242"),
                                        ft.Text("Date of Joining:",
                                                size=10, color="#424242"),
                                        ft.Text("Work Location:",
                                                size=10, color="#424242"),
                                        ft.Text("Reporting To:",
                                                size=10, color="#424242"),
                                    ], width=150, spacing=8),
                                    ft.Column([
                                        ft.Text(pos_title, size=10,
                                                weight=ft.FontWeight.W_500),
                                        ft.Text(dept_name, size=10,
                                                weight=ft.FontWeight.W_500),
                                        ft.Text(emp_type, size=10,
                                                weight=ft.FontWeight.W_500),
                                        ft.Text(doj, size=10,
                                                weight=ft.FontWeight.W_500),
                                        ft.Text("India", size=10,
                                                weight=ft.FontWeight.W_500),
                                        ft.Text("Department Head", size=10,
                                                weight=ft.FontWeight.W_500),
                                    ], spacing=8),
                                ], spacing=30),
                            ], spacing=0)
                        ),
                        ft.Container(height=15),

                        # Compensation Details
                        ft.Container(
                            padding=15,
                            bgcolor="#E8F5E9",
                            border_radius=8,
                            content=ft.Column([
                                ft.Text("2. COMPENSATION PACKAGE (Monthly)", size=12,
                                        weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                ft.Divider(height=10),
                                ft.Row([
                                    ft.Column([
                                        ft.Text("Basic Salary:", size=10),
                                        ft.Text("HRA (40%):", size=10),
                                        ft.Text("Conveyance (10%):", size=10),
                                        ft.Text("Medical Allowance:", size=10),
                                        ft.Text(
                                            "Special Allowance (10%):", size=10),
                                        ft.Text("Gross Salary:", size=11,
                                                weight=ft.FontWeight.BOLD),
                                    ], width=180, spacing=8),
                                    ft.Column([
                                        ft.Text(f"Rs.{basic:,.2f}", size=10),
                                        ft.Text(f"Rs.{hra:,.2f}", size=10),
                                        ft.Text(f"Rs.{conv:,.2f}", size=10),
                                        f"Rs.{medical:,.2f}",
                                        ft.Text(f"Rs.{special:,.2f}", size=10),
                                        ft.Text(
                                            f"Rs.{gross_salary:,.2f}", size=11, weight=ft.FontWeight.BOLD),
                                    ], spacing=8),
                                ], spacing=30),
                                ft.Container(height=10),
                                ft.Divider(),
                                ft.Row([
                                    ft.Column([
                                        ft.Text("Deductions:", size=10,
                                                color="#B71C1C"),
                                        ft.Text(
                                            "Provident Fund (12%):", size=10),
                                        ft.Text("Professional Tax:", size=10),
                                        ft.Text("Total Deductions:", size=10,
                                                weight=ft.FontWeight.BOLD),
                                    ], width=180, spacing=8),
                                    ft.Column([
                                        ft.Text(""),
                                        ft.Text(f"-Rs.{pf:,.2f}",
                                                size=10, color="#B71C1C"),
                                        ft.Text(f"-Rs.{pt:,.2f}",
                                                size=10, color="#B71C1C"),
                                        ft.Text(
                                            f"-Rs.{pf+pt:,.2f}", size=10, weight=ft.FontWeight.BOLD, color="#B71C1C"),
                                    ], spacing=8),
                                ], spacing=30),
                                ft.Container(height=10),
                                ft.Divider(),
                                ft.Row([
                                    ft.Text("NET MONTHLY SALARY:", size=12,
                                            weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        f"Rs.{net_salary:,.2f}", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                                ]),
                                ft.Container(height=5),
                                ft.Text(
                                    f"(Rupees {self._number_to_words(net_salary)} Only)", size=9, color="#424242"),
                            ], spacing=0)
                        ),
                        ft.Container(height=15),

                        # Probation Period
                        ft.Container(
                            padding=12,
                            border_radius=8,
                            border=ft.border.all(1, "#BDBDBD"),
                            content=ft.Column([
                                ft.Text("3. PROBATION PERIOD", size=12,
                                        weight=ft.FontWeight.BOLD, color="#E65100"),
                                ft.Divider(height=8),
                                ft.Text(
                                    "• You will be on probation for a period of 6 months from the date of joining.", size=10),
                                ft.Text(
                                    "• The management may extend the probation period by 3 months if necessary.", size=10),
                                ft.Text(
                                    "• On successful completion of probation, your appointment will be confirmed in writing.", size=10),
                            ], spacing=5)
                        ),
                        ft.Container(height=10),

                        # Leave Policy
                        ft.Container(
                            padding=12,
                            border_radius=8,
                            border=ft.border.all(1, "#BDBDBD"),
                            content=ft.Column([
                                ft.Text("4. LEAVE POLICY", size=12,
                                        weight=ft.FontWeight.BOLD, color="#E65100"),
                                ft.Divider(height=8),
                                ft.Text(
                                    "• Annual Leave: 20 days per calendar year", size=10),
                                ft.Text(
                                    "• Sick Leave: 10 days per calendar year", size=10),
                                ft.Text(
                                    "• Casual Leave: 5 days per calendar year", size=10),
                                ft.Text(
                                    "• Maternity/Paternity Leave: As per statutory regulations", size=10),
                            ], spacing=5)
                        ),
                        ft.Container(height=10),

                        # Working Hours
                        ft.Container(
                            padding=12,
                            border_radius=8,
                            border=ft.border.all(1, "#BDBDBD"),
                            content=ft.Column([
                                ft.Text("5. WORKING HOURS & ATTENDANCE", size=12,
                                        weight=ft.FontWeight.BOLD, color="#E65100"),
                                ft.Divider(height=8),
                                ft.Text(
                                    "• Working Hours: 9:00 AM - 6:00 PM (Monday - Friday)", size=10),
                                ft.Text(
                                    "• Saturday: 9:00 AM - 1:00 PM (Half Day)", size=10),
                                ft.Text(
                                    "• Late arrival more than 3 times in a month will be treated as leave.", size=10),
                            ], spacing=5)
                        ),
                        ft.Container(height=10),

                        # Terms & Conditions
                        ft.Container(
                            padding=12,
                            border_radius=8,
                            border=ft.border.all(1, "#BDBDBD"),
                            content=ft.Column([
                                ft.Text("6. TERMS & CONDITIONS", size=12,
                                        weight=ft.FontWeight.BOLD, color="#E65100"),
                                ft.Divider(height=8),
                                ft.Text(
                                    "1. This offer is subject to verification of all original documents.", size=9),
                                ft.Text(
                                    "2. You will maintain strict confidentiality of company information.", size=9),
                                ft.Text(
                                    "3. All work product and intellectual property belongs to the company.", size=9),
                                ft.Text(
                                    "4. Notice period: 30 days from either party during probation, 60 days after confirmation.", size=9),
                                ft.Text(
                                    "5. The company reserves the right to terminate employment with cause.", size=9),
                                ft.Text(
                                    "6. You must comply with all company policies, rules, and regulations.", size=9),
                                ft.Text(
                                    "7. Transfer/Deputation: You may be posted to any location as per company requirements.", size=9),
                            ], spacing=5)
                        ),
                        ft.Container(height=10),

                        # Benefits
                        ft.Container(
                            padding=12,
                            border_radius=8,
                            border=ft.border.all(1, "#BDBDBD"),
                            content=ft.Column([
                                ft.Text("7. BENEFITS", size=12,
                                        weight=ft.FontWeight.BOLD, color="#E65100"),
                                ft.Divider(height=8),
                                ft.Text(
                                    "• Provident Fund (PF) as per statutory regulations", size=9),
                                ft.Text(
                                    "• ESIC (Employee State Insurance) as applicable", size=9),
                                ft.Text(
                                    "• Group Medical Insurance for employee", size=9),
                                ft.Text(
                                    "• Annual Performance Bonus (as per company policy)", size=9),
                                ft.Text(
                                    "• Training & Development Opportunities", size=9),
                            ], spacing=5)
                        ),
                        ft.Container(height=20),

                        # Acceptance
                        ft.Text("If you accept this offer, please sign and return the duplicate copy of this letter",
                                size=10, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "within 7 days from the date of this letter.", size=10),
                        ft.Container(height=25),

                        # Signatures
                        ft.Row([
                            ft.Column([
                                ft.Text(
                                    "____________________________", size=10),
                                ft.Text("Candidate Signature",
                                        size=9, color="#424242"),
                                ft.Text("Date: ________________", size=9),
                            ], spacing=5),
                            ft.Container(expand=True),
                            ft.Column([
                                ft.Text(
                                    "____________________________", size=10),
                                ft.Text("Authorized Signatory",
                                        size=9, color="#424242"),
                                ft.Text("For Vernika Technologies", size=9),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=5),
                        ], spacing=10),
                    ], spacing=5)
                )
            ], spacing=0)
        )

        # Download function for Offer Letter - Multi-page professional format
        def download_offer_letter(e):
            try:
                import io
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.pdfgen import canvas
                from reportlab.lib.units import mm
                from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

                # Create PDF with multiple pages if needed
                buffer = io.BytesIO()
                story = []

                # Styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=10)
                heading_style = ParagraphStyle(
                    'Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=8, spaceBefore=10)
                normal_style = ParagraphStyle(
                    'Normal', parent=styles['Normal'], fontSize=10, alignment=TA_JUSTIFY, spaceAfter=5)
                small_style = ParagraphStyle(
                    'Small', parent=styles['Normal'], fontSize=9, spaceAfter=3)

                # Page 1: Offer Letter
                c = canvas.Canvas(buffer, pagesize=A4)
                width, height = A4

                # Header
                c.setFillColor(colors.HexColor("#1A237E"))

                c.rect(0, height - 50*mm, width, 50*mm, fill=True)

                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 18)
                c.drawString(20*mm, height - 25*mm, "VERNIKA TECHNOLOGIES")
                c.setFont("Helvetica", 9)
                c.drawString(20*mm, height - 32*mm, "Registered Office: India")
                c.setFont("Helvetica", 8)
                c.drawString(20*mm, height - 38*mm,
                             "CIN: U72900XX2024PTC123456 | GST: 22ABCDE1234F1Z5")

                # Content
                y = height - 60*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 9)
                c.drawString(
                    20*mm, y, f"Ref: VT/HR/Offer/{emp.employee_code or 'N/A'}/{datetime.now().year}")
                c.drawRightString(width - 20*mm, y, f"Date: {current_date}")

                y -= 15*mm
                c.drawString(20*mm, y, "To,")
                y -= 8*mm
                c.setFont("Helvetica-Bold", 10)
                c.drawString(20*mm, y, f"Mr./Ms. {emp_name}")
                y -= 6*mm
                c.setFont("Helvetica", 9)
                c.drawString(20*mm, y, emp.address or "India")

                y -= 15*mm
                c.setFont("Helvetica-Bold", 11)
                c.drawString(
                    20*mm, y, f"Subject: Appointment Letter for the post of {pos_title}")

                y -= 12*mm
                c.setFont("Helvetica-Bold", 10)
                c.drawString(20*mm, y, f"Dear {emp_name},")
                y -= 8*mm
                c.setFont("Helvetica", 9)
                c.drawString(
                    20*mm, y, "We are pleased to offer you the position of")
                y -= 6*mm
                c.setFont("Helvetica-Bold", 10)
                c.drawString(20*mm, y, f"{pos_title}")
                y -= 6*mm
                c.setFont("Helvetica", 9)
                c.drawString(20*mm, y, f"in {dept_name} Department.")

                y -= 10*mm
                text = "Your appointment is subject to the terms and conditions mentioned in this letter and the employment agreement."
                c.drawString(20*mm, y, text[:80])
                y -= 5*mm
                c.drawString(20*mm, y, text[80:])

                # Appointment Details
                y -= 15*mm
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(colors.HexColor("#1A237E"))
                c.drawString(20*mm, y, "1. APPOINTMENT DETAILS")

                y -= 8*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 9)
                c.drawString(25*mm, y, f"Position: {pos_title}")
                y -= 5*mm
                c.drawString(25*mm, y, f"Department: {dept_name}")
                y -= 5*mm
                c.drawString(25*mm, y, f"Employment Type: {emp_type}")
                y -= 5*mm
                c.drawString(25*mm, y, f"Date of Joining: {doj}")
                y -= 5*mm
                c.drawString(25*mm, y, "Work Location: India")

                # Compensation Table
                y -= 15*mm
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(colors.HexColor("#1B5E20"))
                c.drawString(20*mm, y, "2. COMPENSATION PACKAGE (Monthly)")

                y -= 10*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 9)

                # Earnings
                c.drawString(25*mm, y, "Earnings:")
                c.drawRightString(100*mm, y, "Amount (Rs.)")
                y -= 6*mm
                c.drawString(30*mm, y, "Basic Salary")
                c.drawRightString(100*mm, y, f"{basic:,.2f}")
                y -= 5*mm
                c.drawString(30*mm, y, "HRA (40%)")
                c.drawRightString(100*mm, y, f"{hra:,.2f}")
                y -= 5*mm
                c.drawString(30*mm, y, "Conveyance (10%)")
                c.drawRightString(100*mm, y, f"{conv:,.2f}")
                y -= 5*mm
                c.drawString(30*mm, y, "Medical Allowance")
                c.drawRightString(100*mm, y, f"{medical:,.2f}")
                y -= 5*mm
                c.drawString(30*mm, y, "Special Allowance (10%)")
                c.drawRightString(100*mm, y, f"{special:,.2f}")
                y -= 6*mm
                c.setFont("Helvetica-Bold", 10)
                c.drawString(30*mm, y, "Gross Salary")
                c.drawRightString(100*mm, y, f"{gross_salary:,.2f}")

                # Deductions
                y -= 10*mm
                c.setFont("Helvetica", 9)
                c.setFillColor(colors.HexColor("#B71C1C"))
                c.drawString(25*mm, y, "Deductions:")
                y -= 6*mm
                c.drawString(30*mm, y, "Provident Fund (12%)")
                c.drawRightString(100*mm, y, f"-{pf:,.2f}")
                y -= 5*mm
                c.drawString(30*mm, y, "Professional Tax")
                c.drawRightString(100*mm, y, f"-{pt:,.2f}")
                y -= 6*mm
                c.setFont("Helvetica-Bold", 10)
                c.drawString(30*mm, y, "Total Deductions")
                c.drawRightString(100*mm, y, f"-{pf+pt:,.2f}")

                # Net Salary
                y -= 12*mm
                c.setFillColor(colors.HexColor("#1B5E20"))
                c.setFont("Helvetica-Bold", 11)
                c.drawString(25*mm, y, "NET MONTHLY SALARY:")
                c.drawRightString(100*mm, y, f"Rs.{net_salary:,.2f}")

                y -= 6*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 8)
                c.drawString(
                    25*mm, y, f"(Rupees {self._number_to_words(net_salary)} Only)")

                # Continue on Page 2
                c.showPage()

                # Page 2
                y = height - 30*mm

                # Probation
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(colors.HexColor("#E65100"))
                c.drawString(20*mm, y, "3. PROBATION PERIOD")
                y -= 8*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 9)
                c.drawString(
                    25*mm, y, "• You will be on probation for a period of 6 months from the date of joining.")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• The management may extend the probation period by 3 months if necessary.")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• On successful completion of probation, your appointment will be confirmed in writing.")

                # Leave Policy
                y -= 15*mm
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(colors.HexColor("#E65100"))
                c.drawString(20*mm, y, "4. LEAVE POLICY")
                y -= 8*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 9)
                c.drawString(
                    25*mm, y, "• Annual Leave: 20 days per calendar year")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• Sick Leave: 10 days per calendar year")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• Casual Leave: 5 days per calendar year")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• Maternity/Paternity Leave: As per statutory regulations")

                # Working Hours
                y -= 15*mm
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(colors.HexColor("#E65100"))
                c.drawString(20*mm, y, "5. WORKING HOURS & ATTENDANCE")
                y -= 8*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 9)
                c.drawString(
                    25*mm, y, "• Working Hours: 9:00 AM - 6:00 PM (Monday - Friday)")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• Saturday: 9:00 AM - 1:00 PM (Half Day)")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• Late arrival more than 3 times in a month will be treated as leave.")

                # Terms & Conditions
                y -= 15*mm
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(colors.HexColor("#E65100"))
                c.drawString(20*mm, y, "6. TERMS & CONDITIONS")
                y -= 8*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 9)
                c.drawString(
                    25*mm, y, "1. This offer is subject to verification of all original documents.")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "2. You will maintain strict confidentiality of company information.")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "3. All work product and intellectual property belongs to the company.")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "4. Notice period: 30 days during probation, 60 days after confirmation.")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "5. The company reserves the right to terminate employment with cause.")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "6. You must comply with all company policies, rules, and regulations.")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "7. Transfer/Deputation: You may be posted to any location as per requirements.")

                # Benefits
                y -= 15*mm
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(colors.HexColor("#E65100"))
                c.drawString(20*mm, y, "7. BENEFITS")
                y -= 8*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 9)
                c.drawString(
                    25*mm, y, "• Provident Fund (PF) as per statutory regulations")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• ESIC (Employee State Insurance) as applicable")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• Group Medical Insurance for employee")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• Annual Performance Bonus (as per company policy)")
                y -= 5*mm
                c.drawString(
                    25*mm, y, "• Training & Development Opportunities")

                # Acceptance
                y -= 25*mm
                c.setFont("Helvetica-Bold", 9)
                c.drawString(
                    20*mm, y, "If you accept this offer, please sign and return the duplicate copy of this letter")
                y -= 5*mm
                c.drawString(
                    20*mm, y, "within 7 days from the date of this letter.")

                # Signatures
                y -= 25*mm
                c.setFont("Helvetica", 9)
                c.drawString(20*mm, y, "____________________________")
                c.drawRightString(width - 20*mm, y,
                                  "____________________________")
                y -= 5*mm
                c.drawString(20*mm, y, "Candidate Signature")
                c.drawRightString(width - 20*mm, y, "Authorized Signatory")
                y -= 5*mm
                c.drawString(20*mm, y, "Date: ________________")
                c.drawRightString(width - 20*mm, y, "For Vernika Technologies")

                # Footer
                c.setFont("Helvetica", 8)
                c.setFillColor(colors.gray)
                c.drawCentredString(
                    width/2, 15*mm, "This is a computer-generated document. No signature required.")

                c.save()
                buffer.seek(0)

                # Save to file
                import os
                output_dir = os.path.expanduser("~/Downloads")
                os.makedirs(output_dir, exist_ok=True)
                filename = f"Offer_Letter_{emp.employee_code or emp_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'wb') as f:
                    f.write(buffer.read())

                self._show_success(f"Offer Letter saved to: {filepath}")

            except Exception as ex:
                print(f"Error generating PDF: {ex}")
                import traceback
                traceback.print_exc()
                self._show_error(f"Error generating PDF: {str(ex)}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Offer Letter - Professional Format"),
            content=ft.Container(
                content=ft.ListView([
                    offer_letter
                ], spacing=0, padding=0, expand=True),
                width=680,
                height=600,
            ),
            actions=[
                ft.ElevatedButton(
                    "Download PDF",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=download_offer_letter,
                    style=ft.ButtonStyle(bgcolor="#4CAF50", color="WHITE")
                ),
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_info(self, msg):
        """Show info message"""
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#2196F3")
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _generate_salary_slip_dialog(self, emp_id: int):
        """Generate Salary Slip dialog using PostgreSQL"""
        from sqlalchemy.orm import joinedload

        db = None
        try:
            db = get_db_session()
            # Query employee with relationships
            emp = db.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            ).filter(Employee.id == emp_id).first()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if db:
                db.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        # Get department and position names
        dept_name = emp.department.name if emp.department else "General"
        pos_title = emp.position.title if emp.position else "Employee"

        basic = emp.basic_salary or 0
        allowance = emp.allowance or 0
        deduction = emp.deduction or 0
        net_salary = basic + allowance - deduction

        salary_slip = ft.Container(
            width=500,
            height=550,
            bgcolor="white",
            content=ft.Column([
                ft.Container(
                    bgcolor="#1976D2",
                    padding=padding.all(12),
                    content=ft.Row([
                        ft.Text("VERNIKA TECHNOLOGIES", size=14,
                                color="WHITE", weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Text("Salary Slip", size=12, color="WHITE"),
                    ])
                ),
                ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Employee:", size=11, color="#666"),
                            ft.Text(f"{emp.first_name or ''} {emp.last_name or ''}",
                                    size=12, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Text(
                                f"Month: {datetime.now().strftime('%B %Y')}", size=11, color="#666"),
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Department:", size=11, color="#666"),
                            ft.Text(dept_name or '-', size=11),
                            ft.Container(expand=True),
                            ft.Text("Position:", size=11, color="#666"),
                            ft.Text(pos_title or '-', size=11),
                        ]),
                        ft.Row([
                            ft.Text("Emp Code:", size=11, color="#666"),
                            ft.Text(emp.employee_code or '-', size=11),
                            ft.Container(expand=True),
                            ft.Text(" DOJ:", size=11, color="#666"),
                            ft.Text(
                                str(emp.date_of_joining) if emp.date_of_joining else '-', size=11),
                        ]),
                        ft.Divider(height=3),
                        ft.Text("EARNINGS", size=12,
                                weight=ft.FontWeight.BOLD, color="#4CAF50"),
                        ft.Row([
                            ft.Text("Basic Salary", size=11),
                            ft.Container(expand=True),
                            ft.Text(f"Rs.{basic:,.2f}", size=11),
                        ]),
                        ft.Row([
                            ft.Text("Allowances", size=11),
                            ft.Container(expand=True),
                            ft.Text(f"Rs.{allowance:,.2f}", size=11),
                        ]),
                        ft.Row([
                            ft.Text("Gross Salary", size=12,
                                    weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Text(f"Rs.{basic + allowance:,.2f}",
                                    size=12, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Divider(height=3),
                        ft.Text("DEDUCTIONS", size=12,
                                weight=ft.FontWeight.BOLD, color="#F44336"),
                        ft.Row([
                            ft.Text("Deductions", size=11),
                            ft.Container(expand=True),
                            ft.Text(f"Rs.{deduction:,.2f}", size=11),
                        ]),
                        ft.Divider(height=3),
                        ft.Row([
                            ft.Text("NET SALARY", size=14,
                                    weight=ft.FontWeight.BOLD, color="#1976D2"),
                            ft.Container(expand=True),
                            ft.Text(f"Rs.{net_salary:,.2f}", size=14,
                                    weight=ft.FontWeight.BOLD, color="#1976D2"),
                        ]),
                        ft.Divider(),
                        ft.Text(
                            f"Net Salary: {self._number_to_words(net_salary)}", size=10, color="#666"),
                    ], spacing=5)
                )
            ], spacing=0)
        )

        # Download function for Salary Slip
        def download_salary_slip(e):
            try:
                import io
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.pdfgen import canvas

                # Create PDF
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                width, height = A4

                # Header
                c.setFillColor(colors.HexColor("#1976D2"))
                c.rect(0, height - 50, width, 50, fill=True)

                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 18)
                c.drawCentredString(width/2, height - 30,
                                    "VERNIKA TECHNOLOGIES")
                c.setFont("Helvetica", 12)
                c.drawCentredString(width/2, height - 42, "Salary Slip")

                # Month
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 10)
                c.drawString(50, height - 70,
                             f"Month: {datetime.now().strftime('%B %Y')}")

                # Employee Details
                y = height - 100
                c.setFont("Helvetica-Bold", 12)
                name = f"{emp.first_name or ''} {emp.last_name or ''}".strip()
                c.drawString(50, y, f"Employee: {name}")

                c.setFont("Helvetica", 10)
                c.drawString(350, y, f"Department: {dept_name}")
                y -= 20
                c.drawString(50, y, f"Position: {pos_title}")
                c.drawString(
                    350, y, f"Employee Code: {emp.employee_code or 'N/A'}")
                y -= 20
                c.drawString(
                    50, y, f"Date of Joining: {emp.date_of_joining or '-'}")

                # Earnings
                y -= 40
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "EARNINGS")
                y -= 20
                c.setFont("Helvetica", 10)
                c.drawString(50, y, "Basic Salary")
                c.drawRightString(400, y, f"Rs.{basic:,.2f}")
                y -= 15
                c.drawString(50, y, "Allowances")
                c.drawRightString(400, y, f"Rs.{allowance:,.2f}")
                y -= 20
                c.setFont("Helvetica-Bold", 11)
                c.drawString(50, y, "Gross Salary")
                c.drawRightString(400, y, f"Rs.{basic + allowance:,.2f}")

                # Deductions
                y -= 35
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "DEDUCTIONS")
                y -= 20
                c.setFont("Helvetica", 10)
                c.drawString(50, y, "Deductions")
                c.drawRightString(400, y, f"Rs.{deduction:,.2f}")

                # Net Salary
                y -= 35
                c.setFont("Helvetica-Bold", 14)
                c.setFillColor(colors.HexColor("#1976D2"))
                c.drawString(50, y, "NET SALARY")
                c.drawRightString(400, y, f"Rs.{net_salary:,.2f}")

                # Footer
                c.setFont("Helvetica", 8)
                c.setFillColor(colors.gray)
                c.drawCentredString(
                    width/2, 30, "This is a computer-generated document.")

                c.save()
                buffer.seek(0)

                # Save to file
                import os
                output_dir = os.path.expanduser("~/Downloads")
                os.makedirs(output_dir, exist_ok=True)
                filename = f"Salary_Slip_{emp.employee_code or emp_id}_{datetime.now().strftime('%Y%m')}.pdf"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'wb') as f:
                    f.write(buffer.read())

                self._show_success(f"Salary Slip saved to: {filepath}")

            except Exception as ex:
                print(f"Error generating PDF: {ex}")
                self._show_error(f"Error generating PDF: {str(ex)}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Salary Slip"),
            content=ft.Container(
                content=ft.ListView([
                    salary_slip
                ], spacing=0, padding=0, expand=True),
                width=500,
                height=550,
            ),
            actions=[
                ft.ElevatedButton(
                    "Download Salary Slip",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=download_salary_slip,
                    style=ft.ButtonStyle(bgcolor="#2196F3", color="WHITE")
                ),
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_delete_dialog(self, emp_id: int):
        """Show delete confirmation dialog using PostgreSQL"""

        db = None
        emp_name = ""
        user_id = None

        try:
            db = get_db_session()
            emp = db.query(Employee).filter(Employee.id == emp_id).first()
            if emp:
                emp_name = f"{emp.first_name or ''} {emp.last_name or ''}".strip()
                user_id = emp.user_id
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if db:
                db.close()

        if not emp_name:
            self._show_error("Employee not found!")
            return

        def confirm_delete(e):
            """Delete employee - FIXED WITH PROVEN PATTERN"""
            db = get_db_session()
            try:
                result = delete_employee_complete(db, emp_id)
                if result.get("success"):
                    counts_str = ""
                    counts = result.get("deleted_counts", {})
                    if any(counts.values()):
                        counts_str = " + " + \
                            ", ".join(
                                [f"{k}: {v}" for k, v in counts.items() if v > 0])
                    self._show_success(
                        f"Employee '{emp_name}' deleted{counts_str}!")
                    self._close_dialog()
                    self._refresh()
                else:
                    self._show_error(
                        f"Delete failed: {result.get('message', 'Unknown error')}")
            except Exception as ex:
                db.rollback()
                print(f"Employee delete error: {ex}")
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Employee?", color="#F44336"),
            content=ft.Text(
                f"Are you sure you want to delete '{emp_name}'? This action cannot be undone."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm_delete,
                                  style=ft.ButtonStyle(bgcolor="#F44336", color="WHITE"))
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _number_to_words(self, n):
        """Convert number to words"""
        if n <= 0:
            return "Zero"

        units = ["", "One", "Two", "Three", "Four",
                 "Five", "Six", "Seven", "Eight", "Nine"]
        teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
                 "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty",
                "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

        n = int(n)
        if n < 10:
            return units[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (" " + units[n % 10] if n % 10 else "")
        elif n < 1000:
            return units[n // 100] + " Hundred" + (" " + self._number_to_words(n % 100) if n % 100 else "")
        elif n < 100000:
            return self._number_to_words(n // 1000) + " Thousand" + (" " + self._number_to_words(n % 1000) if n % 1000 else "")
        else:
            return str(n)


def show_employees(page, user):
    """Helper function to show employees screen"""
    page.clean()
    page.add(EmployeesScreen(page, user))
