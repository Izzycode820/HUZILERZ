"""
Subscription-Integrated Hosting Models
Multi-tenant hosting architecture with pool infrastructure (Shopify model)
All tiers use shared infrastructure with software-level isolation
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from workspace.core.models import Workspace
from theme.models import Template


class HostingEnvironment(models.Model):
    """
    Resource quota and usage tracker per user subscription
    All users share pool infrastructure, this tracks their tier limits and current usage
    """
    STATUS_CHOICES = [
        ('initializing', 'Initializing'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('grace_period', 'Grace Period'),
        ('error', 'Error'),
    ]

    # Core identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.OneToOneField(
        'subscription.Subscription',
        on_delete=models.CASCADE,
        related_name='hosting_environment'
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosting_environment'
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initializing')
    grace_period_end = models.DateTimeField(null=True, blank=True)

    # Hosting capabilities - Source of truth from YAML (via CapabilityEngine)
    capabilities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Hosting entitlements: storage_gb, custom_domain, deployment_allowed"
    )

    # Current usage tracking
    storage_used_gb = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bandwidth_used_gb = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    active_sites_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_usage_sync = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['subscription']),
            models.Index(fields=['status', 'grace_period_end']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.subscription.plan.tier}"
    
    @property
    def is_deployment_allowed(self):
        """Check if deployment is allowed based on capabilities"""
        return self.capabilities.get('deployment_allowed', False)

    @property
    def storage_usage_percentage(self):
        """Calculate storage usage percentage"""
        storage_limit = self.capabilities.get('storage_gb', 0)
        if storage_limit == 0:
            return 0
        return float((self.storage_used_gb / Decimal(str(storage_limit))) * 100)

    def sync_limits_from_subscription(self):
        """
        Sync hosting capabilities from subscription plan
        Triggers capability provisioning task to update capabilities DB record
        """
        from workspace.hosting.tasks.hosting_capabilities import update_hosting_capabilities

        # Queue task to update capabilities from YAML via CapabilityEngine
        update_hosting_capabilities.delay(
            user_id=str(self.user.id),
            new_tier=self.subscription.plan.tier,
            event_type='manual_sync'
        )

        if self.status == 'initializing':
            self.status = 'active'
            self.save(update_fields=['status', 'updated_at'])

    def check_storage_limit(self, additional_gb=0):
        """Check if storage addition would exceed limit - uses capabilities"""
        storage_limit = self.capabilities.get('storage_gb', 0)
        if storage_limit == 0:
            return True
        return (self.storage_used_gb + Decimal(str(additional_gb))) <= Decimal(str(storage_limit))

    def increment_storage_usage(self, gb_amount):
        """Increment storage usage atomically"""
        from django.db.models import F
        HostingEnvironment.objects.filter(pk=self.pk).update(
            storage_used_gb=F('storage_used_gb') + Decimal(str(gb_amount)),
            last_usage_sync=timezone.now()
        )
        self.refresh_from_db()
    
    def check_resource_limits(self, additional_storage_gb=0):
        """Check if adding resources would exceed limits - reads from capabilities DB record"""
        # Get storage limit from capabilities (DB record)
        storage_limit = self.capabilities.get('storage_gb', 0)

        return {
            'storage_ok': (self.storage_used_gb + Decimal(str(additional_storage_gb))) <= Decimal(str(storage_limit)),
            'deployment_ok': self.is_deployment_allowed  # Already uses capabilities
        }

    def get_usage_summary(self):
        """Get current usage summary with percentages - uses capabilities"""
        storage_limit = self.capabilities.get('storage_gb', 0)
        custom_domain_allowed = self.capabilities.get('custom_domain', False)

        return {
            'storage': {
                'used_gb': float(self.storage_used_gb),
                'limit_gb': float(storage_limit),
                'percentage': float(self.storage_usage_percentage),
                'remaining_gb': float(Decimal(str(storage_limit)) - self.storage_used_gb)
            },
            'sites': {
                'active_count': self.active_sites_count,
                # No site limit - DB constraint enforces one active site per workspace
            },
            'custom_domains': {
                'allowed': custom_domain_allowed,
                'count': self.deployed_sites.filter(custom_domains__isnull=False).count()
            },
            'status': self.status,
            'deployment_allowed': self.is_deployment_allowed
        }

    def get_usage_history(self, days=30):
        """Get usage history for analytics"""
        from django.utils import timezone
        start_date = timezone.now() - timezone.timedelta(days=days)

        logs = self.usage_logs.filter(
            recorded_at__gte=start_date
        ).order_by('recorded_at').values(
            'recorded_at', 'storage_used_gb', 'bandwidth_used_gb',
            'requests_count', 'avg_response_time_ms'
        )

        return {
            'period_days': days,
            'data_points': list(logs),
            'current_usage': self.get_usage_summary()
        }

    def calculate_overage_cost(self):
        """Calculate overage costs for enterprise billing - uses capabilities"""
        overage_cost = Decimal('0.00')
        storage_limit = Decimal(str(self.capabilities.get('storage_gb', 0)))

        # Storage overage ($0.10 per GB)
        if self.storage_used_gb > storage_limit:
            overage_gb = self.storage_used_gb - storage_limit
            overage_cost += overage_gb * Decimal('0.10')

        return {
            'total_overage_usd': float(overage_cost),
            'storage_overage_gb': float(max(0, self.storage_used_gb - storage_limit))
        }


class WorkspaceInfrastructure(models.Model):
    """
    Infrastructure provisioning lifecycle for workspace.
    Tracks the provisioning state and infrastructure assignment.
    Created during workspace creation, provisions infrastructure asynchronously.

    ALL workspaces use shared POOL infrastructure with folder-based isolation.
    No tier types - single shared infrastructure model only.
    Later can be renamed to WorkspaceProvision for clarity.
    """
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('provisioning_pending', 'Provisioning Pending'),
        ('provisioning_in_progress', 'Provisioning In Progress'),
        ('provisioned', 'Provisioned'),
        ('active', 'Active'),
        ('failed', 'Failed'),
        ('degraded', 'Degraded'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.CASCADE,
        related_name='infrastructure'
    )
    # Removed tier_type - POOL is the only infrastructure model
    pool = models.ForeignKey(
        HostingEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workspace_infrastructures',
        help_text="Resource quota tracker for workspace owner"
    )
    subdomain = models.CharField(max_length=255, unique=True, db_index=True)
    preview_url = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='created')
    infra_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="CDN URLs, bucket paths, and other infrastructure details"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    # Subdomain change tracking
    subdomain_changes_count = models.IntegerField(
        default=0,
        help_text="Number of times subdomain has been changed"
    )
    subdomain_changes_limit = models.IntegerField(
        default=2,
        help_text="Maximum number of subdomain changes allowed (aligned with Shopify: 2 changes total)"
    )
    last_subdomain_change_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last subdomain change"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspace_infrastructure'
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['subdomain']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.workspace.name} - POOL Infrastructure"

    def validate_status_transition(self, new_status):
        """Validate status transition according to state machine."""
        from django.core.exceptions import ValidationError

        # Special case: failure can happen from any state
        if new_status == 'failed':
            return

        # Allowed transitions
        allowed = {
            'created': ['provisioning_pending', 'failed'],
            'provisioning_pending': ['provisioning_in_progress', 'failed'],
            'provisioning_in_progress': ['provisioned', 'failed'],
            'provisioned': ['active', 'failed'],
            'active': ['degraded', 'suspended'],
            'degraded': ['active', 'suspended'],
            'suspended': ['active'],
            'failed': ['provisioning_pending'],  # retry
        }
        current = self.status
        if current not in allowed:
            raise ValidationError(f'Current status {current} is not recognized.')
        if new_status not in allowed[current]:
            raise ValidationError(f'Transition from {current} to {new_status} is not allowed.')

    def clean(self):
        """Validate model before saving."""
        from django.core.exceptions import ValidationError
        super().clean()

        # Validate status transition if status changed
        if self.pk:
            try:
                old = WorkspaceInfrastructure.objects.get(pk=self.pk)
                if old.status != self.status:
                    self.validate_status_transition(self.status)
            except WorkspaceInfrastructure.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        """Save with validation."""
        self.clean()
        super().save(*args, **kwargs)

    def mark_active(self):
        """
        Mark infrastructure as active and ready
        Idempotent - safe to call multiple times
        """
        # Idempotent: Only update if not already active
        if self.status == 'active':
            return  # Already active, no-op

        self.status = 'active'
        self.activated_at = timezone.now()
        self.save(update_fields=['status', 'activated_at', 'updated_at'])

    def mark_failed(self):
        """Mark infrastructure provisioning as failed"""
        self.status = 'failed'
        self.save(update_fields=['status', 'updated_at'])

    def get_full_domain(self):
        """Get full domain URL"""
        return f"{self.subdomain}.huzilerz.com"

    def get_preview_url(self):
        """Get preview URL for workspace"""
        if self.preview_url:
            return self.preview_url
        return f"https://{self.subdomain}.preview.huzilerz.com"


class CustomDomain(models.Model):
    """
    Custom domain management for deployed sites
    Supports multiple custom domains per workspace with DNS verification
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('failed', 'Verification Failed'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]

    # Core identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='custom_domains',
        help_text="Workspace that owns this custom domain"
    )
    deployed_site = models.ForeignKey(
        'DeployedSite',
        on_delete=models.CASCADE,
        related_name='custom_domains',
        null=True,
        blank=True,
        help_text="Deployed site this domain points to (optional until assigned)"
    )

    # Domain configuration
    domain = models.CharField(
        max_length=255,
        unique=True,
        help_text="Custom domain (e.g., shoppings.com or www.shoppings.com)"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary domain for the deployed site (only one per site)"
    )

    # Verification
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    verification_token = models.CharField(
        max_length=64,
        unique=True,
        help_text="DNS TXT record token for domain ownership verification (_huzilerz-verify)"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When domain ownership was verified"
    )
    verification_method = models.CharField(
        max_length=20,
        choices=[('txt', 'DNS TXT Record'), ('cname', 'CNAME Record')],
        default='txt'
    )

    # SSL Configuration
    ssl_enabled = models.BooleanField(
        default=False,
        help_text="Whether SSL/TLS is enabled for this domain"
    )
    ssl_certificate_arn = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="AWS ACM certificate ARN for SSL"
    )
    ssl_provisioned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When SSL certificate was provisioned"
    )

    # DNS Configuration
    dns_records = models.JSONField(
        default=dict,
        help_text="Required DNS records for proper configuration"
    )

    # Domain Purchase Information (if purchased via platform)
    purchased_via_platform = models.BooleanField(
        default=False,
        help_text="Whether domain was purchased through Huzilerz"
    )
    registrar_domain_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Domain ID from registrar (Namecheap/GoDaddy)"
    )
    registrar_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[('namecheap', 'Namecheap'), ('godaddy', 'GoDaddy')],
        help_text="Domain registrar if purchased via platform"
    )

    # Pricing (Dual Currency: USD for registrar, FCFA for customer)
    purchase_price_usd = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Domain purchase price in USD (paid to registrar)"
    )
    purchase_price_fcfa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Domain purchase price in FCFA (charged to customer)"
    )
    renewal_price_usd = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual renewal price in USD (paid to registrar)"
    )
    renewal_price_fcfa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual renewal price in FCFA (charged to customer)"
    )
    exchange_rate_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="USD to FCFA exchange rate at time of purchase (e.g., 600.00)"
    )

    # Expiration & Renewal (Mobile Money = Manual only)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Domain expiration date"
    )
    auto_renew_enabled = models.BooleanField(
        default=False,
        help_text="Auto-renewal not supported for mobile money payments (Cameroon market)"
    )
    renewal_reminder_sent = models.BooleanField(
        default=False,
        help_text="Whether renewal reminder has been sent for current period"
    )
    last_renewal_warning_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time renewal warning was sent to user"
    )
    renewal_warning_count = models.IntegerField(
        default=0,
        help_text="Number of renewal warnings sent (reset after successful renewal)"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional domain metadata (SSL info, DNS records, etc.)"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_custom_domains'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['domain']),
            models.Index(fields=['deployed_site']),
            models.Index(fields=['verification_token']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['deployed_site', 'is_primary'],
                condition=models.Q(is_primary=True),
                name='unique_primary_domain_per_site'
            )
        ]

    def __str__(self):
        return f"{self.domain} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Generate verification token if not exists"""
        if not self.verification_token:
            self.verification_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def generate_dns_records(self):
        """
        Generate required DNS records for domain configuration
        Returns categorized by action: remove, add, update
        Matches UI display in verification flow
        """
        import dns.resolver

        target_host = f'{self.deployed_site.subdomain}.huzilerz.com' if self.deployed_site else 'huzilerz.com'

        # Records to remove (conflicting A records pointing elsewhere)
        remove_records = []

        # Records to add (new CNAME and TXT)
        add_records = []

        # Records to update (existing but wrong value)
        update_records = []

        try:
            # Check existing A records - these conflict with CNAME
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 10

            try:
                a_records = resolver.resolve(self.domain, 'A')
                for rdata in a_records:
                    remove_records.append({
                        'type': 'A',
                        'name': '@',
                        'value': str(rdata),
                    })
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass

            # Check existing CNAME - might need update if wrong value
            try:
                cname_records = resolver.resolve(self.domain, 'CNAME')
                existing_cname = str(cname_records[0].target).rstrip('.')

                if existing_cname != target_host:
                    update_records.append({
                        'type': 'CNAME',
                        'name': 'www',
                        'current_value': existing_cname,
                        'update_to': target_host,
                    })
                # If CNAME already correct, don't include it
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                # No CNAME exists, need to add
                add_records.append({
                    'type': 'CNAME',
                    'name': 'www',
                    'value': target_host,
                })

        except Exception:
            # If DNS lookup fails, assume clean slate - just show what to add
            pass

        # Always add verification TXT record (during pending state)
        if self.status == 'pending':
            add_records.append({
                'type': 'TXT',
                'name': '_huzilerz-verify',
                'value': self.verification_token,
            })

        # Always need CNAME if not already added/updated
        if not any(r['type'] == 'CNAME' for r in add_records + update_records):
            add_records.append({
                'type': 'CNAME',
                'name': 'www',
                'value': target_host,
            })

        # A record pointing to our IPs (alternative to CNAME for apex domain)
        if self.domain and not self.domain.startswith('www.'):
            add_records.append({
                'type': 'A',
                'name': '@',
                'value': '23.227.38.65',  # Your primary IP
            })

        return {
            'remove': remove_records,
            'add': add_records,
            'update': update_records
        }

    def verify_domain(self):
        """
        Verify domain ownership via DNS challenge
        This method should be called by a background task that checks DNS records
        """
        # TODO: Implement DNS verification logic using dnspython or similar
        # For now, this is a placeholder that can be implemented later
        pass

    def provision_ssl(self):
        """
        Provision SSL certificate for the domain
        This method should integrate with AWS ACM or Let's Encrypt
        """
        # TODO: Implement SSL provisioning logic
        # For now, this is a placeholder that can be implemented later
        pass

    @property
    def is_expiring_soon(self):
        """Check if domain expires within 30 days"""
        if not self.expires_at:
            return False
        return (self.expires_at - timezone.now()).days <= 30

    @property
    def days_until_expiration(self):
        """Get days until domain expiration"""
        if not self.expires_at:
            return None
        return (self.expires_at - timezone.now()).days

    def calculate_next_renewal_date(self):
        """Calculate next renewal date (30 days before expiration)"""
        if self.expires_at:
            return self.expires_at - timedelta(days=30)
        return None


