#!/usr/bin/env python3
# Final CRM Tables - Create ALL missing tables/columns for Contracts/Invoices/etc

from sqlalchemy import text
from database.connection import get_engine
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('🏗️ Creating COMPLETE CRM Tables...')

engine = get_engine()

with engine.begin() as conn:
    # Invoices table + columns
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            invoice_number VARCHAR(50) UNIQUE NOT NULL,
            customer_name VARCHAR(200),
            customer_email VARCHAR(100),
            customer_address TEXT,
            invoice_date DATE NOT NULL,
            due_date DATE,
            subtotal FLOAT DEFAULT 0,
            tax_amount FLOAT DEFAULT 0,
            total_amount FLOAT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'draft',
            notes TEXT,
            contract_id INTEGER REFERENCES contracts(id),
            created_by_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    print('✅ invoices table + columns')

    # Contracts table + columns
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS contracts (
            id SERIAL PRIMARY KEY,
            contract_number VARCHAR(50) UNIQUE NOT NULL,
            title VARCHAR(200) NOT NULL,
            contract_type VARCHAR(50),
            vendor_id INTEGER REFERENCES suppliers(id),
            client_name VARCHAR(200),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            value FLOAT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'draft',
            description TEXT,
            terms TEXT,
            created_by_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    print('✅ contracts table + columns')

    # Calendar events (for Calendar tab)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            event_type VARCHAR(50) DEFAULT 'meeting',
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            location VARCHAR(200),
            organizer_id INTEGER REFERENCES users(id),
            attendees TEXT,
            is_all_day BOOLEAN DEFAULT false,
            reminder_minutes INTEGER DEFAULT 15,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    print('✅ calendar_events table')

print('🎉 ALL CRM TABLES CREATED!')
print('Restart: python3 main.py')
