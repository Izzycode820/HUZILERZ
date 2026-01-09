# GraphQL types for Cart and CartItem models
# IMPORTANT: These types wrap models owned by storefront app

import graphene
from graphene_django import DjangoObjectType
from workspace.storefront.models import Cart, CartItem
from workspace.store.models import Product, ProductVariant
from .product_types import ProductType, ProductVariantType
from .common_types import BaseConnection
from .discount_types import AppliedDiscountType


class CartItemType(DjangoObjectType):
    """
    GraphQL type for CartItem model

    Performance: Uses select_related for product optimization
    """

    id = graphene.ID(required=True)

    class Meta:
        model = CartItem
        fields = ('id', 'quantity', 'price_snapshot', 'added_at', 'updated_at')
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    # Custom fields
    product = graphene.Field(lambda: ProductType)
    variant = graphene.Field(lambda: ProductVariantType)
    total_price = graphene.Decimal()

    def resolve_product(self, info):
        """Resolve product with optimization"""
        # Use DataLoader for batching
        if hasattr(info.context, 'dataloaders'):
            loader = info.context.dataloaders['product_loader']
            return loader.load(self.product_id)

        # Fallback to direct query
        return Product.objects.filter(
            id=self.product_id,
            status='published',
            is_active=True
        ).first()

    def resolve_variant(self, info):
        """Resolve variant with optimization"""
        if not self.variant_id:
            return None

        # Use DataLoader for batching
        if hasattr(info.context, 'dataloaders'):
            loader = info.context.dataloaders['variant_loader']
            return loader.load(self.variant_id)

        # Fallback to direct query
        return ProductVariant.objects.filter(
            id=self.variant_id,
            is_active=True
        ).first()

    def resolve_total_price(self, info):
        """Calculate total price for cart item"""
        return self.total_price


class CartType(DjangoObjectType):
    """
    GraphQL type for Cart model

    Performance: Uses prefetch_related for items optimization
    """

    id = graphene.ID(required=True)

    class Meta:
        model = Cart
        fields = (
            'id', 'session_id', 'currency', 'is_active',
            'subtotal', 'abandoned_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    # Custom fields
    items = graphene.List(CartItemType)
    item_count = graphene.Int()
    is_empty = graphene.Boolean()
    is_guest_cart = graphene.Boolean()
    
    # Discount fields
    discount_code = graphene.String()
    discount_amount = graphene.Decimal()
    total = graphene.Decimal()
    has_discount = graphene.Boolean()
    applied_discount = graphene.Field(AppliedDiscountType)

    def resolve_items(self, info):
        """Resolve cart items with optimization"""
        return self.items.select_related('product', 'variant').all()

    def resolve_item_count(self, info):
        """Get total number of items in cart"""
        return self.item_count

    def resolve_is_empty(self, info):
        """Check if cart is empty"""
        return self.is_empty

    def resolve_is_guest_cart(self, info):
        """Check if this is a guest cart"""
        return self.is_guest_cart
    
    def resolve_discount_code(self, info):
        """Get applied discount code"""
        return self.discount_code or ''
    
    def resolve_discount_amount(self, info):
        """Get discount amount"""
        from decimal import Decimal
        return self.discount_amount or Decimal('0.00')
    
    def resolve_total(self, info):
        """Calculate cart total (subtotal - discount)"""
        from decimal import Decimal
        discount = self.discount_amount or Decimal('0.00')
        return self.subtotal - discount
    
    def resolve_has_discount(self, info):
        """Check if cart has discount applied"""
        return bool(self.applied_discount_id)
    
    def resolve_applied_discount(self, info):
        """Resolve applied discount details"""
        if not self.applied_discount_id:
            return None
        return self.applied_discount


class CartCreationResultType(graphene.ObjectType):
    """
    Result type for cart creation mutations
    """
    session_id = graphene.String()
    expires_at = graphene.DateTime()
    cart = graphene.Field(CartType)