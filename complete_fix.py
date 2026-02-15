"""
Complete Fix Runner (SQLAlchemy-backed)

Delegates to safer, SQLAlchemy-based fixers and migrations.
"""

from fix_user import fix_users
from add_test_users import main as add_test_users_main
from scripts.migrate_presence import create_sample_groups


def main():
    print("Running complete fix sequence...")
    fix_users()
    add_test_users_main()
    create_sample_groups()
    print("Done. Review logs for details.")


if __name__ == '__main__':
    main()
