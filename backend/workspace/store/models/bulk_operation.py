from django.db import models
from django.conf import settings
from workspace.core.models.workspace_model import Workspace
import uuid

class BulkOperation(models.Model):
    """
    Shopify-style bulk operation tracking

    Tracks core bulk operations only:
    - Bulk publish/unpublish products
    - Bulk update prices
    - Bulk delete products
    - Bulk update inventory

    No file import tracking - that's handled by separate models
    """

    STATUS_CHOICES = (
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('processing', 'Processing'),
    )

    OPERATION_TYPES = (
        ('bulk_publish', 'Bulk Publish Products'),
        ('bulk_unpublish', 'Bulk Unpublish Products'),
        ('bulk_price_update', 'Bulk Price Update'),
        ('bulk_delete', 'Bulk Delete Products'),
        ('bulk_inventory_update', 'Bulk Inventory Update'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='bulk_operations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bulk_operations')

    # Operation info
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')

    # Results
    total_items = models.PositiveIntegerField()  # Total items to process
    processed_items = models.PositiveIntegerField(default=0)  # Successfully processed

    # Error tracking
    error_message = models.TextField(blank=True)  # If failed, why?

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.status} ({self.processed_items}/{self.total_items})"

    @property
    def success_rate(self):
        if self.total_items == 0:
            return 0
        return (self.processed_items / self.total_items) * 100