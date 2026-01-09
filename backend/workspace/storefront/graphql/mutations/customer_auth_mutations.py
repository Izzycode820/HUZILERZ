"""
Customer Authentication Mutations - Storefront Public API
Direct phone-based signup/login (no OTP for now)

Phone-First Approach for Cameroon Market:
- Phone is primary identifier
- Email optional
- Simple session management
- Mobile-optimized

TODO: Add OTP verification later for enhanced security
"""

import graphene
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from graphql import GraphQLError
from workspace.core.models.customer_model import Customer, CustomerService
import secrets
import logging

logger = logging.getLogger('workspace.storefront.customer_auth')


# Session configuration
SESSION_CACHE_PREFIX = 'customer_session_'
SESSION_DURATION = 24 * 60 * 60  # 24 hours


class CustomerSignup(graphene.Mutation):
    """
    Customer signup with password - Phone-first approach

    Security: Password is hashed using Django's make_password
    Creates customer account and returns session token
    """

    class Arguments:
        phone = graphene.String(required=True, description="Customer phone number (E.164 format)")
        password = graphene.String(required=True, description="Customer password (min 6 characters)")
        name = graphene.String(required=True, description="Customer full name")
        email = graphene.String(description="Customer email (optional)")
        city = graphene.String(description="Customer city")
        region = graphene.String(description="Cameroon region")

    success = graphene.Boolean()
    customer = graphene.JSONString()
    session_token = graphene.String()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, phone, password, name, email=None, city=None, region=None):
        """
        Signup with password

        Security: Password hashing, workspace scoping
        Performance: Single atomic transaction
        """
        try:
            workspace = info.context.workspace

            # Import service
            from workspace.storefront.services.customer_auth_service import customer_auth_service

            # Call service
            result = customer_auth_service.signup_with_password(
                workspace_id=str(workspace.id),
                phone=phone,
                password=password,
                name=name,
                email=email,
                city=city,
                region=region
            )

            return CustomerSignup(
                success=result['success'],
                customer=result.get('customer'),
                session_token=result.get('session_token'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            logger.error(f"Customer signup failed: {str(e)}", exc_info=True)
            return CustomerSignup(
                success=False,
                error='Signup failed. Please try again.'
            )


class CustomerLogin(graphene.Mutation):
    """
    Customer login with password - Phone-first authentication

    Security: Password verification with check_password
    Validates customer credentials and returns session token
    """

    class Arguments:
        phone = graphene.String(required=True, description="Customer phone number")
        password = graphene.String(required=True, description="Customer password")

    success = graphene.Boolean()
    customer = graphene.JSONString()
    session_token = graphene.String()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, phone, password):
        """
        Login with password

        Security: Password verification, workspace scoping
        Performance: Single database query
        """
        try:
            workspace = info.context.workspace

            # Import service
            from workspace.storefront.services.customer_auth_service import customer_auth_service

            # Call service
            result = customer_auth_service.login_with_password(
                workspace_id=str(workspace.id),
                phone=phone,
                password=password
            )

            return CustomerLogin(
                success=result['success'],
                customer=result.get('customer'),
                session_token=result.get('session_token'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            logger.error(f"Customer login failed: {str(e)}", exc_info=True)
            return CustomerLogin(
                success=False,
                error='Login failed. Please try again.'
            )


class CustomerLogout(graphene.Mutation):
    """
    Customer logout - Invalidate session
    """

    class Arguments:
        session_token = graphene.String(required=True, description="Customer session token")

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, session_token):
        """Invalidate customer session"""
        try:
            session_key = f"{SESSION_CACHE_PREFIX}{session_token}"
            cache.delete(session_key)

            logger.info("Customer logout successful")

            return CustomerLogout(
                success=True,
                message='Logged out successfully'
            )

        except Exception as e:
            logger.error(f"Customer logout failed: {str(e)}", exc_info=True)
            return CustomerLogout(
                success=False,
                message='Logout failed'
            )


class ValidateCustomerSession(graphene.Mutation):
    """
    Validate customer session token

    Used to check if session is still valid and get customer data
    """

    class Arguments:
        session_token = graphene.String(required=True, description="Customer session token")

    success = graphene.Boolean()
    customer = graphene.JSONString()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, session_token):
        """Validate session and return customer data"""
        try:
            workspace = info.context.workspace
            session_data = _validate_customer_session(session_token, workspace.id)

            if not session_data:
                return ValidateCustomerSession(
                    success=False,
                    error='Session expired or invalid'
                )

            # Get customer
            customer = Customer.objects.get(
                id=session_data['customer_id'],
                workspace=workspace,
                is_active=True
            )

            return ValidateCustomerSession(
                success=True,
                customer=_format_customer_for_auth(customer),
                message='Session valid'
            )

        except Customer.DoesNotExist:
            return ValidateCustomerSession(
                success=False,
                error='Customer not found'
            )
        except Exception as e:
            logger.error(f"Session validation failed: {str(e)}", exc_info=True)
            return ValidateCustomerSession(
                success=False,
                error='Session validation failed'
            )


# Helper Functions

def _create_customer_session(customer: Customer) -> str:
    """
    Create customer session and return token

    Session stored in cache with 24-hour expiry
    """
    session_token = secrets.token_urlsafe(32)
    session_key = f"{SESSION_CACHE_PREFIX}{session_token}"

    session_data = {
        'customer_id': str(customer.id),
        'workspace_id': str(customer.workspace_id),
        'phone': customer.phone,
        'created_at': timezone.now().isoformat(),
        'expires_at': timezone.now().timestamp() + SESSION_DURATION
    }

    cache.set(session_key, session_data, SESSION_DURATION)
    return session_token


def _validate_customer_session(session_token: str, workspace_id: str):
    """
    Validate customer session token

    Returns session data if valid, None if expired/invalid
    """
    try:
        session_key = f"{SESSION_CACHE_PREFIX}{session_token}"
        session_data = cache.get(session_key)

        if not session_data:
            return None

        # Check workspace matches
        if str(session_data.get('workspace_id')) != str(workspace_id):
            return None

        # Check if expired
        if timezone.now().timestamp() > session_data['expires_at']:
            cache.delete(session_key)
            return None

        # Extend session (sliding expiration)
        session_data['expires_at'] = timezone.now().timestamp() + SESSION_DURATION
        cache.set(session_key, session_data, SESSION_DURATION)

        return session_data

    except Exception as e:
        logger.error(f"Session validation error: {str(e)}", exc_info=True)
        return None


def _format_customer_for_auth(customer: Customer) -> dict:
    """Format customer data for authentication responses"""
    return {
        'id': str(customer.id),
        'name': customer.name,
        'phone': customer.phone,
        'email': customer.email,
        'city': customer.city,
        'region': customer.region,
        'customer_type': customer.customer_type,
        'is_verified': customer.is_verified,
        'total_orders': customer.total_orders,
        'total_spent': float(customer.total_spent),
        'is_high_value': customer.is_high_value,
        'is_frequent_buyer': customer.is_frequent_buyer,
        'created_at': customer.created_at.isoformat()
    }


# Mutation Collection

class CustomerAuthMutations(graphene.ObjectType):
    """
    Customer authentication mutations for storefront

    Phone-first approach optimized for Cameroon market
    Direct login/signup (OTP to be added later)
    """

    customer_signup = CustomerSignup.Field()
    customer_login = CustomerLogin.Field()
    customer_logout = CustomerLogout.Field()
    validate_customer_session = ValidateCustomerSession.Field()
