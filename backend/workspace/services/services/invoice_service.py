# Invoice Management Service
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.apps import apps
import logging

logger = logging.getLogger('workspace.services.services')


class InvoiceService:
    """Service for managing invoices"""
    
    @staticmethod
    def create_invoice(client, amount, booking=None, notes=''):
        """Create a new invoice"""
        Invoice = apps.get_model('services', 'Invoice')
        
        try:
            with transaction.atomic():
                invoice = Invoice.objects.create(
                    client=client,
                    booking=booking,
                    amount=amount,
                    status='unpaid'
                )
                
                logger.info(f"Invoice created: {invoice.invoice_number} for {client.name}")
                return invoice
                
        except Exception as e:
            logger.error(f"Failed to create invoice: {str(e)}")
            raise ValidationError(f"Failed to create invoice: {str(e)}")
    
    @staticmethod
    def create_invoice_from_booking(booking, user):
        """Create invoice automatically from booking"""
        if booking.invoices.exists():
            raise ValidationError("Booking already has an invoice")
        
        return InvoiceService.create_invoice(
            client=booking.client,
            amount=booking.service.price,
            booking=booking
        )
    
    @staticmethod
    def update_invoice_status(invoice, status, user):
        """Update invoice status"""
        if status not in ['unpaid', 'paid', 'refunded']:
            raise ValidationError("Invalid invoice status")
        
        try:
            with transaction.atomic():
                invoice.status = status
                invoice.save()
                
                logger.info(f"Invoice {invoice.invoice_number} status changed to {status}")
                return invoice
                
        except Exception as e:
            logger.error(f"Failed to update invoice status: {str(e)}")
            raise ValidationError(f"Failed to update invoice status: {str(e)}")
    
    @staticmethod
    def mark_invoice_paid(invoice, user):
        """Mark invoice as paid"""
        return InvoiceService.update_invoice_status(invoice, 'paid', user)
    
    @staticmethod
    def mark_invoice_refunded(invoice, user):
        """Mark invoice as refunded"""
        return InvoiceService.update_invoice_status(invoice, 'refunded', user)
    
    @staticmethod
    def get_workspace_invoices(workspace, status=None, date_range=None):
        """Get invoices for workspace"""
        Invoice = apps.get_model('services', 'Invoice')
        
        queryset = Invoice.objects.filter(client__workspace=workspace)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_range:
            start_date, end_date = date_range
            queryset = queryset.filter(
                issued_at__gte=start_date,
                issued_at__lte=end_date
            )
        
        return queryset.select_related('client', 'booking').order_by('-issued_at')
    
    @staticmethod
    def get_client_invoices(client, status=None):
        """Get invoices for specific client"""
        Invoice = apps.get_model('services', 'Invoice')
        
        queryset = Invoice.objects.filter(client=client)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-issued_at')
    
    @staticmethod
    def get_workspace_revenue_stats(workspace, date_range=None):
        """Get revenue statistics for workspace"""
        from django.db.models import Sum, Count, Q
        Invoice = apps.get_model('services', 'Invoice')
        
        queryset = Invoice.objects.filter(client__workspace=workspace)
        
        if date_range:
            start_date, end_date = date_range
            queryset = queryset.filter(
                issued_at__gte=start_date,
                issued_at__lte=end_date
            )
        
        stats = queryset.aggregate(
            total_invoiced=Sum('amount'),
            total_paid=Sum('amount', filter=Q(status='paid')),
            total_outstanding=Sum('amount', filter=Q(status='unpaid')),
            total_refunded=Sum('amount', filter=Q(status='refunded')),
            invoice_count=Count('id'),
            paid_count=Count('id', filter=Q(status='paid')),
            outstanding_count=Count('id', filter=Q(status='unpaid')),
        )
        
        # Convert Decimal to float for JSON serialization
        for key, value in stats.items():
            if value is None:
                stats[key] = 0
            elif hasattr(value, '__float__'):
                stats[key] = float(value)
        
        return stats
    
    @staticmethod
    def get_overdue_invoices(workspace, days_overdue=30):
        """Get overdue invoices"""
        from datetime import timedelta
        Invoice = apps.get_model('services', 'Invoice')
        
        cutoff_date = timezone.now() - timedelta(days=days_overdue)
        
        return Invoice.objects.filter(
            client__workspace=workspace,
            status='unpaid',
            issued_at__lte=cutoff_date
        ).select_related('client').order_by('issued_at')
    
    @staticmethod
    def delete_invoice(invoice, user):
        """Delete invoice (be careful!)"""
        try:
            with transaction.atomic():
                if invoice.status == 'paid':
                    raise ValidationError("Cannot delete paid invoice")
                
                invoice_number = invoice.invoice_number
                client_name = invoice.client.name
                invoice.delete()
                
                logger.info(f"Invoice deleted: {invoice_number} for {client_name}")
                
        except Exception as e:
            logger.error(f"Failed to delete invoice: {str(e)}")
            raise ValidationError(f"Failed to delete invoice: {str(e)}")