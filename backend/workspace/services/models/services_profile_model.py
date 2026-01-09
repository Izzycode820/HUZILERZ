# Services Profile Model
from django.db import models
from workspace.core.models.base_models import BaseWorkspaceExtension


class ServicesProfile(BaseWorkspaceExtension):
    """Services workspace profile with service-specific settings"""
    
    # Core settings
    business_name = models.CharField(max_length=200, default='My Services')
    business_description = models.TextField(blank=True)
    booking_advance_days = models.PositiveIntegerField(
        default=30,
        help_text='How many days in advance clients can book'
    )
    booking_notice_hours = models.PositiveIntegerField(
        default=24,
        help_text='Minimum notice required for booking (in hours)'
    )
    
    # Business hours
    business_hours_start = models.TimeField(default='09:00:00')
    business_hours_end = models.TimeField(default='17:00:00')
    working_days = models.JSONField(
        default=list,
        help_text='List of working days (0=Monday, 6=Sunday)'
    )
    
    # Payment settings
    require_payment_upfront = models.BooleanField(default=False)
    accept_online_payments = models.BooleanField(default=True)
    
    # Communication settings
    send_booking_confirmations = models.BooleanField(default=True)
    send_booking_reminders = models.BooleanField(default=True)
    reminder_hours_before = models.PositiveIntegerField(default=24)
    
    # Relationships
    
    class Meta:
        db_table = 'workspace_services_profiles'
        verbose_name = 'Services Profile'
        verbose_name_plural = 'Services Profiles'
    
    def __str__(self):
        return f"Services Profile: {self.workspace.name}"
    
    def save(self, *args, **kwargs):
        # Set default working days (Monday to Friday: 0-4)
        if not self.working_days:
            self.working_days = [0, 1, 2, 3, 4]
        super().save(*args, **kwargs)