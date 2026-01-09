"""
Shipping Models - Shopify-style with Cameroon context
PRODUCTION-READY: Industry standard models for shipping management
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from workspace.core.models.base_models import TenantScopedModel


class ShippingZone(TenantScopedModel):
    """
    Shopify-style shipping zones for Cameroon regions

    Production Best Practices:
    - Tenant scoping for multi-workspace
    - Cameroon regional targeting
    - Performance optimizations
    """

    pass


class Package(TenantScopedModel):
    """
    Cameroon Shipping Package Model

    Simple, flexible shipping for informal markets
    Each package represents ONE complete shipping option

    Example: "Buea Car Shipping - 1000 XAF"
    Can be created from Settings page OR inline on Add Product page
    """

    PACKAGE_TYPE_CHOICES = [
        ('box', 'Box'),
        ('envelope', 'Envelope'),
        ('soft_package', 'Soft Package'),
    ]

    PACKAGE_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]

    # Package identity
    name = models.CharField(
        max_length=100,
        help_text="Package name (e.g., 'Buea Car Shipping')"
    )

    package_type = models.CharField(
        max_length=20,
        choices=PACKAGE_TYPE_CHOICES,
        default='box',
        help_text="Type of package"
    )

    size = models.CharField(
        max_length=20,
        choices=PACKAGE_SIZE_CHOICES,
        default='medium',
        help_text="Package size"
    )

    weight = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Weight capacity in kg"
    )

    method = models.CharField(
        max_length=100,
        help_text="Shipping method (e.g., 'Car', 'Bike', 'Moto-taxi')"
    )

    # Region-specific shipping fees (merchant sets exact costs)
    region_fees = models.JSONField(
        default=dict,
        help_text="Shipping fees by region in XAF format: {'yaounde': 1500, 'douala': 1200, 'buea': 1000}"
    )

    estimated_days = models.CharField(
        max_length=50,
        default="3-5",
        help_text="Estimated delivery time (e.g., '1-2', '3-5 days')"
    )

    # Settings
    use_as_default = models.BooleanField(
        default=False,
        help_text="Use this package as default fallback for products without shipping"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this package is active"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'workspace_store_packages'
        indexes = [
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['workspace', 'use_as_default']),
            models.Index(fields=['workspace', 'method', 'is_active']),
        ]
        ordering = ['method', 'name']

    def __str__(self):
        regions = list(self.region_fees.keys()) if self.region_fees else ['no regions']
        return f"{self.name} via {self.method} - {len(regions)} regions"

    def save(self, *args, **kwargs):
        # Ensure only one default package per workspace
        if self.use_as_default:
            Package.objects.filter(
                workspace=self.workspace,
                use_as_default=True
            ).exclude(id=self.id).update(use_as_default=False)

        super().save(*args, **kwargs)


