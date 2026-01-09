"""
Simplified Trial System - Clean Implementation
Single trial per user with fixed 30-day period and upgrade capability
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal

User = get_user_model()

TRIAL_PRICES = {
    'beginning': Decimal('2000.00'),
    'pro': Decimal('5000.00'),
    'enterprise': Decimal('10000.00')
}

TRIAL_STATUS_CHOICES = [
    ('pending_payment', 'Pending Payment'),
    ('active', 'Active'),
    ('expired', 'Expired'),
    ('converted', 'Converted'),
    ('cancelled', 'Cancelled'),
]

TIER_CHOICES = [
    ('beginning', 'Beginning'),
    ('pro', 'Pro'),
    ('enterprise', 'Enterprise'),
]

class Trial(models.Model):
    """
    Simplified trial system - one trial per user, fixed 30 days, upgrade capability
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='trial'
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='beginning',
        help_text="Current trial tier"
    )
    payment_intent = models.ForeignKey('payments.PaymentIntent', on_delete=models.SET_NULL, null=True, blank=True)

    # Trial period (configurable duration)
    trial_duration_days = models.IntegerField(
        default=28,
        help_text="Trial duration in days (default: 28)"
    )
    started_at = models.DateTimeField(null=True, blank=True, help_text="Set when payment completes")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Set when payment completes")

    # Payment tracking
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount paid for trial"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Payment status from webhook"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=TRIAL_STATUS_CHOICES,
        default='pending_payment'
    )

    # Upgrade tracking (simplified JSON field)
    upgrade_history = models.JSONField(
        default=list,
        help_text="Track tier upgrades during trial period"
    )
    upgrade_metadata = models.JSONField(
        default=dict,
        help_text="Metadata for pending upgrade (matches subscription pattern)"
    )

    # Conversion tracking
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_to_subscription = models.ForeignKey(
        'Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_trial'
    )
    conversion_metadata = models.JSONField(
        default=dict,
        help_text="Metadata for trial conversion"
    )
    cancellation_metadata = models.JSONField(
        default=dict,
        help_text="Metadata for trial cancellation"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_trials'
        verbose_name = 'Trial'
        verbose_name_plural = 'Trials'

    def __str__(self):
        return f"{self.user.email} - {self.tier.title()} Trial"

    def save(self, *args, **kwargs):
        # Webhook-driven: expires_at is set when payment completes
        # No auto-setting of dates
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if trial has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def days_remaining(self):
        """Calculate days remaining in trial"""
        if not self.expires_at or self.is_expired:
            return 0
        remaining = self.expires_at - timezone.now()
        return remaining.days

    @property
    def hours_remaining(self):
        """Calculate hours remaining in trial"""
        if self.is_expired:
            return 0
        remaining = self.expires_at - timezone.now()
        return int(remaining.total_seconds() / 3600)

    @property
    def can_upgrade(self):
        """Check if trial can be upgraded to higher tier"""
        # Allow upgrades from both active and pending_payment (webhook processing)
        # Matches Stripe/Azure pattern: webhooks process upgrades from pending_payment state
        if self.status not in ['active', 'pending_payment'] or self.is_expired:
            return False

        tier_hierarchy = ['beginning', 'pro', 'enterprise']
        current_index = tier_hierarchy.index(self.tier)
        return current_index < len(tier_hierarchy) - 1

    @property
    def next_tier_options(self):
        """Get available upgrade tiers"""
        if not self.can_upgrade:
            return []

        tier_hierarchy = ['beginning', 'pro', 'enterprise']
        current_index = tier_hierarchy.index(self.tier)
        return tier_hierarchy[current_index + 1:]

    def calculate_upgrade_cost(self, target_tier):
        """Calculate cost to upgrade to target tier"""
        if target_tier not in self.next_tier_options:
            raise ValueError(f"Cannot upgrade from {self.tier} to {target_tier}")

        target_price = TRIAL_PRICES[target_tier]
        return target_price - self.amount_paid

    def upgrade_to_tier(self, target_tier, payment_amount):
        """Upgrade trial to higher tier"""
        if target_tier not in self.next_tier_options:
            raise ValueError(f"Cannot upgrade from {self.tier} to {target_tier}")

        expected_cost = self.calculate_upgrade_cost(target_tier)
        if payment_amount != expected_cost:
            raise ValueError(f"Expected payment of {expected_cost}, got {payment_amount}")

        # Record upgrade
        upgrade_record = {
            "from_tier": self.tier,
            "to_tier": target_tier,
            "amount_paid": float(payment_amount),
            "upgraded_at": timezone.now().isoformat()
        }
        self.upgrade_history.append(upgrade_record)

        # Update trial
        self.tier = target_tier
        self.amount_paid += payment_amount
        self.save()

    def convert_to_subscription(self, subscription):
        """Convert trial to full subscription"""
        self.status = 'converted'
        self.converted_at = timezone.now()
        self.converted_to_subscription = subscription
        self.save()

    def cancel(self):
        """Cancel the trial"""
        self.status = 'cancelled'
        self.save()

    def expire(self):
        """Mark trial as expired"""
        self.status = 'expired'
        self.save()

    @classmethod
    def get_trial_price(cls, tier):
        """Get trial price for a tier"""
        return TRIAL_PRICES.get(tier, Decimal('0.00'))

    @classmethod
    def get_all_trial_prices(cls):
        """Get all trial prices"""
        return TRIAL_PRICES.copy()

