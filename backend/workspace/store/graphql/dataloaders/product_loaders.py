"""
Product DataLoaders for N+1 Query Prevention

Critical for performance: Prevents N+1 queries when loading
variants and inventory for multiple products
"""

from promise import Promise
from promise.dataloader import DataLoader


class VariantsByProductLoader(DataLoader):
    """
    Load variants for multiple products in one query

    Performance: 1 query instead of N queries
    Example: Loading variants for 20 products = 1 query instead of 20
    """

    def batch_load_fn(self, product_ids):
        """Batch load variants for multiple products"""
        from workspace.store.models import ProductVariant

        # Single query for all variants
        variants = ProductVariant.objects.filter(
            product_id__in=product_ids,
            is_active=True
        ).order_by('position')

        # Group by product_id
        variant_map = {}
        for variant in variants:
            product_id = str(variant.product_id)
            if product_id not in variant_map:
                variant_map[product_id] = []
            variant_map[product_id].append(variant)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            variant_map.get(str(pid), []) for pid in product_ids
        ])


class ProductsByCategoryLoader(DataLoader):
    """
    Load products for multiple categories in one query

    Performance: 1 query instead of N queries
    Example: Loading products for 10 categories = 1 query instead of 10
    """

    def batch_load_fn(self, category_ids):
        """Batch load products for multiple categories"""
        from workspace.store.models import Product

        # Single query for all products in these categories
        products = Product.objects.filter(
            category_id__in=category_ids,
            is_active=True,
            status='published'
        ).select_related('category')

        # Group by category_id
        product_map = {}
        for product in products:
            category_id = str(product.category_id)
            if category_id not in product_map:
                product_map[category_id] = []
            product_map[category_id].append(product)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            product_map.get(str(cid), []) for cid in category_ids
        ])


class ProductLoader(DataLoader):
    """
    Load multiple products by IDs in one query

    Performance: 1 query instead of N queries
    Example: Loading 20 products by ID = 1 query instead of 20
    """

    def batch_load_fn(self, product_ids):
        """Batch load products by IDs"""
        from workspace.store.models import Product

        # Single query for all products with category relationship
        products = Product.objects.filter(id__in=product_ids).select_related('category')

        # Create mapping
        product_map = {str(product.id): product for product in products}

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            product_map.get(str(pid)) for pid in product_ids
        ])


class InventoryByVariantLoader(DataLoader):
    """
    Load inventory for multiple variants in one query

    Performance: 1 query instead of N queries
    Example: Loading inventory for 20 variants = 1 query instead of 20
    """

    def batch_load_fn(self, variant_ids):
        """Batch load inventory for multiple variants"""
        from workspace.store.models import Inventory

        # Single query for all inventory
        inventory = Inventory.objects.filter(
            variant_id__in=variant_ids
        ).select_related('location')

        # Group by variant_id
        inventory_map = {}
        for inv in inventory:
            variant_id = str(inv.variant_id)
            if variant_id not in inventory_map:
                inventory_map[variant_id] = []
            inventory_map[variant_id].append(inv)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            inventory_map.get(str(vid), []) for vid in variant_ids
        ])