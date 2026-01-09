from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import logging
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


class Template(models.Model):
    """
    Master template model representing a theme/template in the system.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Template ID",
        help_text="Unique identifier for the template"
    )

    # Template Type Choices
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

    # Price Tier Choices
    PRICE_TIER_FREE = 'free'
    PRICE_TIER_PAID = 'paid'
    PRICE_TIER_EXCLUSIVE = 'exclusive'

    PRICE_TIER_CHOICES = [
        (PRICE_TIER_FREE, 'Free'),
        (PRICE_TIER_PAID, 'Paid'),
        (PRICE_TIER_EXCLUSIVE, 'Exclusive'),
    ]

    # Status Choices
    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_DEPRECATED = 'deprecated'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_DEPRECATED, 'Deprecated'),
    ]

    # Core Template Information
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Template Name",
        help_text="Unique name for the template"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        db_index=True,
        verbose_name="URL Slug",
        help_text="URL-friendly version of the name"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Detailed description of the template"
    )

    # Template Type and Compatibility
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        default=TEMPLATE_TYPE_ECOMMERCE,
        db_index=True,
        verbose_name="Template Type",
        help_text="Type of business this template is designed for"
    )
    workspace_types = models.JSONField(
        default=list,
        verbose_name="Compatible Workspaces",
        help_text="List of compatible workspace types (e.g., ['store', 'services'])"
    )

    # Metadata from Manifest
    features = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Features",
        help_text="List of template features from manifest"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Tags",
        help_text="Tags for categorization and search"
    )
    compatibility = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Compatibility",
        help_text="Technology compatibility requirements (nextjs, react, etc.)"
    )
    author = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Author",
        help_text="Template author or creator"
    )
    license = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="License",
        help_text="Template license type"
    )

    # Pricing Information
    price_tier = models.CharField(
        max_length=20,
        choices=PRICE_TIER_CHOICES,
        default=PRICE_TIER_FREE,
        db_index=True,
        verbose_name="Price Tier",
        help_text="Pricing category for the template"
    )
    price_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Price Amount",
        help_text="Price in FCFA for paid/exclusive templates"
    )

    # Version and Status
    version = models.CharField(
        max_length=20,
        default='1.0.0',
        verbose_name="Version",
        help_text="Current version of the template"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        verbose_name="Status",
        help_text="Current status of the template"
    )

    # Preview and Demo
    demo_url = models.URLField(
        blank=True,
        verbose_name="Demo URL",
        help_text="Live demo URL for previewing the template"
    )
    preview_image = models.URLField(
        blank=True,
        verbose_name="Preview Image",
        help_text="Preview image URL from CDN"
    )
    showcase_sections = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Showcase Sections",
        help_text="Array of {title, description, image} for theme details page showcase"
    )

    # Usage Metrics
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="View Count",
        help_text="Number of times this template has been viewed"
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Download Count",
        help_text="Number of times this template has been downloaded"
    )
    active_usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Active Usage Count",
        help_text="Number of active workspaces using this template"
    )

    # Technical Configuration
    puck_config = models.JSONField(
        default=dict,
        verbose_name="Puck Configuration",
        help_text="Puck configuration schema for user customization"
    )
    puck_data = models.JSONField(
        default=dict,
        verbose_name="Puck Data",
        help_text="Puck data containing default page layout and content"
    )

    # Dynamic Theme Loading Configuration
    manifest_url = models.URLField(
        blank=True,
        verbose_name="Manifest URL",
        help_text="URL to theme-manifest.json (dev: localhost:3001, prod: CDN)"
    )
    cdn_base_url = models.URLField(
        blank=True,
        verbose_name="CDN Base URL",
        help_text="Base URL for CDN assets (e.g., https://cdn.example.com/themes/{slug}/)"
    )

    # GitHub Integration
    github_repo_owner = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="GitHub Repository Owner",
        help_text="GitHub username or organization name"
    )
    github_repo_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="GitHub Repository Name",
        help_text="Name of the GitHub repository"
    )
    github_branch = models.CharField(
        max_length=100,
        default='main',
        verbose_name="GitHub Branch",
        help_text="Default branch for GitHub operations"
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_theme_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'theme_templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['template_type']),
            models.Index(fields=['price_tier']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.template_type}) - v{self.version}"

    def clean(self):
        """Custom validation for the template model"""
        super().clean()

        # Validate price amount based on price tier
        if self.price_tier in [self.PRICE_TIER_PAID, self.PRICE_TIER_EXCLUSIVE]:
            if not self.price_amount or self.price_amount <= 0:
                raise ValidationError({
                    'price_amount': 'Price amount is required for paid and exclusive templates'
                })

        # Validate workspace types compatibility
        valid_workspace_types = ['store', 'services', 'blog', 'restaurant']
        for ws_type in self.workspace_types:
            if ws_type not in valid_workspace_types:
                raise ValidationError({
                    'workspace_types': f'Invalid workspace type: {ws_type}. Must be one of {valid_workspace_types}'
                })

    def save(self, *args, **kwargs):
        """Custom save method with validation and slug generation"""
        if not self.slug:
            self.slug = slugify(self.name)

        # Ensure slug is unique
        original_slug = self.slug
        counter = 1
        while Template.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1

        super().save(*args, **kwargs)

    def get_manifest_url(self):
        """Get manifest URL for the template - use database field directly"""
        return self.manifest_url or ''

    def increment_view_count(self):
        """Increment view count atomically with error handling"""
        try:
            # Use update with F expression for atomic increment
            Template.objects.filter(id=self.id).update(view_count=models.F('view_count') + 1)
            # Refresh the instance from database
            self.refresh_from_db()
        except Exception as e:
            logger.error(f"Error incrementing view count for template {self.id}: {e}")

    def increment_download_count(self):
        """Increment download count atomically with error handling"""
        try:
            # Use update with F expression for atomic increment
            Template.objects.filter(id=self.id).update(download_count=models.F('download_count') + 1)
            # Refresh the instance from database
            self.refresh_from_db()
        except Exception as e:
            logger.error(f"Error incrementing download count for template {self.id}: {e}")


    @property
    def is_free(self):
        return self.price_tier == self.PRICE_TIER_FREE

    @property
    def is_paid(self):
        return self.price_tier in [self.PRICE_TIER_PAID, self.PRICE_TIER_EXCLUSIVE]

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE