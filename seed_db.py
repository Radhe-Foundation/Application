"""
Vernika HRA - Safe Seed Script (Guarded)
This script is intentionally disabled by default to avoid accidental
seeding of demo data into production databases.

Usage:
  python seed_db.py --dev

When run with `--dev` it will perform a minimal in-memory or development
seed. The original sqlite-based seeder was removed to enforce use of the
application's SQLAlchemy/Supabase connection and migration path.
"""

import argparse
import sys

from database.connection import get_db_session


def main(dev: bool = False):
    if not dev:
        print("seed_db.py is disabled by default. Use --dev to run it in development.")
        print("This project uses SQLAlchemy and Supabase — use migration scripts to load production data.")
        sys.exit(0)

    # Developer mode: provide a minimal helper to call higher-level seed functions
    print("Dev seeding mode enabled. Running minimal dev seed...")

    # Example: you can implement calls to database.operations here
    # from database import operations
    # db = get_db_session()
    # try:
    #     operations.create_default_roles(db)
    # finally:
    #     db.close()

    print("✓ Dev seeding finished (no-op). Implement seeding via database.operations as needed.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vernika dev seed script')
    parser.add_argument('--dev', action='store_true',
                        help='Enable development seeding')
    args = parser.parse_args()
    main(dev=args.dev)
