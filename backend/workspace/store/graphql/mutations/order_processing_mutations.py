"""
GraphQL Mutations for Order Processing Service Integration

Production-ready order processing mutations with workspace scoping
Follows industry standards for performance and reliability

Performance: < 100ms response time for order operations
Scalability: Bulk operations with background processing
Reliability: Atomic transactions with comprehensive error handling
Security: Workspace scoping and permission validation
"""

import graphene
from graphql import GraphQLError
from workspace.store.services.order_processing_service import order_processing_service
from workspace.core.services import PermissionService

class AddressInput(graphene.InputObjectType):
    """
    Simple address input for Cameroon context
    Used for shipping and billing addresses in orders
    """
    address = graphene.String(description="Street/physical address")
    city = graphene.String(description="City")
    region = graphene.String(description="Cameroon region")


class OrderItemInput(graphene.InputObjectType):
    """
    Input for order item

    Validation: Quantity must be positive, unit_price must be valid
    Security: Product ID validation and workspace scoping
    """

    product_id = graphene.String(required=True, description="Product ID")
    variant_id = graphene.String(description="Variant ID (if applicable)")
    quantity = graphene.Int(required=True, description="Quantity (must be positive)")
    unit_price = graphene.Decimal(required=True, description="Unit price in XAF")

    @staticmethod
    def validate_quantity(value):
        """Validate quantity is positive"""
        if value <= 0:
            from graphql import GraphQLError
            raise GraphQLError("Quantity must be positive")
        return value

    @staticmethod
    def validate_unit_price(value):
        """Validate unit price is positive"""
        if value <= 0:
            from graphql import GraphQLError
            raise GraphQLError("Unit price must be positive")
        return value


class OrderCreateInput(graphene.InputObjectType):
    """
    Input for order creation

    Validation: Required fields and data structure
    Security: Workspace scoping via JWT middleware
    Regional: Cameroon-specific validation for phone and regions
    Phone-first: customer_id required, customer data fetched from Customer table
    """

    # CUSTOMER (Required - relational approach)
    customer_id = graphene.String(required=True, description="Customer ID (fetches customer data automatically)")

    order_source = graphene.String(description="Order source: whatsapp, payment, manual")
    shipping_region = graphene.String(description="Cameroon region: centre, littoral, west, northwest, southwest, adamawa, east, far_north, north, south")
    shipping_address = AddressInput(required=True, description="Shipping address details")
    billing_address = AddressInput(description="Billing address details")
    shipping_cost = graphene.Decimal(description="Shipping cost in XAF")
    tax_amount = graphene.Decimal(description="Tax amount in XAF")
    discount_amount = graphene.Decimal(description="Discount amount in XAF")
    payment_method = graphene.String(description="Payment method: cash_on_delivery, whatsapp, mobile_money, card, bank_transfer")
    currency = graphene.String(description="Currency: XAF (default)")
    notes = graphene.String(description="Order notes")
    items = graphene.List(OrderItemInput, required=True, description="Order items")

    @staticmethod
    def validate_shipping_region(value):
        """Validate Cameroon shipping region (must match DB model choices)"""
        valid_regions = [
            'centre', 'littoral', 'west', 'northwest', 'southwest',
            'adamawa', 'east', 'far_north', 'north', 'south'
        ]
        if value and value not in valid_regions:
            from graphql import GraphQLError
            raise GraphQLError(f"Invalid region. Must be one of: {', '.join(valid_regions)}")
        return value


class StatusUpdateInput(graphene.InputObjectType):
    """
    Input for order status update

    Validation: Valid status transitions
    Security: Workspace scoping and permission validation
    """

    order_id = graphene.String(required=True)
    new_status = graphene.String(required=True)


class BulkStatusUpdateInput(graphene.InputObjectType):
    """
    Input for bulk status updates

    Validation: Batch size limits and status validation
    Security: Workspace scoping for all updates
    """

    updates = graphene.List(StatusUpdateInput, required=True)


class OrderAnalyticsType(graphene.ObjectType):
    """GraphQL type for order analytics"""

    period_days = graphene.Int()
    total_orders = graphene.Int()
    total_revenue = graphene.Float()
    average_order_value = graphene.Float()
    pending_orders = graphene.Int()
    completed_orders = graphene.Int()
    cancelled_orders = graphene.Int()


