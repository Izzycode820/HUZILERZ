"""
Inventory DataLoaders for N+1 Query Prevention

Critical for Cameroon multi-region inventory: Prevents N+1 queries
when loading inventory for multiple variants across 10 regions
"""

from promise import Promise
from promise.dataloader import DataLoader


class InventoryByVariantLoader(DataLoader):
    """
    Load inventory for multiple variants in one query

    Performance: 1 query instead of N queries
    Example: Loading inventory for 6 variants × 10 regions = 1 query instead of 60
    """

    def batch_load_fn(self, variant_ids):
        """Batch load inventory for multiple variants"""
        from workspace.store.models import Inventory

        # Single query for all variants × 10 regions
        inventories = Inventory.objects.filter(
            variant_id__in=variant_ids
        ).select_related('location')

        # Group by variant_id
        inventory_map = {}
        for inv in inventories:
            variant_id = str(inv.variant_id)
            if variant_id not in inventory_map:
                inventory_map[variant_id] = []
            inventory_map[variant_id].append(inv)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            inventory_map.get(str(vid), []) for vid in variant_ids
        ])


class InventoryByLocationLoader(DataLoader):
    """
    Load inventory for multiple locations in one query

    Performance: 1 query instead of N queries
    Example: Loading inventory for 10 locations = 1 query instead of 10
    """

    def batch_load_fn(self, location_ids):
        """Batch load inventory for multiple locations"""
        from workspace.store.models import Inventory

        # Single query for all locations
        inventories = Inventory.objects.filter(
            location_id__in=location_ids
        ).select_related('variant')

        # Group by location_id
        inventory_map = {}
        for inv in inventories:
            location_id = str(inv.location_id)
            if location_id not in inventory_map:
                inventory_map[location_id] = []
            inventory_map[location_id].append(inv)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            inventory_map.get(str(lid), []) for lid in location_ids
        ])


class TotalStockByVariantLoader(DataLoader):
    """
    Load total stock across all regions for multiple variants

    Performance: 1 aggregation query instead of N queries
    Example: Loading total stock for 20 variants = 1 query instead of 20
    """

    def batch_load_fn(self, variant_ids):
        """Batch load total stock for multiple variants"""
        from django.db.models import Sum
        from workspace.store.models import Inventory

        # Single aggregation query for all variants
        stock_totals = Inventory.objects.filter(
            variant_id__in=variant_ids
        ).values('variant_id').annotate(
            total_stock=Sum('quantity')
        )

        # Create map of variant_id -> total_stock
        stock_map = {}
        for stock in stock_totals:
            variant_id = str(stock['variant_id'])
            stock_map[variant_id] = stock['total_stock'] or 0

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            stock_map.get(str(vid), 0) for vid in variant_ids
        ])


class LocationLoader(DataLoader):
    """
    Load Location objects by ID to prevent N+1 queries

    Performance: 1 query instead of N queries
    Example: Loading locations for 50 inventory items = 1 query instead of 50
    """

    def batch_load_fn(self, location_ids):
        """Batch load locations by IDs"""
        from workspace.store.models import Location

        # Single query for all locations
        locations = Location.objects.filter(id__in=location_ids)
        location_dict = {str(location.id): location for location in locations}

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            location_dict.get(str(lid)) for lid in location_ids
        ])