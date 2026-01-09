"""
Discount DataLoaders for N+1 Query Prevention

Critical for discount operations: Prevents N+1 queries
when loading discount usage, validation, and analytics data
"""

from promise import Promise
from promise.dataloader import DataLoader


class DiscountByIdLoader(DataLoader):
    """
    Load multiple discounts by ID in one query

    Performance: 1 query instead of N queries
    Example: Loading 10 discounts by ID = 1 query instead of 10
    """

    def batch_load_fn(self, discount_ids):
        """Batch load discounts by ID"""
        from workspace.store.models.discount_model import Discount

        # Single query for all discounts
        discounts = Discount.objects.filter(
            id__in=discount_ids
        ).select_related('workspace')

        # Create map of id -> discount
        discount_map = {str(discount.id): discount for discount in discounts}

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            discount_map.get(str(did)) for did in discount_ids
        ])


class DiscountByCodeLoader(DataLoader):
    """
    Load multiple discounts by code in one query

    Performance: 1 query instead of N queries
    Example: Loading 5 discounts by code = 1 query instead of 5
    """

    def batch_load_fn(self, discount_codes):
        """Batch load discounts by code"""
        from workspace.store.models.discount_model import Discount

        # Normalize codes for case-insensitive matching
        normalized_codes = [code.upper().strip() for code in discount_codes]

        # Single query for all discounts
        discounts = Discount.objects.filter(
            code__in=normalized_codes
        ).select_related('workspace')

        # Create map of normalized code -> discount
        discount_map = {discount.code: discount for discount in discounts}

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            discount_map.get(normalized_code) for normalized_code in normalized_codes
        ])


class DiscountUsageStatsLoader(DataLoader):
    """
    Load discount usage statistics for multiple discounts

    Performance: 1 aggregation query instead of N queries
    Example: Loading usage stats for 20 discounts = 1 query instead of 20
    """

    def batch_load_fn(self, discount_ids):
        """Batch load discount usage stats"""
        from django.db.models import Count, Avg, Sum, Max, Min
        from workspace.store.models.discount_model import DiscountUsage

        # Single aggregation query for all discounts
        stats = DiscountUsage.objects.filter(
            discount_id__in=discount_ids
        ).values('discount_id').annotate(
            total_usage=Count('id'),
            total_discount_amount=Sum('discount_amount'),
            average_discount_amount=Avg('discount_amount'),
            max_discount_amount=Max('discount_amount'),
            min_discount_amount=Min('discount_amount'),
            average_order_amount=Avg('order_amount'),
            last_used=Max('applied_at')
        )

        # Create map of discount_id -> stats
        stats_map = {}
        for stat in stats:
            discount_id = str(stat['discount_id'])
            stats_map[discount_id] = {
                'total_usage': stat['total_usage'] or 0,
                'total_discount_amount': float(stat['total_discount_amount'] or 0),
                'average_discount_amount': float(stat['average_discount_amount'] or 0),
                'max_discount_amount': float(stat['max_discount_amount'] or 0),
                'min_discount_amount': float(stat['min_discount_amount'] or 0),
                'average_order_amount': float(stat['average_order_amount'] or 0),
                'last_used': stat['last_used']
            }

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            stats_map.get(str(did), {
                'total_usage': 0,
                'total_discount_amount': 0.0,
                'average_discount_amount': 0.0,
                'max_discount_amount': 0.0,
                'min_discount_amount': 0.0,
                'average_order_amount': 0.0,
                'last_used': None
            }) for did in discount_ids
        ])


