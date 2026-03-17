#!/usr/bin/env python3
"""Quick data parity check"""

import sqlite3
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

results = []
results.append('Table Row Count Comparison')
results.append('=' * 60)
results.append(f'{"Table":<25} {"SQLite":>10} {"Supabase":>10} {"Diff":>10}')
results.append('-' * 60)

# Supabase table names (from our earlier query)
supabase_tables = [
    'announcements', 'attendances', 'audit_logs', 'call_logs',
    'chat_group_members', 'chat_groups', 'chat_messages', 'companies',
    'data_import_logs', 'departments', 'documents', 'email_messages',
    'email_recipients', 'employees', 'etl_jobs', 'excel_templates',
    'leave_balances', 'leave_requests', 'leave_type_configs',
    'meeting_participants', 'meetings', 'messages', 'positions',
    'powerbi_refresh_logs', 'projects', 'roles', 'screen_access',
    'task_comments', 'tasks', 'teams', 'time_off_requests',
    'user_permissions', 'users'
]

# SQLite table name mapping (SQLite uses singular, Supabase uses plural)
name_mapping = {
    'attendance': 'attendances',
    'chat_group_member': 'chat_group_members',
    'chat_message': 'chat_messages',
    'data_import_log': 'data_import_logs',
    'email_message': 'email_messages',
    'email_recipient': 'email_recipients',
    'etl_job': 'etl_jobs',
    'excel_template': 'excel_templates',
    'leave_balance': 'leave_balances',
    'leave_request': 'leave_requests',
    'leave_type_config': 'leave_type_configs',
    'meeting_participant': 'meeting_participants',
    'powerbi_refresh_log': 'powerbi_refresh_logs',
    'task_comment': 'task_comments',
    'time_off_request': 'time_off_requests',
    'user_permission': 'user_permissions'
}

# Connect to SQLite
sqlite_conn = sqlite3.connect('RadheFoundation.db')
sqlite_cursor = sqlite_conn.cursor()

# Get SQLite tables
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
sqlite_tables = {row[0] for row in sqlite_cursor.fetchall()}

# Connect to Supabase
pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
pg_conn.autocommit = True  # Avoid transaction issues
pg_cursor = pg_conn.cursor()

mismatch_tables = []

for table in supabase_tables:
    try:
        # Get SQLite count
        sqlite_name = table
        # Check if we need to use singular form
        if table not in sqlite_tables:
            singular = table.rstrip('s')
            if singular in sqlite_tables:
                sqlite_name = singular
        
        sqlite_cursor.execute(f'SELECT COUNT(*) FROM {sqlite_name}')
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        pg_cursor.execute(f'SELECT COUNT(*) FROM {table}')
        supabase_count = pg_cursor.fetchone()[0]
        
        diff = supabase_count - sqlite_count
        results.append(f'{table:<25} {sqlite_count:>10} {supabase_count:>10} {diff:>10}')
        
        if diff != 0:
            mismatch_tables.append((table, sqlite_count, supabase_count))
    except Exception as e:
        results.append(f'{table:<25} ERROR: {str(e)[:40]}')

sqlite_conn.close()
pg_conn.close()

results.append('')
results.append('=' * 60)
results.append(f'Tables needing attention: {len(mismatch_tables)}')
for t, s, p in mismatch_tables:
    results.append(f'  - {t}: {s} (SQLite) vs {p} (Supabase)')

# Write to file
with open('parity_results.txt', 'w') as f:
    f.write('\n'.join(results))

print('Done - results written to parity_results.txt')
print('\n'.join(results))
