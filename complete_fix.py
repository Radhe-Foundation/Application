#!/usr/bin/env python3
"""Complete Vernika Fix - Run this first"""

import sqlite3
import bcrypt
from datetime import datetime

conn = sqlite3.connect('vernika.db')
cursor = conn.cursor()

print("=== Vernika Complete Fix ===\n")

# Fix rajat and tanu passwords
users_to_fix = [
    {'username': 'rajat', 'email': 'rajatsinghtomar15@gmail.com',
        'password': 'rajat123', 'role_id': 1},
    {'username': 'tanu', 'email': 'tanusinghchauhan1999@gmail.com',
        'password': 'tanu123', 'role_id': 2},
]

for user in users_to_fix:
    cursor.execute("SELECT id FROM users WHERE username = ?",
                   (user['username'],))
    if cursor.fetchone():
        hashed = bcrypt.hashpw(
            user['password'].encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "UPDATE users SET password_hash = ?, status = 'active' WHERE username = ?", (hashed, user['username']))
        print(f"Fixed: {user['username']} / {user['password']}")
    else:
        hashed = bcrypt.hashpw(
            user['password'].encode(), bcrypt.gensalt()).decode()
        cursor.execute("INSERT INTO users (username, email, password_hash, role_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (user['username'], user['email'], hashed, user['role_id'], 'active', datetime.now().isoformat()))
        print(f"Created: {user['username']} / {user['password']}")

# Remove test users
test_users = ['john_doe', 'jane_smith', 'mike_wilson', 'manager']
for u in test_users:
    cursor.execute("DELETE FROM users WHERE username = ?", (u,))

conn.commit()

# Ensure chat_groups table exists
cursor.execute('''CREATE TABLE IF NOT EXISTS chat_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS chat_group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT DEFAULT 'member',
    joined_at TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    group_id INTEGER,
    receiver_id INTEGER,
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    is_read INTEGER DEFAULT 0,
    created_at TEXT
)''')

# Add default groups if not exist
cursor.execute("SELECT COUNT(*) FROM chat_groups")
if cursor.fetchone()[0] == 0:
    groups = [
        ('General', 'Company wide discussions', 1),
        ('HR Updates', 'HR announcements', 1),
        ('IT Team', 'IT department channel', 1),
    ]
    for name, desc, created_by in groups:
        cursor.execute("INSERT INTO chat_groups (name, description, created_by, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
                       (name, desc, created_by, 1, datetime.now().isoformat()))
    print("Added default chat groups")

conn.commit()
conn.close()

print("\n=== Fix Complete! ===")
print("Login with: rajat / rajat123 or tanu / tanu123")