class DeployedSite(models.Model):
    """
    Subscription-aware deployed sites
    Links workspace customization to hosting infrastructure
    Content (puck_data) lives in TemplateCustomization, not here
    """
    STATUS_CHOICES = [
        ('active', 'Active'),           # Live and accessible
        ('suspended', 'Suspended'),     # Suspended due to billing/limits
        ('maintenance', 'Maintenance'), # Temporary maintenance mode
        ('preview', 'Preview Only'),    # Free tier - preview only
    ]

    # Core identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='deployed_sites')
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='deployed_instances',
        null=True,
        blank=True,
        help_text="Template for this deployment (set when theme is published)"
    )
    customization = models.OneToOneField(
        'theme.TemplateCustomization',
        on_delete=models.CASCADE,
        related_name='deployed_site',
        null=True,
        blank=True,
        help_text="Active template customization (puck_data) - set when theme is published"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deployed_sites')
    hosting_environment = models.ForeignKey(
        HostingEnvironment,
        on_delete=models.CASCADE,
        related_name='deployed_sites',
        help_text="Resource quota tracker for this deployment"
    )

    # Site configuration
    site_name = models.CharField(max_length=200)
    slug = models.CharField(max_length=100)
    subdomain = models.CharField(
        max_length=100,
        unique=True,
        help_text="Auto-generated subdomain (e.g., mikes-store)"
    )
    custom_subdomain = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="User-customized subdomain (optional, takes priority over auto-generated)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preview')

    # Password Protection (Shopify pattern: "infrastructure live, business not live")
    password_protection_enabled = models.BooleanField(
        default=False,
        help_text="Enable password protection for storefront (prevents public access)"
    )
    password_hash = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Hashed password for storefront access (Django's make_password)"
    )
    password_plaintext = models.CharField(
        max_length=128,
        blank=True,
        default='',
        help_text="Plaintext password for storefront (Shopify pattern: show to merchant)"
    )
    password_description = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Message shown to visitors on password page (e.g., 'Store coming soon!')"
    )

    # SEO Configuration (Phase 4: Prerendering/SEO for headless themes)
    seo_title = models.CharField(
        max_length=60,
        blank=True,
        default='',
        help_text="SEO title for search engines (max 60 chars for Google)"
    )
    seo_description = models.TextField(
        max_length=160,
        blank=True,
        default='',
        help_text="Meta description for search results (max 160 chars)"
    )
    seo_keywords = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Comma-separated keywords (optional, less important for modern SEO)"
    )
    seo_image_url = models.URLField(
        blank=True,
        default='',
        help_text="Open Graph image for social sharing (Facebook, Twitter, WhatsApp)"
    )

    # Template runtime configuration (dev vs prod)
    template_cdn_url = models.URLField(
        blank=True,
        help_text="Production CDN URL for Next.js template (e.g., https://cdn.huzilaz.com/templates/store-modern/)"
    )
    template_dev_url = models.URLField(
        blank=True,
        default='http://localhost:3001',
        help_text="Development URL for Next.js template"
    )

    # AWS infrastructure details (DNS, SSL, CDN only - no static files)
    deployment_details = models.JSONField(
        default=dict,
        help_text="AWS infrastructure config (CloudFront, Route53, SSL certificates)"
    )

    # Resource usage (bandwidth only - no storage for static files)
    monthly_bandwidth_gb = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    monthly_requests_count = models.BigIntegerField(default=0)

    # Performance and monitoring
    last_publish = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time customization was published (role=active)"
    )
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    avg_load_time_ms = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['workspace', 'slug']
        constraints = [
            models.UniqueConstraint(
                fields=['workspace'],
                condition=models.Q(status='active'),
                name='unique_active_site_per_workspace'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['hosting_environment', 'status']),
            models.Index(fields=['subdomain']),
            models.Index(fields=['custom_subdomain']),
        ]
    
    def __init__(self, *args, **kwargs):
        """Track original status to detect publish actions"""
        super().__init__(*args, **kwargs)
        # Store original status for change detection
        self._original_status = self.status if self.pk else None

    def __str__(self):
        return f"{self.site_name} ({self.subdomain})"
    
    def clean(self):
        """
        Enterprise-grade validation following Django best practices
        Called by Django's validation system and ModelForm
        """
        super().clean()
        
        # Validate on creation and critical field changes
        if self._state.adding or self._has_critical_field_changes():
            self._validate_deployment_limits()
    
    def save(self, *args, **kwargs):
        """
        Enterprise-grade save with comprehensive validation
        Multiple layers of protection against bypass attempts
        """
        # Force validation before save (defense in depth)
        skip_validation = kwargs.pop('skip_validation', False)

        if not skip_validation:
            self.clean()

        # Transaction-safe deployment with race condition protection
        # Skip for admin-managed demos (when skip_validation=True)
        if self._state.adding and not skip_validation:
            self._atomic_deployment_validation()

        super().save(*args, **kwargs)
    
    def _has_critical_field_changes(self):
        """Check if critical fields that affect deployment limits have changed"""
        if not self.pk:
            return True

        try:
            original = DeployedSite.objects.get(pk=self.pk)
            return (
                original.user_id != self.user_id or
                original.status != self.status or
                original.hosting_environment_id != self.hosting_environment_id
            )
        except DeployedSite.DoesNotExist:
            return True
    
    def _atomic_deployment_validation(self):
        """
        Race-condition safe deployment validation
        Checks deployment_allowed capability from DB record

        IMPORTANT: Only validates when creating ACTIVE sites
        Preview sites (status='preview') are allowed for ALL users (free tier conversion optimization)

        Note: Site count limits removed - DB constraint enforces one active site per workspace
        """
        from django.db import transaction
        from django.core.exceptions import PermissionDenied

        # CRITICAL: Allow preview site creation for all users
        # Free tier users can create workspaces and preview them
        # Gate only at PUBLISH action (status='preview' → 'active')
        if self.status == 'preview':
            return  # Skip validation for preview sites

        with transaction.atomic():
            # Get user's hosting environment with capabilities
            try:
                hosting_env = HostingEnvironment.objects.select_for_update().get(user=self.user)
            except HostingEnvironment.DoesNotExist:
                raise PermissionDenied("No hosting environment found. Please contact support.")

            # Check deployment_allowed from capabilities DB record
            # Only blocks creation of ACTIVE sites (direct publish bypass attempts)
            deployment_allowed = hosting_env.capabilities.get('deployment_allowed', False)

            if not deployment_allowed and self.status == 'active':
                # Log security violation attempt (trying to bypass publish flow)
                import logging
                logger = logging.getLogger('security')
                logger.warning(
                    f"Deployment blocked: User {self.user.id} attempted to create active site "
                    f"without deployment_allowed capability (bypass attempt)"
                )

                raise PermissionDenied(
                    "Publishing requires a paid subscription (Beginner tier or higher). "
                    "Free tier is limited to preview mode only."
                )

            # Note: DB constraint unique_active_site_per_workspace (models.py:807-811)
            # automatically enforces one active site per workspace

    def _is_publishing_action(self):
        """
        Detect if this is a publish action (preview → active transition)

        Returns:
            bool: True if transitioning to active status (publishing)
        """
        return (
            self.status == 'active' and
            self._original_status in ['preview', None]  # None = first time creation as active
        )

    def _validate_deployment_limits(self):
        """
        Core deployment limit validation
        ENTERPRISE SECURITY: Multi-layer validation with comprehensive checks

        IMPORTANT: Only validates on PUBLISH action (preview → active)
        Preview infrastructure is free for all users
        """
        from django.core.exceptions import PermissionDenied, ValidationError

        # CRITICAL: Only validate when publishing (transitioning preview → active)
        # Preview infrastructure is FREE for all users (free tier can explore)
        if not self._is_publishing_action():
            return  # Skip all subscription checks for preview or status updates

        # --- GATE: Subscription required to PUBLISH ---
        # Validate user has subscription
        if not hasattr(self.user, 'subscription') or not self.user.subscription:
            raise ValidationError(
                "Publishing your site requires an active subscription. "
                "Upgrade to Beginning tier to publish your store."
            )
        
        subscription = self.user.subscription
        plan = subscription.plan
        
        # Validate subscription status
        if subscription.status not in ['active', 'grace_period']:
            raise PermissionDenied(
                f"Cannot publish site with {subscription.status} subscription. "
                f"Please renew your subscription to continue."
            )

        # Check deployment capability from hosting environment DB record
        try:
            hosting_env = self.hosting_environment or HostingEnvironment.objects.get(user=self.user)
        except HostingEnvironment.DoesNotExist:
            raise PermissionDenied("No hosting environment found. Please contact support.")

        deployment_allowed = hosting_env.capabilities.get('deployment_allowed', False)

        if not deployment_allowed:
            raise PermissionDenied(
                "Publishing requires a paid subscription (Beginner tier or higher). "
                "Free tier is limited to preview mode only."
            )
        
        # Rate limiting check (enterprise feature)
        self._validate_deployment_rate_limits()
        
        # Resource availability check
        self._validate_resource_availability()
    
    def _validate_deployment_rate_limits(self):
        """
        Enterprise rate limiting to prevent abuse
        Prevents rapid deployment spam attacks
        """
        from django.core.exceptions import PermissionDenied
        from django.utils import timezone
        from datetime import timedelta
        
        # Check recent deployment frequency (max 10 deployments per hour)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_deployments = DeployedSite.objects.filter(
            user=self.user,
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_deployments >= 10:
            raise PermissionDenied(
                "Deployment rate limit exceeded. Maximum 10 deployments per hour. "
                "Please wait before deploying additional sites."
            )
    
    def _validate_resource_availability(self):
        """
        Pool model: Resource validation handled at application level
        No per-user storage limits in shared infrastructure
        """
        # Pool infrastructure: All resource management happens at application level
        # Rate limiting, bandwidth, and storage managed by middleware and services
        pass
    
    def get_fallback_preview_url(self):
        """
        Get fallback preview URL for DNS propagation window (Critical fix #2)
        Uses central preview domain that always works while DNS propagates
        """
        return f"https://preview.huzilerz.com?workspace={self.workspace.id}"

    def is_dns_ready(self):
        """
        Check if DNS is likely propagated for this site
        DNS propagation typically takes 5-15 minutes but can take up to 48 hours
        We use a conservative 30-minute window for the fallback
        """
        from django.utils import timezone
        from datetime import timedelta

        # If site was just created (within last 30 minutes), DNS might not be ready
        if self.created_at:
            time_since_creation = timezone.now() - self.created_at
            if time_since_creation < timedelta(minutes=30):
                return False

        # If custom domain was just added, DNS might not be ready
        primary_custom = self.get_primary_custom_domain()
        if primary_custom and primary_custom.created_at:
            time_since_domain_add = timezone.now() - primary_custom.created_at
            if time_since_domain_add < timedelta(minutes=30):
                return False

        # Otherwise assume DNS is ready
        return True

    @property
    def preview_url(self):
        """
        Generate preview URL (development or production)
        Uses fallback URL during DNS propagation window to avoid "site not working" errors
        """
        from django.conf import settings

        if settings.DEBUG:
            # Development: localhost with query params
            return f"{self.template_dev_url}?workspace_id={self.workspace.id}&mode=preview"
        else:
            # Production: check if DNS is ready, use fallback if not
            if not self.is_dns_ready():
                return self.get_fallback_preview_url()

            # DNS ready: use primary domain (custom or subdomain)
            return f"https://{self.primary_domain}?mode=preview"

    @property
    def live_url(self):
        """Generate live/production URL"""
        from django.conf import settings

        if settings.DEBUG:
            # Development: localhost with query params
            return f"{self.template_dev_url}?workspace_id={self.workspace.id}&mode=live"
        else:
            # Production: use primary domain (custom or subdomain)
            return f"https://{self.primary_domain}"

    @property
    def primary_url(self):
        """Get primary site URL (defaults to live)"""
        return self.live_url

    @property
    def can_use_custom_domain(self):
        """Check if user can use custom domains - uses capabilities"""
        if not self.hosting_environment:
            return False
        return self.hosting_environment.capabilities.get('custom_domain', False)

    def get_primary_custom_domain(self):
        """Get the primary custom domain for this site"""
        try:
            return self.custom_domains.get(is_primary=True, status='active')
        except CustomDomain.DoesNotExist:
            return None

    def get_all_custom_domains(self):
        """Get all active custom domains for this site"""
        return self.custom_domains.filter(status='active').order_by('-is_primary', 'domain')

    def get_verified_domains(self):
        """Get all verified (but not necessarily active) custom domains"""
        return self.custom_domains.filter(status__in=['verified', 'active']).order_by('-is_primary', 'domain')

    @property
    def has_custom_domain(self):
        """Check if site has any active custom domains"""
        return self.custom_domains.filter(status='active').exists()

    @property
    def active_subdomain(self):
        """Get active subdomain (custom if set, otherwise auto-generated)"""
        return self.custom_subdomain or self.subdomain

    @property
    def primary_domain(self):
        """Get primary domain (custom domain if exists, otherwise subdomain)"""
        primary_custom = self.get_primary_custom_domain()
        if primary_custom:
            return primary_custom.domain
        return f"{self.active_subdomain}.huzilerz.com"

    @property
    def is_live_deployment(self):
        """Check if this is a live deployment (not preview)"""
        return self.status == 'active' and self.customization.role == 'active'
    
    def can_user_deploy(self):
        """Check if user can deploy this site"""
        # Check hosting environment exists and is active
        if not self.hosting_environment or self.hosting_environment.status not in ['active', 'grace_period']:
            return {
                'allowed': False,
                'reason': 'hosting_suspended',
                'message': 'Hosting environment is not active',
                'upgrade_required': False
            }

        # Check deployment permission from subscription
        if not self.hosting_environment.is_deployment_allowed:
            return {
                'allowed': False,
                'reason': 'deployment_not_allowed',
                'message': 'Deployment requires a paid subscription',
                'upgrade_required': True
            }

        # Check deployment capability from DB record
        if not self.hosting_environment.is_deployment_allowed:
            return {
                'allowed': False,
                'reason': 'deployment_not_allowed',
                'message': 'Deployment requires a paid subscription',
                'upgrade_required': True
            }

        # Check template ownership
        if self.template.is_owned_by_user and self.template.owned_by != self.user:
            return {
                'allowed': False,
                'reason': 'template_not_owned',
                'message': 'This template has exclusive design rights owned by another user'
            }

        return {'allowed': True}
    
    def estimate_site_size_gb(self):
        """
        Estimate bandwidth requirements (storage is template CDN, not user-specific)
        Returns expected monthly bandwidth based on site type
        """
        # No static files stored - template is on CDN
        # Only estimate bandwidth needs based on traffic
        base_bandwidth = Decimal('0.5')  # 500MB baseline monthly bandwidth

        # Adjust based on template type
        if self.template.template_type == 'ecommerce':
            base_bandwidth = Decimal('2.0')  # E-commerce = more images/products
        elif self.template.template_type in ['services', 'blog']:
            base_bandwidth = Decimal('1.0')

        return base_bandwidth
    
    def generate_deployment_config(self):
        """
        Generate deployment configuration for shared pool infrastructure
        All users use same pool infrastructure with software-level isolation
        """
        from django.conf import settings

        # Get shared pool configuration from settings
        shared_pool_config = getattr(settings, 'SHARED_POOL_CONFIG', {
            'cdn_distribution': 'shared-pool-distribution',
            'api_gateway': 'shared-api-gateway'
        })

        return {
            'workspace_id': str(self.workspace.id),
            'template_cdn_url': self.template_cdn_url or self.template.get_cdn_url(),
            'runtime_mode': 'development' if settings.DEBUG else 'production',
            'deployment_type': 'shared_pool',
            'subdomain': f"{self.subdomain}.huzilerz.com",
            'cloudfront_routing': f"/ws/{self.workspace.id}/*",
            'api_gateway': shared_pool_config.get('api_gateway'),
            'ssl_mode': 'shared_wildcard',
            'custom_domain_support': self.can_use_custom_domain
        }

    # Password Protection Methods (Shopify pattern: "infrastructure live, business not live")

    def set_password(self, raw_password: str):
        """
        Set storefront password (hashed + plaintext)

        Args:
            raw_password: Plain text password (will be hashed)

        Security:
            - Uses Django's make_password (PBKDF2 with SHA256) for verification
            - Stores plaintext for merchant display (Shopify pattern)
            - Validation happens in service layer
        """
        from django.contrib.auth.hashers import make_password

        if not raw_password:
            self.password_hash = None
            self.password_plaintext = ''
            self.password_protection_enabled = False
        else:
            self.password_hash = make_password(raw_password)
            self.password_plaintext = raw_password
            self.password_protection_enabled = True

    def check_password(self, raw_password: str) -> bool:
        """
        Verify storefront password

        Args:
            raw_password: Plain text password to check

        Returns:
            bool: True if password matches

        Security:
            - Constant-time comparison (timing attack resistant)
            - Returns False if no password set
        """
        from django.contrib.auth.hashers import check_password

        if not self.password_hash:
            return False

        return check_password(raw_password, self.password_hash)

    @property
    def requires_password(self) -> bool:
        """Check if storefront requires password for access"""
        return self.password_protection_enabled and bool(self.password_hash)


