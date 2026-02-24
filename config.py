"""
Vernika - Configuration Module
Industry-Level Human Resource Management System

This module contains all configuration settings for the application.
Settings can be overridden using environment variables.
"""

import sys
import os
import secrets
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==================== APPLICATION INFO ====================
APP_NAME = "Vernika"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Industry-Level Human Resource Management System"

# ==================== DATABASE CONFIGURATION ====================

# Database type: postgresql ONLY (cloud database - no SQLite)
DATABASE_TYPE = "postgresql"

# PostgreSQL configuration (for cloud database - Supabase)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:!vrMVXZrv84wmKH@db.tbofjzzufxqbwfmfapxh.supabase.co:5432/postgres")
DB_HOST = os.getenv("DB_HOST", "db.tbofjzzufxqbwfmfapxh.supabase.co")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "!vrMVXZrv84wmKH")
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "require")
DB_SSL_CERT = os.getenv("DB_SSL_CERT", "None")

# Database pool settings - optimized for cloud PostgreSQL
# Increased for better concurrency with 200+ users
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "40"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))  # Connection timeout
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

# ==================== SECURITY CONFIGURATION ====================
SECRET_KEY = os.getenv(
    "SECRET_KEY", "vernika-hra-secret-key-change-in-production-2024")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password settings
HASH_ALGORITHM = "bcrypt"
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

# Session settings
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

# ==================== WINDOW CONFIGURATION ====================
WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1400"))
WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "900"))
WINDOW_MIN_WIDTH = int(os.getenv("WINDOW_MIN_WIDTH", "1024"))
WINDOW_MIN_HEIGHT = int(os.getenv("WINDOW_MIN_HEIGHT", "768"))
WINDOW_RESIZABLE = os.getenv("WINDOW_RESIZABLE", "true").lower() == "true"
WINDOW_MAXIMIZED = os.getenv("WINDOW_MAXIMIZED", "true").lower() == "true"

# ==================== THEME CONFIGURATION ====================
THEME_PRIMARY = "#2E86AB"  # Teal blue
THEME_SECONDARY = "#A23B72"  # Pink/magenta
THEME_TERTIARY = "#0B6E99"  # Darker teal
THEME_BACKGROUND = "#F8F9FA"
THEME_SURFACE = "#FFFFFF"
THEME_SURFACE_VARIANT = "#E8E8E8"
THEME_ON_PRIMARY = "#FFFFFF"
THEME_ON_SECONDARY = "#FFFFFF"
THEME_ON_BACKGROUND = "#212529"
THEME_ON_SURFACE = "#212529"
THEME_ON_SURFACE_VARIANT = "#6C757D"
THEME_SUCCESS = "#28A745"
THEME_WARNING = "#FFC107"
THEME_ERROR = "#DC3545"
THEME_INFO = "#17A2B8"
THEME_DARK_PRIMARY = "#5EADCC"
THEME_DARK_BACKGROUND = "#121212"
THEME_DARK_SURFACE = "#1E1E1E"
THEME_MODE = os.getenv("THEME_MODE", "light")

# ==================== COMPANY CONFIGURATION ====================
COMPANY_NAME = os.getenv("COMPANY_NAME", "Vernika Technologies")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "hr@vernika.com")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "")

# ==================== WORKING HOURS CONFIGURATION ====================
DEFAULT_WORKING_HOURS_START = os.getenv("WORKING_HOURS_START", "09:00")
DEFAULT_WORKING_HOURS_END = os.getenv("WORKING_HOURS_END", "18:00")
DEFAULT_LUNCH_BREAK_START = os.getenv("LUNCH_BREAK_START", "13:00")
DEFAULT_LUNCH_BREAK_END = os.getenv("LUNCH_BREAK_END", "14:00")
WORKING_DAYS = [0, 1, 2, 3, 4]  # Monday to Friday

# ==================== LEAVE POLICY CONFIGURATION ====================
DEFAULT_ANNUAL_LEAVE_DAYS = int(os.getenv("DEFAULT_ANNUAL_LEAVE", "20"))
DEFAULT_SICK_LEAVE_DAYS = int(os.getenv("DEFAULT_SICK_LEAVE", "10"))
DEFAULT_PERSONAL_LEAVE_DAYS = int(os.getenv("DEFAULT_PERSONAL_LEAVE", "5"))
LEAVE_APPROVAL_REQUIRED = os.getenv(
    "LEAVE_APPROVAL_REQUIRED", "true").lower() == "true"
