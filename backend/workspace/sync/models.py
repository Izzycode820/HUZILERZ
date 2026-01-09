"""
Workspace Sync Models
Track synchronization events, webhook deliveries, and data consistency
"""
from django.db import models
from django.utils import timezone
from workspace.core.models.base_models import TenantScopedModel
import uuid


class SyncEvent(TenantScopedModel):
    """
    Track workspace data synchronization events
    Logs all data changes that need to be synced to deployed sites
    """

    EVENT_TYPES = [
        # Store events
        ('product.created', 'Product Created'),
        ('product.updated', 'Product Updated'),
        ('product.deleted', 'Product Deleted'),
        ('order.created', 'Order Created'),
        ('order.updated', 'Order Updated'),

        # Blog events
        ('post.created', 'Post Created'),
        ('post.updated', 'Post Updated'),
        ('post.published', 'Post Published'),
        ('post.deleted', 'Post Deleted'),

        # Services events
        ('service.created', 'Service Created'),
        ('service.updated', 'Service Updated'),
        ('booking.created', 'Booking Created'),
        ('booking.updated', 'Booking Updated'),

        # Workspace events
        ('workspace.settings_updated', 'Workspace Settings Updated'),
        ('workspace.branding_updated', 'Workspace Branding Updated'),
    ]

    SYNC_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]

    # Event identification
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)

    # Event data
    entity_type = models.CharField(max_length=50, help_text="Model name (Product, Post, etc.)")
    entity_id = models.CharField(max_length=100, help_text="ID of the changed entity")
    event_data = models.JSONField(help_text="Event payload data")
    changed_fields = models.JSONField(default=list, help_text="List of changed field names")

    # Sync tracking
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS, default='pending')
    sites_to_sync = models.JSONField(default=list, help_text="List of site IDs to sync")
    sites_synced = models.JSONField(default=list, help_text="List of successfully synced site IDs")
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=8)  # Shopify pattern

    # Metadata
    triggered_by_user_id = models.CharField(max_length=100, blank=True, help_text="User who triggered the change")
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        app_label = 'workspace_sync'
        db_table = 'workspace_sync_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'sync_status', '-created_at']),
            models.Index(fields=['event_type', 'sync_status']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['event_id']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.entity_type}:{self.entity_id}"

    def mark_processing(self):
        """Mark event as currently being processed"""
        self.sync_status = 'processing'
        self.save(update_fields=['sync_status'])

    def mark_completed(self):
        """Mark event as successfully completed"""
        self.sync_status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['sync_status', 'processed_at'])

    def mark_failed(self, error_message: str):
        """Mark event as failed with error message"""
        self.sync_status = 'failed'
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save(update_fields=['sync_status', 'error_message', 'processed_at'])

    def increment_retry(self):
        """Increment retry counter and update status"""
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.sync_status = 'failed'
            self.error_message = f"Max retries ({self.max_retries}) exceeded"
        else:
            self.sync_status = 'retrying'

        self.save(update_fields=['retry_count', 'sync_status', 'error_message'])

    @property
    def can_retry(self):
        """Check if event can be retried"""
        return self.retry_count < self.max_retries and self.sync_status in ['failed', 'retrying']

    def add_synced_site(self, site_id: str):
        """Add site to successfully synced list"""
        if site_id not in self.sites_synced:
            self.sites_synced.append(site_id)
            self.save(update_fields=['sites_synced'])

    @property
    def is_fully_synced(self):
        """Check if all target sites have been synced"""
        return set(self.sites_to_sync) <= set(self.sites_synced)


class WebhookDelivery(models.Model):
    """
    Track individual webhook delivery attempts
    Implements Shopify's 8-retry pattern with exponential backoff
    """

    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
        ('retry_scheduled', 'Retry Scheduled'),
    ]

    # Delivery identification
    delivery_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    sync_event = models.ForeignKey(SyncEvent, on_delete=models.CASCADE, related_name='webhook_deliveries')

    # Target information
    target_site_id = models.CharField(max_length=100, help_text="Target deployed site ID")
    target_url = models.URLField(help_text="Webhook endpoint URL")

    # Delivery tracking
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    attempt_number = models.PositiveIntegerField(default=1)
    scheduled_at = models.DateTimeField(help_text="When delivery is scheduled")
    sent_at = models.DateTimeField(null=True, blank=True)
    response_received_at = models.DateTimeField(null=True, blank=True)

    # Response data
    http_status_code = models.PositiveIntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    # Timing metrics
    request_duration_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Request duration in milliseconds")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_sync'
        db_table = 'workspace_webhook_deliveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sync_event', 'attempt_number']),
            models.Index(fields=['delivery_status', 'scheduled_at']),
            models.Index(fields=['target_site_id', '-created_at']),
            models.Index(fields=['delivery_id']),
        ]

    def __str__(self):
        return f"Webhook delivery {self.delivery_id} - Attempt {self.attempt_number}"

    def mark_sent(self):
        """Mark webhook as sent"""
        self.delivery_status = 'sending'
        self.sent_at = timezone.now()
        self.save(update_fields=['delivery_status', 'sent_at'])

    def mark_delivered(self, status_code: int, response_body: str = '', duration_ms: int = None):
        """Mark webhook as successfully delivered"""
        self.delivery_status = 'delivered'
        self.http_status_code = status_code
        self.response_body = response_body
        self.response_received_at = timezone.now()
        if duration_ms is not None:
            self.request_duration_ms = duration_ms

        self.save(update_fields=[
            'delivery_status', 'http_status_code', 'response_body',
            'response_received_at', 'request_duration_ms'
        ])

    def mark_failed(self, error_message: str, status_code: int = None, duration_ms: int = None):
        """Mark webhook delivery as failed"""
        self.delivery_status = 'failed'
        self.error_message = error_message
        self.response_received_at = timezone.now()

        if status_code is not None:
            self.http_status_code = status_code
        if duration_ms is not None:
            self.request_duration_ms = duration_ms

        self.save(update_fields=[
            'delivery_status', 'error_message', 'response_received_at',
            'http_status_code', 'request_duration_ms'
        ])

    def schedule_retry(self, retry_delay_seconds: int):
        """Schedule webhook for retry with exponential backoff"""
        from datetime import timedelta

        self.delivery_status = 'retry_scheduled'
        self.scheduled_at = timezone.now() + timedelta(seconds=retry_delay_seconds)
        self.attempt_number += 1
        self.save(update_fields=['delivery_status', 'scheduled_at', 'attempt_number'])

    @property
    def is_successful(self):
        """Check if delivery was successful"""
        return (
            self.delivery_status == 'delivered' and
            self.http_status_code and
            200 <= self.http_status_code < 300
        )


