"""
Payment Models for Multi-Provider Payment System
Core models that work across all payment providers (Fapshi, MTN, Orange, Flutterwave, etc.)
Based on production-grade SaaS payment architecture with security best practices
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class PaymentIntent(models.Model):
    """
    Canonical payment object representing a requested payment
    Works across all providers and purposes (subscription, domain, theme, checkout)

    This is the SOURCE OF TRUTH for all payment states
    """

    PURPOSE_CHOICES = [
        ('subscription', 'Subscription Payment'),
        ('subscription_renewal', 'Subscription Renewal'),
        ('subscription_upgrade', 'Subscription Upgrade'),
        ('domain', 'Domain Purchase'),
        ('theme', 'Theme Purchase'),
        ('checkout', 'Store Checkout'),
        ('trial', 'Trial Subscription'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('created', 'Created'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    CURRENCY_CHOICES = [
        ('XAF', 'Central African CFA Franc'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core payment details
    # NOTE: workspace_id is optional for user-level payments (subscriptions)
    # Workspace-level payments (checkout) will have workspace_id
    workspace_id = models.CharField(max_length=100, null=True, blank=True, db_index=True, help_text="Workspace/Store ID (optional for user-level payments)")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_intents')

    # Amount in smallest currency unit (e.g., cents for USD, francs for XAF)
    amount = models.IntegerField(help_text="Amount in smallest currency unit")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='XAF')

    # Purpose and metadata
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES, db_index=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional context data")

    # Provider information
    provider_name = models.CharField(max_length=50, null=True, blank=True, db_index=True,
                                    help_text="Payment provider (fapshi, mtn, orange, etc.)")
    provider_intent_id = models.CharField(max_length=200, null=True, blank=True, unique=True,
                                         help_text="Provider's transaction ID")

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', db_index=True)

    # Idempotency
    idempotency_key = models.CharField(max_length=100, unique=True, db_index=True,
                                       help_text="Unique key to prevent duplicate payments")

    # User who initiated (for audit)
    created_by_user_id = models.IntegerField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(help_text="Payment session expires after 30 minutes (OWASP/PCI DSS)")
    completed_at = models.DateTimeField(null=True, blank=True)

    # Failure tracking
    failure_reason = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    # Retry chain tracking
    original_payment_intent_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Original PaymentIntent ID if this is a retry (for analytics and debugging)"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace_id', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['provider_intent_id']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'created_at']),  # For reconciliation queries
        ]
        verbose_name = 'Payment Intent'
        verbose_name_plural = 'Payment Intents'

    def __str__(self):
        return f"PaymentIntent {self.id} - {self.amount} {self.currency} - {self.status}"

    @property
    def is_final_state(self):
        """Check if payment is in a final state (no further updates expected)"""
        return self.status in ['success', 'failed', 'cancelled', 'refunded']

    @property
    def is_expired(self):
        """Check if payment session has expired"""
        return timezone.now() > self.expires_at and not self.is_final_state

    @property
    def amount_decimal(self):
        """Get amount as decimal (e.g., 10000 cents -> 100.00)"""
        return Decimal(self.amount) / 100

    def mark_pending(self):
        """Mark payment as pending (provider flow started)"""
        self.status = 'pending'
        self.save(update_fields=['status', 'updated_at'])

    def mark_processing(self):
        """Mark payment as processing"""
        self.status = 'processing'
        self.save(update_fields=['status', 'updated_at'])

    def mark_success(self, provider_intent_id=None):
        """Mark payment as successful"""
        self.status = 'success'
        self.completed_at = timezone.now()
        if provider_intent_id:
            self.provider_intent_id = provider_intent_id
        self.save(update_fields=['status', 'completed_at', 'provider_intent_id', 'updated_at'])

    def mark_failed(self, reason=''):
        """Mark payment as failed"""
        self.status = 'failed'
        self.failure_reason = reason
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'failure_reason', 'completed_at', 'updated_at'])

    def mark_cancelled(self, reason=''):
        """Mark payment as cancelled"""
        self.status = 'cancelled'
        self.failure_reason = reason
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'failure_reason', 'completed_at', 'updated_at'])


class MerchantPaymentMethod(models.Model):
    """
    Workspace-specific payment provider configuration

    For external redirect providers (Fapshi): Stores merchant's checkout URL
    For future API-integrated providers: Stores encrypted credentials
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Workspace association
    workspace_id = models.CharField(max_length=100, db_index=True)
    workspace_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='merchant_payment_methods')

    # Provider details
    provider_name = models.CharField(max_length=50, db_index=True,
                                    help_text="Payment provider (fapshi, mtn, orange, flutterwave)")

    # External redirect URL (for providers like Fapshi)
    checkout_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Merchant's payment checkout URL (for external redirect providers)"
    )

    # Encrypted configuration for API-integrated providers
    config_encrypted = models.TextField(
        blank=True,
        default='',
        help_text="Encrypted provider credentials (for future API-integrated providers)"
    )

    # Status
    enabled = models.BooleanField(default=False, help_text="Merchant has enabled this payment method")
    verified = models.BooleanField(default=False, help_text="URL validated or credentials verified")

    # Provider capabilities (stored as metadata)
    permissions = models.JSONField(default=dict, blank=True,
                                  help_text="What this provider supports (card, mobile-money, redirect, etc.)")

    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_transactions = models.IntegerField(default=0)
    successful_transactions = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-enabled', '-last_used_at']
        indexes = [
            models.Index(fields=['workspace_id', 'enabled']),
            models.Index(fields=['provider_name', 'enabled']),
        ]
        unique_together = [['workspace_id', 'provider_name']]  # One config per workspace per provider
        verbose_name = 'Merchant Payment Method'
        verbose_name_plural = 'Merchant Payment Methods'

    def __str__(self):
        return f"{self.workspace_id} - {self.provider_name} ({'enabled' if self.enabled else 'disabled'})"

    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_transactions == 0:
            return 0
        return round((self.successful_transactions / self.total_transactions) * 100, 2)

    def record_transaction(self, success=True):
        """Update transaction counters"""
        self.total_transactions += 1
        if success:
            self.successful_transactions += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['total_transactions', 'successful_transactions', 'last_used_at', 'updated_at'])


