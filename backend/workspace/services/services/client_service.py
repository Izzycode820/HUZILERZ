# Client Management Service
from django.db import transaction
from django.core.exceptions import ValidationError
from django.apps import apps
import logging

logger = logging.getLogger('workspace.services.services')


class ClientService:
    """Service for managing clients/customers"""
    
    @staticmethod
    def create_client(workspace, user, **client_data):
        """Create a new client"""
        Client = apps.get_model('services', 'Client')
        
        # Check if client with email already exists
        if Client.objects.filter(workspace=workspace, email=client_data.get('email')).exists():
            raise ValidationError("Client with this email already exists in workspace")
        
        try:
            with transaction.atomic():
                client_data['workspace'] = workspace
                client = Client.objects.create(**client_data)
                
                logger.info(f"Client created: {client.name} in {workspace.name}")
                return client
                
        except Exception as e:
            logger.error(f"Failed to create client: {str(e)}")
            raise ValidationError(f"Failed to create client: {str(e)}")
    
    @staticmethod
    def update_client(client, user, **update_data):
        """Update client information"""
        try:
            with transaction.atomic():
                # Check email uniqueness if email is being updated
                if 'email' in update_data and update_data['email'] != client.email:
                    Client = apps.get_model('services', 'Client')
                    if Client.objects.filter(
                        workspace=client.workspace, 
                        email=update_data['email']
                    ).exclude(id=client.id).exists():
                        raise ValidationError("Client with this email already exists in workspace")
                
                for field, value in update_data.items():
                    if hasattr(client, field):
                        setattr(client, field, value)
                
                client.save()
                
                logger.info(f"Client updated: {client.name}")
                return client
                
        except Exception as e:
            logger.error(f"Failed to update client: {str(e)}")
            raise ValidationError(f"Failed to update client: {str(e)}")
    
    @staticmethod
    def delete_client(client, user):
        """Delete client (hard delete - be careful!)"""
        try:
            with transaction.atomic():
                client_name = client.name
                workspace_name = client.workspace.name
                
                # Check if client has active bookings
                active_bookings = client.bookings.filter(status__in=['pending', 'confirmed']).count()
                if active_bookings > 0:
                    raise ValidationError(
                        f"Cannot delete client with {active_bookings} active bookings"
                    )
                
                client.delete()
                
                logger.info(f"Client deleted: {client_name} from {workspace_name}")
                
        except Exception as e:
            logger.error(f"Failed to delete client: {str(e)}")
            raise ValidationError(f"Failed to delete client: {str(e)}")
    
    @staticmethod
    def get_workspace_clients(workspace):
        """Get all clients for workspace"""
        Client = apps.get_model('services', 'Client')
        
        return Client.objects.filter(workspace=workspace).order_by('name')
    
    @staticmethod
    def search_clients(workspace, query):
        """Search clients by name or email"""
        from django.db.models import Q
        Client = apps.get_model('services', 'Client')
        
        return Client.objects.filter(
            workspace=workspace
        ).filter(
            Q(name__icontains=query) | Q(email__icontains=query)
        ).order_by('name')
    
    @staticmethod
    def get_client_statistics(client):
        """Get statistics for a client"""
        from django.db.models import Sum, Count, Q
        
        # Get booking statistics
        total_bookings = client.bookings.count()
        completed_bookings = client.bookings.filter(status='confirmed').count()
        cancelled_bookings = client.bookings.filter(status='cancelled').count()
        
        # Get financial statistics
        total_invoiced = client.invoices.aggregate(Sum('amount'))['amount__sum'] or 0
        total_paid = client.invoices.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
        total_outstanding = client.invoices.filter(status='unpaid').aggregate(Sum('amount'))['amount__sum'] or 0
        
        return {
            'total_bookings': total_bookings,
            'completed_bookings': completed_bookings,
            'cancelled_bookings': cancelled_bookings,
            'total_invoiced': float(total_invoiced),
            'total_paid': float(total_paid),
            'total_outstanding': float(total_outstanding),
        }
    
    @staticmethod
    def get_or_create_client_by_email(workspace, email, name=None):
        """Get existing client or create new one by email"""
        Client = apps.get_model('services', 'Client')
        
        try:
            client = Client.objects.get(workspace=workspace, email=email)
            return client, False
        except Client.DoesNotExist:
            if not name:
                raise ValidationError("Name is required for new client")
            
            return ClientService.create_client(
                workspace=workspace,
                user=None,  # System creation
                name=name,
                email=email
            ), True