class SitePerformanceMetrics(models.Model):
    """
    Infrastructure performance metrics only
    Hosting-specific metrics (uptime, load time, resource usage)
    """
    site = models.ForeignKey(DeployedSite, on_delete=models.CASCADE, related_name='performance_metrics')
    date = models.DateField()
    
    # Infrastructure performance only
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    avg_load_time_ms = models.IntegerField(default=0)
    avg_response_time_ms = models.IntegerField(default=0)
    
    # Core web vitals (hosting performance)
    largest_contentful_paint = models.IntegerField(default=0)  # milliseconds
    first_input_delay = models.IntegerField(default=0)
    cumulative_layout_shift = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    
    # Error rates (hosting issues)
    error_rate_4xx = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    error_rate_5xx = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # CDN and caching performance
    cache_hit_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cdn_response_time_ms = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['site', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['site', '-date']),
        ]
    
    def __str__(self):
        return f"{self.site.site_name} performance - {self.date}"


class ResourceUsageLog(models.Model):
    """
    Track resource usage for billing and limit enforcement
    """
    hosting_environment = models.ForeignKey(
        HostingEnvironment,
        on_delete=models.CASCADE,
        related_name='usage_logs'
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        null=True,
        blank=True
    )
    site = models.ForeignKey(
        DeployedSite,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        null=True, blank=True
    )
    
    # Usage metrics
    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=4)
    bandwidth_used_gb = models.DecimalField(max_digits=10, decimal_places=4)
    requests_count = models.BigIntegerField(default=0)
    
    # AWS cost tracking
    estimated_cost_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Performance metrics
    avg_response_time_ms = models.IntegerField(default=0)
    error_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['hosting_environment', '-recorded_at']),
            models.Index(fields=['workspace', '-recorded_at']),
            models.Index(fields=['site', '-recorded_at']),
        ]

    def __str__(self):
        return f"Usage for {self.hosting_environment.user.email} - {self.recorded_at.date()}"


