from rest_framework import serializers
from ..models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'price',
            'duration_minutes',
            'category',
            'is_active',
            'workspace',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

    def validate_duration_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than 0 minutes")
        if value > 1440:  # 24 hours
            raise serializers.ValidationError("Duration cannot exceed 24 hours")
        return value

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Service name must be at least 2 characters")
        return value.strip()


class ServiceListSerializer(serializers.ModelSerializer):
    bookings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'price',
            'duration_minutes',
            'category',
            'is_active',
            'bookings_count',
            'created_at',
        ]

    def get_bookings_count(self, obj):
        return obj.bookings.filter(status__in=['pending', 'confirmed']).count()