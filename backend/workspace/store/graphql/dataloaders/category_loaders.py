"""
Category DataLoaders for N+1 Query Prevention

Critical for hierarchical category navigation: Prevents N+1 queries
when loading children, ancestors, and related category data
"""

from promise import Promise
from promise.dataloader import DataLoader


class ChildrenByCategoryLoader(DataLoader):
    """
    Load children for multiple categories in one query

    Performance: 1 query instead of N queries
    Example: Loading children for 10 categories = 1 query instead of 10
    """

    def batch_load_fn(self, category_ids):
        """Batch load children for multiple categories"""
        from workspace.store.models import Category

        # Single query for all children
        children = Category.objects.filter(
            parent_id__in=category_ids,
            is_visible=True
        ).order_by('sort_order', 'name')

        # Group by parent_id
        children_map = {}
        for child in children:
            parent_id = str(child.parent_id)
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(child)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            children_map.get(str(cid), []) for cid in category_ids
        ])


class AncestorsByCategoryLoader(DataLoader):
    """
    Load ancestors for multiple categories in one query

    Performance: 1 query instead of N queries
    Example: Loading ancestors for 20 categories = 1 query instead of 20
    """

    def batch_load_fn(self, category_ids):
        """Batch load ancestors for multiple categories"""
        from workspace.store.models import Category

        # Single query to get all categories
        all_categories = Category.objects.filter(
            workspace_id__in=[cat.workspace_id for cat in Category.objects.filter(id__in=category_ids)]
        ).values('id', 'parent_id', 'name', 'slug')

        # Build category map for efficient lookup
        category_map = {str(cat['id']): cat for cat in all_categories}

        # Function to get ancestors for a category
        def get_ancestors(category_id):
            ancestors = []
            current_id = str(category_id)

            while current_id in category_map:
                current = category_map[current_id]
                ancestors.insert(0, {
                    'id': current['id'],
                    'name': current['name'],
                    'slug': current['slug']
                })

                if not current['parent_id']:
                    break

                current_id = str(current['parent_id'])

            return ancestors

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            get_ancestors(cid) for cid in category_ids
        ])


class CategoryStatsLoader(DataLoader):
    """
    Load category statistics (product counts, analytics) for multiple categories

    Performance: 1 aggregation query instead of N queries
    Example: Loading stats for 15 categories = 1 query instead of 15
    """

    def batch_load_fn(self, category_ids):
        """Batch load category stats for multiple categories"""
        from django.db.models import Count, Avg, Sum
        from workspace.store.models import Product

        # Single aggregation query for all categories
        stats = Product.objects.filter(
            category_id__in=category_ids,
            is_active=True,
            status='published'
        ).values('category_id').annotate(
            active_product_count=Count('id'),
            average_price=Avg('price'),
            total_stock=Sum('stock_quantity'),
            total_views=Sum('views'),
            total_orders=Sum('orders')
        )

        # Create map of category_id -> stats
        stats_map = {}
        for stat in stats:
            category_id = str(stat['category_id'])
            stats_map[category_id] = {
                'active_product_count': stat['active_product_count'] or 0,
                'average_price': float(stat['average_price'] or 0),
                'total_stock': stat['total_stock'] or 0,
                'total_views': stat['total_views'] or 0,
                'total_orders': stat['total_orders'] or 0
            }

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            stats_map.get(str(cid), {
                'active_product_count': 0,
                'average_price': 0.0,
                'total_stock': 0,
                'total_views': 0,
                'total_orders': 0
            }) for cid in category_ids
        ])