class TransactionLog(models.Model):
    """
    Immutable audit trail of all provider interactions
    Stores raw provider responses and webhook payloads

    Critical for:
    - Debugging payment issues
    - Compliance and auditing
    - Reconciliation
    - Fraud investigation
    """

    EVENT_TYPE_CHOICES = [
        ('payment_created', 'Payment Created'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('payment_failed', 'Payment Failed'),
        ('webhook_received', 'Webhook Received'),
        ('refund_initiated', 'Refund Initiated'),
        ('refund_completed', 'Refund Completed'),
        ('reconciliation', 'Reconciliation Check'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Associated payment intent
    payment_intent = models.ForeignKey(PaymentIntent, on_delete=models.CASCADE, related_name='transaction_logs')

    # Event details
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, db_index=True)
    provider_name = models.CharField(max_length=50)

    # Raw provider response (encrypted or access-controlled in production)
    provider_response = models.JSONField(help_text="Raw provider API response or webhook payload")

    # Status
    status = models.CharField(max_length=20, help_text="Status from provider")

    # Timing
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Request metadata
    request_metadata = models.JSONField(default=dict, blank=True,
                                       help_text="Request details (headers, IP, user agent)")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_intent', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Transaction Log'
        verbose_name_plural = 'Transaction Logs'

    def __str__(self):
        return f"TransactionLog {self.id} - {self.event_type} - {self.provider_name}"


class EventLog(models.Model):
    """
    Webhook event deduplication table
    Prevents processing the same webhook event multiple times (idempotency)

    Critical for:
    - Preventing duplicate payments
    - Webhook replay attack protection
    - Ensuring idempotency
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Provider event ID (unique from provider)
    provider_event_id = models.CharField(max_length=200, unique=True, db_index=True,
                                        help_text="Unique event ID from provider")
    provider_name = models.CharField(max_length=50)

    # Event payload
    payload = models.JSONField(help_text="Raw webhook payload")

    # Processing status
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['provider_event_id']),
            models.Index(fields=['processed', 'received_at']),
        ]
        verbose_name = 'Event Log'
        verbose_name_plural = 'Event Logs'

    def __str__(self):
        return f"EventLog {self.provider_event_id} - {self.provider_name}"

    def mark_processed(self):
        """Mark event as processed"""
        self.processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['processed', 'processed_at'])


class RefundRequest(models.Model):
    """
    Refund tracking for payment reversals
    Supports full and partial refunds
    """

    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Associated payment
    payment_intent = models.ForeignKey(PaymentIntent, on_delete=models.CASCADE, related_name='refunds')

    # Refund details
    amount = models.IntegerField(help_text="Refund amount in smallest currency unit")
    reason = models.TextField()

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested', db_index=True)

    # Provider details
    provider_refund_id = models.CharField(max_length=200, null=True, blank=True)

    # User who requested
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Failure tracking
    failure_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_intent', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
        verbose_name = 'Refund Request'
        verbose_name_plural = 'Refund Requests'

    def __str__(self):
        return f"RefundRequest {self.id} - {self.amount} - {self.status}"

    def mark_success(self, provider_refund_id=None):
        """Mark refund as successful"""
        self.status = 'success'
        self.completed_at = timezone.now()
        if provider_refund_id:
            self.provider_refund_id = provider_refund_id
        self.save(update_fields=['status', 'completed_at', 'provider_refund_id', 'updated_at'])

    def mark_failed(self, reason=''):
        """Mark refund as failed"""
        self.status = 'failed'
        self.failure_reason = reason
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'failure_reason', 'completed_at', 'updated_at'])
