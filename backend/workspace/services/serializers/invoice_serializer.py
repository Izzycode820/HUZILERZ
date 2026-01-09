from rest_framework import serializers
from django.utils import timezone
from ..models import Invoice, Booking


class InvoiceSerializer(serializers.ModelSerializer):
    booking_details = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='booking.client.name', read_only=True)
    client_email = serializers.CharField(source='booking.client.email', read_only=True)
    service_name = serializers.CharField(source='booking.service.name', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'amount',
            'status',
            'issued_at',
            'due_date',
            'paid_at',
            'notes',
            'booking',
            'booking_details',
            'client_name',
            'client_email',
            'service_name',
            'is_overdue',
            'days_overdue',
            'workspace',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'invoice_number', 'is_overdue', 'days_overdue', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

    def validate_due_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value

    def validate(self, attrs):
        # Ensure booking belongs to the workspace
        workspace = self.context.get('workspace')
        booking = attrs.get('booking')
        
        if booking and booking.workspace != workspace:
            raise serializers.ValidationError("Booking must belong to the same workspace")
        
        # If status is being set to paid, ensure paid_at is set
        status = attrs.get('status')
        paid_at = attrs.get('paid_at')
        
        if status == 'paid' and not paid_at:
            attrs['paid_at'] = timezone.now()
        elif status != 'paid' and paid_at:
            attrs['paid_at'] = None
        
        return attrs

    def get_booking_details(self, obj):
        if obj.booking:
            return {
                'id': obj.booking.id,
                'scheduled_at': obj.booking.scheduled_at,
                'status': obj.booking.status,
                'service_name': obj.booking.service.name if obj.booking.service else None,
                'client_name': obj.booking.client.name if obj.booking.client else None,
            }
        return None

    def get_is_overdue(self, obj):
        if obj.status == 'paid':
            return False
        return obj.due_date < timezone.now().date()

    def get_days_overdue(self, obj):
        if obj.status == 'paid':
            return 0
        if obj.due_date < timezone.now().date():
            return (timezone.now().date() - obj.due_date).days
        return 0


class InvoiceListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='booking.client.name', read_only=True)
    service_name = serializers.CharField(source='booking.service.name', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'amount',
            'status',
            'issued_at',
            'due_date',
            'client_name',
            'service_name',
            'is_overdue',
            'created_at',
        ]

    def get_is_overdue(self, obj):
        if obj.status == 'paid':
            return False
        return obj.due_date < timezone.now().date()


class InvoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'amount',
            'due_date',
            'notes',
            'booking',
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

    def validate_due_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value

    def create(self, validated_data):
        workspace = self.context.get('workspace')
        validated_data['workspace'] = workspace
        validated_data['status'] = 'pending'
        validated_data['issued_at'] = timezone.now()
        
        # Generate invoice number
        from ..services import InvoiceService
        invoice_service = InvoiceService()
        validated_data['invoice_number'] = invoice_service._generate_invoice_number(workspace)
        
        return super().create(validated_data)