# Client Model
from django.db import models
from workspace.core.models.base_models import TenantScopedModel


class Client(TenantScopedModel):
    """Client/customer for services"""
    
    # Core fields
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True, help_text='Internal notes about the client')
    
    # Relationships
    
    class Meta:
        db_table = 'workspace_clients'
        unique_together = ['workspace', 'email']
        ordering = ['name']
        indexes = [
            models.Index(fields=['workspace', 'email']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.workspace.name} - {self.name}"
    
    @property
    def total_bookings(self):
        """Get total number of bookings for this client"""
        return self.bookings.count()
    
    @property
    def total_spent(self):
        """Get total amount spent by this client"""
        from django.db.models import Sum
        total = self.invoices.aggregate(Sum('amount'))['amount__sum']
        return total or 0