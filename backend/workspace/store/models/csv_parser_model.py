"""
Shopify-inspired CSV Parser Models

Core models for CSV import operations with minimal, production-focused features:
- CSVImportJob: Track import operations and progress
- CSVImportResult: Store validation results and errors
- CSVImportRow: Individual row processing with error tracking

Shopify Principles Applied:
- Simple, focused models
- Clear status tracking
- Comprehensive error handling
- Workspace scoping
- Audit trail
"""

from django.db import models
from workspace.core.models.base_models import TenantScopedModel


class CSVImportJob(TenantScopedModel):
    """
    Shopify-inspired CSV import job tracking

    Tracks the overall import operation with status, progress, and metadata
    Similar to Shopify's bulk import operations
    """

    # Status choices inspired by Shopify's bulk operations
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # Core job metadata
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()  # Size in bytes
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)

    # Shopify-style job metadata
    job_type = models.CharField(max_length=50, default='product_import')
    source = models.CharField(max_length=100, default='csv_upload')

    class Meta:
        db_table = 'store_csv_import_jobs'
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['workspace', 'created_at']),
            models.Index(fields=['status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} ({self.status})"

    @property
    def progress_percentage(self):
        """Calculate progress percentage like Shopify"""
        if self.total_rows == 0:
            return 0
        return int((self.processed_rows / self.total_rows) * 100)

    @property
    def is_completed(self):
        """Check if job is completed"""
        return self.status in ['completed', 'failed', 'cancelled']

    @property
    def duration_seconds(self):
        """Calculate job duration in seconds"""
        if not self.started_at:
            return 0

        end_time = self.completed_at or self.updated_at
        return (end_time - self.started_at).total_seconds()


class CSVImportRow(TenantScopedModel):
    """
    Shopify-inspired individual CSV row processing

    Tracks processing of each CSV row with validation results
    Similar to Shopify's row-level error tracking
    """

    # Row status inspired by Shopify
    ROW_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('skipped', 'Skipped'),
    ]

    # Core row data
    job = models.ForeignKey(
        CSVImportJob,
        on_delete=models.CASCADE,
        related_name='rows'
    )
    row_number = models.IntegerField()  # 1-based row number

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=ROW_STATUS_CHOICES,
        default='pending'
    )

    # Shopify-style error tracking
    error_message = models.TextField(blank=True)
    error_type = models.CharField(max_length=100, blank=True)

    # Original data for debugging
    raw_data = models.JSONField(default=dict)  # Original CSV row data

    # Processing results
    processed_data = models.JSONField(default=dict)  # Cleaned/validated data
    product_id = models.CharField(max_length=100, blank=True)  # Created product ID

    class Meta:
        db_table = 'store_csv_import_rows'
        indexes = [
            models.Index(fields=['job', 'row_number']),
            models.Index(fields=['job', 'status']),
        ]
        unique_together = ['job', 'row_number']

    def __str__(self):
        return f"Row {self.row_number} - {self.status}"


class CSVImportResult(TenantScopedModel):
    """
    Shopify-inspired CSV import summary results

    Stores final import results and summary statistics
    Similar to Shopify's import completion reports
    """

    job = models.OneToOneField(
        CSVImportJob,
        on_delete=models.CASCADE,
        related_name='result'
    )

    # Shopify-style summary statistics
    total_products_created = models.IntegerField(default=0)
    total_products_updated = models.IntegerField(default=0)
    total_products_skipped = models.IntegerField(default=0)
    total_products_failed = models.IntegerField(default=0)

    # Processing metrics
    processing_time_seconds = models.FloatField(default=0.0)
    average_row_time_ms = models.FloatField(default=0.0)

    # Error summary
    validation_errors = models.JSONField(default=list)  # List of validation errors
    system_errors = models.JSONField(default=list)     # List of system errors
    warnings = models.JSONField(default=list)          # List of warnings

    # Shopify-style result metadata
    result_summary = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    class Meta:
        db_table = 'store_csv_import_results'

    def __str__(self):
        return f"Results for {self.job.filename}"

    @property
    def success_rate(self):
        """Calculate success rate like Shopify"""
        total_processed = (
            self.total_products_created +
            self.total_products_updated +
            self.total_products_failed
        )
        if total_processed == 0:
            return 0
        successful = self.total_products_created + self.total_products_updated
        return int((successful / total_processed) * 100)

    @property
    def total_processed(self):
        """Total processed rows"""
        return (
            self.total_products_created +
            self.total_products_updated +
            self.total_products_failed +
            self.total_products_skipped
        )