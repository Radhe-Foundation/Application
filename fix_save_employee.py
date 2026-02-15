#!/usr/bin/env python3
"""
Deprecated: fix_save_employee.py

This helper script previously attempted to patch `screens/employees_screen.py`
and contained inline SQLite usage. The application now uses SQLAlchemy via
`database.connection.get_db_session()`. Keep `employees_screen.py` under
version control and edit it directly if further fixes are required.

If you need an automated migration, consider using `scripts/migrate_fix_schema.py`
or the central `database` helpers. This script is intentionally inert to avoid
reintroducing direct sqlite usage.
"""

import sys


def main():
    print("fix_save_employee.py is deprecated and does not perform any changes.")
    print("Edit screens/employees_screen.py directly to adjust save behavior.")


if __name__ == '__main__':
    main()
