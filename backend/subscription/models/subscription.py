"""
Multi-Revenue Stream Subscription Models
Core subscription system for workspace subscriptions with hosting resource allocation
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()

class SubscriptionPlan(models.Model):
    """
    Subscription plan template - Minimal model
    Feature definitions loaded from subscriptions/plans.yaml
    Synced via: python manage.py sync_plans
    """
    TIER_CHOICES = [
        ('free', 'Free'),
        ('beginning', 'Beginning'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    description = models.TextField(blank=True, help_text="Plan description for pricing page")

    # Intro Pricing (28-day first cycle, same for all billing cycles)
    intro_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Intro price for 28-day first cycle (first-time users only)"
    )
    intro_duration_days = models.IntegerField(
        default=28,
        help_text="Intro period duration in days (default: 28)"
    )

    # Regular Pricing (based on billing_cycle)
    regular_price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Regular monthly price (30 days)"
    )
    regular_price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Regular yearly price (365 days)"
    )

    # All features stored in YAML and loaded at runtime
    # No hardcoded feature fields - use CapabilityEngine instead

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['regular_price_monthly']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} - {self.regular_price_monthly} FCFA/month"

    def clean(self):
        """Validate plan configuration"""
        if self.tier == 'free' and (self.regular_price_monthly > 0 or self.regular_price_yearly > 0):
            raise ValidationError("Free tier must have 0 price")

    @property
    def is_paid_tier(self):
        return self.tier != 'free'

    @property
    def target_market(self):
        """Return target market description"""
        market_map = {
            'free': 'conversion_focused',
            'beginner': 'side_hustlers_students',
            'pro': 'solopreneurs',
            'enterprise': 'companies_firms'
        }
        return market_map.get(self.tier, 'unknown')

    def get_capabilities(self):
        """
        Get all capabilities for this plan from YAML
        Uses CapabilityEngine to load features
        """
        from subscription.services.capability_engine import CapabilityEngine
        return CapabilityEngine.get_plan_capabilities(self.tier)

    def get_price(self, billing_cycle='monthly', billing_phase='regular'):
        """
        Get price based on billing cycle and phase

        Args:
            billing_cycle: 'monthly' or 'yearly'
            billing_phase: 'intro' or 'regular'

        Returns:
            Decimal: Price in FCFA
        """
        if billing_phase == 'intro':
            return self.intro_price

        if billing_cycle == 'yearly':
            return self.regular_price_yearly

        return self.regular_price_monthly

    def get_cycle_duration_days(self, billing_phase='regular'):
        """
        Get cycle duration in days based on billing phase

        Args:
            billing_phase: 'intro' or 'regular'

        Returns:
            int: Duration in days
        """
        if billing_phase == 'intro':
            return self.intro_duration_days

        # Regular cycles default to 30 days (monthly) or 365 days (yearly)
        # Note: billing_cycle is on Subscription model, not Plan
        return 30  # Default for monthly


class Subscription(models.Model):
    """
    User subscription with manual renewal system for Cameroon market
    Links to workspace for multi-tenant resource allocation
    """
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('change_pending', 'Change Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('grace_period', 'Grace Period'),
        ('restricted', 'Restricted'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    payment_intent = models.ForeignKey('payments.PaymentIntent', on_delete=models.SET_NULL, null=True, blank=True)

    # Workspace link (for multi-tenant resource scoping)
    primary_workspace = models.ForeignKey(
        'workspace_core.Workspace', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Primary workspace for this subscription"
    )
    
    # Subscription lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Billing configuration
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    BILLING_PHASE_CHOICES = [
        ('intro', 'Intro Pricing'),
        ('regular', 'Regular Pricing'),
    ]

    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default='monthly',
        help_text="Billing cycle duration (monthly = 30 days, yearly = 365 days)"
    )
    billing_phase = models.CharField(
        max_length=20,
        choices=BILLING_PHASE_CHOICES,
        default='regular',
        help_text="Current billing phase - intro pricing or regular pricing"
    )
    currency = models.CharField(
        max_length=10,
        default='XAF',
        help_text="Currency code (ISO 4217)"
    )

    # Intro pricing tracking
    intro_cycles_remaining = models.IntegerField(
        default=0,
        help_text="Number of intro cycles remaining (typically 1 for 28-day intro)"
    )

    # Cycle tracking (replaces simple started_at/expires_at)
    current_cycle_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When current billing cycle started"
    )
    current_cycle_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When current billing cycle ends"
    )

    # Legacy fields (kept for backward compatibility during migration)
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Manual renewal system (no auto-billing)
    last_manual_renewal = models.DateTimeField(null=True, blank=True)
    next_renewal_reminder = models.DateTimeField(null=True, blank=True)
    grace_period_ends_at = models.DateTimeField(null=True, blank=True)
    
    
    # Discount tracking (for template purchase integration)
    applied_discounts = models.JSONField(default=dict, blank=True)
    
    # Downgrade handling (effective next billing cycle)
    pending_plan_change = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pending_subscriptions',
        help_text="Plan to switch to at next billing cycle"
    )
    plan_change_effective_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    subscription_metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'status']),  # Common query pattern
            models.Index(fields=['status', 'expires_at']),  # Active subscription checks
            models.Index(fields=['plan', 'status']),  # Plan-based queries
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    def clean(self):
        """Validate subscription configuration"""
        if self.expires_at and self.expires_at <= self.started_at:
            raise ValidationError("Expiry date must be after start date")
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_expired(self):
        if self.expires_at is None:
            return False  # Free plans never expire
        return timezone.now() > self.expires_at
    
    @property
    def is_in_grace_period(self):
        if not self.grace_period_ends_at:
            return False
        return timezone.now() <= self.grace_period_ends_at

    @property
    def is_restricted(self):
        return self.status == 'restricted'
    
    @property
    def days_until_expiry(self):
        if self.expires_at is None:
            return None  # Free plans have no expiry
        if self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return delta.days

    @property
    def is_in_renewal_window(self):
        """
        Check if subscription is in 5-day renewal window
        Industry standard: Allow renewals/upgrades 5 days before expiry
        """
        if not self.expires_at or self.plan.tier == 'free':
            return False

        days_left = self.days_until_expiry
        if days_left is None:
            return False

        # 5-day window (days 26-30 of 30-day cycle)
        return 0 <= days_left <= 5 and self.status == 'active'

    @property
    def can_renew_or_upgrade(self):
        """
        Check if user can renew or upgrade based on subscription state
        Renewal/Upgrade allowed in:
        1. 5-day renewal window (active subscription)
        2. Grace period (after expiry, before grace expires)
        """
        # In renewal window (5 days before expiry)
        if self.is_in_renewal_window:
            return True

        # In grace period (after expiry)
        if self.status == 'grace_period' and self.is_in_grace_period:
            return True

        return False

    @property
    def is_old_plan_still_valid(self):
        """
        Check if subscription still has validity (for payment failure reversion)
        Used when upgrade/renewal payment fails
        """
        if self.status == 'active' and self.expires_at:
            # Active and not yet expired
            return not self.is_expired

        if self.status == 'grace_period':
            # In grace period and grace hasn't expired
            return self.is_in_grace_period

        return False
    
    def extend_subscription(self, days=30):
        """Extend subscription for manual renewal"""
        self.expires_at = timezone.now() + timezone.timedelta(days=days)
        self.status = 'active'
        self.last_manual_renewal = timezone.now()
        self.save()
    
    def start_grace_period(self, hours=72):
        """Start 72-hour grace period after expiry"""
        self.status = 'grace_period'
        self.grace_period_ends_at = timezone.now() + timezone.timedelta(hours=hours)
        self.save()
    
    def suspend_subscription(self, reason='payment_failure'):
        """Suspend subscription while preserving data"""
        self.status = 'suspended'
        self.subscription_metadata['suspension_reason'] = reason
        self.subscription_metadata['suspended_at'] = timezone.now().isoformat()
        self.save()
    
    def reactivate_subscription(self):
        """Reactivate suspended subscription"""
        if self.status == 'suspended':
            self.status = 'active'
            self.payment_failures_count = 0
            self.subscription_metadata.pop('suspension_reason', None)
            self.subscription_metadata.pop('suspended_at', None)
            self.save()
    
    def schedule_plan_change(self, new_plan, effective_date=None):
        """Schedule plan change for next billing cycle"""
        if not effective_date:
            effective_date = self.expires_at
        
        self.pending_plan_change = new_plan
        self.plan_change_effective_date = effective_date
        self.save()
    
    def apply_pending_plan_change(self):
        """Apply scheduled plan change (called at billing cycle)"""
        if self.pending_plan_change and timezone.now() >= self.plan_change_effective_date:
            old_plan = self.plan
            self.plan = self.pending_plan_change
            self.pending_plan_change = None
            self.plan_change_effective_date = None
            
            # Log the change
            self.subscription_metadata['plan_changes'] = self.subscription_metadata.get('plan_changes', [])
            self.subscription_metadata['plan_changes'].append({
                'from_plan': old_plan.name,
                'to_plan': self.plan.name,
                'changed_at': timezone.now().isoformat()
            })

            self.save()
            return True
        return False
    
    def save(self, *args, **kwargs):
        """Save subscription - signals will handle module provisioning"""
        super().save(*args, **kwargs)


class SubscriptionHistory(models.Model):
    """Track subscription changes and payment history"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('renewed', 'Renewed'),
        ('upgraded', 'Upgraded'),
        ('downgraded', 'Downgraded'),
        ('converted', 'Converted'),
        ('suspended', 'Suspended'),
        ('reactivated', 'Reactivated'),
        ('cancelled', 'Cancelled'),
    ]

    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('pending', 'Pending'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    # Bill tracking
    bill_number = models.CharField(
        max_length=120,
        unique=True,
        editable=False,
        help_text="Human-readable bill number (e.g., #452157574)"
    )
    status = models.CharField(
        max_length=120,
        choices=STATUS_CHOICES,
        default='unpaid',
        help_text="Payment status of this bill"
    )

    # Plan changes
    previous_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_subscriptions'
    )
    new_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='new_subscriptions'
    )

    # Payment information
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)

    # Additional context
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscription History'
        verbose_name_plural = 'Subscription Histories'
        indexes = [
            models.Index(fields=['bill_number']),
            models.Index(fields=['status']),
            models.Index(fields=['subscription', 'status']),
        ]

    def __str__(self):
        return f"{self.subscription.user.email} - {self.action} - {self.created_at}"

    def save(self, *args, **kwargs):
        """
        Auto-generate bill number on creation using database-level atomicity
        Uses Max() + retry mechanism to handle race conditions safely
        Reference: https://hakibenita.com/how-to-manage-concurrency-in-django-models
        """
        if not self.bill_number:
            from django.db.models import Max
            from django.db import transaction, IntegrityError
            import time

            # CRITICAL: Retry mechanism for handling unique constraint violations
            # If two requests generate same bill number, database rejects duplicate
            # We retry with fresh Max() query to get next available number
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    with transaction.atomic():
                        # Get the maximum bill number atomically from database
                        max_bill = SubscriptionHistory.objects.aggregate(
                            max_num=Max('bill_number')
                        )['max_num']

                        if max_bill:
                            try:
                                # Extract number from format: #400000001 → 400000001
                                last_num = int(max_bill.replace('#', ''))
                                next_num = last_num + 1
                            except (ValueError, AttributeError):
                                # Fallback if bill_number format is corrupted
                                next_num = 400000000
                        else:
                            # No bills exist yet, start sequence
                            next_num = 400000000

                        self.bill_number = f"#{next_num}"
                        super().save(*args, **kwargs)
                        return  # Success - exit retry loop

                except IntegrityError as e:
                    if 'bill_number' in str(e) and attempt < max_retries - 1:
                        # Duplicate bill number detected - retry with fresh Max() query
                        time.sleep(0.01 * (attempt + 1))  # Exponential backoff
                        self.bill_number = None  # Reset for retry
                        continue
                    else:
                        # Different IntegrityError or max retries exceeded
                        raise
        else:
            # Bill number already set - normal save
            super().save(*args, **kwargs)


