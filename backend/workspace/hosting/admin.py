"""
Django Admin Configuration for Hosting Module

Comprehensive admin interface for managing:
- Hosting environments and resource quotas
- Infrastructure provisioning and deployments
- Custom domains and SSL certificates
- Usage metrics and performance monitoring
- Deployment audits and rollback history
"""
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse, path
from django.shortcuts import render
from django.utils import timezone
from django.db import models as db_models
from django.db.models import Count, Sum, Avg, Q, F
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse, JsonResponse
import csv
from datetime import timedelta

from .models import (
    HostingEnvironment,
    WorkspaceInfrastructure,
    DeployedSite,
    DeploymentAudit,
    CustomDomain,
    DomainPurchase,
    DomainRenewal,
    SubdomainHistory,
    ResourceUsageLog,
    DeploymentLog,
    SitePerformanceMetrics,
)


# Custom Filters

class SubscriptionTierFilter(SimpleListFilter):
    title = 'subscription tier'
    parameter_name = 'tier'

    def lookups(self, request, model_admin):
        return [
            ('free', 'Free'),
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('business', 'Business'),
            ('enterprise', 'Enterprise'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(subscription__plan__tier=self.value())
        return queryset


class ResourceUsageFilter(SimpleListFilter):
    """
    Filter hosting environments by storage usage percentage.
    Uses Python-level filtering since storage limit is in JSON capabilities field.
    """
    title = 'resource usage'
    parameter_name = 'usage'

    def lookups(self, request, model_admin):
        return [
            ('low', 'Low (< 25%)'),
            ('medium', 'Medium (25-75%)'),
            ('high', 'High (75-95%)'),
            ('critical', 'Critical (> 95%)'),
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        
        # Filter by usage percentage (calculated from capabilities JSON)
        filtered_ids = []
        for env in queryset:
            storage_limit = env.capabilities.get('storage_gb', 0)
            if storage_limit == 0:
                percentage = 0
            else:
                percentage = float(env.storage_used_gb / storage_limit) * 100
            
            if self.value() == 'low' and percentage < 25:
                filtered_ids.append(env.pk)
            elif self.value() == 'medium' and 25 <= percentage < 75:
                filtered_ids.append(env.pk)
            elif self.value() == 'high' and 75 <= percentage < 95:
                filtered_ids.append(env.pk)
            elif self.value() == 'critical' and percentage >= 95:
                filtered_ids.append(env.pk)
        
        return queryset.filter(pk__in=filtered_ids)


class ProvisioningStatusFilter(SimpleListFilter):
    title = 'provisioning status'
    parameter_name = 'provision_status'

    def lookups(self, request, model_admin):
        return [
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status__icontains=self.value())
        return queryset


# Inline Admins

class DeployedSiteInline(admin.TabularInline):
    model = DeployedSite
    extra = 0
    readonly_fields = ('site_name', 'subdomain', 'status', 'created_at')
    fields = ('site_name', 'subdomain', 'status', 'created_at')
    can_delete = False
    show_change_link = True
    max_num = 5

    def has_add_permission(self, request, obj=None):
        return False


class CustomDomainInline(admin.TabularInline):
    model = CustomDomain
    extra = 0
    readonly_fields = ('domain', 'status', 'verified_at')
    fields = ('domain', 'status', 'verified_at')
    can_delete = False
    show_change_link = True


class DeploymentAuditInline(admin.TabularInline):
    model = DeploymentAudit
    extra = 0
    readonly_fields = ('status', 'initiated_by', 'initiated_at', 'completed_at')
    fields = ('status', 'initiated_by', 'initiated_at', 'completed_at')
    can_delete = False
    show_change_link = True
    ordering = ('-initiated_at',)
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


class ResourceUsageLogInline(admin.TabularInline):
    model = ResourceUsageLog
    extra = 0
    readonly_fields = ('recorded_at', 'storage_used_gb', 'bandwidth_used_gb')
    fields = ('recorded_at', 'storage_used_gb', 'bandwidth_used_gb')
    can_delete = False
    ordering = ('-recorded_at',)
    max_num = 5

    def has_add_permission(self, request, obj=None):
        return False


class SubdomainHistoryInline(admin.TabularInline):
    model = SubdomainHistory
    extra = 0
    readonly_fields = ('subdomain', 'used_from', 'used_until', 'changed_by')
    fields = ('subdomain', 'used_from', 'used_until', 'changed_by')
    can_delete = False
    ordering = ('-used_from',)
    max_num = 5

    def has_add_permission(self, request, obj=None):
        return False


# Model Admins

@admin.register(HostingEnvironment)
class HostingEnvironmentAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'subscription_tier',
        'status_badge',
        'storage_usage_display',
        'sites_count_display',
        'deployment_allowed_badge',
        'last_usage_sync',
    )
    list_filter = (
        'status',
        SubscriptionTierFilter,
        ResourceUsageFilter,
        'last_usage_sync',
    )
    search_fields = ('user__email', 'user__username', 'subscription__plan__name')
    readonly_fields = (
        'id',
        'user',
        'subscription',
        'created_at',
        'updated_at',
        'usage_summary_display',
        'storage_progress_bar',
    )
    fieldsets = (
        ('Identity', {
            'fields': ('id', 'user', 'subscription')
        }),
        ('Status', {
            'fields': ('status', 'grace_period_end', 'last_usage_sync')
        }),
        ('Capabilities', {
            'fields': ('capabilities',)
        }),
        ('Current Usage', {
            'fields': (
                'storage_used_gb',
                'storage_progress_bar',
                'active_sites_count',
            )
        }),
        ('Usage Summary', {
            'fields': ('usage_summary_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [DeployedSiteInline, ResourceUsageLogInline]
    actions = ['sync_limits_from_subscription', 'reset_usage', 'export_usage_csv']

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance"""
        return super().get_queryset(request).select_related(
            'user', 'subscription', 'subscription__plan'
        )

    def changelist_view(self, request, extra_context=None):
        """Add dashboard metrics to the changelist view"""
        extra_context = extra_context or {}
        qs = self.get_queryset(request)
        
        # Calculate tier breakdown
        tier_breakdown = {}
        for tier in ['free', 'starter', 'professional', 'business', 'enterprise']:
            tier_breakdown[tier] = qs.filter(subscription__plan__tier=tier).count()
        
        extra_context['dashboard_metrics'] = {
            'total_environments': qs.count(),
            'status_breakdown': {
                'active': qs.filter(status='active').count(),
                'suspended': qs.filter(status='suspended').count(),
                'grace_period': qs.filter(status='grace_period').count(),
                'initializing': qs.filter(status='initializing').count(),
                'error': qs.filter(status='error').count(),
            },
            'tier_breakdown': tier_breakdown,
            'deployment_enabled': qs.filter(capabilities__deployment_allowed=True).count(),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def subscription_tier(self, obj):
        if obj.subscription:
            return obj.subscription.plan.tier.upper()
        return 'NO PLAN'
    subscription_tier.short_description = 'Tier'
    subscription_tier.admin_order_field = 'subscription__plan__tier'

    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'suspended': 'red',
            'grace_period': 'orange',
            'error': 'red',
            'initializing': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def storage_usage_display(self, obj):
        percentage = obj.storage_usage_percentage
        storage_limit = obj.capabilities.get('storage_gb', 0)
        color = 'green' if percentage < 75 else ('orange' if percentage < 95 else 'red')
        # Pre-format numbers for format_html (Django 6.0 compliance)
        pct_str = f"{percentage:.1f}"
        used_str = f"{float(obj.storage_used_gb):.2f}"
        limit_str = f"{float(storage_limit):.2f}"
        return format_html(
            '{}% <span style="color: {};">({}/ {} GB)</span>',
            pct_str, color, used_str, limit_str
        )
    storage_usage_display.short_description = 'Storage'

    def sites_count_display(self, obj):
        # No site limit - DB constraint enforces one active site per workspace
        return f"{obj.active_sites_count}"
    sites_count_display.short_description = 'Active Sites'

    def deployment_allowed_badge(self, obj):
        allowed = obj.is_deployment_allowed
        color = 'green' if allowed else 'red'
        text = 'YES' if allowed else 'NO'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, text
        )
    deployment_allowed_badge.short_description = 'Can Deploy'

    def storage_progress_bar(self, obj):
        percentage = obj.storage_usage_percentage
        color = 'green' if percentage < 75 else ('orange' if percentage < 95 else 'red')
        return format_html(
            '<div style="width: 200px; background-color: #f0f0f0; border-radius: 5px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 5px; '
            'text-align: center; color: white; font-weight: bold;">{:.1f}%</div></div>',
            min(percentage, 100), color, percentage
        )
    storage_progress_bar.short_description = 'Storage Usage'

    def usage_summary_display(self, obj):
        summary = obj.get_usage_summary()
        return format_html(
            '<pre>{}</pre>',
            str(summary)
        )
    usage_summary_display.short_description = 'Usage Summary JSON'

    def sync_limits_from_subscription(self, request, queryset):
        count = 0
        for env in queryset:
            env.sync_limits_from_subscription()
            count += 1
        self.message_user(request, f'Successfully synced limits for {count} hosting environments.')
    sync_limits_from_subscription.short_description = 'Sync limits from subscription'

    def reset_usage(self, request, queryset):
        count = queryset.update(
            storage_used_gb=0,
            bandwidth_used_gb=0,
            last_usage_sync=timezone.now()
        )
        self.message_user(request, f'Reset usage for {count} hosting environments.')
    reset_usage.short_description = 'Reset usage counters (DANGEROUS)'

    def export_usage_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="hosting_usage.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'User Email', 'Tier', 'Status', 'Storage Used (GB)', 'Storage Limit (GB)',
            'Active Sites', 'Deployment Allowed', 'Custom Domain Allowed'
        ])

        for env in queryset:
            storage_limit = env.capabilities.get('storage_gb', 0)
            deployment_allowed = env.capabilities.get('deployment_allowed', False)
            custom_domain_allowed = env.capabilities.get('custom_domain', False)

            writer.writerow([
                env.user.email,
                env.subscription.plan.tier if env.subscription else 'N/A',
                env.status,
                env.storage_used_gb,
                storage_limit,
                env.active_sites_count,
                'Yes' if deployment_allowed else 'No',
                'Yes' if custom_domain_allowed else 'No',
            ])

        return response
    export_usage_csv.short_description = 'Export usage as CSV'


@admin.register(WorkspaceInfrastructure)
class WorkspaceInfrastructureAdmin(admin.ModelAdmin):
    list_display = (
        'workspace_name',
        'subdomain',
        'status_badge',
        'pool_tier',
        'subdomain_changes_display',
        'assigned_at',
        'activated_at',
    )
    list_filter = (
        'status',
        'assigned_at',
        'activated_at',
    )
    search_fields = (
        'workspace__name',
        'workspace__slug',
        'subdomain',
        'workspace__owner__email',
    )
    readonly_fields = (
        'id',
        'workspace',
        'pool',
        'assigned_at',
        'created_at',
        'updated_at',
        'infra_metadata_display',
        'preview_url_link',
    )
    fieldsets = (
        ('Workspace', {
            'fields': ('id', 'workspace', 'pool')
        }),
        ('Infrastructure', {
            'fields': ('subdomain', 'preview_url', 'preview_url_link', 'status')
        }),
        ('Subdomain Management', {
            'fields': (
                'subdomain_changes_count',
                'subdomain_changes_limit',
                'last_subdomain_change_at',
            )
        }),
        ('Metadata', {
            'fields': ('infra_metadata', 'infra_metadata_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('assigned_at', 'activated_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = []
    actions = ['mark_as_active', 'mark_as_suspended', 'invalidate_cache']

    def workspace_name(self, obj):
        return obj.workspace.name
    workspace_name.short_description = 'Workspace'
    workspace_name.admin_order_field = 'workspace__name'

    def status_badge(self, obj):
        colors = {
            'created': 'gray',
            'provisioning_pending': 'blue',
            'provisioning_in_progress': 'blue',
            'provisioned': 'green',
            'active': 'green',
            'failed': 'red',
            'degraded': 'orange',
            'suspended': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def pool_tier(self, obj):
        return 'POOL (Shared)'
    pool_tier.short_description = 'Infrastructure Type'

    def subdomain_changes_display(self, obj):
        color = 'green' if obj.subdomain_changes_count < obj.subdomain_changes_limit else 'red'
        return format_html(
            '<span style="color: {};">{} / {}</span>',
            color, obj.subdomain_changes_count, obj.subdomain_changes_limit
        )
    subdomain_changes_display.short_description = 'Subdomain Changes'

    def preview_url_link(self, obj):
        if obj.preview_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.preview_url, obj.preview_url)
        return '-'
    preview_url_link.short_description = 'Preview URL'

    def infra_metadata_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.infra_metadata, indent=2))
    infra_metadata_display.short_description = 'Infrastructure Metadata (JSON)'

    def mark_as_active(self, request, queryset):
        count = 0
        for infra in queryset:
            infra.mark_active()
            count += 1
        self.message_user(request, f'Marked {count} infrastructures as active.')
    mark_as_active.short_description = 'Mark as active'

    def mark_as_suspended(self, request, queryset):
        count = queryset.update(status='suspended')
        self.message_user(request, f'Suspended {count} infrastructures.')
    mark_as_suspended.short_description = 'Mark as suspended'

    def invalidate_cache(self, request, queryset):
        from workspace.hosting.services.tenant_lookup_cache import TenantLookupCache
        count = 0
        for infra in queryset:
            TenantLookupCache.invalidate_all_for_workspace(
                workspace_id=str(infra.workspace.id),
                subdomain=infra.subdomain
            )
            count += 1
        self.message_user(request, f'Invalidated cache for {count} workspaces.')
    invalidate_cache.short_description = 'Invalidate tenant cache'


@admin.register(DeployedSite)
class DeployedSiteAdmin(admin.ModelAdmin):
    list_display = (
        'site_name',
        'workspace_link',
        'subdomain_link',
        'status_badge',
        'password_protected_badge',
        'template_name',
        'last_publish_display',
        'user_email',
    )
    list_filter = (
        'status',
        'password_protection_enabled',
        'template',
        'created_at',
        'last_publish',
    )
    search_fields = (
        'site_name',
        'slug',
        'subdomain',
        'custom_subdomain',
        'workspace__name',
        'user__email',
    )
    readonly_fields = (
        'id',
        'workspace',
        'template',
        'customization',
        'user',
        'hosting_environment',
        'created_at',
        'updated_at',
        'deployment_details_display',
        'live_url',
    )
    fieldsets = (
        ('Site Information', {
            'fields': ('id', 'workspace', 'site_name', 'slug', 'status')
        }),
        ('User & Hosting', {
            'fields': ('user', 'hosting_environment')
        }),
        ('Theme', {
            'fields': ('template', 'customization')
        }),
        ('Domain Configuration', {
            'fields': ('subdomain', 'custom_subdomain', 'live_url')
        }),
        ('Template URLs', {
            'fields': ('template_cdn_url', 'template_dev_url')
        }),
        ('Deployment Details', {
            'fields': ('deployment_details', 'deployment_details_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [DeploymentAuditInline]
    actions = ['mark_active', 'mark_suspended', 'trigger_health_check', 'export_sites_csv']

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance"""
        return super().get_queryset(request).select_related(
            'workspace', 'template', 'user', 'hosting_environment',
            'hosting_environment__subscription', 'hosting_environment__subscription__plan'
        )

    def changelist_view(self, request, extra_context=None):
        """Add dashboard metrics to the changelist view"""
        extra_context = extra_context or {}
        qs = self.model.objects.all()
        
        # Count sites with custom domains
        sites_with_custom_domains = qs.filter(
            custom_domains__status='active'
        ).distinct().count()
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        
        extra_context['dashboard_metrics'] = {
            'total_sites': qs.count(),
            'status_breakdown': {
                'active': qs.filter(status='active').count(),
                'preview': qs.filter(status='preview').count(),
                'suspended': qs.filter(status='suspended').count(),
                'maintenance': qs.filter(status='maintenance').count(),
            },
            'sites_with_custom_domains': sites_with_custom_domains,
            'password_protected': qs.filter(password_protection_enabled=True).count(),
            'published_this_week': qs.filter(last_publish__gte=week_ago).count(),
            'created_this_week': qs.filter(created_at__gte=week_ago).count(),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def workspace_link(self, obj):
        url = reverse('admin:workspace_core_workspace_change', args=[obj.workspace.id])
        return format_html('<a href="{}">{}</a>', url, obj.workspace.name)
    workspace_link.short_description = 'Workspace'

    def subdomain_link(self, obj):
        subdomain = obj.custom_subdomain or obj.subdomain
        url = f"https://{subdomain}.huzilerz.com"
        return format_html('<a href="{}" target="_blank">{}</a>', url, subdomain)
    subdomain_link.short_description = 'Subdomain'

    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'suspended': 'red',
            'maintenance': 'orange',
            'preview': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def template_name(self, obj):
        return obj.template.name if obj.template else '-'
    template_name.short_description = 'Template'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Owner'
    user_email.admin_order_field = 'user__email'

    def deployed_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    deployed_at_display.short_description = 'Deployed At'
    deployed_at_display.admin_order_field = 'created_at'

    def password_protected_badge(self, obj):
        """Show password protection status with lock icon"""
        if obj.password_protection_enabled:
            return mark_safe('<span style="color: #ffc107; font-weight: bold;">🔒 Protected</span>')
        return mark_safe('<span style="color: green;">🔓 Public</span>')
    password_protected_badge.short_description = 'Access'

    def last_publish_display(self, obj):
        """Show last publish timestamp with relative time"""
        if not obj.last_publish:
            return mark_safe('<span style="color: gray;">Never</span>')
        
        now = timezone.now()
        diff = now - obj.last_publish
        
        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                return format_html('<span style="color: green;">{}m ago</span>', minutes)
            return format_html('<span style="color: green;">{}h ago</span>', hours)
        elif diff.days < 7:
            return format_html('<span style="color: #17a2b8;">{}d ago</span>', diff.days)
        elif diff.days < 30:
            weeks = diff.days // 7
            return format_html('<span style="color: #6c757d;">{}w ago</span>', weeks)
        else:
            return obj.last_publish.strftime('%Y-%m-%d')
    last_publish_display.short_description = 'Last Publish'
    last_publish_display.admin_order_field = 'last_publish'

    def live_url(self, obj):
        subdomain = obj.custom_subdomain or obj.subdomain
        url = f"https://{subdomain}.huzilerz.com"
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    live_url.short_description = 'Live Site URL'

    def deployment_details_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.deployment_details, indent=2))
    deployment_details_display.short_description = 'Deployment Details (JSON)'

    def mark_active(self, request, queryset):
        count = queryset.update(status='active')
        self.message_user(request, f'Marked {count} sites as active.')
    mark_active.short_description = 'Mark as active'

    def mark_suspended(self, request, queryset):
        count = queryset.update(status='suspended')
        self.message_user(request, f'Suspended {count} sites.')
    mark_suspended.short_description = 'Suspend sites'

    def trigger_health_check(self, request, queryset):
        from workspace.hosting.tasks.deployment_tasks import health_check_deployment
        count = 0
        for site in queryset:
            health_check_deployment.delay(str(site.id))
            count += 1
        self.message_user(request, f'Triggered health checks for {count} sites.')
    trigger_health_check.short_description = 'Run health check'

    def export_sites_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="deployed_sites.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Site Name', 'Workspace', 'Subdomain', 'Status', 'Template',
            'User Email', 'Created At'
        ])

        for site in queryset:
            writer.writerow([
                site.site_name,
                site.workspace.name,
                site.custom_subdomain or site.subdomain,
                site.status,
                site.template.name if site.template else 'N/A',
                site.user.email,
                site.created_at.strftime('%Y-%m-%d %H:%M'),
            ])

        return response
    export_sites_csv.short_description = 'Export as CSV'


@admin.register(DeploymentAudit)
class DeploymentAuditAdmin(admin.ModelAdmin):
    list_display = (
        'deployed_site_link',
        'status_badge',
        'initiated_by_display',
        'initiated_at',
        'duration_display',
        'rolled_back_display',
    )
    list_filter = (
        'status',
        'initiated_at',
        'completed_at',
        'rolled_back_at',
    )
    search_fields = (
        'deployed_site__site_name',
        'deployed_site__workspace__name',
        'initiated_by__email',
    )
    readonly_fields = (
        'id',
        'deployed_site',
        'previous_customization',
        'new_customization',
        'initiated_by',
        'initiated_at',
        'completed_at',
        'rolled_back_at',
        'deployment_metadata_display',
        'duration_display',
    )
    fieldsets = (
        ('Deployment', {
            'fields': ('id', 'deployed_site', 'status')
        }),
        ('Customizations', {
            'fields': ('previous_customization', 'new_customization')
        }),
        ('User & Timing', {
            'fields': ('initiated_by', 'initiated_at', 'completed_at', 'rolled_back_at', 'duration_display')
        }),
        ('Error Details', {
            'fields': ('error_message',)
        }),
        ('Metadata', {
            'fields': ('deployment_metadata', 'deployment_metadata_display'),
            'classes': ('collapse',)
        }),
    )
    actions = ['export_audit_csv']

    def deployed_site_link(self, obj):
        url = reverse('admin:workspace_hosting_deployedsite_change', args=[obj.deployed_site.id])
        return format_html('<a href="{}">{}</a>', url, obj.deployed_site.site_name)
    deployed_site_link.short_description = 'Site'

    def status_badge(self, obj):
        colors = {
            'initiated': 'blue',
            'in_progress': 'blue',
            'completed': 'green',
            'failed': 'red',
            'rolled_back': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def initiated_by_display(self, obj):
        return obj.initiated_by.email if obj.initiated_by else 'System'
    initiated_by_display.short_description = 'Initiated By'

    def duration_display(self, obj):
        if obj.completed_at and obj.initiated_at:
            duration = (obj.completed_at - obj.initiated_at).total_seconds()
            return f"{duration:.2f}s"
        return '-'
    duration_display.short_description = 'Duration'

    def rolled_back_display(self, obj):
        if obj.rolled_back_at:
            return mark_safe(
                '<span style="color: orange; font-weight: bold;">YES</span>'
            )
        return '-'
    rolled_back_display.short_description = 'Rolled Back'

    def deployment_metadata_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.deployment_metadata, indent=2))
    deployment_metadata_display.short_description = 'Metadata (JSON)'

    def export_audit_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="deployment_audits.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Site Name', 'Status', 'Initiated By', 'Initiated At',
            'Completed At', 'Duration (s)', 'Rolled Back', 'Error'
        ])

        for audit in queryset:
            duration = '-'
            if audit.completed_at and audit.initiated_at:
                duration = (audit.completed_at - audit.initiated_at).total_seconds()

            writer.writerow([
                audit.deployed_site.site_name,
                audit.status,
                audit.initiated_by.email if audit.initiated_by else 'System',
                audit.initiated_at.strftime('%Y-%m-%d %H:%M:%S'),
                audit.completed_at.strftime('%Y-%m-%d %H:%M:%S') if audit.completed_at else '-',
                duration,
                'Yes' if audit.rolled_back_at else 'No',
                audit.error_message or '-',
            ])

        return response
    export_audit_csv.short_description = 'Export as CSV'


