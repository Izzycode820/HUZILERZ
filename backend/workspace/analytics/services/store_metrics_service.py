"""
Store Metrics Service

Computes analytics metrics from StoreEvent data.
Provides tier-gated access to analytics features.

Design Principles:
- Performance: Caching with configurable TTL, optimized aggregations
- Scalability: Uses pre-computed snapshots where available
- Reliability: Graceful fallback to real-time computation
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import date, timedelta
from django.db import models
from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncDate
from django.core.cache import cache
from django.utils import timezone
import logging

from workspace.core.models import Workspace
from subscription.services.gating import (
    check_analytics_capability,
    get_analytics_level,
    ANALYTICS_LEVELS
)
from ..models import StoreEvent, StoreMetricsSnapshot

logger = logging.getLogger('workspace.analytics.metrics')

# Cache timeout constants (in seconds)
CACHE_TIMEOUTS = {
    'dashboard_full': 300,      # 5 min - full dashboard
    'metrics_cards': 60,        # 1 min - cards/KPIs
    'chart_data': 180,          # 3 min - time-series
    'funnel_data': 120,         # 2 min - conversion funnel
}


class StoreMetricsService:
    """
    Store analytics metrics computation service.
    
    Computes analytics from StoreEvent data with tier-gated access.
    Uses caching for performance and StoreMetricsSnapshot for efficiency.
    
    Usage:
        service = StoreMetricsService(workspace)
        cards = service.get_dashboard_cards(days=30)
        
    Performance: Caching with configurable TTL
    Scalability: Pre-computed snapshots for frequent queries
    """
    
    def __init__(self, workspace: Workspace):
        """
        Initialize metrics service for a workspace.
        
        Args:
            workspace: Workspace instance with capabilities JSONField
        """
        if not isinstance(workspace, Workspace):
            raise TypeError(f"Expected Workspace instance, got {type(workspace)}")
        
        self.workspace = workspace
        self.analytics_level = get_analytics_level(workspace)
    
    def _get_cache_key(self, metric_type: str, **params) -> str:
        """Generate cache key for a metric query"""
        param_str = '_'.join(f"{k}:{v}" for k, v in sorted(params.items()))
        return f"analytics:{self.workspace.id}:{metric_type}:{param_str}"
    
    def _get_date_range(self, days: int) -> Tuple[date, date]:
        """Calculate date range for queries"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    
    def _validate_days(self, days: int) -> int:
        """Validate and clamp days parameter"""
        try:
            days = int(days)
            return max(1, min(days, 365))
        except (ValueError, TypeError):
            return 30
    
    # =========================================================================
    # BASIC Tier Methods - analytics: basic+
    # =========================================================================
    
    def get_dashboard_cards(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get dashboard metric cards - BASIC tier.
        
        Returns 4 cards: Revenue, Orders, Customers, Growth Rate
        
        Args:
            days: Number of days for metrics
            
        Returns:
            List of card dictionaries with title, value, trend, trend_direction
        """
        days = self._validate_days(days)
        
        # Check cache
        cache_key = self._get_cache_key('cards', days=days)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        start_date, end_date = self._get_date_range(days)
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            timezone.datetime.combine(end_date, timezone.datetime.max.time())
        )
        
        # Current period metrics from events
        current_events = StoreEvent.objects.filter(
            workspace=self.workspace,
            event_type='order_completed',
            created_at__range=(start_datetime, end_datetime)
        )
        
        current_revenue = current_events.aggregate(
            total=Sum('order_value')
        )['total'] or Decimal('0.00')
        
        current_orders = current_events.count()
        
        current_customers = current_events.values('customer_id').distinct().count()
        
        # Previous period for growth calculation
        prev_start = start_date - timedelta(days=days)
        prev_start_datetime = timezone.make_aware(
            timezone.datetime.combine(prev_start, timezone.datetime.min.time())
        )
        
        previous_events = StoreEvent.objects.filter(
            workspace=self.workspace,
            event_type='order_completed',
            created_at__range=(prev_start_datetime, start_datetime)
        )
        
        previous_revenue = previous_events.aggregate(
            total=Sum('order_value')
        )['total'] or Decimal('0.00')
        
        previous_orders = previous_events.count()
        previous_customers = previous_events.values('customer_id').distinct().count()
        
        # Calculate growth percentages
        revenue_growth = self._calculate_growth(float(current_revenue), float(previous_revenue))
        orders_growth = self._calculate_growth(current_orders, previous_orders)
        customers_growth = self._calculate_growth(current_customers, previous_customers)
        overall_growth = (revenue_growth + orders_growth + customers_growth) / 3
        
        cards = [
            {
                'title': 'Total Revenue',
                'value': f'{float(current_revenue):,.0f} XAF',
                'trend': f'{revenue_growth:+.1f}%',
                'trend_direction': 'up' if revenue_growth >= 0 else 'down'
            },
            {
                'title': 'Total Orders',
                'value': f'{current_orders:,}',
                'trend': f'{orders_growth:+.1f}%',
                'trend_direction': 'up' if orders_growth >= 0 else 'down'
            },
            {
                'title': 'Customers',
                'value': f'{current_customers:,}',
                'trend': f'{customers_growth:+.1f}%',
                'trend_direction': 'up' if customers_growth >= 0 else 'down'
            },
            {
                'title': 'Growth Rate',
                'value': f'{overall_growth:.1f}%',
                'trend': f'{overall_growth:+.1f}%',
                'trend_direction': 'up' if overall_growth >= 0 else 'down'
            }
        ]
        
        cache.set(cache_key, cards, CACHE_TIMEOUTS['metrics_cards'])
        return cards
    
    def get_payment_breakdown(self, days: int = 30) -> Dict[str, int]:
        """
        Get payment method breakdown - BASIC tier.
        
        Args:
            days: Number of days for analysis
            
        Returns:
            Dictionary with payment method counts
        """
        days = self._validate_days(days)
        start_date, end_date = self._get_date_range(days)
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        
        breakdown = StoreEvent.objects.filter(
            workspace=self.workspace,
            event_type='order_completed',
            created_at__gte=start_datetime
        ).values('payment_method').annotate(
            count=Count('id')
        )
        
        result = {
            'mobile_money': 0,
            'cash_on_delivery': 0,
            'card': 0,
            'whatsapp': 0,
            'bank_transfer': 0,
        }
        
        for item in breakdown:
            method = item['payment_method']
            if method in result:
                result[method] = item['count']
        
        return result
    
    def get_chart_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Get time-series chart data - BASIC tier.
        
        Returns daily orders and revenue for charting.
        
        Args:
            days: Number of days for chart
            
        Returns:
            Dictionary with data points and chart config
        """
        days = self._validate_days(days)
        
        # Check cache
        cache_key = self._get_cache_key('chart', days=days)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        start_date, end_date = self._get_date_range(days)
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        
        # Aggregate orders by date
        daily_data = StoreEvent.objects.filter(
            workspace=self.workspace,
            event_type='order_completed',
            created_at__gte=start_datetime
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            orders=Count('id'),
            revenue=Sum('order_value')
        ).order_by('date')
        
        # Convert to dict for O(1) lookup
        data_by_date = {
            item['date']: {
                'orders': item['orders'],
                'revenue': float(item['revenue'] or 0)
            }
            for item in daily_data
        }
        
        # Build complete date range with zeros for missing days
        chart_data = []
        current_date = start_date
        while current_date <= end_date:
            day_data = data_by_date.get(current_date, {'orders': 0, 'revenue': 0})
            chart_data.append({
                'date': current_date.isoformat(),
                'orders': day_data['orders'],
                'revenue': day_data['revenue']
            })
            current_date += timedelta(days=1)
        
        result = {
            'data': chart_data,
            'config': {
                'orders': {
                    'label': 'Orders',
                    'color': 'var(--primary)'
                },
                'revenue': {
                    'label': 'Revenue (XAF)',
                    'color': 'var(--secondary)'
                }
            }
        }
        
        cache.set(cache_key, result, CACHE_TIMEOUTS['chart_data'])
        return result
    
    # =========================================================================
    # PRO Tier Methods - analytics: pro+
    # =========================================================================
    
    def get_conversion_funnel(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get conversion funnel - PRO tier.
        
        Funnel: Page View -> Add to Cart -> Checkout -> Order
        
        Args:
            days: Number of days for analysis
            
        Returns:
            Funnel data or None if not authorized
        """
        # Check tier
        allowed, error = check_analytics_capability(self.workspace, 'pro')
        if not allowed:
            logger.debug(f"Funnel gated for workspace {self.workspace.id}")
            return None
        
        days = self._validate_days(days)
        
        # Check cache
        cache_key = self._get_cache_key('funnel', days=days)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        start_date, end_date = self._get_date_range(days)
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        
        # Count each funnel stage
        base_qs = StoreEvent.objects.filter(
            workspace=self.workspace,
            created_at__gte=start_datetime
        )
        
        page_views = base_qs.filter(event_type='store_page_view').count()
        add_to_cart = base_qs.filter(event_type='add_to_cart').count()
        checkout_started = base_qs.filter(event_type='checkout_started').count()
        orders = base_qs.filter(event_type='order_completed').count()
        abandoned = base_qs.filter(event_type='cart_abandoned').count()
        
        # Calculate rates
        conversion_rate = (orders / page_views * 100) if page_views > 0 else 0
        cart_rate = (add_to_cart / page_views * 100) if page_views > 0 else 0
        checkout_rate = (checkout_started / add_to_cart * 100) if add_to_cart > 0 else 0
        abandonment_rate = (abandoned / checkout_started * 100) if checkout_started > 0 else 0
        
        funnel = {
            'stages': [
                {'name': 'Page Views', 'count': page_views, 'rate': 100.0},
                {'name': 'Add to Cart', 'count': add_to_cart, 'rate': round(cart_rate, 1)},
                {'name': 'Checkout Started', 'count': checkout_started, 'rate': round(checkout_rate, 1)},
                {'name': 'Orders Completed', 'count': orders, 'rate': round(conversion_rate, 1)},
            ],
            'metrics': {
                'conversion_rate': round(conversion_rate, 2),
                'abandonment_rate': round(abandonment_rate, 2),
                'cart_abandoned': abandoned,
            }
        }
        
        cache.set(cache_key, funnel, CACHE_TIMEOUTS['funnel_data'])
        return funnel
    
    def get_customer_metrics(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get customer analytics - PRO tier.
        
        Returns new vs returning customers metrics.
        
        Args:
            days: Number of days for analysis
            
        Returns:
            Customer metrics or None if not authorized
        """
        allowed, error = check_analytics_capability(self.workspace, 'pro')
        if not allowed:
            return None
        
        days = self._validate_days(days)
        start_date, end_date = self._get_date_range(days)
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        
        base_qs = StoreEvent.objects.filter(
            workspace=self.workspace,
            created_at__gte=start_datetime
        )
        
        new_customers = base_qs.filter(event_type='customer_created').count()
        returning = base_qs.filter(event_type='customer_returned').count()
        
        return {
            'new_customers': new_customers,
            'returning_customers': returning,
            'total': new_customers + returning,
            'new_rate': round(
                (new_customers / (new_customers + returning) * 100)
                if (new_customers + returning) > 0 else 0, 1
            )
        }
    
    # =========================================================================
    # Dashboard Methods
    # =========================================================================
    
    def get_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Get complete dashboard data.
        
        Returns tier-appropriate data based on workspace capabilities.
        
        Args:
            days: Number of days for metrics
            
        Returns:
            Complete dashboard data dictionary
        """
        days = self._validate_days(days)
        
        # Check base analytics access
        allowed, error = check_analytics_capability(self.workspace, 'basic')
        if not allowed:
            return {
                'error': error,
                'has_access': False,
                'required_plan': 'Free',  # Basic analytics available on Free tier and above
                'analytics_level': self.analytics_level,  # Required by GraphQL schema
                'generated_at': timezone.now().isoformat(),
            }
        
        # Always include BASIC data
        result = {
            'has_access': True,
            'analytics_level': self.analytics_level,
            'cards': self.get_dashboard_cards(days),
            'chart': self.get_chart_data(days),
            'payment_breakdown': self.get_payment_breakdown(days),
            'generated_at': timezone.now().isoformat(),
        }

        
        # Add PRO data if available
        if self.analytics_level in ('pro', 'advanced'):
            result['funnel'] = self.get_conversion_funnel(days)
            result['customers'] = self.get_customer_metrics(days)
        else:
            result['funnel'] = None
            result['customers'] = None
        
        return result
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def _calculate_growth(self, current: float, previous: float) -> float:
        """Calculate percentage growth between periods"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / abs(previous)) * 100, 1)
    
    def invalidate_cache(self):
        """Invalidate all cached analytics for this workspace"""
        patterns = ['cards', 'chart', 'funnel']
        for pattern in patterns:
            for days in [7, 14, 30, 90]:
                cache_key = self._get_cache_key(pattern, days=days)
                cache.delete(cache_key)
        
        logger.debug(f"Invalidated analytics cache for workspace {self.workspace.id}")
    
    def has_analytics_access(self, level: str = 'basic') -> bool:
        """Check if workspace has analytics access at specified level"""
        allowed, _ = check_analytics_capability(self.workspace, level)
        return allowed
