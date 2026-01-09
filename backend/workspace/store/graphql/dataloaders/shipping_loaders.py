"""
Shipping DataLoaders for N+1 Query Prevention

Critical for shipping operations: Prevents N+1 queries
when loading shipping zones, rates, and cost calculations
"""

from promise import Promise
from promise.dataloader import DataLoader


class ShippingZoneByIdLoader(DataLoader):
    """
    Load multiple shipping zones by ID in one query

    Performance: 1 query instead of N queries
    Example: Loading 10 shipping zones by ID = 1 query instead of 10
    """

    def batch_load_fn(self, zone_ids):
        """Batch load shipping zones by ID"""
        from workspace.store.models.shipping_model import ShippingZone

        # Single query for all shipping zones
        zones = ShippingZone.objects.filter(
            id__in=zone_ids
        ).select_related('workspace')

        # Create map of id -> zone
        zone_map = {str(zone.id): zone for zone in zones}

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            zone_map.get(str(zid)) for zid in zone_ids
        ])


class ShippingRatesByZoneLoader(DataLoader):
    """
    Load shipping rates for multiple zones in one query

    Performance: 1 query instead of N queries
    Example: Loading rates for 8 zones = 1 query instead of 8
    """

    def batch_load_fn(self, zone_ids):
        """Batch load shipping rates by zone"""
        from workspace.store.models.shipping_model import ShippingRate

        # Single query for all rates
        rates = ShippingRate.objects.filter(
            shipping_zone_id__in=zone_ids,
            is_active=True
        ).select_related('shipping_zone').order_by('weight_min')

        # Group by zone_id
        rates_map = {}
        for rate in rates:
            zone_id = str(rate.shipping_zone_id)
            if zone_id not in rates_map:
                rates_map[zone_id] = []
            rates_map[zone_id].append(rate)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            rates_map.get(str(zid), []) for zid in zone_ids
        ])


class ShippingMethodsByWorkspaceLoader(DataLoader):
    """
    Load shipping methods for multiple workspaces

    Performance: 1 query instead of N queries
    Example: Loading methods for 5 workspaces = 1 query instead of 5
    """

    def batch_load_fn(self, workspace_ids):
        """Batch load shipping methods by workspace"""
        from workspace.store.models.shipping_model import ShippingMethod

        # Single query for all workspaces
        methods = ShippingMethod.objects.filter(
            workspace_id__in=workspace_ids,
            is_active=True
        ).select_related('workspace').order_by('name')

        # Group by workspace_id
        workspace_methods = {}
        for method in methods:
            workspace_id = str(method.workspace_id)
            if workspace_id not in workspace_methods:
                workspace_methods[workspace_id] = []
            workspace_methods[workspace_id].append(method)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            workspace_methods.get(str(wid), []) for wid in workspace_ids
        ])


class ShippingCostCalculatorLoader(DataLoader):
    """
    Calculate shipping costs for multiple orders in one query

    Performance: 1 query instead of N queries
    Example: Calculating costs for 12 orders = 1 query instead of 12
    """

    def batch_load_fn(self, shipping_requests):
        """Batch calculate shipping costs"""
        from workspace.store.models.shipping_model import ShippingZone, ShippingRate

        # Extract region and weight from requests
        regions = [req['region'] for req in shipping_requests]
        weights = [req['weight'] for req in shipping_requests]
        amounts = [req.get('order_amount', 0) for req in shipping_requests]

        # Single query for all applicable zones
        zones = ShippingZone.objects.filter(
            regions__overlap=regions,
            is_active=True
        ).prefetch_related('shipping_rates')

        # Create map of region -> zones
        region_zones = {}
        for zone in zones:
            for region in zone.regions:
                if region not in region_zones:
                    region_zones[region] = []
                region_zones[region].append(zone)

        # Calculate costs for each request
        results = []
        for i, req in enumerate(shipping_requests):
            region = req['region']
            weight = req['weight']
            order_amount = req.get('order_amount', 0)

            applicable_zones = region_zones.get(region, [])
            best_rate = None
            best_cost = float('inf')

            for zone in applicable_zones:
                for rate in zone.rates.all():
                    if rate.is_active and rate.weight_min <= weight <= rate.weight_max:
                        cost = rate.calculate_shipping_cost(order_amount, weight)
                        if cost is not None and cost < best_cost:
                            best_cost = cost
                            best_rate = rate

            if best_rate:
                results.append({
                    'shipping_cost': best_cost,
                    'shipping_rate': best_rate,
                    'shipping_zone': best_rate.shipping_zone,
                    'estimated_days': best_rate.estimated_days,
                    'message': 'Shipping cost calculated successfully'
                })
            else:
                results.append({
                    'shipping_cost': None,
                    'shipping_rate': None,
                    'shipping_zone': None,
                    'estimated_days': None,
                    'message': 'No shipping rates available for this region and weight'
                })

        return Promise.resolve(results)


class ShippingZoneStatsLoader(DataLoader):
    """
    Load shipping zone statistics for multiple zones

    Performance: 1 aggregation query instead of N queries
    Example: Loading stats for 15 zones = 1 query instead of 15
    """

    def batch_load_fn(self, zone_ids):
        """Batch load shipping zone stats"""
        from django.db.models import Count, Q
        from workspace.store.models.shipping_model import ShippingRate

        # Single aggregation query for all zones
        stats = ShippingRate.objects.filter(
            shipping_zone_id__in=zone_ids
        ).values('shipping_zone_id').annotate(
            total_rates=Count('id'),
            active_rates=Count('id', filter=models.Q(is_active=True))
        )

        # Create map of zone_id -> stats
        stats_map = {}
        for stat in stats:
            zone_id = str(stat['shipping_zone_id'])
            stats_map[zone_id] = {
                'total_rates': stat['total_rates'] or 0,
                'active_rates': stat['active_rates'] or 0
            }

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            stats_map.get(str(zid), {
                'total_rates': 0,
                'active_rates': 0
            }) for zid in zone_ids
        ])