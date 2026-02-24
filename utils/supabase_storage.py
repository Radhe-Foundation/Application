"""
Vernika - Supabase Storage Utility
Handles file uploads to Supabase Storage for documents, images, and other files
"""

from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_STORAGE_URL, SUPABASE_STORAGE_BUCKET
import os
import uuid
import logging
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Supabase
try:
    from supabase import create_client, Client
    from supabase.lib.storage_client import StorageFileApi
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase not installed - file storage will use local fallback")


class SupabaseStorage:
    """Supabase Storage client for file uploads"""

    _instance: Optional['SupabaseStorage'] = None
    _client: Optional[Client] = None
    _bucket = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not SUPABASE_AVAILABLE:
            self.available = False
            return

        if self._client is None and SUPABASE_KEY:
            try:
                self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
                self._bucket = self._client.storage.from_(
                    SUPABASE_STORAGE_BUCKET)
                self.available = True
                print(
                    f"[Storage] Connected to Supabase Storage bucket: {SUPABASE_STORAGE_BUCKET}")
            except Exception as e:
                print(f"[Storage] Failed to connect: {e}")
                self.available = False
        else:
            self.available = False

    def _ensure_bucket_exists(self) -> bool:
        """Ensure the storage bucket exists, create if not"""
        if not self._client:
            return False

        try:
            # Try to get bucket info - will fail if doesn't exist
            self._bucket = self._client.storage.get_bucket(
                SUPABASE_STORAGE_BUCKET)
            return True
        except Exception:
            try:
                # Create bucket if it doesn't exist
                self._bucket = self._client.storage.create_bucket(
                    SUPABASE_STORAGE_BUCKET,
                    options={
                        'public': True,
                        'allowed_mime_types': ['*'],
                        'file_size_limit': 52428800,  # 50MB
                    }
                )
                print(f"[Storage] Created bucket: {SUPABASE_STORAGE_BUCKET}")
                return True
            except Exception as e:
                print(f"[Storage] Failed to create bucket: {e}")
                return False

    def upload_file(
        self,
        file_path: str,
        folder: str = "documents",
        custom_filename: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload a file to Supabase Storage

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

        # Ensure bucket exists
        if not self._ensure_bucket_exists():
            return False, "Failed to access storage bucket", None

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

            # Upload to Supabase
            response = self._bucket.upload(
                bucket_path,
                file_content,
                options={
                    'content_type': self._get_mime_type(file_ext),
                    'upsert': False
                }
            )

            # Get public URL
            file_url = self._bucket.get_public_url(bucket_path)

            logger.info(f"[Storage] Uploaded: {bucket_path} -> {file_url}")
            return True, file_url, bucket_path

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

        # Ensure bucket exists
        if not self._ensure_bucket_exists():
            return False, "Failed to access storage bucket", None

        try:
            # Generate unique filename
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            bucket_path = f"{folder}/{unique_filename}"

            # Upload to Supabase
            response = self._bucket.upload(
                bucket_path,
                file_content,
                options={
                    'content_type': content_type,
                    'upsert': False
                }
            )

            # Get public URL
            file_url = self._bucket.get_public_url(bucket_path)

            logger.info(f"[Storage] Uploaded from bytes: {bucket_path}")
            return True, file_url, bucket_path

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

        try:
            self._bucket.remove([bucket_path])
            logger.info(f"[Storage] Deleted: {bucket_path}")
            return True, ""
        except Exception as e:
            error_msg = f"Delete failed: {str(e)}"
            logger.error(f"[Storage] {error_msg}")
            return False, error_msg

    def get_file_url(self, bucket_path: str) -> str:
        """Get public URL for a file"""
        if not self.available:
            return ""
        return self._bucket.get_public_url(bucket_path)

    def list_files(self, folder: str = "") -> list:
        """List files in a folder"""
        if not self.available:
            return []

        try:
            if folder:
                response = self._bucket.list(path=folder)
            else:
                response = self._bucket.list()
            return response
        except Exception as e:
            logger.error(f"[Storage] List failed: {e}")
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
