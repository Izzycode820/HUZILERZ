"""
Customer Profile Mutations - Storefront Public API
Consolidated profile management for Cameroon market

Phone-First Approach:
- Single mutation for all profile updates
- Handles profile data, addresses, and preferences
- Mobile-optimized (minimal network calls)
"""

import graphene
from graphql import GraphQLError
from workspace.storefront.services.customer_profile_service import customer_profile_service
import logging

logger = logging.getLogger('workspace.storefront.customer_profile')


# Input Types

class ProfileDataInput(graphene.InputObjectType):
    """Input for basic profile data"""
    name = graphene.String(description="Customer name")
    email = graphene.String(description="Customer email (optional)")
    customer_type = graphene.String(description="Customer type (individual, business, etc.)")
    city = graphene.String(description="Customer city")
    region = graphene.String(description="Cameroon region")


class AddressInput(graphene.InputObjectType):
    """Input for address data"""
    id = graphene.Int(description="Address ID (for update/remove operations)")
    name = graphene.String(description="Address label (e.g., Home, Work)")
    street = graphene.String(description="Street address")
    city = graphene.String(description="City")
    region = graphene.String(description="Cameroon region")
    landmark = graphene.String(description="Nearby landmark")
    phone = graphene.String(description="Contact phone for this address")


class AddressOperationsInput(graphene.InputObjectType):
    """
    Input for address operations

    All fields are optional - provide only the operations you need
    """
    add = graphene.List(AddressInput, description="Add new address(es)")
    update = graphene.Field(AddressInput, description="Update existing address (requires id)")
    remove = graphene.Int(description="Remove address by ID")
    set_default = graphene.Int(description="Set default address by ID")


class PreferencesInput(graphene.InputObjectType):
    """Input for communication preferences"""
    sms_notifications = graphene.Boolean(description="Receive SMS notifications")
    email_notifications = graphene.Boolean(description="Receive email notifications")
    whatsapp_notifications = graphene.Boolean(description="Receive WhatsApp notifications")


# Mutations

