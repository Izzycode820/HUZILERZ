"""
Production-Ready Django Admin Configuration for Security Models
Enterprise-grade admin interface for security monitoring and management
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import (
    SecurityEvent, SecurityAlert, SessionInfo, 
    AuditLog, ThreatIntelligence, SecurityMetrics
)


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """
    Production-grade SecurityEvent administration
    Enhanced security event monitoring with advanced filtering and actions
    """
    
    list_display = (
        'event_type', 'user_info', 'risk_level_display', 
        'ip_address', 'location_display', 'is_processed', 'timestamp'
    )
    
    list_filter = (
        'event_type', 'risk_level', 'is_processed', 'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter),
        'event_category'  # Custom property from model
    )
    
    search_fields = (
        'user__email', 'user__username', 'event_description', 
        'ip_address', 'user_agent'
    )
    
    readonly_fields = (
        'id', 'timestamp', 'created_at', 'processed_at', 
        'location_info', 'metadata', 'event_category'
    )
    
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    list_per_page = 50
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'event_description', 'risk_level', 'event_category')
        }),
        ('User Context', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'device_fingerprint'),
            'classes': ('collapse',)
        }),
        ('Location & Metadata', {
            'fields': ('location_info', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'created_at')
        })
    )
    
    actions = ['mark_processed', 'mark_unprocessed', 'export_events']
    
    def user_info(self, obj):
        """Display user information with link"""
        if obj.user:
            url = reverse('admin:authentication_user_change', args=[obj.user.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.user.email
            )
        return format_html('<em style="color: gray;">Anonymous</em>')
    user_info.short_description = 'User'
    user_info.admin_order_field = 'user__email'
    
    def risk_level_display(self, obj):
        """Display risk level with color coding"""
        colors = {
            1: ('#28a745', 'Low'),      # Green
            2: ('#ffc107', 'Medium'),   # Yellow
            3: ('#fd7e14', 'High'),     # Orange
            4: ('#dc3545', 'Critical')  # Red
        }
        color, label = colors.get(obj.risk_level, ('#6c757d', 'Unknown'))
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, label
        )
    risk_level_display.short_description = 'Risk Level'
    risk_level_display.admin_order_field = 'risk_level'
    
    def location_display(self, obj):
        """Display location information"""
        if obj.location_info and isinstance(obj.location_info, dict):
            country = obj.location_info.get('country', '')
            city = obj.location_info.get('city', '')
            if country and city:
                return f"{city}, {country}"
            elif country:
                return country
        return '-'
    location_display.short_description = 'Location'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')
    
    def mark_processed(self, request, queryset):
        """Mark selected events as processed"""
        updated = 0
        for event in queryset.filter(is_processed=False):
            event.mark_processed()
            updated += 1
        
        self.message_user(
            request, 
            f'{updated} security events marked as processed.',
            level='SUCCESS' if updated > 0 else 'INFO'
        )
    mark_processed.short_description = 'Mark as processed'
    
    def mark_unprocessed(self, request, queryset):
        """Mark selected events as unprocessed"""
        updated = queryset.filter(is_processed=True).update(
            is_processed=False,
            processed_at=None
        )
        self.message_user(
            request, 
            f'{updated} security events marked as unprocessed.',
            level='SUCCESS' if updated > 0 else 'INFO'
        )
    mark_unprocessed.short_description = 'Mark as unprocessed'
    
    def export_events(self, request, queryset):
        """Export selected events (placeholder for CSV/JSON export)"""
        # In production, implement actual export functionality
        count = queryset.count()
        self.message_user(
            request,
            f'Export functionality would export {count} events. '
            'Implement CSV/JSON export in production.',
            level='INFO'
        )
    export_events.short_description = 'Export selected events'


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    """
    Production-grade SecurityAlert administration
    Alert management with priority-based workflow
    """
    
    list_display = (
        'alert_type', 'title_truncated', 'severity_display', 
        'user_info', 'status', 'assigned_to_display', 'created_at'
    )
    
    list_filter = (
        'alert_type', 'severity', 'status', 'created_at',
        ('user', admin.RelatedOnlyFieldListFilter),
        ('assigned_to', admin.RelatedOnlyFieldListFilter)
    )
    
    search_fields = (
        'title', 'description', 'user__email', 'user__username'
    )
    
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'resolved_at', 'alert_data'
    )
    
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('alert_type', 'title', 'description', 'severity')
        }),
        ('Assignment & Status', {
            'fields': ('status', 'assigned_to')
        }),
        ('Related User', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        ('Alert Data', {
            'fields': ('alert_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at')
        })
    )
    
    actions = ['assign_to_me', 'mark_resolved', 'mark_false_positive']
    
    def title_truncated(self, obj):
        """Display truncated title"""
        if len(obj.title) > 50:
            return obj.title[:47] + '...'
        return obj.title
    title_truncated.short_description = 'Title'
    title_truncated.admin_order_field = 'title'
    
    def severity_display(self, obj):
        """Display severity with appropriate styling"""
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107', 
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.severity
        )
    severity_display.short_description = 'Severity'
    severity_display.admin_order_field = 'severity'
    
    def user_info(self, obj):
        """Display associated user"""
        if obj.user:
            url = reverse('admin:authentication_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_info.short_description = 'User'
    
    def assigned_to_display(self, obj):
        """Display assigned user"""
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return format_html('<em style="color: gray;">Unassigned</em>')
    assigned_to_display.short_description = 'Assigned To'
    
    def assign_to_me(self, request, queryset):
        """Assign selected alerts to current user"""
        updated = queryset.filter(status='OPEN').update(assigned_to=request.user)
        self.message_user(
            request,
            f'{updated} alerts assigned to you.',
            level='SUCCESS' if updated > 0 else 'INFO'
        )
    assign_to_me.short_description = 'Assign to me'
    
    def mark_resolved(self, request, queryset):
        """Mark selected alerts as resolved"""
        updated = 0
        for alert in queryset.exclude(status='RESOLVED'):
            alert.resolve(resolved_by=request.user)
            updated += 1
        
        self.message_user(
            request,
            f'{updated} alerts marked as resolved.',
            level='SUCCESS' if updated > 0 else 'INFO'
        )
    mark_resolved.short_description = 'Mark as resolved'
    
    def mark_false_positive(self, request, queryset):
        """Mark selected alerts as false positives"""
        updated = queryset.exclude(status='FALSE_POSITIVE').update(
            status='FALSE_POSITIVE',
            resolved_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} alerts marked as false positives.',
            level='SUCCESS' if updated > 0 else 'INFO'
        )
    mark_false_positive.short_description = 'Mark as false positive'


@admin.register(SessionInfo)
class SessionInfoAdmin(admin.ModelAdmin):
    """
    Production-grade SessionInfo administration
    Enhanced session monitoring and management
    """
    
    list_display = (
        'session_id_short', 'user_info', 'is_active', 'mfa_verified',
        'is_suspicious', 'last_activity', 'expires_at'
    )
    
    list_filter = (
        'is_active', 'mfa_verified', 'is_suspicious', 'expires_at',
        ('user', admin.RelatedOnlyFieldListFilter)
    )
    
    search_fields = (
        'user__email', 'user__username', 'ip_address', 'device_fingerprint'
    )
    
    readonly_fields = (
        'session_id', 'created_at', 'device_info', 'location_info', 
        'security_flags', 'token_family'
    )
    
    ordering = ('-last_activity',)
    list_per_page = 50
    
    actions = ['revoke_sessions', 'mark_suspicious', 'clear_suspicious']
    
    def session_id_short(self, obj):
        """Display shortened session ID"""
        return str(obj.session_id)[:8] + '...'
    session_id_short.short_description = 'Session ID'
    
    def user_info(self, obj):
        """Display user with link"""
        if obj.user:
            url = reverse('admin:authentication_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_info.short_description = 'User'
    
    def revoke_sessions(self, request, queryset):
        """Revoke selected sessions"""
        updated = 0
        for session in queryset.filter(is_active=True):
            session.revoke()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} sessions revoked.',
            level='SUCCESS' if updated > 0 else 'INFO'
        )
    revoke_sessions.short_description = 'Revoke sessions'
    
    def mark_suspicious(self, request, queryset):
        """Mark sessions as suspicious"""
        updated = 0
        for session in queryset.filter(is_suspicious=False):
            session.mark_suspicious(['Manually marked by admin'])
            updated += 1
        
        self.message_user(request, f'{updated} sessions marked as suspicious.')
    mark_suspicious.short_description = 'Mark as suspicious'
    
    def clear_suspicious(self, request, queryset):
        """Clear suspicious flag"""
        updated = queryset.filter(is_suspicious=True).update(
            is_suspicious=False,
            security_flags=[]
        )
        self.message_user(request, f'{updated} sessions cleared from suspicious status.')
    clear_suspicious.short_description = 'Clear suspicious flag'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Production-grade AuditLog administration
    Comprehensive audit trail management
    """
    
    list_display = (
        'action', 'resource', 'user_info', 'ip_address', 'timestamp'
    )
    
    list_filter = (
        'action', 'resource', 'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter)
    )
    
    search_fields = (
        'user__email', 'resource', 'resource_id', 'ip_address'
    )
    
    readonly_fields = (
        'id', 'timestamp', 'changes', 'metadata'
    )
    
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    list_per_page = 100
    
    def user_info(self, obj):
        """Display user with link"""
        if obj.user:
            url = reverse('admin:authentication_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return format_html('<em style="color: gray;">System</em>')
    user_info.short_description = 'User'


@admin.register(ThreatIntelligence)
class ThreatIntelligenceAdmin(admin.ModelAdmin):
    """
    Production-grade ThreatIntelligence administration
    IOC and threat feed management
    """
    
    list_display = (
        'ioc_type', 'ioc_value_truncated', 'threat_type', 
        'severity_display', 'confidence', 'is_active', 'last_seen'
    )
    
    list_filter = (
        'ioc_type', 'threat_type', 'severity', 'is_active', 
        'confidence', 'source', 'last_seen'
    )
    
    search_fields = (
        'ioc_value', 'description', 'source'
    )
    
    readonly_fields = (
        'id', 'first_seen', 'last_seen', 'created_at', 'updated_at'
    )
    
    ordering = ('-last_seen',)
    list_per_page = 50
    
    actions = ['activate_indicators', 'deactivate_indicators', 'update_last_seen']
    
    def ioc_value_truncated(self, obj):
        """Display truncated IOC value"""
        if len(obj.ioc_value) > 30:
            return obj.ioc_value[:27] + '...'
        return obj.ioc_value
    ioc_value_truncated.short_description = 'IOC Value'
    ioc_value_truncated.admin_order_field = 'ioc_value'
    
    def severity_display(self, obj):
        """Display severity with color coding"""
        colors = {
            1: '#28a745',   # Low - Green
            2: '#ffc107',   # Medium - Yellow
            3: '#fd7e14',   # High - Orange
            4: '#dc3545'    # Critical - Red
        }
        color = colors.get(obj.severity, '#6c757d')
        severity_labels = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical'}
        label = severity_labels.get(obj.severity, 'Unknown')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, label
        )
    severity_display.short_description = 'Severity'
    severity_display.admin_order_field = 'severity'
    
    def activate_indicators(self, request, queryset):
        """Activate selected threat indicators"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} threat indicators activated.')
    activate_indicators.short_description = 'Activate indicators'
    
    def deactivate_indicators(self, request, queryset):
        """Deactivate selected threat indicators"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} threat indicators deactivated.')
    deactivate_indicators.short_description = 'Deactivate indicators'
    
    def update_last_seen(self, request, queryset):
        """Update last seen timestamp"""
        updated = 0
        for indicator in queryset:
            indicator.update_last_seen()
            updated += 1
        self.message_user(request, f'{updated} indicators updated.')
    update_last_seen.short_description = 'Update last seen'


