from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging
import re
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


class TemplateVersion(models.Model):
    """
    Template version model for tracking different versions of templates.
    Supports semantic versioning and change tracking.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Version ID",
        help_text="Unique identifier for the template version"
    )

    # Version Status Choices
    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_DEPRECATED = 'deprecated'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_DEPRECATED, 'Deprecated'),
    ]

    # Core Relationships
    template = models.ForeignKey(
        'Template',
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name="Template",
        help_text="Parent template this version belongs to"
    )

    # Version Information
    version = models.CharField(
        max_length=20,
        verbose_name="Version",
        help_text="Semantic version (e.g., 1.0.0, 1.1.0)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        verbose_name="Status",
        help_text="Current status of this version"
    )

    # Change Information
    changelog = models.TextField(
        blank=True,
        verbose_name="Changelog",
        help_text="What changed in this version"
    )
    breaking_changes = models.BooleanField(
        default=False,
        verbose_name="Breaking Changes",
        help_text="Whether this version contains breaking changes"
    )

    # Technical Configuration
    cdn_path = models.CharField(
        max_length=500,
        verbose_name="CDN Path",
        help_text="CDN path for this specific version"
    )
    puck_config = models.JSONField(
        default=dict,
        verbose_name="Puck Configuration",
        help_text="Puck configuration for this version"
    )

    # Git Integration
    git_commit_hash = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Git Commit Hash",
        help_text="Git commit hash for this version"
    )
    git_tag = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Git Tag",
        help_text="Git tag for this version"
    )

    # Compatibility Information
    min_workspace_version = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Minimum Workspace Version",
        help_text="Minimum workspace system version required"
    )
    dependencies = models.JSONField(
        default=list,
        verbose_name="Dependencies",
        help_text="List of required dependencies/packages"
    )

    # Performance Metrics
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name="File Size",
        help_text="Total file size in bytes"
    )
    load_time = models.FloatField(
        default=0.0,
        verbose_name="Load Time",
        help_text="Average load time in seconds"
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_template_versions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deployed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'theme_template_versions'
        ordering = ['template', '-created_at']
        unique_together = ['template', 'version']
        indexes = [
            models.Index(fields=['template', 'version']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.template.name} v{self.version}"

    def clean(self):
        """Custom validation for template version model"""
        super().clean()

        # Validate semantic version format
        version_pattern = r'^\d+\.\d+\.\d+$'
        if not re.match(version_pattern, self.version):
            raise ValidationError({
                'version': 'Version must follow semantic versioning format (e.g., 1.0.0, 2.1.3)'
            })

        # Validate CDN path format
        # In production: must start with 'themes/'
        # In development: accept file:// paths for local testing
        if self.cdn_path and not (self.cdn_path.startswith('themes/') or self.cdn_path.startswith('file://')):
            raise ValidationError({
                'cdn_path': 'CDN path must start with "themes/" (production) or "file://" (development)'
            })

        # Validate git commit hash format if provided
        if self.git_commit_hash and not re.match(r'^[a-f0-9]{40}$', self.git_commit_hash):
            raise ValidationError({
                'git_commit_hash': 'Git commit hash must be a valid 40-character SHA-1 hash'
            })

    def save(self, *args, **kwargs):
        """Custom save method with validation and status handling"""
        # Set deployed_at when status changes to active
        if self.status == self.STATUS_ACTIVE and not self.deployed_at:
            from django.utils import timezone
            self.deployed_at = timezone.now()

        # Ensure version uniqueness
        if TemplateVersion.objects.filter(
            template=self.template,
            version=self.version
        ).exclude(pk=self.pk).exists():
            raise ValidationError(f"Version {self.version} already exists for template {self.template.name}")

        super().save(*args, **kwargs)

    @property
    def is_latest(self):
        """Check if this is the latest version of the template with error handling"""
        try:
            latest_version = TemplateVersion.objects.filter(
                template=self.template,
                status=self.STATUS_ACTIVE
            ).order_by('-created_at').first()
            return latest_version == self if latest_version else False
        except Exception as e:
            logger.error(f"Error checking if version {self.id} is latest: {e}")
            return False

    @property
    def major_version(self):
        """Extract major version number (e.g., '1' from '1.2.3') with error handling"""
        try:
            return int(self.version.split('.')[0])
        except (ValueError, IndexError) as e:
            logger.warning(f"Error extracting major version from {self.version}: {e}")
            return 0

    @property
    def minor_version(self):
        """Extract minor version number (e.g., '2' from '1.2.3') with error handling"""
        try:
            return int(self.version.split('.')[1])
        except (ValueError, IndexError) as e:
            logger.warning(f"Error extracting minor version from {self.version}: {e}")
            return 0

    @property
    def patch_version(self):
        """Extract patch version number (e.g., '3' from '1.2.3') with error handling"""
        try:
            return int(self.version.split('.')[2])
        except (ValueError, IndexError) as e:
            logger.warning(f"Error extracting patch version from {self.version}: {e}")
            return 0

    def get_cdn_url(self, file_path=''):
        """Get full CDN URL for this version's files with error handling"""
        try:
            if not self.cdn_path:
                logger.warning(f"Template version {self.id} has no CDN path configured")
                return ''
            base_url = f"https://cdn.huzilaz.com/{self.cdn_path}"
            if file_path:
                return f"{base_url}/{file_path}"
            return base_url
        except Exception as e:
            logger.error(f"Error generating CDN URL for template version {self.id}: {e}")
            return ''

    def get_download_url(self):
        """Get URL for downloading this version with error handling"""
        try:
            return self.get_cdn_url('template.zip')
        except Exception as e:
            logger.error(f"Error generating download URL for template version {self.id}: {e}")
            return ''

    def get_preview_url(self):
        """Get URL for previewing this version with error handling"""
        try:
            return self.get_cdn_url('preview.html')
        except Exception as e:
            logger.error(f"Error generating preview URL for template version {self.id}: {e}")
            return ''

    def can_update_from(self, previous_version):
        """
        Check if this version can be updated from a previous version.
        Returns True if no breaking changes or if major version hasn't changed.
        """
        try:
            if not previous_version:
                return True

            # If no breaking changes, always allow update
            if not self.breaking_changes:
                return True

            # If breaking changes, only allow if major version is same
            return self.major_version == previous_version.major_version
        except Exception as e:
            logger.error(f"Error checking update compatibility for version {self.id}: {e}")
            return False

    def get_update_type(self, previous_version):
        """
        Determine the type of update from previous version.
        Returns: 'major', 'minor', 'patch', or None if not applicable
        """
        try:
            if not previous_version:
                return None

            if self.major_version != previous_version.major_version:
                return 'major'
            elif self.minor_version != previous_version.minor_version:
                return 'minor'
            elif self.patch_version != previous_version.patch_version:
                return 'patch'

            return None
        except Exception as e:
            logger.error(f"Error determining update type for version {self.id}: {e}")
            return None