class SourceBreakdownType(graphene.ObjectType):
    """GraphQL type for order source breakdown"""

    order_source = graphene.String()
    count = graphene.Int()
    revenue = graphene.Float()


class RegionalBreakdownType(graphene.ObjectType):
    """GraphQL type for regional breakdown"""

    shipping_region = graphene.String()
    count = graphene.Int()
    revenue = graphene.Float()


class CreateOrder(graphene.Mutation):
    """
    Create a new order with validation and inventory checks

    Performance: Atomic creation with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive error handling with rollback
    """

    class Arguments:
        order_data = OrderCreateInput(required=True)

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()
    unavailable_items = graphene.List(graphene.JSONString)

    @staticmethod
    def mutate(root, info, order_data):
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:create'):
            raise GraphQLError("Insufficient permissions to create orders")
 
        try:
            # Convert GraphQL input to service format with proper null handling
            order_dict = {
                'customer_id': order_data.customer_id,  # NEW: Customer ID for relational approach
                'order_source': order_data.order_source,
                'shipping_region': order_data.shipping_region,
                'shipping_address': {
                    'address': order_data.shipping_address.address if order_data.shipping_address else '',
                    'city': order_data.shipping_address.city if order_data.shipping_address else '',
                    'region': order_data.shipping_address.region if order_data.shipping_address else ''
                },
                'billing_address': {
                    'address': order_data.billing_address.address if order_data.billing_address else '',
                    'city': order_data.billing_address.city if order_data.billing_address else '',
                    'region': order_data.billing_address.region if order_data.billing_address else ''
                } if order_data.billing_address else {},
                'shipping_cost': str(order_data.shipping_cost) if order_data.shipping_cost else '0.00',
                'tax_amount': str(order_data.tax_amount) if order_data.tax_amount else '0.00',
                'discount_amount': str(order_data.discount_amount) if order_data.discount_amount else '0.00',
                'payment_method': order_data.payment_method,
                'currency': order_data.currency,
                'notes': order_data.notes,
                'items': [
                    {
                        'product_id': item.product_id,
                        'variant_id': item.variant_id,
                        'quantity': item.quantity,
                        'unit_price': str(item.unit_price)
                    }
                    for item in order_data.items
                ]
            }

            # Remove None values to allow service defaults to work
            order_dict = {k: v for k, v in order_dict.items() if v is not None}

            result = order_processing_service.create_order(
                workspace=workspace,
                order_data=order_dict,
                user=user
            )

            return CreateOrder(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error'),
                unavailable_items=result.get('unavailable_items', [])
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Order creation mutation failed: {str(e)}", exc_info=True)

            return CreateOrder(
                success=False,
                error=f"Order creation failed: {str(e)}"
            )


class CreateCashOnDeliveryOrder(graphene.Mutation):
    """
    Create a cash on delivery order

    Payment status remains 'pending' until marked as paid on delivery
    """

    class Arguments:
        order_data = OrderCreateInput(required=True)

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()
    unavailable_items = graphene.List(graphene.JSONString)

    @staticmethod
    def mutate(root, info, order_data):
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:create'):
            raise GraphQLError("Insufficient permissions to create a C.O.D order")
 
        try:
            # Convert GraphQL input to service format
            order_dict = {
                'customer_id': order_data.customer_id,  # NEW: Customer ID for relational approach
                'order_source': order_data.order_source,
                'shipping_region': order_data.shipping_region,
                'shipping_address': {
                    'street': order_data.shipping_address.street if order_data.shipping_address else '',
                    'city': order_data.shipping_address.city if order_data.shipping_address else '',
                    'region': order_data.shipping_address.region if order_data.shipping_address else ''
                },
                'billing_address': {
                    'street': order_data.billing_address.street if order_data.billing_address else '',
                    'city': order_data.billing_address.city if order_data.billing_address else '',
                    'region': order_data.billing_address.region if order_data.billing_address else ''
                } if order_data.billing_address else {},
                'shipping_cost': str(order_data.shipping_cost) if order_data.shipping_cost else '0.00',
                'tax_amount': str(order_data.tax_amount) if order_data.tax_amount else '0.00',
                'discount_amount': str(order_data.discount_amount) if order_data.discount_amount else '0.00',
                'payment_method': 'cash_on_delivery',  # Force COD payment method
                'currency': order_data.currency,
                'notes': order_data.notes,
                'items': [
                    {
                        'product_id': item.product_id,
                        'variant_id': item.variant_id,
                        'quantity': item.quantity,
                        'unit_price': str(item.unit_price)
                    }
                    for item in order_data.items
                ]
            }

            # Remove None values
            order_dict = {k: v for k, v in order_dict.items() if v is not None}

            # Use unified create_order with COD payment method
            result = order_processing_service.create_order(
                workspace=workspace,
                order_data=order_dict,
                user=user
            )

            return CreateCashOnDeliveryOrder(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error'),
                unavailable_items=result.get('unavailable_items', [])
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Cash on delivery order creation mutation failed: {str(e)}", exc_info=True)

            return CreateCashOnDeliveryOrder(
                success=False,
                error=f"Cash on delivery order creation failed: {str(e)}"
            )


class CreateWhatsAppOrder(graphene.Mutation):
    """
    Create a WhatsApp order

    Creates order and sends WhatsApp DM to admin
    """

    class Arguments:
        order_data = OrderCreateInput(required=True)

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()
    unavailable_items = graphene.List(graphene.JSONString)

    @staticmethod
    def mutate(root, info, order_data):
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:create'):
            raise GraphQLError("Insufficient permissions to create WhatsApp orders")
 
        try:
            # Convert GraphQL input to service format
            order_dict = {
                'customer_id': order_data.customer_id,  # NEW: Customer ID for relational approach
                'order_source': 'whatsapp',  # Force WhatsApp order source
                'shipping_region': order_data.shipping_region,
                'shipping_address': {
                    'street': order_data.shipping_address.street if order_data.shipping_address else '',
                    'city': order_data.shipping_address.city if order_data.shipping_address else '',
                    'region': order_data.shipping_address.region if order_data.shipping_address else ''
                },
                'billing_address': {
                    'street': order_data.billing_address.street if order_data.billing_address else '',
                    'city': order_data.billing_address.city if order_data.billing_address else '',
                    'region': order_data.billing_address.region if order_data.billing_address else ''
                } if order_data.billing_address else {},
                'shipping_cost': str(order_data.shipping_cost) if order_data.shipping_cost else '0.00',
                'tax_amount': str(order_data.tax_amount) if order_data.tax_amount else '0.00',
                'discount_amount': str(order_data.discount_amount) if order_data.discount_amount else '0.00',
                'payment_method': 'whatsapp',  # Force WhatsApp payment method
                'currency': order_data.currency,
                'notes': order_data.notes,
                'items': [
                    {
                        'product_id': item.product_id,
                        'variant_id': item.variant_id,
                        'quantity': item.quantity,
                        'unit_price': str(item.unit_price)
                    }
                    for item in order_data.items
                ]
            }

            # Remove None values
            order_dict = {k: v for k, v in order_dict.items() if v is not None}

            # Use unified create_order with WhatsApp source and payment
            result = order_processing_service.create_order(
                workspace=workspace,
                order_data=order_dict,
                user=user
            )

            return CreateWhatsAppOrder(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error'),
                unavailable_items=result.get('unavailable_items', [])
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"WhatsApp order creation mutation failed: {str(e)}", exc_info=True)

            return CreateWhatsAppOrder(
                success=False,
                error=f"WhatsApp order creation failed: {str(e)}"
            )


class UpdateOrderStatus(graphene.Mutation):
    """
    Update order status with validation and side effects

    Performance: Atomic update with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive status transition validation
    """

    class Arguments:
        order_id = graphene.String(required=True)
        new_status = graphene.String(required=True)

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, order_id, new_status):
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:update'):
            raise GraphQLError("Insufficient permissions to update orders")
 
        try:
            result = order_processing_service.update_order_status(
                workspace=workspace,
                order_id=order_id,
                new_status=new_status,
                user=user
            )

            return UpdateOrderStatus(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Order status update mutation failed: {str(e)}", exc_info=True)

            return UpdateOrderStatus(
                success=False,
                error=f"Order status update failed: {str(e)}"
            )


class CancelOrder(graphene.Mutation):
    """
    Cancel an order with validation and inventory restoration

    Performance: Atomic cancellation with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive validation and rollback
    """

    class Arguments:
        order_id = graphene.String(required=True)
        reason = graphene.String()

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, order_id, reason=None):
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:cancel'):
            raise GraphQLError("Insufficient permissions to cancel orders")
 
        try:
            result = order_processing_service.cancel_order(
                workspace=workspace,
                order_id=order_id,
                reason=reason,
                user=user
            )

            return CancelOrder(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Order cancellation mutation failed: {str(e)}", exc_info=True)

            return CancelOrder(
                success=False,
                error=f"Order cancellation failed: {str(e)}"
            )


class BulkUpdateOrderStatus(graphene.Mutation):
    """
    Process bulk order status updates

    Performance: Optimized bulk operations with transaction
    Scalability: Handles up to 500 updates per batch
    Reliability: Atomic transaction with rollback on failure
    """

    class Arguments:
        bulk_data = BulkStatusUpdateInput(required=True)

    success = graphene.Boolean()
    total_updates = graphene.Int()
    successful_updates = graphene.Int()
    failed_updates = graphene.List(graphene.JSONString)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, bulk_data):
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:update'):
            raise GraphQLError("Insufficient permissions to Bulk Update Orders")
 
        try:
            # Convert GraphQL input to service format
            updates = []
            for update in bulk_data.updates:
                updates.append({
                    'order_id': update.order_id,
                    'new_status': update.new_status
                })

            result = order_processing_service.process_bulk_status_updates(
                workspace=workspace,
                updates=updates,
                user=user
            )

            return BulkUpdateOrderStatus(
                success=result['success'],
                total_updates=result['total_updates'],
                successful_updates=result['successful_updates'],
                failed_updates=result.get('failed_updates', []),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Bulk status update mutation failed: {str(e)}", exc_info=True)

            return BulkUpdateOrderStatus(
                success=False,
                total_updates=0,
                successful_updates=0,
                failed_updates=[],
                error=f"Bulk status update failed: {str(e)}"
            )


class ArchiveOrder(graphene.Mutation):
    """
    Archive an order to remove it from active view

    Performance: Atomic update with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Validates order can be archived before update
    """

    class Arguments:
        order_id = graphene.String(required=True)

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, order_id):
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:update'):
            raise GraphQLError("Insufficient permissions to archive orders")

        try:
            result = order_processing_service.archive_order(
                workspace=workspace,
                order_id=order_id,
                user=user
            )

            return ArchiveOrder(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Order archiving mutation failed: {str(e)}", exc_info=True)

            return ArchiveOrder(
                success=False,
                error=f"Order archiving failed: {str(e)}"
            )


class UnarchiveOrder(graphene.Mutation):
    """
    Unarchive an order to restore it to active view

    Performance: Atomic update with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Validates order can be unarchived before update
    """

    class Arguments:
        order_id = graphene.String(required=True)

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, order_id):
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:update'):
            raise GraphQLError("Insufficient permissions to unarchive orders")

        try:
            result = order_processing_service.unarchive_order(
                workspace=workspace,
                order_id=order_id,
                user=user
            )

            return UnarchiveOrder(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Order unarchiving mutation failed: {str(e)}", exc_info=True)

            return UnarchiveOrder(
                success=False,
                error=f"Order unarchiving failed: {str(e)}"
            )


class GetOrderAnalytics(graphene.Mutation):
    """
    Get order analytics for workspace

    Performance: Optimized aggregations with proper indexing
    Scalability: Efficient queries for large datasets
    Security: Workspace scoping and permission validation
    """

    class Arguments:
        period_days = graphene.Int()

    analytics = graphene.Field(OrderAnalyticsType)
    source_breakdown = graphene.List(SourceBreakdownType)
    regional_breakdown = graphene.List(RegionalBreakdownType)
    success = graphene.Boolean()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, period_days=30):
        workspace = info.context.workspace
        user = info.context.user

        try:
            result = order_processing_service.get_order_analytics(
                workspace=workspace,
                user=user,
                period_days=period_days
            )

            if result['success']:
                analytics_data = result['analytics']
                source_data = result['source_breakdown']
                regional_data = result['regional_breakdown']

                analytics = OrderAnalyticsType(
                    period_days=analytics_data['period_days'],
                    total_orders=analytics_data['total_orders'],
                    total_revenue=analytics_data['total_revenue'],
                    average_order_value=analytics_data['average_order_value'],
                    pending_orders=analytics_data['pending_orders'],
                    completed_orders=analytics_data['completed_orders'],
                    cancelled_orders=analytics_data['cancelled_orders']
                )

                source_breakdown = [
                    SourceBreakdownType(
                        order_source=item['order_source'],
                        count=item['count'],
                        revenue=item['revenue']
                    )
                    for item in source_data
                ]

                regional_breakdown = [
                    RegionalBreakdownType(
                        shipping_region=item['shipping_region'],
                        count=item['count'],
                        revenue=item['revenue']
                    )
                    for item in regional_data
                ]

                return GetOrderAnalytics(
                    analytics=analytics,
                    source_breakdown=source_breakdown,
                    regional_breakdown=regional_breakdown,
                    success=True
                )
            else:
                return GetOrderAnalytics(
                    success=False,
                    error=result.get('error')
                )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Order analytics mutation failed: {str(e)}", exc_info=True)

            return GetOrderAnalytics(
                success=False,
                error=f"Order analytics failed: {str(e)}"
            )


class MarkOrderAsPaid(graphene.Mutation):
    """
    Mark order as paid (for COD and WhatsApp orders)

    Performance: Atomic update with proper validation
    Security: Workspace scoping and permission validation
    Use Case: Admin marks COD/WhatsApp orders as paid upon delivery/confirmation
    """

    class Arguments:
        order_id = graphene.String(required=True)

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, order_id):
        workspace = info.context.workspace
        user = info.context.user

        try:
            result = order_processing_service.mark_order_as_paid(
                workspace=workspace,
                order_id=order_id,
                user=user
            )

            return MarkOrderAsPaid(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Mark order as paid mutation failed: {str(e)}", exc_info=True)

            return MarkOrderAsPaid(
                success=False,
                error=f"Failed to mark order as paid: {str(e)}"
            )


class UpdateOrderNotes(graphene.Mutation):
    """
    Update order notes
    """
    class Arguments:
        order_id = graphene.String(required=True)
        notes = graphene.String(required=True)

    success = graphene.Boolean()
    order = graphene.Field('workspace.store.graphql.types.order_types.OrderType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, order_id, notes):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'order:update'):
            raise GraphQLError("Insufficient permissions to update orders")

        try:
            result = order_processing_service.update_order_notes(
                workspace=workspace,
                order_id=order_id,
                notes=notes,
                user=user
            )

            return UpdateOrderNotes(
                success=result['success'],
                order=result.get('order'),
                message=result.get('message'),
                error=result.get('error')
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Order notes update mutation failed: {str(e)}", exc_info=True)
            return UpdateOrderNotes(success=False, error=str(e))


class AddOrderComment(graphene.Mutation):
    """
    Add comment to order timeline
    """
    class Arguments:
        order_id = graphene.String(required=True)
        message = graphene.String(required=True)
        is_internal = graphene.Boolean(default_value=True)

    success = graphene.Boolean()
    comment = graphene.Field('workspace.store.graphql.types.order_types.OrderCommentType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, order_id, message, is_internal=True):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'order:update'):
            raise GraphQLError("Insufficient permissions to update orders")

        try:
            result = order_processing_service.add_order_comment(
                workspace=workspace,
                order_id=order_id,
                message=message,
                is_internal=is_internal,
                user=user
            )

            return AddOrderComment(
                success=result['success'],
                comment=result.get('comment'),
                message=result.get('message'),
                error=result.get('error')
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Add order comment mutation failed: {str(e)}", exc_info=True)
            return AddOrderComment(success=False, error=str(e))


class OrderProcessingMutations(graphene.ObjectType):
    """
    Order processing mutations collection - ADMIN ONLY

    Shopify-style admin order management:
    - Create orders manually (admin order entry)
    - Create COD orders
    - Create WhatsApp orders
    - Update order status
    - Cancel orders
    - Mark orders as paid
    - Bulk status updates
    - View analytics
    """

    create_order = CreateOrder.Field()
    create_cash_on_delivery_order = CreateCashOnDeliveryOrder.Field()
    create_whatsapp_order = CreateWhatsAppOrder.Field()
    update_order_status = UpdateOrderStatus.Field()
    cancel_order = CancelOrder.Field()
    mark_order_as_paid = MarkOrderAsPaid.Field()
    bulk_update_order_status = BulkUpdateOrderStatus.Field()
    archive_order = ArchiveOrder.Field()
    unarchive_order = UnarchiveOrder.Field()
    update_order_notes = UpdateOrderNotes.Field()
    add_order_comment = AddOrderComment.Field()