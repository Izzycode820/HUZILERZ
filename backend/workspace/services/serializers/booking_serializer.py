from rest_framework import serializers
from django.utils import timezone
from ..models import Booking, Service, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class BookingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_email = serializers.CharField(source='client.email', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.username', read_only=True)
    duration_minutes = serializers.IntegerField(source='service.duration_minutes', read_only=True)
    service_price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id',
            'scheduled_at',
            'status',
            'notes',
            'service',
            'service_name',
            'service_price',
            'duration_minutes',
            'client',
            'client_name',
            'client_email',
            'assigned_staff',
            'assigned_staff_name',
            'workspace',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_scheduled_at(self, value):
        # Cannot schedule in the past
        if value <= timezone.now():
            raise serializers.ValidationError("Booking cannot be scheduled in the past")
        
        # Cannot schedule more than 6 months in advance
        six_months_later = timezone.now() + timezone.timedelta(days=180)
        if value > six_months_later:
            raise serializers.ValidationError("Booking cannot be scheduled more than 6 months in advance")
        
        return value

    def validate(self, attrs):
        # Get workspace from context
        workspace = self.context.get('workspace')
        if not workspace:
            raise serializers.ValidationError("Workspace is required")
        
        # Ensure service belongs to the workspace
        service = attrs.get('service')
        if service and service.workspace != workspace:
            raise serializers.ValidationError("Service must belong to the same workspace")
        
        # Ensure client belongs to the workspace
        client = attrs.get('client')
        if client and client.workspace != workspace:
            raise serializers.ValidationError("Client must belong to the same workspace")
        
        # Check for booking conflicts if we have all required data
        scheduled_at = attrs.get('scheduled_at')
        assigned_staff = attrs.get('assigned_staff')
        
        if scheduled_at and service and assigned_staff:
            from ..services import BookingService
            booking_service = BookingService()
            
            # Calculate end time
            end_time = scheduled_at + timezone.timedelta(minutes=service.duration_minutes)
            
            # Check for conflicts (exclude current booking if editing)
            exclude_booking_id = self.instance.id if self.instance else None
            has_conflict = booking_service.has_booking_conflict(
                staff_member=assigned_staff,
                start_time=scheduled_at,
                end_time=end_time,
                exclude_booking_id=exclude_booking_id
            )
            
            if has_conflict:
                raise serializers.ValidationError(
                    "This time slot conflicts with another booking for the assigned staff member"
                )
        
        return attrs


class BookingListSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.username', read_only=True)
    duration_minutes = serializers.IntegerField(source='service.duration_minutes', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id',
            'scheduled_at',
            'status',
            'service_name',
            'client_name',
            'assigned_staff_name',
            'duration_minutes',
            'created_at',
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'scheduled_at',
            'notes',
            'service',
            'client',
            'assigned_staff',
        ]

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Booking cannot be scheduled in the past")
        return value

    def create(self, validated_data):
        workspace = self.context.get('workspace')
        validated_data['workspace'] = workspace
        return super().create(validated_data)