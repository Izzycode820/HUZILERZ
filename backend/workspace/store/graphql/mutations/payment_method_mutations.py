"""
Payment Method GraphQL Mutations for Admin Store API

Mutations for managing merchant payment method configuration.
Workspace-scoped via JWT middleware.
All mutations use atomic transactions for data integrity.
"""

import graphene
import logging
from django.db import transaction
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from payments.models import MerchantPaymentMethod
from payments.services.registry import registry
from ..types.payment_method_types import (
    MerchantPaymentMethodType,
    AddPaymentMethodInput,
    UpdatePaymentMethodInput
)

logger = logging.getLogger(__name__)


def validate_checkout_url(url):
    """
    Validate checkout URL format and security.
    
    Args:
        url: URL string to validate
        
    Raises:
        ValueError: If URL is invalid or insecure
    """
    if not url:
        raise ValueError("Checkout URL is required for Fapshi")
    
    # Basic URL validation
    validator = URLValidator(schemes=['https'])
    try:
        validator(url)
    except ValidationError:
        raise ValueError("Checkout URL must be a valid HTTPS URL")
    
    # Fapshi URL pattern validation (flexible for different Fapshi URL formats)
    allowed_domains = ['fapshi.com', 'checkout.fapshi.com', 'pay.fapshi.com']
    is_valid_domain = any(domain in url.lower() for domain in allowed_domains)
    
    if not is_valid_domain:
        raise ValueError("Checkout URL must be a valid Fapshi URL (e.g., https://checkout.fapshi.com/...)")


class AddPaymentMethod(graphene.Mutation):
    """
    Add a payment method to workspace.
    
    For Fapshi: Requires checkout_url from merchant's Fapshi dashboard.
    Uses atomic transaction to ensure data integrity.
    """
    
    class Arguments:
        input = AddPaymentMethodInput(required=True)
    
    success = graphene.Boolean()
    payment_method = graphene.Field(MerchantPaymentMethodType)
    message = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user
        
        if not workspace:
            logger.warning("No workspace in context for addPaymentMethod mutation")
            return AddPaymentMethod(
                success=False,
                error="Workspace not found"
            )
        
        provider_name = input.provider_name
        checkout_url = input.checkout_url
        
        try:
            # Check payment processing capability
            from subscription.services.gating import check_payment_processing
            allowed, error_msg = check_payment_processing(workspace)
            if not allowed:
                return AddPaymentMethod(
                    success=False,
                    error=error_msg
                )

            # Validate provider exists
            if provider_name not in registry.list_providers():
                return AddPaymentMethod(
                    success=False,
                    error=f"Payment provider '{provider_name}' is not available"
                )
            
            # Validate checkout URL for Fapshi
            if provider_name == 'fapshi':
                validate_checkout_url(checkout_url)
            
            with transaction.atomic():
                # Check for existing method (use select_for_update to prevent race)
                existing = MerchantPaymentMethod.objects.select_for_update().filter(
                    workspace_id=str(workspace.id),
                    provider_name=provider_name
                ).first()
                
                if existing:
                    return AddPaymentMethod(
                        success=False,
                        error=f"{provider_name.title()} is already configured for this workspace"
                    )
                
                # Get provider capabilities
                try:
                    adapter = registry.get_adapter(provider_name, {})
                    capabilities = adapter.get_capabilities()
                except Exception as e:
                    logger.error(f"Failed to get adapter capabilities: {e}")
                    capabilities = {'payment_modes': ['redirect']}
                
                # Create payment method
                method = MerchantPaymentMethod.objects.create(
                    workspace_id=str(workspace.id),
                    workspace_owner=user,
                    provider_name=provider_name,
                    checkout_url=checkout_url,
                    config_encrypted='',
                    enabled=True,
                    verified=True,
                    permissions=capabilities
                )
                
                logger.info(
                    f"Payment method added: {provider_name} for workspace {workspace.id}"
                )
                
                return AddPaymentMethod(
                    success=True,
                    payment_method=method,
                    message=f"{provider_name.title()} payment method added successfully"
                )
                
        except ValueError as e:
            return AddPaymentMethod(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Add payment method failed: {e}", exc_info=True)
            return AddPaymentMethod(
                success=False,
                error="Failed to add payment method. Please try again."
            )


class TogglePaymentMethod(graphene.Mutation):
    """
    Enable or disable a payment method.
    
    Uses atomic transaction with row-level locking.
    """
    
    class Arguments:
        method_id = graphene.ID(required=True)
        enabled = graphene.Boolean(required=True)
    
    success = graphene.Boolean()
    payment_method = graphene.Field(MerchantPaymentMethodType)
    message = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, method_id, enabled):
        workspace = info.context.workspace
        user = info.context.user
        
        if not workspace:
            return TogglePaymentMethod(
                success=False,
                error="Workspace not found"
            )
        
        try:
            with transaction.atomic():
                # Get method with row lock and validate ownership
                method = MerchantPaymentMethod.objects.select_for_update().filter(
                    id=method_id,
                    workspace_id=str(workspace.id),
                    workspace_owner=user
                ).first()
                
                if not method:
                    return TogglePaymentMethod(
                        success=False,
                        error="Payment method not found"
                    )
                
                method.enabled = enabled
                method.save(update_fields=['enabled', 'updated_at'])
                
                status = "enabled" if enabled else "disabled"
                logger.info(
                    f"Payment method {status}: {method.provider_name} "
                    f"for workspace {workspace.id}"
                )
                
                return TogglePaymentMethod(
                    success=True,
                    payment_method=method,
                    message=f"Payment method {status}"
                )
                
        except Exception as e:
            logger.error(f"Toggle payment method failed: {e}", exc_info=True)
            return TogglePaymentMethod(
                success=False,
                error="Failed to update payment method"
            )


