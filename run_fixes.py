#!/usr/bin/env python3
"""
Vernika HRA - Production Fixes Runner
Run all fixes to make the application production-ready.
"""

import sys
import subprocess
import os

# Color codes for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print a header"""
    print()
    print(BLUE + "=" * 60 + RESET)
    print(BLUE + text + RESET)
    print(BLUE + "=" * 60 + RESET)
    print()


def print_step(step, text):
    """Print a step"""
    print(f"{GREEN}[{step}]{RESET} {text}")


def run_command(cmd, description):
    """Run a command and print result"""
    print(f"  Running: {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ✓ {description} completed")
            return True
        else:
            print(f"  ✗ {description} failed")
            if result.stdout:
                print(f"    Output: {result.stdout[:200]}")
            if result.stderr:
                print(f"    Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ {description} error: {e}")
        return False


def check_requirements():
    """Check if required packages are installed"""
    print_step(1, "Checking requirements")

    required_packages = [
        ('flet', 'flet'),
        ('sqlalchemy', 'sqlalchemy'),
        ('bcrypt', 'bcrypt'),
    ]

    all_ok = True
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✓ {package_name} is installed")
        except ImportError:
            print(f"  ✗ {package_name} is NOT installed")
            all_ok = False

    return all_ok


def verify_files():
    """Verify all critical files exist"""
    print_step(2, "Verifying critical files")

    critical_files = [
        ('main.py', 'Main application'),
        ('config.py', 'Configuration'),
        ('database/models.py', 'Database models'),
        ('database/connection.py', 'Database connection'),
        ('screens/employees_screen.py', 'Employees screen'),
        ('screens/documents_screen.py', 'Documents screen'),
        ('screens/dashboard_screen.py', 'Dashboard screen'),
        ('screens/admin_screen.py', 'Admin screen'),
        ('fix_database.py', 'Database fix script'),
        ('utils/excel_export.py', 'Excel export utility'),
        ('utils/google_sheets.py', 'Google Sheets utility'),
    ]

    all_ok = True
    for filepath, description in critical_files:
        if os.path.exists(filepath):
            print(f"  ✓ {description}: {filepath}")
        else:
            print(f"  ✗ {description}: {filepath} - MISSING!")
            all_ok = False

    return all_ok


def run_syntax_check():
    """Run syntax check on Python files"""
    print_step(3, "Running syntax check")

    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                python_files.append(filepath)

    errors = []
    for filepath in python_files:
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), filepath, 'exec')
            print(f"  ✓ {filepath}")
        except SyntaxError as e:
            print(f"  ✗ {filepath}: Syntax error at line {e.lineno}")
            errors.append(filepath)

    return len(errors) == 0


def fix_database():
    """Run database fixes"""
    print_step(4, "Running database fixes")
    return run_command("python fix_database.py", "Database fixes")


def export_test():
    """Test export functionality"""
    print_step(5, "Testing Excel export")

    # Add utils to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    try:
        from utils.excel_export import get_exporter
        exporter = get_exporter()

        # Test employee export
        employees_csv = exporter.export_employees()
        print(
            f"  ✓ Employee export: {len(employees_csv.split(chr(10)))} lines")

        # Test department export
        depts_csv = exporter.export_departments()
        print(f"  ✓ Department export: {len(depts_csv.split(chr(10)))} lines")

        # Save test file
        filepath = exporter.save_to_file(employees_csv, "test_export")
        print(f"  ✓ Test export saved to: {filepath}")

        return True
    except Exception as e:
        print(f"  ✗ Export test failed: {e}")
        return False


def print_summary():
    """Print summary of fixes"""
    print_header("Fixes Summary")

    print("""
Phase 1: Critical Bug Fixes
├── Fixed Add Employee button syntax error
├── Fixed FilePicker in documents screen
├── Verified navigation to employees screen
└── Fixed DataTable column parameters

Phase 2: Database Fixes
├── Added missing columns (created_at, updated_at)
├── Added indexes for performance
├── Created foreign key triggers
└── Created database views

Phase 3: Export & Cloud Integration
├── Created Excel export utility
├── Created Google Sheets integration
├── Added CSV export for all tables
└── Defined sync configuration

Phase 4: Ready for Production
├── Database ready for PostgreSQL/MySQL
├── Export ready for Google Sheets
└── All screens functional

Next Steps:
1. Run: python fix_database.py
2. Test: python run_fixes.py
3. Start: python main.py
4. Export data to Excel/Google Sheets
""")


def main():
    """Main entry point"""
    print_header("Vernika HRA - Production Fixes")

    # Run all checks
    checks = [
        ("Requirements Check", check_requirements),
        ("File Verification", verify_files),
        ("Syntax Check", run_syntax_check),
        ("Database Fixes", fix_database),
        ("Export Test", export_test),
    ]

    results = []
    for name, func in checks:
        try:
            result = func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ {name} error: {e}")
            results.append((name, False))

    # Print summary
    print_header("Results")

    all_passed = True
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False

    print()
    if all_passed:
        print(GREEN + "All checks passed!" + RESET)
        print_summary()
        return 0
    else:
        print(RED + "Some checks failed. Please review the output above." + RESET)
        return 1


if __name__ == "__main__":
    sys.exit(main())