class UpdateCustomerProfile(graphene.Mutation):
    """
    Consolidated profile update mutation

    Updates profile, addresses, and preferences in ONE operation
    All parameters are optional - update only what you need

    Cameroon Market: Phone-first, mobile-optimized, single atomic operation
    """

    class Arguments:
        customer_id = graphene.String(required=True, description="Customer ID")
        session_token = graphene.String(required=True, description="Customer session token")
        profile_data = ProfileDataInput(description="Optional profile data to update")
        addresses_data = AddressOperationsInput(description="Optional address operations")
        preferences_data = PreferencesInput(description="Optional communication preferences")

    success = graphene.Boolean()
    profile = graphene.JSONString()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, customer_id, session_token, profile_data=None, addresses_data=None, preferences_data=None):
        """
        Consolidated profile update

        Security: Validates session token and workspace scoping
        Performance: Single atomic transaction
        """
        try:
            workspace = info.context.workspace

            # Validate session (basic validation - can be enhanced)
            from workspace.storefront.graphql.mutations.customer_auth_mutations import _validate_customer_session
            session_data = _validate_customer_session(session_token, str(workspace.id))

            if not session_data:
                return UpdateCustomerProfile(
                    success=False,
                    error='Session expired or invalid'
                )

            # Verify customer ID matches session
            if str(session_data['customer_id']) != str(customer_id):
                return UpdateCustomerProfile(
                    success=False,
                    error='Unauthorized'
                )

            # Convert GraphQL inputs to service format
            profile_dict = None
            if profile_data:
                profile_dict = {
                    k: v for k, v in profile_data.items() if v is not None
                }

            addresses_dict = None
            if addresses_data:
                addresses_dict = {}
                if addresses_data.add:
                    addresses_dict['add'] = [
                        {k: v for k, v in addr.items() if v is not None}
                        for addr in addresses_data.add
                    ]
                if addresses_data.update:
                    addresses_dict['update'] = {
                        k: v for k, v in addresses_data.update.items() if v is not None
                    }
                if addresses_data.remove:
                    addresses_dict['remove'] = addresses_data.remove
                if addresses_data.set_default:
                    addresses_dict['set_default'] = addresses_data.set_default

            preferences_dict = None
            if preferences_data:
                preferences_dict = {
                    k: v for k, v in preferences_data.items() if v is not None
                }

            # Call service
            result = customer_profile_service.update_customer_profile(
                workspace_id=str(workspace.id),
                customer_id=customer_id,
                profile_data=profile_dict,
                addresses_data=addresses_dict,
                preferences_data=preferences_dict
            )

            if result['success']:
                logger.info(
                    f"Profile updated for customer {customer_id}",
                    extra={'workspace_id': workspace.id}
                )

            return UpdateCustomerProfile(
                success=result['success'],
                profile=result.get('profile'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}", exc_info=True)
            return UpdateCustomerProfile(
                success=False,
                error='Profile update failed. Please try again.'
            )


class GetCustomerProfile(graphene.Mutation):
    """
    Get customer profile data

    Returns complete profile with addresses, preferences, and order stats
    """

    class Arguments:
        customer_id = graphene.String(required=True, description="Customer ID")
        session_token = graphene.String(required=True, description="Customer session token")

    success = graphene.Boolean()
    profile = graphene.JSONString()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, customer_id, session_token):
        """
        Get customer profile

        Security: Validates session token and customer ownership
        """
        try:
            workspace = info.context.workspace

            # Validate session
            from workspace.storefront.graphql.mutations.customer_auth_mutations import _validate_customer_session
            session_data = _validate_customer_session(session_token, str(workspace.id))

            if not session_data:
                return GetCustomerProfile(
                    success=False,
                    error='Session expired or invalid'
                )

            # Verify customer ID matches session
            if str(session_data['customer_id']) != str(customer_id):
                return GetCustomerProfile(
                    success=False,
                    error='Unauthorized'
                )

            # Get profile
            result = customer_profile_service.get_customer_profile(
                workspace_id=str(workspace.id),
                customer_id=customer_id
            )

            return GetCustomerProfile(
                success=result['success'],
                profile=result.get('profile'),
                error=result.get('error')
            )

        except Exception as e:
            logger.error(f"Failed to get profile: {str(e)}", exc_info=True)
            return GetCustomerProfile(
                success=False,
                error='Failed to load profile. Please try again.'
            )


class GetCustomerOrders(graphene.Mutation):
    """
    Get customer order summary

    Returns order statistics (total orders, total spent, etc.)
    """

    class Arguments:
        customer_id = graphene.String(required=True, description="Customer ID")
        session_token = graphene.String(required=True, description="Customer session token")

    success = graphene.Boolean()
    order_summary = graphene.JSONString()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, customer_id, session_token):
        """Get customer order summary"""
        try:
            workspace = info.context.workspace

            # Validate session
            from workspace.storefront.graphql.mutations.customer_auth_mutations import _validate_customer_session
            session_data = _validate_customer_session(session_token, str(workspace.id))

            if not session_data:
                return GetCustomerOrders(
                    success=False,
                    error='Session expired or invalid'
                )

            # Verify customer ID matches session
            if str(session_data['customer_id']) != str(customer_id):
                return GetCustomerOrders(
                    success=False,
                    error='Unauthorized'
                )

            # Get order summary
            result = customer_profile_service.get_customer_orders_summary(
                workspace_id=str(workspace.id),
                customer_id=customer_id
            )

            return GetCustomerOrders(
                success=result['success'],
                order_summary=result.get('order_summary'),
                error=result.get('error')
            )

        except Exception as e:
            logger.error(f"Failed to get order summary: {str(e)}", exc_info=True)
            return GetCustomerOrders(
                success=False,
                error='Failed to load order summary. Please try again.'
            )


# Mutation Collection

class CustomerProfileMutations(graphene.ObjectType):
    """
    Customer profile mutations for storefront

    Simplified phone-first approach for Cameroon market
    """

    update_customer_profile = UpdateCustomerProfile.Field()
    get_customer_profile = GetCustomerProfile.Field()
    get_customer_orders = GetCustomerOrders.Field()
