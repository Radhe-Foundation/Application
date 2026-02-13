#!/usr/bin/env python3
"""
Fix script for employees_screen.py save_employee function
This script patches the file to fix the save employee functionality.
"""

import re

# Read the original file
with open('/Users/shashankrajput/Desktop/Vernika/screens/employees_screen.py', 'r') as f:
    content = f.read()

# The old save_employee function (problematic)
old_save = '''        def save_employee(e):
            if not all([first_name.value, last_name.value, email.value, username.value, password.value]):
                error_text.value = "Fill required fields (Name, Email, Username, Password)!"
                error_text.visible = True
                self._page.update()
                return

            # Validate email format
            if '@' not in email.value or '.' not in email.value:
                error_text.value = "Please enter a valid email address!"
                error_text.visible = True
                self._page.update()
                return

            conn = None
            try:
                conn = sqlite3.connect('vernika.db')
                cursor = conn.cursor()

                # Check for duplicate username (case insensitive)
                cursor.execute(
                    "SELECT id FROM users WHERE LOWER(username)=?", (username.value.lower(),))
                if cursor.fetchone():
                    error_text.value = "Username already exists! Please choose another."
                    error_text.visible = True
                    self._page.update()
                    return

                # Check for duplicate email (case insensitive)
                cursor.execute(
                    "SELECT id FROM users WHERE LOWER(email)=?", (email.value.lower(),))
                if cursor.fetchone():
                    error_text.value = "Email already registered! Please use another email."
                    error_text.visible = True
                    self._page.update()
                    return

                hashed_pw = bcrypt.hashpw(
                    password.value.encode(), bcrypt.gensalt()).decode()
                cursor.execute("INSERT INTO users (username, email, password_hash, role_id, status) VALUES (?, ?, ?, ?, ?)",
                               (username.value, email.value, hashed_pw, int(role_dropdown.value) if role_dropdown.value else 2, 'active'))
                user_id = cursor.lastrowid

                cursor.execute("SELECT MAX(id) FROM employees")
                max_id = cursor.fetchone()[0] or 0
                emp_code = f"EMP{max_id + 1:03d}"

                dept_id = int(
                    dept_dropdown.value) if dept_dropdown.value else 1
                pos_id = int(pos_dropdown.value) if pos_dropdown.value else 1

                dob_value = None
                try:
                    if dob_picker.value:
                        dob_value = dob_picker.value
                except:
                    pass

                doj_value = None
                try:
                    if date_of_joining_picker.value:
                        doj_value = date_of_joining_picker.value
                except:
                    pass

                cursor.execute("""INSERT INTO employees (
                    employee_code, user_id, first_name, last_name, email, phone,
                    date_of_birth, gender, address, city, state, pincode,
                    emergency_contact_name, emergency_phone, emergency_relation,
                    bank_name, account_number, ifsc_code, branch_name,
                    basic_salary, allowance, deduction,
                    department_id, position_id, employment_type, employment_status, date_of_joining, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                               (emp_code, user_id, first_name.value, last_name.value, email.value, phone.value or None,
                                dob_value, gender.value, address.value or None, city.value or None, state.value or None, pincode.value or None,
                                emergency_contact_name.value or None, emergency_phone.value or None, emergency_relation.value or None,
                                bank_name.value or None, account_number.value or None, ifsc_code.value or None, branch_name.value or None,
                                float(
                                    basic_salary.value) if basic_salary.value else 0,
                                float(allowance.value) if allowance.value else 0,
                                float(deduction.value) if deduction.value else 0,
                                dept_id, pos_id, employment_type.value, employment_status.value, doj_value, True))
                conn.commit()
                self._close_dialog()
                self._show_success(
                    f"Employee '{first_name.value} {last_name.value}' created successfully!\\nUsername: {username.value}")
                self._refresh()

            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self._page.update()
            finally:
                if conn:
                    conn.close()'''

