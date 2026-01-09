"""
Location GraphQL Mutations for Admin Store API - Cameroon Context

Simple Location CRUD for user-defined warehouse/store management
Perfect for Cameroon's 10 regions with flexible location management
"""

import graphene
from graphql import GraphQLError
from django.db import transaction
from ..types.inventory_types import LocationType
from workspace.store.services.location_service import location_service


class LocationInput(graphene.InputObjectType):
    """Input for creating/updating locations"""
    name = graphene.String(required=True)
    region = graphene.String(required=True)
    address_line1 = graphene.String(required=True)
    address_line2 = graphene.String()
    city = graphene.String(required=True)
    phone = graphene.String()
    email = graphene.String()
    is_active = graphene.Boolean(default_value=True)
    is_primary = graphene.Boolean(default_value=False)
    low_stock_threshold = graphene.Int(default_value=5)
    manager_name = graphene.String()


class CreateLocation(graphene.Mutation):
    """Create location (warehouse/store)"""

    class Arguments:
        input = LocationInput(required=True)

    success = graphene.Boolean()
    location = graphene.Field(LocationType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Convert GraphQL input to service format
            location_data = {
                'name': input.name,
                'region': input.region,
                'address_line1': input.address_line1,
                'address_line2': input.address_line2,
                'city': input.city,
                'phone': input.phone,
                'email': input.email,
                'is_active': input.is_active,
                'is_primary': input.is_primary,
                'low_stock_threshold': input.low_stock_threshold,
                'manager_name': input.manager_name
            }

            # Call service layer
            result = location_service.create_location(
                workspace=workspace,
                location_data=location_data,
                user=user
            )

            return CreateLocation(
                success=result['success'],
                location=result.get('location'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Location creation mutation failed: {str(e)}", exc_info=True)

            return CreateLocation(
                success=False,
                error=f"Location creation failed: {str(e)}"
            )


class UpdateLocation(graphene.Mutation):
    """Update location"""

    class Arguments:
        id = graphene.ID(required=True)
        input = LocationInput(required=True)

    success = graphene.Boolean()
    location = graphene.Field(LocationType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Convert GraphQL input to service format
            update_data = {}
            for field, value in input.items():
                if value is not None:
                    update_data[field] = value

            # Call service layer
            result = location_service.update_location(
                workspace=workspace,
                location_id=id,
                update_data=update_data,
                user=user
            )

            return UpdateLocation(
                success=result['success'],
                location=result.get('location'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Location update mutation failed: {str(e)}", exc_info=True)

            return UpdateLocation(
                success=False,
                error=f"Location update failed: {str(e)}"
            )


class DeleteLocation(graphene.Mutation):
    """Delete location"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Call service layer
            result = location_service.delete_location(
                workspace=workspace,
                location_id=id,
                user=user
            )

            return DeleteLocation(
                success=result['success'],
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Location deletion mutation failed: {str(e)}", exc_info=True)

            return DeleteLocation(
                success=False,
                error=f"Location deletion failed: {str(e)}"
            )


class LocationMutations(graphene.ObjectType):
    """Location mutations collection - Simple Location CRUD"""

    create_location = CreateLocation.Field()
    update_location = UpdateLocation.Field()
    delete_location = DeleteLocation.Field()
