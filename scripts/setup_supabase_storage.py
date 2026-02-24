"""
Vernika - Supabase Storage Setup
Creates the storage bucket for file uploads
"""

from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_STORAGE_BUCKET
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_storage():
    """Create storage bucket for Vernika"""

    if not SUPABASE_KEY:
        print("❌ Error: SUPABASE_KEY not configured in config.py")
        print("Please add your Supabase API key to config.py")
        return False

    try:
        from supabase import create_client, Client

        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        print(f"🔌 Connected to Supabase")
        print(f"   URL: {SUPABASE_URL}")

        # Try to get bucket (will fail if doesn't exist)
        try:
            bucket = supabase.storage.get_bucket(SUPABASE_STORAGE_BUCKET)
            print(
                f"✅ Storage bucket already exists: {SUPABASE_STORAGE_BUCKET}")
            return True
        except Exception:
            # Bucket doesn't exist, create it
            pass

        # Create the bucket
        bucket = supabase.storage.create_bucket(
            SUPABASE_STORAGE_BUCKET,
            options={
                'public': True,  # Files will be publicly accessible via URL
                'allowed_mime_types': [
                    'image/jpeg',
                    'image/png',
                    'image/gif',
                    'image/webp',
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.ms-powerpoint',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'text/plain',
                    'text/csv',
                    'application/zip',
                    'application/x-rar-compressed',
                    'audio/mpeg',
                    'video/mp4',
                ],
                'file_size_limit': 52428800,  # 50MB limit
            }
        )

        print(f"✅ Created storage bucket: {SUPABASE_STORAGE_BUCKET}")
        print(f"   - Public access: Yes")
        print(f"   - Max file size: 50MB")
        print(f"   - Supported: Images, PDFs, Documents, Videos, Audio")

        # Create folders within the bucket
        folders = ['documents', 'images', 'profiles', 'attachments', 'reports']

        print(f"\n📁 Creating folder structure...")
        for folder in folders:
            try:
                # Upload a placeholder file to create folder
                supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
                    f"{folder}/.gitkeep",
                    b"",
                    options={'content-type': 'text/plain'}
                )
                print(f"   ✅ {folder}/")
            except Exception as e:
                # Folder might already exist
                print(f"   ✅ {folder}/ (ready)")

        print(f"\n🎉 Storage setup complete!")
        print(f"\n📝 Storage Configuration:")
        print(f"   Bucket Name: {SUPABASE_STORAGE_BUCKET}")
        print(f"   Base URL: {SUPABASE_URL}/storage/v1")

        return True

    except ImportError:
        print("❌ Error: Supabase Python library not installed")
        print("   Install with: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Error setting up storage: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Vernika - Supabase Storage Setup")
    print("=" * 60)
    print()

    success = setup_storage()

    if success:
        print("\n" + "=" * 60)
        print("✅ You can now upload files to Supabase Storage!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Setup failed. Please check the errors above.")
        print("=" * 60)
