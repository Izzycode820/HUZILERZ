"""
Event Tracking Service

Central analytics entry point following the analytics guide architecture.
All event tracking goes through trackStoreEvent().
Plan gating happens HERE, not in UI.

Dual-Tracking:
- First-party analytics: Our database (StoreEvent)
- PostHog: Advanced analytics, funnels, session replay

Design Principles:
- Performance: Async event creation, minimal overhead on critical paths
- Scalability: Tier-gated tracking based on workspace capabilities
- Reliability: Graceful degradation, never blocks order flow
"""

from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
import logging

from workspace.core.models import Workspace
from subscription.services.gating import check_analytics_capability, get_analytics_level
from ..models import StoreEvent, StoreMetricsSnapshot
from .posthog_service import get_posthog_service

logger = logging.getLogger('workspace.analytics.tracking')


class EventTrackingService:
    """
    Central analytics event tracking service.
    
    All event tracking goes through this service.
    Plan gating based on workspace.capabilities['analytics'] happens here.
    
    Dual-Tracking:
    - Saves events to our database (StoreEvent)
    - Sends events to PostHog for advanced analytics
    
    Usage:
        service = EventTrackingService(workspace)
        service.track_order_completed(order, session_id)
        
    Performance: Non-blocking event creation
    Scalability: Events gated by analytics capability level
    """
    
    def __init__(self, workspace: Workspace):
        """
        Initialize tracking service for a workspace.
        
        Args:
            workspace: Workspace instance with capabilities JSONField
        """
        if not isinstance(workspace, Workspace):
            raise TypeError(f"Expected Workspace instance, got {type(workspace)}")
        
        self.workspace = workspace
        self.analytics_level = get_analytics_level(workspace)
        self.posthog = get_posthog_service()

    
    def track_store_event(
        self,
        event_type: str,
        session_id: UUID,
        payload: Optional[Dict[str, Any]] = None
    ) -> Optional[StoreEvent]:
        """
        Main tracking method - central entry point per analytics guide.
        
        All tracking goes through this method. Plan gating happens here,
        not in UI or other services.
        
        Dual-tracks to:
        1. Our database (StoreEvent) - first-party analytics
        2. PostHog - advanced analytics, funnels, session replay
        
        Args:
            event_type: Event from taxonomy (order_completed, etc.)
            session_id: Customer session identifier
            payload: Event-specific data (order_value, items_count, etc.)
            
        Returns:
            StoreEvent instance if tracked, None if gated or failed
            
        Reliability: Never raises exceptions - logs and returns None on failure
        """
        payload = payload or {}
        
        try:
            # Check if workspace can track this event type
            if not StoreEvent.can_track_event(self.workspace, event_type):
                logger.debug(
                    f"Event {event_type} gated for workspace {self.workspace.id} "
                    f"(analytics: {self.analytics_level})"
                )
                return None
            
            # Validate event type
            valid_types = [t[0] for t in StoreEvent.EVENT_TYPES]
            if event_type not in valid_types:
                logger.warning(f"Unknown event type: {event_type}")
                return None
            
            # Create event in our database (first-party analytics)
            event = StoreEvent.objects.create(
                workspace=self.workspace,
                session_id=session_id,
                event_type=event_type,
                order_value=payload.get('order_value'),
                items_count=payload.get('items_count'),
                currency=payload.get('currency', 'XAF'),
                payment_method=payload.get('payment_method'),
                order_id=payload.get('order_id'),
                product_id=payload.get('product_id'),
                customer_id=payload.get('customer_id'),
                metadata=payload.get('metadata', {})
            )
            
            # Also send to PostHog for advanced analytics (non-blocking)
            self._send_to_posthog(event_type, session_id, payload)
            
            logger.debug(
                f"Tracked {event_type} for workspace {self.workspace.id} "
                f"(session: {session_id})"
            )
            
            return event
            
        except Exception as e:
            # Never fail order flow due to analytics
            logger.error(
                f"Failed to track {event_type} for workspace {self.workspace.id}: {e}",
                exc_info=True
            )
            return None
    
    def _send_to_posthog(
        self,
        event_type: str,
        session_id: UUID,
        payload: Dict[str, Any]
    ):
        """
        Send event to PostHog (internal helper).
        
        Non-blocking - failures don't affect our DB tracking.
        Uses workspace_id as distinctId per PostHog guide.
        
        Args:
            event_type: Event name
            session_id: Session UUID
            payload: Event payload
        """
        try:
            # Build PostHog properties
            posthog_properties = {
                'session_id': str(session_id),
                'analytics_level': self.analytics_level,
            }
            
            # Add numeric/string fields from payload
            if payload.get('order_value'):
                posthog_properties['order_value'] = float(payload['order_value'])
            if payload.get('items_count'):
                posthog_properties['items_count'] = payload['items_count']
            if payload.get('currency'):
                posthog_properties['currency'] = payload['currency']
            if payload.get('payment_method'):
                posthog_properties['payment_method'] = payload['payment_method']
            if payload.get('product_id'):
                posthog_properties['product_id'] = str(payload['product_id'])
            if payload.get('customer_id'):
                posthog_properties['customer_id'] = str(payload['customer_id'])
            
            # Add metadata
            if payload.get('metadata'):
                posthog_properties.update(payload['metadata'])
            
            # Send to PostHog
            self.posthog.capture_event(
                workspace_id=self.workspace.id,
                event_name=event_type,
                properties=posthog_properties,
                session_id=session_id
            )
            
        except Exception as e:
            # Log but don't raise - PostHog failures shouldn't break tracking
            logger.warning(f"PostHog tracking failed for {event_type}: {e}")
    
    # =========================================================================
    # BASIC Tier Events - Available for analytics: basic+
    # =========================================================================
    
    def track_order_completed(
        self,
        order,
        session_id: Optional[UUID] = None
    ) -> Optional[StoreEvent]:
        """
        Track successful order completion - BASIC tier.
        
        Args:
            order: Order instance
            session_id: Customer session (auto-generated if not provided)
            
        Returns:
            StoreEvent if tracked
        """
        if session_id is None:
            session_id = uuid4()
        
        return self.track_store_event(
            event_type='order_completed',
            session_id=session_id,
            payload={
                'order_value': order.total_amount,
                'items_count': order.item_count,
                'currency': order.currency,
                'payment_method': order.payment_method,
                'order_id': order.id,
                'customer_id': getattr(order.customer, 'id', None) if order.customer else None,
            }
        )
    
    def track_order_failed(
        self,
        order,
        session_id: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> Optional[StoreEvent]:
        """
        Track failed order - BASIC tier.
        
        Args:
            order: Order instance
            session_id: Customer session
            reason: Failure reason for metadata
            
        Returns:
            StoreEvent if tracked
        """
        if session_id is None:
            session_id = uuid4()
        
        return self.track_store_event(
            event_type='order_failed',
            session_id=session_id,
            payload={
                'order_value': order.total_amount,
                'order_id': order.id,
                'metadata': {'reason': reason} if reason else {}
            }
        )
    
    def track_page_view(
        self,
        session_id: UUID,
        page_type: str = 'home'
    ) -> Optional[StoreEvent]:
        """
        Track store page view - BASIC tier.
        
        Args:
            session_id: Customer session
            page_type: Type of page (home, product, collection, etc.)
            
        Returns:
            StoreEvent if tracked
        """
        return self.track_store_event(
            event_type='store_page_view',
            session_id=session_id,
            payload={
                'metadata': {'page_type': page_type}
            }
        )
    
    def track_add_to_cart(
        self,
        session_id: UUID,
        product_id: UUID,
        quantity: int = 1,
        variant_id: Optional[UUID] = None
    ) -> Optional[StoreEvent]:
        """
        Track add to cart action - BASIC tier.
        
        Args:
            session_id: Customer session
            product_id: Product being added
            quantity: Quantity added
            variant_id: Optional variant ID
            
        Returns:
            StoreEvent if tracked
        """
        return self.track_store_event(
            event_type='add_to_cart',
            session_id=session_id,
            payload={
                'product_id': product_id,
                'items_count': quantity,
                'metadata': {'variant_id': str(variant_id)} if variant_id else {}
            }
        )
    
    # =========================================================================
    # PRO Tier Events - Available for analytics: pro+
    # =========================================================================
    
    def track_product_view(
        self,
        session_id: UUID,
        product_id: UUID
    ) -> Optional[StoreEvent]:
        """
        Track product detail view - PRO tier.
        
        Args:
            session_id: Customer session
            product_id: Product being viewed
            
        Returns:
            StoreEvent if tracked
        """
        return self.track_store_event(
            event_type='product_view',
            session_id=session_id,
            payload={'product_id': product_id}
        )
    
    def track_checkout_started(
        self,
        session_id: UUID,
        cart_value: Decimal,
        items_count: int
    ) -> Optional[StoreEvent]:
        """
        Track checkout initiation - PRO tier.
        
        Args:
            session_id: Customer session
            cart_value: Total cart value
            items_count: Number of items in cart
            
        Returns:
            StoreEvent if tracked
        """
        return self.track_store_event(
            event_type='checkout_started',
            session_id=session_id,
            payload={
                'order_value': cart_value,
                'items_count': items_count,
                'currency': 'XAF'
            }
        )
    
    def track_customer_created(
        self,
        session_id: UUID,
        customer_id: UUID,
        is_first_order: bool = True
    ) -> Optional[StoreEvent]:
        """
        Track new customer creation - PRO tier.
        
        Args:
            session_id: Customer session
            customer_id: New customer ID
            is_first_order: Whether this is from first order
            
        Returns:
            StoreEvent if tracked
        """
        return self.track_store_event(
            event_type='customer_created',
            session_id=session_id,
            payload={
                'customer_id': customer_id,
                'metadata': {'is_first_order': is_first_order}
            }
        )
    
    def track_cart_abandoned(
        self,
        session_id: UUID,
        cart_value: Decimal,
        items_count: int
    ) -> Optional[StoreEvent]:
        """
        Track cart abandonment - PRO tier.
        
        Called when checkout started but not completed within threshold.
        
        Args:
            session_id: Customer session
            cart_value: Abandoned cart value
            items_count: Number of items in abandoned cart
            
        Returns:
            StoreEvent if tracked
        """
        return self.track_store_event(
            event_type='cart_abandoned',
            session_id=session_id,
            payload={
                'order_value': cart_value,
                'items_count': items_count,
                'currency': 'XAF'
            }
        )
    
    # =========================================================================
    # ADVANCED/ENTERPRISE Tier Events - Available for analytics: advanced
    # =========================================================================
    
    def track_customer_returned(
        self,
        session_id: UUID,
        customer_id: UUID,
        days_since_last_order: int
    ) -> Optional[StoreEvent]:
        """
        Track returning customer - ADVANCED tier.
        
        Args:
            session_id: Customer session
            customer_id: Returning customer ID
            days_since_last_order: Days since their last order
            
        Returns:
            StoreEvent if tracked
        """
        return self.track_store_event(
            event_type='customer_returned',
            session_id=session_id,
            payload={
                'customer_id': customer_id,
                'metadata': {'days_since_last_order': days_since_last_order}
            }
        )
    
    def track_coupon_applied(
        self,
        session_id: UUID,
        coupon_code: str,
        discount_value: Decimal
    ) -> Optional[StoreEvent]:
        """
        Track coupon application - ADVANCED tier.
        
        Args:
            session_id: Customer session
            coupon_code: Applied coupon code
            discount_value: Discount amount
            
        Returns:
            StoreEvent if tracked
        """
        return self.track_store_event(
            event_type='coupon_applied',
            session_id=session_id,
            payload={
                'order_value': discount_value,
                'metadata': {'coupon_code': coupon_code}
            }
        )
    
    def track_order_refunded(
        self,
        order,
        session_id: Optional[UUID] = None,
        refund_amount: Optional[Decimal] = None
    ) -> Optional[StoreEvent]:
        """
        Track order refund - ADVANCED tier.
        
        Args:
            order: Order being refunded
            session_id: Customer session
            refund_amount: Amount refunded (defaults to order total)
            
        Returns:
            StoreEvent if tracked
        """
        if session_id is None:
            session_id = uuid4()
        
        return self.track_store_event(
            event_type='order_refunded',
            session_id=session_id,
            payload={
                'order_value': refund_amount or order.total_amount,
                'order_id': order.id,
                'customer_id': getattr(order.customer, 'id', None) if order.customer else None,
            }
        )
    
    def track_delivery_completed(
        self,
        order,
        session_id: Optional[UUID] = None
    ) -> Optional[StoreEvent]:
        """
        Track delivery completion - ADVANCED tier.
        
        Args:
            order: Delivered order
            session_id: Customer session
            
        Returns:
            StoreEvent if tracked
        """
        if session_id is None:
            session_id = uuid4()
        
        return self.track_store_event(
            event_type='delivery_completed',
            session_id=session_id,
            payload={
                'order_value': order.total_amount,
                'order_id': order.id,
                'customer_id': getattr(order.customer, 'id', None) if order.customer else None,
            }
        )
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_session_events(
        self,
        session_id: UUID,
        event_types: Optional[list] = None
    ) -> list:
        """
        Get all events for a session.
        
        Args:
            session_id: Session to query
            event_types: Optional filter by event types
            
        Returns:
            List of StoreEvent instances
        """
        queryset = StoreEvent.objects.filter(
            workspace=self.workspace,
            session_id=session_id
        )
        
        if event_types:
            queryset = queryset.filter(event_type__in=event_types)
        
        return list(queryset.order_by('created_at'))
    
    def has_analytics_access(self, level: str = 'basic') -> bool:
        """
        Check if workspace has analytics access at specified level.
        
        Args:
            level: Required level (basic, pro, advanced)
            
        Returns:
            True if workspace has access
        """
        allowed, _ = check_analytics_capability(self.workspace, level)
        return allowed