class PollingState(models.Model):
    """
    Track polling state for 1-minute backup sync
    Ensures we don't miss changes when webhooks fail
    """

    workspace = models.OneToOneField(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='polling_state'
    )

    # Polling tracking
    last_poll_at = models.DateTimeField(help_text="Last successful poll time")
    last_change_detected_at = models.DateTimeField(null=True, blank=True, help_text="Last time changes were detected")
    next_poll_at = models.DateTimeField(help_text="Next scheduled poll time")

    # Status tracking
    is_polling_active = models.BooleanField(default=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    max_failures = models.PositiveIntegerField(default=10)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_sync'
        db_table = 'workspace_polling_states'
        indexes = [
            models.Index(fields=['next_poll_at', 'is_polling_active']),
            models.Index(fields=['workspace']),
        ]

    def __str__(self):
        return f"Polling state for {self.workspace.name}"

    def schedule_next_poll(self, minutes_from_now: int = 1):
        """Schedule next polling check"""
        from datetime import timedelta

        self.next_poll_at = timezone.now() + timedelta(minutes=minutes_from_now)
        self.save(update_fields=['next_poll_at'])

    def mark_poll_completed(self, changes_detected: bool = False):
        """Mark polling cycle as completed"""
        now = timezone.now()
        self.last_poll_at = now
        self.consecutive_failures = 0  # Reset failure count on success

        if changes_detected:
            self.last_change_detected_at = now

        # Schedule next poll
        self.schedule_next_poll()

        self.save(update_fields=[
            'last_poll_at', 'consecutive_failures',
            'last_change_detected_at', 'updated_at'
        ])

    def mark_poll_failed(self):
        """Mark polling cycle as failed"""
        self.consecutive_failures += 1

        if self.consecutive_failures >= self.max_failures:
            self.is_polling_active = False

        # Schedule retry with backoff
        retry_minutes = min(self.consecutive_failures, 30)  # Max 30 minute delay
        self.schedule_next_poll(retry_minutes)

        self.save(update_fields=[
            'consecutive_failures', 'is_polling_active', 'updated_at'
        ])

    @property
    def is_healthy(self):
        """Check if polling is healthy"""
        return (
            self.is_polling_active and
            self.consecutive_failures < 5 and
            (timezone.now() - self.last_poll_at).total_seconds() < 300  # 5 minutes
        )


class SyncMetrics(models.Model):
    """
    Track sync performance metrics for monitoring and optimization
    """

    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='sync_metrics'
    )

    # Time period
    date = models.DateField(help_text="Metrics date")

    # Event metrics
    events_generated = models.PositiveIntegerField(default=0)
    events_processed = models.PositiveIntegerField(default=0)
    events_failed = models.PositiveIntegerField(default=0)

    # Webhook metrics
    webhooks_sent = models.PositiveIntegerField(default=0)
    webhooks_delivered = models.PositiveIntegerField(default=0)
    webhooks_failed = models.PositiveIntegerField(default=0)

    # Performance metrics
    avg_delivery_time_ms = models.PositiveIntegerField(default=0)
    max_delivery_time_ms = models.PositiveIntegerField(default=0)

    # Polling metrics
    polls_completed = models.PositiveIntegerField(default=0)
    polls_with_changes = models.PositiveIntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_sync'
        db_table = 'workspace_sync_metrics'
        unique_together = ['workspace', 'date']
        indexes = [
            models.Index(fields=['workspace', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Sync metrics for {self.workspace.name} on {self.date}"

    @property
    def webhook_success_rate(self):
        """Calculate webhook delivery success rate"""
        if self.webhooks_sent == 0:
            return 100.0
        return (self.webhooks_delivered / self.webhooks_sent) * 100

    @property
    def event_success_rate(self):
        """Calculate event processing success rate"""
        if self.events_generated == 0:
            return 100.0
        return (self.events_processed / self.events_generated) * 100