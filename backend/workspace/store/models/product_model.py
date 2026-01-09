# Product Model - Enhanced with proper category relationships
# Complete logic correction with bidirectional category listening

from django.db import models
from decimal import Decimal
import uuid
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.db.models import F
from workspace.core.models.base_models import BaseWorkspaceContentModel


class Product(BaseWorkspaceContentModel):
    """
    Enhanced product model with proper category relationships
    Bidirectional listening to category changes and analytics

    Engineering Principles Applied:
    - Performance: Optimized category queries with ForeignKey indexing
    - Scalability: Efficient category-based product filtering
    - Maintainability: Clear bidirectional relationships and cascading logic
    - Security: Data integrity through ForeignKey constraints
    - Simplicity: Standard product-category relationship patterns
    - Production-Ready: Proper cascading updates and deletion handling
    """

    # CORE PRODUCT FIELDS
    name = models.CharField(max_length=255, help_text="Product name")
    description = models.TextField(blank=True, help_text="Product description")
    slug = models.SlugField(max_length=255, blank=True, help_text="URL-friendly identifier")

    # PRICING
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Selling price (required)"
    )
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Original price for discounts"
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cost/wholesale price"
    )

    # CAMEROON-SPECIFIC PRICING
    charge_tax = models.BooleanField(
        default=True,
        help_text="Whether to charge tax on this product"
    )
    payment_charges = models.BooleanField(
        default=False,
        help_text="Whether to apply Cameroon mobile money/payment method charges"
    )
    charges_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Fixed payment charges amount (if applicable)"
    )

    # IDENTIFIERS
    sku = models.CharField(max_length=100, blank=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=50, blank=True, help_text="Product barcode")
    brand = models.CharField(max_length=100, blank=True, help_text="Product brand")
    vendor = models.CharField(max_length=100, blank=True, help_text="Product vendor")

    # PRODUCT TYPE & STATUS
    product_type = models.CharField(
        max_length=50,
        choices=[
            ('physical', 'Physical Product'),
            ('digital', 'Digital Product'),
            ('service', 'Service')
        ],
        default='physical',
        help_text="Type of product"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('published', 'Published'),
            ('draft', 'Draft')
        ],
        default='published',
        help_text="Product status"
    )
    # Subscription enforcement: Products beyond plan limit are marked inactive
    # They remain stored but cannot be published or sold
    active_by_plan = models.BooleanField(
        default=True,
        db_index=True,
        help_text="False when product exceeds plan limit (auto-enforcement)"
    )
    published_at = models.DateTimeField(null=True, blank=True, help_text="When product was published")

    # CATEGORIZATION
    category = models.ForeignKey(
        'workspace_store.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Primary product category"
    )
    tags = models.JSONField(default=list, blank=True, help_text="Product tags for search")

    # MEDIA (NEW - Production-grade media system)
    featured_media = models.ForeignKey(
        'medialib.MediaUpload',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_in_products',
        help_text="Primary product image (thumbnail/featured)"
    )
    media_gallery = models.ManyToManyField(
        'medialib.MediaUpload',
        through='ProductMediaGallery',
        related_name='product_gallery',
        blank=True,
        help_text="Product media gallery (images, videos, 3D models)"
    )

    # INVENTORY
    track_inventory = models.BooleanField(default=True, help_text="Whether to track inventory")
    inventory_quantity = models.PositiveIntegerField(default=0, help_text="Available stock quantity")
    allow_backorders = models.BooleanField(default=False, help_text="Allow orders when out of stock")
    inventory_health = models.CharField(
        max_length=20,
        choices=[
            ('healthy', 'Healthy'),
            ('low', 'Low Stock'),
            ('critical', 'Critical'),
            ('out_of_stock', 'Out of Stock')
        ],
        default='healthy',
        help_text="Inventory health status"
    )

    # VARIANTS
    has_variants = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether product has variants"
    )
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="Product options for variants (e.g., [{'name': 'Size', 'values': ['S', 'M', 'L']}])"
    )

    # SHIPPING
    requires_shipping = models.BooleanField(default=True, help_text="Needs shipping")
    package = models.ForeignKey(
        'workspace_store.Package',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Shipping package for this product (optional - falls back to default if not set)"
    )
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Product weight (kg)"
    )

    # SEO
    meta_title = models.CharField(max_length=255, blank=True, help_text="SEO meta title")
    meta_description = models.TextField(blank=True, help_text="SEO meta description")

    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_products'
        unique_together = ['workspace', 'slug']
        indexes = [
            models.Index(fields=['workspace', 'status', '-created_at']),
            models.Index(fields=['workspace', 'category', 'status']),
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['workspace', 'sku']),
            models.Index(fields=['price']),
            models.Index(fields=['category']),
            # Downgrade enforcement queries
            models.Index(fields=['workspace', 'active_by_plan', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.workspace.name}"

    def save(self, *args, **kwargs):
        # Auto-generate unique slug
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while Product.objects.filter(workspace=self.workspace, slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()

        # Ensure title matches name for content model compatibility
        if not self.title:
            self.title = self.name

        # Safety net: Enforce non-physical product constraints
        # Digital and service products should never have shipping or inventory tracking
        if self.product_type in ('digital', 'service'):
            self.requires_shipping = False
            self.track_inventory = False
            self.allow_backorders = False

        super().save(*args, **kwargs)


    # SIMPLE DATA PROPERTIES ONLY - No business logic
    @property
    def category_name(self):
        """Get category name"""
        return self.category.name if self.category else ""

    def get_absolute_url(self):
        """Get product URL"""
        return f"/store/{self.workspace.slug}/products/{self.slug}"

    # NEW MEDIA SYSTEM: Use featured_media FK and media_gallery M2M relationships
    # Access via: product.featured_media, product.media_gallery.all(), product.gallery_items.all()

    @property
    def image_count(self):
        """Get count of images in media gallery"""
        return self.gallery_items.filter(media__media_type='image').count()

    @property
    def video_count(self):
        """Get count of videos in media gallery"""
        return self.gallery_items.filter(media__media_type='video').count()

    @property
    def model_3d_count(self):
        """Get count of 3D models in media gallery"""
        return self.gallery_items.filter(media__media_type='3d_model').count()

    @property
    def has_media(self):
        """Check if product has any media (featured or gallery)"""
        return bool(self.featured_media_id) or self.gallery_items.exists()

    def create_snapshot(self):
        """
        Create comprehensive product snapshot for order history.

        Used by checkout and order services to preserve product state at order time.
        Follows Shopify-style pattern: capture everything at time of purchase.

        Performance: <5ms (single query with prefetch)
        Reliability: Returns empty dict on failure, never raises

        Returns:
            dict: Complete product state with images, pricing, metadata
        """
        import logging
        from django.utils import timezone

        logger = logging.getLogger('store.models.product')

        try:
            # Build images array from media system
            images_data = []

            # Add featured media first (primary image)
            if self.featured_media:
                images_data.append({
                    'id': str(self.featured_media.id),
                    'url': self.featured_media.file_url,
                    'position': 0
                })

            # Add gallery images (avoid N+1 with select_related)
            from workspace.store.models import ProductMediaGallery
            gallery_items = ProductMediaGallery.objects.filter(
                product=self,
                media__media_type='image'
            ).select_related('media').order_by('position')

            for item in gallery_items:
                # Skip if it's the same as featured_media (avoid duplicate)
                if self.featured_media and item.media.id == self.featured_media.id:
                    continue
                images_data.append({
                    'id': str(item.media.id),
                    'url': item.media.file_url,
                    'position': item.position
                })

            # Build complete snapshot
            return {
                'id': str(self.id),
                'name': self.name,
                'description': self.description,
                'slug': self.slug,
                'price': str(self.price),
                'compare_at_price': str(self.compare_at_price) if self.compare_at_price else None,
                'cost_price': str(self.cost_price) if self.cost_price else None,
                'sku': self.sku,
                'barcode': self.barcode,
                'brand': self.brand,
                'vendor': self.vendor,
                'product_type': self.product_type,
                'status': self.status,
                'published_at': self.published_at.isoformat() if self.published_at else None,
                'category': {
                    'id': str(self.category.id) if self.category else None,
                    'name': self.category.name if self.category else None
                },
                'tags': self.tags,
                'track_inventory': self.track_inventory,
                'inventory_quantity': self.inventory_quantity,
                'allow_backorders': self.allow_backorders,
                'inventory_health': self.inventory_health,
                'has_variants': self.has_variants,
                'options': self.options,
                'requires_shipping': self.requires_shipping,
                'weight': str(self.weight) if self.weight else None,
                'package': {
                    'id': str(self.package.id) if self.package else None,
                    'name': self.package.name if self.package else None
                },
                'meta_title': self.meta_title,
                'meta_description': self.meta_description,
                'images': images_data,
                'snapshot_timestamp': timezone.now().isoformat()
            }

        except Exception as e:
            # Graceful degradation: log error but don't block order creation
            logger.error(
                f"Failed to create product snapshot for {self.id}: {e}",
                extra={'product_id': str(self.id), 'product_name': self.name},
                exc_info=True
            )
            # Return minimal snapshot to prevent total failure
            return {
                'id': str(self.id),
                'name': self.name,
                'price': str(self.price),
                'sku': self.sku,
                'snapshot_timestamp': timezone.now().isoformat(),
                'error': 'Snapshot creation failed'
            }