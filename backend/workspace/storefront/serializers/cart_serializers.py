# Storefront Cart Serializers - Public cart data for customers

from rest_framework import serializers
from workspace.storefront.models import Cart, CartItem
from .product_serializers import StorefrontProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """
    Cart item with product details
    Uses public product serializer
    """

    product = StorefrontProductListSerializer(read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'quantity',
            'price_snapshot',
            'total_price',
            'added_at',
        ]


class StorefrontCartSerializer(serializers.ModelSerializer):
    """
    Public cart data for customers

    SECURITY: NO workspace_id exposed
    Only session_id used for identification
    """

    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'session_id',
            'items',
            'item_count',
            'subtotal',
            'currency',
            'created_at',
            'updated_at',
        ]

    def get_item_count(self, obj):
        """Total number of items in cart"""
        return obj.item_count


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""

    product_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""

    quantity = serializers.IntegerField(required=True, min_value=0)

    def validate_quantity(self, value):
        """Validate quantity (0 means remove)"""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value
