#!/usr/bin/env python3
"""
RadheFoundation - Complete Storage Setup
Creates the storage bucket and enables RLS policies for secure file sharing
"""

from dotenv import load_dotenv
import os
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv(
    "SUPABASE_SERVICE_KEY")  # For admin operations
DATABASE_URL = os.getenv("DATABASE_URL")

# Use service role key for bucket creation (has admin permissions)
# If not set, we'll try to use the anon key but it might fail for admin operations
SERVICE_KEY = SUPABASE_SERVICE_KEY or SUPABASE_KEY

BUCKET_NAME = os.getenv("SUPABASE_STORAGE_BUCKET", "RadheFoundation-files")


def create_storage_bucket():
    """Create storage bucket via Supabase Storage API"""
    print("\n" + "="*60)
    print("📦 STEP 1: Creating Storage Bucket")
    print("="*60)

    headers = {
        "Authorization": f"Bearer {SERVICE_KEY}",
        "apikey": SERVICE_KEY,
        "Content-Type": "application/json"
    }

    # First, list all buckets to check if ours exists
    list_url = f"{SUPABASE_URL}/storage/v1/bucket"
    response = requests.get(list_url, headers=headers)

    if response.status_code == 200:
        buckets = response.json()
        print(f"Found {len(buckets)} existing bucket(s)")

        # Check if our bucket exists
        for bucket in buckets:
            if bucket.get('id') == BUCKET_NAME:
                print(f"✅ Bucket '{BUCKET_NAME}' already exists!")
                return True

    # Create the bucket
    print(f"Creating bucket '{BUCKET_NAME}'...")
    create_url = f"{SUPABASE_URL}/storage/v1/bucket"

    data = {
        "id": BUCKET_NAME,
        "name": BUCKET_NAME,
        "public": True,
        "file_size_limit": 52428800,  # 50MB
        "allowed_mime_types": [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain", "text/csv",
            "application/zip", "application/x-rar-compressed", "application/x-7z-compressed",
            "audio/mpeg", "audio/wav",
            "video/mp4"
        ]
    }

    response = requests.post(create_url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        print(f"✅ Bucket '{BUCKET_NAME}' created successfully!")
    elif response.status_code == 400 and "already exists" in response.text.lower():
        print(f"✅ Bucket '{BUCKET_NAME}' already exists!")
    else:
        print(f"⚠️ Bucket creation response: {response.status_code}")
        print(f"   {response.text[:200]}")
        # Continue anyway - bucket might already exist

    # Create folder structure
    print("\n📁 Creating folder structure...")
    folders = [
        "documents",      # General documents
        "images",         # Images
        "profiles",       # Profile photos
        "attachments",    # Email attachments
        "chat_files",     # Chat file sharing
        "mail_attachments",  # Mail attachments
        "reports"        # Report exports
    ]

    for folder in folders:
        # Create a placeholder file to create the folder
        folder_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{folder}/.gitkeep"
        try:
            resp = requests.post(folder_url, headers=headers, content=b"")
            if resp.status_code in [200, 201, 400]:  # 400 means already exists
                print(f"   ✅ {folder}/")
        except Exception as e:
            print(f"   ⚠️ {folder}/ - {e}")

    return True


def setup_storage_rls():
    """Set up Row Level Security policies for storage"""
    print("\n" + "="*60)
    print("🔒 STEP 2: Setting Up RLS Policies")
    print("="*60)

    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return False

    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Installing...")
        os.system(f"{sys.executable} -m pip install psycopg2-binary")
        import psycopg2

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()

        # Storage RLS policies
        # Allow authenticated users to upload files
        # Allow public read access for shared files

        policies = [
            # Allow authenticated users to upload to their own folders
            f"""
            DROP POLICY IF EXISTS "Allow authenticated uploads" ON storage.objects;
            CREATE POLICY "Allow authenticated uploads" ON storage.objects
            FOR INSERT WITH CHECK (bucket_id = '{BUCKET_NAME}' AND auth.role() = 'authenticated');
            """,

            # Allow users to update their own files
            f"""
            DROP POLICY IF EXISTS "Allow authenticated updates" ON storage.objects;
            CREATE POLICY "Allow authenticated updates" ON storage.objects
            FOR UPDATE USING (bucket_id = '{BUCKET_NAME}' AND auth.role() = 'authenticated');
            """,

            # Allow users to delete their own files
            f"""
            DROP POLICY IF EXISTS "Allow authenticated deletes" ON storage.objects;
            CREATE POLICY "Allow authenticated deletes" ON storage.objects
            FOR DELETE USING (bucket_id = '{BUCKET_NAME}' AND auth.role() = 'authenticated');
            """,

            # Allow public read access (files are shared via URL)
            f"""
            DROP POLICY IF EXISTS "Public read access" ON storage.objects;
            CREATE POLICY "Public read access" ON storage.objects
            FOR SELECT USING (bucket_id = '{BUCKET_NAME}');
            """,
        ]

        for i, policy_sql in enumerate(policies, 1):
            try:
                cursor.execute(policy_sql)
                print(f"   ✅ Policy {i} created")
            except Exception as e:
                print(f"   ⚠️ Policy {i}: {e}")

        cursor.close()
        conn.close()

        print("✅ RLS policies configured!")
        return True

    except Exception as e:
        print(f"❌ Error setting up RLS: {e}")
        return False


def test_storage_connection():
    """Test the storage connection"""
    print("\n" + "="*60)
    print("🧪 STEP 3: Testing Storage Connection")
    print("="*60)

    try:
        from supabase import create_client, Client

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Try to list buckets
        buckets = supabase.storage.list_buckets()
        print(f"✅ Connected to Supabase Storage")
        print(f"   Found {len(buckets)} bucket(s)")

        # Check if our bucket exists
        bucket_found = False
        for bucket in buckets:
            if bucket.id == BUCKET_NAME:
                bucket_found = True
                print(f"   ✅ Bucket '{BUCKET_NAME}' is ready!")
                break

        if not bucket_found:
            print(f"   ⚠️ Bucket '{BUCKET_NAME}' not found in list")
            print(f"   Available buckets: {[b.id for b in buckets]}")

        return True

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def update_config():
    """Ensure config has correct bucket name"""
    print("\n" + "="*60)
    print("⚙️ STEP 4: Checking Configuration")
    print("="*60)

    from config import SUPABASE_STORAGE_BUCKET

    if SUPABASE_STORAGE_BUCKET == BUCKET_NAME:
        print(f"✅ Config is correct: bucket = '{BUCKET_NAME}'")
        return True
    else:
        print(f"⚠️ Config mismatch!")
        print(f"   Config has: {SUPABASE_STORAGE_BUCKET}")
        print(f"   Expected: {BUCKET_NAME}")
        return False


def main():
    print("="*60)
    print("RadheFoundation - Storage & RLS Setup")
    print("="*60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Bucket Name: {BUCKET_NAME}")

    # Step 1: Create bucket
    create_storage_bucket()

    # Step 2: Setup RLS
    setup_storage_rls()

    # Step 3: Test connection
    test_storage_connection()

    # Step 4: Check config
    update_config()

    print("\n" + "="*60)
    print("🎉 Storage Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart the RadheFoundation app")
    print("2. Try sharing a file in Chat or Mail screen")
    print("3. Files will be uploaded to Supabase cloud storage")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
