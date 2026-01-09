from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from django.utils import timezone

from ..models import Client
from ..serializers import ClientSerializer, ClientListSerializer
from ..services import ClientService
from workspace.core.models import Workspace
from workspace.core.permissions import IsWorkspaceMember


class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    
    def get_queryset(self):
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)
        queryset = Client.objects.filter(workspace=workspace).order_by('-created_at')
        
        # Apply search filter if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ClientListSerializer
        return ClientSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        workspace_id = self.kwargs.get('workspace_id')
        if workspace_id:
            context['workspace'] = get_object_or_404(Workspace, id=workspace_id)
        return context
    
    def perform_create(self, serializer):
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        client_service = ClientService()
        client = client_service.create_client(
            workspace=workspace,
            name=serializer.validated_data['name'],
            email=serializer.validated_data.get('email', ''),
            phone=serializer.validated_data.get('phone', ''),
            notes=serializer.validated_data.get('notes', ''),
        )
        serializer.instance = client
    
    def perform_update(self, serializer):
        client_service = ClientService()
        client = client_service.update_client(
            client_id=serializer.instance.id,
            **serializer.validated_data
        )
        serializer.instance = client
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None, workspace_id=None):
        """Get all bookings for this client"""
        client = self.get_object()
        bookings = client.bookings.all().order_by('-scheduled_at')
        
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
    
    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None, workspace_id=None):
        """Get all invoices for this client"""
        client = self.get_object()
        
        # Get invoices through bookings
        from ..models import Invoice
        invoices = Invoice.objects.filter(
            booking__client=client
        ).order_by('-created_at')
        
        # Apply status filter if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            invoices = invoices.filter(status=status_filter)
        
        from ..serializers import InvoiceListSerializer
        serializer = InvoiceListSerializer(invoices, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None, workspace_id=None):
        """Get statistics for this client"""
        client = self.get_object()
        
        bookings = client.bookings.all()
        confirmed_bookings = bookings.filter(status='confirmed')
        
        # Calculate total spent from confirmed bookings
        total_spent = sum(
            booking.service.price for booking in confirmed_bookings 
            if booking.service
        )
        
        # Get favorite services (most booked)
        from django.db.models import Count
        favorite_services = client.bookings.filter(
            status='confirmed'
        ).values(
            'service__id', 'service__name'
        ).annotate(
            booking_count=Count('id')
        ).order_by('-booking_count')[:3]
        
        # Get upcoming bookings
        upcoming_bookings = bookings.filter(
            scheduled_at__gt=timezone.now(),
            status__in=['pending', 'confirmed']
        ).count()
        
        # Get overdue invoices
        from ..models import Invoice
        overdue_invoices = Invoice.objects.filter(
            booking__client=client,
            status='pending',
            due_date__lt=timezone.now().date()
        ).count()
        
        statistics = {
            'total_bookings': bookings.count(),
            'confirmed_bookings': confirmed_bookings.count(),
            'cancelled_bookings': bookings.filter(status='cancelled').count(),
            'upcoming_bookings': upcoming_bookings,
            'total_spent': total_spent,
            'favorite_services': list(favorite_services),
            'overdue_invoices': overdue_invoices,
            'first_booking': bookings.order_by('scheduled_at').first().scheduled_at if bookings.exists() else None,
            'last_booking': bookings.order_by('-scheduled_at').first().scheduled_at if bookings.exists() else None,
        }
        
        return Response(statistics)
    
    @action(detail=False, methods=['get'])
    def search(self, request, workspace_id=None):
        """Search clients by name, email, or phone"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({'results': []})
        
        clients = Client.objects.filter(
            workspace=workspace
        ).filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )[:10]  # Limit to 10 results
        
        serializer = ClientListSerializer(clients, many=True)
        return Response({'results': serializer.data})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request, workspace_id=None):
        """Get client statistics for the workspace"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        clients = Client.objects.filter(workspace=workspace)
        
        # Get clients with bookings
        clients_with_bookings = clients.filter(bookings__isnull=False).distinct()
        
        # Get new clients (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        new_clients = clients.filter(created_at__gte=thirty_days_ago)
        
        # Get most active clients
        active_clients = clients.annotate(
            booking_count=Count('bookings', filter=Q(bookings__status='confirmed'))
        ).filter(booking_count__gt=0).order_by('-booking_count')[:5]
        
        active_clients_data = [
            {
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'booking_count': client.booking_count,
                'total_spent': sum(
                    booking.service.price for booking in client.bookings.filter(status='confirmed')
                    if booking.service
                )
            }
            for client in active_clients
        ]
        
        statistics = {
            'total_clients': clients.count(),
            'clients_with_bookings': clients_with_bookings.count(),
            'new_clients_30_days': new_clients.count(),
            'active_clients': active_clients_data,
        }
        
        return Response(statistics)