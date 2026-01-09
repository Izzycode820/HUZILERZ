from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import Booking
from ..serializers import BookingSerializer, BookingListSerializer, BookingCreateSerializer
from ..services import BookingService
from workspace.core.models import Workspace
from workspace.core.permissions import IsWorkspaceMember


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    
    def get_queryset(self):
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)
        queryset = Booking.objects.filter(workspace=workspace).order_by('-scheduled_at')
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Date range filter
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(scheduled_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_at__date__lte=end_date)
        
        # Staff filter
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            queryset = queryset.filter(assigned_staff_id=staff_id)
        
        # Service filter
        service_id = self.request.query_params.get('service')
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        
        # Client filter
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'list':
            return BookingListSerializer
        return BookingSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        workspace_id = self.kwargs.get('workspace_id')
        if workspace_id:
            context['workspace'] = get_object_or_404(Workspace, id=workspace_id)
        return context
    
    def perform_create(self, serializer):
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        booking_service = BookingService()
        booking = booking_service.create_booking(
            workspace=workspace,
            service=serializer.validated_data['service'],
            client=serializer.validated_data['client'],
            scheduled_at=serializer.validated_data['scheduled_at'],
            assigned_staff=serializer.validated_data.get('assigned_staff'),
            notes=serializer.validated_data.get('notes', ''),
        )
        serializer.instance = booking
    
    def perform_update(self, serializer):
        booking_service = BookingService()
        booking = booking_service.update_booking(
            booking_id=serializer.instance.id,
            **serializer.validated_data
        )
        serializer.instance = booking
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None, workspace_id=None):
        """Confirm a booking"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response(
                {'error': 'Only pending bookings can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking_service = BookingService()
        booking = booking_service.confirm_booking(booking.id)
        
        return Response({
            'message': 'Booking confirmed successfully',
            'booking': BookingSerializer(booking, context=self.get_serializer_context()).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None, workspace_id=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        if booking.status == 'cancelled':
            return Response(
                {'error': 'Booking is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking_service = BookingService()
        booking = booking_service.cancel_booking(booking.id)
        
        return Response({
            'message': 'Booking cancelled successfully',
            'booking': BookingSerializer(booking, context=self.get_serializer_context()).data
        })
    
    @action(detail=False, methods=['get'])
    def calendar(self, request, workspace_id=None):
        """Get bookings in calendar format"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        # Get date range (default to current month)
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if not start_date or not end_date:
            now = timezone.now()
            start_date = now.replace(day=1).date()
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        bookings = Booking.objects.filter(
            workspace=workspace,
            scheduled_at__date__gte=start_date,
            scheduled_at__date__lte=end_date
        ).select_related('service', 'client', 'assigned_staff').order_by('scheduled_at')
        
        # Format for calendar
        calendar_events = []
        for booking in bookings:
            event = {
                'id': booking.id,
                'title': f"{booking.client.name} - {booking.service.name}",
                'start': booking.scheduled_at.isoformat(),
                'end': (booking.scheduled_at + timedelta(minutes=booking.service.duration_minutes)).isoformat(),
                'status': booking.status,
                'client': booking.client.name,
                'service': booking.service.name,
                'staff': booking.assigned_staff.username if booking.assigned_staff else None,
                'notes': booking.notes,
            }
            
            # Color coding based on status
            if booking.status == 'confirmed':
                event['color'] = '#28a745'  # Green
            elif booking.status == 'pending':
                event['color'] = '#ffc107'  # Yellow
            elif booking.status == 'cancelled':
                event['color'] = '#dc3545'  # Red
            
            calendar_events.append(event)
        
        return Response({'events': calendar_events})
    
    @action(detail=False, methods=['get'])
    def availability(self, request, workspace_id=None):
        """Check availability for a given date and staff member"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        date_str = request.query_params.get('date')
        staff_id = request.query_params.get('staff_id')
        
        if not date_str:
            return Response(
                {'error': 'Date parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking_service = BookingService()
        
        if staff_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                staff_member = User.objects.get(id=staff_id)
                availability = booking_service.get_staff_availability(staff_member, date)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Staff member not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            availability = booking_service.get_general_availability(workspace, date)
        
        return Response({'availability': availability})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request, workspace_id=None):
        """Get booking statistics for the workspace"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        bookings = Booking.objects.filter(workspace=workspace)
        
        # Get today's bookings
        today = timezone.now().date()
        today_bookings = bookings.filter(scheduled_at__date=today)
        
        # Get this week's bookings
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_bookings = bookings.filter(
            scheduled_at__date__gte=week_start,
            scheduled_at__date__lte=week_end
        )
        
        # Get this month's bookings
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        month_bookings = bookings.filter(
            scheduled_at__date__gte=month_start,
            scheduled_at__date__lte=month_end
        )
        
        # Calculate revenue from confirmed bookings
        confirmed_bookings = bookings.filter(status='confirmed')
        total_revenue = sum(
            booking.service.price for booking in confirmed_bookings 
            if booking.service
        )
        
        month_revenue = sum(
            booking.service.price for booking in month_bookings.filter(status='confirmed')
            if booking.service
        )
        
        statistics = {
            'total_bookings': bookings.count(),
            'pending_bookings': bookings.filter(status='pending').count(),
            'confirmed_bookings': confirmed_bookings.count(),
            'cancelled_bookings': bookings.filter(status='cancelled').count(),
            'today_bookings': today_bookings.count(),
            'week_bookings': week_bookings.count(),
            'month_bookings': month_bookings.count(),
            'total_revenue': total_revenue,
            'month_revenue': month_revenue,
        }
        
        return Response(statistics)