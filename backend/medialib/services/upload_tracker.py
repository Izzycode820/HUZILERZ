"""
Upload Tracking Service

Service to track media uploads with user attribution and metadata
Works with MediaUpload model to provide audit trail and analytics
"""

from typing import Dict, Any, Optional, List
from django.utils import timezone
from medialib.models.media_upload_model import MediaUpload
import logging

logger = logging.getLogger(__name__)


class UploadTracker:
    """
    Service for tracking media uploads with metadata (NEW FK-based system)

    Features:
    - Create entity-agnostic upload records
    - Track user attribution
    - Query uploads by workspace/user
    - Find orphaned uploads (not referenced by any entity FK)
    - Calculate storage quotas

    NEW Flow:
        1. track_upload() → Returns MediaUpload with ID
        2. Entity sets FK: product.featured_media_id = upload_id
        3. Media can be reused by multiple entities
    """

    def track_upload(
        self,
        workspace_id: str,
        user_id: str,
        media_type: str,
        original_filename: str,
        file_size: int,
        mime_type: str,
        file_path: str = None,  # Optional - may not exist yet
        file_url: str = None,   # Optional - may not exist yet
        status: str = 'pending',
        file_hash: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> MediaUpload:
        """
        Create MediaUpload record (entity-agnostic)

        NEW Flow:
            1. Create MediaUpload record first
            2. Get upload_id
            3. Attach to entity via FK: entity.featured_media_id = upload_id

        Args:
            workspace_id: Workspace ID
            user_id: User who uploaded
            media_type: 'image', 'video', '3d_model'
            original_filename: Original filename
            file_size: File size in bytes
            mime_type: MIME type
            file_path: Storage path (optional - may not exist yet)
            file_url: Public URL (optional - may not exist yet)
            status: Upload status ('pending', 'processing', 'completed')
            file_hash: SHA256 hash for deduplication (optional)
            width: Image/video width (optional)
            height: Image/video height (optional)
            metadata: Additional metadata (optional)

        Returns:
            MediaUpload instance
        """
        try:
            upload = MediaUpload.objects.create(
                workspace_id=workspace_id,
                uploaded_by_id=user_id,
                media_type=media_type,
                original_filename=original_filename,
                file_path=file_path,
                file_url=file_url,
                file_size=file_size,
                mime_type=mime_type,
                file_hash=file_hash,
                width=width,
                height=height,
                metadata=metadata or {},
                status=status
            )

            logger.info(f"Upload tracked: {upload.id} - {original_filename} by user {user_id}")
            return upload

        except Exception as e:
            logger.error(f"Upload tracking failed: {str(e)}", exc_info=True)
            raise

    def update_file_paths(
        self,
        upload_id: str,
        file_path: str,
        file_url: str
    ) -> MediaUpload:
        """
        Update file paths after file is saved to storage

        Args:
            upload_id: Upload ID
            file_path: Storage path
            file_url: Public URL

        Returns:
            Updated MediaUpload instance
        """
        try:
            upload = MediaUpload.objects.get(id=upload_id)
            upload.file_path = file_path
            upload.file_url = file_url
            upload.save(update_fields=['file_path', 'file_url'])

            logger.info(f"File paths updated for upload: {upload_id}")
            return upload

        except MediaUpload.DoesNotExist:
            logger.error(f"Upload not found: {upload_id}")
            raise
        except Exception as e:
            logger.error(f"File path update failed: {str(e)}", exc_info=True)
            raise

    def update_upload_status(
        self,
        upload_id: str,
        status: str,
        optimized_path: Optional[str] = None,
        thumbnail_path: Optional[str] = None
    ) -> MediaUpload:
        """
        Update upload processing status

        Args:
            upload_id: Upload ID
            status: New status
            optimized_path: Path to optimized version (optional)
            thumbnail_path: Path to thumbnail (optional)

        Returns:
            Updated MediaUpload instance
        """
        try:
            upload = MediaUpload.objects.get(id=upload_id)

            upload.status = status

            if optimized_path:
                upload.optimized_path = optimized_path

            if thumbnail_path:
                upload.thumbnail_path = thumbnail_path

            if status == 'completed':
                upload.processed_at = timezone.now()

            upload.save()

            logger.info(f"Upload status updated: {upload_id} -> {status}")
            return upload

        except MediaUpload.DoesNotExist:
            logger.error(f"Upload not found: {upload_id}")
            raise
        except Exception as e:
            logger.error(f"Upload status update failed: {str(e)}", exc_info=True)
            raise

    def get_user_uploads(
        self,
        workspace_id: str,
        user_id: str,
        limit: int = 50,
        media_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = 'date',
        sort_order: str = 'desc'
    ) -> List[MediaUpload]:
        """
        Get recent uploads by a specific user with search and filters

        Args:
            workspace_id: Workspace ID
            user_id: User ID
            limit: Maximum number of uploads to return
            media_type: Filter by media type (image, video, 3d_model)
            search: Search by filename
            sort_by: Sort by field (date, name, size)
            sort_order: Sort order (asc, desc)

        Returns:
            List of MediaUpload instances
        """
        queryset = MediaUpload.objects.filter(
            workspace_id=workspace_id,
            uploaded_by_id=user_id,
            deleted_at__isnull=True
        )

        # Filter by media type
        if media_type:
            queryset = queryset.filter(media_type=media_type)

        # Search by filename
        if search:
            queryset = queryset.filter(original_filename__icontains=search)

        # Sort
        sort_field_map = {
            'date': 'uploaded_at',
            'name': 'original_filename',
            'size': 'file_size'
        }
        sort_field = sort_field_map.get(sort_by, 'uploaded_at')

        if sort_order == 'asc':
            queryset = queryset.order_by(sort_field)
        else:
            queryset = queryset.order_by(f'-{sort_field}')

        return list(queryset[:limit])

    def get_orphaned_uploads(
        self,
        workspace_id: str,
        older_than_days: int = 7
    ) -> List[MediaUpload]:
        """
        Find orphaned uploads (not attached to any entity or pending too long)

        Args:
            workspace_id: Workspace ID
            older_than_days: Consider uploads older than X days as orphaned

        Returns:
            List of potentially orphaned MediaUpload instances
        """
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=older_than_days)

        return list(
            MediaUpload.objects.filter(
                workspace_id=workspace_id,
                status='pending',
                uploaded_at__lt=cutoff_date,
                deleted_at__isnull=True
            ).order_by('uploaded_at')
        )

    def calculate_workspace_storage(self, workspace_id: str) -> Dict[str, Any]:
        """
        Calculate total storage used by a workspace

        Args:
            workspace_id: Workspace ID

        Returns:
            Dict with storage statistics
        """
        from django.db.models import Sum, Count

        uploads = MediaUpload.objects.filter(
            workspace_id=workspace_id,
            deleted_at__isnull=True
        )

        total_size = uploads.aggregate(total=Sum('file_size'))['total'] or 0

        by_media_type = {}
        for media_type, _ in MediaUpload.MEDIA_TYPE_CHOICES:
            type_uploads = uploads.filter(media_type=media_type)
            by_media_type[media_type] = {
                'count': type_uploads.count(),
                'size': type_uploads.aggregate(total=Sum('file_size'))['total'] or 0
            }

        return {
            'workspace_id': workspace_id,
            'total_uploads': uploads.count(),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_media_type': by_media_type,
            'calculated_at': timezone.now().isoformat()
        }

    def calculate_user_storage(self, workspace_id: str, user_id: str) -> Dict[str, Any]:
        """
        Calculate total storage used by a specific user

        Args:
            workspace_id: Workspace ID
            user_id: User ID

        Returns:
            Dict with storage statistics
        """
        from django.db.models import Sum

        uploads = MediaUpload.objects.filter(
            workspace_id=workspace_id,
            uploaded_by_id=user_id,
            deleted_at__isnull=True
        )

        total_size = uploads.aggregate(total=Sum('file_size'))['total'] or 0

        return {
            'workspace_id': workspace_id,
            'user_id': user_id,
            'total_uploads': uploads.count(),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'calculated_at': timezone.now().isoformat()
        }

    def get_upload_by_path(self, file_path: str) -> Optional[MediaUpload]:
        """
        Get upload record by file path

        Args:
            file_path: File path

        Returns:
            MediaUpload instance or None
        """
        try:
            return MediaUpload.objects.get(file_path=file_path, deleted_at__isnull=True)
        except MediaUpload.DoesNotExist:
            return None


# Global instance for easy access
upload_tracker = UploadTracker()
