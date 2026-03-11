"""
Vernika - Supabase Storage Utility
Handles file uploads to Supabase Storage for documents, images, and other files
Updated to use REST API directly for more reliable uploads
"""

import os
import uuid
import logging
from typing import Optional, Tuple
from datetime import datetime

# Check for requests - required for Supabase Storage
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None
    print("WARNING: 'requests' module not installed. File uploads to Supabase will not work.")

from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_STORAGE_URL, SUPABASE_STORAGE_BUCKET, SUPABASE_SERVICE_KEY

logger = logging.getLogger(__name__)

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase not installed - file storage will use local fallback")


class SupabaseStorage:
    """Supabase Storage client for file uploads using REST API"""

    _instance: Optional['SupabaseStorage'] = None
    _client: Optional[Client] = None
    _last_error: Optional[str] = None  # Store last error for debugging

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.available = False
        self.bucket_name = SUPABASE_STORAGE_BUCKET
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        # Use service key if available for better permissions
        self.service_key = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_KEY
        self._last_error = None

        if not SUPABASE_URL or not SUPABASE_KEY:
            self._last_error = "Supabase URL or Key not configured"
            print(f"[Storage] ERROR: {self._last_error}")
            print("[Storage] Please set SUPABASE_URL and SUPABASE_KEY in .env file")
            return

        if not REQUESTS_AVAILABLE or requests is None:
            self._last_error = "requests module not installed"
            print(f"[Storage] ERROR: {self._last_error}")
            print("[Storage] Install with: pip install requests")
            return

        # Initialize storage - be more permissive for uploads to work
        self._initialize_storage()

    def _initialize_storage(self):
        """Initialize storage connection with more permissive settings"""
        try:
            # Use service key for bucket checks (has better permissions)
            headers = {
                'Authorization': f'Bearer {self.service_key}',
                'apikey': self.service_key
            }

            # Try to list buckets to verify connection - more reliable than checking specific bucket
            test_url = f"{SUPABASE_URL}/storage/v1/bucket"
            response = requests.get(test_url, headers=headers, timeout=10)

            if response.status_code == 200:
                buckets = response.json()
                bucket_exists = any(
                    b.get('id') == self.bucket_name for b in buckets)
                if bucket_exists:
                    self.available = True
                    print(f"[Storage] Connected to bucket: {self.bucket_name}")
                else:
                    self._last_error = f"Bucket '{self.bucket_name}' not found"
                    print(f"[Storage] WARNING: {self._last_error}")
                    print(
                        f"[Storage] Available buckets: {[b.get('id') for b in buckets]}")
                    # Try anyway - uploads might work
                    self.available = True
            else:
                # Try anyway - uploads might work
                print(
                    f"[Storage] Bucket list returned {response.status_code}, will attempt uploads")
                self.available = True

        except requests.exceptions.Timeout:
            self._last_error = "Connection timeout when checking bucket"
            print(f"[Storage] ERROR: {self._last_error}")
            self.available = False
        except requests.exceptions.ConnectionError as e:
            self._last_error = f"Connection error: {str(e)[:100]}"
            print(f"[Storage] ERROR: {self._last_error}")
            self.available = False
        except Exception as e:
            self._last_error = f"Failed to connect: {str(e)}"
            print(f"[Storage] ERROR: {self._last_error}")
            # Set available to try anyway - might work
            self.available = True

    def get_last_error(self) -> Optional[str]:
        """Get the last error message for debugging"""
        return self._last_error

    def test_connection(self) -> Tuple[bool, str]:
        """Test if storage is properly configured and accessible"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            return False, "Supabase not configured - check .env file"

        if not self.available:
            return False, self._last_error or "Storage not available"

        # Try a simple test - list buckets (use service key for better permissions)
        try:
            headers = {
                'Authorization': f'Bearer {self.service_key}',
                'apikey': self.service_key
            }
            # Use bucket list endpoint instead of object list
            test_url = f"{self.supabase_url}/storage/v1/bucket"
            response = requests.get(test_url, headers=headers, timeout=10)

            if response.status_code == 200:
                buckets = response.json()
                bucket_exists = any(
                    b.get('id') == self.bucket_name for b in buckets)
                if bucket_exists:
                    return True, f"Storage connected - bucket '{self.bucket_name}' exists"
                else:
                    return False, f"Bucket '{self.bucket_name}' not found - run create_bucket script"
            elif response.status_code == 401:
                return False, "Authentication failed - check SUPABASE_KEY"
            else:
                return False, f"Storage error: {response.status_code}"
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    def _get_headers(self) -> dict:
        """Get headers for REST API calls"""
        return {
            'Authorization': f'Bearer {self.supabase_key}',
            'apikey': self.supabase_key,
            'Content-Type': 'application/octet-stream',
            'x-upsert': 'false'
        }

    def upload_file(
        self,
        file_path: str,
        folder: str = "documents",
        custom_filename: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload a file to Supabase Storage using REST API

        Args:
            file_path: Local file path to upload
            folder: Folder name in the bucket (documents, images, profiles, etc.)
            custom_filename: Optional custom filename, otherwise uses original

        Returns:
            Tuple of (success, file_url or error_message, file_path_in_bucket)
        """
        # Always try to upload regardless of availability check
        # The check might fail but upload might still work

        if not REQUESTS_AVAILABLE or requests is None:
            error_msg = "requests module not installed"
            logger.error(f"[Storage] {error_msg}")
            return False, error_msg, None

        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(f"[Storage] {error_msg}")
            return False, error_msg, None

        try:
            # Generate unique filename
            original_filename = custom_filename or os.path.basename(file_path)
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"

            # Full path in bucket
            bucket_path = f"{folder}/{unique_filename}"

            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            logger.info(
                f"[Storage] Uploading file to {self.bucket_name}/{bucket_path}")
            print(
                f"[Storage] Uploading file: {original_filename} to {folder}/")

            # Upload via REST API
            upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{bucket_path}"
            headers = self._get_headers()
            headers['Content-Type'] = self._get_mime_type(file_ext)

            print(f"[Storage] Upload URL: {upload_url}")

            response = requests.post(
                upload_url, headers=headers, data=file_content, timeout=60)

            print(f"[Storage] Response status: {response.status_code}")
            print(
                f"[Storage] Response text: {response.text[:500] if response.text else 'Empty'}")

            if response.status_code in [200, 201]:
                # Get public URL
                file_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{bucket_path}"
                logger.info(f"[Storage] Successfully uploaded: {bucket_path}")
                logger.info(f"[Storage] File URL: {file_url}")
                print(f"[Storage] Upload successful: {file_url}")
                return True, file_url, bucket_path
            else:
                # Provide more specific error messages
                error_msg = f"Upload failed: HTTP {response.status_code}"
                try:
                    error_details = response.json()
                    error_message = error_details.get(
                        'message', response.text[:200])

                    # Add specific guidance based on error type
                    if 'row-level-security' in error_message.lower() or 'rls' in error_message.lower():
                        error_msg = f"Permission denied (RLS). Contact admin to set storage policies."
                    elif 'bucket' in error_message.lower() and 'not found' in error_message.lower():
                        error_msg = f"Storage bucket not found. Run: python scripts/create_bucket.py"
                    elif 'quota' in error_message.lower() or 'limit' in error_message.lower():
                        error_msg = f"Storage quota exceeded. Check Supabase plan limits."
                    elif 'duplicate' in error_message.lower():
                        error_msg = f"File already exists. Try with a different filename."
                    else:
                        error_msg = f"Upload failed: {error_message}"
                except:
                    error_msg += f" - {response.text[:200]}"
                logger.error(f"[Storage] {error_msg}")
                print(f"[Storage] ERROR: {error_msg}")
                return False, error_msg, None

        except requests.exceptions.Timeout:
            error_msg = "Upload failed: Connection timeout. Check your internet connection."
            logger.error(f"[Storage] {error_msg}")
            print(f"[Storage] ERROR: {error_msg}")
            return False, error_msg, None
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Upload failed: Connection error - {str(e)[:100]}. Check internet and Supabase config."
            logger.error(f"[Storage] {error_msg}")
            print(f"[Storage] ERROR: {error_msg}")
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            logger.error(f"[Storage] {error_msg}")
            print(f"[Storage] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg, None

    def upload_file_from_bytes(
        self,
        file_content: bytes,
        filename: str,
        folder: str = "documents",
        content_type: str = "application/octet-stream"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload file from bytes

        Args:
            file_content: File content as bytes
            filename: Original filename
            folder: Folder name in bucket
            content_type: MIME type

        Returns:
            Tuple of (success, file_url or error_message, file_path_in_bucket)
        """
        if not self.available:
            return False, "Supabase storage not available", None

        if not REQUESTS_AVAILABLE or requests is None:
            return False, "requests module not installed", None

        try:
            # Generate unique filename
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            bucket_path = f"{folder}/{unique_filename}"

            # Upload via REST API
            upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{bucket_path}"
            headers = self._get_headers()
            headers['Content-Type'] = content_type

            response = requests.post(
                upload_url, headers=headers, data=file_content, timeout=30)

            if response.status_code in [200, 201]:
                file_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{bucket_path}"
                logger.info(f"[Storage] Uploaded from bytes: {bucket_path}")
                return True, file_url, bucket_path
            else:
                error_msg = f"Upload failed: {response.status_code}"
                return False, error_msg, None

        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            logger.error(f"[Storage] {error_msg}")
            return False, error_msg, None

    def delete_file(self, bucket_path: str) -> Tuple[bool, str]:
        """
        Delete a file from Supabase Storage

        Args:
            bucket_path: Path in bucket (e.g., 'documents/abc123.jpg')

        Returns:
            Tuple of (success, error_message if any)
        """
        if not self.available:
            return False, "Supabase storage not available"

        # Delete requires service key - not supported with anon key
        return False, "Delete not supported with anon key"

    def get_file_url(self, bucket_path: str) -> str:
        """Get public URL for a file"""
        if not self.available:
            return ""
        return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{bucket_path}"

    def list_files(self, folder: str = "") -> list:
        """List files in a folder - requires service key"""
        # Not available with anon key
        return []

    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from file extension"""
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.7z': 'application/x-7z-compressed',
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.wav': 'audio/wav',
        }
        return mime_types.get(extension.lower(), 'application/octet-stream')


# Global instance
_storage: Optional[SupabaseStorage] = None


def get_storage() -> SupabaseStorage:
    """Get global Supabase Storage instance"""
    global _storage
    if _storage is None:
        _storage = SupabaseStorage()
    return _storage


def upload_to_supabase(
    file_path: str,
    folder: str = "documents",
    custom_filename: str = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Convenience function to upload file to Supabase Storage

    Returns:
        Tuple of (success, file_url_or_error, bucket_path)
    """
    storage = get_storage()
    return storage.upload_file(file_path, folder, custom_filename)


def upload_image_to_supabase(
    image_path: str,
    folder: str = "images"
) -> Tuple[bool, str, Optional[str]]:
    """Upload image to Supabase Storage"""
    storage = get_storage()
    return storage.upload_file(image_path, folder)


def upload_document_to_supabase(
    doc_path: str,
    folder: str = "documents"
) -> Tuple[bool, str, Optional[str]]:
    """Upload document to Supabase Storage"""
    storage = get_storage()
    return storage.upload_file(doc_path, folder)


def delete_from_supabase(bucket_path: str) -> Tuple[bool, str]:
    """Delete file from Supabase Storage"""
    storage = get_storage()
    return storage.delete_file(bucket_path)


def upload_company_logo(file_content: bytes, filename: str) -> Optional[str]:
    """
    Upload company logo to Supabase Storage

    Args:
        file_content: File content as bytes
        filename: Original filename (e.g., logo.png)

    Returns:
        URL of uploaded file or None if failed
    """
    storage = get_storage()

    # Determine content type from filename
    import os
    file_ext = os.path.splitext(filename)[1].lower()
    content_type = storage._get_mime_type(file_ext)

    # Upload to logo folder
    success, url_or_error, _ = storage.upload_file_from_bytes(
        file_content=file_content,
        filename=filename,
        folder="logo",
        content_type=content_type
    )

    if success:
        return url_or_error
    else:
        print(f"[Storage] Logo upload failed: {url_or_error}")
        return None
