# Storefront Checkout Serializers - Customer checkout data

from rest_framework import serializers


class CheckoutSerializer(serializers.Serializer):
    """
    Serializer for checkout process
    Collects customer information at checkout
    """

    # Customer information
    customer_name = serializers.CharField(required=True, max_length=255)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=True, max_length=20)

    # Addresses (JSON fields)
    shipping_address = serializers.JSONField(required=False)
    billing_address = serializers.JSONField(required=False)

    # Optional notes
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, data):
        """Validate that at least email or phone is provided"""
        if not data.get('customer_email') and not data.get('customer_phone'):
            raise serializers.ValidationError(
                "Either customer email or phone number must be provided"
            )
        return data


class OrderConfirmationSerializer(serializers.Serializer):
    """
    Serializer for order confirmation response
    Returns order details to customer after successful checkout
    """

    order_id = serializers.UUIDField(read_only=True)
    order_number = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    status = serializers.CharField(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    customer_email = serializers.EmailField(read_only=True, allow_null=True)
    customer_phone = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    message = serializers.CharField(read_only=True)


class OrderTrackingSerializer(serializers.Serializer):
    """
    Public order tracking information
    Limited data for customer to track their order
    """

    order_number = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)
    fulfillment_status = serializers.CharField(read_only=True)
    tracking_number = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    shipped_at = serializers.DateTimeField(read_only=True, allow_null=True)
    delivered_at = serializers.DateTimeField(read_only=True, allow_null=True)
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    # NO admin fields exposed:
    # - customer_full_info ❌
    # - notes ❌
    # - internal status details ❌
