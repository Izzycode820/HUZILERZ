# Core Workspace Model - Foundation for multi-tenant SaaS

import uuid
import secrets
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Workspace(models.Model):
    """
    Core Workspace Model - Central entity for multi-tenant SaaS
    Every store, company, or enterprise instance belongs to a workspace
    """
    
    WORKSPACE_TYPES = [
        ('store', 'Store'),
        ('blog', 'Blog'),
        ('services', 'Services'),
    ]
    
    STATUS_CHOICES = [
        ('provisioning', 'Provisioning'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('suspended_by_plan', 'Suspended by Plan'),  # Downgrade enforcement
        ('pending', 'Pending Approval'),
    ]

    # Compliance status for subscription downgrade enforcement
    PLAN_STATUS_CHOICES = [
        ('compliant', 'Compliant'),
        ('plan_violation', 'Plan Violation'),
        ('auto_enforced', 'Auto Enforced'),
    ]

    
    # Core identity fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Workspace display name")
    type = models.CharField(max_length=20, choices=WORKSPACE_TYPES, help_text="Workspace type determines available features")
    slug = models.SlugField(max_length=255, unique=True, help_text="URL-friendly identifier")
    description = models.TextField(blank=True, help_text="Optional workspace description")
    
    # Ownership and access
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_workspaces')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='provisioning')
    provisioning_complete = models.BooleanField(default=False, help_text="True when all background provisioning tasks complete")

    # Capabilities (merged from subscription plan + overrides)
    capabilities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Merged capability map from CapabilityEngine - runtime source of truth for features"
    )

    # Demo workspace flags
    is_demo = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this workspace is a demo workspace for theme preview"
    )
    is_admin_managed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this workspace is managed by admins (bypasses subscription limits)"
    )

    # Deletion tracking (soft delete with grace period)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When workspace was soft-deleted (status='suspended')"
    )
    deletion_scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When permanent deletion/deprovisioning will occur (deleted_at + 5 days)"
    )

    # Compliance tracking for subscription downgrade enforcement
    # Per downgrade guide: Workspace enters PLAN_VIOLATION when caps shrink below usage
    plan_status = models.CharField(
        max_length=20,
        choices=PLAN_STATUS_CHOICES,
        default='compliant',
        db_index=True,
        help_text="Compliance status: compliant, plan_violation, or auto_enforced"
    )
    violation_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of violated caps: workspaces, products, staff, domains, themes, payment"
    )
    compliance_deadline = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When auto-enforcement triggers (7 days after violation detected)"
    )
    # Stores enforcement details after auto-enforcement runs
    enforcement_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Details of what was enforced: suspended workspaces, deactivated products, etc."
    )

    # Subscription restriction flag - set when owner's subscription enters restricted status
    # When True, gating.py denies ALL new actions (create product, invite staff, etc.)
    # Different from plan_violation: restricted_mode = payment issue, plan_violation = cap exceedance
    restricted_mode = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True when owner subscription is restricted - blocks all new actions until reactivation"
    )
    restricted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When restricted_mode was enabled (for tracking reactivation eligibility)"
    )
    restricted_reason = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Reason for restriction: grace_period_expired, payment_failed, admin_action"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspaces'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['slug']),
            # Compliance enforcement queries (Celery task)
            models.Index(fields=['plan_status', 'compliance_deadline']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def clean(self):
        """
        Enterprise-grade validation following Django best practices
        Called by Django's validation system and ModelForm
        """
        super().clean()
        
        # Validate on creation and critical field changes
        if self._state.adding or self._has_critical_field_changes():
            self._validate_workspace_limits()
        
        # Validate slug uniqueness
        if self.slug and Workspace.objects.exclude(id=self.id).filter(slug=self.slug).exists():
            raise ValidationError({'slug': 'Workspace with this slug already exists.'})
    
    def save(self, *args, **kwargs):
        """
        Enterprise-grade save with comprehensive validation
        Multiple layers of protection against bypass attempts
        """
        if not self.slug:
            self.slug = self._generate_unique_slug()

        # Force validation before save (defense in depth)
        if not kwargs.pop('skip_validation', False):
            self.clean()

        # Transaction-safe workspace creation with race condition protection
        if self._state.adding:
            self._atomic_workspace_validation()

        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        """
        Generate unique slug from workspace name with random suffix if needed
        Ensures URL-safe and human-readable slugs for storefront URLs
        """
        base_slug = slugify(self.name)
        if not base_slug:
            # Fallback if name doesn't produce valid slug
            base_slug = 'workspace'

        slug = base_slug

        # Add random suffix if slug already exists
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            random_suffix = secrets.token_hex(4)
            slug = f"{base_slug}-{random_suffix}"
            counter += 1
            if counter > 10:  # Fallback after 10 attempts
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                break

        return slug

    def _has_critical_field_changes(self):
        """Check if critical fields that affect workspace limits have changed"""
        if not self.pk:
            return True
        
        try:
            original = Workspace.objects.get(pk=self.pk)
            return (
                original.owner_id != self.owner_id or
                original.status != self.status
            )
        except Workspace.DoesNotExist:
            return True
    
    def _atomic_workspace_validation(self):
        """
        Race-condition safe validation using database constraints
        ENTERPRISE SECURITY: Prevents concurrent workspace creation bypass
        """
        from django.db import transaction
        from django.core.exceptions import PermissionDenied

        # Bypass validation for admin-managed workspaces
        if self.is_admin_managed:
            return

        with transaction.atomic():
            # Lock user's subscription for atomic count verification
            try:
                subscription = (
                    self.owner.subscription.__class__.objects
                    .select_for_update()
                    .get(user=self.owner)
                )
            except:
                # No subscription = free tier (1 workspace limit)
                subscription = None
            
            # Re-validate with fresh count under lock
            # Note: Workspace limit validation moved to WorkspaceService
            # Model only performs basic security checks
            pass
    
    def _validate_workspace_limits(self):
        """
        Basic workspace validation
        Note: Subscription-based limits validated in WorkspaceService
        """
        # Rate limiting check (enterprise feature)
        self._validate_workspace_rate_limits()

        # Resource availability check (basic validation only)
        self._validate_workspace_resources()
    
    def _validate_workspace_rate_limits(self):
        """
        Enterprise rate limiting to prevent abuse
        Prevents rapid workspace creation spam attacks
        """
        from django.core.exceptions import PermissionDenied
        from django.utils import timezone
        from datetime import timedelta

        # Bypass rate limits for admin-managed workspaces
        if self.is_admin_managed:
            return

        # Check recent workspace creation frequency (max 5 workspaces per hour)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_workspaces = Workspace.objects.filter(
            owner=self.owner,
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_workspaces >= 5:
            raise PermissionDenied(
                "Workspace creation rate limit exceeded. Maximum 5 workspaces per hour. "
                "Please wait before creating additional workspaces."
            )
    
    def _validate_workspace_resources(self):
        """
        Basic resource validation
        Note: Subscription-based resource limits validated in WorkspaceService
        """
        # Bypass resource validation for admin-managed workspaces
        if self.is_admin_managed:
            return

        # Future: Add basic resource checks here (disk space, etc.)
        pass
    
    @property
    def is_active(self):
        """Check if workspace is active"""
        return self.status == 'active'
    
    @property
    def member_count(self):
        """Get total member count"""
        from workspace.core.models import Membership
        return self.memberships.filter(status=Membership.Status.ACTIVE).count()
    
    def can_user_access(self, user):
        """
        Check if user has access to this workspace
        NO OWNER BYPASS - checks membership only

        DEPRECATED: Use PermissionService.can_user_access_workspace() instead
        """
        from workspace.core.models import Membership
        return Membership.get_user_active_membership(user, self) is not None
    
    @property
    def current_tier(self):
        """
        Get current subscription tier from owner's subscription
        Always in sync - no denormalized cache
        """
        try:
            return self.owner.subscription.plan.tier
        except:
            return 'free'

    def can_deploy_sites(self):
        """Check if workspace can deploy sites based on capabilities"""
        return self.capabilities.get('deployment_allowed', False)

    def get_capabilities(self):
        """Get workspace capabilities (runtime source of truth)"""
        return self.capabilities

    def is_feature_available(self, feature_name):
        """
        Check if a specific feature is available for this workspace
        Reads from workspace.capabilities (generated from YAML)

        Args:
            feature_name: Feature key to check

        Returns:
            bool or value from capabilities
        """
        return self.capabilities.get(feature_name, False)

    def has_capability(self, capability_key):
        """
        Check if workspace has a specific capability

        Args:
            capability_key: Key from plans.yaml (e.g., 'custom_domain', 'api_access')

        Returns:
            The capability value (bool, string, int, etc.)
        """
        return self.capabilities.get(capability_key)
    
    def get_resource_usage(self):
        """Get resource usage for this workspace"""
        # This would integrate with hosting app to get actual usage
        # For now, return placeholder data
        return {
            'sites_count': getattr(self, 'deployed_sites', []).count() if hasattr(self, 'deployed_sites') else 0,
            'storage_used_mb': 0,
            'bandwidth_used_gb': 0,
        }

    def get_sync_settings(self):
        """Get sync-related settings for this workspace"""
        return {
            'auto_sync_enabled': True,
            'polling_enabled': True,
            'webhook_retries': 8,
            'polling_interval_minutes': 1,
            'sync_rate_limit_per_second': 40,  # Shopify's uniform rate limit
        }

    def get_sync_status(self):
        """Get current sync status for this workspace"""
        try:
            from workspace.sync.models import SyncEvent
            from django.utils import timezone
            from datetime import timedelta

            # Get recent sync events
            recent_cutoff = timezone.now() - timedelta(hours=1)
            recent_events = SyncEvent.objects.filter(
                workspace=self,
                created_at__gte=recent_cutoff
            )

            total = recent_events.count()
            if total == 0:
                return {'status': 'idle', 'last_sync': None}

            failed = recent_events.filter(sync_status='failed').count()
            success_rate = ((total - failed) / total) * 100

            status = 'healthy' if success_rate >= 95 else 'degraded' if success_rate >= 80 else 'unhealthy'

            return {
                'status': status,
                'success_rate': round(success_rate, 2),
                'events_last_hour': total,
                'last_sync': recent_events.first().created_at if recent_events.exists() else None
            }
        except ImportError:
            # Sync app not installed yet
            return {'status': 'unavailable', 'last_sync': None}

    # =========================================================================
    # COMPLIANCE MANAGEMENT METHODS (Downgrade Flow)
    # =========================================================================

    def mark_plan_violation(self, violation_types, grace_days=7):
        """
        Mark workspace as having plan violations with enforcement deadline.
        Called by ComplianceService when downgrade causes cap exceedance.

        Args:
            violation_types: List of violation type strings
                            (workspaces, products, staff, domains, themes, payment)
            grace_days: Days before auto-enforcement (default 7 per guide)

        Thread-safe: Uses update_fields to avoid race conditions
        """
        from django.utils import timezone
        from datetime import timedelta

        self.plan_status = 'plan_violation'
        self.violation_types = list(violation_types)
        self.compliance_deadline = timezone.now() + timedelta(days=grace_days)
        self.save(update_fields=[
            'plan_status', 'violation_types', 'compliance_deadline', 'updated_at'
        ])

    def mark_auto_enforced(self, enforcement_details):
        """
        Mark workspace as auto-enforced after grace period expires.
        Called by Celery task when compliance_deadline passes.

        Args:
            enforcement_details: Dict with enforcement actions taken.
                                Example: {'suspended_workspaces': [...], 'deactivated_products': [...]}
        """
        self.plan_status = 'auto_enforced'
        self.enforcement_metadata = enforcement_details
        self.compliance_deadline = None  # Clear deadline
        self.save(update_fields=[
            'plan_status', 'enforcement_metadata', 'compliance_deadline', 'updated_at'
        ])

    def resolve_violation(self, violation_type):
        """
        User manually resolved a violation (e.g., deleted extra workspaces).
        Removes violation type from list. If all resolved, marks compliant.

        Args:
            violation_type: String type being resolved (e.g., 'products')

        Returns:
            bool: True if all violations now resolved, False if some remain
        """
        if violation_type in self.violation_types:
            self.violation_types.remove(violation_type)

        if not self.violation_types:
            # All violations resolved - back to compliant
            self.plan_status = 'compliant'
            self.compliance_deadline = None
            self.enforcement_metadata = {}
            self.save(update_fields=[
                'plan_status', 'violation_types', 'compliance_deadline',
                'enforcement_metadata', 'updated_at'
            ])
            return True
        else:
            self.save(update_fields=['violation_types', 'updated_at'])
            return False

    def mark_compliant(self):
        """
        Reset workspace to compliant state.
        Called after upgrade or when user manually resolves all violations.
        """
        self.plan_status = 'compliant'
        self.violation_types = []
        self.compliance_deadline = None
        self.enforcement_metadata = {}
        self.save(update_fields=[
            'plan_status', 'violation_types', 'compliance_deadline',
            'enforcement_metadata', 'updated_at'
        ])

    @property
    def is_compliant(self):
        """Check if workspace is in compliant state"""
        return self.plan_status == 'compliant'

    @property
    def has_violations(self):
        """Check if workspace has any active violations"""
        return self.plan_status == 'plan_violation' and bool(self.violation_types)

    @property
    def is_enforcement_due(self):
        """Check if compliance deadline has passed (ready for auto-enforcement)"""
        if self.plan_status != 'plan_violation' or not self.compliance_deadline:
            return False
        from django.utils import timezone
        return timezone.now() >= self.compliance_deadline

    def suspend_by_plan(self, reason='downgrade_enforcement'):
        """
        Suspend workspace due to plan downgrade enforcement.
        Different from regular suspension - can be auto-reinstated on upgrade.

        Args:
            reason: Reason for suspension (stored in enforcement_metadata)
        """
        from django.utils import timezone

        self.status = 'suspended_by_plan'
        self.enforcement_metadata = self.enforcement_metadata or {}
        self.enforcement_metadata['suspension_reason'] = reason
        self.enforcement_metadata['suspended_at'] = timezone.now().isoformat()
        self.save(update_fields=['status', 'enforcement_metadata', 'updated_at'])