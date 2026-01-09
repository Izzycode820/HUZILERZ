# DataLoader for batching product queries
# IMPORTANT: Prevents N+1 query problems in GraphQL

from aiodataloader import DataLoader
from workspace.store.models import Product, ProductVariant
import logging

logger = logging.getLogger(__name__)


class ProductLoader(DataLoader):
    """
    DataLoader for batching product queries

    Performance: Reduces N queries to 1 batch query
    Example: Loading 100 products = 1 query instead of 100
    """

    async def batch_load_fn(self, product_ids):
        """
        Batch load products by IDs

        Performance Optimization:
        - Single query for all IDs
        - select_related for workspace
        - Maintains order of requested IDs
        """
        logger.debug(f"Batch loading {len(product_ids)} products")

        # Single query for all products
        products = Product.objects.filter(
            id__in=product_ids,
            status='published',
            is_active=True
        ).select_related('workspace')

        # Create dict for O(1) lookup
        product_map = {str(product.id): product for product in products}

        # Return in same order as requested (DataLoader requirement)
        return [product_map.get(str(pid)) for pid in product_ids]


class ProductVariantLoader(DataLoader):
    """
    DataLoader for batching product variant queries
    """

    async def batch_load_fn(self, variant_ids):
        """
        Batch load variants by IDs
        """
        logger.debug(f"Batch loading {len(variant_ids)} variants")

        variants = ProductVariant.objects.filter(
            id__in=variant_ids,
            is_active=True
        ).select_related('product', 'inventory')

        variant_map = {str(variant.id): variant for variant in variants}

        return [variant_map.get(str(vid)) for vid in variant_ids]


class ProductByWorkspaceLoader(DataLoader):
    """
    DataLoader for loading products by workspace
    """

    async def batch_load_fn(self, workspace_ids):
        """
        Batch load products by workspace IDs
        """
        logger.debug(f"Batch loading products for {len(workspace_ids)} workspaces")

        # Get products for each workspace
        products_by_workspace = {}
        for workspace_id in workspace_ids:
            products = Product.objects.filter(
                workspace_id=workspace_id,
                status='published',
                is_active=True
            ).select_related('workspace')
            products_by_workspace[str(workspace_id)] = list(products)

        return [products_by_workspace.get(str(wid), []) for wid in workspace_ids]


# DataLoader context setup
def get_dataloaders(request):
    """
    Create DataLoader instances per request

    Important: One loader instance per request (not shared)
    """
    return {
        'product_loader': ProductLoader(),
        'variant_loader': ProductVariantLoader(),
        'product_by_workspace_loader': ProductByWorkspaceLoader(),
    }


def add_dataloaders_to_context(get_response):
    """
    Middleware to add DataLoaders to request context
    """
    def middleware(request):
        request.dataloaders = get_dataloaders(request)
        response = get_response(request)
        return response

    return middleware