#!/usr/bin/env python3
"""
Vernika Database Migration Management Script

This script provides commands to:
1. Run all necessary migrations
2. Check current migration status
3. Reset the database (dangerous - clears all data)
4. Clean up old migration files

Usage:
    python scripts/manage_migrations.py run      - Run all migrations
    python scripts/manage_migrations.py status   - Check migration status
    python scripts/manage_migrations.py reset    - Reset database (DANGEROUS)
    python scripts/manage_migrations.py cleanup   - Clean up old SQL files
"""

from database.connection import get_engine, get_db_session
from sqlalchemy import text, inspect
import os
import sys
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Migration definitions - consolidated from multiple files
# This is the ONLY place migrations should be defined going forward
MIGRATIONS = [
    {
        "name": "create_companies_table",
        "description": "Create companies table",
        "sql": """
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                address TEXT
            )
        """
    },
    {
        "name": "create_roles_table",
        "description": "Create roles table",
        "sql": """
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                level INTEGER DEFAULT 1,
                permissions JSON DEFAULT '{}'
            )
        """
    },
    {
        "name": "create_users_table",
        "description": "Create users table",
        "sql": """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role_id INTEGER REFERENCES roles(id),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                is_online BOOLEAN DEFAULT FALSE,
                session_token VARCHAR(255),
                last_login TIMESTAMP,
                last_ip VARCHAR(50)
            )
        """
    },
    {
        "name": "create_departments_table",
        "description": "Create departments table",
        "sql": """
            CREATE TABLE IF NOT EXISTS departments (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                description TEXT,
                head_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                budget DECIMAL(12,2) DEFAULT 0,
                location VARCHAR(200),
                contact_email VARCHAR(100),
                contact_phone VARCHAR(20),
                parent_dept_id INTEGER
            )
        """
    },
    {
        "name": "create_positions_table",
        "description": "Create positions table",
        "sql": """
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                description TEXT,
                department_id INTEGER REFERENCES departments(id),
                is_active BOOLEAN DEFAULT TRUE,
                min_salary FLOAT,
                max_salary FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_employees_table",
        "description": "Create employees table",
        "sql": """
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                employee_code VARCHAR(20) UNIQUE NOT NULL,
                user_id INTEGER UNIQUE REFERENCES users(id),
                company_id INTEGER REFERENCES companies(id),
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                date_of_birth DATE,
                gender VARCHAR(20),
                email VARCHAR(100),
                phone VARCHAR(20),
                department_id INTEGER REFERENCES departments(id),
                position_id INTEGER REFERENCES positions(id),
                date_of_joining DATE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                employment_type VARCHAR(50) DEFAULT 'full_time',
                employment_status VARCHAR(50) DEFAULT 'active',
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(100),
                pincode VARCHAR(20),
                emergency_contact_name VARCHAR(200),
                emergency_phone VARCHAR(20),
                emergency_relation VARCHAR(50),
                bank_name VARCHAR(200),
                account_number VARCHAR(50),
                ifsc_code VARCHAR(50),
                branch_name VARCHAR(200),
                basic_salary FLOAT DEFAULT 0,
                allowance FLOAT DEFAULT 0,
                deduction FLOAT DEFAULT 0,
                profile_photo VARCHAR(500),
                profile_photo_data BYTEA
            )
        """
    },
    {
        "name": "create_attendances_table",
        "description": "Create attendances table",
        "sql": """
            CREATE TABLE IF NOT EXISTS attendances (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                date DATE NOT NULL,
                check_in TIMESTAMP,
                check_out TIMESTAMP,
                status VARCHAR(20) NOT NULL,
                working_hours FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(employee_id, date)
            )
        """
    },
    {
        "name": "create_holidays_table",
        "description": "Create holidays table",
        "sql": """
            CREATE TABLE IF NOT EXISTS holidays (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                date DATE NOT NULL,
                day VARCHAR(20) NOT NULL,
                holiday_type VARCHAR(50) DEFAULT 'national',
                is_optional BOOLEAN DEFAULT FALSE,
                year INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(id)
            )
        """
    },
    {
        "name": "create_leave_type_configs_table",
        "description": "Create leave_type_configs table",
        "sql": """
            CREATE TABLE IF NOT EXISTS leave_type_configs (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                display_name VARCHAR(50) NOT NULL,
                max_days_per_year INTEGER DEFAULT 0,
                is_paid BOOLEAN DEFAULT TRUE,
                color VARCHAR(20) DEFAULT '#2E86AB'
            )
        """
    },
    {
        "name": "create_leave_balances_table",
        "description": "Create leave_balances table",
        "sql": """
            CREATE TABLE IF NOT EXISTS leave_balances (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                leave_type_id INTEGER NOT NULL REFERENCES leave_type_configs(id),
                year INTEGER NOT NULL,
                total_days FLOAT DEFAULT 0,
                used_days FLOAT DEFAULT 0
            )
        """
    },
    {
        "name": "create_leave_requests_table",
        "description": "Create leave_requests table",
        "sql": """
            CREATE TABLE IF NOT EXISTS leave_requests (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                leave_type_id INTEGER NOT NULL REFERENCES leave_type_configs(id),
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                days_requested FLOAT NOT NULL,
                reason TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_tasks_table",
        "description": "Create tasks table",
        "sql": """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                assigned_to_id INTEGER NOT NULL REFERENCES employees(id),
                created_by_id INTEGER NOT NULL REFERENCES employees(id),
                status VARCHAR(20) DEFAULT 'todo',
                priority VARCHAR(20) DEFAULT 'medium',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category VARCHAR(50),
                project_name VARCHAR(200),
                estimated_hours DECIMAL(5,2) DEFAULT 0,
                actual_hours DECIMAL(5,2) DEFAULT 0,
                start_date DATE,
                end_date DATE,
                task_type VARCHAR(50) DEFAULT 'feature',
                attachments TEXT,
                time_spent DECIMAL(5,2) DEFAULT 0
            )
        """
    },
    {
        "name": "create_task_comments_table",
        "description": "Create task_comments table",
        "sql": """
            CREATE TABLE IF NOT EXISTS task_comments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL REFERENCES tasks(id),
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_announcements_table",
        "description": "Create announcements table",
        "sql": """
            CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'general',
                priority VARCHAR(20) DEFAULT 'normal',
                author VARCHAR(100) DEFAULT 'Admin',
                views INTEGER DEFAULT 0,
                created_at DATE DEFAULT CURRENT_DATE,
                target_audience VARCHAR(50) DEFAULT 'all',
                target_department_id INTEGER REFERENCES departments(id),
                target_employee_ids TEXT
            )
        """
    },
    {
        "name": "create_app_settings_table",
        "description": "Create app_settings table",
        "sql": """
            CREATE TABLE IF NOT EXISTS app_settings (
                id SERIAL PRIMARY KEY,
                key VARCHAR(100) UNIQUE NOT NULL,
                value TEXT,
                description VARCHAR(500),
                category VARCHAR(50) DEFAULT 'general',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_teams_table",
        "description": "Create teams table",
        "sql": """
            CREATE TABLE IF NOT EXISTS teams (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_projects_table",
        "description": "Create projects table",
        "sql": """
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                client_name VARCHAR(200),
                start_date DATE,
                end_date DATE,
                budget FLOAT DEFAULT 0,
                status VARCHAR(50) DEFAULT 'planning',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_audit_logs_table",
        "description": "Create audit_logs table",
        "sql": """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_messages_table",
        "description": "Create messages table",
        "sql": """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER NOT NULL REFERENCES employees(id),
                receiver_id INTEGER NOT NULL REFERENCES employees(id),
                content TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_chat_groups_table",
        "description": "Create chat_groups table",
        "sql": """
            CREATE TABLE IF NOT EXISTS chat_groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_by INTEGER NOT NULL REFERENCES users(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_chat_group_members_table",
        "description": "Create chat_group_members table",
        "sql": """
            CREATE TABLE IF NOT EXISTS chat_group_members (
                id SERIAL PRIMARY KEY,
                group_id INTEGER NOT NULL REFERENCES chat_groups(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                role VARCHAR(20) DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_chat_messages_table",
        "description": "Create chat_messages table",
        "sql": """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER NOT NULL REFERENCES users(id),
                group_id INTEGER REFERENCES chat_groups(id),
                receiver_id INTEGER REFERENCES users(id),
                content TEXT NOT NULL,
                message_type VARCHAR(20) DEFAULT 'text',
                is_read BOOLEAN DEFAULT FALSE,
                has_attachment BOOLEAN DEFAULT FALSE,
                attachment_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_email_messages_table",
        "description": "Create email_messages table",
        "sql": """
            CREATE TABLE IF NOT EXISTS email_messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER NOT NULL REFERENCES users(id),
                subject VARCHAR(200) NOT NULL,
                body TEXT NOT NULL,
                category VARCHAR(50) DEFAULT 'general',
                is_read BOOLEAN DEFAULT FALSE,
                is_draft BOOLEAN DEFAULT FALSE,
                has_attachment BOOLEAN DEFAULT FALSE,
                attachment_path VARCHAR(500),
                attachment_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_email_recipients_table",
        "description": "Create email_recipients table",
        "sql": """
            CREATE TABLE IF NOT EXISTS email_recipients (
                id SERIAL PRIMARY KEY,
                email_id INTEGER NOT NULL REFERENCES email_messages(id),
                recipient_id INTEGER NOT NULL REFERENCES users(id),
                recipient_type VARCHAR(10) DEFAULT 'to',
                is_read BOOLEAN DEFAULT FALSE,
                read_at TIMESTAMP
            )
        """
    },
    {
        "name": "create_meetings_table",
        "description": "Create meetings table",
        "sql": """
            CREATE TABLE IF NOT EXISTS meetings (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                organizer_id INTEGER NOT NULL REFERENCES users(id),
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                meeting_link VARCHAR(500),
                status VARCHAR(20) DEFAULT 'scheduled',
                is_recurring BOOLEAN DEFAULT FALSE,
                recurrence_pattern VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_meeting_participants_table",
        "description": "Create meeting_participants table",
        "sql": """
            CREATE TABLE IF NOT EXISTS meeting_participants (
                id SERIAL PRIMARY KEY,
                meeting_id INTEGER NOT NULL REFERENCES meetings(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                status VARCHAR(20) DEFAULT 'pending',
                response_at TIMESTAMP,
                joined_at TIMESTAMP,
                left_at TIMESTAMP
            )
        """
    },
    {
        "name": "create_app_notifications_table",
        "description": "Create app_notifications table",
        "sql": """
            CREATE TABLE IF NOT EXISTS app_notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                sender_id INTEGER REFERENCES users(id),
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                notification_type VARCHAR(50) NOT NULL,
                priority VARCHAR(20) DEFAULT 'medium',
                related_entity_type VARCHAR(50),
                related_entity_id INTEGER,
                is_read BOOLEAN DEFAULT FALSE,
                read_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_documents_table",
        "description": "Create documents table",
        "sql": """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_type VARCHAR(50),
                file_size INTEGER,
                uploaded_by INTEGER NOT NULL REFERENCES users(id),
                description TEXT,
                category VARCHAR(50) DEFAULT 'general',
                group_id INTEGER REFERENCES chat_groups(id),
                is_public BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    {
        "name": "create_time_off_requests_table",
        "description": "Create time_off_requests table",
        "sql": """
            CREATE TABLE IF NOT EXISTS time_off_requests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                leave_type VARCHAR(50) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                reason TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_by INTEGER REFERENCES employees(id)
            )
        """
    },
]


def get_existing_tables():
    """Get list of existing tables in database"""
    engine = get_engine()
    inspector = inspect(engine)
    return inspector.get_table_names()


def get_executed_migrations(session):
    """Get list of executed migrations from app_settings"""
    try:
        result = session.execute(text(
            "SELECT key FROM app_settings WHERE key LIKE 'migration_%' AND is_active = TRUE"
        ))
        return [row[0].replace('migration_', '') for row in result]
    except Exception:
        return []


def run_migrations():
    """Run all necessary migrations"""
    print("\n" + "="*60)
    print("Running Vernika Database Migrations")
    print("="*60 + "\n")

    engine = get_engine()
    existing_tables = get_existing_tables()
    print(f"Existing tables: {len(existing_tables)}")

    session = get_db_session()
    try:
        executed = get_executed_migrations(session)
        print(f"Already executed migrations: {len(executed)}\n")

        success_count = 0
        skip_count = 0

        for migration in MIGRATIONS:
            name = migration["name"]

            if name in executed:
                print(f"  ⏭️  Skipping: {name} (already executed)")
                skip_count += 1
                continue

            # Check if table already exists
            # Extract table name from SQL
            table_name = None
            if "CREATE TABLE" in migration["sql"]:
                import re
                match = re.search(
                    r'CREATE TABLE.*?(\w+)\s*\(', migration["sql"], re.IGNORECASE)
                if match:
                    table_name = match.group(1)

            if table_name and table_name in existing_tables:
                print(
                    f"  ⏭️  Skipping: {name} (table '{table_name}' already exists)")
                skip_count += 1
                # Mark as executed anyway
                session.execute(text(
                    "INSERT INTO app_settings (key, value, description, category) "
                    "VALUES (:key, 'executed', :desc, 'migration') "
                    "ON CONFLICT (key) DO UPDATE SET value = 'executed'",
                    {"key": f"migration_{name}",
                        "desc": migration["description"]}
                ))
                session.commit()
                continue

            try:
                print(f"  ▶️  Running: {name}")
                print(f"      {migration['description']}")

                # Execute migration
                for stmt in migration["sql"].split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        session.execute(text(stmt))

                # Record migration as executed
                session.execute(text(
                    "INSERT INTO app_settings (key, value, description, category) "
                    "VALUES (:key, 'executed', :desc, 'migration') "
                    "ON CONFLICT (key) DO UPDATE SET value = 'executed'",
                    {"key": f"migration_{name}",
                        "desc": migration["description"]}
                ))

                session.commit()
                print(f"  ✅ Success: {name}")
                success_count += 1

            except Exception as e:
                session.rollback()
                print(f"  ❌ Failed: {name} - {str(e)[:100]}")

        print(f"\n{'='*60}")
        print(f"Migration Summary:")
        print(f"  ✅ Successful: {success_count}")
        print(f"  ⏭️  Skipped: {skip_count}")
        print(f"  📊 Total: {len(MIGRATIONS)}")
        print(f"{'='*60}\n")

    finally:
        session.close()


def check_status():
    """Check migration status"""
    print("\n" + "="*60)
    print("Migration Status")
    print("="*60 + "\n")

    engine = get_engine()
    existing_tables = get_existing_tables()

    session = get_db_session()
    try:
        executed = get_executed_migrations(session)

        print(f"Database Tables: {len(existing_tables)}")
        print(f"Executed Migrations: {len(executed)}")
        print(f"Pending Migrations: {len(MIGRATIONS) - len(executed)}")

        print("\n--- Migration Status ---")
        for migration in MIGRATIONS:
            status = "✅ Executed" if migration["name"] in executed else "⏳ Pending"
            print(f"  {status} - {migration['name']}")

        print("\n--- Missing Tables ---")
        for table in existing_tables:
            print(f"  📋 {table}")

    finally:
        session.close()


def reset_database():
    """Reset database - WARNING: This will delete all data!"""
    print("\n" + "⚠️"*20)
    print("WARNING: This will delete ALL data in the database!")
    print("⚠️"*20)

    response = input("\nType 'yes' to confirm: ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    print("\nResetting database...")

    engine = get_engine()

    # Drop all tables
    try:
        # Import all models to ensure they're registered
        import database.models

        from database.connection import Base
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
    except Exception as e:
        print(f"Error dropping tables: {e}")

    # Recreate tables
    try:
        import database.models
        from database.connection import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Tables recreated")
    except Exception as e:
        print(f"Error creating tables: {e}")

    # Run migrations
    run_migrations()

    print("\n✅ Database reset complete!")


def cleanup_old_migrations():
    """Clean up old SQL migration files"""
    print("\n" + "="*60)
    print("Cleaning up old SQL migration files")
    print("="*60 + "\n")

    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "supabase", "migrations"
    )

    if not os.path.exists(migrations_dir):
        print("No supabase/migrations directory found.")
        return

    # List old SQL files
    sql_files = [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]

    print(f"Found {len(sql_files)} SQL files:")
    for f in sql_files:
        print(f"  - {f}")

    # Create backup directory
    backup_dir = os.path.join(migrations_dir, "backup")
    os.makedirs(backup_dir, exist_ok=True)

    # Move files to backup
    import shutil
    for f in sql_files:
        src = os.path.join(migrations_dir, f)
        dst = os.path.join(backup_dir, f)
        shutil.move(src, dst)
        print(f"  Moved: {f} -> backup/")

    print(f"\n✅ Backed up {len(sql_files)} files to 'backup/' directory")
    print("   These migrations are now consolidated in manage_migrations.py")


def seed_default_data():
    """Seed default data after migrations"""
    print("\n" + "="*60)
    print("Seeding Default Data")
    print("="*60 + "\n")

    import bcrypt
    from database.models import Company, Role, User, LeaveTypeConfig, Department, Position

    session = get_db_session()
    try:
        # Create default company
        if not session.query(Company).first():
            company = Company(
                name="Vernika Technologies",
                email="hr@vernika.com",
                phone="+91-XXXX-XXXXXX",
                address="India"
            )
            session.add(company)
            print("✅ Created default company")

        # Create default roles
        if not session.query(Role).first():
            roles = [
                Role(name="admin", display_name="Administrator", level=100,
                     permissions={"manage_users": True, "manage_employees": True,
                                  "manage_departments": True, "view_reports": True}),
                Role(name="employee", display_name="Employee", level=10,
                     permissions={"view_profile": True, "apply_leave": True}),
            ]
            for role in roles:
                session.add(role)
            print("✅ Created default roles")

        # Create default admin user
        if not session.query(User).first():
            admin_role = session.query(Role).filter_by(name="admin").first()
            if admin_role:
                admin_user = User(
                    username="Vernika",
                    email="admin@vernika.com",
                    password_hash=bcrypt.hashpw(
                        "vernika8268".encode(), bcrypt.gensalt()).decode(),
                    role_id=admin_role.id
                )
                session.add(admin_user)
                print("✅ Created default admin user")

        # Create default leave types
        if not session.query(LeaveTypeConfig).first():
            leave_types = [
                LeaveTypeConfig(name="annual", display_name="Annual Leave",
                                max_days_per_year=20, is_paid=True, color="#4CAF50"),
                LeaveTypeConfig(name="sick", display_name="Sick Leave",
                                max_days_per_year=10, is_paid=True, color="#F44336"),
                LeaveTypeConfig(name="personal", display_name="Personal Leave",
                                max_days_per_year=5, is_paid=True, color="#2196F3"),
            ]
            for lt in leave_types:
                session.add(lt)
            print("✅ Created default leave types")

        # Create default departments
        if not session.query(Department).first():
            departments = [
                Department(name="Human Resources", code="HR"),
                Department(name="Information Technology", code="IT"),
                Department(name="Finance", code="FIN"),
                Department(name="Marketing", code="MKT"),
                Department(name="Operations", code="OPS"),
            ]
            for dept in departments:
                session.add(dept)
            session.flush()
            print("✅ Created default departments")

            # Create default positions
            if not session.query(Position).first():
                positions = [
                    Position(title="HR Manager", code="HRMGR",
                             department_id=departments[0].id),
                    Position(title="Software Developer", code="DEV",
                             department_id=departments[1].id),
                    Position(title="Accountant", code="ACC",
                             department_id=departments[2].id),
                    Position(title="Marketing Specialist",
                             code="MKTSP", department_id=departments[3].id),
                    Position(title="Operations Manager", code="OPSMGR",
                             department_id=departments[4].id),
                ]
                for pos in positions:
                    session.add(pos)
                print("✅ Created default positions")

        session.commit()
        print("\n✅ Default data seeded successfully!")
        print("   Login: Vernika / vernika8268")

    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Vernika Database Migration Manager")
    parser.add_argument("command", choices=["run", "status", "reset", "cleanup", "seed"],
                        help="Command to execute")

    args = parser.parse_args()

    if args.command == "run":
        run_migrations()
    elif args.command == "status":
        check_status()
    elif args.command == "reset":
        reset_database()
    elif args.command == "cleanup":
        cleanup_old_migrations()
    elif args.command == "seed":
        seed_default_data()


if __name__ == "__main__":
    main()