class DeploymentLog(models.Model):
    """
    Track publish/deployment actions (no build step - just publish)
    Simplified for Next.js runtime architecture
    """
    DEPLOYMENT_STATUS = [
        ('started', 'Started'),
        ('publishing', 'Publishing'),  # Setting customization to published/active
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    site = models.ForeignKey(DeployedSite, on_delete=models.CASCADE, related_name='deployment_logs')
    customization = models.ForeignKey(
        'theme.TemplateCustomization',
        on_delete=models.CASCADE,
        related_name='deployment_logs',
        null=True
    )
    status = models.CharField(max_length=20, choices=DEPLOYMENT_STATUS, default='started')

    # Deployment details
    trigger = models.CharField(
        max_length=100,
        help_text="Trigger: 'manual_publish', 'auto_publish', 'rollback', 'dns_update'"
    )
    template_version = models.CharField(max_length=50, blank=True)
    infrastructure_model = models.CharField(max_length=10)

    # Deployment actions performed
    actions_log = models.JSONField(
        default=list,
        help_text="List of actions: ['published_customization', 'updated_dns', 'invalidated_cache']"
    )
    deployment_config = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)

    # Performance tracking (publish is instant - no build)
    publish_duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time to publish customization in milliseconds"
    )

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['site', '-started_at']),
            models.Index(fields=['customization', '-started_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.site.site_name} publish - {self.status}"

    def mark_completed(self, success=True, error_message=''):
        """Mark publish as completed"""
        self.completed_at = timezone.now()
        self.status = 'success' if success else 'failed'
        if error_message:
            self.error_message = error_message

        # Calculate duration in milliseconds
        if self.started_at:
            duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
            self.publish_duration_ms = duration_ms

        self.save()


class DomainPurchase(models.Model):
    """
    Track domain purchases through the platform
    Linked to mobile money payment flow (MTN, Orange Money)
    """
    PAYMENT_STATUS = [
        ('pending', 'Pending Payment'),          # Waiting for mobile money confirmation
        ('processing', 'Processing'),            # Payment confirmed, purchasing from registrar
        ('completed', 'Completed'),              # Domain successfully purchased
        ('failed', 'Failed'),                    # Purchase failed
        ('refunded', 'Refunded'),                # Payment refunded
    ]

    # Core identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    custom_domain = models.ForeignKey(
        CustomDomain,
        on_delete=models.CASCADE,
        related_name='purchase_history',
        help_text="Domain that was purchased"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='domain_purchases'
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='domain_purchases'
    )

    # Purchase details
    domain_name = models.CharField(max_length=255, help_text="Domain purchased (e.g., mystore.com)")
    registrar = models.CharField(
        max_length=50,
        choices=[('namecheap', 'Namecheap'), ('godaddy', 'GoDaddy')],
        help_text="Registrar used for purchase"
    )
    registrar_order_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Order ID from registrar API"
    )

    # Pricing (Dual Currency)
    price_usd = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Price paid to registrar in USD"
    )
    price_fcfa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price charged to customer in FCFA"
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="USD to FCFA exchange rate at time of purchase"
    )

    # Mobile Money Payment Integration
    payment_method = models.CharField(
        max_length=50,
        default='mobile_money',
        help_text="Payment method used (mobile_money, card, etc.)"
    )
    payment_provider = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="MTN Mobile Money, Orange Money, etc."
    )
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Payment reference from mobile money provider"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )
    payment_intent = models.OneToOneField(
        'payments.PaymentIntent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='domain_purchase',
        help_text="Linked payment intent for this purchase"
    )

    # Domain registration details
    registration_period_years = models.IntegerField(
        default=1,
        help_text="Domain registration period in years"
    )
    registered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When domain was successfully registered"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Domain expiration date after this purchase"
    )

    # Contact information for WHOIS
    contact_info = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contact information for domain registration (WHOIS)"
    )

    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="Error message if purchase failed"
    )
    registrar_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full response from registrar API"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['custom_domain', '-created_at']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['payment_reference']),
        ]

    def __str__(self):
        return f"{self.domain_name} - {self.get_payment_status_display()}"

    def mark_payment_received(self, payment_reference):
        """Mark payment as received from mobile money webhook"""
        self.payment_reference = payment_reference
        self.payment_status = 'processing'
        self.save(update_fields=['payment_reference', 'payment_status', 'updated_at'])

    def mark_completed(self, registrar_order_id, expires_at):
        """Mark purchase as completed"""
        self.payment_status = 'completed'
        self.registrar_order_id = registrar_order_id
        self.registered_at = timezone.now()
        self.expires_at = expires_at
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error_message):
        """Mark purchase as failed"""
        self.payment_status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()


