# Booking Management Service
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.apps import apps
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('workspace.services.services')


class BookingService:
    """Service for managing bookings/appointments"""
    
    @staticmethod
    def create_booking(service, client, scheduled_at, notes='', assigned_staff=None):
        """Create a new booking"""
        Booking = apps.get_model('services', 'Booking')
        
        # Validate booking time
        if not BookingService._validate_booking_time(service, scheduled_at):
            raise ValidationError("Invalid booking time")
        
        # Check for conflicts
        if BookingService._has_booking_conflict(service, scheduled_at, assigned_staff):
            raise ValidationError("Booking conflict detected")
        
        try:
            with transaction.atomic():
                booking = Booking.objects.create(
                    service=service,
                    client=client,
                    scheduled_at=scheduled_at,
                    notes=notes,
                    assigned_staff=assigned_staff,
                    status='pending'
                )
                
                logger.info(f"Booking created: {service.title} for {client.name}")
                return booking
                
        except Exception as e:
            logger.error(f"Failed to create booking: {str(e)}")
            raise ValidationError(f"Failed to create booking: {str(e)}")
    
    @staticmethod
    def update_booking_status(booking, status, user):
        """Update booking status"""
        if status not in ['pending', 'confirmed', 'cancelled']:
            raise ValidationError("Invalid booking status")
        
        try:
            with transaction.atomic():
                booking.status = status
                booking.save()
                
                logger.info(f"Booking {booking.id} status changed to {status}")
                return booking
                
        except Exception as e:
            logger.error(f"Failed to update booking status: {str(e)}")
            raise ValidationError(f"Failed to update booking status: {str(e)}")
    
    @staticmethod
    def reschedule_booking(booking, new_scheduled_at, user):
        """Reschedule a booking"""
        # Validate new time
        if not BookingService._validate_booking_time(booking.service, new_scheduled_at):
            raise ValidationError("Invalid reschedule time")
        
        # Check for conflicts
        if BookingService._has_booking_conflict(
            booking.service, new_scheduled_at, booking.assigned_staff, exclude_booking=booking
        ):
            raise ValidationError("Booking conflict detected for new time")
        
        try:
            with transaction.atomic():
                booking.scheduled_at = new_scheduled_at
                booking.save()
                
                logger.info(f"Booking {booking.id} rescheduled to {new_scheduled_at}")
                return booking
                
        except Exception as e:
            logger.error(f"Failed to reschedule booking: {str(e)}")
            raise ValidationError(f"Failed to reschedule booking: {str(e)}")
    
    @staticmethod
    def cancel_booking(booking, user):
        """Cancel a booking"""
        return BookingService.update_booking_status(booking, 'cancelled', user)
    
    @staticmethod
    def get_workspace_bookings(workspace, status=None, date_range=None):
        """Get bookings for workspace"""
        Booking = apps.get_model('services', 'Booking')
        
        queryset = Booking.objects.filter(service__workspace=workspace)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_range:
            start_date, end_date = date_range
            queryset = queryset.filter(
                scheduled_at__gte=start_date,
                scheduled_at__lte=end_date
            )
        
        return queryset.select_related('service', 'client', 'assigned_staff').order_by('-scheduled_at')
    
    @staticmethod
    def get_client_bookings(client, status=None):
        """Get bookings for specific client"""
        Booking = apps.get_model('services', 'Booking')
        
        queryset = Booking.objects.filter(client=client)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('service').order_by('-scheduled_at')
    
    @staticmethod
    def get_staff_bookings(staff, date_range=None):
        """Get bookings for specific staff member"""
        Booking = apps.get_model('services', 'Booking')
        
        queryset = Booking.objects.filter(assigned_staff=staff)
        
        if date_range:
            start_date, end_date = date_range
            queryset = queryset.filter(
                scheduled_at__gte=start_date,
                scheduled_at__lte=end_date
            )
        
        return queryset.select_related('service', 'client').order_by('scheduled_at')
    
    @staticmethod
    def _validate_booking_time(service, scheduled_at):
        """Validate booking time constraints"""
        workspace = service.workspace
        profile = workspace.services_profile
        
        # Check if it's not in the past
        if scheduled_at <= timezone.now():
            return False
        
        # Check minimum notice period
        min_notice = timedelta(hours=profile.booking_notice_hours)
        if scheduled_at <= timezone.now() + min_notice:
            return False
        
        # Check maximum advance booking
        max_advance = timedelta(days=profile.booking_advance_days)
        if scheduled_at >= timezone.now() + max_advance:
            return False
        
        # Check if day is a working day
        weekday = scheduled_at.weekday()
        if weekday not in profile.working_days:
            return False
        
        # Check business hours
        booking_time = scheduled_at.time()
        if not (profile.business_hours_start <= booking_time <= profile.business_hours_end):
            return False
        
        return True
    
    @staticmethod
    def _has_booking_conflict(service, scheduled_at, assigned_staff=None, exclude_booking=None):
        """Check for booking conflicts"""
        Booking = apps.get_model('services', 'Booking')
        
        # Calculate booking end time
        end_time = scheduled_at + timedelta(minutes=service.duration)
        
        # Check for overlapping bookings
        conflicts = Booking.objects.filter(
            status__in=['pending', 'confirmed'],
            scheduled_at__lt=end_time,
            # Calculated end time overlaps with start time
        )
        
        # Add service duration to scheduled_at for each booking to get end time
        # This is a simplified check - in production, you'd want to be more precise
        for booking in conflicts:
            booking_end = booking.scheduled_at + timedelta(minutes=booking.service.duration)
            if scheduled_at < booking_end and end_time > booking.scheduled_at:
                # If assigned to same staff, it's definitely a conflict
                if assigned_staff and booking.assigned_staff == assigned_staff:
                    if exclude_booking and booking.id != exclude_booking.id:
                        return True
                    elif not exclude_booking:
                        return True
        
        return False