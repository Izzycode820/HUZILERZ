from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta

from ..models import Invoice
from ..serializers import InvoiceSerializer, InvoiceListSerializer, InvoiceCreateSerializer
from ..services import InvoiceService
from workspace.core.models import Workspace
from workspace.core.permissions import IsWorkspaceMember


class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    
    def get_queryset(self):
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)
        queryset = Invoice.objects.filter(workspace=workspace).order_by('-created_at')
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Date range filter
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(issued_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issued_at__date__lte=end_date)
        
        # Client filter (through booking)
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(booking__client_id=client_id)
        
        # Overdue filter
        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            queryset = queryset.filter(
                status='pending',
                due_date__lt=timezone.now().date()
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        elif self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        workspace_id = self.kwargs.get('workspace_id')
        if workspace_id:
            context['workspace'] = get_object_or_404(Workspace, id=workspace_id)
        return context
    
    def perform_create(self, serializer):
        workspace_id = self.kwargs.get('workspace_id')
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        invoice_service = InvoiceService()
        invoice = invoice_service.create_invoice(
            workspace=workspace,
            booking=serializer.validated_data['booking'],
            amount=serializer.validated_data['amount'],
            due_date=serializer.validated_data['due_date'],
            notes=serializer.validated_data.get('notes', ''),
        )
        serializer.instance = invoice
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None, workspace_id=None):
        """Mark invoice as paid"""
        invoice = self.get_object()
        
        if invoice.status == 'paid':
            return Response(
                {'error': 'Invoice is already marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice_service = InvoiceService()
        invoice = invoice_service.mark_paid(invoice.id)
        
        return Response({
            'message': 'Invoice marked as paid successfully',
            'invoice': InvoiceSerializer(invoice, context=self.get_serializer_context()).data
        })
    
    @action(detail=True, methods=['post'])
    def mark_pending(self, request, pk=None, workspace_id=None):
        """Mark invoice as pending"""
        invoice = self.get_object()
        
        if invoice.status == 'pending':
            return Response(
                {'error': 'Invoice is already pending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.status = 'pending'
        invoice.paid_at = None
        invoice.save()
        
        return Response({
            'message': 'Invoice marked as pending successfully',
            'invoice': InvoiceSerializer(invoice, context=self.get_serializer_context()).data
        })
    
    @action(detail=False, methods=['get'])
    def overdue(self, request, workspace_id=None):
        """Get all overdue invoices"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        invoice_service = InvoiceService()
        overdue_invoices = invoice_service.get_overdue_invoices(workspace)
        
        serializer = InvoiceListSerializer(overdue_invoices, many=True)
        return Response({
            'count': overdue_invoices.count(),
            'invoices': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request, workspace_id=None):
        """Get invoice statistics for the workspace"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        invoice_service = InvoiceService()
        statistics = invoice_service.get_revenue_statistics(workspace)
        
        # Add additional statistics
        invoices = Invoice.objects.filter(workspace=workspace)
        
        # Get overdue invoices
        overdue_invoices = invoices.filter(
            status='pending',
            due_date__lt=timezone.now().date()
        )
        
        # Get this month's invoices
        today = timezone.now().date()
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        month_invoices = invoices.filter(
            issued_at__date__gte=month_start,
            issued_at__date__lte=month_end
        )
        
        month_paid = month_invoices.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        month_pending = month_invoices.filter(status='pending').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        statistics.update({
            'total_invoices': invoices.count(),
            'paid_invoices': invoices.filter(status='paid').count(),
            'pending_invoices': invoices.filter(status='pending').count(),
            'overdue_invoices': overdue_invoices.count(),
            'overdue_amount': overdue_invoices.aggregate(total=Sum('amount'))['total'] or 0,
            'month_invoices': month_invoices.count(),
            'month_paid': month_paid,
            'month_pending': month_pending,
        })
        
        return Response(statistics)
    
    @action(detail=False, methods=['get'])
    def recent(self, request, workspace_id=None):
        """Get recent invoices"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        limit = int(request.query_params.get('limit', 10))
        recent_invoices = Invoice.objects.filter(
            workspace=workspace
        ).order_by('-created_at')[:limit]
        
        serializer = InvoiceListSerializer(recent_invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None, workspace_id=None):
        """Generate and download invoice PDF"""
        invoice = self.get_object()
        
        # This would typically generate a PDF
        # For now, return invoice data for frontend to handle PDF generation
        serializer = InvoiceSerializer(invoice, context=self.get_serializer_context())
        
        return Response({
            'message': 'Invoice data prepared for PDF generation',
            'invoice': serializer.data,
            'download_url': f'/api/workspaces/{workspace_id}/services/invoices/{pk}/pdf/'
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request, workspace_id=None):
        """Create multiple invoices from bookings"""
        workspace = get_object_or_404(Workspace, id=workspace_id)
        booking_ids = request.data.get('booking_ids', [])
        
        if not booking_ids:
            return Response(
                {'error': 'No booking IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from ..models import Booking
        bookings = Booking.objects.filter(
            id__in=booking_ids,
            workspace=workspace,
            status='confirmed'
        )
        
        if not bookings.exists():
            return Response(
                {'error': 'No valid confirmed bookings found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice_service = InvoiceService()
        created_invoices = []
        
        for booking in bookings:
            # Check if invoice already exists for this booking
            existing_invoice = Invoice.objects.filter(booking=booking).first()
            if not existing_invoice:
                invoice = invoice_service.create_invoice(
                    workspace=workspace,
                    booking=booking,
                    amount=booking.service.price,
                    due_date=timezone.now().date() + timedelta(days=30),  # Default 30 days
                    notes='Auto-generated invoice'
                )
                created_invoices.append(invoice)
        
        serializer = InvoiceListSerializer(created_invoices, many=True)
        return Response({
            'message': f'Created {len(created_invoices)} invoices successfully',
            'invoices': serializer.data
        })