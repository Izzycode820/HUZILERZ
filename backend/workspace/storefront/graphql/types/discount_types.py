# GraphQL types for Discount models
# IMPORTANT: These types wrap discount models from store app for storefront use

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models.discount_model import Discount
from decimal import Decimal


class ItemDiscountType(graphene.ObjectType):
    """
    Individual item discount breakdown for buy_x_get_y and amount_off_product
    """
    product_id = graphene.ID(required=True)
    product_name = graphene.String(required=True)
    quantity = graphene.Int()
    quantity_discounted = graphene.Int()
    original_price = graphene.Decimal(required=True)
    discount_amount = graphene.Decimal(required=True)


class AppliedDiscountType(graphene.ObjectType):
    """
    Applied discount details for cart display
    
    Lightweight type showing only customer-facing discount info
    """
    code = graphene.String(required=True)
    name = graphene.String(required=True)
    discount_type = graphene.String(required=True)
    discount_amount = graphene.Decimal()
    
    # Optional breakdown for transparency
    item_discounts = graphene.List(ItemDiscountType)


class DiscountValidationType(graphene.ObjectType):
    """
    Result type for discount code validation
    """
    valid = graphene.Boolean(required=True)
    error = graphene.String()
    discount_code = graphene.String()
    discount_name = graphene.String()
    discount_type = graphene.String()
    message = graphene.String()


class ApplyDiscountResultType(graphene.ObjectType):
    """
    Result type for apply discount mutation
    """
    success = graphene.Boolean(required=True)
    error = graphene.String()
    message = graphene.String()
    cart = graphene.Field('workspace.storefront.graphql.types.cart_types.CartType')
    discount = graphene.Field(AppliedDiscountType)
