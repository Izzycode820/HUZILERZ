"""
Payment Serializers
REST API serializers for payment views
"""
from rest_framework import serializers
from .models import PaymentIntent, MerchantPaymentMethod


class PaymentIntentSerializer(serializers.ModelSerializer):
    """Serializer for PaymentIntent (read-only for frontend)"""

    amount_decimal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = PaymentIntent
        fields = [
            'id',
            'workspace_id',
            'amount',
            'amount_decimal',
            'currency',
            'purpose',
            'provider_name',
            'provider_intent_id',
            'status',
            'idempotency_key',
            'created_at',
            'updated_at',
            'expires_at',
            'completed_at',
            'failure_reason',
            'is_expired',
            'metadata'
        ]
        read_only_fields = fields


class MerchantPaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for MerchantPaymentMethod (list view)"""

    success_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = MerchantPaymentMethod
        fields = [
            'id',
            'workspace_id',
            'provider_name',
            'checkout_url',
            'enabled',
            'verified',
            'permissions',
            'last_used_at',
            'total_transactions',
            'successful_transactions',
            'success_rate',
            'created_at',
            'verified_at'
        ]
        read_only_fields = [
            'id',
            'verified',
            'last_used_at',
            'total_transactions',
            'successful_transactions',
            'success_rate',
            'created_at',
            'verified_at'
        ]


class AddPaymentMethodSerializer(serializers.Serializer):
    """
    Serializer for adding payment method to workspace

    For external redirect providers (Fapshi): Provide checkout_url
    For future API-integrated providers: Provide credentials
    """

    provider_name = serializers.CharField(max_length=50, required=True)
    checkout_url = serializers.URLField(max_length=500, required=False, allow_blank=True)

    def validate_provider_name(self, value):
        """Validate provider is registered"""
        from .services.registry import registry

        if not registry.is_registered(value):
            raise serializers.ValidationError(
                f"Provider '{value}' is not supported. "
                f"Available: {', '.join(registry.list_providers())}"
            )
        return value

    def validate(self, attrs):
        """Validate that checkout_url is provided for external redirect providers"""
        provider_name = attrs.get('provider_name')
        checkout_url = attrs.get('checkout_url')

        if provider_name == 'fapshi' and not checkout_url:
            raise serializers.ValidationError({
                'checkout_url': 'Fapshi checkout URL is required'
            })

        return attrs


class TogglePaymentMethodSerializer(serializers.Serializer):
    """Serializer for toggling payment method enabled status"""

    enabled = serializers.BooleanField(required=True)
