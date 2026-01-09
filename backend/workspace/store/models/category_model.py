# Category Model - Simple Collection System
# Shopify-inspired collections without complex hierarchy

from django.db import models
from django.utils.text import slugify
from workspace.core.models.base_models import TenantScopedModel


class Category(TenantScopedModel):
    """
    Simple collection model for product categorization
    Focused on practical e-commerce needs without complex hierarchy

    Modern E-commerce Principles:
    - Simplicity: Flat structure for easy management
    - Performance: Minimal overhead and fast queries
    - Practical: Essential fields only for collections
    - SEO-Friendly: Built-in SEO optimization
    """

    # BASIC COLLECTION FIELDS
    name = models.CharField(max_length=255, help_text="Collection name")
    description = models.TextField(blank=True, help_text="Collection description")
    slug = models.SlugField(max_length=255, blank=True, help_text="URL-friendly identifier")

    # MEDIA
    featured_media = models.ForeignKey(
        'medialib.MediaUpload',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_in_categories',
        help_text="Featured image for this category/collection"
    )

    # COLLECTION VISIBILITY & FEATURES
    is_visible = models.BooleanField(default=True, help_text="Whether collection is visible to customers")
    is_featured = models.BooleanField(default=False, help_text="Whether collection is featured on homepage")
    sort_order = models.IntegerField(default=0, help_text="Manual sort order for admin drag-drop")

    # SEO OPTIMIZATION
    meta_title = models.CharField(max_length=255, blank=True, help_text="SEO meta title")
    meta_description = models.TextField(blank=True, help_text="SEO meta description")

    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_categories'
        unique_together = ['workspace', 'slug']
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['workspace', 'is_visible']),
            models.Index(fields=['workspace', 'is_featured']),
            models.Index(fields=['workspace', 'sort_order']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name)

        # Ensure unique slug within workspace
        original_slug = self.slug
        counter = 1
        while Category.objects.filter(workspace=self.workspace, slug=self.slug).exclude(id=self.id).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1

        super().save(*args, **kwargs)

    # SIMPLE PROPERTIES
    @property
    def active_products(self):
        """Get active products in this collection"""
        from .product_model import Product
        return Product.objects.filter(
            category=self,
            is_active=True,
            status='published'
        )

    @property
    def product_count(self):
        """Get count of products in this collection"""
        return self.active_products.count()

    # NEW MEDIA SYSTEM: Use featured_media FK relationship
    # Access via: category.featured_media

    @property
    def has_featured_image(self):
        """Check if category has a featured image"""
        return bool(self.featured_media_id)

    @property
    def featured_image_url(self):
        """Get featured image URL"""
        return self.featured_media.file_url if self.featured_media else None
