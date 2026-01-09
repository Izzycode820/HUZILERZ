# Customer Model - Shared customer management for all workspace types
# Phone-first approach optimized for Cameroonian market

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.conf import settings
from workspace.core.models.base_models import TenantScopedModel
from django.contrib.auth import get_user_model

User = get_user_model()


class Customer(TenantScopedModel):
    """
    Shared customer model for all workspace types
    Phone-first approach for Cameroonian market (MTN, Orange Mobile Money)

    Engineering Principles Applied:
    - Performance: Optimized phone number queries and indexing
    - Scalability: Phone-based customer identification across workspaces
    - Maintainability: Clear customer lifecycle management
    - Security: Phone verification patterns and data validation
    - Simplicity: Phone-first UX patterns for African market
    - Production-Ready: Customer data consistency across workspaces
    """

    # PHONE-FIRST IDENTIFICATION (Primary for Cameroon market)
    phone = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message="Phone number must be in E.164 format"
            )
        ],
        help_text="Primary customer identifier (MTN/Orange Mobile Money)"
    )

    # CUSTOMER PROFILE
    name = models.CharField(max_length=255, help_text="Customer full name")
    email = models.EmailField(blank=True, help_text="Customer email (optional)")

    # CUSTOMER SEGMENTATION
    customer_type = models.CharField(
        max_length=20,
        choices=[
            ('student', 'Student'),
            ('business', 'Small Business'),
            ('individual', 'Individual'),
            ('corporate', 'Corporate')
        ],
        default='individual',
        help_text="Customer type for segmentation"
    )

    # LOCATION DATA (Cameroon-specific)
    city = models.CharField(max_length=100, blank=True, help_text="Customer city")
    region = models.CharField(
        max_length=50,
        choices=[
            ('littoral', 'Littoral'),
            ('centre', 'Centre'),
            ('sud', 'South'),
            ('nord', 'North'),
            ('extreme-nord', 'Extreme North'),
            ('est', 'East'),
            ('ouest', 'West'),
            ('nord-ouest', 'North West'),
            ('sud-ouest', 'South West'),
            ('adamawa', 'Adamawa')
        ],
        blank=True,
        help_text="Cameroon region"
    )

    # ADDRESS (Street/physical address)
    address = models.TextField(
        blank=True,
        help_text="Customer street/physical address"
    )

    # BUSINESS ANALYTICS
    total_orders = models.PositiveIntegerField(default=0, help_text="Total orders across all workspaces")
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total amount spent across all workspaces"
    )
    first_order_at = models.DateTimeField(null=True, blank=True, help_text="First order date")
    last_order_at = models.DateTimeField(null=True, blank=True, help_text="Last order date")

    # CUSTOMER SEGMENTATION
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Customer tags for segmentation ['vip', 'wholesale', 'frequent', 'student']"
    )

    # COMMUNICATION PREFERENCES
    sms_notifications = models.BooleanField(default=True, help_text="Opt-in for SMS notifications")
    whatsapp_notifications = models.BooleanField(default=True, help_text="Opt-in for WhatsApp notifications")

    # CUSTOMER STATUS
    is_active = models.BooleanField(default=True, help_text="Whether customer is active")
    verified_at = models.DateTimeField(null=True, blank=True, help_text="When customer was verified")

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_customers'
        indexes = [
            models.Index(fields=['workspace', 'phone']),
            models.Index(fields=['workspace', 'customer_type']),
            models.Index(fields=['workspace', 'region']),
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['phone']),
            models.Index(fields=['total_spent']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.workspace.name}"

    # BUSINESS LOGIC PROPERTIES
    @property
    def is_verified(self):
        """Check if customer is verified"""
        return self.verified_at is not None

    @property
    def average_order_value(self):
        """Calculate average order value"""
        from decimal import Decimal
        if self.total_orders == 0:
            return Decimal('0.00')
        return self.total_spent / self.total_orders

    @property
    def lifetime_value(self):
        """Get customer lifetime value"""
        return self.total_spent

    @property
    def has_email(self):
        """Check if customer has email"""
        return bool(self.email)

    @property
    def is_high_value(self):
        """Check if customer is high value"""
        return self.total_spent > 100000  # 100k FCFA threshold

    @property
    def is_frequent_buyer(self):
        """Check if customer is frequent buyer"""
        return self.total_orders >= 3

    def add_tag(self, tag):
        """Add tag to customer"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save(update_fields=['tags'])

    def remove_tag(self, tag):
        """Remove tag from customer"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save(update_fields=['tags'])

    def update_order_stats(self, order_amount):
        """Update customer order statistics"""
        from django.utils import timezone

        self.total_orders += 1
        self.total_spent += order_amount

        # Update timestamps
        now = timezone.now()
        if not self.first_order_at:
            self.first_order_at = now
        self.last_order_at = now

        self.save(update_fields=[
            'total_orders',
            'total_spent',
            'first_order_at',
            'last_order_at'
        ])

    def mark_verified(self):
        """Mark customer as verified"""
        from django.utils import timezone

        self.verified_at = timezone.now()
        self.save(update_fields=['verified_at'])

    def format_phone_for_display(self):
        """Format phone number for display"""
        # Cameroon phone format: +237 6XX XXX XXX
        if self.phone.startswith('+237'):
            return f"{self.phone[:4]} {self.phone[4:7]} {self.phone[7:10]} {self.phone[10:]}"
        return self.phone

    def get_carrier(self):
        """Detect mobile carrier from phone number"""
        if self.phone.startswith('+2376'):
            return 'mtn'
        elif self.phone.startswith('+2377'):
            return 'orange'
        return 'unknown'

    def has_account(self):
        """Check if customer has authentication credentials"""
        return hasattr(self, 'auth') and self.auth is not None


