from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import logging
import uuid

logger = logging.getLogger(__name__)


class TemplateCategory(models.Model):
    """
    Template category model for organizing templates in the theme store.
    Supports categorization by template type, price tier, and custom categories.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Category ID",
        help_text="Unique identifier for the category"
    )

    # Template Type Choices (matching Template model)
    TEMPLATE_TYPE_ECOMMERCE = 'ecommerce'
    TEMPLATE_TYPE_SERVICES = 'services'
    TEMPLATE_TYPE_BLOG = 'blog'
    TEMPLATE_TYPE_RESTAURANT = 'restaurant'

    TEMPLATE_TYPE_CHOICES = [
        (TEMPLATE_TYPE_ECOMMERCE, 'E-commerce'),
        (TEMPLATE_TYPE_SERVICES, 'Services'),
        (TEMPLATE_TYPE_BLOG, 'Blog'),
        (TEMPLATE_TYPE_RESTAURANT, 'Restaurant'),
    ]

    # Price Tier Choices (matching Template model)
    PRICE_TIER_FREE = 'free'
    PRICE_TIER_PAID = 'paid'
    PRICE_TIER_EXCLUSIVE = 'exclusive'

    PRICE_TIER_CHOICES = [
        (PRICE_TIER_FREE, 'Free'),
        (PRICE_TIER_PAID, 'Paid'),
        (PRICE_TIER_EXCLUSIVE, 'Exclusive'),
    ]

    # Core Category Information
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Category Name",
        help_text="Unique name for the category"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        db_index=True,
        verbose_name="URL Slug",
        help_text="URL-friendly version of the category name"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Detailed description of the category"
    )

    # Category Type and Filtering
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        blank=True,
        db_index=True,
        verbose_name="Template Type",
        help_text="Specific template type this category applies to (optional)"
    )
    price_tier_filters = models.JSONField(
        default=list,
        verbose_name="Price Tier Filters",
        help_text="List of price tiers this category includes (e.g., ['free', 'paid'])"
    )

    # Display and Organization
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Sort Order",
        help_text="Order in which categories are displayed (lower numbers first)"
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Is Featured",
        help_text="Whether this category should be featured prominently"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Is Active",
        help_text="Whether this category is currently active"
    )

    # Visual Elements
    icon_url = models.URLField(
        blank=True,
        verbose_name="Icon URL",
        help_text="URL to category icon image"
    )
    background_color = models.CharField(
        max_length=7,
        blank=True,
        verbose_name="Background Color",
        help_text="Hex color code for category background (e.g., #FF5733)"
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
        db_table = 'theme_template_categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['template_type']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
        ]
        verbose_name = "Template Category"
        verbose_name_plural = "Template Categories"

    def __str__(self):
        return self.name

    def clean(self):
        """Custom validation for the template category model"""
        super().clean()

        # Validate price tier filters
        valid_price_tiers = [self.PRICE_TIER_FREE, self.PRICE_TIER_PAID, self.PRICE_TIER_EXCLUSIVE]
        for tier in self.price_tier_filters:
            if tier not in valid_price_tiers:
                raise ValidationError({
                    'price_tier_filters': f'Invalid price tier: {tier}. Must be one of {valid_price_tiers}'
                })

        # Validate background color format if provided
        if self.background_color:
            if not self.background_color.startswith('#') or len(self.background_color) != 7:
                raise ValidationError({
                    'background_color': 'Background color must be a valid hex color code (e.g., #FF5733)'
                })

    def save(self, *args, **kwargs):
        """Custom save method with validation and slug generation"""
        if not self.slug:
            self.slug = slugify(self.name)

        # Ensure slug is unique
        original_slug = self.slug
        counter = 1
        while TemplateCategory.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1

        super().save(*args, **kwargs)

    def get_templates_count(self):
        """Get count of templates in this category with error handling"""
        try:
            from .template import Template
            queryset = Template.objects.filter(status=Template.STATUS_ACTIVE)

            # Apply template type filter if specified
            if self.template_type:
                queryset = queryset.filter(template_type=self.template_type)

            # Apply price tier filters if specified
            if self.price_tier_filters:
                queryset = queryset.filter(price_tier__in=self.price_tier_filters)

            return queryset.count()
        except Exception as e:
            logger.error(f"Error getting templates count for category {self.id}: {e}")
            return 0

    def get_featured_templates(self, limit=6):
        """Get featured templates in this category with error handling"""
        try:
            from .template import Template
            queryset = Template.objects.filter(
                status=Template.STATUS_ACTIVE
            ).order_by('-rating', '-download_count')

            # Apply template type filter if specified
            if self.template_type:
                queryset = queryset.filter(template_type=self.template_type)

            # Apply price tier filters if specified
            if self.price_tier_filters:
                queryset = queryset.filter(price_tier__in=self.price_tier_filters)

            return queryset[:limit]
        except Exception as e:
            logger.error(f"Error getting featured templates for category {self.id}: {e}")
            return []

    @property
    def display_name(self):
        """Get display name with template type context"""
        try:
            if self.template_type:
                template_type_display = dict(self.TEMPLATE_TYPE_CHOICES).get(self.template_type, '')
                return f"{self.name} ({template_type_display})"
            return self.name
        except Exception as e:
            logger.error(f"Error getting display name for category {self.id}: {e}")
            return self.name

    def activate(self):
        """Activate category with error handling"""
        try:
            self.is_active = True
            self.save(update_fields=['is_active'])
            logger.info(f"Activated template category {self.id}")
        except Exception as e:
            logger.error(f"Error activating template category {self.id}: {e}")
            raise

    def deactivate(self):
        """Deactivate category with error handling"""
        try:
            self.is_active = False
            self.save(update_fields=['is_active'])
            logger.info(f"Deactivated template category {self.id}")
        except Exception as e:
            logger.error(f"Error deactivating template category {self.id}: {e}")
            raise

    def feature(self):
        """Mark category as featured with error handling"""
        try:
            self.is_featured = True
            self.save(update_fields=['is_featured'])
            logger.info(f"Featured template category {self.id}")
        except Exception as e:
            logger.error(f"Error featuring template category {self.id}: {e}")
            raise

    def unfeature(self):
        """Remove featured status from category with error handling"""
        try:
            self.is_featured = False
            self.save(update_fields=['is_featured'])
            logger.info(f"Unfeatured template category {self.id}")
        except Exception as e:
            logger.error(f"Error unfeaturing template category {self.id}: {e}")
            raise