@admin.register(CustomDomain)
class CustomDomainAdmin(admin.ModelAdmin):
    list_display = (
        'domain',
        'workspace_link',
        'status_badge',
        'ssl_status_display',
        'ssl_expiry_warning',
        'domain_expiry_warning',
        'is_primary',
        'verified_at',
        'created_at',
    )
    list_filter = (
        'status',
        'ssl_enabled',
        'is_primary',
        'purchased_via_platform',
        'verified_at',
        'created_at',
    )
    search_fields = (
        'domain',
        'workspace__name',
        'workspace__owner__email',
    )
    readonly_fields = (
        'id',
        'workspace',
        'created_at',
        'updated_at',
        'verified_at',
        'ssl_provisioned_at',
        'expires_at',
        'dns_records_display',
        'purchase_info_display',
        'verification_instructions',
    )
    fieldsets = (
        ('Domain Information', {
            'fields': ('id', 'workspace', 'deployed_site', 'domain', 'status', 'is_primary')
        }),
        ('Verification', {
            'fields': ('verification_token', 'verification_method', 'verified_at', 'verification_instructions')
        }),
        ('SSL Certificate', {
            'fields': ('ssl_enabled', 'ssl_certificate_arn', 'ssl_provisioned_at', 'expires_at')
        }),
        ('Domain Purchase', {
            'fields': ('purchased_via_platform', 'registrar_name', 'purchase_info_display'),
            'classes': ('collapse',)
        }),
        ('DNS Configuration', {
            'fields': ('dns_records', 'dns_records_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['verify_domain', 'enable_ssl', 'disable_ssl', 'check_expiring_domains']

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'workspace', 'deployed_site', 'created_by'
        )

    def workspace_link(self, obj):
        url = reverse('admin:workspace_core_workspace_change', args=[obj.workspace.id])
        return format_html('<a href="{}">{}</a>', url, obj.workspace.name)
    workspace_link.short_description = 'Workspace'

    def status_badge(self, obj):
        colors = {
            'pending': 'blue',
            'active': 'green',
            'failed': 'red',
            'expired': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def ssl_status_display(self, obj):
        if obj.ssl_enabled:
            return mark_safe(
                '<span style="color: green; font-weight: bold;">ENABLED</span>'
            )
        return mark_safe('<span style="color: gray;">DISABLED</span>')
    ssl_status_display.short_description = 'SSL'

    def dns_records_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.dns_records, indent=2))
    dns_records_display.short_description = 'DNS Records (JSON)'

    def ssl_expiry_warning(self, obj):
        """Show SSL expiry status with color-coded warning"""
        if not obj.ssl_enabled or not obj.expires_at:
            return '-'
        
        days_until_expiry = (obj.expires_at - timezone.now()).days
        
        if days_until_expiry < 0:
            return mark_safe('<span style="color: red; font-weight: bold;">⚠️ EXPIRED</span>')
        elif days_until_expiry <= 7:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} days</span>',
                days_until_expiry
            )
        elif days_until_expiry <= 30:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏰ {} days</span>',
                days_until_expiry
            )
        elif days_until_expiry <= 60:
            return format_html(
                '<span style="color: #ffc107;">{} days</span>',
                days_until_expiry
            )
        return format_html('<span style="color: green;">✓ {} days</span>', days_until_expiry)
    ssl_expiry_warning.short_description = 'SSL Expiry'

    def domain_expiry_warning(self, obj):
        """Show domain expiry for platform-purchased domains"""
        if not obj.purchased_via_platform or not obj.expires_at:
            return '-'
        
        days = obj.days_until_expiration
        if days is None:
            return '-'
        
        if days < 0:
            return mark_safe('<span style="color: red; font-weight: bold;">⚠️ EXPIRED</span>')
        elif days <= 7:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} days</span>',
                days
            )
        elif days <= 30:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏰ {} days</span>',
                days
            )
        return format_html('<span style="color: green;">{} days</span>', days)
    domain_expiry_warning.short_description = 'Domain Expiry'

    def purchase_info_display(self, obj):
        """Display purchase information for platform-purchased domains"""
        if not obj.purchased_via_platform:
            return mark_safe('<span style="color: gray;">External domain (not purchased via platform)</span>')
        
        info = []
        if obj.registrar_name:
            info.append(f"Registrar: {obj.registrar_name.upper()}")
        if obj.purchase_price_fcfa:
            info.append(f"Purchase: {obj.purchase_price_fcfa:,.0f} FCFA (${obj.purchase_price_usd:.2f})")
        if obj.renewal_price_fcfa:
            info.append(f"Renewal: {obj.renewal_price_fcfa:,.0f} FCFA/year")
        if obj.expires_at:
            info.append(f"Expires: {obj.expires_at.strftime('%Y-%m-%d')}")
        
        return mark_safe('<br>'.join(info) if info else 'Platform purchased (no details)')
    purchase_info_display.short_description = 'Purchase Info'

    def verification_instructions(self, obj):
        """Display DNS verification instructions"""
        if obj.status != 'pending':
            if obj.status == 'active':
                return mark_safe('<span style="color: green; font-weight: bold;">✓ Domain verified and active</span>')
            return f'Status: {obj.status}'
        
        instructions = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <h4 style="margin-top: 0;">DNS Verification Required</h4>
            <p>Add the following TXT record to your domain's DNS settings:</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #e9ecef;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Type</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Name</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Value</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">TXT</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">_huzilerz-verify</td>
                    <td style="padding: 8px; border: 1px solid #ddd; font-family: monospace;">{obj.verification_token}</td>
                </tr>
            </table>
            <p style="margin-bottom: 0; color: #6c757d; font-size: 12px;">
                DNS changes can take up to 48 hours to propagate.
            </p>
        </div>
        """
        return mark_safe(instructions)
    verification_instructions.short_description = 'Verification Instructions'

    def verify_domain(self, request, queryset):
        from workspace.hosting.tasks.domain_tasks import verify_custom_domain
        count = 0
        for domain in queryset.filter(status='pending'):
            verify_custom_domain.delay(str(domain.id))
            count += 1
        self.message_user(request, f'Triggered verification for {count} domains.')
    verify_domain.short_description = 'Verify domain'

    def enable_ssl(self, request, queryset):
        from workspace.hosting.tasks.domain_tasks import provision_ssl_certificate
        count = 0
        for domain in queryset.filter(status='active', ssl_enabled=False):
            provision_ssl_certificate.delay(str(domain.id))
            count += 1
        self.message_user(request, f'Triggered SSL provisioning for {count} domains.')
    enable_ssl.short_description = 'Enable SSL'

    def disable_ssl(self, request, queryset):
        count = queryset.update(ssl_enabled=False)
        self.message_user(request, f'Disabled SSL for {count} domains.')
    disable_ssl.short_description = 'Disable SSL'

    def check_expiring_domains(self, request, queryset):
        """Check and report domains expiring within 30 days"""
        expiring_soon = []
        for domain in queryset:
            if domain.expires_at and domain.is_expiring_soon:
                expiring_soon.append(f"{domain.domain} ({domain.days_until_expiration} days)")
        
        if expiring_soon:
            self.message_user(
                request,
                f'Domains expiring within 30 days: {", ".join(expiring_soon)}',
                level='WARNING'
            )
        else:
            self.message_user(request, 'No domains expiring within 30 days.')
    check_expiring_domains.short_description = 'Check expiring domains'


@admin.register(DomainPurchase)
class DomainPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'domain_name',
        'user_email',
        'status_badge',
        'price_display',
        'created_at',
        'expires_at',
    )
    list_filter = (
        'payment_status',
        'created_at',
        'expires_at',
    )
    search_fields = (
        'domain_name',
        'user__email',
        'registrar_order_id',
    )
    readonly_fields = (
        'id',
        'user',
        'created_at',
        'updated_at',
        'completed_at',
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def status_badge(self, obj):
        colors = {
            'pending': 'blue',
            'processing': 'yellow',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'orange',
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.payment_status.upper()
        )
    status_badge.short_description = 'Status'

    def price_display(self, obj):
        return f"${obj.price_usd:.2f}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price_usd'


@admin.register(DomainRenewal)
class DomainRenewalAdmin(admin.ModelAdmin):
    list_display = (
        'custom_domain_link',
        'status_badge',
        'price_display',
        'renewed_at',
        'new_expiry_date',
    )
    list_filter = (
        'renewal_status',
        'renewed_at',
        'new_expiry_date',
    )
    search_fields = (
        'domain_name',
        'registrar_renewal_id',
    )
    readonly_fields = (
        'id',
        'custom_domain',
        'renewed_at',
        'created_at',
        'updated_at',
    )

    def custom_domain_link(self, obj):
        if obj.custom_domain:
            url = reverse('admin:hosting_customdomain_change', args=[obj.custom_domain.id])
            return format_html('<a href="{}">{}</a>', url, obj.custom_domain.domain)
        return obj.domain_name
    custom_domain_link.short_description = 'Domain'

    def status_badge(self, obj):
        colors = {
            'pending_payment': 'blue',
            'payment_received': 'yellow',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red',
            'expired': 'gray',
        }
        color = colors.get(obj.renewal_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.renewal_status.upper()
        )
    status_badge.short_description = 'Status'

    def price_display(self, obj):
        return f"${obj.renewal_price_usd:.2f}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'renewal_price_usd'


@admin.register(SubdomainHistory)
class SubdomainHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'subdomain',
        'workspace_link',
        'is_active_display',
        'used_from',
        'used_until',
        'changed_by_display',
    )
    list_filter = (
        'used_from',
        'used_until',
    )
    search_fields = (
        'subdomain',
        'workspace__name',
        'changed_by__email',
    )
    readonly_fields = (
        'id',
        'workspace',
        'subdomain',
        'used_from',
        'used_until',
        'changed_by',
        'change_reason',
    )

    def workspace_link(self, obj):
        url = reverse('admin:workspace_core_workspace_change', args=[obj.workspace.id])
        return format_html('<a href="{}">{}</a>', url, obj.workspace.name)
    workspace_link.short_description = 'Workspace'

    def is_active_display(self, obj):
        if obj.is_active:
            return mark_safe('<span style="color: green; font-weight: bold;">ACTIVE</span>')
        return mark_safe('<span style="color: gray;">INACTIVE</span>')
    is_active_display.short_description = 'Status'

    def changed_by_display(self, obj):
        return obj.changed_by.email if obj.changed_by else 'System'
    changed_by_display.short_description = 'Changed By'


@admin.register(ResourceUsageLog)
class ResourceUsageLogAdmin(admin.ModelAdmin):
    list_display = (
        'hosting_environment_link',
        'recorded_at',
        'storage_used_gb',
        'bandwidth_used_gb',
        'requests_count',
        'avg_response_time_ms',
    )
    list_filter = (
        'recorded_at',
    )
    search_fields = (
        'hosting_environment__user__email',
    )
    readonly_fields = (
        'id',
        'hosting_environment',
        'recorded_at',
        'storage_used_gb',
        'bandwidth_used_gb',
        'requests_count',
        'avg_response_time_ms',
    )
    actions = ['export_usage_logs_csv']

    def hosting_environment_link(self, obj):
        url = reverse('admin:hosting_hostingenvironment_change', args=[obj.hosting_environment.id])
        return format_html('<a href="{}">{}</a>', url, obj.hosting_environment.user.email)
    hosting_environment_link.short_description = 'Hosting Environment'

    def export_usage_logs_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="usage_logs.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'User Email', 'Recorded At', 'Storage Used (GB)', 'Bandwidth Used (GB)',
            'Requests Count', 'Avg Response Time (ms)'
        ])

        for log in queryset:
            writer.writerow([
                log.hosting_environment.user.email,
                log.recorded_at.strftime('%Y-%m-%d %H:%M:%S'),
                log.storage_used_gb,
                log.bandwidth_used_gb,
                log.requests_count,
                log.avg_response_time_ms,
            ])

        return response
    export_usage_logs_csv.short_description = 'Export as CSV'


@admin.register(DeploymentLog)
class DeploymentLogAdmin(admin.ModelAdmin):
    list_display = (
        'deployed_site_link',
        'trigger',
        'status_badge',
        'started_at',
    )
    list_filter = (
        'trigger',
        'status',
        'started_at',
    )
    search_fields = (
        'site__site_name',
        'site__workspace__name',
        'trigger',
    )
    readonly_fields = (
        'id',
        'site',
        'trigger',
        'status',
        'started_at',
        'completed_at',
        'actions_log',
        'actions_log_display',
    )

    def deployed_site_link(self, obj):
        url = reverse('admin:hosting_deployedsite_change', args=[obj.site.id])
        return format_html('<a href="{}">{}</a>', url, obj.site.site_name)
    deployed_site_link.short_description = 'Site'

    def status_badge(self, obj):
        colors = {
            'success': 'green',
            'failed': 'red',
            'in_progress': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'


    def actions_log_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.actions_log, indent=2))
    actions_log_display.short_description = 'Actions Log (JSON)'


@admin.register(SitePerformanceMetrics)
class SitePerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = (
        'deployed_site_link',
        'date',
        'uptime_percentage',
        'avg_response_time_ms',
    )
    list_filter = (
        'date',
    )
    search_fields = (
        'site__site_name',
        'site__workspace__name',
    )
    readonly_fields = (
        'id',
        'site',
        'date',
    )

    def deployed_site_link(self, obj):
        url = reverse('admin:hosting_deployedsite_change', args=[obj.site.id])
        return format_html('<a href="{}">{}</a>', url, obj.site.site_name)
    deployed_site_link.short_description = 'Site'


# Custom Admin Site with Metrics Dashboard

class HostingAdminSite(admin.AdminSite):
    site_header = "Hosting Management"
    site_title = "Hosting Admin"
    index_title = "Infrastructure & Deployment Management"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('metrics/', self.admin_view(self.metrics_dashboard), name='hosting_metrics'),
            path('metrics/api/', self.admin_view(self.metrics_api), name='hosting_metrics_api'),
            path('cache/management/', self.admin_view(self.cache_management), name='cache_management'),
        ]
        return custom_urls + urls

    def metrics_dashboard(self, request):
        """Display metrics dashboard"""
        from workspace.hosting.services.metrics_service import MetricsService

        # Get metrics for different windows
        metrics_minute = MetricsService.get_all_metrics('minute')
        metrics_hour = MetricsService.get_all_metrics('hour')
        metrics_day = MetricsService.get_all_metrics('day')

        # Check alerts
        alerts = MetricsService.check_alert_thresholds()

        context = dict(
            self.each_context(request),
            title="Infrastructure Metrics Dashboard",
            metrics_minute=metrics_minute,
            metrics_hour=metrics_hour,
            metrics_day=metrics_day,
            alerts=alerts,
        )

        return render(request, 'admin/hosting/metrics_dashboard.html', context)

    def metrics_api(self, request):
        """API endpoint for fetching metrics"""
        from workspace.hosting.services.metrics_service import MetricsService

        window = request.GET.get('window', 'hour')
        metrics = MetricsService.get_all_metrics(window)
        alerts = MetricsService.check_alert_thresholds()

        return JsonResponse({
            'metrics': metrics,
            'alerts': alerts,
        })

    def cache_management(self, request):
        """Cache management interface"""
        from workspace.hosting.services.tenant_lookup_cache import TenantLookupCache

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'warm_all':
                result = TenantLookupCache.warm_cache_for_all_workspaces()
                self.message_user(request, f'Warmed cache for {result["warmed"]} workspaces.')
            elif action == 'invalidate_workspace':
                workspace_id = request.POST.get('workspace_id')
                if workspace_id:
                    TenantLookupCache.invalidate_workspace(workspace_id)
                    self.message_user(request, f'Invalidated cache for workspace {workspace_id}.')

        context = dict(
            self.each_context(request),
            title="Tenant Cache Management",
        )

        return render(request, 'admin/hosting/cache_management.html', context)


# Optional: Use custom admin site (uncomment if you want a separate hosting admin)
# hosting_admin_site = HostingAdminSite(name='hosting_admin')
# Register all models with the custom admin site if using it
