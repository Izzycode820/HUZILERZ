# Location Model - Simplified for Cameroon
# Manages user warehouse/store locations across Cameroon's 10 regions

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from workspace.core.models.base_models import TenantScopedModel


class Location(TenantScopedModel):
    """
    Simplified location model for Cameroon
    User-created warehouses/stores in Cameroon's 10 regions

    Simple, scalable, production-ready
    """

    # LOCATION IDENTIFICATION
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Location name (e.g., Douala Main Store)"
    )

    # CAMEROON REGION MAPPING (10 regions)
    region = models.CharField(
        max_length=50,
        choices=[
            ('centre', 'Centre'),
            ('littoral', 'Littoral'),
            ('west', 'West'),
            ('northwest', 'Northwest'),
            ('southwest', 'Southwest'),
            ('adamawa', 'Adamawa'),
            ('east', 'East'),
            ('far_north', 'Far North'),
            ('north', 'North'),
            ('south', 'South'),
        ],
        db_index=True,
        help_text="Cameroon region"
    )

    # ADDRESS INFORMATION
    address_line1 = models.CharField(
        max_length=255,
        help_text="Street address"
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Additional address info"
    )
    city = models.CharField(
        max_length=100,
        help_text="City name"
    )

    # CONTACT INFORMATION
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone"
    )
    email = models.EmailField(
        blank=True,
        help_text="Contact email"
    )

    # OPERATIONAL CONFIGURATION
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Active and operational"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary/default location"
    )
    low_stock_threshold = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="Low stock alert threshold"
    )
    manager_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Location manager"
    )

    # ANALYTICS (Auto-calculated)
    total_products = models.PositiveIntegerField(
        default=0,
        help_text="Total products at location"
    )
    total_stock_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total inventory value"
    )
    low_stock_alerts = models.PositiveIntegerField(
        default=0,
        help_text="Number of low stock alerts"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_locations'
        indexes = [
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['workspace', 'region']),
        ]
        ordering = ['-is_primary', 'region', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_region_display()})"

    def save(self, *args, **kwargs):
        # Only one primary location per workspace
        if self.is_primary:
            Location.objects.filter(
                workspace=self.workspace,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)

        super().save(*args, **kwargs)
        self.update_analytics()

    # PROPERTIES
    @property
    def full_address(self):
        """Get formatted address"""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.get_region_display(), 'Cameroon'])
        return ', '.join(parts)

    # INVENTORY METHODS
    @property
    def active_inventory_items(self):
        """Active inventory at this location"""
        from .inventory_model import Inventory
        return Inventory.objects.filter(
            location=self,
            quantity__gt=0
        ).select_related('variant', 'variant__product')

    @property
    def low_stock_items(self):
        """Low stock items at this location"""
        from .inventory_model import Inventory
        return Inventory.objects.filter(
            location=self,
            quantity__gt=0,
            quantity__lte=self.low_stock_threshold
        ).select_related('variant', 'variant__product')

    def update_analytics(self):
        """Update location analytics"""
        from .inventory_model import Inventory

        inventory_stats = Inventory.objects.filter(
            location=self,
            quantity__gt=0
        ).aggregate(
            total_products=models.Count('id'),
            total_value=models.Sum(
                models.F('quantity') * models.F('variant__cost_price')
            )
        )

        low_stock_count = Inventory.objects.filter(
            location=self,
            quantity__gt=0,
            quantity__lte=self.low_stock_threshold
        ).count()

        Location.objects.filter(id=self.id).update(
            total_products=inventory_stats['total_products'] or 0,
            total_stock_value=inventory_stats['total_value'] or 0,
            low_stock_alerts=low_stock_count
        )

    def can_deactivate(self):
        """Check if location can be deactivated (no inventory)"""
        from .inventory_model import Inventory
        return not Inventory.objects.filter(
            location=self,
            quantity__gt=0
        ).exists()