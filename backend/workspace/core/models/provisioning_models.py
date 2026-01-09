import uuid
from django.db import models
from django.utils import timezone


class ProvisioningRecord(models.Model):
    """
    Tracks workspace provisioning lifecycle
    Created when workspace is created, updated as background tasks complete
    """
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='provisioning'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    # Retry tracking (Critical fix #5)
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of times provisioning has been retried"
    )
    max_retries = models.IntegerField(
        default=5,
        help_text="Maximum number of automatic retries allowed"
    )
    last_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last retry attempt"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_provisioning_records'
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Provisioning {self.workspace.name} - {self.status}"

    def mark_in_progress(self):
        """Mark provisioning as started"""
        self.status = 'in_progress'
        self.save(update_fields=['status', 'updated_at'])

    def mark_completed(self):
        """Mark provisioning as successfully completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def mark_failed(self, error_message):
        """Mark provisioning as failed with error details"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'completed_at', 'updated_at'])

    def can_retry(self):
        """
        Check if provisioning can be retried (Critical fix #5)
        Returns (can_retry: bool, reason: str)
        """
        if self.status not in ['failed']:
            return False, "Only failed provisioning can be retried"

        if self.retry_count >= self.max_retries:
            return False, f"Max retries ({self.max_retries}) exceeded"

        return True, "Retry allowed"

    def retry(self):
        """
        Reset status to queued for retry with backoff tracking (Critical fix #5)
        Raises ValueError if retry not allowed
        """
        can_retry, reason = self.can_retry()
        if not can_retry:
            raise ValueError(f"Cannot retry provisioning: {reason}")

        self.status = 'queued'
        self.error_message = None
        self.completed_at = None
        self.retry_count += 1
        self.last_retry_at = timezone.now()
        self.save(update_fields=[
            'status', 'error_message', 'completed_at', 'retry_count',
            'last_retry_at', 'updated_at'
        ])

    def get_retry_delay(self):
        """
        Calculate exponential backoff delay for next retry (Critical fix #5)
        Formula: min(base_delay * (2 ^ retry_count), max_delay)
        Returns delay in seconds
        """
        base_delay = 60  # 1 minute
        max_delay = 3600  # 1 hour
        delay = min(base_delay * (2 ** self.retry_count), max_delay)
        return delay

    def should_auto_retry(self):
        """
        Check if automatic retry should be triggered (Critical fix #5)
        Used by background tasks to decide whether to auto-retry
        """
        can_retry, _ = self.can_retry()
        return can_retry and self.retry_count < 3  # Auto-retry only first 3 attempts


class ProvisioningLog(models.Model):
    """
    Detailed log of each provisioning step
    Multiple logs per provisioning record (one per task/step)
    """
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provisioning = models.ForeignKey(
        ProvisioningRecord,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    step = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    metadata = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    attempt = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_provisioning_logs'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['provisioning', 'timestamp']),
            models.Index(fields=['step', 'status']),
        ]

    def __str__(self):
        return f"{self.step} - {self.status} (attempt {self.attempt})"

    @classmethod
    def log_step_started(cls, provisioning, step, metadata=None):
        """Log that a provisioning step has started"""
        return cls.objects.create(
            provisioning=provisioning,
            step=step,
            status='started',
            metadata=metadata or {}
        )

    @classmethod
    def log_step_completed(cls, provisioning, step, metadata=None):
        """Log that a provisioning step completed successfully"""
        return cls.objects.create(
            provisioning=provisioning,
            step=step,
            status='completed',
            metadata=metadata or {}
        )

    @classmethod
    def log_step_failed(cls, provisioning, step, error, attempt=None, metadata=None):
        """Log that a provisioning step failed"""
        # Auto-calculate attempt number if not provided
        if attempt is None:
            # Find the highest attempt number for this provisioning and step
            last_attempt = cls.objects.filter(
                provisioning=provisioning,
                step=step,
                status='failed'
            ).order_by('-attempt').values_list('attempt', flat=True).first()
            attempt = (last_attempt or 0) + 1

        return cls.objects.create(
            provisioning=provisioning,
            step=step,
            status='failed',
            error=str(error),
            attempt=attempt,
            metadata=metadata or {}
        )