@admin.register(SecurityMetrics)
class SecurityMetricsAdmin(admin.ModelAdmin):
    """
    Production-grade SecurityMetrics administration
    Security metrics and analytics dashboard
    """
    
    list_display = (
        'metric_type', 'aggregation_period', 'period_start', 
        'count', 'updated_at'
    )
    
    list_filter = (
        'metric_type', 'aggregation_period', 'period_start'
    )
    
    search_fields = ('metric_type',)
    
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'breakdown', 'metadata'
    )
    
    date_hierarchy = 'period_start'
    ordering = ('-period_start',)
    list_per_page = 100
    
    actions = ['recalculate_metrics']
    
    def recalculate_metrics(self, request, queryset):
        """Recalculate selected metrics (placeholder)"""
        count = queryset.count()
        self.message_user(
            request,
            f'Recalculation triggered for {count} metrics. '
            'Implement actual recalculation in production.',
            level='INFO'
        )
    recalculate_metrics.short_description = 'Recalculate metrics'


# Custom admin site configuration
class SecurityAdminSite(admin.AdminSite):
    """Custom admin site for security models"""
    site_header = 'HustlerzCamp Security Center'
    site_title = 'Security Admin'
    index_title = 'Security Monitoring & Management'
    
    def index(self, request, extra_context=None):
        """Enhanced admin index with security dashboard"""
        extra_context = extra_context or {}
        
        # Add security dashboard data
        if request.user.is_authenticated:
            extra_context.update({
                'recent_high_risk_events': SecurityEvent.objects.filter(
                    risk_level__gte=3
                ).order_by('-timestamp')[:5],
                'open_alerts_count': SecurityAlert.objects.filter(
                    status='OPEN'
                ).count(),
                'active_sessions_count': SessionInfo.objects.filter(
                    is_active=True,
                    expires_at__gt=timezone.now()
                ).count()
            })
        
        return super().index(request, extra_context)


# Register security admin site
security_admin_site = SecurityAdminSite(name='security_admin')