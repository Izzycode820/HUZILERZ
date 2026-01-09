"""
Payment Method GraphQL Types for Admin Store API

GraphQL types for MerchantPaymentMethod model operations.
Workspace-scoped via JWT middleware.
"""

import graphene
from graphene_django import DjangoObjectType
from payments.models import MerchantPaymentMethod
from workspace.store.graphql.types.common_types import BaseConnection


class ProviderCapabilitiesType(graphene.ObjectType):
    """
    GraphQL type for payment provider capabilities.
    Nested object within MerchantPaymentMethodType.
    """
    payment_modes = graphene.List(graphene.String)
    supported_currencies = graphene.List(graphene.String)
    supports_refunds = graphene.Boolean()
    supports_webhooks = graphene.Boolean()
    display_name = graphene.String()


class MerchantPaymentMethodType(DjangoObjectType):
    """
    GraphQL type for MerchantPaymentMethod model.
    
    Exposes payment method configuration for workspace settings.
    """
    id = graphene.ID(required=True)
    
    class Meta:
        model = MerchantPaymentMethod
        fields = (
            'id', 'provider_name', 'checkout_url',
            'enabled', 'verified',
            'total_transactions', 'successful_transactions',
            'last_used_at', 'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection
    
    # Computed fields
    success_rate = graphene.Float(description="Success rate percentage")
    display_name = graphene.String(description="Human-readable provider name")
    capabilities = graphene.Field(ProviderCapabilitiesType)
    
    def resolve_id(self, info):
        return str(self.id)
    
    def resolve_success_rate(self, info):
        """Calculate success rate percentage."""
        return self.success_rate
    
    def resolve_display_name(self, info):
        """Get human-readable provider name."""
        display_names = {
            'fapshi': 'Fapshi (Mobile Money)',
            'mtn': 'MTN Mobile Money',
            'orange': 'Orange Money',
        }
        return display_names.get(self.provider_name, self.provider_name.title())
    
    def resolve_capabilities(self, info):
        """Get provider capabilities from permissions field."""
        perms = self.permissions or {}
        return ProviderCapabilitiesType(
            payment_modes=perms.get('payment_modes', []),
            supported_currencies=perms.get('supported_currencies', ['XAF']),
            supports_refunds=perms.get('supports_refunds', False),
            supports_webhooks=perms.get('supports_webhooks', False),
            display_name=perms.get('display_name', self.provider_name.title())
        )


class AvailableProviderType(graphene.ObjectType):
    """
    GraphQL type for available payment providers.
    Used when adding new payment methods.
    """
    provider = graphene.String(required=True)
    display_name = graphene.String(required=True)
    description = graphene.String()
    requires_url = graphene.Boolean(description="Whether checkout URL is required")
    already_added = graphene.Boolean(description="Whether already configured for workspace")


class AddPaymentMethodInput(graphene.InputObjectType):
    """
    Input type for adding a payment method to workspace.
    """
    provider_name = graphene.String(
        required=True,
        description="Payment provider identifier (e.g., 'fapshi')"
    )
    checkout_url = graphene.String(
        description="Fapshi checkout URL from merchant's Fapshi dashboard"
    )


class UpdatePaymentMethodInput(graphene.InputObjectType):
    """
    Input type for updating payment method configuration.
    """
    checkout_url = graphene.String(description="Updated checkout URL")
    enabled = graphene.Boolean(description="Enable/disable payment method")
