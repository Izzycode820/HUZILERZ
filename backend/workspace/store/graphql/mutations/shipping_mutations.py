"""
Shipping GraphQL Mutations for Admin Store API - Cameroon Context

Simple Package CRUD for flexible shipping management
Perfect for informal markets with manual shipping rates
"""

import graphene
from graphql import GraphQLError
from django.db import transaction
from ..types.shipping_types import PackageType
from workspace.store.services.shipping_service import shipping_service


class PackageInput(graphene.InputObjectType):
    """Input for creating/updating shipping packages"""
    name = graphene.String(required=True)
    package_type = graphene.String(default_value='box')
    size = graphene.String(default_value='medium')
    weight = graphene.Decimal()
    method = graphene.String(required=True)
    region_fees = graphene.JSONString(required=True)
    estimated_days = graphene.String(default_value='3-5')
    use_as_default = graphene.Boolean(default_value=False)
    is_active = graphene.Boolean(default_value=True)


class CreatePackage(graphene.Mutation):
    """Create shipping package"""

    class Arguments:
        input = PackageInput(required=True)

    success = graphene.Boolean()
    package = graphene.Field(PackageType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Convert GraphQL input to service format
            package_data = {
                'name': input.name,
                'package_type': input.package_type,
                'size': input.size,
                'weight': input.weight,
                'method': input.method,
                'region_fees': input.region_fees,
                'estimated_days': input.estimated_days,
                'use_as_default': input.use_as_default,
                'is_active': input.is_active
            }

            # Call service layer
            result = shipping_service.create_package(
                workspace=workspace,
                package_data=package_data,
                user=user
            )

            return CreatePackage(
                success=result['success'],
                package=result.get('package'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Package creation mutation failed: {str(e)}", exc_info=True)

            return CreatePackage(
                success=False,
                error=f"Package creation failed: {str(e)}"
            )


class UpdatePackage(graphene.Mutation):
    """Update shipping package"""

    class Arguments:
        id = graphene.ID(required=True)
        input = PackageInput(required=True)

    success = graphene.Boolean()
    package = graphene.Field(PackageType)
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
            result = shipping_service.update_package(
                workspace=workspace,
                package_id=id,
                update_data=update_data,
                user=user
            )

            return UpdatePackage(
                success=result['success'],
                package=result.get('package'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Package update mutation failed: {str(e)}", exc_info=True)

            return UpdatePackage(
                success=False,
                error=f"Package update failed: {str(e)}"
            )


class DeletePackage(graphene.Mutation):
    """Delete shipping package"""

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
            result = shipping_service.delete_package(
                workspace=workspace,
                package_id=id,
                user=user
            )

            return DeletePackage(
                success=result['success'],
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Package deletion mutation failed: {str(e)}", exc_info=True)

            return DeletePackage(
                success=False,
                error=f"Package deletion failed: {str(e)}"
            )


class ShippingMutations(graphene.ObjectType):
    """Shipping mutations collection - Simple Package CRUD"""

    create_package = CreatePackage.Field()
    update_package = UpdatePackage.Field()
    delete_package = DeletePackage.Field()
