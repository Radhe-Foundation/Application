"""
RadheFoundation - Supabase Environment Setup Script
Run this script to generate .env file with Supabase connection
"""

# Supabase Configuration
SUPABASE_PROJECT = "tbofjzzufxqbwfmfapxh"
SUPABASE_URL = f"https://{SUPABASE_PROJECT}.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRib2Zqenp1ZnhxYndmbWZhcHhoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5NTAwMDQsImV4cCI6MjA4NzUyNjAwNH0.lzMhQNeNYhXK42id-AH0A4tGxcnbeSPNra6ObOLW-lk"
DB_PASSWORD = "!vrMVXZrv84wmKH"

# Connection String Options
CONNECTION_STRINGS = {
    "transaction": f"postgresql://postgres.{SUPABASE_PROJECT}:{DB_PASSWORD}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres",
    "session": f"postgresql://postgres.{SUPABASE_PROJECT}:{DB_PASSWORD}@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
    "direct": f"postgresql://postgres:{DB_PASSWORD}@db.{SUPABASE_PROJECT}.supabase.co:5432/postgres"
}

# Generate .env file content
ENV_CONTENT = f"""# RadheFoundation - Environment Configuration
# Generated for Supabase + Vercel Deployment

# ==================== DATABASE CONFIGURATION ====================
# Using Transaction Pooler (recommended for Vercel/serverless)
DATABASE_URL={CONNECTION_STRINGS["transaction"]}

# Individual DB components (optional if using DATABASE_URL)
DB_HOST=aws-0-ap-southeast-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.{SUPABASE_PROJECT}
DB_PASSWORD={DB_PASSWORD}
DB_SSL_MODE=require

# Database Pool Settings (optimized for Vercel/serverless)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800
DB_POOL_TIMEOUT=30
DB_ECHO=false

# ==================== SUPABASE CONFIGURATION ====================
SUPABASE_URL={SUPABASE_URL}
SUPABASE_KEY={SUPABASE_KEY}
SUPABASE_STORAGE_BUCKET=RadheFoundation-files

# ==================== SECURITY ====================
SECRET_KEY=RadheFoundation-hra-secret-key-change-in-production-2024-always-change
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
SESSION_TIMEOUT_MINUTES=30

# ==================== APPLICATION ====================
ENVIRONMENT=production
APP_NAME=RadheFoundation
APP_VERSION=1.0.0

# ==================== COMPANY ====================
COMPANY_NAME=RadheFoundation Technologies
COMPANY_EMAIL=hr@RadheFoundation.com

# ==================== THEME ====================
THEME_MODE=light
"""

# Vercel Environment Variables (for dashboard)
VERCEL_ENV = f"""
DATABASE_URL={CONNECTION_STRINGS["transaction"]}
SUPABASE_URL={SUPABASE_URL}
SUPABASE_KEY={SUPABASE_KEY}
SUPABASE_STORAGE_BUCKET=RadheFoundation-files
SECRET_KEY=RadheFoundation-hra-secret-key-change-in-production-2024-always-change
ENVIRONMENT=production
"""

if __name__ == "__main__":
    import os

    # Write .env file
    env_file_path = os.path.join(os.path.dirname(__file__), "..", ".env")

    print("=" * 60)
    print("RadheFoundation - Supabase + Vercel Setup")
    print("=" * 60)
    print("\n📋 Connection Strings:")
    print("\n🔷 Transaction Pooler (Recommended for Vercel):")
    print(CONNECTION_STRINGS["transaction"])
    print("\n🔷 Session Pooler:")
    print(CONNECTION_STRINGS["session"])
    print("\n🔷 Direct Connection:")
    print(CONNECTION_STRINGS["direct"])

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n📝 Next Steps:")
    print("1. Copy the .env content to your project's .env file")
    print("2. Add the same variables to Vercel Dashboard")
    print("3. Run: python main.py")
    print("\n📖 See VERCEL_SETUP.md for detailed instructions")
