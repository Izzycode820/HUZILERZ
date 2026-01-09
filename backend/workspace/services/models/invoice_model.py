# Invoice Model  
from django.db import models
from django.core.validators import MinValueValidator
from workspace.core.models.base_models import TenantScopedModel


class Invoice(TenantScopedModel):
    """Invoice for services"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    
    # Core fields
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Relationships
    booking = models.ForeignKey(
        'services.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invoices',
        help_text='Nullable since invoice might be general retainer'
    )
    
    class Meta:
        db_table = 'workspace_invoices'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['issued_at']),
            models.Index(fields=['booking']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.booking.client.name if self.booking else 'No Client'} - ${self.amount}"
    
    
