"""
Media Upload Tracking Model - NEW FK-Based System

Tracks all media uploads (images, videos, 3D models) with metadata:
- Who uploaded it
- When it was uploaded
- Entity relationships via FK (Product.featured_media, Category.featured_media, etc.)
- File metadata (size, dimensions, format)
- Processing status

Architecture:
- Entity-agnostic: MediaUpload doesn't know about entities
- Relationships: Entities point to MediaUpload via FK
- Works for ALL entities: Product, Category, Variant, future ones
- Works for ALL media types: image, video, 3D model
"""

from django.db import models
from django.contrib.auth import get_user_model
from workspace.core.models.base_models import TenantScopedModel
import uuid

User = get_user_model()


class MediaUpload(TenantScopedModel):
    """
    Tracks all media uploads across the platform

    Security:
    - Workspace scoped (multi-tenant isolation)
    - User attribution (audit trail)

    Use Cases:
    - Audit logs (who uploaded what when)
    - Quota tracking (per workspace/user)
    - Orphan file cleanup (unused uploads)
    - Analytics (upload patterns)
    """

    # Media Types
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('3d_model', '3D Model'),
        ('document', 'Document'),
    ]

    # Processing Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),          # Just uploaded, not processed yet
        ('processing', 'Processing'),    # Currently being optimized/transcoded
        ('completed', 'Completed'),      # Processing complete
        ('failed', 'Failed'),            # Processing failed
        ('orphaned', 'Orphaned'),        # Not attached to any entity
    ]

    # Primary Keys
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User attribution
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='media_uploads',
        db_index=True,
        help_text="User who uploaded this file"
    )

    # Media classification
    media_type = models.CharField(
        max_length=20,
        choices=MEDIA_TYPE_CHOICES,
        db_index=True,
        help_text="Type of media (image, video, 3D model)"
    )

    # NEW SYSTEM: Entity relationships via FK (Product.featured_media, etc.)
    # No entity_type/entity_id needed - relationships defined on entity models

    # File information
    original_filename = models.CharField(
        max_length=255,
        help_text="Original filename from upload"
    )

    file_path = models.CharField(
        max_length=500,
        unique=True,
        null=True,
        blank=True,
        help_text="Storage path (works for both local and S3)"
    )

    file_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Public URL to access the file"
    )

    file_size = models.BigIntegerField(
        help_text="File size in bytes"
    )

    mime_type = models.CharField(
        max_length=100,
        help_text="MIME type (e.g., image/jpeg, video/mp4)"
    )

    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        null=True,
        blank=True,
        help_text="SHA256 hash of file content for deduplication"
    )

    # Image-specific metadata (NULL for non-images)
    width = models.IntegerField(
        null=True,
        blank=True,
        help_text="Image/video width in pixels"
    )

    height = models.IntegerField(
        null=True,
        blank=True,
        help_text="Image/video height in pixels"
    )

    # Processing information
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Processing status"
    )

    optimized_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Path to optimized version (if applicable)"
    )

    thumbnail_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Path to thumbnail (if applicable)"
    )

    # Additional metadata (JSON for flexibility)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (format, duration for videos, etc.)"
    )

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete (for audit trail)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the file was deleted (soft delete)"
    )

    class Meta:
        app_label = 'medialib'  # Explicit app label for medialib module
        db_table = 'medialib_uploads'  # Generic table name (not store-specific)
        ordering = ['-uploaded_at']
        indexes = [
            # Core workspace indexes
            models.Index(fields=['workspace', 'uploaded_by']),
            models.Index(fields=['workspace', 'media_type']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['uploaded_at']),
            # Deduplication performance indexes
            models.Index(fields=['workspace', 'file_hash', 'deleted_at']),
            models.Index(fields=['workspace', 'status', 'deleted_at']),
            # Cleanup job performance
            models.Index(fields=['deleted_at', 'uploaded_at']),
        ]
        verbose_name = 'Media Upload'
        verbose_name_plural = 'Media Uploads'

    def __str__(self):
        return f"{self.media_type} - {self.original_filename} ({self.workspace.name})"

    @property
    def is_image(self):
        """Check if this is an image"""
        return self.media_type == 'image'

    @property
    def is_video(self):
        """Check if this is a video"""
        return self.media_type == 'video'

    @property
    def is_3d_model(self):
        """Check if this is a 3D model"""
        return self.media_type == '3d_model'

    @property
    def is_processed(self):
        """Check if processing is complete"""
        return self.status == 'completed'

    @property
    def is_orphaned(self):
        """Check if file is not attached to any entity"""
        return self.status == 'orphaned'

    def mark_as_completed(self):
        """Mark upload as processed"""
        from django.utils import timezone
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])

    def mark_as_failed(self):
        """Mark upload processing as failed"""
        self.status = 'failed'
        self.save(update_fields=['status'])

    def mark_as_orphaned(self):
        """Mark upload as orphaned (not attached to any entity)"""
        self.status = 'orphaned'
        self.save(update_fields=['status'])

    def soft_delete(self):
        """Soft delete the upload record"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
