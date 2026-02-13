"""
Vernika HRA - Enhanced Employees Screen with ID/PASS Creation, Full Details, and Document Generation
"""

import flet as ft
from flet import padding
import bcrypt
from datetime import datetime, date
from sqlalchemy import func
import random
import string
from database.connection import get_db_session
from database.models import Employee, User, Department, Position, Role
from database.operations import get_all_employees, get_employee_by_id
from components.forms import DatePickerField
import sqlite3  # For backward compatibility references only


class EmployeesScreen(ft.Container):
    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = "#F5F5F5"
        self._dialog = None
        self.content = self._build_content()

    def _get_db(self):
        """Get database connection using SQLAlchemy"""
        return get_db_session()

    def _build_content(self):
        header = ft.Container(
            padding=15,
            bgcolor="#2E86AB",
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self.on_back
                ),
                ft.Text(
                    "Employee Management",
                    size=18,
                    color="WHITE",
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Add Employee",
                    icon=ft.Icons.ADD,
                    on_click=self.on_add_employee,
                    style=ft.ButtonStyle(
                        color="WHITE",
                        bgcolor="#1976D2",
                    )
                ),
            ])
        )

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

    def on_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def on_add_employee(self, e):
        self._show_add_dialog()

    def _build_employee_list(self):
        db = None
        try:
            db = get_db_session()
            # Query employees with eager loading of relationships using SQLAlchemy
            from sqlalchemy.orm import joinedload
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
                            ft.Container(
                                ft.Text(emp_type, size=10, color="WHITE"),
                                bgcolor=type_color,
                                padding=padding.all(4),
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
                ft.DataColumn(label=ft.Text("Type")),
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
        conn = None
        try:
            conn = sqlite3.connect('vernika.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
            emp = cursor.fetchone()
            cursor.execute("SELECT id, name FROM departments")
            departments = cursor.fetchall()
            cursor.execute("SELECT id, title FROM positions")
            positions = cursor.fetchall()
            cursor.execute("SELECT id, name FROM roles")
            roles = cursor.fetchall()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        # Edit form fields
        first_name = ft.TextField(
            label="First Name *", width=200, value=emp['first_name'] or "")
        last_name = ft.TextField(
            label="Last Name *", width=200, value=emp['last_name'] or "")
        email = ft.TextField(label="Email *", width=420,
                             value=emp['email'] or "")
        phone = ft.TextField(label="Phone", width=200,
                             value=emp['phone'] or "")

        # Date pickers with values
        dob_picker = DatePickerField(label="Date of Birth", width=200)
        dob_picker._page = self._page
        if emp['date_of_birth']:
            dob_picker.value = str(emp['date_of_birth'])

        gender = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("MALE", "Male"),
                ft.dropdown.Option("FEMALE", "Female"),
                ft.dropdown.Option("OTHER", "Other"),
            ],
            label="Gender",
            value=(emp['gender'].upper() if emp['gender']
                   else "MALE") if emp['gender'] else "MALE"
        )
        address = ft.TextField(label="Address", width=420,
                               value=emp['address'] or "", multiline=True)
        city = ft.TextField(label="City", width=200, value=emp['city'] or "")
        state = ft.TextField(label="State", width=200,
                             value=emp['state'] or "")
        pincode = ft.TextField(label="Pincode", width=100,
                               value=emp['pincode'] or "")

        dept_options = [ft.dropdown.Option(
            key=str(d['id']), text=d['name']) for d in departments]
        dept_dropdown = ft.Dropdown(width=200, options=dept_options, label="Department",
                                    value=str(emp['department_id']) if emp['department_id'] else None)

        pos_options = [ft.dropdown.Option(
            key=str(p['id']), text=p['title']) for p in positions]
        pos_dropdown = ft.Dropdown(width=200, options=pos_options, label="Position",
                                   value=str(emp['position_id']) if emp['position_id'] else None)

        employment_type = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("full_time", "Full-time"),
                ft.dropdown.Option("part_time", "Part-time"),
                ft.dropdown.Option("contract", "Contract"),
                ft.dropdown.Option("intern", "Intern"),
            ],
            label="Employment Type",
            value=emp['employment_type'] or "full_time"
        )

        employment_status = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("active", "Active"),
                ft.dropdown.Option("on_probation", "On Probation"),
                ft.dropdown.Option("inactive", "Inactive"),
            ],
            label="Employment Status",
            value=emp['employment_status'] or "active"
        )

        # Date picker for Date of Joining
        date_of_joining_picker = DatePickerField(
            label="Date of Joining", width=200)
        date_of_joining_picker._page = self._page
        if emp['date_of_joining']:
            date_of_joining_picker.value = str(emp['date_of_joining'])

        bank_name = ft.TextField(
            label="Bank Name", width=250, value=emp['bank_name'] or "")
        account_number = ft.TextField(
            label="Account Number", width=200, value=emp['account_number'] or "")
        ifsc_code = ft.TextField(
            label="IFSC Code", width=150, value=emp['ifsc_code'] or "")
        branch_name = ft.TextField(
            label="Branch", width=200, value=emp['branch_name'] or "")

        basic_salary = ft.TextField(
            label="Basic Salary", width=150, value=str(emp['basic_salary'] or 0))
        allowance = ft.TextField(
            label="Allowances", width=150, value=str(emp['allowance'] or 0))
        deduction = ft.TextField(
            label="Deductions", width=150, value=str(emp['deduction'] or 0))

        status_switch = ft.Switch(label="Active", value=bool(emp['is_active']))

        def update_employee(e):
            conn = None
            try:
                conn = sqlite3.connect('vernika.db')
                cursor = conn.cursor()

                dob_value = emp['date_of_birth']
                try:
                    if dob_picker.value:
                        dob_value = dob_picker.value
                except (AttributeError, ValueError) as e:
                    print(f"Warning: Could not parse DOB value: {e}")

                doj_value = emp['date_of_joining']
                try:
                    if date_of_joining_picker.value:
                        doj_value = date_of_joining_picker.value
                except (AttributeError, ValueError) as e:
                    print(f"Warning: Could not parse DOJ value: {e}")

                cursor.execute("""UPDATE employees SET
                    first_name=?, last_name=?, email=?, phone=?,
                    date_of_birth=?, gender=?, address=?, city=?, state=?, pincode=?,
                    bank_name=?, account_number=?, ifsc_code=?, branch_name=?,
                    basic_salary=?, allowance=?, deduction=?,
                    department_id=?, position_id=?, employment_type=?, employment_status=?,
                    date_of_joining=?, is_active=? WHERE id=?""",
                               (first_name.value, last_name.value, email.value, phone.value or None,
                                dob_value, gender.value, address.value or None, city.value or None,
                                state.value or None, pincode.value or None,
                                bank_name.value or None, account_number.value or None,
                                ifsc_code.value or None, branch_name.value or None,
                                float(
                                    basic_salary.value) if basic_salary.value else 0,
                                float(allowance.value) if allowance.value else 0,
                                float(deduction.value) if deduction.value else 0,
                                int(dept_dropdown.value) if dept_dropdown.value else None,
                                int(pos_dropdown.value) if pos_dropdown.value else None,
                                employment_type.value, employment_status.value,
                                doj_value, status_switch.value, emp_id))
                conn.commit()
                self._close_dialog()
                self._show_success("Employee updated successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                if conn:
                    conn.close()

        tab_content = ft.Column([
            ft.Text("Personal Information", size=14,
                    weight=ft.FontWeight.BOLD, color="#2E86AB"),
            ft.Row([first_name, last_name], spacing=10),
            email, phone,
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
        """Show full employee details"""
        conn = None
        try:
            conn = sqlite3.connect('vernika.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, d.name as dept_name, p.title as position_title,
                       r.name as role_name, u.username
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                LEFT JOIN users u ON e.user_id = u.id
                LEFT JOIN roles r ON u.role_id = r.id
                WHERE e.id=?
            """, (emp_id,))
            emp = cursor.fetchone()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        total_salary = (emp['basic_salary'] or 0) + \
            (emp['allowance'] or 0) - (emp['deduction'] or 0)

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
                            ft.Text(f"{emp['first_name'] or ''} {emp['last_name'] or ''}",
                                    size=20, weight=ft.FontWeight.BOLD, color="#2E86AB"),
                            ft.Text(
                                f"Employee Code: {emp['employee_code'] or 'N/A'}", size=12, color="#757575"),
                        ]),
                        ft.Container(expand=True),
                        ft.Container(
                            bgcolor="#4CAF50" if emp['is_active'] else "#F44336",
                            padding=padding.all(10),
                            border_radius=8,
                            content=ft.Text(
                                (emp['employment_status'] or 'Active').replace(
                                    '_', ' ').title(),
                                color="WHITE", weight=ft.FontWeight.BOLD
                            )
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Text("Personal Details", size=14,
                            weight=ft.FontWeight.BOLD, color="#2E86AB"),
                    create_detail_row("Email:", emp['email']),
                    create_detail_row("Phone:", emp['phone']),
                    create_detail_row("Date of Birth:", emp['date_of_birth']),
                    create_detail_row(
                        "Gender:", emp['gender'].title() if emp['gender'] else "-"),
                    create_detail_row("Address:", emp['address']),
                    create_detail_row("City:", emp['city']),
                    ft.Divider(),
                    ft.Text("Employment Details", size=14,
                            weight=ft.FontWeight.BOLD, color="#2E86AB"),
                    create_detail_row("Department:", emp['dept_name']),
                    create_detail_row("Position:", emp['position_title']),
                    create_detail_row(
                        "Employment Type:", (emp['employment_type'] or 'Full-time').replace('_', ' ').title()),
                    create_detail_row("Date of Joining:",
                                      emp['date_of_joining']),
                    create_detail_row("Username:", emp['username']),
                    ft.Divider(),
                    ft.Text("Emergency Contact", size=14,
                            weight=ft.FontWeight.BOLD, color="#D32F2F"),
                    create_detail_row("Name:", emp['emergency_contact_name']),
                    create_detail_row("Phone:", emp['emergency_phone']),
                    create_detail_row(
                        "Relationship:", emp['emergency_relation']),
                    ft.Divider(),
                    ft.Text("Bank Details", size=14,
                            weight=ft.FontWeight.BOLD, color="#4CAF50"),
                    create_detail_row("Bank:", emp['bank_name']),
                    create_detail_row("Account:", emp['account_number']),
                    create_detail_row("IFSC:", emp['ifsc_code']),
                    ft.Divider(),
                    ft.Text("Salary Information", size=14,
                            weight=ft.FontWeight.BOLD, color="#FF9800"),
                    create_detail_row(
                        "Basic:", f"Rs.{emp['basic_salary'] or 0:,.2f}"),
                    create_detail_row(
                        "Allowances:", f"Rs.{emp['allowance'] or 0:,.2f}"),
                    create_detail_row(
                        "Deductions:", f"Rs.{emp['deduction'] or 0:,.2f}"),
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
            title=ft.Text(f"Employee Details - {emp['employee_code']}"),
            content=ft.Container(content=details, height=500, width=550),
            actions=[
                ft.ElevatedButton("ID Card", on_click=lambda e: self._generate_id_card_dialog(emp_id),
                                  style=ft.ButtonStyle(bgcolor="#FF9800", color="WHITE")),
                ft.ElevatedButton("Offer Letter", on_click=lambda e: self._generate_offer_letter_dialog(emp_id),
                                  style=ft.ButtonStyle(bgcolor="#9C27B0", color="WHITE")),
                ft.ElevatedButton("Salary Slip", on_click=lambda e: self._generate_salary_slip_dialog(emp_id),
                                  style=ft.ButtonStyle(bgcolor="#2196F3", color="WHITE")),
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _generate_id_card_dialog(self, emp_id: int):
        """Generate ID Card dialog"""
        conn = None
        try:
            conn = sqlite3.connect('vernika.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, d.name as dept_name, p.title as position_title
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                WHERE e.id=?
            """, (emp_id,))
            emp = cursor.fetchone()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        id_card = ft.Container(
            width=380,
            height=240,
            bgcolor="white",
            border=ft.border.all(3, "#2E86AB"),
            border_radius=12,
            content=ft.Column([
                ft.Container(
                    bgcolor="#2E86AB",
                    padding=padding.all(12),
                    content=ft.Row([
                        ft.Icon(ft.Icons.BADGE, color="WHITE", size=28),
                        ft.Column([
                            ft.Text("VERNIKA TECHNOLOGIES", size=14,
                                    color="WHITE", weight=ft.FontWeight.BOLD),
                            ft.Text("Employee Identity Card",
                                    size=10, color="WHITE"),
                        ]),
                    ], spacing=10)
                ),
                ft.Container(
                    padding=15,
                    content=ft.Row([
                        ft.Container(
                            width=85,
                            height=100,
                            bgcolor="#E3F2FD",
                            border_radius=8,
                            content=ft.Column([
                                ft.Icon(ft.Icons.PERSON, size=40,
                                        color="#2E86AB"),
                                ft.Text("PHOTO", size=9, color="#757575"),
                            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        ),
                        ft.Column([
                            ft.Text(f"{emp['first_name'] or ''} {emp['last_name'] or ''}",
                                    size=15, weight=ft.FontWeight.BOLD, color="#333"),
                            ft.Text(
                                f"{emp['position_title'] or 'Employee'}", size=11, color="#666"),
                            ft.Text(
                                f"Dept: {emp['dept_name'] or 'General'}", size=10, color="#888"),
                            ft.Text(f"ID: {emp['employee_code'] or 'N/A'}",
                                    size=11, weight=ft.FontWeight.BOLD, color="#2E86AB"),
                            ft.Text(
                                f"DOB: {emp['date_of_birth'] or '-'}", size=10, color="#666"),
                        ], spacing=3),
                    ], spacing=15)
                ),
                ft.Container(
                    expand=True,
                    bgcolor="#F5F5F5",
                    padding=padding.all(8),
                    content=ft.Row([
                        ft.Icon(ft.Icons.EMAIL, size=14, color="#666"),
                        ft.Text(emp['email'] or '-', size=10, color="#666"),
                        ft.Container(expand=True),
                        ft.Icon(ft.Icons.PHONE, size=14, color="#666"),
                        ft.Text(emp['phone'] or '-', size=10, color="#666"),
                    ], spacing=5)
                )
            ], spacing=0)
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Employee ID Card"),
            content=ft.Container(content=id_card, width=380, height=240),
            actions=[
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

    def _generate_offer_letter_dialog(self, emp_id: int):
        """Generate Offer Letter dialog"""
        conn = None
        try:
            conn = sqlite3.connect('vernika.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, d.name as dept_name, p.title as position_title
                FROM employees e 
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                WHERE e.id=?
            """, (emp_id,))
            emp = cursor.fetchone()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        offer_letter = ft.Container(
            width=600,
            height=700,
            bgcolor="white",
            content=ft.Column([
                ft.Container(
                    bgcolor="#2E86AB",
                    padding=padding.all(15),
                    content=ft.Column([
                        ft.Text("VERNIKA TECHNOLOGIES", size=16,
                                color="WHITE", weight=ft.FontWeight.BOLD),
                        ft.Text("Offer of Employment", size=12, color="WHITE"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text(
                            f"Date: {datetime.now().strftime('%Y-%m-%d')}", size=11),
                        ft.Container(height=10),
                        ft.Text(
                            f"Dear {emp['first_name'] or ''} {emp['last_name'] or ''},", size=12),
                        ft.Container(height=10),
                        ft.Text(
                            "We are pleased to offer you the position of", size=11),
                        ft.Text(f"{emp['position_title'] or 'Employee'}", size=14,
                                weight=ft.FontWeight.BOLD, color="#2E86AB"),
                        ft.Text(
                            f"in the {emp['dept_name'] or 'General'} Department.", size=11),
                        ft.Container(height=15),
                        ft.Text("Terms of Employment:", size=12,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"• Employment Type: {(emp['employment_type'] or 'Full-time').replace('_', ' ').title()}", size=11),
                        ft.Text(
                            f"• Basic Salary: Rs.{emp['basic_salary'] or 0:,.2f}/-", size=11),
                        ft.Text(
                            f"• Allowances: Rs.{emp['allowance'] or 0:,.2f}/-", size=11),
                        ft.Text(
                            f"• Deductions: Rs.{emp['deduction'] or 0:,.2f}/-", size=11),
                        ft.Text(
                            f"• Date of Joining: {emp['date_of_joining'] or 'To be decided'}", size=11),
                        ft.Container(height=15),
                        ft.Text(
                            "This offer is subject to verification of your documents and references.", size=10, color="#666"),
                        ft.Text("Welcome to Vernika Technologies!", size=11),
                        ft.Container(height=20),
                        ft.Text("For Vernika Technologies",
                                size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("Authorized Signature", size=10, color="#666"),
                    ], spacing=2)
                )
            ], spacing=0)
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Offer Letter"),
            content=ft.Container(content=offer_letter, width=600, height=700),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _generate_salary_slip_dialog(self, emp_id: int):
        """Generate Salary Slip dialog"""
        conn = None
        try:
            conn = sqlite3.connect('vernika.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, d.name as dept_name, p.title as position_title
                FROM employees e 
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                WHERE e.id=?
            """, (emp_id,))
            emp = cursor.fetchone()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        basic = emp['basic_salary'] or 0
        allowance = emp['allowance'] or 0
        deduction = emp['deduction'] or 0
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
                            ft.Text(f"{emp['first_name'] or ''} {emp['last_name'] or ''}",
                                    size=12, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Text(
                                f"Month: {datetime.now().strftime('%B %Y')}", size=11, color="#666"),
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Department:", size=11, color="#666"),
                            ft.Text(emp['dept_name'] or '-', size=11),
                            ft.Container(expand=True),
                            ft.Text("Position:", size=11, color="#666"),
                            ft.Text(emp['position_title'] or '-', size=11),
                        ]),
                        ft.Row([
                            ft.Text("Emp Code:", size=11, color="#666"),
                            ft.Text(emp['employee_code'] or '-', size=11),
                            ft.Container(expand=True),
                            ft.Text(" DOJ:", size=11, color="#666"),
                            ft.Text(
                                str(emp['date_of_joining']) if emp['date_of_joining'] else '-', size=11),
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

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Salary Slip"),
            content=ft.Container(content=salary_slip, width=500, height=550),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_delete_dialog(self, emp_id: int):
        """Show delete confirmation dialog"""
        conn = None
        try:
            conn = sqlite3.connect('vernika.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT first_name, last_name FROM employees WHERE id=?", (emp_id,))
            emp = cursor.fetchone()
        except Exception as e:
            self._show_error(f"Error: {e}")
            return
        finally:
            if conn:
                conn.close()

        if not emp:
            self._show_error("Employee not found!")
            return

        def confirm_delete(e):
            conn = None
            try:
                conn = sqlite3.connect('vernika.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Get user_id first
                cursor.execute(
                    "SELECT user_id FROM employees WHERE id=?", (emp_id,))
                result = cursor.fetchone()
                if result:
                    user_id = result['user_id']
                    # Delete employee first (due to FK constraints)
                    cursor.execute(
                        "DELETE FROM employees WHERE id=?", (emp_id,))
                    # Then delete user if exists (cascade delete)
                    if user_id:
                        cursor.execute(
                            "DELETE FROM users WHERE id=?", (user_id,))
                conn.commit()
                self._close_dialog()
                self._show_success("Employee deleted successfully!")
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                if conn:
                    conn.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Employee?", color="#F44336"),
            content=ft.Text(
                f"Are you sure you want to delete '{emp['first_name'] or ''} {emp['last_name'] or ''}'? This action cannot be undone."),
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
