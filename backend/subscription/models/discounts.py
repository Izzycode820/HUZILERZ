"""
Simplified Discount System
Only yearly billing discount and template ownership bonus
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

DISCOUNT_TYPE_CHOICES = [
    ('yearly_billing', 'Yearly Billing Discount'),
    ('template_bonus', 'Template Ownership Bonus'),
]

class Discount(models.Model):
    """
    Simplified discount system - only two types
    """
    name = models.CharField(max_length=100)
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES
    )

    # Discount value
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Discount percentage (e.g., 15.00 for 15%)"
    )

    # For template bonus - free months instead of percentage
    bonus_months = models.PositiveIntegerField(
        default=0,
        help_text="Free months for template bonus (usually 3)"
    )

    # Applicability
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_discounts'
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'

    def __str__(self):
        if self.discount_type == 'template_bonus':
            return f"{self.name} - {self.bonus_months} months free"
        return f"{self.name} - {self.percentage}%"

    @classmethod
    def get_yearly_discount(cls):
        """Get active yearly billing discount"""
        return cls.objects.filter(
            discount_type='yearly_billing',
            is_active=True
        ).first()

    @classmethod
    def get_template_bonus(cls):
        """Get active template bonus"""
        return cls.objects.filter(
            discount_type='template_bonus',
            is_active=True
        ).first()

class UserDiscount(models.Model):
    """
    Track discount usage by users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discounts')
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE)
    subscription = models.ForeignKey(
        'Subscription',
        on_delete=models.CASCADE,
        related_name='user_applied_discounts'
    )

    # Applied values
    amount_discounted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    months_added = models.PositiveIntegerField(
        default=0,
        help_text="Free months added for template bonus"
    )

    # Context
    template_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Template ID that triggered the bonus (if applicable)"
    )

    # Timestamps
    applied_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'user_discounts'
        verbose_name = 'User Discount'
        verbose_name_plural = 'User Discounts'

    def __str__(self):
        return f"{self.user.email} - {self.discount.name}"