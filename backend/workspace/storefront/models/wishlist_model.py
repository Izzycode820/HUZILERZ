# Wishlist Model - Customer favorites management
# Optimized for Cameroon market with phone-first approach

from django.db import models
from workspace.core.models.base_models import BaseWorkspaceContentModel
from workspace.store.models import Product
from workspace.core.models.customer_model import Customer
import uuid


class Wishlist(BaseWorkspaceContentModel):
    """
    Customer wishlist for saving favorite products

    Performance: Optimized customer-product relationships
    Scalability: Efficient wishlist management
    Reliability: Consistent wishlist operations
    Security: Customer-specific wishlist access

    Cameroon Market Optimizations:
    - Phone-based customer identification
    - Mobile-friendly wishlist management
    - Local product favorites tracking
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='wishlists',
        help_text="Customer who owns this wishlist"
    )

    name = models.CharField(
        max_length=255,
        default='My Wishlist',
        help_text="Wishlist name"
    )

    is_default = models.BooleanField(
        default=True,
        help_text="Whether this is the default wishlist"
    )

    is_public = models.BooleanField(
        default=False,
        help_text="Whether wishlist is publicly visible"
    )

    items_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of items in wishlist"
    )

    class Meta:
        app_label = 'workspace_storefront'
        db_table = 'storefront_wishlists'
        unique_together = ['workspace', 'customer', 'name']
        indexes = [
            models.Index(fields=['workspace', 'customer', 'is_default']),
            models.Index(fields=['workspace', 'customer', 'is_public']),
            models.Index(fields=['workspace', 'items_count']),
        ]

    def __str__(self):
        return f"{self.name} - {self.customer.name}"

    def update_items_count(self):
        """Update items count from related items"""
        self.items_count = self.items.count()
        self.save(update_fields=['items_count'])

    @property
    def is_empty(self):
        """Check if wishlist is empty"""
        return self.items_count == 0


class WishlistItem(BaseWorkspaceContentModel):
    """
    Individual item in customer wishlist

    Performance: Optimized product-wishlist relationships
    Scalability: Efficient wishlist item management
    """

    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Wishlist containing this item"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        help_text="Product in wishlist"
    )

    added_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Product price when added to wishlist"
    )

    notes = models.TextField(
        blank=True,
        help_text="Customer notes about this product"
    )

    priority = models.PositiveSmallIntegerField(
        default=1,
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')],
        help_text="Priority level for this item"
    )

    class Meta:
        app_label = 'workspace_storefront'
        db_table = 'storefront_wishlist_items'
        unique_together = ['wishlist', 'product']
        indexes = [
            models.Index(fields=['wishlist', 'product']),
            models.Index(fields=['workspace', 'wishlist', 'priority']),
            models.Index(fields=['workspace', 'product']),
        ]

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.name}"

    def save(self, *args, **kwargs):
        # Set added_at_price if not set
        if not self.added_at_price:
            self.added_at_price = self.product.price

        super().save(*args, **kwargs)

        # Update wishlist items count
        self.wishlist.update_items_count()

    def delete(self, *args, **kwargs):
        wishlist = self.wishlist
        super().delete(*args, **kwargs)
        wishlist.update_items_count()

    @property
    def price_changed(self):
        """Check if product price has changed since added"""
        if not self.added_at_price:
            return False
        return self.product.price != self.added_at_price

    @property
    def price_difference(self):
        """Calculate price difference since added"""
        if not self.added_at_price or not self.product.price:
            return 0
        return self.product.price - self.added_at_price

    @property
    def price_change_percentage(self):
        """Calculate price change percentage"""
        if not self.added_at_price or self.added_at_price == 0:
            return 0
        return ((self.product.price - self.added_at_price) / self.added_at_price) * 100