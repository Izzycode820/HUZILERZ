"""
Shopify-Style Storage Service - Integrated with Hosting Infrastructure

Features:
- Shopify-inspired multi-tenant storage (one shared bucket for all)
- Reads bucket paths from WorkspaceInfrastructure.infra_metadata
- Gets CloudFront URLs from HostingEnvironment.aws_resources
- Entity-agnostic upload organization by upload_id
- Automatic cache headers for optimal CDN performance
- Works in both mock mode (dev) and AWS mode (production)

Shopify-Style Architecture:
- Shared buckets: shared-pool-media, shared-pool-storage
- Simple paths: workspaces/{id}/products/{upload_id}/original/file.jpg
- Type-based folders: products/, themes/, collections/, files/
- No entity coupling - files tracked by upload_id

Infrastructure Integration:
- Bucket paths from: WorkspaceInfrastructure.infra_metadata['media_product_path']
- CDN domain from: HostingEnvironment.aws_resources['cdn_distribution_domain']
- Respects INFRASTRUCTURE_MODE setting (mock/aws)
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Literal, Tuple
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Type definitions for better type safety
MediaType = Literal['images', 'videos', '3d_models', 'documents']
VersionType = Literal['original', 'optimized', 'thumbnails', 'previews', 'tiny']


class StorageService:
    """
    Shopify-style entity-agnostic storage service integrated with hosting infrastructure

    Architecture:
    - Reads bucket paths from WorkspaceInfrastructure.infra_metadata
    - Gets CDN URLs from HostingEnvironment.aws_resources
    - Supports both local (dev) and S3 (production) via INFRASTRUCTURE_MODE
    - No entity coupling - all media in one pool per workspace

    Folder Structure (Entity-Agnostic):
    workspaces/
      └── {workspace_id}/
          └── media/                    ← All media here (no entity subfolders)
              └── {upload_id}/          ← Unique per MediaUpload record
                  ├── images/
                  │   ├── original/
                  │   ├── optimized/
                  │   └── thumbnails/
                  ├── videos/
                  └── 3d_models/

    Local Example:
      local_data/media/workspaces/abc-123/media/def-456/images/original/shoe.jpg

    S3 Example:
      s3://shared-pool-media/workspaces/abc-123/media/def-456/images/original/shoe.jpg
    """

    # Cache headers for optimal CDN performance
    CACHE_HEADERS = {
        'original': 'public, max-age=31536000, immutable',      # 1 year
        'optimized': 'public, max-age=31536000, immutable',     # 1 year
        'thumbnails': 'public, max-age=31536000, immutable',    # 1 year
        'tiny': 'public, max-age=31536000, immutable',          # 1 year
        'previews': 'public, max-age=604800, s-maxage=2592000', # 7 days/30 days CDN
    }

    def __init__(self):
        self.is_production = not settings.DEBUG
        self.infrastructure_mode = getattr(settings, 'INFRASTRUCTURE_MODE', 'mock')
        self.cdn_enabled = self.infrastructure_mode == 'aws'

    def generate_media_path(
        self,
        workspace_id: str,
        upload_id: str,
        media_type: MediaType,
        version: VersionType,
        filename: str
    ) -> Tuple[str, str]:
        """
        Generate entity-agnostic media path (Shopify-style)

        Args:
            workspace_id: Workspace identifier
            upload_id: MediaUpload UUID
            media_type: Type of media ('images', 'videos', '3d_models', 'documents')
            version: Version type ('original', 'optimized', 'thumbnails', etc.)
            filename: Original filename

        Returns:
            Tuple[bucket_name, file_path]

        Examples:
            Local: ('', 'workspaces/abc-123/media/def-456/images/original/shoe_20250202_a1b2c3d4.jpg')
            AWS: ('shared-pool-media', 'workspaces/abc-123/media/def-456/images/original/shoe_20250202_a1b2c3d4.jpg')
        """
        # Extract file extension
        file_extension = filename.split('.')[-1].lower()

        # Generate unique filename with timestamp
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime('%Y%m%d')
        safe_name = ''.join(c for c in filename.split('.')[0] if c.isalnum() or c in ('-', '_'))
        safe_name = safe_name[:50]  # Limit length

        # Generate unique filename
        unique_filename = f"{safe_name}_{timestamp}_{unique_id}.{file_extension}"

        # Build entity-agnostic path
        path = f"workspaces/{workspace_id}/media/{upload_id}/{media_type}/{version}/{unique_filename}"

        # Get bucket name from infrastructure
        bucket_name = self._get_bucket_for_workspace(workspace_id)

        return (bucket_name, path)

    def get_cache_header(self, file_path: str) -> str:
        """
        Get appropriate cache header based on file path

        Args:
            file_path: File path

        Returns:
            Cache-Control header value
        """
        for version, cache_header in self.CACHE_HEADERS.items():
            if f'/{version}/' in file_path:
                return cache_header
        # Default for unknown versions
        return 'public, max-age=604800'

    def _get_bucket_for_workspace(self, workspace_id: str) -> str:
        """
        Get bucket name from WorkspaceInfrastructure metadata

        Args:
            workspace_id: Workspace identifier

        Returns:
            Bucket name for S3, empty string for local storage
        """
        if self.infrastructure_mode == 'mock':
            # Local storage - no bucket needed
            return ''

        try:
            # Import here to avoid circular imports
            from workspace.hosting.models import WorkspaceInfrastructure

            workspace_infra = WorkspaceInfrastructure.objects.get(workspace_id=workspace_id)

            # Extract bucket from media_product_path
            # Format: s3://shared-pool-media/workspaces/{id}/products/
            media_path = workspace_infra.infra_metadata.get('media_product_path', '')

            if media_path.startswith('s3://'):
                bucket = media_path.replace('s3://', '').split('/')[0]
                return bucket

            return ''
        except Exception as e:
            logger.warning(f"Could not get bucket for workspace {workspace_id}: {e}")
            return ''

    def _get_cdn_domain_for_workspace(self, workspace_id: str) -> Optional[str]:
        """
        Get CloudFront CDN domain from HostingEnvironment

        Args:
            workspace_id: Workspace identifier

        Returns:
            CloudFront domain or None
        """
        if self.infrastructure_mode == 'mock':
            return None

        try:
            # Import here to avoid circular imports
            from workspace.hosting.models import WorkspaceInfrastructure

            workspace_infra = WorkspaceInfrastructure.objects.select_related('pool').get(workspace_id=workspace_id)

            if workspace_infra.pool and workspace_infra.pool.aws_resources:
                cdn_domain = workspace_infra.pool.aws_resources.get('cdn_distribution_domain')
                return cdn_domain

            return None
        except Exception as e:
            logger.warning(f"Could not get CDN domain for workspace {workspace_id}: {e}")
            return None

    def get_cdn_url(self, workspace_id: str, file_path: str) -> str:
        """
        Generate CDN URL for a file path using hosting infrastructure

        Args:
            workspace_id: Workspace identifier
            file_path: Relative file path in storage

        Returns:
            Full URL (CDN URL in AWS mode, local URL in mock mode)
        """
        if self.cdn_enabled:
            # Production: Get CDN domain from HostingEnvironment
            cdn_domain = self._get_cdn_domain_for_workspace(workspace_id)

            if cdn_domain:
                return f"https://{cdn_domain}/{file_path}"

            # Fallback to S3 direct URL if CDN not configured
            bucket_name = self._get_bucket_for_workspace(workspace_id)
            if bucket_name:
                region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
                if region == 'us-east-1':
                    return f"https://{bucket_name}.s3.amazonaws.com/{file_path}"
                return f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_path}"

        # Development: Use local URL
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        if not media_url.startswith('http'):
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            return f"{base_url}{media_url}{file_path}"
        return f"{media_url}{file_path}"

    def save_file(
        self,
        workspace_id: str,
        file_content: bytes,
        bucket: str,
        file_path: str,
        version: Optional[VersionType] = None
    ) -> Dict[str, Any]:
        """
        Save file using Django's storage abstraction with CDN support

        Args:
            workspace_id: Workspace identifier
            file_content: File content as bytes
            bucket: S3 bucket name (empty for local storage)
            file_path: Generated file path
            version: Optional version type for cache headers

        Returns:
            Dict with save result and file info
        """
        try:
            # Save file using Django's storage system
            saved_path = default_storage.save(file_path, ContentFile(file_content))

            # Generate CDN-aware URL
            file_url = self.get_cdn_url(workspace_id, saved_path)

            # Get cache header for this file
            cache_header = self.get_cache_header(saved_path)

            return {
                'success': True,
                'bucket': bucket,
                'file_path': saved_path,
                'file_url': file_url,
                'infrastructure_mode': self.infrastructure_mode,
                'cdn_enabled': self.cdn_enabled,
                'cache_control': cache_header
            }

        except Exception as e:
            logger.error(f"File save failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"File save failed: {str(e)}"
            }

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file using Django's storage abstraction

        Args:
            file_path: File path to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"File deletion failed: {str(e)}", exc_info=True)
            return False

    def get_file_url(self, workspace_id: str, file_path: str) -> Optional[str]:
        """
        Get CDN-aware file URL based on current environment

        Args:
            workspace_id: Workspace identifier
            file_path: File path

        Returns:
            File URL or None if file doesn't exist
        """
        try:
            if default_storage.exists(file_path):
                return self.get_cdn_url(workspace_id, file_path)
            return None
        except Exception as e:
            logger.error(f"File URL generation failed: {str(e)}", exc_info=True)
            return None

    def get_storage_info(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current storage configuration info

        Args:
            workspace_id: Optional workspace identifier for bucket details

        Returns:
            Dict with storage backend details
        """
        info = {
            'infrastructure_mode': self.infrastructure_mode,
            'cdn_enabled': self.cdn_enabled,
            'is_production': self.is_production,
        }

        if workspace_id:
            info['bucket'] = self._get_bucket_for_workspace(workspace_id)
            info['cdn_domain'] = self._get_cdn_domain_for_workspace(workspace_id)

        return info

    def delete_media(self, workspace_id: str, upload_id: str) -> Dict[str, Any]:
        """
        Delete all files for a specific media upload (entity-agnostic)

        Args:
            workspace_id: Workspace identifier
            upload_id: MediaUpload UUID

        Returns:
            Dict with deletion results
        """
        try:
            # Build upload folder path (entity-agnostic)
            upload_folder = f"workspaces/{workspace_id}/media/{upload_id}"

            deleted_count = 0

            if self.infrastructure_mode == 'mock':
                # Local filesystem deletion
                deleted_count = self._delete_local_folder(upload_folder)

            elif self.infrastructure_mode == 'aws':
                # AWS S3 batch deletion
                bucket_name = self._get_bucket_for_workspace(workspace_id)
                deleted_count = self._delete_s3_folder(bucket_name, upload_folder)

            return {
                'success': True,
                'deleted_count': deleted_count,
                'upload_folder': upload_folder,
                'infrastructure_mode': self.infrastructure_mode
            }

        except Exception as e:
            logger.error(f"Media deletion failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"Media deletion failed: {str(e)}"
            }

    def _delete_local_folder(self, folder_path: str) -> int:
        """
        Delete folder and all contents from local filesystem

        Args:
            folder_path: Relative folder path

        Returns:
            Number of files deleted
        """
        deleted_count = 0
        try:
            entity_path = Path(settings.MEDIA_ROOT) / folder_path
            if entity_path.exists():
                for file_path in entity_path.rglob('*'):
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_count += 1

                # Remove empty directories
                for dir_path in sorted(entity_path.rglob('*'), reverse=True):
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        dir_path.rmdir()

                entity_path.rmdir()

            logger.info(f"Deleted {deleted_count} files from local storage: {folder_path}")
        except Exception as e:
            logger.error(f"Local folder deletion failed: {str(e)}", exc_info=True)

        return deleted_count

    def _delete_s3_folder(self, bucket_name: str, folder_path: str) -> int:
        """
        Delete folder and all contents from S3 using batch delete

        Args:
            bucket_name: S3 bucket name
            folder_path: Relative folder path (S3 prefix)

        Returns:
            Number of files deleted
        """
        deleted_count = 0
        try:
            import boto3
            from botocore.exceptions import ClientError

            if not bucket_name:
                logger.error("Bucket name not provided")
                return 0

            s3_client = boto3.client('s3')

            # List all objects with the prefix
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=folder_path)

            # Collect objects to delete
            objects_to_delete = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects_to_delete.append({'Key': obj['Key']})

            # Batch delete (max 1000 objects per request)
            if objects_to_delete:
                # Split into chunks of 1000
                for i in range(0, len(objects_to_delete), 1000):
                    chunk = objects_to_delete[i:i + 1000]
                    response = s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': chunk, 'Quiet': True}
                    )
                    deleted_count += len(chunk)

            logger.info(f"Deleted {deleted_count} files from S3 bucket {bucket_name}: {folder_path}")

        except ImportError:
            logger.error("boto3 not installed - cannot delete from S3")
        except ClientError as e:
            logger.error(f"S3 deletion failed: {str(e)}", exc_info=True)
        except Exception as e:
            logger.error(f"S3 folder deletion failed: {str(e)}", exc_info=True)

        return deleted_count

    # ====================================================================
    # ENTITY-AGNOSTIC MEDIA STORAGE - Shopify-Style Unified Approach
    # ====================================================================

    def save_media(
        self,
        workspace_id: str,
        upload_id: str,
        media_type: MediaType,
        version: VersionType,
        file,
        filename: str
    ) -> Dict[str, Any]:
        """
        Save media (entity-agnostic, Shopify-style)

        Args:
            workspace_id: Workspace ID
            upload_id: MediaUpload UUID
            media_type: 'images', 'videos', '3d_models', or 'documents'
            version: 'original', 'optimized', 'thumbnails', 'previews', or 'tiny'
            file: File object
            filename: Original filename

        Returns:
            Dict with save result including CDN URL

        Example:
            save_media(workspace_id, upload_id, 'images', 'original', file, 'shoe.jpg')

        Returns:
            {
                'success': True,
                'bucket': 'shared-pool-media',
                'file_path': 'workspaces/abc/media/def/images/original/shoe_20250202_a1b2c3d4.jpg',
                'file_url': 'https://d123456abcdef.cloudfront.net/workspaces/abc/media/def/images/original/shoe.jpg',
                'infrastructure_mode': 'aws',
                'cdn_enabled': True,
                'cache_control': 'public, max-age=31536000, immutable'
            }
        """
        # Generate path and get bucket
        bucket, file_path = self.generate_media_path(
            workspace_id=workspace_id,
            upload_id=upload_id,
            media_type=media_type,
            version=version,
            filename=filename
        )

        # Read file content
        file_content = file.read() if hasattr(file, 'read') else file

        # Save file with hosting infrastructure integration
        return self.save_file(
            workspace_id=workspace_id,
            file_content=file_content,
            bucket=bucket,
            file_path=file_path,
            version=version
        )


"""
USAGE PATTERN - Entity-Agnostic Upload Flow:
=============================================

Step 1: User uploads file in UI
Step 2: Backend creates MediaUpload record immediately
        - workspace_id: Current workspace
        - uploaded_by: Current user
        - file_name: Original filename
        - media_type: 'images', 'videos', etc.

Step 3: Save file using upload_id from MediaUpload
        storage_service.save_media(
            workspace_id=workspace.id,
            upload_id=media_upload.id,  # ← From MediaUpload record
            media_type='images',
            version='original',
            file=request.FILES['file'],
            filename='shoe.jpg'
        )

Step 4: User attaches media to entities (Product, Category, Theme) via UI
        - Unified media library modal shows all workspace media
        - No entity coupling at storage level
        - Same file can be used by multiple entities

Benefits:
- No temporary files or cleanup needed
- All media tracked in MediaUpload table
- Entity-agnostic from the start
- Files organized by upload_id, not entity_id
"""


# Global instance for easy access
storage_service = StorageService()