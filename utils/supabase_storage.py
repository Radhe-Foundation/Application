"""
Vernika - Supabase Storage Utility
Handles file uploads to Supabase Storage for documents, images, and other files
Updated to use REST API directly for more reliable uploads
"""

import os
import uuid
import logging
import requests
from typing import Optional, Tuple
from datetime import datetime

# Check for requests - required for Supabase Storage
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: 'requests' module not installed. File uploads to Supabase will not work.")

from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_STORAGE_URL, SUPABASE_STORAGE_BUCKET

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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.available = False
        self.bucket_name = SUPABASE_STORAGE_BUCKET
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY

        if not SUPABASE_URL or not SUPABASE_KEY:
            print("[Storage] Supabase not configured")
            return

        # Check if bucket exists by testing with a simple request
        try:
            # Use REST API to check if bucket is accessible
            headers = {
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'apikey': SUPABASE_KEY
            }
            # Try to access the bucket
            test_url = f"{SUPABASE_URL}/storage/v1/bucket/{self.bucket_name}"
            response = requests.get(test_url, headers=headers, timeout=5)

            if response.status_code == 200:
                self.available = True
                print(f"[Storage] Connected to bucket: {self.bucket_name}")
            else:
                print(f"[Storage] Bucket check failed: {response.status_code}")
                # Try anyway - uploads might still work
                self.available = True
                print(f"[Storage] Will attempt uploads anyway")

        except Exception as e:
            print(f"[Storage] Failed to connect: {e}")
            self.available = False

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
        if not self.available:
            return False, "Supabase storage not available", None

        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}", None

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

            # Upload via REST API
            upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{bucket_path}"
            headers = self._get_headers()
            headers['Content-Type'] = self._get_mime_type(file_ext)

            response = requests.post(
                upload_url, headers=headers, data=file_content, timeout=30)

            if response.status_code in [200, 201]:
                # Get public URL
                file_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{bucket_path}"
                logger.info(f"[Storage] Uploaded: {bucket_path}")
                return True, file_url, bucket_path
            else:
                error_msg = f"Upload failed: {response.status_code} - {response.text[:100]}"
                logger.error(f"[Storage] {error_msg}")
                return False, error_msg, None

        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            logger.error(f"[Storage] {error_msg}")
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
