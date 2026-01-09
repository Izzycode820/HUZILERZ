"""
Store Profile GraphQL Types for Admin Store API

GraphQL types for StoreProfile model operations.
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import StoreProfile
from workspace.store.graphql.types.common_types import BaseConnection


class StoreProfileType(DjangoObjectType):
    """
    GraphQL type for StoreProfile model
    
    Exposes store settings for the General Settings page.
    """
    id = graphene.ID(required=True)
    
    class Meta:
        model = StoreProfile
        fields = (
            'id', 'store_name', 'store_description', 
            'store_email', 'support_email',
            'phone_number', 'whatsapp_number',
            'currency', 'timezone',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection
    
    def resolve_id(self, info):
        return str(self.id)


class StoreProfileInput(graphene.InputObjectType):
    """
    Input type for updating store profile settings.
    All fields optional - only provided fields are updated.
    """
    store_name = graphene.String(description="Display name for the store")
    store_description = graphene.String(description="Store description or tagline")
    store_email = graphene.String(description="Primary contact email")
    support_email = graphene.String(description="Customer support email")
    phone_number = graphene.String(description="Store phone (Cameroon format: +237XXXXXXXXX)")
    whatsapp_number = graphene.String(description="WhatsApp number (Cameroon format: +237XXXXXXXXX)")
    timezone = graphene.String(description="Store timezone")
