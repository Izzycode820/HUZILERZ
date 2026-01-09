# Service Management Service
from django.db import transaction
from django.core.exceptions import ValidationError
from django.apps import apps
import logging

logger = logging.getLogger('workspace.services.services')


class ServiceService:
    """Service for managing services offered"""
    
    @staticmethod
    def create_service(workspace, user, **service_data):
        """Create a new service"""
        Service = apps.get_model('services', 'Service')
        
        try:
            with transaction.atomic():
                service_data['workspace'] = workspace
                service = Service.objects.create(**service_data)
                
                logger.info(f"Service created: {service.title} in {workspace.name}")
                return service
                
        except Exception as e:
            logger.error(f"Failed to create service: {str(e)}")
            raise ValidationError(f"Failed to create service: {str(e)}")
    
    @staticmethod
    def update_service(service, user, **update_data):
        """Update service"""
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(service, field):
                        setattr(service, field, value)
                
                service.save()
                
                logger.info(f"Service updated: {service.title}")
                return service
                
        except Exception as e:
            logger.error(f"Failed to update service: {str(e)}")
            raise ValidationError(f"Failed to update service: {str(e)}")
    
    @staticmethod
    def delete_service(service, user):
        """Delete service (soft delete by deactivating)"""
        try:
            with transaction.atomic():
                service.is_active = False
                service.save()
                
                logger.info(f"Service deactivated: {service.title}")
                
        except Exception as e:
            logger.error(f"Failed to deactivate service: {str(e)}")
            raise ValidationError(f"Failed to deactivate service: {str(e)}")
    
    @staticmethod
    def get_workspace_services(workspace, active_only=True):
        """Get services for workspace"""
        Service = apps.get_model('services', 'Service')
        
        queryset = Service.objects.filter(workspace=workspace)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('title')
    
    @staticmethod
    def get_available_services(workspace, date=None, staff=None):
        """Get services available for booking on specific date/time"""
        services = ServiceService.get_workspace_services(workspace, active_only=True)
        
        # Future enhancement: Filter by staff availability, date constraints, etc.
        # For now, return all active services
        
        return services