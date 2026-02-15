#!/usr/bin/env python3
"""
Add announcements table using SQLAlchemy engine
"""

from datetime import datetime
from sqlalchemy import text
from database.connection import get_engine, get_db_session


def add_announcements_table():
    engine = get_engine()
    inspector = __import__('sqlalchemy').inspect(engine)
    if 'announcements' in inspector.get_table_names():
        print('Announcements table already exists')
        return

    create_sql = '''
        CREATE TABLE announcements (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            type VARCHAR(50) DEFAULT 'general',
            priority VARCHAR(50) DEFAULT 'normal',
            author VARCHAR(255) DEFAULT 'Admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            views INTEGER DEFAULT 0
        )
    '''

    # For sqlite dialect, adjust create SQL
    if engine.dialect.name == 'sqlite':
        create_sql = '''
        CREATE TABLE announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'general',
            priority TEXT DEFAULT 'normal',
            author TEXT DEFAULT 'Admin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            views INTEGER DEFAULT 0
        )
        '''

    with engine.begin() as conn:
        conn.execute(text(create_sql))

        # Insert sample announcements (optional)
        sample_announcements = [
            ('Office Closure - Holiday Notice',
             'The office will be closed on Friday for a company-wide holiday.', 'important', 'high', 'Admin'),
            ('New Health Insurance Plan', 'We are pleased to announce an improved health insurance plan.',
             'policy', 'important', 'HR Manager'),
            ('Welcome to New Team Members', "Let's welcome our new team members joining this month!",
             'general', 'normal', 'HR Manager'),
        ]

        for title, content, type_, priority, author in sample_announcements:
            conn.execute(text("""
                INSERT INTO announcements (title, content, type, priority, author, created_at, views)
                VALUES (:title, :content, :type, :priority, :author, :created_at, 0)
            """), {"title": title, "content": content, "type": type_, "priority": priority, "author": author, "created_at": datetime.now()})

    print('Announcements table created/seeded')


if __name__ == "__main__":
    add_announcements_table()
