# Product Variant Model - Shopify-like
# Simplified variant model following Shopify patterns

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from workspace.core.models.base_models import BaseWorkspaceContentModel


class ProductVariant(BaseWorkspaceContentModel):
    """
    Simplified product variant model following Shopify patterns
    Handles product variations with minimal complexity
    """

    # CORE RELATIONSHIPS
    product = models.ForeignKey(
        'workspace_store.Product',
        on_delete=models.CASCADE,
        related_name='variants',
        db_index=True,
        help_text="Parent product"
    )

    # MEDIA
    featured_media = models.ForeignKey(
        'medialib.MediaUpload',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_in_variants',
        help_text="Featured image for this variant"
    )

    # IDENTIFIERS
    sku = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Stock Keeping Unit"
    )

    barcode = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Barcode (ISBN, UPC, GTIN, etc.)"
    )

    # OPTIONS (Shopify uses flexible options, we'll keep it simple)
    option1 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Option (e.g., Size, Color)"
    )
    option2 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Additional option"
    )

    option3 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Third option (if needed)"
    )

    # PRICING (Can override product pricing)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price (overrides product price)"
    )

    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Compare at price (overrides product compare_at_price)"
    )

    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Cost per item (overrides product cost_price)"
    )

    # INVENTORY
    track_inventory = models.BooleanField(
        default=True,
        help_text="Track inventory for this variant"
    )

    # STATUS
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Available for purchase"
    )
    position = models.PositiveIntegerField(
        default=0,
        help_text="Display position"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_product_variants'
        unique_together = [
            ['workspace', 'sku'],
            ['product', 'option1', 'option2', 'option3']
        ]
        indexes = [
            models.Index(fields=['workspace', 'product', 'is_active']),
            models.Index(fields=['workspace', 'sku']),
            models.Index(fields=['workspace', 'barcode']),
            models.Index(fields=['product', 'position']),
        ]
        ordering = ['product', 'position', 'id']

    def __str__(self):
        options = []
        if self.option1:
            options.append(self.option1)
        if self.option2:
            options.append(self.option2)
        if self.option3:
            options.append(self.option3)

        if options:
            return f"{self.product.name} ({', '.join(options)})"
        return self.product.name

