#!/usr/bin/env python3
"""
Script to add announcements table to the database
"""

import sqlite3
from datetime import datetime


def add_announcements_table():
    """Add announcements table to the database"""
    conn = sqlite3.connect('vernika.db')
    cursor = conn.cursor()

    # Check if announcements table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='announcements'")
    if cursor.fetchone():
        print('Announcements table already exists')
    else:
        # Create announcements table
        cursor.execute('''
            CREATE TABLE announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT DEFAULT "general",
                priority TEXT DEFAULT "normal",
                author TEXT DEFAULT "Admin",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0
            )
        ''')
        print('Created announcements table')

        # Insert sample announcements
        sample_announcements = [
            ('Office Closure - Holiday Notice',
             'The office will be closed on Friday for a company-wide holiday.',
             'important', 'high', 'Admin'),
            ('New Health Insurance Plan',
             'We are pleased to announce an improved health insurance plan.',
             'policy', 'important', 'HR Manager'),
            ('Welcome to New Team Members',
             "Let's welcome our new team members joining this month!",
             'general', 'normal', 'HR Manager'),
        ]

        for title, content, type_, priority, author in sample_announcements:
            cursor.execute('''
                INSERT INTO announcements (title, content, type, priority, author, created_at, views)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            ''', (title, content, type_, priority, author, datetime.now().strftime('%Y-%m-%d')))

        print('Added sample announcements')

    conn.commit()
    conn.close()
    print('Done!')


if __name__ == "__main__":
    add_announcements_table()