class DomainRenewal(models.Model):
    """
    Track domain renewal attempts and history
    Mobile Money payment flow (manual renewal only)
    """
    RENEWAL_STATUS = [
        ('pending_payment', 'Pending Payment'),  # Waiting for user to pay
        ('payment_received', 'Payment Received'), # Payment confirmed
        ('processing', 'Processing Renewal'),     # Renewing with registrar
        ('completed', 'Completed'),               # Successfully renewed
        ('failed', 'Failed'),                     # Renewal failed
        ('expired', 'Expired - Not Renewed'),     # User didn't renew, domain expired
    ]

    # Core identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    custom_domain = models.ForeignKey(
        CustomDomain,
        on_delete=models.CASCADE,
        related_name='renewal_history'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='domain_renewals'
    )

    # Renewal details
    domain_name = models.CharField(max_length=255)
    registrar = models.CharField(max_length=50)
    registrar_renewal_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Renewal transaction ID from registrar"
    )

    # Pricing (Dual Currency)
    renewal_price_usd = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Renewal price in USD (paid to registrar)"
    )
    renewal_price_fcfa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Renewal price in FCFA (charged to customer)"
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="USD to FCFA exchange rate at time of renewal"
    )

    # Mobile Money Payment
    payment_method = models.CharField(max_length=50, default='mobile_money')
    payment_provider = models.CharField(max_length=50, blank=True, null=True)
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )
    payment_intent = models.OneToOneField(
        'payments.PaymentIntent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='domain_renewal',
        help_text="Linked payment intent for this renewal"
    )
    renewal_status = models.CharField(
        max_length=20,
        choices=RENEWAL_STATUS,
        default='pending_payment'
    )

    # Renewal period
    renewal_period_years = models.IntegerField(default=1)
    previous_expiry_date = models.DateTimeField(
        help_text="Domain expiry date before renewal"
    )
    new_expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="New expiry date after renewal"
    )

    # Warning tracking
    warning_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When renewal warning was sent to user"
    )
    days_before_expiry_warned = models.IntegerField(
        null=True,
        blank=True,
        help_text="How many days before expiry the warning was sent (30, 15, 7, 1)"
    )

    # Error tracking
    error_message = models.TextField(blank=True)
    registrar_response = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    renewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['custom_domain', '-created_at']),
            models.Index(fields=['renewal_status']),
            models.Index(fields=['previous_expiry_date']),
        ]

    def __str__(self):
        return f"{self.domain_name} renewal - {self.get_renewal_status_display()}"

    def mark_payment_received(self, payment_reference):
        """Mark renewal payment as received"""
        self.payment_reference = payment_reference
        self.renewal_status = 'processing'
        self.save(update_fields=['payment_reference', 'renewal_status', 'updated_at'])

    def mark_completed(self, registrar_renewal_id, new_expiry_date):
        """Mark renewal as completed"""
        self.renewal_status = 'completed'
        self.registrar_renewal_id = registrar_renewal_id
        self.new_expiry_date = new_expiry_date
        self.renewed_at = timezone.now()
        self.save()

    def mark_failed(self, error_message):
        """Mark renewal as failed"""
        self.renewal_status = 'failed'
        self.error_message = error_message
        self.save()

    def mark_expired(self):
        """Mark as expired (user didn't renew in time)"""
        self.renewal_status = 'expired'
        self.save()


