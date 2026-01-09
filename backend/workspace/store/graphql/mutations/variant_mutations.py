# Variant GraphQL Mutations
# GraphQL mutations for variant operations

import graphene
from graphql import GraphQLError
from workspace.store.services.variant_service import variant_service
from workspace.store.graphql.types.variant_types import ProductVariantType


class InventoryUpdateInput(graphene.InputObjectType):
    """Input for inventory updates per location"""

    location_id = graphene.String(required=True)
    onhand = graphene.Int()
    available = graphene.Int()
    condition = graphene.String()


class VariantUpdateInput(graphene.InputObjectType):
    """Input for variant updates"""

    sku = graphene.String()
    barcode = graphene.String()
    option1 = graphene.String()
    option2 = graphene.String()
    option3 = graphene.String()
    price = graphene.Float()
    compare_at_price = graphene.Float()
    cost_price = graphene.Float()
    track_inventory = graphene.Boolean()
    is_active = graphene.Boolean()
    position = graphene.Int()
    featured_media_id = graphene.String()
    inventory_updates = graphene.List(InventoryUpdateInput, description="Update inventory per location")


class UpdateVariant(graphene.Mutation):
    """Update variant with atomic transaction"""

    class Arguments:
        variant_id = graphene.String(required=True)
        update_data = VariantUpdateInput(required=True)

    success = graphene.Boolean()
    variant = graphene.Field(ProductVariantType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, variant_id, update_data):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Convert GraphQL input to service format
            update_dict = {}
            for field, value in update_data.items():
                if value is not None:
                    # Handle inventory_updates specially (convert list of objects to list of dicts)
                    if field == 'inventory_updates':
                        update_dict[field] = [
                            {
                                'location_id': inv.location_id,
                                'onhand': inv.onhand,
                                'available': inv.available,
                                'condition': inv.condition
                            }
                            for inv in value
                        ]
                    else:
                        update_dict[field] = value

            # Call service layer
            result = variant_service.update_variant(
                workspace_id=str(workspace.id),
                variant_id=variant_id,
                update_data=update_dict,
                user=user
            )

            return UpdateVariant(
                success=result['success'],
                variant=result.get('variant'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Variant update mutation failed: {str(e)}", exc_info=True)

            return UpdateVariant(
                success=False,
                error=f"Variant update failed: {str(e)}"
            )


class VariantMutations(graphene.ObjectType):
    """Variant mutations collection"""

    update_variant = UpdateVariant.Field()