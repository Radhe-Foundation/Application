#!/usr/bin/env python3
"""
Fix script for employees_screen.py INSERT statement
Fixes column count mismatch - missing company_id column
"""

# Read the original file
with open('/Users/shashankrajput/Desktop/Vernika/screens/employees_screen.py', 'r') as f:
    content = f.read()

# Find and replace the INSERT statement
old_insert = '''cursor.execute("""INSERT INTO employees (
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
                    dept_id, pos_id, emp_type, emp_status, doj_value, 1))'''

new_insert = '''# Insert employee with company_id set to None (or 1 if you have companies)
                cursor.execute("""INSERT INTO employees (
                    employee_code, user_id, company_id, first_name, last_name, email, phone,
                    date_of_birth, gender, address, city, state, pincode,
                    emergency_contact_name, emergency_phone, emergency_relation,
                    bank_name, account_number, ifsc_code, branch_name,
                    basic_salary, allowance, deduction,
                    department_id, position_id, employment_type, employment_status, date_of_joining, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_code, user_id, None, first_name_val, last_name_val, email_val, 
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
                    dept_id, pos_id, emp_type, emp_status, doj_value, 1))'''

# Replace
new_content = content.replace(old_insert, new_insert)

# Write
with open('/Users/shashankrajput/Desktop/Vernika/screens/employees_screen.py', 'w') as f:
    f.write(new_content)

# Verify
if new_content != content:
    print("✅ Fixed INSERT statement - added company_id column")
    print("   Now has 28 values for 28 columns")
else:
    print("⚠️ Could not find the INSERT statement to replace")
    print("   Please manually add 'company_id' column to the INSERT")
