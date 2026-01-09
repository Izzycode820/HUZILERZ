# Input types for GraphQL mutations

import graphene
from workspace.core.graphql.types import CustomerInfoInput




class CheckoutInput(graphene.InputObjectType):
    """
    Input type for checkout mutations
    """
    store_slug = graphene.String(required=True)
    session_id = graphene.String(required=True)
    customer_info = CustomerInfoInput(required=True)  # From core
    shipping_method = graphene.String()
    payment_method = graphene.String()
    notes = graphene.String()


class WhatsAppOrderInput(graphene.InputObjectType):
    """
    Input type for WhatsApp order requests
    """
    store_slug = graphene.String(required=True)
    session_id = graphene.String(required=True)
    whatsapp_number = graphene.String(required=True)
    customer_info = CustomerInfoInput(required=True)  # From core
    notes = graphene.String()