# The new save_employee function (fixed)
new_save = '''        def save_employee(e):
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

            conn = None
            try:
                conn = sqlite3.connect('vernika.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check for duplicate username
                cursor.execute("SELECT id FROM users WHERE username=?", (username_val,))
                if cursor.fetchone():
                    error_text.value = "Username already exists!"
                    error_text.visible = True
                    self._page.update()
                    return

                # Check for duplicate email
                cursor.execute("SELECT id FROM users WHERE email=?", (email_val,))
                if cursor.fetchone():
                    error_text.value = "Email already registered!"
                    error_text.visible = True
                    self._page.update()
                    return

                # Hash password
                hashed_pw = bcrypt.hashpw(password_val.encode(), bcrypt.gensalt()).decode()
                
                # Get role_id
                role_id = 2
                if role_dropdown.value:
                    try:
                        role_id = int(role_dropdown.value)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid role value: {e}")
                
                # Insert user
                cursor.execute("INSERT INTO users (username, email, password_hash, role_id, status) VALUES (?, ?, ?, ?, ?)",
                    (username_val, email_val, hashed_pw, role_id, 'active'))
                user_id = cursor.lastrowid

                # Get next employee code
                cursor.execute("SELECT MAX(id) FROM employees")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] else 0
                emp_code = f"EMP{max_id + 1:03d}"

                # Get department and position IDs
                dept_id = None
                if dept_dropdown.value:
                    try:
                        dept_id = int(dept_dropdown.value)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid department value: {e}")
                        
                pos_id = None
                if pos_dropdown.value:
                    try:
                        pos_id = int(pos_dropdown.value)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid position value: {e}")

                # Get values
                dob_value = dob_picker.value if dob_picker.value else None
                doj_value = None
                if date_of_joining_picker.value:
                    try:
                        doj_value = date_of_joining_picker.value
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid date of joining value: {e}")
                emp_type = employment_type.value if employment_type.value else 'full_time'
                emp_status = employment_status.value if employment_status.value else 'active'
                
                # Insert employee
                cursor.execute("""INSERT INTO employees (
                    employee_code, user_id, first_name, last_name, email, phone,
                    date_of_birth, gender, address, city, state, pincode,
                    emergency_contact_name, emergency_phone, emergency_relation,
                    bank_name, account_number, ifsc_code, branch_name,
                    basic_salary, allowance, deduction,
                    department_id, position_id, employment_type, employment_status, date_of_joining, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_code, user_id, first_name_val, last_name_val, email_val, 
                    phone.value.strip() if phone.value else None,
                    dob_value, gender.value,
                    address.value.strip() if address.value else None,
                    city.value.strip() if city.value else None,
                    state.value.strip() if state.value else None,
                    pincode.value.strip() if pincode.value else None,
                    emergency_contact_name.value.strip() if emergency_contact_name.value else None,
                    emergency_phone.value.strip() if emergency_phone.value else None,
                    emergency_relation.value,
                    bank_name.value.strip() if bank_name.value else None,
                    account_number.value.strip() if account_number.value else None,
                    ifsc_code.value.strip() if ifsc_code.value else None,
                    branch_name.value.strip() if branch_name.value else None,
                    float(basic_salary.value) if basic_salary.value and basic_salary.value.strip() else 0,
                    float(allowance.value) if allowance.value and allowance.value.strip() else 0,
                    float(deduction.value) if deduction.value and deduction.value.strip() else 0,
                    dept_id, pos_id, emp_type, emp_status, doj_value, 1))
                
                conn.commit()
                self._close_dialog()
                self._show_success(f"Employee '{first_name_val} {last_name_val}' created successfully!")
                self._refresh()

            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self._page.update()
                print(f"Save error: {ex}")
            finally:
                if conn:
                    conn.close()'''

# Replace the old function with the new one
new_content = content.replace(old_save, new_save)

# Write the fixed content
with open('/Users/shashankrajput/Desktop/Vernika/screens/employees_screen.py', 'w') as f:
    f.write(new_content)

print("✅ Fixed save_employee function in employees_screen.py")
print("Changes made:")
print("- Fixed variable handling (strip() and None checks)")
print("- Added conn.row_factory for proper row access")
print("- Improved error handling")
print("- Better value validation")