class UpdatePaymentMethod(graphene.Mutation):
    """
    Update payment method configuration (e.g., checkout URL).
    
    Uses atomic transaction with row-level locking.
    """
    
    class Arguments:
        method_id = graphene.ID(required=True)
        input = UpdatePaymentMethodInput(required=True)
    
    success = graphene.Boolean()
    payment_method = graphene.Field(MerchantPaymentMethodType)
    message = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, method_id, input):
        workspace = info.context.workspace
        user = info.context.user
        
        if not workspace:
            return UpdatePaymentMethod(
                success=False,
                error="Workspace not found"
            )
        
        try:
            with transaction.atomic():
                method = MerchantPaymentMethod.objects.select_for_update().filter(
                    id=method_id,
                    workspace_id=str(workspace.id),
                    workspace_owner=user
                ).first()
                
                if not method:
                    return UpdatePaymentMethod(
                        success=False,
                        error="Payment method not found"
                    )
                
                update_fields = ['updated_at']
                
                # Update checkout URL if provided
                if input.checkout_url is not None:
                    if method.provider_name == 'fapshi':
                        validate_checkout_url(input.checkout_url)
                    method.checkout_url = input.checkout_url
                    update_fields.append('checkout_url')
                
                # Update enabled status if provided
                if input.enabled is not None:
                    method.enabled = input.enabled
                    update_fields.append('enabled')
                
                method.save(update_fields=update_fields)
                
                logger.info(
                    f"Payment method updated: {method.provider_name} "
                    f"for workspace {workspace.id}"
                )
                
                return UpdatePaymentMethod(
                    success=True,
                    payment_method=method,
                    message="Payment method updated successfully"
                )
                
        except ValueError as e:
            return UpdatePaymentMethod(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Update payment method failed: {e}", exc_info=True)
            return UpdatePaymentMethod(
                success=False,
                error="Failed to update payment method"
            )


class RemovePaymentMethod(graphene.Mutation):
    """
    Remove a payment method from workspace.
    
    Uses atomic transaction with row-level locking.
    """
    
    class Arguments:
        method_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, method_id):
        workspace = info.context.workspace
        user = info.context.user
        
        if not workspace:
            return RemovePaymentMethod(
                success=False,
                error="Workspace not found"
            )
        
        try:
            with transaction.atomic():
                method = MerchantPaymentMethod.objects.select_for_update().filter(
                    id=method_id,
                    workspace_id=str(workspace.id),
                    workspace_owner=user
                ).first()
                
                if not method:
                    return RemovePaymentMethod(
                        success=False,
                        error="Payment method not found"
                    )
                
                provider_name = method.provider_name
                method.delete()
                
                logger.info(
                    f"Payment method removed: {provider_name} "
                    f"for workspace {workspace.id}"
                )
                
                return RemovePaymentMethod(
                    success=True,
                    message=f"{provider_name.title()} payment method removed"
                )
                
        except Exception as e:
            logger.error(f"Remove payment method failed: {e}", exc_info=True)
            return RemovePaymentMethod(
                success=False,
                error="Failed to remove payment method"
            )


class PaymentMethodMutations(graphene.ObjectType):
    """Payment method mutations collection."""
    
    add_payment_method = AddPaymentMethod.Field()
    toggle_payment_method = TogglePaymentMethod.Field()
    update_payment_method = UpdatePaymentMethod.Field()
    remove_payment_method = RemovePaymentMethod.Field()
