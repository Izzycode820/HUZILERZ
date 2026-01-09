"""
Sales Channel DataLoaders for N+1 Query Prevention

Critical for sales channel operations: Prevents N+1 queries
when loading channel products, orders, and analytics data
"""

from promise import Promise
from promise.dataloader import DataLoader


class SalesChannelByIdLoader(DataLoader):
    """
    Load multiple sales channels by ID in one query

    Performance: 1 query instead of N queries
    Example: Loading 10 sales channels by ID = 1 query instead of 10
    """

    def batch_load_fn(self, channel_ids):
        """Batch load sales channels by ID"""
        from workspace.store.models.sales_channel_model import SalesChannel

        # Single query for all sales channels
        channels = SalesChannel.objects.filter(
            id__in=channel_ids
        ).select_related('workspace')

        # Create map of id -> channel
        channel_map = {str(channel.id): channel for channel in channels}

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            channel_map.get(str(cid)) for cid in channel_ids
        ])


class ChannelProductsBySalesChannelLoader(DataLoader):
    """
    Load channel products for multiple sales channels in one query

    Performance: 1 query instead of N queries
    Example: Loading products for 8 channels = 1 query instead of 8
    """

    def batch_load_fn(self, channel_ids):
        """Batch load channel products by sales channel"""
        from workspace.store.models.sales_channel_model import ChannelProduct

        # Single query for all channel products
        products = ChannelProduct.objects.filter(
            sales_channel_id__in=channel_ids,
            is_visible=True
        ).select_related('sales_channel', 'workspace').order_by('-created_at')

        # Group by channel_id
        products_map = {}
        for product in products:
            channel_id = str(product.sales_channel_id)
            if channel_id not in products_map:
                products_map[channel_id] = []
            products_map[channel_id].append(product)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            products_map.get(str(cid), []) for cid in channel_ids
        ])


class ChannelOrdersBySalesChannelLoader(DataLoader):
    """
    Load channel orders for multiple sales channels in one query

    Performance: 1 query instead of N queries
    Example: Loading orders for 8 channels = 1 query instead of 8
    """

    def batch_load_fn(self, channel_ids):
        """Batch load channel orders by sales channel"""
        from workspace.store.models.sales_channel_model import ChannelOrder

        # Single query for all channel orders
        orders = ChannelOrder.objects.filter(
            sales_channel_id__in=channel_ids
        ).select_related('sales_channel', 'workspace').order_by('-created_at')

        # Group by channel_id
        orders_map = {}
        for order in orders:
            channel_id = str(order.sales_channel_id)
            if channel_id not in orders_map:
                orders_map[channel_id] = []
            orders_map[channel_id].append(order)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            orders_map.get(str(cid), []) for cid in channel_ids
        ])


class ActiveSalesChannelsByWorkspaceLoader(DataLoader):
    """
    Load active sales channels for multiple workspaces

    Performance: 1 query instead of N queries
    Example: Loading active channels for 5 workspaces = 1 query instead of 5
    """

    def batch_load_fn(self, workspace_ids):
        """Batch load active sales channels by workspace"""
        from workspace.store.models.sales_channel_model import SalesChannel

        # Single query for all workspaces
        channels = SalesChannel.objects.filter(
            workspace_id__in=workspace_ids,
            is_active=True
        ).select_related('workspace').order_by('name')

        # Group by workspace_id
        workspace_channels = {}
        for channel in channels:
            workspace_id = str(channel.workspace_id)
            if workspace_id not in workspace_channels:
                workspace_channels[workspace_id] = []
            workspace_channels[workspace_id].append(channel)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            workspace_channels.get(str(wid), []) for wid in workspace_ids
        ])


