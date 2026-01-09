# Recently Viewed Model - Customer product view tracking
# Optimized for Cameroon market with phone-first approach

from django.db import models
from workspace.core.models.base_models import BaseWorkspaceContentModel
from workspace.store.models import Product
from workspace.core.models.customer_model import Customer
from django.utils import timezone


class RecentlyViewed(BaseWorkspaceContentModel):
    """
    Track recently viewed products by customers

    Performance: Optimized view tracking with TTL
    Scalability: Efficient view history management
    Reliability: Consistent view tracking
    Security: Customer-specific view history

    Cameroon Market Optimizations:
    - Phone-based customer tracking
    - Mobile-friendly view history
    - Local product view patterns
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='recently_viewed',
        help_text="Customer who viewed the product"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='recently_viewed_by',
        help_text="Product that was viewed"
    )

    viewed_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the product was viewed"
    )

    view_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of times viewed in this session"
    )

    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Browser session identifier"
    )

    class Meta:
        app_label = 'workspace_storefront'
        db_table = 'storefront_recently_viewed'
        unique_together = ['workspace', 'customer', 'product']
        indexes = [
            models.Index(fields=['workspace', 'customer', '-viewed_at']),
            models.Index(fields=['workspace', 'product', '-viewed_at']),
            models.Index(fields=['workspace', 'viewed_at']),
        ]
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.customer.name} viewed {self.product.name}"

    def save(self, *args, **kwargs):
        # Update view count if record exists
        if self.pk:
            self.view_count += 1
        super().save(*args, **kwargs)

    @property
    def is_recent(self):
        """Check if view is recent (within 30 days)"""
        return (timezone.now() - self.viewed_at).days < 30

    @classmethod
    def cleanup_old_views(cls, days_old: int = 30):
        """Clean up views older than specified days"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        deleted_count, _ = cls.objects.filter(viewed_at__lt=cutoff_date).delete()
        return deleted_count