class CustomerDiscountUsageLoader(DataLoader):
    """
    Load discount usage count per customer for multiple discounts

    Performance: 1 aggregation query instead of N queries
    Example: Loading customer usage for 15 discounts = 1 query instead of 15
    """

    def batch_load_fn(self, discount_customer_pairs):
        """Batch load customer discount usage"""
        from django.db.models import Count
        from workspace.store.models.discount_model import DiscountUsage

        # Extract discount_ids and customer_ids
        discount_ids = [pair[0] for pair in discount_customer_pairs]
        customer_ids = [pair[1] for pair in discount_customer_pairs]

        # Single aggregation query for all discount-customer pairs
        usage_counts = DiscountUsage.objects.filter(
            discount_id__in=discount_ids,
            customer_id__in=customer_ids
        ).values('discount_id', 'customer_id').annotate(
            usage_count=Count('id')
        )

        # Create map of (discount_id, customer_id) -> usage_count
        usage_map = {}
        for usage in usage_counts:
            key = (str(usage['discount_id']), str(usage['customer_id']))
            usage_map[key] = usage['usage_count'] or 0

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            usage_map.get((str(pair[0]), str(pair[1])), 0)
            for pair in discount_customer_pairs
        ])


class ActiveDiscountsByWorkspaceLoader(DataLoader):
    """
    Load active discounts for multiple workspaces

    Performance: 1 query instead of N queries
    Example: Loading active discounts for 5 workspaces = 1 query instead of 5
    """

    def batch_load_fn(self, workspace_ids):
        """Batch load active discounts by workspace"""
        from django.utils import timezone
        from workspace.store.models.discount_model import Discount

        now = timezone.now()

        # Single query for all workspaces
        discounts = Discount.objects.filter(
            workspace_id__in=workspace_ids,
            status='active',
            starts_at__lte=now
        ).filter(
            models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
        ).select_related('workspace').order_by('-created_at')

        # Group by workspace_id
        workspace_discounts = {}
        for discount in discounts:
            workspace_id = str(discount.workspace_id)
            if workspace_id not in workspace_discounts:
                workspace_discounts[workspace_id] = []
            workspace_discounts[workspace_id].append(discount)

        # Return in requested order (DataLoader requirement)
        return Promise.resolve([
            workspace_discounts.get(str(wid), []) for wid in workspace_ids
        ])


class DiscountValidationLoader(DataLoader):
    """
    Validate multiple discount codes in one query

    Performance: 1 query instead of N queries
    Example: Validating 8 discount codes = 1 query instead of 8
    """

    def batch_load_fn(self, validation_requests):
        """Batch validate discount codes"""
        from django.utils import timezone
        from workspace.store.models.discount_model import Discount

        # Extract codes and workspace_ids
        codes = [req['code'] for req in validation_requests]
        workspace_ids = [req['workspace_id'] for req in validation_requests]

        # Normalize codes
        normalized_codes = [code.upper().strip() for code in codes]

        # Single query for all discounts
        discounts = Discount.objects.filter(
            workspace_id__in=workspace_ids,
            code__in=normalized_codes
        ).select_related('workspace')

        # Create map of (workspace_id, normalized_code) -> discount
        discount_map = {}
        for discount in discounts:
            key = (str(discount.workspace_id), discount.code)
            discount_map[key] = discount

        # Validate each request
        now = timezone.now()
        results = []

        for i, req in enumerate(validation_requests):
            key = (str(req['workspace_id']), normalized_codes[i])
            discount = discount_map.get(key)

            if not discount:
                results.append({
                    'is_valid': False,
                    'discount': None,
                    'message': 'Invalid discount code'
                })
                continue

            # Check if discount is active
            if not discount.is_active:
                results.append({
                    'is_valid': False,
                    'discount': discount,
                    'message': 'Discount is not active'
                })
                continue

            # Check customer eligibility if provided
            if req.get('customer') and not discount.can_apply_to_customer(req['customer']):
                results.append({
                    'is_valid': False,
                    'discount': discount,
                    'message': 'Discount not available for this customer'
                })
                continue

            # Check order requirements if provided
            if req.get('order_amount') and not discount.can_apply_to_order(req['order_amount'], req.get('customer')):
                results.append({
                    'is_valid': False,
                    'discount': discount,
                    'message': 'Order amount does not meet discount requirements'
                })
                continue

            # Valid discount
            results.append({
                'is_valid': True,
                'discount': discount,
                'message': 'Discount code is valid'
            })

        return Promise.resolve(results)