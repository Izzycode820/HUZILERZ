"""
Template Marketplace Models
Handles template purchases, developer commissions, and stacked discount system
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()

class TemplatePurchase(models.Model):
    """
    Template purchases with stacked discount integration
    Links template purchases to subscription discounts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Purchase details
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='template_purchases')
    template = models.ForeignKey('theme.Template', on_delete=models.CASCADE)
    
    # Pricing
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Stacked discount system integration
    subscription_discount = models.JSONField(default=dict, blank=True, help_text="Discount details applied")
    triggered_subscription_bonus = models.BooleanField(default=False)
    
    # License and access
    license_type = models.CharField(max_length=50, default='standard')
    license_expires_at = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    max_downloads = models.IntegerField(default=10)
    
    # Payment tracking
    payment_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    
    # Usage tracking
    used_in_workspaces = models.ManyToManyField(
        'workspace_core.Workspace', 
        blank=True,
        help_text="Workspaces where this template is used"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [['buyer', 'template']]
        indexes = [
            models.Index(fields=['buyer']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.buyer.email} - {self.template.name} - {self.final_price} FCFA"
    
    @property
    def discount_percentage(self):
        if self.original_price == 0:
            return 0
        return (self.discount_applied / self.original_price) * 100
    
    @property
    def can_download(self):
        return (
            self.payment_status == 'completed' and 
            self.download_count < self.max_downloads and
            (not self.license_expires_at or timezone.now() <= self.license_expires_at)
        )
    
    def apply_simple_discount(self, discount_percentage=0):
        """
        Apply simple percentage discount (for future template marketplace)
        """
        if discount_percentage > 0:
            self.discount_applied = self.original_price * (Decimal(discount_percentage) / 100)
            self.final_price = self.original_price - self.discount_applied
        else:
            self.discount_applied = Decimal('0')
            self.final_price = self.original_price

        self.subscription_discount = {
            'discount_percentage': discount_percentage,
            'discount_amount': float(self.discount_applied),
            'final_price': float(self.final_price)
        }

        return self.subscription_discount
    
    def record_download(self):
        """Record a template download"""
        if self.can_download:
            self.download_count += 1
            self.save()
            return True
        return False


class DeveloperCommission(models.Model):
    """
    Track commissions for developer template sales
    Revenue stream #3: Developer Platform commission-based revenue sharing
    """
    COMMISSION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Commission details
    template_purchase = models.OneToOneField(TemplatePurchase, on_delete=models.CASCADE)
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commissions_earned')
    
    # Commission calculation
    sale_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4)  # 0.15 = 15%
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=COMMISSION_STATUS_CHOICES, default='pending')
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Payment details
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['developer']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.developer.email} - {self.commission_amount} FCFA - {self.status}"
    
    def calculate_commission(self):
        """Calculate commission based on sale amount and rate"""
        self.commission_amount = self.sale_amount * self.commission_rate
        self.platform_fee = self.sale_amount - self.commission_amount
        return self.commission_amount
    
    def approve_commission(self):
        """Approve commission for payment"""
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()
    
    def mark_paid(self, payment_method, payment_reference):
        """Mark commission as paid"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self.save()


class DeveloperProfile(models.Model):
    """
    Extended profile for template developers
    Revenue stream #3: Developer Platform features
    """
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='developer_profile')
    
    # Developer information
    display_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Verification and status
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES, 
        default='pending'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Revenue tracking
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_sales = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Commission settings
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        default=Decimal('0.15'),  # 15% default
        help_text="Commission rate (15-30% based on volume)"
    )
    
    # Payment preferences
    preferred_payment_method = models.CharField(max_length=50, default='mtn_momo')
    payment_phone_number = models.CharField(max_length=20, blank=True)
    payment_details = models.JSONField(default=dict, blank=True)
    
    # Performance metrics
    templates_published = models.IntegerField(default=0)
    templates_sold = models.IntegerField(default=0)
    customer_satisfaction = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_earnings', '-total_sales']
    
    def __str__(self):
        return f"{self.display_name} - {self.total_earnings} FCFA earned"
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'
    
    @property
    def commission_tier(self):
        """Calculate commission rate based on volume (from brainstorm)"""
        if self.total_sales >= 100:
            return 'tier_3'  # 30% for high volume
        elif self.total_sales >= 50:
            return 'tier_2'  # 25% for medium volume
        else:
            return 'tier_1'  # 15% for low volume
    
    def update_commission_rate(self):
        """Update commission rate based on performance"""
        tier_rates = {
            'tier_1': Decimal('0.15'),  # 15%
            'tier_2': Decimal('0.25'),  # 25%
            'tier_3': Decimal('0.30'),  # 30%
        }
        
        old_rate = self.commission_rate
        self.commission_rate = tier_rates.get(self.commission_tier, Decimal('0.15'))
        
        if old_rate != self.commission_rate:
            self.save()
            return True
        return False