class PaymentRecord(models.Model):
    """
    Payment record linking PaymentIntent to Subscription
    Stores Cameroon mobile money payment details
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    CHARGE_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('subscription_renewal', 'Subscription Renewal'),
        ('subscription_upgrade', 'Subscription Upgrade'),
        ('domain', 'Domain'),
        ('domain_renewal', 'Domain Renewal'),
        ('theme', 'Theme'),
        ('checkout', 'Checkout'),
        ('addon', 'Add-on'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_records')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payment_records')
    payment_intent = models.ForeignKey('payments.PaymentIntent', on_delete=models.CASCADE, related_name='payment_records')

    # Payment details
    amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Amount in XAF")
    reference = models.CharField(max_length=255, blank=True, help_text="Payment reference")

    # Charge classification
    charge_type = models.CharField(
        max_length=30,
        choices=CHARGE_TYPE_CHOICES,
        default='subscription',
        help_text="Type of charge (derived from PaymentIntent.purpose)"
    )

    # Mobile money details (Cameroon)
    momo_operator = models.CharField(max_length=50, blank=True, help_text="MTN, Orange, etc.")
    momo_phone_used = models.CharField(max_length=20, blank=True, help_text="Phone number used for payment")
    transaction_id = models.CharField(max_length=255, blank=True, db_index=True, help_text="Provider transaction ID")

    # Webhook data
    raw_webhook_payload = models.JSONField(default=dict, blank=True, help_text="Raw webhook payload for debugging")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['subscription']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['charge_type']),
            models.Index(fields=['user', 'charge_type']),
        ]
        verbose_name = 'Payment Record'
        verbose_name_plural = 'Payment Records'

    def __str__(self):
        return f"{self.user.email} - {self.amount} XAF - {self.status} - {self.created_at.date()}"


class SubscriptionEventLog(models.Model):
    """
    Event logging for subscription debugging and auditing
    """
    EVENT_TYPE_CHOICES = [
        ('subscription_created', 'Subscription Created'),
        ('subscription_activated', 'Subscription Activated'),
        ('subscription_expired', 'Subscription Expired'),
        ('upgrade_initiated', 'Upgrade Initiated'),
        ('subscription_renewed', 'Subscription Renewed'),
        ('subscription_downgraded', 'Subscription Downgraded'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('trial_converted', 'Trial Converted'),
        ('payment_received', 'Payment Received'),
        ('payment_failed', 'Payment Failed'),
        ('plan_changed', 'Plan Changed'),
        ('status_changed', 'Status Changed'),
        ('grace_period_started', 'Grace Period Started'),
        ('downgrade_to_free', 'Downgrade to Free'),
        ('provisioning_success', 'Provisioning Success'),
        ('provisioning_failed', 'Provisioning Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='event_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_event_logs')

    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription']),
            models.Index(fields=['user']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Subscription Event Log'
        verbose_name_plural = 'Subscription Event Logs'

    def __str__(self):
        return f"{self.subscription.user.email} - {self.event_type} - {self.created_at}"


class SubscriptionDeadLetterQueue(models.Model):
    """
    Dead Letter Queue for failed subscription creation
    Stores failures for manual recovery via background task
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    task_type = models.CharField(max_length=100, default='subscription_creation')

    error_message = models.TextField()
    original_failure_reason = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    priority = models.CharField(max_length=20, default='critical')

    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['task_type', 'processed']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Subscription Dead Letter Queue'
        verbose_name_plural = 'Subscription Dead Letter Queue'

    def __str__(self):
        status = "Processed" if self.processed else "Pending"
        return f"DLQ {self.user_id} - {status} - {self.created_at}"