class CustomerService:
    """
    Service class for customer operations
    Phone-first customer lookup and creation
    """

    @staticmethod
    def get_or_create_customer_by_phone(workspace, phone, name=None, **kwargs):
        """
        Phone-first customer lookup/creation
        Primary method for customer identification in Cameroon market
        """
        # Normalize phone number
        normalized_phone = CustomerService.normalize_phone(phone)

        try:
            customer = Customer.objects.get(
                workspace=workspace,
                phone=normalized_phone
            )
            created = False
        except Customer.DoesNotExist:
            # Ensure tags has a default value to avoid validation error
            if 'tags' not in kwargs:
                kwargs['tags'] = []
            
            customer = Customer.objects.create(
                workspace=workspace,
                phone=normalized_phone,
                name=name or 'Customer',
                **kwargs
            )
            created = True

        return customer, created

    @staticmethod
    def normalize_phone(phone):
        """Normalize phone number to E.164 format"""
        import re

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)

        # Handle Cameroon numbers
        if digits.startswith('6') or digits.startswith('7'):
            # Assume Cameroon number, add +237 prefix
            return f"+237{digits}"
        elif digits.startswith('237'):
            # Already has country code, add +
            return f"+{digits}"
        else:
            # Return as-is, assume international format
            return f"+{digits}"

    @staticmethod
    def find_customers_by_workspace(workspace, **filters):
        """Find customers by workspace with optional filters"""
        queryset = Customer.objects.filter(workspace=workspace, is_active=True)

        if 'customer_type' in filters:
            queryset = queryset.filter(customer_type=filters['customer_type'])

        if 'region' in filters:
            queryset = queryset.filter(region=filters['region'])

        if 'tags' in filters:
            queryset = queryset.filter(tags__contains=filters['tags'])

        return queryset

    @staticmethod
    def get_customer_analytics(workspace):
        """Get customer analytics for workspace"""
        customers = Customer.objects.filter(workspace=workspace, is_active=True)

        return {
            'total_customers': customers.count(),
            'total_revenue': sum(c.total_spent for c in customers),
            'average_order_value': sum(c.average_order_value for c in customers) / customers.count() if customers.count() > 0 else 0,
            'high_value_customers': customers.filter(total_spent__gt=100000).count(),
            'frequent_buyers': customers.filter(total_orders__gte=3).count(),
            'customer_regions': dict(customers.values_list('region').annotate(count=models.Count('id'))),
            'customer_types': dict(customers.values_list('customer_type').annotate(count=models.Count('id')))
        }