class SubdomainHistory(models.Model):
    """
    Track subdomain usage history

    Prevents subdomain reuse for SEO protection, security, and brand protection.
    Critical for production: once a subdomain is used, it's permanently reserved.
    """

    # Core identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='subdomain_history',
        help_text="Workspace that used this subdomain"
    )

    # Subdomain details
    subdomain = models.CharField(
        max_length=63,
        db_index=True,
        help_text="The subdomain that was used (without .huzilerz.com)"
    )

    # Usage period
    used_from = models.DateTimeField(
        auto_now_add=True,
        help_text="When this subdomain was assigned to the workspace"
    )
    used_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When workspace changed from this subdomain (null if still active)"
    )

    # Change metadata
    change_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional reason for subdomain change (e.g., rebranding, typo fix)"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subdomain_changes',
        help_text="User who initiated the change"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subdomain_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subdomain']),
            models.Index(fields=['workspace', '-created_at']),
            models.Index(fields=['used_from', 'used_until']),
        ]
        verbose_name = 'Subdomain History'
        verbose_name_plural = 'Subdomain Histories'

    def __str__(self):
        status = "active" if self.used_until is None else f"until {self.used_until.strftime('%Y-%m-%d')}"
        return f"{self.subdomain} - {self.workspace.name} ({status})"

    @property
    def is_active(self):
        """Check if this subdomain is still active for the workspace"""
        return self.used_until is None

    def mark_changed(self, changed_by=None, reason=''):
        """Mark this subdomain as no longer active"""
        self.used_until = timezone.now()
        self.changed_by = changed_by
        if reason:
            self.change_reason = reason
        self.save(update_fields=['used_until', 'changed_by', 'change_reason'])