class DeProvisioningRecord(models.Model):
    """
    Tracks workspace deprovisioning lifecycle (mirrors ProvisioningRecord)
    Created when workspace is deleted, tracks cleanup tasks until completion
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),  # User restored workspace during grace period
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='deprovisioning'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Timing
    scheduled_for = models.DateTimeField(help_text="When deprovisioning should execute (after grace period)")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Error handling
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)

    # Cleanup tracking
    cleanup_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Track what was cleaned up: {s3_files: bool, dns_records: bool, etc.}"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_deprovisioning_records'
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['scheduled_for']),  # For Celery beat to find due tasks
        ]

    def __str__(self):
        return f"Deprovisioning {self.workspace.name} - {self.status}"

    def mark_in_progress(self):
        """Mark deprovisioning as started"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])

    def mark_completed(self, cleanup_summary=None):
        """Mark deprovisioning as successfully completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if cleanup_summary:
            self.cleanup_metadata.update(cleanup_summary)
        self.save(update_fields=['status', 'completed_at', 'cleanup_metadata', 'updated_at'])

    def mark_failed(self, error_message):
        """Mark deprovisioning as failed with error details"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])

    def mark_cancelled(self):
        """Mark deprovisioning as cancelled (workspace restored)"""
        self.status = 'cancelled'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def retry(self):
        """Reset status to scheduled for retry"""
        self.status = 'scheduled'
        self.error_message = None
        self.save(update_fields=['status', 'error_message', 'updated_at'])

    @property
    def is_overdue(self):
        """Check if deprovisioning is overdue"""
        return self.status == 'scheduled' and timezone.now() >= self.scheduled_for

    @property
    def days_until_scheduled(self):
        """Calculate days until scheduled deprovisioning"""
        if self.status != 'scheduled':
            return None
        delta = self.scheduled_for - timezone.now()
        return max(0, delta.days)


class DeProvisioningLog(models.Model):
    """
    Detailed log of each deprovisioning step (mirrors ProvisioningLog)
    Multiple logs per deprovisioning record (one per cleanup task/step)
    """
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),  # Resource already cleaned or not found
        ('retrying', 'Retrying'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deprovisioning = models.ForeignKey(
        DeProvisioningRecord,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    step = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    metadata = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    attempt = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_deprovisioning_logs'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['deprovisioning', 'timestamp']),
            models.Index(fields=['step', 'status']),
        ]

    def __str__(self):
        return f"{self.step} - {self.status} (attempt {self.attempt})"

    @classmethod
    def log_step_started(cls, deprovisioning, step, metadata=None):
        """Log that a deprovisioning step has started"""
        return cls.objects.create(
            deprovisioning=deprovisioning,
            step=step,
            status='started',
            metadata=metadata or {}
        )

    @classmethod
    def log_step_completed(cls, deprovisioning, step, metadata=None):
        """Log that a deprovisioning step completed successfully"""
        return cls.objects.create(
            deprovisioning=deprovisioning,
            step=step,
            status='completed',
            metadata=metadata or {}
        )

    @classmethod
    def log_step_failed(cls, deprovisioning, step, error, attempt=None, metadata=None):
        """Log that a deprovisioning step failed"""
        # Auto-calculate attempt number if not provided
        if attempt is None:
            # Find the highest attempt number for this deprovisioning and step
            last_attempt = cls.objects.filter(
                deprovisioning=deprovisioning,
                step=step,
                status='failed'
            ).order_by('-attempt').values_list('attempt', flat=True).first()
            attempt = (last_attempt or 0) + 1

        return cls.objects.create(
            deprovisioning=deprovisioning,
            step=step,
            status='failed',
            error=str(error),
            attempt=attempt,
            metadata=metadata or {}
        )

    @classmethod
    def log_step_skipped(cls, deprovisioning, step, reason, metadata=None):
        """Log that a deprovisioning step was skipped"""
        metadata = metadata or {}
        metadata['skip_reason'] = reason
        return cls.objects.create(
            deprovisioning=deprovisioning,
            step=step,
            status='skipped',
            metadata=metadata
        )
