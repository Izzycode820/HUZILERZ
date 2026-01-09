"""
DataLoader Registry for GraphQL Context

Central registry for all DataLoaders to prevent N+1 queries
"""

from .product_loaders import VariantsByProductLoader, ProductsByCategoryLoader
from .inventory_loaders import InventoryByVariantLoader, InventoryByLocationLoader, TotalStockByVariantLoader
from .order_loaders import OrderItemsByOrderLoader, OrdersByCustomerLoader, OrderStatsByProductLoader
from .category_loaders import ChildrenByCategoryLoader, AncestorsByCategoryLoader, CategoryStatsLoader


class LoaderRegistry:
    """
    Registry for all DataLoaders

    Each DataLoader instance is created once per request
    and shared across all resolvers to maximize performance
    """

    def __init__(self):
        # Product-related loaders
        self.variants_by_product = VariantsByProductLoader()
        self.products_by_category = ProductsByCategoryLoader()

        # Inventory-related loaders
        self.inventory_by_variant = InventoryByVariantLoader()
        self.inventory_by_location = InventoryByLocationLoader()
        self.total_stock_by_variant = TotalStockByVariantLoader()

        # Order-related loaders
        self.order_items_by_order = OrderItemsByOrderLoader()
        self.orders_by_customer = OrdersByCustomerLoader()
        self.order_stats_by_product = OrderStatsByProductLoader()

        # Category-related loaders
        self.children_by_category = ChildrenByCategoryLoader()
        self.ancestors_by_category = AncestorsByCategoryLoader()
        self.category_stats = CategoryStatsLoader()