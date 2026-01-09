from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class UpdateNotification(models.Model):
    """
    Update notification model for managing user update prompts
    Follows Google Play Store model: new users get latest, existing users opt-in
    """

    # Notification Status Choices
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_READ = 'read'
    STATUS_DISMISSED = 'dismissed'
    STATUS_ACCEPTED = 'accepted'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_READ, 'Read'),
        (STATUS_DISMISSED, 'Dismissed'),
        (STATUS_ACCEPTED, 'Accepted'),
    ]

    # Update Type Choices
    UPDATE_TYPE_MINOR = 'minor'
    UPDATE_TYPE_MAJOR = 'major'
    UPDATE_TYPE_SECURITY = 'security'
    UPDATE_TYPE_BREAKING = 'breaking'

    UPDATE_TYPE_CHOICES = [
        (UPDATE_TYPE_MINOR, 'Minor Update'),
        (UPDATE_TYPE_MAJOR, 'Major Update'),
        (UPDATE_TYPE_SECURITY, 'Security Update'),
        (UPDATE_TYPE_BREAKING, 'Breaking Change'),
    ]

    # Core Relationships
    template = models.ForeignKey(
        'Template',
        on_delete=models.CASCADE,
        related_name='update_notifications',
        verbose_name="Template",
        help_text="Template that has an available update"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='update_notifications',
        verbose_name="User",
        help_text="User who should receive the update notification"
    )
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='update_notifications',
        verbose_name="Workspace",
        help_text="Workspace where the template is used"
    )

    # Version Information
    current_version = models.ForeignKey(
        'TemplateVersion',
        on_delete=models.CASCADE,
        related_name='current_notifications',
        verbose_name="Current Version",
        help_text="Version currently being used"
    )
    new_version = models.ForeignKey(
        'TemplateVersion',
        on_delete=models.CASCADE,
        related_name='new_notifications',
        verbose_name="New Version",
        help_text="New version available for update"
    )

    # Notification Details
    update_type = models.CharField(
        max_length=20,
        choices=UPDATE_TYPE_CHOICES,
        default=UPDATE_TYPE_MINOR,
        db_index=True,
        verbose_name="Update Type",
        help_text="Type of update (minor, major, security, breaking)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name="Status",
        help_text="Current status of the notification"
    )

    # Update Information
    changelog = models.TextField(
        blank=True,
        verbose_name="Changelog",
        help_text="What's new in this update"
    )
    breaking_changes = models.TextField(
        blank=True,
        verbose_name="Breaking Changes",
        help_text="List of breaking changes that may affect customizations"
    )
    estimated_update_time = models.PositiveIntegerField(
        default=5,
        verbose_name="Estimated Update Time",
        help_text="Estimated time to complete update in minutes"
    )
    customization_preservation_score = models.PositiveSmallIntegerField(
        default=100,
        verbose_name="Customization Preservation Score",
        help_text="Percentage of customizations expected to be preserved (0-100)"
    )

    # Notification Tracking
    notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Notification Sent At",
        help_text="When the notification was sent to the user"
    )
    first_seen_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="First Seen At",
        help_text="When the user first saw the notification"
    )
    dismissed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dismissed At",
        help_text="When the user dismissed the notification"
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Accepted At",
        help_text="When the user accepted the update"
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    class Meta:
        db_table = 'theme_update_notifications'
        ordering = ['-created_at']
        unique_together = ['template', 'user', 'workspace', 'new_version']
        indexes = [
            models.Index(fields=['template', 'user', 'status']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['update_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Update Notification"
        verbose_name_plural = "Update Notifications"

    def __str__(self):
        return f"Update for {self.template.name} - {self.user.username}"

    def clean(self):
        """Custom validation for the update notification model"""
        super().clean()

        # Ensure current and new versions are different
        if self.current_version == self.new_version:
            raise ValidationError({
                'new_version': 'New version must be different from current version'
            })

        # Ensure new version is newer than current version
        if self.new_version.created_at <= self.current_version.created_at:
            raise ValidationError({
                'new_version': 'New version must be newer than current version'
            })

        # Validate customization preservation score
        if not 0 <= self.customization_preservation_score <= 100:
            raise ValidationError({
                'customization_preservation_score': 'Customization preservation score must be between 0 and 100'
            })

    def save(self, *args, **kwargs):
        """Custom save method with validation"""
        self.clean()
        super().save(*args, **kwargs)

    def mark_as_sent(self):
        """Mark notification as sent with error handling"""
        try:
            self.status = self.STATUS_SENT
            self.notification_sent_at = timezone.now()
            self.save(update_fields=['status', 'notification_sent_at'])
            logger.info(f"Marked update notification {self.id} as sent")
        except Exception as e:
            logger.error(f"Error marking update notification {self.id} as sent: {e}")
            raise

    def mark_as_read(self):
        """Mark notification as read with error handling"""
        try:
            self.status = self.STATUS_READ
            if not self.first_seen_at:
                self.first_seen_at = timezone.now()
            self.save(update_fields=['status', 'first_seen_at'])
            logger.info(f"Marked update notification {self.id} as read")
        except Exception as e:
            logger.error(f"Error marking update notification {self.id} as read: {e}")
            raise

    def dismiss(self):
        """Dismiss notification with error handling"""
        try:
            self.status = self.STATUS_DISMISSED
            self.dismissed_at = timezone.now()
            self.save(update_fields=['status', 'dismissed_at'])
            logger.info(f"Dismissed update notification {self.id}")
        except Exception as e:
            logger.error(f"Error dismissing update notification {self.id}: {e}")
            raise

    def accept(self):
        """Accept update notification with error handling"""
        try:
            self.status = self.STATUS_ACCEPTED
            self.accepted_at = timezone.now()
            self.save(update_fields=['status', 'accepted_at'])
            logger.info(f"Accepted update notification {self.id}")
        except Exception as e:
            logger.error(f"Error accepting update notification {self.id}: {e}")
            raise

    @property
    def is_actionable(self):
        """Check if notification can be acted upon with error handling"""
        try:
            return self.status in [self.STATUS_PENDING, self.STATUS_SENT, self.STATUS_READ]
        except Exception as e:
            logger.error(f"Error checking if notification {self.id} is actionable: {e}")
            return False

    @property
    def days_since_notification(self):
        """Get days since notification was sent with error handling"""
        try:
            if not self.notification_sent_at:
                return 0
            return (timezone.now() - self.notification_sent_at).days
        except Exception as e:
            logger.error(f"Error calculating days since notification {self.id}: {e}")
            return 0


class SyncLog(models.Model):
    """
    Sync log model for tracking Git-to-CDN sync operations
    """

    # Sync Status Choices
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # Sync Type Choices
    SYNC_TYPE_AUTOMATIC = 'automatic'
    SYNC_TYPE_MANUAL = 'manual'
    SYNC_TYPE_ROLLBACK = 'rollback'
    SYNC_TYPE_EMERGENCY = 'emergency'

    SYNC_TYPE_CHOICES = [
        (SYNC_TYPE_AUTOMATIC, 'Automatic'),
        (SYNC_TYPE_MANUAL, 'Manual'),
        (SYNC_TYPE_ROLLBACK, 'Rollback'),
        (SYNC_TYPE_EMERGENCY, 'Emergency'),
    ]

    # Core Information
    template = models.ForeignKey(
        'Template',
        on_delete=models.CASCADE,
        related_name='sync_logs',
        verbose_name="Template",
        help_text="Template being synced"
    )
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_syncs',
        verbose_name="Triggered By",
        help_text="User who triggered the sync (if manual)"
    )

    # Sync Details
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        default=SYNC_TYPE_AUTOMATIC,
        db_index=True,
        verbose_name="Sync Type",
        help_text="Type of sync operation"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name="Status",
        help_text="Current status of the sync operation"
    )

    # Version Information
    source_version = models.CharField(
        max_length=100,
        verbose_name="Source Version",
        help_text="Git commit hash or tag being synced"
    )
    target_version = models.CharField(
        max_length=100,
        verbose_name="Target Version",
        help_text="Version being deployed to CDN"
    )

    # Sync Progress
    files_processed = models.PositiveIntegerField(
        default=0,
        verbose_name="Files Processed",
        help_text="Number of files processed during sync"
    )
    total_files = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Files",
        help_text="Total number of files to process"
    )
    progress_percentage = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Progress Percentage",
        help_text="Sync progress percentage (0-100)"
    )

    # Sync Results
    cdn_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="CDN Path",
        help_text="Final CDN path where files were deployed"
    )
    git_commit_hash = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Git Commit Hash",
        help_text="Git commit hash that was synced"
    )
    git_tag = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Git Tag",
        help_text="Git tag that was synced"
    )

    # Error Information
    error_message = models.TextField(
        blank=True,
        verbose_name="Error Message",
        help_text="Error message if sync failed"
    )
    error_stack_trace = models.TextField(
        blank=True,
        verbose_name="Error Stack Trace",
        help_text="Full stack trace if sync failed"
    )

    # Performance Metrics
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Start Time",
        help_text="When the sync operation started"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="End Time",
        help_text="When the sync operation ended"
    )
    duration_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="Duration Seconds",
        help_text="Total duration of sync in seconds"
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    class Meta:
        db_table = 'theme_sync_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template', 'status']),
            models.Index(fields=['sync_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"

    def __str__(self):
        return f"Sync for {self.template.name} - {self.source_version} → {self.target_version}"

    def clean(self):
        """Custom validation for the sync log model"""
        super().clean()

        # Validate progress percentage
        if not 0 <= self.progress_percentage <= 100:
            raise ValidationError({
                'progress_percentage': 'Progress percentage must be between 0 and 100'
            })

        # Validate files processed doesn't exceed total files
        if self.files_processed > self.total_files:
            raise ValidationError({
                'files_processed': 'Files processed cannot exceed total files'
            })

    def save(self, *args, **kwargs):
        """Custom save method with validation and progress calculation"""
        self.clean()

        # Calculate progress percentage
        if self.total_files > 0:
            self.progress_percentage = int((self.files_processed / self.total_files) * 100)

        # Calculate duration if both start and end times are set
        if self.start_time and self.end_time:
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())

        super().save(*args, **kwargs)

    def start_sync(self):
        """Start sync operation with error handling"""
        try:
            self.status = self.STATUS_RUNNING
            self.start_time = timezone.now()
            self.save(update_fields=['status', 'start_time'])
            logger.info(f"Started sync operation {self.id}")
        except Exception as e:
            logger.error(f"Error starting sync operation {self.id}: {e}")
            raise

    def complete_sync(self, cdn_path=None):
        """Complete sync operation with error handling"""
        try:
            self.status = self.STATUS_COMPLETED
            self.end_time = timezone.now()
            if cdn_path:
                self.cdn_path = cdn_path
            self.save(update_fields=['status', 'end_time', 'cdn_path'])
            logger.info(f"Completed sync operation {self.id}")
        except Exception as e:
            logger.error(f"Error completing sync operation {self.id}: {e}")
            raise

    def fail_sync(self, error_message, stack_trace=None):
        """Mark sync as failed with error handling"""
        try:
            self.status = self.STATUS_FAILED
            self.end_time = timezone.now()
            self.error_message = error_message
            if stack_trace:
                self.error_stack_trace = stack_trace
            self.save(update_fields=['status', 'end_time', 'error_message', 'error_stack_trace'])
            logger.error(f"Sync operation {self.id} failed: {error_message}")
        except Exception as e:
            logger.error(f"Error marking sync operation {self.id} as failed: {e}")
            raise

    def update_progress(self, files_processed, total_files=None):
        """Update sync progress with error handling"""
        try:
            self.files_processed = files_processed
            if total_files:
                self.total_files = total_files
            self.save(update_fields=['files_processed', 'total_files', 'progress_percentage'])
        except Exception as e:
            logger.error(f"Error updating progress for sync operation {self.id}: {e}")
            raise

    @property
    def is_completed(self):
        """Check if sync is completed with error handling"""
        try:
            return self.status == self.STATUS_COMPLETED
        except Exception as e:
            logger.error(f"Error checking if sync {self.id} is completed: {e}")
            return False

    @property
    def is_failed(self):
        """Check if sync failed with error handling"""
        try:
            return self.status == self.STATUS_FAILED
        except Exception as e:
            logger.error(f"Error checking if sync {self.id} failed: {e}")
            return False

    @property
    def is_running(self):
        """Check if sync is running with error handling"""
        try:
            return self.status == self.STATUS_RUNNING
        except Exception as e:
            logger.error(f"Error checking if sync {self.id} is running: {e}")
            return False