"""
Store Event Model

Event-based analytics tracking for commerce intelligence.
Tracks customer journey events scoped by workspace + session.

Design Principles:
- Performance: Indexed queries for fast aggregation
- Scalability: Tier-gated event types based on analytics capability
- Reliability: Simple flat structure, no arrays or nested objects
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
from uuid import uuid4
import logging

logger = logging.getLogger('workspace.analytics.events')


class StoreEvent(models.Model):
    """
    Commerce event tracking model.
    
    Tracks customer money flow events per the analytics guide:
    - Scoped by workspace (store) + session_id
    - Tier-gated event types based on workspace analytics capability
    - Flat payload structure for efficient querying
    
    Performance: Proper indexing on workspace, event_type, created_at
    Scalability: Supports high-volume event ingestion
    """
    
    # Event taxonomy aligned with analytics guide
    EVENT_TYPES = [
        # BASIC - MVP Essential (analytics: basic+)
        ('order_completed', 'Order Completed'),
        ('order_failed', 'Order Failed'),
        ('store_page_view', 'Store Page View'),
        ('add_to_cart', 'Add to Cart'),
        
        # PRO - Gated Features (analytics: pro+)
        ('product_view', 'Product View'),
        ('checkout_started', 'Checkout Started'),
        ('customer_created', 'Customer Created'),
        ('cart_abandoned', 'Cart Abandoned'),
        
        # ADVANCED/ENTERPRISE - Future (analytics: advanced)
        ('customer_returned', 'Customer Returned'),
        ('coupon_applied', 'Coupon Applied'),
        ('order_refunded', 'Order Refunded'),
        ('delivery_completed', 'Delivery Completed'),
    ]
    
    # Maps event types to required analytics capability level
    # Aligns with plans.yaml: analytics: none/basic/pro/advanced
    EVENT_CAPABILITY_REQUIREMENTS = {
        # basic tier events
        'order_completed': 'basic',
        'order_failed': 'basic',
        'store_page_view': 'basic',
        'add_to_cart': 'basic',
        # pro tier events
        'product_view': 'pro',
        'checkout_started': 'pro',
        'customer_created': 'pro',
        'cart_abandoned': 'pro',
        # advanced tier events
        'customer_returned': 'advanced',
        'coupon_applied': 'advanced',
        'order_refunded': 'advanced',
        'delivery_completed': 'advanced',
    }
    
    # Analytics capability hierarchy (matches plans.yaml values)
    ANALYTICS_LEVELS = {
        'none': 0,
        'basic': 1,
        'pro': 2,
        'advanced': 3,
    }
    
    # Core identifiers (per analytics guide)
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='store_events',
        db_index=True,
        help_text="Store/workspace this event belongs to"
    )
    session_id = models.UUIDField(
        db_index=True,
        help_text="Customer session identifier (cookie-based, resets after order or 24h)"
    )
    
    # Event classification
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES,
        db_index=True,
        help_text="Event type from taxonomy"
    )
    
    # Order event fields (populated for order_completed, order_failed)
    order_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Order total amount"
    )
    items_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of items in order"
    )
    currency = models.CharField(
        max_length=3,
        default='XAF',
        help_text="Currency code (XAF for Cameroon)"
    )
    
    # Payment tracking
    PAYMENT_METHODS = [
        ('mobile_money', 'Mobile Money'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card'),
        ('whatsapp', 'WhatsApp Order'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        null=True,
        blank=True,
        help_text="Payment method used"
    )
    
    # Reference IDs for joining with other tables
    order_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to Order if applicable"
    )
    product_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to Product if applicable"
    )
    customer_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to Customer if applicable"
    )
    
    # Extensibility (kept minimal per guide - no arrays, no raw objects)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event context (kept minimal)"
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When event occurred"
    )
    
    class Meta:
        app_label = 'workspace_analytics'
        db_table = 'analytics_store_events'
        ordering = ['-created_at']
        indexes = [
            # Primary query patterns
            models.Index(fields=['workspace', '-created_at']),
            models.Index(fields=['workspace', 'event_type', '-created_at']),
            models.Index(fields=['workspace', 'session_id']),
            # Aggregation patterns
            models.Index(fields=['workspace', 'event_type', 'payment_method']),
            models.Index(fields=['workspace', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.workspace_id} - {self.event_type} - {self.created_at}"
    
    @classmethod
    def get_required_capability(cls, event_type: str) -> str:
        """
        Get required analytics capability for an event type.
        
        Args:
            event_type: Event type from taxonomy
            
        Returns:
            Required capability level (basic, pro, advanced)
        """
        return cls.EVENT_CAPABILITY_REQUIREMENTS.get(event_type, 'basic')
    
    @classmethod
    def can_track_event(cls, workspace, event_type: str) -> bool:
        """
        Check if workspace can track an event type based on analytics capability.
        
        Uses workspace.capabilities['analytics'] from plans.yaml
        
        Args:
            workspace: Workspace instance with capabilities JSONField
            event_type: Event type to check
            
        Returns:
            True if workspace has sufficient analytics capability
        """
        capabilities = workspace.capabilities or {}
        workspace_analytics = capabilities.get('analytics')
        
        # analytics: none means no tracking allowed
        if not workspace_analytics or workspace_analytics == 'none':
            return False
        
        required_capability = cls.get_required_capability(event_type)
        
        workspace_level = cls.ANALYTICS_LEVELS.get(workspace_analytics, 0)
        required_level = cls.ANALYTICS_LEVELS.get(required_capability, 1)
        
        return workspace_level >= required_level
    
    @classmethod
    def get_allowed_event_types(cls, workspace) -> list:
        """
        Get list of event types allowed for a workspace.
        
        Args:
            workspace: Workspace instance
            
        Returns:
            List of allowed event type strings
        """
        capabilities = workspace.capabilities or {}
        workspace_analytics = capabilities.get('analytics')
        
        if not workspace_analytics or workspace_analytics == 'none':
            return []
        
        workspace_level = cls.ANALYTICS_LEVELS.get(workspace_analytics, 0)
        
        allowed = []
        for event_type, required_cap in cls.EVENT_CAPABILITY_REQUIREMENTS.items():
            required_level = cls.ANALYTICS_LEVELS.get(required_cap, 1)
            if workspace_level >= required_level:
                allowed.append(event_type)
        
        return allowed
    
    @classmethod
    def get_basic_event_types(cls) -> list:
        """Get list of basic tier event types"""
        return [k for k, v in cls.EVENT_CAPABILITY_REQUIREMENTS.items() if v == 'basic']
    
    @classmethod
    def get_pro_event_types(cls) -> list:
        """Get list of pro tier event types (includes basic)"""
        return [k for k, v in cls.EVENT_CAPABILITY_REQUIREMENTS.items() if v in ('basic', 'pro')]
    
    @classmethod
    def get_advanced_event_types(cls) -> list:
        """Get list of advanced tier event types (all events)"""
        return list(cls.EVENT_CAPABILITY_REQUIREMENTS.keys())
