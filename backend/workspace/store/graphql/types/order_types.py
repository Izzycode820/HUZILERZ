"""
Order GraphQL Types for Admin Store API

Provides GraphQL types for Order and OrderItem models
with proper DataLoader integration for N+1 query prevention
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import Order, OrderItem, OrderHistory
from .common_types import BaseConnection


class OrderItemType(DjangoObjectType):
    """
    GraphQL type for OrderItem model

    Features:
    - All order item fields with proper typing
    - Product and variant relationships
    - Price calculations
    """
    id = graphene.ID(required=True)

    class Meta:
        model = OrderItem
        fields = (
            'id', 'product_name', 'product_sku', 'quantity',
            'unit_price', 'product_data'
        )
        interfaces = (graphene.relay.Node,)

    def resolve_id(self, info):
        return str(self.id)

    product = graphene.Field('workspace.store.graphql.types.product_types.ProductType')
    variant = graphene.Field('workspace.store.graphql.types.product_types.ProductVariantType')
    total_price = graphene.Float()

    def resolve_product(self, info):
        """
        Resolve product for this order item
        """
        return self.product

    def resolve_variant(self, info):
        """
        Resolve variant for this order item
        """
        return self.variant

    def resolve_total_price(self, info):
        """
        Calculate total price for this item
        """
        return float(self.quantity * self.unit_price)


class OrderCommentType(DjangoObjectType):
    """
    GraphQL type for OrderComment model
    """
    id = graphene.ID(required=True)

    class Meta:
        from workspace.store.models import OrderComment
        model = OrderComment
        fields = ('id', 'message', 'created_at', 'is_internal')
        interfaces = (graphene.relay.Node,)

    def resolve_id(self, info):
        return str(self.id)

    author = graphene.Field('workspace.core.graphql.types.membership_types.UserType')

    def resolve_author(self, info):
        """
        Resolve comment author (workspace staff member)
        """
        return self.author


class OrderHistoryType(DjangoObjectType):
    """
    GraphQL type for OrderHistory model
    System-generated timeline events
    """
    id = graphene.ID(required=True)

    class Meta:
        model = OrderHistory
        fields = ('id', 'action', 'details', 'created_at')
        interfaces = (graphene.relay.Node,)

    def resolve_id(self, info):
        return str(self.id)

    performed_by = graphene.Field('workspace.core.graphql.types.membership_types.UserType')
    display_message = graphene.String()

    def resolve_performed_by(self, info):
        """
        Resolve user who performed the action
        """
        return self.performed_by

    def resolve_display_message(self, info):
        """
        Get human-readable message for timeline display
        """
        return self.get_display_message()


class TimelineEventType(graphene.ObjectType):
    """
    Unified timeline event type that combines OrderComment and OrderHistory
    """
    id = graphene.ID(required=True)
    type = graphene.String(required=True)
    message = graphene.String(required=True)
    created_at = graphene.DateTime(required=True)
    is_internal = graphene.Boolean()
    metadata = graphene.JSONString()
    author = graphene.Field('workspace.core.graphql.types.membership_types.UserType')

    def resolve_author(self, info):
        """
        Resolve author from either comment or history
        """
        return getattr(self, '_author', None)


class OrderType(DjangoObjectType):
    """
    GraphQL type for Order model

    Features:
    - All order fields with proper typing
    - Order items relationship with DataLoader
    - Status tracking and analytics
    - Cameroon-specific fields (order_source, shipping_region)
    """
    id = graphene.ID(required=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'order_source',
            'customer', 'customer_email', 'customer_name', 'customer_phone',
            'shipping_region', 'shipping_address', 'billing_address',
            'status', 'subtotal', 'shipping_cost', 'tax_amount',
            'discount_amount', 'total_amount', 'payment_method',
            'payment_status', 'currency', 'notes', 'tracking_number',
            'confirmed_at', 'shipped_at', 'delivered_at',
            'is_archived', 'archived_at',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    items = graphene.List(OrderItemType)
    item_count = graphene.Int()
    is_paid = graphene.Boolean()
    can_be_cancelled = graphene.Boolean()
    can_be_refunded = graphene.Boolean()
    can_be_archived = graphene.Boolean()
    can_be_unarchived = graphene.Boolean()
    requires_payment_processing = graphene.Boolean()
    is_whatsapp_order = graphene.Boolean()
    is_cash_on_delivery = graphene.Boolean()
    can_mark_as_paid = graphene.Boolean()

    def resolve_items(self, info):
        """
        Resolve order items using direct ORM query
        Ordered by creation time (first added items first)
        """
        from workspace.store.models import OrderItem
        return OrderItem.objects.filter(
            order=self
        ).order_by('created_at')

    def resolve_item_count(self, info):
        """
        Get total number of items in order
        """
        return self.item_count

    def resolve_is_paid(self, info):
        """
        Check if order is paid
        """
        return self.is_paid

    def resolve_can_be_cancelled(self, info):
        """
        Check if order can be cancelled
        """
        return self.can_be_cancelled

    def resolve_can_be_refunded(self, info):
        """
        Check if order can be refunded
        """
        return self.can_be_refunded

    def resolve_can_be_archived(self, info):
        """
        Check if order can be archived
        """
        return self.can_be_archived

    def resolve_can_be_unarchived(self, info):
        """
        Check if order can be unarchived
        """
        return self.can_be_unarchived

    def resolve_requires_payment_processing(self, info):
        """
        Check if order requires payment processing
        """
        return self.requires_payment_processing

    def resolve_is_whatsapp_order(self, info):
        """
        Check if this is a WhatsApp order
        """
        return self.is_whatsapp_order

    def resolve_is_cash_on_delivery(self, info):
        """
        Check if this is a cash on delivery order
        """
        return self.is_cash_on_delivery

    def resolve_can_mark_as_paid(self, info):
        """
        Check if order can be marked as paid
        """
        return self.can_mark_as_paid

    comments = graphene.List(OrderCommentType)
    history = graphene.List(OrderHistoryType)
    timeline = graphene.List(TimelineEventType)

    def resolve_comments(self, info):
        """
        Resolve order comments with proper ordering
        """
        return self.comments.all().order_by('-created_at')

    def resolve_history(self, info):
        """
        Resolve order history events with proper ordering
        """
        return self.history.all().order_by('-created_at')

    def resolve_timeline(self, info):
        """
        Resolve unified timeline combining comments and history
        Sorted by created_at descending (newest first)
        """
        timeline_events = []

        # Add comments as timeline events
        for comment in self.comments.all():
            event = TimelineEventType(
                id=f"comment_{comment.id}",
                type="COMMENT",
                message=comment.message,
                created_at=comment.created_at,
                is_internal=comment.is_internal,
                metadata={}
            )
            event._author = comment.author
            timeline_events.append(event)

        # Add history as timeline events
        for history in self.history.all():
            # Map action types to frontend event types
            event_type_mapping = {
                'created': 'ORDER_CREATED',
                'status_changed': 'STATUS_CHANGE',
                'marked_as_paid': 'STATUS_CHANGE',
                'cancelled': 'STATUS_CHANGE',
                'archived': 'STATUS_CHANGE',
                'unarchived': 'STATUS_CHANGE',
                'fulfilled': 'STATUS_CHANGE',
                'unfulfilled': 'STATUS_CHANGE',
                'shipped': 'STATUS_CHANGE',
                'delivered': 'STATUS_CHANGE',
                'customer_notified': 'NOTIFICATION',
            }

            event = TimelineEventType(
                id=f"history_{history.id}",
                type=event_type_mapping.get(history.action, 'STATUS_CHANGE'),
                message=history.get_display_message(),
                created_at=history.created_at,
                is_internal=True,
                metadata=history.details
            )
            event._author = history.performed_by
            timeline_events.append(event)

        # Sort by created_at descending (newest first)
        timeline_events.sort(key=lambda e: e.created_at, reverse=True)

        return timeline_events



# Order Connection for pagination
class OrderConnection(graphene.relay.Connection):
    """
    Order connection with pagination support
    """
    class Meta:
        node = OrderType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()


__all__ = [
    'OrderType',
    'OrderItemType',
    'OrderCommentType',
    'OrderHistoryType',
    'TimelineEventType',
    'OrderConnection'
]