class CustomerAuth(models.Model):
    """
    Optional authentication for customers who create accounts

    Separation of Concerns:
    - Customer model: Core customer data (always exists)
    - CustomerAuth model: Authentication credentials (optional)

    Use Cases:
    - Admin creates customer → No auth (customer can later claim account)
    - Guest checkout → No auth (customer can later create account)
    - Customer signup → Creates auth (password, verification)
    - Customer login → Uses auth (password verification)

    Shopify Pattern:
    This follows Shopify's architecture where customers can exist without
    authentication, and later "claim" their account by creating credentials.
    """

    # One-to-one relationship with Customer
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name='auth',
        help_text="Customer this authentication belongs to"
    )

    # Authentication Credentials
    password = models.CharField(
        max_length=128,
        help_text="Hashed password using Django's make_password()"
    )

    # Email Verification (Important for password reset)
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether customer's email has been verified"
    )
    email_verification_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="Token for email verification"
    )
    email_verification_expires = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When email verification token expires"
    )

    # Password Reset
    password_reset_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="Token for password reset"
    )
    password_reset_expires = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When password reset token expires"
    )

    # Activity Tracking
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful login timestamp"
    )
    login_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Failed login attempts (for security)"
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Account locked until this time (after multiple failed attempts)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'customer_auth'
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['email_verification_token']),
            models.Index(fields=['password_reset_token']),
        ]

    def __str__(self):
        return f"Auth for {self.customer.name} ({self.customer.phone})"

    def set_password(self, raw_password):
        """Hash and set password"""
        self.password = make_password(raw_password)
        self.save(update_fields=['password'])

    def check_password(self, raw_password):
        """Verify password"""
        return check_password(raw_password, self.password)

    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def record_failed_login(self):
        """Record a failed login attempt and lock account if needed"""
        self.login_attempts += 1

        # Lock account after 5 failed attempts for 30 minutes
        if self.login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)

        self.save(update_fields=['login_attempts', 'locked_until'])

    def record_successful_login(self):
        """Record successful login and reset failed attempts"""
        self.last_login = timezone.now()
        self.login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['last_login', 'login_attempts', 'locked_until'])

    def generate_verification_token(self):
        """Generate email verification token"""
        import secrets
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_expires = timezone.now() + timezone.timedelta(hours=24)
        self.save(update_fields=['email_verification_token', 'email_verification_expires'])
        return self.email_verification_token

    def verify_email(self, token):
        """Verify email with token"""
        if (self.email_verification_token == token and
            self.email_verification_expires and
            self.email_verification_expires > timezone.now()):
            self.email_verified = True
            self.email_verification_token = ''
            self.email_verification_expires = None
            self.save(update_fields=['email_verified', 'email_verification_token', 'email_verification_expires'])
            return True
        return False

    def generate_password_reset_token(self):
        """Generate password reset token"""
        import secrets
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = timezone.now() + timezone.timedelta(hours=1)
        self.save(update_fields=['password_reset_token', 'password_reset_expires'])
        return self.password_reset_token

    def reset_password(self, token, new_password):
        """Reset password with token"""
        if (self.password_reset_token == token and
            self.password_reset_expires and
            self.password_reset_expires > timezone.now()):
            self.set_password(new_password)
            self.password_reset_token = ''
            self.password_reset_expires = None
            self.login_attempts = 0
            self.locked_until = None
            self.save(update_fields=['password_reset_token', 'password_reset_expires', 'login_attempts', 'locked_until'])
            return True
        return False


class CustomerHistory(TenantScopedModel):
    """
    Customer History/Timeline Model
    Tracks all events and interactions in the customer lifecycle.

    Events:
    - Commerce: Order placed, paid, refunded, etc.
    - Lifecycle: Created, updated, verified.
    - Staff: Notes, tags, manual updates.
    - Marketing: Subscribed, unsubscribed, campaign emails.

    Engineering Principles:
    - Immutability: History records should generally not be modified.
    - Performance: Indexed for efficient timeline retrieval.
    - Auditability: Tracks 'performed_by' for staff actions.
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Customer this history entry belongs to"
    )

    # ACTION CLASSIFICATION
    # Standardizing actions to allow for easy filtering and icons in UI
    action = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Type of action (e.g., 'order_placed', 'note_added')"
    )

    # EVENT DETAILS
    # Structured JSON data to store context-specific info (e.g., order_id, amounts, old/new values)
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured event details"
    )

    # ACTOR (Who performed the action)
    # Can be a user (staff) or system (None) or customer (if self-service)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_history_actions',
        help_text="User who performed the action (if applicable)"
    )

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_customer_history'
        ordering = ['-created_at']  # Latest first default
        indexes = [
            models.Index(fields=['workspace', 'customer', '-created_at']),  # Optimize timeline queries
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.customer.name} - {self.action} - {self.created_at}"

    def get_display_message(self):
        """
        Generate human-readable message for timeline display
        """
        # Parse action types (handles namespaces like 'commerce:order_placed' or simple 'order_placed')
        action_type = self.action.split(':')[-1] if ':' in self.action else self.action
        
        details = self.details or {}
        
        action_messages = {
            # Lifecycle
            'created': f"Customer created",
            'updated': f"Profile updated",
            'verified': "Customer verified",
            
            # Commerce
            'order_placed': f"Placed Order #{details.get('order_number', '')} - {details.get('total_price', '')}",
            'order_status_updated': f"Order #{details.get('order_number', '')} is {details.get('new_status', 'updated')}",
            'order_paid': f"Order #{details.get('order_number', '')} marked as paid",
            
            # Marketing
            'subscribed': "Subscribed to marketing",
            'unsubscribed': "Unsubscribed from marketing",
            
            # Staff
            'note_added': "Note added",
            'tag_added': f"Added tag '{details.get('tag', '')}'",
            'tag_removed': f"Removed tag '{details.get('tag', '')}'",
        }

        # Fallback to formatting the action slug if not found
        return action_messages.get(action_type, action_type.replace('_', ' ').capitalize())

