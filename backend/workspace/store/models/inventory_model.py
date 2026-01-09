# Inventory Model - Shopify-Style Design
# Simple inventory tracking per variant/location like Shopify

from django.db import models
from django.core.validators import MinValueValidator
from workspace.core.models.base_models import TenantScopedModel


class Inventory(TenantScopedModel):
    """
    Shopify-style inventory model
    Simple stock tracking per variant/location combination

    Shopify Design Principles:
    - Simple: Only essential fields for stock tracking
    - Fast: Minimal overhead, optimized queries
    - Reliable: Atomic operations for stock adjustments
    - Scalable: Works for small to large catalogs
    """

    # CORE RELATIONSHIPS
    variant = models.ForeignKey(
        'workspace_store.ProductVariant',
        on_delete=models.CASCADE,
        related_name='inventory',
        db_index=True,
        help_text="Product variant for this inventory entry"
    )
    location = models.ForeignKey(
        'workspace_store.Location',
        on_delete=models.CASCADE,
        related_name='inventory',
        db_index=True,
        help_text="Location where inventory is stored"
    )

    # STOCK QUANTITY (Core Shopify field)
    quantity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Available stock quantity at this location (deprecated, use onhand/available)"
    )

    # INVENTORY TRACKING FIELDS (Shopify-style)
    onhand = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Total stock on hand (committed inventory)"
    )

    available = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Stock available for sale"
    )

    # CONDITION TRACKING
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('refurbished', 'Refurbished'),
        ('second_hand', 'Second Hand'),
        ('used_like_new', 'Used - Like New'),
        ('used_good', 'Used - Good'),
        ('used_acceptable', 'Used - Acceptable'),
    ]

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        null=True,
        blank=True,
        help_text="Condition of inventory items"
    )

    # INVENTORY STATUS (Core Shopify field)
    is_available = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether inventory is available for sale"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_inventory'
        unique_together = ['variant', 'location']  # One inventory entry per variant per location
        indexes = [
            models.Index(fields=['workspace', 'location', 'is_available']),
            models.Index(fields=['workspace', 'variant', 'is_available']),
            models.Index(fields=['workspace', 'quantity']),
            models.Index(fields=['variant', 'location', 'quantity']),
        ]
        ordering = ['location', 'variant']

    def __str__(self):
        return f"{self.variant} at {self.location} - {self.quantity} units"

    def save(self, *args, **kwargs):
        # Shopify-style: Update availability based on quantity
        self.is_available = self.quantity > 0
        super().save(*args, **kwargs)

    # SIMPLE BUSINESS LOGIC (Shopify-style)
    @property
    def is_low_stock(self):
        """Check if inventory is below location threshold"""
        threshold = getattr(self.location, 'low_stock_threshold', 5)
        return self.quantity > 0 and self.quantity <= threshold

    @property
    def stock_status(self):
        """Shopify-style: Simple stock status"""
        if self.quantity == 0:
            return "out_of_stock"
        elif self.is_low_stock:
            return "low_stock"
        else:
            return "in_stock"

    # SIMPLE STOCK OPERATIONS (Shopify-style)
    def adjust_stock(self, quantity):
        """
        Shopify-style: Simple stock adjustment
        Positive quantity = increase, Negative quantity = decrease
        """
        from django.db import transaction
        from django.db.models import F

        try:
            with transaction.atomic():
                # Atomic update to prevent race conditions
                updated = Inventory.objects.filter(
                    id=self.id,
                    quantity__gte=-quantity if quantity < 0 else 0
                ).update(quantity=F('quantity') + quantity)

                if updated:
                    self.refresh_from_db()
                    return True
                return False

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Stock adjustment failed for inventory {self.id}: {e}")
            return False

    def set_quantity(self, new_quantity):
        """
        Shopify-style: Set specific quantity
        """
        from django.db import transaction

        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")

        try:
            with transaction.atomic():
                updated = Inventory.objects.filter(id=self.id).update(quantity=new_quantity)

                if updated:
                    self.refresh_from_db()
                    return True
                return False

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Stock set failed for inventory {self.id}: {e}")
            return False

    def validate_availability(self, requested_quantity):
        """
        Shopify-style: Simple availability check
        """
        return self.quantity >= requested_quantity