class SalesChannelStatsLoader(DataLoader):
    """
    Load sales channel statistics for multiple channels

    Performance: 1 aggregation query instead of N queries
    Example: Loading stats for 15 channels = 1 query instead of 15
    """

    def batch_load_fn(self, channel_ids):
        """Batch load sales channel stats"""
        from django.db.models import Count, Sum, Avg
        from workspace.store.models.sales_channel_model import ChannelProduct, ChannelOrder

        # Single aggregation query for all channels - products
        product_stats = ChannelProduct.objects.filter(
            sales_channel_id__in=channel_ids
        ).values('sales_channel_id').annotate(
            total_products=Count('id'),
            active_products=Count('id', filter=models.Q(is_visible=True)),
            products_needing_sync=Count('id', filter=models.Q(
                sync_inventory=True,
                last_synced_at__isnull=True
            ))
        )

        # Single aggregation query for all channels - orders
        order_stats = ChannelOrder.objects.filter(
            sales_channel_id__in=channel_ids
        ).values('sales_channel_id').annotate(
            total_orders=Count('id'),
            synced_orders=Count('id', filter=models.Q(is_synced=True)),
            pending_orders=Count('id', filter=models.Q(is_synced=False)),
            total_revenue=Sum('order_amount'),
            average_order_amount=Avg('order_amount')
        )

        # Create map of channel_id -> stats
        stats_map = {}

        # Process product stats
        for stat in product_stats:
            channel_id = str(stat['sales_channel_id'])
            if channel_id not in stats_map:
                stats_map[channel_id] = {}
            stats_map[channel_id].update({
                'total_products': stat['total_products'] or 0,
                'active_products': stat['active_products'] or 0,
                'products_needing_sync': stat['products_needing_sync'] or 0
            })

        # Process order stats
        for stat in order_stats:
            channel_id = str(stat['sales_channel_id'])
            if channel_id not in stats_map:
                stats_map[channel_id] = {}
            stats_map[channel_id].update({
                'total_orders': stat['total_orders'] or 0,
                'synced_orders': stat['synced_orders'] or 0,
                'pending_orders': stat['pending_orders'] or 0,
                'total_revenue': float(stat['total_revenue'] or 0),
                'average_order_amount': float(stat['average_order_amount'] or 0)
            })

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            stats_map.get(str(cid), {
                'total_products': 0,
                'active_products': 0,
                'products_needing_sync': 0,
                'total_orders': 0,
                'synced_orders': 0,
                'pending_orders': 0,
                'total_revenue': 0.0,
                'average_order_amount': 0.0
            }) for cid in channel_ids
        ])


class SalesChannelAnalyticsLoader(DataLoader):
    """
    Load sales channel analytics for multiple channels

    Performance: 1 aggregation query instead of N queries
    Example: Loading analytics for 10 channels = 1 query instead of 10
    """

    def batch_load_fn(self, channel_ids):
        """Batch load sales channel analytics"""
        from django.db.models import Count, Sum, Avg, Max, Min
        from django.utils import timezone
        from workspace.store.models.sales_channel_model import ChannelOrder

        # Get date range for analytics (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

        # Single aggregation query for all channels
        analytics = ChannelOrder.objects.filter(
            sales_channel_id__in=channel_ids,
            created_at__gte=thirty_days_ago
        ).values('sales_channel_id').annotate(
            orders_30_days=Count('id'),
            revenue_30_days=Sum('order_amount'),
            average_order_value=Avg('order_amount'),
            max_order_value=Max('order_amount'),
            min_order_value=Min('order_amount'),
            sync_success_rate=Avg(
                models.Case(
                    models.When(is_synced=True, then=1),
                    default=0,
                    output_field=models.FloatField()
                )
            )
        )

        # Create map of channel_id -> analytics
        analytics_map = {}
        for analytic in analytics:
            channel_id = str(analytic['sales_channel_id'])
            analytics_map[channel_id] = {
                'orders_30_days': analytic['orders_30_days'] or 0,
                'revenue_30_days': float(analytic['revenue_30_days'] or 0),
                'average_order_value': float(analytic['average_order_value'] or 0),
                'max_order_value': float(analytic['max_order_value'] or 0),
                'min_order_value': float(analytic['min_order_value'] or 0),
                'sync_success_rate': float(analytic['sync_success_rate'] or 0) * 100
            }

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            analytics_map.get(str(cid), {
                'orders_30_days': 0,
                'revenue_30_days': 0.0,
                'average_order_value': 0.0,
                'max_order_value': 0.0,
                'min_order_value': 0.0,
                'sync_success_rate': 0.0
            }) for cid in channel_ids
        ])