class DeploymentAudit(models.Model):
    """
    Audit trail for site deployments (theme publishes)
    Tracks history of theme activations for rollback capability
    """
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deployed_site = models.ForeignKey(
        DeployedSite,
        on_delete=models.CASCADE,
        related_name='deployment_audits'
    )
    previous_customization = models.ForeignKey(
        'theme.TemplateCustomization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_deployments',
        help_text="Previous theme customization before this deployment"
    )
    new_customization = models.ForeignKey(
        'theme.TemplateCustomization',
        on_delete=models.CASCADE,
        related_name='new_deployments',
        help_text="New theme customization deployed"
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='initiated_deployments'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    error_message = models.TextField(null=True, blank=True)

    # Deployment metadata
    deployment_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="CDN invalidation details, health check results, etc."
    )

    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    rolled_back_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'deployment_audit'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['deployed_site', 'status']),
            models.Index(fields=['initiated_by', 'initiated_at']),
            models.Index(fields=['status', 'initiated_at']),
        ]

    def __str__(self):
        return f"Deployment {self.deployed_site.workspace.name} - {self.status}"

    def mark_in_progress(self):
        """Mark deployment as in progress"""
        self.status = 'in_progress'
        self.save(update_fields=['status'])

    def mark_completed(self, metadata=None):
        """Mark deployment as successfully completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if metadata:
            self.deployment_metadata.update(metadata)
        self.save(update_fields=['status', 'completed_at', 'deployment_metadata'])

    def mark_failed(self, error_message, metadata=None):
        """Mark deployment as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        if metadata:
            self.deployment_metadata.update(metadata)
        self.save(update_fields=['status', 'error_message', 'completed_at', 'deployment_metadata'])

    def mark_rolled_back(self):
        """Mark deployment as rolled back"""
        self.status = 'rolled_back'
        self.rolled_back_at = timezone.now()
        self.save(update_fields=['status', 'rolled_back_at'])