"""
Services Workspace Data Export Service
Implements workspace data export for service-based businesses
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
from typing import Dict, Any, Optional, List
from django.db import transaction, models
from django.core.exceptions import PermissionDenied
from django.apps import apps
from workspace.core.services.base_data_export_service import BaseWorkspaceDataExporter
from ..models import Booking
import logging

logger = logging.getLogger('workspace.services.data_export')


class ServicesDataExporter(BaseWorkspaceDataExporter):
    """
    Services-specific implementation of workspace data exporter
    Handles appointment booking and service management data
    """

    # Fields that trigger site sync when changed
    SYNC_TRIGGER_FIELDS = [
        'name', 'description', 'price', 'duration_minutes',
        'is_active', 'availability', 'booking_enabled'
    ]

    # Admin-only fields (never exposed to public booking)
    ADMIN_ONLY_FIELDS = [
        'cost_per_hour', 'profit_margin', 'internal_notes',
        'staff_requirements', 'booking_analytics'
    ]

    def export_data(self, workspace_id: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export complete services data with optional filtering

        Args:
            workspace_id: UUID of the services workspace
            filters: Optional filters for data export

        Returns:
            Dict containing complete services data
        """
        try:
            with transaction.atomic():
                # Base filters
                base_filters = {'workspace_id': workspace_id, 'is_active': True}
                if filters:
                    base_filters.update(filters)

                # Export services
                services = self._export_services(base_filters)

                # Export bookings
                bookings = self._export_bookings(workspace_id)

                # Export clients
                clients = self._export_clients(workspace_id)

                # Export availability schedules
                availability = self._export_availability(workspace_id)

                # Export services settings
                services_settings = self._export_services_settings(workspace_id)

                return {
                    'services': services,
                    'bookings': bookings,
                    'clients': clients,
                    'availability': availability,
                    'services_settings': services_settings,
                    'export_metadata': {
                        'workspace_id': workspace_id,
                        'export_type': 'full_data',
                        'services_count': len(services),
                        'bookings_count': len(bookings),
                        'clients_count': len(clients)
                    }
                }

        except Exception as e:
            logger.error(f"Failed to export services data for workspace {workspace_id}: {str(e)}")
            raise

    def get_storefront_data(self, workspace_id: str) -> Dict[str, Any]:
        """
        Export public booking data only
        Excludes sensitive business information

        Args:
            workspace_id: UUID of the services workspace

        Returns:
            Dict containing public booking information
        """
        try:
            # Only active, bookable services
            Service = apps.get_model('services', 'Service')
            services = Service.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                booking_enabled=True
            ).values(
                'id', 'name', 'description', 'duration_minutes',
                'price', 'category', 'featured_image', 'tags'
                # Excludes: cost_per_hour, profit_margin, internal_notes, etc.
            )

            # Public business information
            business_info = self._get_public_business_info(workspace_id)

            # Available time slots (next 30 days)
            available_slots = self._get_available_time_slots(workspace_id)

            # Service categories
            categories = self._get_public_service_categories(workspace_id)

            return {
                'services': list(services),
                'business_info': business_info,
                'available_slots': available_slots,
                'categories': categories,
                'storefront_metadata': {
                    'total_services': len(services),
                    'categories_count': len(categories),
                    'data_type': 'public_booking'
                }
            }

        except Exception as e:
            logger.error(f"Failed to export services storefront data for workspace {workspace_id}: {str(e)}")
            raise

    def get_admin_data(self, workspace_id: str, user) -> Dict[str, Any]:
        """
        Export full services admin data
        Includes booking analytics, client management, and business metrics

        Args:
            workspace_id: UUID of the services workspace
            user: User requesting the data

        Returns:
            Dict containing complete admin data
        """
        try:
            # Validate admin permissions
            if not self.validate_export_permissions(workspace_id, user, 'admin'):
                raise PermissionDenied("Insufficient permissions for services admin data export")

            # All services with business metrics
            Service = apps.get_model('services', 'Service')
            services = Service.objects.filter(
                workspace_id=workspace_id
            ).values(
                'id', 'name', 'description', 'price', 'cost_per_hour',
                'duration_minutes', 'category', 'is_active', 'booking_enabled',
                'created_at', 'updated_at'
            )

            # Booking analytics
            booking_analytics = self._get_booking_analytics(workspace_id)

            # Client analytics
            client_analytics = self._get_client_analytics(workspace_id)

            # Revenue analytics
            revenue_analytics = self._get_revenue_analytics(workspace_id)

            # Business performance metrics
            performance_metrics = self._get_services_performance_metrics(workspace_id)

            return {
                'services': list(services),
                'booking_analytics': booking_analytics,
                'client_analytics': client_analytics,
                'revenue_analytics': revenue_analytics,
                'performance_metrics': performance_metrics,
                'admin_metadata': {
                    'export_type': 'admin_api',
                    'includes_analytics': True,
                    'includes_client_data': True
                }
            }

        except Exception as e:
            logger.error(f"Failed to export services admin data for workspace {workspace_id}: {str(e)}")
            raise

    def get_template_variables(self, workspace_id: str) -> Dict[str, Any]:
        """
        Export services data formatted for template variable replacement

        Args:
            workspace_id: UUID of the services workspace

        Returns:
            Dict with template variable mappings
        """
        try:
            # Get workspace info
            Workspace = apps.get_model('core', 'Workspace')
            workspace = Workspace.objects.get(id=workspace_id)

            # Featured services for homepage
            Service = apps.get_model('services', 'Service')
            featured_services = Service.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                booking_enabled=True
            )[:6]  # Limit for performance

            # Service categories
            categories = self._get_active_service_categories(workspace_id)

            # Business profile
            business_profile = self._get_business_profile(workspace_id)

            # Contact and location info
            contact_info = self._get_contact_info(workspace_id)

            # Business hours
            business_hours = self._get_business_hours(workspace_id)

            return {
                # Business information
                'business_name': workspace.name,
                'business_description': workspace.description or '',
                'business_logo': business_profile.get('logo_url', ''),
                'brand_color': business_profile.get('primary_color', '#007bff'),
                'accent_color': business_profile.get('accent_color', '#28a745'),

                # Contact information
                'contact_phone': contact_info.get('phone', ''),
                'contact_email': contact_info.get('email', ''),
                'contact_address': contact_info.get('address', ''),
                'contact_city': contact_info.get('city', ''),
                'social_links': contact_info.get('social_links', {}),

                # Services data
                'featured_services': [
                    {
                        'id': service.id,
                        'name': service.name,
                        'description': service.description,
                        'price': str(service.price),
                        'duration': f"{service.duration_minutes} min",
                        'category': service.category,
                        'featured_image': getattr(service, 'featured_image', ''),
                        'booking_url': f"/services/{workspace.slug}/book/{service.id}"
                    }
                    for service in featured_services
                ],

                # Service categories
                'service_categories': [
                    {
                        'name': cat['category'],
                        'service_count': cat['service_count'],
                        'url': f"/services/{workspace.slug}/category/{cat['category']}"
                    }
                    for cat in categories if cat['category']
                ],

                # Business operations
                'business_hours': business_hours,
                'booking_enabled': True,
                'online_booking': True,
                'appointment_confirmation': business_profile.get('auto_confirm', False),
                'advance_booking_days': business_profile.get('advance_booking_days', 30),

                # Location and service area
                'service_location': {
                    'address': contact_info.get('address', ''),
                    'city': contact_info.get('city', ''),
                    'service_radius': business_profile.get('service_radius_km', 0),
                    'home_visits': business_profile.get('offers_home_visits', False),
                    'in_person': business_profile.get('offers_in_person', True)
                },

                # Business credentials
                'certifications': business_profile.get('certifications', []),
                'experience_years': business_profile.get('experience_years', 0),
                'specialties': business_profile.get('specialties', []),

                # Template metadata
                'template_data': {
                    'workspace_type': 'services',
                    'total_services': featured_services.count(),
                    'booking_system': 'integrated',
                    'last_updated': workspace.updated_at.isoformat() if workspace.updated_at else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to export services template variables for workspace {workspace_id}: {str(e)}")
            raise

    def validate_export_permissions(self, workspace_id: str, user, export_type: str) -> bool:
        """
        Validate user permissions for services data export

        Args:
            workspace_id: UUID of the services workspace
            user: User requesting export
            export_type: Type of export (admin, storefront, template)

        Returns:
            Boolean indicating permission status
        """
        try:
            if not user or not user.is_authenticated:
                return False

            # Public booking and template data are generally accessible
            if export_type in ['storefront', 'template']:
                return True

            # Admin data requires workspace membership
            if export_type == 'admin':
                WorkspaceMembership = apps.get_model('core', 'WorkspaceMembership')
                return WorkspaceMembership.objects.filter(
                    workspace_id=workspace_id,
                    user=user,
                    is_active=True
                ).exists()

            return False

        except Exception as e:
            logger.error(f"Services permission validation failed for workspace {workspace_id}: {str(e)}")
            return False

    # Helper methods for services data export

    def _export_services(self, filters: Dict) -> List[Dict]:
        """Export services with applied filters"""
        Service = apps.get_model('services', 'Service')
        return list(Service.objects.filter(**filters).values(
            'id', 'name', 'description', 'price', 'duration_minutes',
            'category', 'is_active', 'booking_enabled', 'created_at'
        ))

    def _export_bookings(self, workspace_id: str) -> List[Dict]:
        """Export recent bookings (last 90 days for performance)"""
        from django.utils import timezone
        from datetime import timedelta

        ninety_days_ago = timezone.now() - timedelta(days=90)

        return list(Booking.objects.filter(
            service__workspace_id=workspace_id,
            created_at__gte=ninety_days_ago
        ).values(
            'id', 'scheduled_at', 'status', 'service__name',
            'client__name', 'created_at'
        ))

    def _export_clients(self, workspace_id: str) -> List[Dict]:
        """Export client information"""
        Client = apps.get_model('services', 'Client')
        return list(Client.objects.filter(
            workspace_id=workspace_id,
            is_active=True
        ).values(
            'id', 'name', 'email', 'phone', 'created_at'
        ))

    def _export_availability(self, workspace_id: str) -> Dict:
        """Export availability schedules"""
        # This would typically come from an Availability model
        # For now, return default business hours
        return {
            'monday': {'start': '09:00', 'end': '17:00', 'available': True},
            'tuesday': {'start': '09:00', 'end': '17:00', 'available': True},
            'wednesday': {'start': '09:00', 'end': '17:00', 'available': True},
            'thursday': {'start': '09:00', 'end': '17:00', 'available': True},
            'friday': {'start': '09:00', 'end': '17:00', 'available': True},
            'saturday': {'start': '10:00', 'end': '15:00', 'available': True},
            'sunday': {'start': '10:00', 'end': '15:00', 'available': False}
        }

    def _export_services_settings(self, workspace_id: str) -> Dict:
        """Export services-specific settings"""
        return {
            'auto_confirm_bookings': False,
            'advance_booking_days': 30,
            'booking_buffer_minutes': 15,
            'cancellation_policy': '24 hours notice required',
            'payment_required': 'at_booking'
        }

    def _get_public_business_info(self, workspace_id: str) -> Dict:
        """Get public business information"""
        Workspace = apps.get_model('core', 'Workspace')
        workspace = Workspace.objects.get(id=workspace_id)

        return {
            'name': workspace.name,
            'description': workspace.description or '',
            'phone': '',  # Would come from business settings
            'email': '',  # Would come from business settings
            'address': '',  # Would come from business settings
            'booking_policy': 'Online booking available'
        }

    def _get_available_time_slots(self, workspace_id: str) -> List[Dict]:
        """Get available booking time slots for next 30 days"""
        # This would integrate with booking system
        # For now, return sample slots
        from django.utils import timezone
        from datetime import timedelta

        slots = []
        start_date = timezone.now().date()

        for i in range(30):  # Next 30 days
            date = start_date + timedelta(days=i)
            # Skip Sundays for example
            if date.weekday() != 6:
                slots.append({
                    'date': date.isoformat(),
                    'available_times': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
                })

        return slots

    def _get_public_service_categories(self, workspace_id: str) -> List[Dict]:
        """Get service categories with active services"""
        Service = apps.get_model('services', 'Service')

        return list(
            Service.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                booking_enabled=True
            ).values('category').annotate(
                service_count=models.Count('id')
            ).filter(
                category__isnull=False
            ).exclude(
                category=''
            ).order_by('category')
        )

    def _get_booking_analytics(self, workspace_id: str) -> Dict:
        """Get booking analytics for admin"""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        bookings = Booking.objects.filter(service__workspace_id=workspace_id)
        recent_bookings = bookings.filter(created_at__gte=thirty_days_ago)

        return {
            'total_bookings': bookings.count(),
            'bookings_last_30_days': recent_bookings.count(),
            'confirmed_bookings': bookings.filter(status='confirmed').count(),
            'pending_bookings': bookings.filter(status='pending').count(),
            'cancelled_bookings': bookings.filter(status='cancelled').count(),
            'booking_conversion_rate': 85.0  # Would calculate from actual data
        }

    def _get_client_analytics(self, workspace_id: str) -> Dict:
        """Get client analytics"""
        Client = apps.get_model('services', 'Client')
        clients = Client.objects.filter(workspace_id=workspace_id)

        return {
            'total_clients': clients.count(),
            'active_clients': clients.filter(is_active=True).count(),
            'new_clients_this_month': clients.filter(
                created_at__month=timezone.now().month
            ).count(),
            'repeat_client_rate': 65.0  # Would calculate from booking history
        }

    def _get_revenue_analytics(self, workspace_id: str) -> Dict:
        """Get revenue analytics"""
        # This would calculate from completed bookings
        return {
            'total_revenue': 0.0,
            'revenue_last_30_days': 0.0,
            'average_booking_value': 0.0,
            'revenue_by_service': []
        }

    def _get_services_performance_metrics(self, workspace_id: str) -> Dict:
        """Get business performance metrics"""
        Service = apps.get_model('services', 'Service')
        services = Service.objects.filter(workspace_id=workspace_id)

        return {
            'total_services': services.count(),
            'active_services': services.filter(is_active=True).count(),
            'most_popular_services': [],  # Would calculate from booking frequency
            'average_service_duration': services.aggregate(
                avg=models.Avg('duration_minutes')
            )['avg'] or 0
        }

    def _get_active_service_categories(self, workspace_id: str) -> List[Dict]:
        """Get active service categories"""
        Service = apps.get_model('services', 'Service')

        return list(
            Service.objects.filter(
                workspace_id=workspace_id,
                is_active=True
            ).values('category').annotate(
                service_count=models.Count('id')
            ).filter(
                category__isnull=False
            ).exclude(
                category=''
            ).order_by('category')
        )

    def _get_business_profile(self, workspace_id: str) -> Dict:
        """Get business profile settings"""
        # This would typically come from a ServicesProfile model
        return {
            'logo_url': '',
            'primary_color': '#007bff',
            'accent_color': '#28a745',
            'auto_confirm': False,
            'advance_booking_days': 30,
            'service_radius_km': 10,
            'offers_home_visits': True,
            'offers_in_person': True,
            'certifications': [],
            'experience_years': 5,
            'specialties': []
        }

    def _get_contact_info(self, workspace_id: str) -> Dict:
        """Get business contact information"""
        # This would typically come from business settings
        return {
            'phone': '',
            'email': '',
            'address': '',
            'city': '',
            'social_links': {}
        }

    def _get_business_hours(self, workspace_id: str) -> Dict:
        """Get business operating hours"""
        return {
            'monday': '9:00 AM - 5:00 PM',
            'tuesday': '9:00 AM - 5:00 PM',
            'wednesday': '9:00 AM - 5:00 PM',
            'thursday': '9:00 AM - 5:00 PM',
            'friday': '9:00 AM - 5:00 PM',
            'saturday': '10:00 AM - 3:00 PM',
            'sunday': 'Closed'
        }


# Register the services data exporter
from workspace.core.services.base_data_export_service import workspace_data_export_service
workspace_data_export_service.register_exporter('services', ServicesDataExporter())