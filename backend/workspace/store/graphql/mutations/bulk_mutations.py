"""
Shopify-inspired Bulk GraphQL Mutations

Provides bulk mutations following GraphQL architecture standards:
- Service layer integration
- Proper typed responses
- Input validation
- Workspace scoping
"""

import graphene
from graphql import GraphQLError
from workspace.store.services.bulk_operation_service import bulk_operation_service
from workspace.store.graphql.types.bulk_operation_types import (
    BulkPublishResponse, BulkUpdateResponse, BulkDeleteResponse
)


# Input types for bulk operations
class PriceUpdateInput(graphene.InputObjectType):
    product_id = graphene.ID(required=True)
    new_price = graphene.Float(required=True)


class InventoryUpdateInput(graphene.InputObjectType):
    variant_id = graphene.ID(required=True)
    location_id = graphene.ID(required=True)
    quantity = graphene.Int(required=True)


class OrderStatusUpdateInput(graphene.InputObjectType):
    order_id = graphene.ID(required=True)
    new_status = graphene.String(required=True)


class BulkJobStatus(graphene.ObjectType):
    """Type for job status polling"""
    job_id = graphene.String()
    status = graphene.String()  # PENDING, PROGRESS, SUCCESS, FAILURE
    current = graphene.Int()
    total = graphene.Int()
    percent = graphene.Int()
    error = graphene.String()


class BulkPublishProducts(graphene.Mutation):
    """
    Publish multiple products in background

    Follows GraphQL architecture standards:
    - Service layer integration
    - Proper typed response
    - Input validation
    - Workspace scoping
    """

    class Arguments:
        product_ids = graphene.List(graphene.ID, required=True)

    Output = BulkPublishResponse

    @staticmethod
    def mutate(root, info, product_ids):
        workspace = info.context.workspace
        user = info.context.user

        if not product_ids:
            return BulkPublishResponse(
                success=False,
                error="No product IDs provided"
            )

        # Call service layer
        result = bulk_operation_service.bulk_publish_products(
            workspace=workspace,
            product_ids=[str(pid) for pid in product_ids],
            user=user
        )

        return BulkPublishResponse(
            success=result['success'],
            operation_id=result.get('operation_id'),
            processed_count=result.get('processed_count'),
            message=result.get('message'),
            error=result.get('error')
        )


class BulkUpdatePrices(graphene.Mutation):
    """
    Update prices for multiple products in background

    Follows GraphQL architecture standards:
    - Service layer integration
    - Proper typed response
    - Input validation
    - Workspace scoping
    """

    class Arguments:
        price_updates = graphene.List(
            graphene.NonNull(PriceUpdateInput),
            required=True
        )

    Output = BulkUpdateResponse

    @staticmethod
    def mutate(root, info, price_updates):
        workspace = info.context.workspace
        user = info.context.user

        if not price_updates:
            return BulkUpdateResponse(
                success=False,
                error="No price updates provided"
            )

        # Prepare data for service
        updates_data = [
            {
                'product_id': str(update.product_id),
                'new_price': update.new_price
            }
            for update in price_updates
        ]

        # Call service layer
        result = bulk_operation_service.bulk_update_prices(
            workspace=workspace,
            price_updates=updates_data,
            user=user
        )

        return BulkUpdateResponse(
            success=result['success'],
            operation_id=result.get('operation_id'),
            processed_count=result.get('processed_count'),
            message=result.get('message'),
            error=result.get('error')
        )


class BulkDeleteProducts(graphene.Mutation):
    """
    Delete multiple products in background

    Follows GraphQL architecture standards:
    - Service layer integration
    - Proper typed response
    - Input validation
    - Workspace scoping
    """

    class Arguments:
        product_ids = graphene.List(graphene.ID, required=True)

    Output = BulkDeleteResponse

    @staticmethod
    def mutate(root, info, product_ids):
        workspace = info.context.workspace
        user = info.context.user

        if not product_ids:
            return BulkDeleteResponse(
                success=False,
                error="No product IDs provided"
            )

        # Call service layer
        result = bulk_operation_service.bulk_delete_products(
            workspace=workspace,
            product_ids=[str(pid) for pid in product_ids],
            user=user
        )

        return BulkDeleteResponse(
            success=result['success'],
            operation_id=result.get('operation_id'),
            processed_count=result.get('processed_count'),
            message=result.get('message'),
            error=result.get('error')
        )


class BulkUpdateInventory(graphene.Mutation):
    """
    Update inventory for multiple variants across regions

    Follows GraphQL architecture standards:
    - Service layer integration
    - Proper typed response
    - Input validation
    - Workspace scoping
    """

    class Arguments:
        inventory_updates = graphene.List(
            graphene.NonNull(InventoryUpdateInput),
            required=True
        )

    Output = BulkUpdateResponse

    @staticmethod
    def mutate(root, info, inventory_updates):
        workspace = info.context.workspace
        user = info.context.user

        if not inventory_updates:
            return BulkUpdateResponse(
                success=False,
                error="No inventory updates provided"
            )

        # Prepare data for service
        updates_data = [
            {
                'variant_id': str(update.variant_id),
                'location_id': str(update.location_id),
                'quantity': update.quantity
            }
            for update in inventory_updates
        ]

        # Call service layer
        result = bulk_operation_service.bulk_update_inventory(
            workspace=workspace,
            inventory_updates=updates_data,
            user=user
        )

        return BulkUpdateResponse(
            success=result['success'],
            operation_id=result.get('operation_id'),
            processed_count=result.get('processed_count'),
            message=result.get('message'),
            error=result.get('error')
        )




class BulkUnpublishProducts(graphene.Mutation):
    """
    Unpublish multiple products in background

    Follows GraphQL architecture standards:
    - Service layer integration
    - Proper typed response
    - Input validation
    - Workspace scoping
    """

    class Arguments:
        product_ids = graphene.List(graphene.ID, required=True)

    Output = BulkPublishResponse

    @staticmethod
    def mutate(root, info, product_ids):
        workspace = info.context.workspace
        user = info.context.user

        if not product_ids:
            return BulkPublishResponse(
                success=False,
                error="No product IDs provided"
            )

        # Call service layer
        result = bulk_operation_service.bulk_unpublish_products(
            workspace=workspace,
            product_ids=[str(pid) for pid in product_ids],
            user=user
        )

        return BulkPublishResponse(
            success=result['success'],
            operation_id=result.get('operation_id'),
            processed_count=result.get('processed_count'),
            message=result.get('message'),
            error=result.get('error')
        )


class BulkMutations(graphene.ObjectType):
    """
    Bulk mutations collection
    """

    bulk_publish_products = BulkPublishProducts.Field()
    bulk_unpublish_products = BulkUnpublishProducts.Field()
    bulk_update_prices = BulkUpdatePrices.Field()
    bulk_delete_products = BulkDeleteProducts.Field()
    bulk_update_inventory = BulkUpdateInventory.Field()