MAX_CONSECUTIVE_LEAVE_DAYS = int(os.getenv("MAX_CONSECUTIVE_LEAVE", "10"))

# ==================== FILE UPLOAD CONFIGURATION ====================
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".doc",
                               ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]
PROFILE_PIC_MAX_SIZE_MB = int(os.getenv("PROFILE_PIC_MAX_SIZE", "2"))
PROFILE_PIC_DIMENSIONS = (300, 300)

# ==================== REPORT CONFIGURATION ====================
REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "reports")
DEFAULT_REPORT_FORMAT = os.getenv(
    "DEFAULT_REPORT_FORMAT", "pdf")

# ==================== LOGGING CONFIGURATION ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.getenv("LOG_FILE", "vernika.log")
LOG_FILE_MAX_SIZE_MB = int(os.getenv("LOG_FILE_MAX_SIZE", "10"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# ==================== LOCALIZATION ====================
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
DATE_FORMAT = os.getenv("DATE_FORMAT", "%Y-%m-%d")
TIME_FORMAT = os.getenv("TIME_FORMAT", "%H:%M")
DATETIME_FORMAT = os.getenv("DATETIME_FORMAT", "%Y-%m-%d %H:%M")

# ==================== API CONFIGURATION ====================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
API_PREFIX = "/api/v1"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv(
    "CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

# ==================== FEATURE FLAGS ====================
FEATURE_MULTI_BRANCH = os.getenv(
    "FEATURE_MULTI_BRANCH", "false").lower() == "true"
FEATURE_OVERTIME_TRACKING = os.getenv(
    "FEATURE_OVERTIME_TRACKING", "true").lower() == "true"
FEATURE_PERFORMANCE_REVIEWS = os.getenv(
    "FEATURE_PERFORMANCE_REVIEWS", "true").lower() == "true"
FEATURE_DOCUMENT_MANAGEMENT = os.getenv(
    "FEATURE_DOCUMENT_MANAGEMENT", "true").lower() == "true"
FEATURE_ANNOUNCEMENTS = os.getenv(
    "FEATURE_ANNOUNCEMENTS", "true").lower() == "true"
FEATURE_ATTENDANCE_GPS = os.getenv(
    "FEATURE_ATTENDANCE_GPS", "false").lower() == "true"

# ==================== DEFAULT USER ACCOUNTS ====================


def _generate_secure_password():
    """Generate a secure random password if not set in environment"""
    return secrets.token_urlsafe(16)


DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@vernika.com")
DEFAULT_ADMIN_PASSWORD = os.getenv(
    "DEFAULT_ADMIN_PASSWORD", _generate_secure_password())

DEFAULT_HR_USERNAME = os.getenv("DEFAULT_HR_USERNAME", "hr")
DEFAULT_HR_EMAIL = os.getenv("DEFAULT_HR_EMAIL", "hr@vernika.com")
DEFAULT_HR_PASSWORD = os.getenv(
    "DEFAULT_HR_PASSWORD", _generate_secure_password())

# ==================== ASSETS PATH ====================
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_DIR = ASSETS_DIR / "logo"
PROFILE_PHOTOS_DIR = ASSETS_DIR / "profile_photos"
DOCUMENTS_DIR = ASSETS_DIR / "documents"

for directory in [ASSETS_DIR, LOGO_DIR, PROFILE_PHOTOS_DIR, DOCUMENTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== SUPABASE CONFIGURATION ====================
SUPABASE_URL = os.getenv(
    "SUPABASE_URL", "https://tbofjzzufxqbwfmfapxh.supabase.co")
SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRib2Zqenp1ZnhxYndmbWZhcHhoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTk1MDAwNCwiZXhwIjoyMDg3NTI2MDA0fQ.l_OP2BCTYN8W-M3c3SJRxg_pNgu8Kmpp0tLBIVAo7JM")
SUPABASE_REALTIME_URL = f"{SUPABASE_URL}/realtime/v1"

# Supabase Storage Configuration
SUPABASE_STORAGE_URL = f"{SUPABASE_URL}/storage/v1"
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "vernika-files")

# ==================== HELPERS ====================


def get_database_url() -> str:
    """Get the database URL - always PostgreSQL"""
    return DATABASE_URL


def is_development() -> bool:
    """Check if running in development mode"""
    return os.getenv("ENVIRONMENT", "development").lower() == "development"


def is_production() -> bool:
    """Check if running in production mode"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


# ==================== VERSION INFO ====================
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "string": APP_VERSION,
    "full": f"{APP_NAME} v{APP_VERSION}"
}
