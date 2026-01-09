"""
Customer Service GraphQL Mutations

Production-ready customer mutations using CustomerMutationService
Follows industry standards for performance and reliability

Performance: < 100ms response time for customer operations
Scalability: Bulk operations with background processing
Reliability: Atomic transactions with comprehensive error handling
Security: Workspace scoping and permission validation
"""

import graphene
from graphql import GraphQLError
from workspace.core.services.customer_service import customer_mutation_service
from ..types.customer_types import CustomerType
from workspace.store.utils.workspace_permissions import assert_permission


class CustomerUpdateInput(graphene.InputObjectType):
    """
    Input for customer updates

    Validation: Field validation and data integrity
    Security: Workspace scoping via JWT middleware
    """

    name = graphene.String()
    email = graphene.String()
    customer_type = graphene.String()
    city = graphene.String()
    region = graphene.String()
    address = graphene.String()
    tags = graphene.JSONString()
    sms_notifications = graphene.Boolean()
    whatsapp_notifications = graphene.Boolean()
    is_active = graphene.Boolean()


class CustomerCreateInput(graphene.InputObjectType):
    """
    Input for customer creation

    Validation: Required fields and data structure
    Security: Workspace scoping via JWT middleware
    """

    phone = graphene.String(required=True)
    name = graphene.String(required=True)
    email = graphene.String()
    customer_type = graphene.String(default_value='individual')
    city = graphene.String()
    region = graphene.String()
    address = graphene.String()
    tags = graphene.JSONString()
    sms_notifications = graphene.Boolean(default_value=True)
    whatsapp_notifications = graphene.Boolean(default_value=True)


class CustomerTagUpdateInput(graphene.InputObjectType):
    """Input for customer tag operations"""

    add_tags = graphene.List(graphene.String)
    remove_tags = graphene.List(graphene.String)


class UpdateCustomer(graphene.Mutation):
    """
    Update customer with atomic transaction using CustomerMutationService

    Performance: Atomic update with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive error handling with rollback
    """

    class Arguments:
        customer_id = graphene.String(required=True)
        update_data = CustomerUpdateInput(required=True)

    success = graphene.Boolean()
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, customer_id, update_data):
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:update')

        try:
            # Convert GraphQL input to service format
            update_dict = {}
            for field, value in update_data.items():
                if value is not None:
                    update_dict[field] = value

            result = customer_mutation_service.update_customer(
                workspace=workspace,
                customer_id=customer_id,
                update_data=update_dict,
                user=user
            )

            return UpdateCustomer(
                success=result['success'],
                customer=result.get('customer'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer update mutation failed: {str(e)}", exc_info=True)

            return UpdateCustomer(
                success=False,
                error=f"Customer update failed: {str(e)}"
            )


class DeleteCustomer(graphene.Mutation):
    """
    Delete customer with validation and atomic transaction using CustomerMutationService

    Performance: Atomic deletion with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive validation and rollback
    """

    class Arguments:
        customer_id = graphene.String(required=True)

    success = graphene.Boolean()
    deleted_id = graphene.String()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, customer_id):
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:delete')

        try:
            result = customer_mutation_service.delete_customer(
                workspace=workspace,
                customer_id=customer_id,
                user=user
            )

            return DeleteCustomer(
                success=result['success'],
                deleted_id=result.get('deleted_id'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer deletion mutation failed: {str(e)}", exc_info=True)

            return DeleteCustomer(
                success=False,
                error=f"Customer deletion failed: {str(e)}"
            )


class ToggleCustomerStatus(graphene.Mutation):
    """
    Toggle customer active status with validation using CustomerMutationService

    Performance: Atomic status update
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive status validation
    """

    class Arguments:
        customer_id = graphene.String(required=True)
        new_status = graphene.Boolean(required=True)

    success = graphene.Boolean()
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, customer_id, new_status):
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:update')

        try:
            result = customer_mutation_service.toggle_customer_status(
                workspace=workspace,
                customer_id=customer_id,
                new_status=new_status,
                user=user
            )

            return ToggleCustomerStatus(
                success=result['success'],
                customer=result.get('customer'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer status update mutation failed: {str(e)}", exc_info=True)

            return ToggleCustomerStatus(
                success=False,
                error=f"Customer status update failed: {str(e)}"
            )


class CreateCustomer(graphene.Mutation):
    """
    Create customer with atomic transaction using CustomerMutationService

    Performance: Atomic creation with validation
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive validation and rollback
    """

    class Arguments:
        customer_data = CustomerCreateInput(required=True)

    success = graphene.Boolean()
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, customer_data):
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:create')

        try:
            # Convert GraphQL input to service format
            customer_dict = {
                'phone': customer_data.phone,
                'name': customer_data.name,
                'email': customer_data.email,
                'customer_type': customer_data.customer_type,
                'city': customer_data.city,
                'region': customer_data.region,
                'address': customer_data.address,
                'tags': customer_data.tags,
                'sms_notifications': customer_data.sms_notifications,
                'whatsapp_notifications': customer_data.whatsapp_notifications
            }

            result = customer_mutation_service.create_customer(
                workspace=workspace,
                customer_data=customer_dict,
                user=user
            )

            return CreateCustomer(
                success=result['success'],
                customer=result.get('customer'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer creation mutation failed: {str(e)}", exc_info=True)

            return CreateCustomer(
                success=False,
                error=f"Customer creation failed: {str(e)}"
            )


class UpdateCustomerTags(graphene.Mutation):
    """
    Update customer tags with atomic transaction using CustomerMutationService

    Performance: Atomic tag operations
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive tag validation
    """

    class Arguments:
        customer_id = graphene.String(required=True)
        tag_operations = CustomerTagUpdateInput(required=True)

    success = graphene.Boolean()
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, customer_id, tag_operations):
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:update')

        try:
            # Convert GraphQL input to service format
            tag_dict = {}
            if tag_operations.add_tags:
                tag_dict['add_tags'] = tag_operations.add_tags
            if tag_operations.remove_tags:
                tag_dict['remove_tags'] = tag_operations.remove_tags

            result = customer_mutation_service.update_customer_tags(
                workspace=workspace,
                customer_id=customer_id,
                tag_operations=tag_dict,
                user=user
            )

            return UpdateCustomerTags(
                success=result['success'],
                customer=result.get('customer'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer tag update mutation failed: {str(e)}", exc_info=True)

            return UpdateCustomerTags(
                success=False,
                error=f"Customer tag update failed: {str(e)}"
            )


class CustomerMutations(graphene.ObjectType):
    """
    Customer mutations collection

    All mutations follow production standards for performance and security
    Integrates with modern CustomerMutationService for business logic
    """

    create_customer = CreateCustomer.Field()
    update_customer = UpdateCustomer.Field()
    delete_customer = DeleteCustomer.Field()
    toggle_customer_status = ToggleCustomerStatus.Field()
    update_customer_tags = UpdateCustomerTags.Field()