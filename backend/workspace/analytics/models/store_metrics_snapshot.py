"""
Store Metrics Snapshot Model

Pre-aggregated daily metrics for fast dashboard loading.
Computed from StoreEvent data via scheduled tasks or on-demand.

Design Principles:
- Performance: Pre-computed aggregates for O(1) dashboard queries
- Scalability: Daily snapshots reduce real-time computation load
- Reliability: Denormalized for read-heavy dashboard patterns
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import logging

logger = logging.getLogger('workspace.analytics.metrics')


class StoreMetricsSnapshot(models.Model):
    """
    Daily aggregated metrics for dashboard performance.
    
    Pre-computes key metrics from StoreEvent data to enable
    fast dashboard loading without expensive aggregation queries.
    
    Performance: Single row lookup per day
    Scalability: Grows linearly with days, not events
    """
    
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='metrics_snapshots',
        db_index=True,
        help_text="Store/workspace this snapshot belongs to"
    )
    date = models.DateField(
        db_index=True,
        help_text="Date this snapshot represents"
    )
    
    # BASIC Tier Metrics (MVP Essential)
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Sum of order_value from order_completed events"
    )
    total_orders = models.IntegerField(
        default=0,
        help_text="Count of order_completed events"
    )
    failed_orders = models.IntegerField(
        default=0,
        help_text="Count of order_failed events"
    )
    
    # Payment method breakdown (BASIC)
    payment_mobile_money = models.IntegerField(
        default=0,
        help_text="Orders paid via Mobile Money"
    )
    payment_cash_on_delivery = models.IntegerField(
        default=0,
        help_text="Orders paid via Cash on Delivery"
    )
    payment_card = models.IntegerField(
        default=0,
        help_text="Orders paid via Card"
    )
    payment_whatsapp = models.IntegerField(
        default=0,
        help_text="Orders via WhatsApp"
    )
    payment_bank_transfer = models.IntegerField(
        default=0,
        help_text="Orders paid via Bank Transfer"
    )
    
    # PRO Tier Metrics (Funnel/Conversion)
    page_views = models.IntegerField(
        default=0,
        help_text="Count of store_page_view events"
    )
    unique_sessions = models.IntegerField(
        default=0,
        help_text="Count of unique session_ids for the day"
    )
    product_views = models.IntegerField(
        default=0,
        help_text="Count of product_view events"
    )
    add_to_cart_count = models.IntegerField(
        default=0,
        help_text="Count of add_to_cart events"
    )
    checkout_started_count = models.IntegerField(
        default=0,
        help_text="Count of checkout_started events"
    )
    cart_abandoned_count = models.IntegerField(
        default=0,
        help_text="Count of cart_abandoned events"
    )
    
    # Customer metrics (PRO)
    new_customers = models.IntegerField(
        default=0,
        help_text="Count of customer_created events"
    )
    returning_customers = models.IntegerField(
        default=0,
        help_text="Count of customer_returned events"
    )
    
    # Computed rates (calculated on save)
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="(total_orders / page_views) * 100"
    )
    cart_abandonment_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="(cart_abandoned / checkout_started) * 100"
    )
    average_order_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="total_revenue / total_orders"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'workspace_analytics'
        db_table = 'analytics_store_metrics_snapshots'
        unique_together = ['workspace', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['workspace', '-date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.workspace_id} metrics - {self.date}"
    
    def save(self, *args, **kwargs):
        """Calculate derived rates before saving"""
        self._calculate_rates()
        super().save(*args, **kwargs)
    
    def _calculate_rates(self):
        """Calculate conversion and abandonment rates"""
        # Conversion rate: orders / page_views
        if self.page_views > 0:
            self.conversion_rate = Decimal(
                (self.total_orders / self.page_views) * 100
            ).quantize(Decimal('0.01'))
        else:
            self.conversion_rate = Decimal('0.00')
        
        # Cart abandonment rate: abandoned / checkout_started
        if self.checkout_started_count > 0:
            self.cart_abandonment_rate = Decimal(
                (self.cart_abandoned_count / self.checkout_started_count) * 100
            ).quantize(Decimal('0.01'))
        else:
            self.cart_abandonment_rate = Decimal('0.00')
        
        # Average order value
        if self.total_orders > 0:
            self.average_order_value = (
                self.total_revenue / self.total_orders
            ).quantize(Decimal('0.01'))
        else:
            self.average_order_value = Decimal('0.00')
    
    @classmethod
    def get_or_create_for_today(cls, workspace):
        """
        Get or create metrics snapshot for today.
        
        Returns:
            Tuple of (snapshot, created)
        """
        today = date.today()
        return cls.objects.get_or_create(
            workspace=workspace,
            date=today,
            defaults={
                'total_revenue': Decimal('0.00'),
                'total_orders': 0,
            }
        )
    
    @classmethod
    def get_range(cls, workspace, days: int = 30):
        """
        Get metrics for a date range.
        
        Args:
            workspace: Workspace instance
            days: Number of days to fetch (default 30)
            
        Returns:
            QuerySet of StoreMetricsSnapshot ordered by date desc
        """
        start_date = date.today() - timedelta(days=days)
        return cls.objects.filter(
            workspace=workspace,
            date__gte=start_date
        ).order_by('-date')
    
    def to_api_format(self, include_pro: bool = False):
        """
        Convert to API response format.
        
        Args:
            include_pro: Whether to include PRO tier metrics
            
        Returns:
            Dictionary with metrics data
        """
        result = {
            'date': self.date.isoformat(),
            'revenue': float(self.total_revenue),
            'orders': self.total_orders,
            'failed_orders': self.failed_orders,
            'average_order_value': float(self.average_order_value),
            'payment_breakdown': {
                'mobile_money': self.payment_mobile_money,
                'cash_on_delivery': self.payment_cash_on_delivery,
                'card': self.payment_card,
                'whatsapp': self.payment_whatsapp,
                'bank_transfer': self.payment_bank_transfer,
            }
        }
        
        if include_pro:
            result.update({
                'page_views': self.page_views,
                'unique_sessions': self.unique_sessions,
                'product_views': self.product_views,
                'add_to_cart': self.add_to_cart_count,
                'checkout_started': self.checkout_started_count,
                'cart_abandoned': self.cart_abandoned_count,
                'conversion_rate': float(self.conversion_rate),
                'abandonment_rate': float(self.cart_abandonment_rate),
                'new_customers': self.new_customers,
                'returning_customers': self.returning_customers,
            })
        
        return result
