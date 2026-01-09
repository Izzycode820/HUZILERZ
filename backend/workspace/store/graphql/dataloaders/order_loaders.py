"""
Order DataLoaders for N+1 Query Prevention

Critical for order management: Prevents N+1 queries when loading
order items and related data for multiple orders
"""

from promise import Promise
from promise.dataloader import DataLoader


class OrderItemsByOrderLoader(DataLoader):
    """
    Load order items for multiple orders in one query

    Performance: 1 query instead of N queries
    Example: Loading items for 20 orders = 1 query instead of 20
    """

    def batch_load_fn(self, order_ids):
        """Batch load order items for multiple orders"""
        from workspace.store.models import OrderItem

        # Single query for all order items
        order_items = OrderItem.objects.filter(
            order_id__in=order_ids
        ).select_related('product', 'variant')

        # Group by order_id
        order_item_map = {}
        for item in order_items:
            order_id = str(item.order_id)
            if order_id not in order_item_map:
                order_item_map[order_id] = []
            order_item_map[order_id].append(item)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            order_item_map.get(str(oid), []) for oid in order_ids
        ])


class OrdersByCustomerLoader(DataLoader):
    """
    Load orders for multiple customers in one query

    Performance: 1 query instead of N queries
    Example: Loading orders for 10 customers = 1 query instead of 10
    """

    def batch_load_fn(self, customer_emails):
        """Batch load orders for multiple customers"""
        from workspace.store.models import Order

        # Single query for all customer orders
        orders = Order.objects.filter(
            customer_email__in=customer_emails
        ).order_by('-created_at')

        # Group by customer_email
        order_map = {}
        for order in orders:
            customer_email = order.customer_email
            if customer_email not in order_map:
                order_map[customer_email] = []
            order_map[customer_email].append(order)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            order_map.get(email, []) for email in customer_emails
        ])


class OrderStatsByProductLoader(DataLoader):
    """
    Load order statistics for multiple products

    Performance: 1 aggregation query instead of N queries
    Example: Loading stats for 20 products = 1 query instead of 20
    """

    def batch_load_fn(self, product_ids):
        """Batch load order stats for multiple products"""
        from django.db.models import Sum, Count
        from workspace.store.models import OrderItem

        # Single aggregation query for all products
        stats = OrderItem.objects.filter(
            product_id__in=product_ids
        ).values('product_id').annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total_price'),
            order_count=Count('order_id', distinct=True)
        )

        # Create map of product_id -> stats
        stats_map = {}
        for stat in stats:
            product_id = str(stat['product_id'])
            stats_map[product_id] = {
                'total_sold': stat['total_sold'] or 0,
                'total_revenue': float(stat['total_revenue'] or 0),
                'order_count': stat['order_count'] or 0
            }

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            stats_map.get(str(pid), {
                'total_sold': 0,
                'total_revenue': 0.0,
                'order_count': 0
            }) for pid in product_ids
        ])