# Transaction Model - Payment tracking for orders

import uuid
from django.db import models
from decimal import Decimal


class Transaction(models.Model):
    """
    Payment transaction model for tracking payments
    Links to orders for payment processing
    """
    
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('card', 'Credit/Debit Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash on Delivery'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
    ]
    
    # Transaction identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=100, unique=True, help_text="Unique transaction identifier")
    
    # Related order
    order = models.ForeignKey('workspace_store.Order', on_delete=models.CASCADE, related_name='transactions')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Transaction amount")
    currency = models.CharField(max_length=3, default='XAF', help_text="Transaction currency")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, help_text="Payment method used")
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    
    # Gateway information
    gateway = models.CharField(max_length=50, blank=True, help_text="Payment gateway used")
    gateway_transaction_id = models.CharField(max_length=255, blank=True, help_text="Gateway transaction ID")
    gateway_response = models.JSONField(default=dict, help_text="Full gateway response")
    
    # Metadata
    reference = models.CharField(max_length=255, blank=True, help_text="Transaction reference")
    description = models.TextField(blank=True, help_text="Transaction description")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True, help_text="When transaction was processed")
    
    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['gateway_transaction_id']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Generate transaction ID if not provided
        if not self.transaction_id:
            self.transaction_id = self._generate_transaction_id()
        super().save(*args, **kwargs)
    
    def _generate_transaction_id(self):
        """Generate unique transaction ID"""
        import uuid
        from datetime import datetime
        
        # Format: TXN-YYYYMMDD-XXXXXXXX
        date_str = datetime.now().strftime('%Y%m%d')
        short_uuid = str(uuid.uuid4())[:8].upper()
        return f"TXN-{date_str}-{short_uuid}"
    
    @property
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        """Check if transaction is pending"""
        return self.status in ['pending', 'processing']
    
    @property
    def can_be_refunded(self):
        """Check if transaction can be refunded"""
        return self.status == 'completed' and self.amount > 0
    
    def mark_as_completed(self):
        """Mark transaction as completed"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
        
        # Update related order payment status
        self.order.payment_status = 'paid'
        self.order.save(update_fields=['payment_status'])
    
    def mark_as_failed(self, reason=None):
        """Mark transaction as failed"""
        from django.utils import timezone
        
        self.status = 'failed'
        self.processed_at = timezone.now()
        
        if reason:
            if not self.gateway_response:
                self.gateway_response = {}
            self.gateway_response['failure_reason'] = reason
        
        self.save(update_fields=['status', 'processed_at', 'gateway_response'])
        
        # Update related order payment status
        self.order.payment_status = 'failed'
        self.order.save(update_fields=['payment_status'])
    
    def create_refund(self, amount=None, reason=None):
        """Create refund transaction"""
        refund_amount = amount or self.amount
        
        if refund_amount > self.amount:
            raise ValueError("Refund amount cannot exceed original transaction amount")
        
        refund = Transaction.objects.create(
            order=self.order,
            amount=-refund_amount,  # Negative amount for refunds
            currency=self.currency,
            payment_method=self.payment_method,
            gateway=self.gateway,
            status='pending',
            reference=f"REFUND-{self.transaction_id}",
            description=f"Refund for {self.transaction_id}: {reason or 'No reason provided'}"
        )
        
        return refund