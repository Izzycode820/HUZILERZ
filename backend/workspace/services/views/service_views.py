from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone

from ..models import Service
from ..serializers import ServiceSerializer, ServiceListSerializer
from ..services import ServiceService
from workspace.core.models import Workspace
from workspace.core.permissions import IsWorkspaceMember


class ServiceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    
    def get_queryset(self):
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)
        return Service.objects.filter(workspace=workspace).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceListSerializer
        return ServiceSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        workspace_id = self.kwargs.get('workspace_id')
        if workspace_id:
            context['workspace'] = get_object_or_404(Workspace, id=workspace_id)
        return context
    
    def perform_create(self, serializer):
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        service_service = ServiceService()
        service = service_service.create_service(
            workspace=workspace,
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            price=serializer.validated_data['price'],
            duration_minutes=serializer.validated_data['duration_minutes'],
            category=serializer.validated_data.get('category', ''),
        )
        serializer.instance = service
    
    def perform_update(self, serializer):
        service_service = ServiceService()
        service = service_service.update_service(
            service_id=serializer.instance.id,
            **serializer.validated_data
        )
        serializer.instance = service
    
    @action(detail=False, methods=['get'])
    def categories(self, request, workspace_id=None):
        """Get all unique categories for services in this workspace"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        categories = Service.objects.filter(
            workspace=workspace,
            is_active=True
        ).exclude(
            category__isnull=True
        ).exclude(
            category__exact=''
        ).values_list('category', flat=True).distinct().order_by('category')
        
        return Response({'categories': list(categories)})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request, workspace_id=None):
        """Get service statistics for the workspace"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        services = Service.objects.filter(workspace=workspace)
        active_services = services.filter(is_active=True)
        
        # Get booking statistics
        from ..models import Booking
        bookings = Booking.objects.filter(service__workspace=workspace)
        confirmed_bookings = bookings.filter(status='confirmed')
        
        # Calculate revenue from confirmed bookings
        total_revenue = sum(
            booking.service.price for booking in confirmed_bookings 
            if booking.service
        )
        
        # Get most popular services
        popular_services = active_services.annotate(
            booking_count=Count('bookings', filter=Q(bookings__status='confirmed'))
        ).filter(booking_count__gt=0).order_by('-booking_count')[:5]
        
        popular_services_data = [
            {
                'id': service.id,
                'name': service.name,
                'booking_count': service.booking_count,
                'price': service.price,
                'revenue': service.booking_count * service.price
            }
            for service in popular_services
        ]
        
        # Calculate average service price
        avg_price = active_services.aggregate(avg_price=Avg('price'))['avg_price'] or 0
        
        statistics = {
            'total_services': services.count(),
            'active_services': active_services.count(),
            'total_bookings': bookings.count(),
            'confirmed_bookings': confirmed_bookings.count(),
            'total_revenue': total_revenue,
            'average_service_price': round(avg_price, 2),
            'popular_services': popular_services_data,
        }
        
        return Response(statistics)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None, workspace_id=None):
        """Toggle service active status"""
        service = self.get_object()
        service.is_active = not service.is_active
        service.save()
        
        return Response({
            'message': f"Service {'activated' if service.is_active else 'deactivated'} successfully",
            'is_active': service.is_active
        })
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None, workspace_id=None):
        """Get all bookings for this service"""
        service = self.get_object()
        bookings = service.bookings.all().order_by('-scheduled_at')
        
        # Apply status filter if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        # Apply date range filter if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            bookings = bookings.filter(scheduled_at__date__gte=start_date)
        if end_date:
            bookings = bookings.filter(scheduled_at__date__lte=end_date)
        
        from ..serializers import BookingListSerializer
        serializer = BookingListSerializer(bookings, many=True)
        
        return Response(serializer.data)