"""
Vernika HRA - Excel Export Utilities
Export data to Excel format with proper ordering for Google Sheets compatibility.
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from database.connection import get_db_session


class ExcelExporter:
    """Export data to Excel-compatible CSV format using SQLAlchemy sessions"""

    def __init__(self):
        pass

    def export_employees(self, include_salary: bool = False) -> str:
        """
        Export all employees to CSV format.

        Args:
            include_salary: Include salary information (default: False for privacy)

        Returns:
            CSV formatted string
        """
        session = get_db_session()
        query = text("""
            SELECT
                e.id,
                e.employee_code,
                e.first_name,
                e.last_name,
                e.email,
                e.phone,
                d.name as department,
                p.title as position,
                e.employment_type,
                e.employment_status,
                e.date_of_joining,
                e.is_active,
                e.created_at
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN positions p ON e.position_id = p.id
            ORDER BY e.id ASC
        """

        if include_salary:
            query=text("""
                SELECT
                    e.id,
                    e.employee_code,
                    e.first_name,
                    e.last_name,
                    e.email,
                    e.phone,
                    d.name as department,
                    p.title as position,
                    e.employment_type,
                    e.employment_status,
                    e.date_of_joining,
                    e.is_active,
                    e.basic_salary,
                    e.allowance,
                    e.deduction,
                    (e.basic_salary + e.allowance - e.deduction) as net_salary,
                    e.created_at
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                ORDER BY e.id ASC
            """
        result=session.execute(query)
        employees=result.mappings().all()

        # Generate CSV
        output=io.StringIO()
        writer=csv.writer(output)

        # Write header
        if include_salary:
            headers=[
                'ID', 'Employee Code', 'First Name', 'Last Name', 'Email', 'Phone',
                'Department', 'Position', 'Employment Type', 'Employment Status',
                'Date of Joining', 'Active', 'Basic Salary', 'Allowance',
                'Deduction', 'Net Salary', 'Created At'
            ]
        else:
            headers=[
                'ID', 'Employee Code', 'First Name', 'Last Name', 'Email', 'Phone',
                'Department', 'Position', 'Employment Type', 'Employment Status',
                'Date of Joining', 'Active', 'Created At'
            ]

        writer.writerow(headers)

        # Write data rows
        for emp in employees:
            row=[
                emp['id'],
                emp['employee_code'],
                emp['first_name'],
                emp['last_name'],
                emp['email'],
                emp['phone'],
                emp['department'] or '',
                emp['position'] or '',
                emp['employment_type'] or '',
                emp['employment_status'] or '',
                emp['date_of_joining'] or '',
                'Yes' if emp['is_active'] else 'No',
            ]

            if include_salary:
                row.extend([
                    emp['basic_salary'] or 0,
                    emp['allowance'] or 0,
                    emp['deduction'] or 0,
                    emp['net_salary'] or 0,
                ])

            row.append(emp['created_at'] or '')
            writer.writerow(row)

        return output.getvalue()

    def export_attendance(self, start_date: str=None, end_date: str=None) -> str:
        """
        Export attendance records to CSV format.

        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
        """
        session=get_db_session()
        query="""
            SELECT
                a.id,
                a.employee_id,
                e.employee_code,
                e.first_name || ' ' || e.last_name as employee_name,
                d.name as department,
                a.date,
                a.check_in,
                a.check_out,
                a.status,
                a.working_hours
            FROM attendances a
            LEFT JOIN employees e ON a.employee_id = e.id
            LEFT JOIN departments d ON e.department_id = d.id
        """

        sql_text=query
        conditions=[]
        params: Dict[str, Any]={}
        if start_date:
            conditions.append("a.date >= :start_date")
            params['start_date']=start_date
        if end_date:
            conditions.append("a.date <= :end_date")
            params['end_date']=end_date
        if conditions:
            sql_text += " WHERE " + " AND ".join(conditions)
        sql_text += " ORDER BY a.date DESC, e.id ASC"

        result=session.execute(text(sql_text), params)
        records=result.mappings().all()

        output=io.StringIO()
        writer=csv.writer(output)

        writer.writerow([
            'ID', 'Employee ID', 'Employee Code', 'Employee Name', 'Department',
            'Date', 'Check In', 'Check Out', 'Status', 'Working Hours'
        ])

        for rec in records:
            writer.writerow([
                rec['id'],
                rec['employee_id'],
                rec['employee_code'],
                rec['employee_name'],
                rec['department'] or '',
                rec['date'],
                rec['check_in'] or '',
                rec['check_out'] or '',
                rec['status'],
                rec['working_hours'] or 0
            ])

        return output.getvalue()

    def export_leave_requests(self) -> str:
        """Export leave requests to CSV format."""
        session=get_db_session()
        result=session.execute(text("""
            SELECT
                l.id,
                e.employee_code,
                e.first_name || ' ' || e.last_name as employee_name,
                d.name as department,
                l.start_date,
                l.end_date,
                l.days_requested,
                l.reason,
                l.status,
                l.created_at
            FROM leave_requests l
            LEFT JOIN employees e ON l.employee_id = e.id
            LEFT JOIN departments d ON e.department_id = d.id
            ORDER BY l.created_at DESC, l.id DESC
        """)
        records=result.mappings().all()

        output=io.StringIO()
        writer=csv.writer(output)

        writer.writerow([
            'ID', 'Employee Code', 'Employee Name', 'Department',
            'Start Date', 'End Date', 'Days Requested', 'Reason', 'Status', 'Created At'
        ])

        for rec in records:
            writer.writerow([
                rec['id'],
                rec['employee_code'],
                rec['employee_name'],
                rec['department'] or '',
                rec['start_date'],
                rec['end_date'],
                rec['days_requested'],
                rec['reason'],
                rec['status'],
                rec['created_at']
            ])

        return output.getvalue()

    def export_departments(self) -> str:
        """Export departments to CSV format."""
        session=get_db_session()
        result=session.execute(text("""
            SELECT
                d.id,
                d.name,
                d.code,
                d.description,
                d.budget,
                d.location,
                d.contact_email,
                d.contact_phone,
                e.first_name || ' ' || e.last_name as head_name,
                d.created_at
            FROM departments d
            LEFT JOIN employees e ON d.head_id = e.id
            ORDER BY d.id ASC
        """)
        records=result.mappings().all()

        output=io.StringIO()
        writer=csv.writer(output)

        writer.writerow([
            'ID', 'Name', 'Code', 'Description', 'Budget', 'Location',
            'Contact Email', 'Contact Phone', 'Head/Manager', 'Created At'
        ])

        for rec in records:
            writer.writerow([
                rec['id'],
                rec['name'],
                rec['code'],
                rec['description'] or '',
                rec['budget'] or 0,
                rec['location'] or '',
                rec['contact_email'] or '',
                rec['contact_phone'] or '',
                rec['head_name'] or 'Not Assigned',
                rec['created_at'] or ''
            ])

        return output.getvalue()

    def export_positions(self) -> str:
        """Export positions to CSV format."""
        session=get_db_session()
        result=session.execute(text("""
            SELECT
                p.id,
                p.code,
                p.title,
                p.description,
                d.name as department,
                p.min_salary,
                p.max_salary,
                CASE WHEN p.is_active = 1 THEN 'Active' ELSE 'Inactive' END as status,
                p.created_at
            FROM positions p
            LEFT JOIN departments d ON p.department_id = d.id
            ORDER BY p.id ASC
        """)
        records=result.mappings().all()

        output=io.StringIO()
        writer=csv.writer(output)

        writer.writerow([
            'ID', 'Code', 'Title', 'Description', 'Department',
            'Min Salary', 'Max Salary', 'Status', 'Created At'
        ])

        for rec in records:
            writer.writerow([
                rec['id'],
                rec['code'],
                rec['title'],
                rec['description'] or '',
                rec['department'] or '',
                rec['min_salary'] or 0,
                rec['max_salary'] or 0,
                rec['status'],
                rec['created_at'] or ''
            ])

        return output.getvalue()

    def export_tasks(self) -> str:
        """Export tasks to CSV format."""
        session=get_db_session()
        result=session.execute(text("""
            SELECT
                t.id,
                t.title,
                t.description,
                t.priority,
                t.status,
                t.due_date,
                e_assigned.first_name || ' ' || e_assigned.last_name as assigned_to,
                e_created.first_name || ' ' || e_created.last_name as created_by,
                t.estimated_hours,
                t.actual_hours,
                t.created_at
            FROM tasks t
            LEFT JOIN employees e_assigned ON t.assigned_to_id = e_assigned.id
            LEFT JOIN employees e_created ON t.created_by_id = e_created.id
            ORDER BY t.created_at DESC, t.id DESC
        """)
        records=result.mappings().all()

        output=io.StringIO()
        writer=csv.writer(output)

        writer.writerow([
            'ID', 'Title', 'Description', 'Priority', 'Status', 'Due Date',
            'Assigned To', 'Created By', 'Estimated Hours', 'Actual Hours', 'Created At'
        ])

        for rec in records:
            writer.writerow([
                rec['id'],
                rec['title'],
                rec['description'] or '',
                rec['priority'],
                rec['status'],
                rec['due_date'] or '',
                rec['assigned_to'] or 'Unassigned',
                rec['created_by'] or '',
                rec['estimated_hours'] or 0,
                rec['actual_hours'] or 0,
                rec['created_at'] or ''
            ])

        return output.getvalue()

    def save_to_file(self, content: str, filename: str) -> str:
        """
        Save CSV content to a file.

        Args:
            content: CSV content string
            filename: Output filename (without extension)

        Returns:
            Full path to saved file
        """
        from pathlib import Path

        # Create reports directory if it doesn't exist
        reports_dir=Path('reports')
        reports_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath=reports_dir / f"{filename}_{timestamp}.csv"

        # Write content
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            f.write(content)

        return str(filepath)


def get_exporter(db_path: str='vernika.db') -> ExcelExporter:
    """Get Excel exporter instance"""
    return ExcelExporter(db_path)


if __name__ == "__main__":
    exporter=get_exporter()

    # Test exports
    print("Testing Excel Export...")
    print()

    # Export employees
    print("1. Exporting employees...")
    employees_csv=exporter.export_employees()
    filepath=exporter.save_to_file(employees_csv, "employees")
    print(f"   Saved to: {filepath}")
    print(f"   Preview (first 500 chars): {employees_csv[:500]}...")
    print()

    # Export departments
    print("2. Exporting departments...")
    depts_csv=exporter.export_departments()
    filepath=exporter.save_to_file(depts_csv, "departments")
    print(f"   Saved to: {filepath}")
    print()

    # Export attendance
    print("3. Exporting attendance...")
    attendance_csv=exporter.export_attendance()
    filepath=exporter.save_to_file(attendance_csv, "attendance")
    print(f"   Saved to: {filepath}")
    print()

    # Export leave requests
    print("4. Exporting leave requests...")
    leaves_csv=exporter.export_leave_requests()
    filepath=exporter.save_to_file(leaves_csv, "leave_requests")
    print(f"   Saved to: {filepath}")
    print()

    # Export with salary
    print("5. Exporting employees with salary...")
    salary_csv=exporter.export_employees(include_salary=True)
    filepath=exporter.save_to_file(salary_csv, "employees_salary")
    print(f"   Saved to: {filepath}")
    print()

    print("All exports completed successfully!")
