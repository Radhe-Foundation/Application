#!/usr/bin/env python3
"""
RadheFoundation - Fix Storage Upload Issue
Updates RLS policies to allow file uploads with anon key
"""

from dotenv import load_dotenv
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BUCKET_NAME = os.getenv("SUPABASE_STORAGE_BUCKET", "RadheFoundation-files")


def fix_storage_policies():
    """Fix RLS policies to allow public uploads"""
    print("="*60)
    print("Fixing Storage RLS Policies")
    print("="*60)

    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        print("\nPlease ensure your .env file has DATABASE_URL set")
        return False

    try:
        import psycopg2
    except ImportError:
        print("Installing psycopg2...")
        os.system(f"{sys.executable} -m pip install psycopg2-binary")
        import psycopg2

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()

        print(f"\nUpdating RLS policies for bucket '{BUCKET_NAME}'...")

        # Policy 1: Allow public inserts (uploads)
        policy1 = f"""
        DROP POLICY IF EXISTS "Allow public uploads" ON storage.objects;
        CREATE POLICY "Allow public uploads" ON storage.objects
        FOR INSERT WITH CHECK (bucket_id = '{BUCKET_NAME}');
        """
        cursor.execute(policy1)
        print("   ✅ Insert policy created")

        # Policy 2: Allow public selects (reads)
        policy2 = f"""
        DROP POLICY IF EXISTS "Allow public read" ON storage.objects;
        CREATE POLICY "Allow public read" ON storage.objects
        FOR SELECT USING (bucket_id = '{BUCKET_NAME}');
        """
        cursor.execute(policy2)
        print("   ✅ Select policy created")

        # Policy 3: Allow public updates
        policy3 = f"""
        DROP POLICY IF EXISTS "Allow public updates" ON storage.objects;
        CREATE POLICY "Allow public updates" ON storage.objects
        FOR UPDATE USING (bucket_id = '{BUCKET_NAME}');
        """
        cursor.execute(policy3)
        print("   ✅ Update policy created")

        # Policy 4: Allow public deletes
        policy4 = f"""
        DROP POLICY IF EXISTS "Allow public deletes" ON storage.objects;
        CREATE POLICY "Allow public deletes" ON storage.objects
        FOR DELETE USING (bucket_id = '{BUCKET_NAME}');
        """
        cursor.execute(policy4)
        print("   ✅ Delete policy created")

        # Make bucket public
        bucket_update = f"""
        UPDATE storage.buckets SET public = true WHERE id = '{BUCKET_NAME}';
        """
        cursor.execute(bucket_update)
        print("   ✅ Bucket set to public")

        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print("✅ All RLS policies updated successfully!")
        print("="*60)
        print("\nYou can now upload files in RadheFoundation!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = fix_storage_policies()
    sys.exit(0 if success else 1)
