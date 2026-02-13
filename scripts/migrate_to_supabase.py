"""
Vernika - Database Migration Script
Migrate from SQLite to PostgreSQL (Supabase)

Usage:
    python scripts/migrate_to_supabase.py [--source vernika.db] [--dry-run]
    python scripts/migrate_to_supabase.py --enable-rls-only  # Enable RLS on existing DB
    python scripts/enable_rls.py  # Run RLS migration separately

Prerequisites:
    1. Create a Supabase project: https://supabase.com
    2. Get your database credentials from Settings > Database
    3. Update your .env file with Supabase credentials
    4. Install dependencies: pip install psycopg2-binary
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text, inspect
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def enable_rls(pg_engine, dry_run=True):
    """
    Enable Row Level Security on all tables
    This is called after data migration to secure the database
    """
    print("\n[RLS] Enabling Row Level Security...")

    rls_sql_file = Path(__file__).parent / "supabase_rls_migration.sql"

    if not rls_sql_file.exists():
        print(f"  [ERROR] RLS SQL file not found: {rls_sql_file}")
        return False

    with open(rls_sql_file, 'r') as f:
        sql_content = f.read()

    # Execute RLS SQL
    with pg_engine.connect() as conn:
        # Split into statements and execute
        statements = []
        current = []

        for line in sql_content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('--') or not stripped:
                continue
            current.append(line)
            if stripped.endswith(';'):
                statements.append('\n'.join(current))
                current = []

        for i, stmt in enumerate(statements, 1):
            try:
                if not dry_run:
                    conn.execute(text(stmt))
                if dry_run:
                    # Print first few statements for preview
                    if i <= 3:
                        print(f"  [PREVIEW] {stmt[:80]}...")
            except Exception as e:
                if not dry_run:
                    print(f"  [ERROR] Statement {i}: {e}")

        if not dry_run:
            conn.commit()
            print("  [OK] RLS enabled successfully")
        else:
            print(
                f"  [DRY RUN] Would execute {len(statements)} RLS statements")

    return True


def get_sqlite_engine(db_path):
    """Create SQLite engine for source database"""
    return create_engine(f"sqlite:///{db_path}")


def get_pg_engine(connection_string):
    """Create PostgreSQL engine for target database"""
    return create_engine(connection_string)


def get_all_tables(engine):
    """Get all table names from database"""
    inspector = inspect(engine)
    return inspector.get_table_names()


def migrate_table(source_engine, pg_engine, table_name, dry_run=True):
    """Migrate a single table from SQLite to PostgreSQL"""
    # Get data from SQLite
    with source_engine.connect() as source_conn:
        result = source_conn.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()
        columns = result.keys()

        if not rows:
            print(f"  [SKIP] {table_name}: No data")
            return 0

        print(f"  [MIGRATE] {table_name}: {len(rows)} rows")

        if dry_run:
            print(f"     [DRY RUN] Would insert {len(rows)} rows")
            return len(rows)

        # Insert into PostgreSQL
        columns_str = ", ".join([f'"{col}"' for col in columns])
        placeholders = ", ".join([f":{col}" for col in columns])
        insert_sql = text(
            f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})')

        # Create session and migrate
        Session = sessionmaker(bind=pg_engine)
        session = Session()
        try:
            for row in rows:
                row_dict = dict(zip(columns, row))
                session.execute(insert_sql, row_dict)
            session.commit()
            print(f"  [OK] {table_name}: {len(rows)} rows migrated")
            return len(rows)
        except Exception as e:
            session.rollback()
            print(f"  [ERROR] {table_name}: {e}")
            return 0
        finally:
            session.close()


def migrate_sequences(pg_engine, dry_run=True):
    """Migrate SQLite auto-increment sequences to PostgreSQL"""
    print("\n[SEQUENCES] Migrating auto-increment sequences...")
    inspector = inspect(pg_engine)
    tables = inspector.get_table_names()
    for table in tables:
        pk_column = inspector.get_pk_constraint(table)
        if not pk_column:
            continue
        pk_columns = pk_column.get('constrained_columns', [])
        if not pk_columns:
            continue
        column = pk_columns[0]
        with pg_engine.connect() as conn:
            result = conn.execute(
                text(f'SELECT COALESCE(MAX("{column}"), 0) + 1 FROM "{table}"'))
            max_id = result.scalar()
        if dry_run:
            print(f"  [DRY RUN] {table}.{column} -> {max_id}")
        else:
            sequence_name = f"{table}_{column}_seq"
            with pg_engine.connect() as conn:
                conn.execute(
                    text(f"SELECT setval('{sequence_name}', {max_id}, false)"))
            print(f"  [OK] {table}.{column} sequence set to {max_id}")


def create_tables(pg_engine, dry_run=True):
    """Create all tables in PostgreSQL using SQLAlchemy models"""
    print("\n[TABLES] Creating tables in PostgreSQL...")
    from database.connection import Base
    if dry_run:
        print("  [DRY RUN] Would create tables:")
        for table in Base.metadata.sorted_tables:
            print(f"     - {table.name}")
    else:
        Base.metadata.create_all(pg_engine)
        print("  [OK] All tables created")


def verify_migration(source_engine, pg_engine):
    """Verify migration by comparing row counts"""
    print("\n[VERIFY] Checking data migration...")
    source_tables = get_all_tables(source_engine)
    target_tables = get_all_tables(pg_engine)
    results = {}
    for table in source_tables:
        if table not in target_tables:
            print(f"  [MISSING] {table}")
            continue
        with source_engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            src_count = result.scalar()
        with pg_engine.connect() as conn:
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            tgt_count = result.scalar()
        status = "OK" if src_count == tgt_count else "MISMATCH"
        print(f"  [{status}] {table}: SQLite={src_count}, PG={tgt_count}")
        results[table] = {'source': src_count, 'target': tgt_count}
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Vernika from SQLite to Supabase")
    parser.add_argument("--source", default="vernika.db",
                        help="Source SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Dry run only")
    parser.add_argument("--skip-data", action="store_true",
                        help="Skip data migration")
    parser.add_argument("--enable-rls", action="store_true",
                        help="Enable RLS (Row Level Security) on existing tables")
    parser.add_argument("--skip-rls", action="store_true",
                        help="Skip RLS setup (for faster migration)")
    args = parser.parse_args()

    print("=" * 60)
    print("Vernika DB Migration: SQLite -> Supabase (PostgreSQL)")
    print("=" * 60)

    from dotenv import load_dotenv
    load_dotenv()

    source_db = args.source
    target_url = os.getenv("DATABASE_URL")

    if not os.path.exists(source_db):
        print(f"[ERROR] Source database not found: {source_db}")
        sys.exit(1)

    if not target_url:
        print("[ERROR] No DATABASE_URL in .env")
        sys.exit(1)

    print(f"\n[SOURCE] {source_db} (SQLite)")
    print(f"[TARGET] Supabase PostgreSQL")
    print(f"[MODE] {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")

    source_engine = get_sqlite_engine(source_db)
    pg_engine = get_pg_engine(target_url)

    # Test connections
    try:
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] SQLite connected")
    except Exception as e:
        print(f"[ERROR] SQLite: {e}")
        sys.exit(1)

    try:
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] PostgreSQL connected")
    except Exception as e:
        print(f"[ERROR] PostgreSQL: {e}")
        sys.exit(1)

    tables = get_all_tables(source_engine)
    print(f"\n[TABLES] Found {len(tables)} tables to migrate")

    # Create tables
    if not args.skip_data:
        create_tables(pg_engine, dry_run=args.dry_run)

    # Migrate data
    if not args.skip_data:
        print("\n[DATA] Migrating data...")
        total_rows = 0
        for table in tables:
            rows = migrate_table(source_engine, pg_engine,
                                 table, dry_run=args.dry_run)
            total_rows += rows

        if not args.dry_run:
            print(f"\n[COMPLETE] Migrated {total_rows} total rows")
            migrate_sequences(pg_engine, dry_run=args.dry_run)
            verify_migration(source_engine, pg_engine)

    # Enable RLS
    if not args.skip_rls and not args.dry_run:
        enable_rls(pg_engine, dry_run=args.dry_run)
    elif args.enable_rls:
        enable_rls(pg_engine, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    if args.dry_run:
        print("[DONE] Dry run complete - no changes made")
    else:
        print("[DONE] Migration complete!")
        print("\n[NEXT STEPS]")
        print("  1. Enable RLS for security:")
        print("     python scripts/enable_rls.py")
        print("  2. Test the application: python main.py")
        print("  3. Keep vernika.db as backup")
        print("  4. Update team members with Supabase URL")
    print("=" * 60)


if __name__ == "__main__":
    main()
