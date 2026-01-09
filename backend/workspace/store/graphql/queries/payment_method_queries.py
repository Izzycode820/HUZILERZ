"""
Payment Method GraphQL Queries for Admin Store API

Queries for retrieving merchant payment method configuration.
Workspace-scoped via JWT middleware.
"""

import graphene
import logging
from payments.models import MerchantPaymentMethod
from payments.services.registry import registry
from ..types.payment_method_types import (
    MerchantPaymentMethodType,
    AvailableProviderType
)

logger = logging.getLogger(__name__)


class PaymentMethodQueries(graphene.ObjectType):
    """
    Payment method queries for admin dashboard.
    All queries are automatically workspace-scoped via JWT middleware.
    """
    
    payment_methods = graphene.List(
        MerchantPaymentMethodType,
        description="List configured payment methods for current workspace"
    )
    
    available_providers = graphene.List(
        AvailableProviderType,
        description="List payment providers available to add"
    )
    
    def resolve_payment_methods(self, info):
        """
        Get all configured payment methods for workspace.
        
        Returns:
            List of MerchantPaymentMethod ordered by enabled status
        """
        workspace = info.context.workspace
        user = info.context.user
        
        if not workspace:
            logger.warning("No workspace in context for payment_methods query")
            return []
        
        # Get methods owned by user for this workspace
        methods = MerchantPaymentMethod.objects.filter(
            workspace_id=str(workspace.id),
            workspace_owner=user
        ).order_by('-enabled', '-last_used_at')
        
        return methods
    
    def resolve_available_providers(self, info):
        """
        Get list of available payment providers.
        
        Checks which providers are already added to workspace
        so UI can show/hide "Add" buttons appropriately.
        
        Returns:
            List of AvailableProviderType with already_added flag
        """
        workspace = info.context.workspace
        user = info.context.user
        
        if not workspace:
            logger.warning("No workspace in context for available_providers query")
            return []
        
        # Get already configured providers
        existing_providers = set(
            MerchantPaymentMethod.objects.filter(
                workspace_id=str(workspace.id),
                workspace_owner=user
            ).values_list('provider_name', flat=True)
        )
        
        # Get all registered providers from registry
        all_providers = registry.list_providers()
        
        # Provider metadata (Fapshi only for now)
        provider_metadata = {
            'fapshi': {
                'display_name': 'Fapshi (Mobile Money)',
                'description': 'Accept MTN MoMo and Orange Money payments via Fapshi hosted checkout',
                'requires_url': True
            }
        }
        
        result = []
        for provider in all_providers:
            meta = provider_metadata.get(provider, {
                'display_name': provider.title(),
                'description': f'Pay with {provider.title()}',
                'requires_url': True
            })
            
            result.append(AvailableProviderType(
                provider=provider,
                display_name=meta['display_name'],
                description=meta['description'],
                requires_url=meta['requires_url'],
                already_added=provider in existing_providers
            ))
        
        return result
