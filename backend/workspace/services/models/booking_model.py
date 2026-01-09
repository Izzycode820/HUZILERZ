# Booking Model
from django.db import models
from django.contrib.auth import get_user_model
from workspace.core.models.base_models import TenantScopedModel

User = get_user_model()


class Booking(TenantScopedModel):
    """Service booking/appointment"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Core fields
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text='Special requests or notes')
    
    # Relationships
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    client = models.ForeignKey(
        'services.Client',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    assigned_staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings',
        help_text='Staff member assigned to provide the service'
    )
    
    class Meta:
        db_table = 'workspace_bookings'
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['service', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['client']),
            models.Index(fields=['assigned_staff']),
        ]
    
    def __str__(self):
        return f"{self.service.name} - {self.client.name} on {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def workspace(self):
        """Get workspace through service"""
        return self.service.workspace
    
    @property
    def duration_end(self):
        """Calculate end time based on service duration"""
        from datetime import timedelta
        return self.scheduled_at + timedelta(minutes=self.service.duration_minutes)