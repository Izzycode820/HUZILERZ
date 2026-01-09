from rest_framework import serializers
from ..models import Client


class ClientSerializer(serializers.ModelSerializer):
    bookings_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'notes',
            'workspace',
            'bookings_count',
            'total_spent',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        if not value:
            return value
        
        # Check for duplicate emails within the same workspace
        workspace = self.context.get('workspace')
        if workspace:
            existing_client = Client.objects.filter(
                email=value,
                workspace=workspace
            ).exclude(pk=self.instance.pk if self.instance else None).first()
            
            if existing_client:
                raise serializers.ValidationError(
                    "A client with this email already exists in this workspace"
                )
        
        return value.lower().strip()

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Client name must be at least 2 characters")
        return value.strip()

    def validate_phone(self, value):
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 characters")
        return value.strip() if value else value

    def get_bookings_count(self, obj):
        return obj.bookings.count()

    def get_total_spent(self, obj):
        from decimal import Decimal
        total = Decimal('0.00')
        for booking in obj.bookings.filter(status='confirmed'):
            if booking.service:
                total += booking.service.price
        return total


class ClientListSerializer(serializers.ModelSerializer):
    bookings_count = serializers.SerializerMethodField()
    last_booking = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'bookings_count',
            'last_booking',
            'created_at',
        ]

    def get_bookings_count(self, obj):
        return obj.bookings.count()

    def get_last_booking(self, obj):
        last_booking = obj.bookings.order_by('-scheduled_at').first()
        if last_booking:
            return {
                'id': last_booking.id,
                'scheduled_at': last_booking.scheduled_at,
                'service_name': last_booking.service.name if last_booking.service else None,
                'status': last_booking.status
            }
        return None