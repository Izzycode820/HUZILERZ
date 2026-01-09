from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging
import os
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


class TemplateAsset(models.Model):
    """
    Template asset model for managing files and resources associated with templates.
    Supports various asset types including images, stylesheets, scripts, and configuration files.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Asset ID",
        help_text="Unique identifier for the template asset"
    )

    # Asset Type Choices
    ASSET_TYPE_IMAGE = 'image'
    ASSET_TYPE_STYLESHEET = 'stylesheet'
    ASSET_TYPE_SCRIPT = 'script'
    ASSET_TYPE_CONFIG = 'config'
    ASSET_TYPE_FONT = 'font'
    ASSET_TYPE_OTHER = 'other'

    ASSET_TYPE_CHOICES = [
        (ASSET_TYPE_IMAGE, 'Image'),
        (ASSET_TYPE_STYLESHEET, 'Stylesheet'),
        (ASSET_TYPE_SCRIPT, 'Script'),
        (ASSET_TYPE_CONFIG, 'Configuration'),
        (ASSET_TYPE_FONT, 'Font'),
        (ASSET_TYPE_OTHER, 'Other'),
    ]

    # Status Choices
    STATUS_ACTIVE = 'active'
    STATUS_DEPRECATED = 'deprecated'
    STATUS_DELETED = 'deleted'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_DEPRECATED, 'Deprecated'),
        (STATUS_DELETED, 'Deleted'),
    ]

    # Core Relationships
    template = models.ForeignKey(
        'Template',
        on_delete=models.CASCADE,
        related_name='assets',
        verbose_name="Template",
        help_text="Parent template this asset belongs to"
    )
    version = models.ForeignKey(
        'TemplateVersion',
        on_delete=models.CASCADE,
        related_name='assets',
        verbose_name="Template Version",
        help_text="Specific template version this asset belongs to"
    )

    # Asset Information
    file_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="File Name",
        help_text="Name of the asset file"
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name="File Path",
        help_text="Relative path to the asset within the template"
    )
    asset_type = models.CharField(
        max_length=20,
        choices=ASSET_TYPE_CHOICES,
        default=ASSET_TYPE_OTHER,
        db_index=True,
        verbose_name="Asset Type",
        help_text="Type of asset file"
    )

    # File Metadata
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name="File Size",
        help_text="Size of the asset file in bytes"
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="MIME Type",
        help_text="MIME type of the asset file"
    )
    checksum = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Checksum",
        help_text="SHA-256 checksum for file integrity verification"
    )

    # CDN Information
    cdn_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="CDN URL",
        help_text="Full CDN URL for accessing this asset"
    )
    cdn_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="CDN Path",
        help_text="CDN path relative to template version"
    )

    # Status and Metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True,
        verbose_name="Status",
        help_text="Current status of the asset"
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name="Is Required",
        help_text="Whether this asset is required for the template to function"
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name="Is Public",
        help_text="Whether this asset is publicly accessible"
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_template_assets',
        verbose_name="Created By",
        help_text="User who created this asset"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    class Meta:
        db_table = 'theme_template_assets'
        ordering = ['template', 'version', 'asset_type', 'file_path']
        unique_together = ['template', 'version', 'file_path']
        indexes = [
            models.Index(fields=['template', 'version']),
            models.Index(fields=['asset_type']),
            models.Index(fields=['status']),
            models.Index(fields=['file_name']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Template Asset"
        verbose_name_plural = "Template Assets"

    def __str__(self):
        return f"{self.file_name} ({self.asset_type}) - {self.template.name}"

    def clean(self):
        """Custom validation for the template asset model"""
        super().clean()

        # Validate file path format
        if self.file_path:
            # Check for path traversal attempts
            if '..' in self.file_path or self.file_path.startswith('/'):
                raise ValidationError({
                    'file_path': 'File path cannot contain path traversal sequences or absolute paths'
                })

            # Validate file extension based on asset type
            file_ext = os.path.splitext(self.file_path)[1].lower()
            if self.asset_type == self.ASSET_TYPE_IMAGE:
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']
                if file_ext not in valid_extensions:
                    raise ValidationError({
                        'file_path': f'Image assets must have one of these extensions: {valid_extensions}'
                    })
            elif self.asset_type == self.ASSET_TYPE_STYLESHEET:
                if file_ext not in ['.css', '.scss', '.sass']:
                    raise ValidationError({
                        'file_path': 'Stylesheet assets must have .css, .scss, or .sass extension'
                    })
            elif self.asset_type == self.ASSET_TYPE_SCRIPT:
                if file_ext not in ['.js', '.jsx', '.ts', '.tsx']:
                    raise ValidationError({
                        'file_path': 'Script assets must have .js, .jsx, .ts, or .tsx extension'
                    })

        # Validate file size limits
        max_file_size = 50 * 1024 * 1024  # 50MB
        if self.file_size > max_file_size:
            raise ValidationError({
                'file_size': f'File size cannot exceed {max_file_size / (1024*1024)}MB'
            })

        # Ensure template and version belong to the same template
        if self.template and self.version and self.template != self.version.template:
            raise ValidationError({
                'version': 'Template version must belong to the same template'
            })

    def save(self, *args, **kwargs):
        """Custom save method with validation and automatic field population"""
        # Auto-populate file_name from file_path if not provided
        if self.file_path and not self.file_name:
            self.file_name = os.path.basename(self.file_path)

        # Auto-generate CDN path if not provided
        if not self.cdn_path and self.version and self.file_path:
            self.cdn_path = f"{self.version.cdn_path}/{self.file_path}"

        # Auto-generate CDN URL if not provided
        if not self.cdn_url and self.cdn_path:
            self.cdn_url = f"https://cdn.huzilaz.com/{self.cdn_path}"

        # Ensure unique file path within template version
        if TemplateAsset.objects.filter(
            template=self.template,
            version=self.version,
            file_path=self.file_path
        ).exclude(pk=self.pk).exists():
            raise ValidationError(f"Asset with path '{self.file_path}' already exists in this template version")

        super().save(*args, **kwargs)

    def get_full_cdn_url(self):
        """Get full CDN URL for this asset with error handling"""
        try:
            if self.cdn_url:
                return self.cdn_url
            elif self.cdn_path:
                return f"https://cdn.huzilaz.com/{self.cdn_path}"
            else:
                logger.warning(f"Template asset {self.id} has no CDN path or URL configured")
                return ''
        except Exception as e:
            logger.error(f"Error generating CDN URL for template asset {self.id}: {e}")
            return ''

    def get_relative_path(self):
        """Get relative path within template with error handling"""
        try:
            return self.file_path
        except Exception as e:
            logger.error(f"Error getting relative path for template asset {self.id}: {e}")
            return ''

    def get_file_extension(self):
        """Get file extension with error handling"""
        try:
            return os.path.splitext(self.file_path)[1].lower() if self.file_path else ''
        except Exception as e:
            logger.error(f"Error getting file extension for template asset {self.id}: {e}")
            return ''

    def is_image(self):
        """Check if asset is an image with error handling"""
        try:
            return self.asset_type == self.ASSET_TYPE_IMAGE
        except Exception as e:
            logger.error(f"Error checking if asset {self.id} is image: {e}")
            return False

    def is_stylesheet(self):
        """Check if asset is a stylesheet with error handling"""
        try:
            return self.asset_type == self.ASSET_TYPE_STYLESHEET
        except Exception as e:
            logger.error(f"Error checking if asset {self.id} is stylesheet: {e}")
            return False

    def is_script(self):
        """Check if asset is a script with error handling"""
        try:
            return self.asset_type == self.ASSET_TYPE_SCRIPT
        except Exception as e:
            logger.error(f"Error checking if asset {self.id} is script: {e}")
            return False

    @property
    def formatted_file_size(self):
        """Get formatted file size (KB, MB, GB) with error handling"""
        try:
            if not self.file_size:
                return "0 B"

            size = self.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except Exception as e:
            logger.error(f"Error formatting file size for asset {self.id}: {e}")
            return "Unknown"

    def mark_as_deprecated(self):
        """Mark asset as deprecated with error handling"""
        try:
            self.status = self.STATUS_DEPRECATED
            self.save(update_fields=['status'])
            logger.info(f"Marked template asset {self.id} as deprecated")
        except Exception as e:
            logger.error(f"Error marking template asset {self.id} as deprecated: {e}")
            raise

    def mark_as_deleted(self):
        """Mark asset as deleted with error handling"""
        try:
            self.status = self.STATUS_DELETED
            self.save(update_fields=['status'])
            logger.info(f"Marked template asset {self.id} as deleted")
        except Exception as e:
            logger.error(f"Error marking template asset {self.id} as deleted: {e}")
            raise