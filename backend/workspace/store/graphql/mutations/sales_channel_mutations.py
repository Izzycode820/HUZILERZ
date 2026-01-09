"""
Sales Channel GraphQL Mutations for Admin Store API

Production-ready sales channel mutations using SalesChannelService
"""

import graphene
from django.db import transaction
from graphql import GraphQLError
from ..types.sales_channel_types import SalesChannelType, ChannelProductType, ChannelOrderType
from workspace.store.models import SalesChannel, ChannelProduct, ChannelOrder


class SalesChannelInput(graphene.InputObjectType):
    """Input for creating/updating sales channels"""
    name = graphene.String(required=True)
    channel_type = graphene.String(required=True)
    is_active = graphene.Boolean(default_value=True)
    base_url = graphene.String()
    supports_inventory_sync = graphene.Boolean(default_value=True)
    supports_order_sync = graphene.Boolean(default_value=True)
    supports_customer_sync = graphene.Boolean(default_value=False)


class CreateSalesChannel(graphene.Mutation):
    """Create sales channel with atomic transaction"""

    class Arguments:
        input = SalesChannelInput(required=True)

    success = graphene.Boolean()
    sales_channel = graphene.Field(SalesChannelType)
    message = graphene.String()

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        workspace = info.context.workspace

        try:
            sales_channel = SalesChannel.objects.create(
                workspace=workspace,
                name=input.name,
                channel_type=input.channel_type,
                is_active=input.get('is_active', True),
                base_url=input.get('base_url'),
                supports_inventory_sync=input.get('supports_inventory_sync', True),
                supports_order_sync=input.get('supports_order_sync', True),
                supports_customer_sync=input.get('supports_customer_sync', False)
            )

            return CreateSalesChannel(
                success=True,
                sales_channel=sales_channel,
                message="Sales channel created successfully"
            )

        except Exception as e:
            raise GraphQLError(f"Failed to create sales channel: {str(e)}")


class UpdateSalesChannel(graphene.Mutation):
    """Update sales channel with atomic transaction"""

    class Arguments:
        id = graphene.ID(required=True)
        input = SalesChannelInput(required=True)

    success = graphene.Boolean()
    sales_channel = graphene.Field(SalesChannelType)
    message = graphene.String()

    @staticmethod
    @transaction.atomic
    def mutate(root, info, id, input):
        workspace = info.context.workspace

        try:
            sales_channel = SalesChannel.objects.select_for_update().get(
                id=id,
                workspace=workspace
            )

            # Update fields
            for field, value in input.items():
                if value is not None:
                    setattr(sales_channel, field, value)

            sales_channel.save()

            return UpdateSalesChannel(
                success=True,
                sales_channel=sales_channel,
                message="Sales channel updated successfully"
            )

        except SalesChannel.DoesNotExist:
            raise GraphQLError("Sales channel not found")


class DeleteSalesChannel(graphene.Mutation):
    """Delete sales channel with atomic transaction"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    @transaction.atomic
    def mutate(root, info, id):
        workspace = info.context.workspace

        try:
            sales_channel = SalesChannel.objects.get(id=id, workspace=workspace)
            sales_channel.delete()

            return DeleteSalesChannel(
                success=True,
                message="Sales channel deleted successfully"
            )

        except SalesChannel.DoesNotExist:
            raise GraphQLError("Sales channel not found")


class SyncInventory(graphene.Mutation):
    """Sync inventory using SalesChannelService"""

    class Arguments:
        channel_id = graphene.ID(required=True)
        product_id = graphene.String(required=True)
        quantity = graphene.Int(required=True)

    success = graphene.Boolean()
    channel_product = graphene.Field(ChannelProductType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, channel_id, product_id, quantity):
        workspace = info.context.workspace

        try:
            channel = SalesChannel.objects.get(id=channel_id, workspace=workspace)
            channel_product, error = SalesChannelService.sync_inventory(
                channel, product_id, quantity
            )

            if error:
                return SyncInventory(success=False, message=error)

            return SyncInventory(
                success=True,
                channel_product=channel_product,
                message="Inventory synced successfully"
            )

        except SalesChannel.DoesNotExist:
            raise GraphQLError("Sales channel not found")


class SalesChannelMutations(graphene.ObjectType):
    """All sales channel mutations"""
    create_sales_channel = CreateSalesChannel.Field()
    update_sales_channel = UpdateSalesChannel.Field()
    delete_sales_channel = DeleteSalesChannel.Field()
    sync_inventory = SyncInventory.Field()
