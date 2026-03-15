#!/usr/bin/env python3
"""
Local config for scripts - loads project config
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Database URL from environment (Supabase/PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("WARNING: DATABASE_URL not found in environment")
    DATABASE_URL = None
