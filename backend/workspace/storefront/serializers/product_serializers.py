# Storefront Product Serializers - PUBLIC DATA ONLY
# CRITICAL: NO cost_price, NO profit_margin, NO admin fields exposed

from rest_framework import serializers
from workspace.store.models import Product


class StorefrontProductSerializer(serializers.ModelSerializer):
    """
    Public product data for customers

    SECURITY: Only exposes customer-facing data
    - NO cost_price
    - NO profit_margin
    - NO exact stock_quantity (only status)
    - NO created_by/updated_by
    - NO workspace_id
    """

    stock_status = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    has_discount = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            # Basic info
            'id',
            'name',
            'slug',
            'description',

            # Pricing (PUBLIC ONLY)
            'price',
            'compare_at_price',  # For showing discounts
            'discount_percentage',  # Calculated
            'has_discount',

            # Stock (BOOLEAN STATUS ONLY)
            'stock_status',  # 'in_stock' or 'out_of_stock' only

            # Organization
            'category',
            'sub_category',
            'brand',

            # Physical attributes (for shipping)
            'weight',
            'condition',  # new, used, refurbished

            # Media
            'featured_image',
            'images',

            # Currency
            'currency',

            # Timestamps (basic)
            'created_at',

        
        ]

    def get_stock_status(self, obj):
        """
        Only show if in stock or not (NOT exact quantity)
        Security: Prevent competitors from seeing inventory levels
        """
        if not obj.track_inventory:
            return 'in_stock'

        return 'in_stock' if obj.stock_quantity > 0 else 'out_of_stock'

    def get_discount_percentage(self, obj):
        """Calculate discount percentage if compare_at_price exists"""
        if obj.compare_at_price and obj.compare_at_price > obj.price:
            return int(((obj.compare_at_price - obj.price) / obj.compare_at_price) * 100)
        return 0

    def get_has_discount(self, obj):
        """Check if product has an active discount"""
        return obj.compare_at_price and obj.compare_at_price > obj.price


class StorefrontProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight product serializer for list views
    Optimized for performance in catalog browsing
    """

    stock_status = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'price',
            'compare_at_price',
            'discount_percentage',
            'stock_status',
            'category',
            'brand',
            'featured_image',
            'currency',
        ]

    def get_stock_status(self, obj):
        """Only show if in stock or not"""
        if not obj.track_inventory:
            return 'in_stock'
        return 'in_stock' if obj.stock_quantity > 0 else 'out_of_stock'

    def get_discount_percentage(self, obj):
        """Calculate discount percentage"""
        if obj.compare_at_price and obj.compare_at_price > obj.price:
            return int(((obj.compare_at_price - obj.price) / obj.compare_at_price) * 100)
        return 0
