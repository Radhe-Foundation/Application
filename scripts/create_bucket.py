"""
RadheFoundation - Create Storage Bucket via Supabase API
"""
import requests

# Supabase credentials
SUPABASE_URL = "https://tbofjzzufxqbwfmfapxh.supabase.co"
# Service role key (has admin permissions) - from supabase CLI
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRib2Zqenp1ZnhxYndmbWZhcHhoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTk1MDAwNCwiZXhwIjoyMDg3NTI2MDA0fQ.l_OP2BCTYN8W-M3c3SJRxg_pNgu8Kmpp0tLBIVAo7JM"


def create_bucket():
    """Create storage bucket via Supabase API"""
    print("=" * 60)
    print("RadheFoundation - Storage Bucket Setup")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }

    # First, list all buckets
    list_url = f"{SUPABASE_URL}/storage/v1/bucket"
    response = requests.get(list_url, headers=headers)
    print(f"Debug: List buckets: {response.status_code}")

    if response.status_code == 200:
        buckets = response.json()
        print(f"Existing buckets: {buckets}")

        # Check if RadheFoundation-files exists
        for bucket in buckets:
            if bucket.get('id') == 'RadheFoundation-files':
                print("✅ Bucket 'RadheFoundation-files' already exists!")
                return True

    # Create bucket
    print("📦 Creating bucket 'RadheFoundation-files'...")
    create_url = f"{SUPABASE_URL}/storage/v1/bucket"

    data = {
        "id": "RadheFoundation-files",
        "name": "RadheFoundation-files",
        "public": True
    }

    response = requests.post(create_url, headers=headers, json=data)
    print(
        f"Debug: POST bucket response: {response.status_code} - {response.text}")

    if response.status_code in [200, 201]:
        print("✅ Bucket created successfully!")

        # Create folders
        folders = ["documents", "images", "profiles", "attachments", "reports"]
        for folder in folders:
            folder_url = f"{SUPABASE_URL}/storage/v1/object/RadheFoundation-files/{folder}/.gitkeep"
            requests.post(folder_url, headers=headers)

        print(f"✅ Created folders: {', '.join(folders)}")
        return True
    else:
        print(f"❌ Failed to create bucket: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


if __name__ == "__main__":
    success = create_bucket()
    print("=" * 60)
