# Service Model
from django.db import models
from django.core.validators import MinValueValidator
from workspace.core.models.base_models import TenantScopedModel


class Service(TenantScopedModel):
    """Service offered by the workspace"""
    
    # Core fields
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    duration_minutes = models.PositiveIntegerField(
        help_text='Duration in minutes'
    )
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Relationships
    
    class Meta:
        db_table = 'workspace_services'
        ordering = ['name']
        indexes = [
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.workspace.name} - {self.name}"
    
    @property
    def duration_hours(self):
        """Get duration in hours"""
        return self.duration_minutes / 60