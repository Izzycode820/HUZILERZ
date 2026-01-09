"""
Subscription Admin - Production-Ready for Solo Dev Monitoring
==============================================================
Clean, comprehensive Django admin for subscription lifecycle management.
Designed for solo devs to monitor their SaaS in early stages.

Key Features:
- Dashboard-style metrics in changelist headers
- Color-coded status badges for quick scanning
- Smart filters for common monitoring scenarios
- Admin actions for manual interventions
- Inline history and payment records
- DLQ (Dead Letter Queue) monitoring

Author: HUZILERZ Team
Last Updated: 2026-01-06
"""
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Sum, Q
from django.http import HttpResponse
from datetime import timedelta
import csv

from .models import (
    SubscriptionPlan,
    Subscription,
    SubscriptionHistory,
    SubscriptionEventLog,
    PaymentRecord,
    SubscriptionDeadLetterQueue,
)


# =============================================================================
# SUBSCRIPTION PLAN ADMIN
# =============================================================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """
    Subscription Plans Management
    Shows pricing tiers and active subscriber counts
    """

    list_display = (
        'name',
        'tier_badge',
        'intro_price_display',
        'monthly_price_display',
        'yearly_price_display',
        'active_subscribers_count',
        'is_active',
    )

    list_filter = ('tier', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'subscriber_stats')
    ordering = ('regular_price_monthly',)

    fieldsets = (
        ('Plan Identity', {
            'fields': ('name', 'tier', 'description', 'is_active')
        }),
        ('Intro Pricing (First-Time Users)', {
            'fields': ('intro_price', 'intro_duration_days'),
            'description': 'One-time intro offer for new users. Eligibility tracked per user.'
        }),
        ('Regular Pricing', {
            'fields': ('regular_price_monthly', 'regular_price_yearly'),
        }),
        ('Analytics', {
            'fields': ('subscriber_stats',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def tier_badge(self, obj):
        """Color-coded tier badge"""
        colors = {
            'free': '#6c757d',      # gray
            'beginning': '#17a2b8', # teal
            'pro': '#007bff',       # blue
            'enterprise': '#6f42c1', # purple
        }
        color = colors.get(obj.tier, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.tier.upper()
        )
    tier_badge.short_description = 'Tier'
    tier_badge.admin_order_field = 'tier'

    def intro_price_display(self, obj):
        """Intro price with duration"""
        if obj.intro_price == 0:
            return mark_safe('<span style="color: #6c757d;">—</span>')
        price_formatted = f"{obj.intro_price:,.0f}"
        return format_html(
            '<span style="color: #28a745;">{} XAF</span><br>'
            '<small style="color: #6c757d;">{} days</small>',
            price_formatted, obj.intro_duration_days
        )
    intro_price_display.short_description = 'Intro'

    def monthly_price_display(self, obj):
        """Monthly price formatted"""
        if obj.regular_price_monthly == 0:
            return mark_safe('<span style="color: #28a745; font-weight: bold;">FREE</span>')
        price_formatted = f"{obj.regular_price_monthly:,.0f}"
        return format_html('{} XAF<br><small style="color: #6c757d;">/month</small>',
                          price_formatted)
    monthly_price_display.short_description = 'Monthly'

    def yearly_price_display(self, obj):
        """Yearly price with savings percentage"""
        if obj.regular_price_yearly == 0:
            return mark_safe('<span style="color: #6c757d;">—</span>')
        
        # Calculate savings vs monthly
        monthly_yearly = obj.regular_price_monthly * 12
        price_formatted = f"{obj.regular_price_yearly:,.0f}"
        if monthly_yearly > 0:
            savings_pct = ((monthly_yearly - obj.regular_price_yearly) / monthly_yearly) * 100
            savings_formatted = f"{savings_pct:.0f}"
            return format_html(
                '{} XAF<br><small style="color: #28a745;">Save {}%</small>',
                price_formatted, savings_formatted
            )
        return format_html('{} XAF/year', price_formatted)
    yearly_price_display.short_description = 'Yearly'

    def active_subscribers_count(self, obj):
        """Link to active subscribers"""
        count = Subscription.objects.filter(plan=obj, status='active').count()
        if count == 0:
            return mark_safe('<span style="color: #6c757d;">0</span>')
        return format_html(
            '<a href="{}?plan__id__exact={}&status__exact=active">'
            '<strong>{}</strong> active</a>',
            reverse('admin:subscription_subscription_changelist'),
            obj.id, count
        )
    active_subscribers_count.short_description = 'Subscribers'

    def subscriber_stats(self, obj):
        """Detailed subscriber breakdown"""
        stats = Subscription.objects.filter(plan=obj).aggregate(
            active=Count('id', filter=Q(status='active')),
            grace=Count('id', filter=Q(status='grace_period')),
            pending=Count('id', filter=Q(status='pending_payment')),
            total=Count('id'),
        )
        return format_html(
            '<div style="font-family: monospace;">'
            'Active: <strong>{}</strong><br>'
            'Grace Period: {}<br>'
            'Pending Payment: {}<br>'
            '<hr style="margin: 5px 0;">'
            'Total Ever: {}'
            '</div>',
            stats['active'], stats['grace'], stats['pending'], stats['total']
        )
    subscriber_stats.short_description = 'Subscriber Stats'


# =============================================================================
# SUBSCRIPTION ADMIN - Main Monitoring Hub
# =============================================================================

class SubscriptionHistoryInline(admin.TabularInline):
    """Inline subscription change history"""
    model = SubscriptionHistory
    extra = 0
    can_delete = False
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at', 'action', 'bill_number', 'status_badge',
        'previous_plan', 'new_plan', 'amount_paid', 'payment_method'
    )
    fields = (
        'created_at', 'action', 'bill_number', 'status_badge',
        'previous_plan', 'new_plan', 'amount_paid'
    )

    def status_badge(self, obj):
        colors = {'paid': '#28a745', 'unpaid': '#dc3545', 'pending': '#ffc107'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def has_add_permission(self, request, obj=None):
        return False


class PaymentRecordInline(admin.TabularInline):
    """Inline payment history"""
    model = PaymentRecord
    extra = 0
    can_delete = False
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at', 'amount_display', 'status_badge', 'charge_type',
        'momo_operator', 'momo_phone_used', 'transaction_id'
    )
    fields = (
        'created_at', 'amount_display', 'status_badge', 'charge_type',
        'momo_operator', 'transaction_id'
    )

    def amount_display(self, obj):
        amount_formatted = f"{obj.amount:,.0f}"
        return format_html('<strong>{} XAF</strong>', amount_formatted)
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {'success': '#28a745', 'failed': '#dc3545', 'pending': '#ffc107'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Main Subscription Monitoring Hub
    ================================
    Your primary dashboard for monitoring subscription health.
    
    Quick Reference:
    - GREEN status = healthy
    - ORANGE status = needs attention soon
    - RED status = action required
    """

    list_display = (
        'user_email',
        'plan_tier_badge',
        'status_badge',
        'billing_info',
        'expiry_countdown',
        'last_payment_date',
        'created_at',
    )

    list_filter = (
        'status',
        'plan__tier',
        'billing_cycle',
        'billing_phase',
        ('expires_at', admin.DateFieldListFilter),
        ('created_at', admin.DateFieldListFilter),
    )

    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'id',
    )

    readonly_fields = (
        'id',
        'user_link',
        'plan_link',
        'workspace_link',
        'payment_intent_display',
        'created_at',
        'updated_at',
        'subscription_health_summary',
        'lifecycle_timeline',
    )

    fieldsets = (
        ('🔍 Quick Health Check', {
            'fields': ('subscription_health_summary',),
            'classes': ('wide',),
        }),
        ('👤 User & Plan', {
            'fields': ('user_link', 'plan_link', 'workspace_link'),
        }),
        ('📊 Status & Billing', {
            'fields': (
                'status',
                ('billing_cycle', 'billing_phase'),
                ('intro_cycles_remaining', 'currency'),
            ),
        }),
        ('📅 Billing Cycle Dates', {
            'fields': (
                ('current_cycle_started_at', 'current_cycle_ends_at'),
                ('started_at', 'expires_at'),
                'last_manual_renewal',
            ),
        }),
        ('⚠️ Grace Period & Reminders', {
            'fields': (
                'grace_period_ends_at',
                'next_renewal_reminder',
            ),
            'classes': ('collapse',),
        }),
        ('🔄 Pending Plan Change', {
            'fields': (
                'pending_plan_change',
                'plan_change_effective_date',
            ),
            'classes': ('collapse',),
        }),
        ('💳 Current Payment', {
            'fields': ('payment_intent_display',),
            'classes': ('collapse',),
        }),
        ('📋 Metadata', {
            'fields': ('subscription_metadata', 'applied_discounts'),
            'classes': ('collapse',),
        }),
        ('📜 Lifecycle Timeline', {
            'fields': ('lifecycle_timeline',),
            'classes': ('collapse',),
        }),
        ('🔧 System', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    inlines = [PaymentRecordInline, SubscriptionHistoryInline]

    actions = [
        'action_start_grace_period',
        'action_force_expire',
        'action_extend_30_days',
        'action_downgrade_to_free',
        'action_suspend',
        'action_reactivate',
        'action_export_csv',
    ]

    # -------------------------------------------------------------------------
    # List Display Methods
    # -------------------------------------------------------------------------

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def plan_tier_badge(self, obj):
        """Color-coded plan tier"""
        colors = {
            'free': '#6c757d',
            'beginning': '#17a2b8',
            'pro': '#007bff',
            'enterprise': '#6f42c1',
        }
        color = colors.get(obj.plan.tier, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.plan.tier.upper()
        )
    plan_tier_badge.short_description = 'Plan'
    plan_tier_badge.admin_order_field = 'plan__tier'

    def status_badge(self, obj):
        """Color-coded status with icon hints"""
        status_config = {
            'active': ('🟢', '#28a745'),
            'pending_payment': ('🟡', '#ffc107'),
            'change_pending': ('🔄', '#17a2b8'),
            'grace_period': ('🟠', '#fd7e14'),
            'expired': ('🔴', '#dc3545'),
            'suspended': ('⛔', '#6c757d'),
            'cancelled': ('❌', '#6c757d'),
        }
        icon, color = status_config.get(obj.status, ('❓', '#6c757d'))
        display_status = obj.status.replace('_', ' ').upper()
        return format_html(
            '{} <span style="color: {}; font-weight: bold;">{}</span>',
            icon, color, display_status
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def billing_info(self, obj):
        """Combined billing cycle + phase info"""
        phase_color = '#28a745' if obj.billing_phase == 'intro' else '#6c757d'
        phase_label = 'INTRO 🎁' if obj.billing_phase == 'intro' else 'Regular'
        return format_html(
            '{}<br><small style="color: {};">{}</small>',
            obj.billing_cycle.capitalize(),
            phase_color,
            phase_label
        )
    billing_info.short_description = 'Billing'

    def expiry_countdown(self, obj):
        """Days until expiry with color coding"""
        if not obj.expires_at:
            return mark_safe('<span style="color: #6c757d;">Never</span>')
        
        now = timezone.now()
        if obj.expires_at < now:
            days_ago = (now - obj.expires_at).days
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">EXPIRED</span><br>'
                '<small>{} days ago</small>',
                days_ago
            )
        
        days_left = (obj.expires_at - now).days
        
        if days_left <= 3:
            color = '#dc3545'  # Red - urgent
            label = '⚠️ URGENT'
        elif days_left <= 5:
            color = '#fd7e14'  # Orange - renewal window
            label = '📢 Renewal Window'
        elif days_left <= 7:
            color = '#ffc107'  # Yellow - soon
            label = ''
        else:
            color = '#28a745'  # Green - healthy
            label = ''
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} days</span>'
            '<br><small>{}</small>',
            color, days_left, label
        )
    expiry_countdown.short_description = 'Expires'
    expiry_countdown.admin_order_field = 'expires_at'

    def last_payment_date(self, obj):
        """Last successful payment"""
        last_payment = PaymentRecord.objects.filter(
            subscription=obj, status='success'
        ).order_by('-created_at').first()
        
        if not last_payment:
            return mark_safe('<span style="color: #6c757d;">No payments</span>')
        
        amount_formatted = f"{last_payment.amount:,.0f}"
        return format_html(
            '{}<br><small>{} XAF</small>',
            last_payment.created_at.strftime('%Y-%m-%d'),
            amount_formatted
        )
    last_payment_date.short_description = 'Last Payment'

    # -------------------------------------------------------------------------
    # Detail View Methods
    # -------------------------------------------------------------------------

    def user_link(self, obj):
        """Clickable link to user admin"""
        if not obj.user:
            return '—'
        try:
            url = reverse('admin:authentication_user_change', args=[obj.user.id])
            return format_html(
                '<a href="{}" style="font-weight: bold;">{}</a><br>'
                '<small style="color: #6c757d;">{}</small>',
                url, obj.user.email,
                obj.user.get_full_name() or 'No name'
            )
        except Exception:
            return obj.user.email
    user_link.short_description = 'User'

    def plan_link(self, obj):
        """Clickable link to plan admin"""
        if not obj.plan:
            return '—'
        url = reverse('admin:subscription_subscriptionplan_change', args=[obj.plan.id])
        return format_html(
            '<a href="{}">{}</a><br>'
            '<small style="color: #6c757d;">Tier: {}</small>',
            url, obj.plan.name, obj.plan.tier.upper()
        )
    plan_link.short_description = 'Plan'

    def workspace_link(self, obj):
        """Link to primary workspace"""
        if not obj.primary_workspace:
            return mark_safe('<span style="color: #6c757d;">No workspace linked</span>')
        try:
            url = reverse('admin:workspace_core_workspace_change', args=[obj.primary_workspace.id])
            return format_html('<a href="{}">{}</a>', url, obj.primary_workspace.name)
        except Exception:
            return str(obj.primary_workspace)
    workspace_link.short_description = 'Workspace'

    def payment_intent_display(self, obj):
        """Current payment intent status"""
        if not obj.payment_intent:
            return mark_safe('<span style="color: #6c757d;">No active payment</span>')
        
        pi = obj.payment_intent
        status_colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
            'expired': '#dc3545',
        }
        status = getattr(pi, 'status', 'unknown')
        color = status_colors.get(status, '#6c757d')
        
        amount_formatted = f"{pi.amount:,.0f}"
        return format_html(
            '<div style="font-family: monospace; padding: 10px; background: #f8f9fa; border-radius: 4px;">'
            'ID: {}<br>'
            'Status: <span style="color: {}; font-weight: bold;">{}</span><br>'
            'Amount: {} XAF<br>'
            'Provider: {}'
            '</div>',
            str(pi.id)[:8] + '...',
            color, status.upper(),
            amount_formatted,
            getattr(pi, 'provider_name', 'Unknown')
        )
    payment_intent_display.short_description = 'Payment Intent'

    def subscription_health_summary(self, obj):
        """Quick health check summary for detail view"""
        issues = []
        
        # Check expiry
        if obj.expires_at:
            days_left = (obj.expires_at - timezone.now()).days if obj.expires_at > timezone.now() else 0
            if days_left <= 0:
                issues.append(('🔴', 'Subscription has EXPIRED'))
            elif days_left <= 3:
                issues.append(('🟠', f'Expiring in {days_left} days - URGENT'))
            elif days_left <= 5:
                issues.append(('🟡', f'In renewal window ({days_left} days left)'))
        
        # Check status
        if obj.status == 'grace_period':
            grace_left = (obj.grace_period_ends_at - timezone.now()).total_seconds() / 3600 if obj.grace_period_ends_at else 0
            issues.append(('🟠', f'In GRACE PERIOD ({grace_left:.0f} hours remaining)'))
        elif obj.status == 'suspended':
            issues.append(('⛔', 'Account is SUSPENDED'))
        elif obj.status == 'pending_payment':
            issues.append(('🟡', 'Waiting for payment confirmation'))
        
        # Check intro pricing
        if obj.billing_phase == 'intro':
            issues.append(('🎁', f'Using INTRO pricing ({obj.intro_cycles_remaining} cycles left)'))
        
        # Check pending plan change
        if obj.pending_plan_change:
            issues.append(('🔄', f'Plan change pending → {obj.pending_plan_change.name}'))
        
        if not issues:
            return format_html(
                '<div style="padding: 15px; background: #d4edda; border-radius: 4px; color: #155724;">'
                '✅ <strong>Healthy</strong> - No issues detected'
                '</div>'
            )
        
        html_lines = []
        for icon, msg in issues:
            html_lines.append(f'{icon} {msg}')
        
        return format_html(
            '<div style="padding: 15px; background: #fff3cd; border-radius: 4px;">'
            '{}'
            '</div>',
            '<br>'.join(html_lines)
        )
    subscription_health_summary.short_description = 'Health Check'

    def lifecycle_timeline(self, obj):
        """Visual timeline of subscription lifecycle"""
        events = SubscriptionEventLog.objects.filter(
            subscription=obj
        ).order_by('-created_at')[:10]
        
        if not events:
            return mark_safe('<span style="color: #6c757d;">No events recorded</span>')
        
        html = '<div style="font-family: monospace; font-size: 12px;">'
        for event in events:
            html += format_html(
                '<div style="padding: 5px 0; border-bottom: 1px solid #eee;">'
                '<strong>{}</strong> - {}<br>'
                '<small style="color: #6c757d;">{}</small>'
                '</div>',
                event.created_at.strftime('%Y-%m-%d %H:%M'),
                event.get_event_type_display(),
                event.description[:100] + '...' if len(event.description) > 100 else event.description
            )
        html += '</div>'
        return mark_safe(html)
    lifecycle_timeline.short_description = 'Recent Events'

    # -------------------------------------------------------------------------
    # Changelist customization - Dashboard Metrics
    # -------------------------------------------------------------------------

    def changelist_view(self, request, extra_context=None):
        """Add dashboard metrics to changelist header"""
        extra_context = extra_context or {}
        
        now = timezone.now()
        five_days_later = now + timedelta(days=5)
        
        # Calculate key metrics
        metrics = {
            'total_active': Subscription.objects.filter(status='active').count(),
            'total_grace': Subscription.objects.filter(status='grace_period').count(),
            'total_pending': Subscription.objects.filter(status='pending_payment').count(),
            'expiring_soon': Subscription.objects.filter(
                status='active',
                expires_at__lte=five_days_later,
                expires_at__gt=now
            ).count(),
            'expired_today': Subscription.objects.filter(
                expires_at__date=now.date()
            ).count(),
        }
        
        # Revenue this month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue = PaymentRecord.objects.filter(
            status='success',
            created_at__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        metrics['revenue_this_month'] = revenue
        
        # Plan distribution
        by_plan = Subscription.objects.filter(status='active').values(
            'plan__tier'
        ).annotate(count=Count('id')).order_by('plan__tier')
        metrics['by_plan'] = {item['plan__tier']: item['count'] for item in by_plan}
        
        extra_context['dashboard_metrics'] = metrics
        
        return super().changelist_view(request, extra_context=extra_context)

    # -------------------------------------------------------------------------
    # Admin Actions
    # -------------------------------------------------------------------------

    @admin.action(description='⏰ Start 72hr Grace Period')
    def action_start_grace_period(self, request, queryset):
        """Start grace period for selected subscriptions"""
        count = 0
        for sub in queryset.filter(status='active'):
            sub.status = 'grace_period'
            sub.grace_period_ends_at = timezone.now() + timedelta(hours=72)
            sub.save(update_fields=['status', 'grace_period_ends_at'])
            count += 1
        self.message_user(request, f'Started grace period for {count} subscription(s)')

    @admin.action(description='🔴 Force Expire Now')
    def action_force_expire(self, request, queryset):
        """Immediately expire selected subscriptions"""
        count = queryset.update(
            status='expired',
            expires_at=timezone.now()
        )
        self.message_user(request, f'Force expired {count} subscription(s)')

    @admin.action(description='📅 Extend by 30 Days')
    def action_extend_30_days(self, request, queryset):
        """Extend expiry by 30 days"""
        count = 0
        for sub in queryset.exclude(plan__tier='free'):
            if sub.expires_at:
                sub.expires_at = sub.expires_at + timedelta(days=30)
            else:
                sub.expires_at = timezone.now() + timedelta(days=30)
            sub.status = 'active'
            sub.save(update_fields=['expires_at', 'status'])
            count += 1
        self.message_user(request, f'Extended {count} subscription(s) by 30 days')

    @admin.action(description='⬇️ Downgrade to Free')
    def action_downgrade_to_free(self, request, queryset):
        """Force downgrade to free plan"""
        try:
            free_plan = SubscriptionPlan.objects.get(tier='free', is_active=True)
        except SubscriptionPlan.DoesNotExist:
            self.message_user(request, 'Free plan not found!', level='error')
            return
        
        count = queryset.exclude(plan__tier='free').update(
            plan=free_plan,
            status='active',
            expires_at=None,
            grace_period_ends_at=None,
            billing_phase='regular',
        )
        self.message_user(request, f'Downgraded {count} subscription(s) to free')

    @admin.action(description='⛔ Suspend')
    def action_suspend(self, request, queryset):
        """Suspend selected subscriptions"""
        count = queryset.exclude(status='suspended').update(status='suspended')
        self.message_user(request, f'Suspended {count} subscription(s)')

    @admin.action(description='✅ Reactivate')
    def action_reactivate(self, request, queryset):
        """Reactivate suspended subscriptions"""
        count = 0
        for sub in queryset.filter(status='suspended'):
            sub.status = 'active'
            # Set new expiry if none exists
            if not sub.expires_at or sub.expires_at < timezone.now():
                sub.expires_at = timezone.now() + timedelta(days=30)
            sub.save(update_fields=['status', 'expires_at'])
            count += 1
        self.message_user(request, f'Reactivated {count} subscription(s)')

    @admin.action(description='📊 Export to CSV')
    def action_export_csv(self, request, queryset):
        """Export subscriptions to CSV for analysis"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscriptions_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'User Email', 'Plan', 'Tier', 'Status', 'Billing Cycle',
            'Billing Phase', 'Started At', 'Expires At', 'Created At'
        ])
        
        for sub in queryset.select_related('user', 'plan'):
            writer.writerow([
                sub.user.email,
                sub.plan.name,
                sub.plan.tier,
                sub.status,
                sub.billing_cycle,
                sub.billing_phase,
                sub.started_at.isoformat() if sub.started_at else '',
                sub.expires_at.isoformat() if sub.expires_at else '',
                sub.created_at.isoformat(),
            ])
        
        return response

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related(
            'user', 'plan', 'payment_intent', 'primary_workspace', 'pending_plan_change'
        )


# =============================================================================
# SUBSCRIPTION HISTORY ADMIN
# =============================================================================

@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    """
    Subscription Change History / Billing Records
    Use this to look up customer billing inquiries
    """

    list_display = (
        'bill_number',
        'subscription_user',
        'action_badge',
        'status_badge',
        'plan_change',
        'amount_display',
        'payment_method',
        'created_at',
    )

    list_filter = (
        'action',
        'status',
        'payment_method',
        ('created_at', admin.DateFieldListFilter),
    )

    search_fields = (
        'bill_number',
        'subscription__user__email',
        'notes',
    )

    readonly_fields = (
        'id', 'subscription', 'action', 'bill_number', 'status',
        'previous_plan', 'new_plan', 'amount_paid', 'payment_method',
        'notes', 'metadata', 'created_at'
    )

    ordering = ('-created_at',)

    def subscription_user(self, obj):
        return obj.subscription.user.email
    subscription_user.short_description = 'User'
    subscription_user.admin_order_field = 'subscription__user__email'

    def action_badge(self, obj):
        """Color-coded action badge"""
        colors = {
            'created': '#17a2b8',
            'renewed': '#28a745',
            'upgraded': '#007bff',
            'downgraded': '#fd7e14',
            'converted': '#6f42c1',
            'suspended': '#6c757d',
            'reactivated': '#28a745',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.action.upper()
        )
    action_badge.short_description = 'Action'
    action_badge.admin_order_field = 'action'

    def status_badge(self, obj):
        colors = {'paid': '#28a745', 'unpaid': '#dc3545', 'pending': '#ffc107'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Payment'
    status_badge.admin_order_field = 'status'

    def plan_change(self, obj):
        """Show plan transition"""
        if obj.previous_plan and obj.new_plan:
            return format_html(
                '{} → <strong>{}</strong>',
                obj.previous_plan.tier, obj.new_plan.tier
            )
        elif obj.new_plan:
            return format_html('<strong>{}</strong>', obj.new_plan.tier)
        return '—'
    plan_change.short_description = 'Plan Change'

    def amount_display(self, obj):
        if not obj.amount_paid:
            return mark_safe('<span style="color: #6c757d;">—</span>')
        amount_formatted = f"{obj.amount_paid:,.0f}"
        return format_html('<strong>{} XAF</strong>', amount_formatted)
    amount_display.short_description = 'Amount'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'subscription__user', 'previous_plan', 'new_plan'
        )


# =============================================================================
# PAYMENT RECORD ADMIN
# =============================================================================

@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    """
    Payment History
    Track all mobile money payments for subscriptions
    """

    list_display = (
        'created_at',
        'user_email',
        'amount_display',
        'charge_type_badge',
        'status_badge',
        'momo_operator',
        'momo_phone_used',
        'transaction_id_short',
    )

    list_filter = (
        'status',
        'charge_type',
        'momo_operator',
        ('created_at', admin.DateFieldListFilter),
    )

    search_fields = (
        'user__email',
        'transaction_id',
        'reference',
        'momo_phone_used',
    )

    readonly_fields = (
        'id', 'user', 'subscription', 'payment_intent',
        'amount', 'reference', 'charge_type', 'momo_operator',
        'momo_phone_used', 'transaction_id', 'status',
        'raw_webhook_payload', 'created_at'
    )

    ordering = ('-created_at',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def amount_display(self, obj):
        amount_formatted = f"{obj.amount:,.0f}"
        return format_html('<strong>{} XAF</strong>', amount_formatted)
    amount_display.short_description = 'Amount'

    def charge_type_badge(self, obj):
        """Color-coded charge type"""
        colors = {
            'subscription': '#007bff',
            'subscription_renewal': '#28a745',
            'subscription_upgrade': '#17a2b8',
            'domain': '#6f42c1',
            'domain_renewal': '#6f42c1',
            'theme': '#fd7e14',
            'checkout': '#20c997',
            'addon': '#e83e8c',
            'other': '#6c757d',
        }
        color = colors.get(obj.charge_type, '#6c757d')
        label = obj.charge_type.replace('_', ' ').title()
        return format_html(
            '<span style="color: {};">{}</span>',
            color, label
        )
    charge_type_badge.short_description = 'Type'
    charge_type_badge.admin_order_field = 'charge_type'

    def status_badge(self, obj):
        colors = {'success': '#28a745', 'failed': '#dc3545', 'pending': '#ffc107'}
        color = colors.get(obj.status, '#6c757d')
        icon = {'success': '✓', 'failed': '✗', 'pending': '⏳'}.get(obj.status, '?')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def transaction_id_short(self, obj):
        if not obj.transaction_id:
            return '—'
        return obj.transaction_id[:12] + '...' if len(obj.transaction_id) > 12 else obj.transaction_id
    transaction_id_short.short_description = 'Transaction ID'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'subscription__plan', 'payment_intent'
        )


# =============================================================================
# EVENT LOG ADMIN
# =============================================================================

@admin.register(SubscriptionEventLog)
class SubscriptionEventLogAdmin(admin.ModelAdmin):
    """
    Subscription Event Audit Log
    Debug and audit subscription lifecycle events
    """

    list_display = (
        'created_at',
        'user_email',
        'event_type_badge',
        'description_short',
    )

    list_filter = (
        'event_type',
        ('created_at', admin.DateFieldListFilter),
    )

    search_fields = (
        'subscription__user__email',
        'user__email',
        'description',
    )

    readonly_fields = (
        'id', 'subscription', 'user', 'event_type',
        'description', 'metadata', 'created_at'
    )

    ordering = ('-created_at',)

    def user_email(self, obj):
        return obj.user.email if obj.user else '—'
    user_email.short_description = 'User'

    def event_type_badge(self, obj):
        """Color-coded event type"""
        colors = {
            'subscription_created': '#17a2b8',
            'subscription_activated': '#28a745',
            'subscription_expired': '#dc3545',
            'upgrade_initiated': '#007bff',
            'subscription_renewed': '#28a745',
            'subscription_downgraded': '#fd7e14',
            'subscription_cancelled': '#dc3545',
            'trial_converted': '#6f42c1',
            'payment_received': '#28a745',
            'payment_failed': '#dc3545',
            'plan_changed': '#17a2b8',
            'status_changed': '#6c757d',
            'grace_period_started': '#fd7e14',
            'downgrade_to_free': '#fd7e14',
            'provisioning_success': '#28a745',
            'provisioning_failed': '#dc3545',
        }
        color = colors.get(obj.event_type, '#6c757d')
        label = obj.event_type.replace('_', ' ').title()
        return format_html('<span style="color: {};">{}</span>', color, label)
    event_type_badge.short_description = 'Event'
    event_type_badge.admin_order_field = 'event_type'

    def description_short(self, obj):
        if len(obj.description) > 80:
            return obj.description[:80] + '...'
        return obj.description
    description_short.short_description = 'Description'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subscription', 'user')


# =============================================================================
# DEAD LETTER QUEUE ADMIN
# =============================================================================

@admin.register(SubscriptionDeadLetterQueue)
class SubscriptionDeadLetterQueueAdmin(admin.ModelAdmin):
    """
    Dead Letter Queue - Failed Subscription Operations
    ===================================================
    Monitor and retry failed subscription creations.
    
    🔴 CRITICAL: Check this regularly during launch!
    Any items here mean users couldn't complete their subscription.
    """

    list_display = (
        'created_at',
        'user_id_short',
        'task_type',
        'priority_badge',
        'retry_count',
        'processed_badge',
        'error_short',
    )

    list_filter = (
        'processed',
        'priority',
        'task_type',
        ('created_at', admin.DateFieldListFilter),
    )

    search_fields = (
        'user_id',
        'error_message',
        'original_failure_reason',
    )

    readonly_fields = (
        'id', 'user_id', 'task_type', 'error_message',
        'original_failure_reason', 'retry_count', 'priority',
        'created_at', 'updated_at'
    )

    fieldsets = (
        ('Status', {
            'fields': ('processed', 'processed_at', 'resolution_notes')
        }),
        ('Error Details', {
            'fields': ('user_id', 'task_type', 'priority', 'retry_count')
        }),
        ('Error Message', {
            'fields': ('error_message', 'original_failure_reason'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)
    actions = ['action_mark_processed', 'action_retry']

    def user_id_short(self, obj):
        """Look up user and show email instead of just UUID"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=obj.user_id)
            return format_html(
                '<strong>{}</strong><br><small style="color: #6c757d;">{}</small>',
                user.email,
                user.get_full_name() or 'No name'
            )
        except User.DoesNotExist:
            return format_html(
                '<span style="color: #dc3545;">User not found</span><br>'
                '<small>{}</small>',
                str(obj.user_id)[:8] + '...'
            )
    user_id_short.short_description = 'User'

    def priority_badge(self, obj):
        colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#6c757d',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.priority.upper()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'

    def processed_badge(self, obj):
        if obj.processed:
            return mark_safe(
                '<span style="color: #28a745;">✓ Processed</span>'
            )
        return mark_safe(
            '<span style="color: #dc3545; font-weight: bold;">⚠ PENDING</span>'
        )
    processed_badge.short_description = 'Status'
    processed_badge.admin_order_field = 'processed'

    def error_short(self, obj):
        if len(obj.error_message) > 50:
            return obj.error_message[:50] + '...'
        return obj.error_message
    error_short.short_description = 'Error'

    @admin.action(description='✅ Mark as Processed')
    def action_mark_processed(self, request, queryset):
        count = queryset.filter(processed=False).update(
            processed=True,
            processed_at=timezone.now(),
            resolution_notes=f'Manually marked processed by {request.user.email}'
        )
        self.message_user(request, f'Marked {count} item(s) as processed')

    @admin.action(description='🔄 Retry (Manual)')
    def action_retry(self, request, queryset):
        """
        Manual retry trigger - increments retry count
        Actual retry logic should be in a background task
        """
        count = 0
        for item in queryset.filter(processed=False):
            item.retry_count += 1
            item.save(update_fields=['retry_count', 'updated_at'])
            count += 1
            # TODO: Trigger actual retry via Celery/background task
        self.message_user(
            request,
            f'Incremented retry count for {count} item(s). '
            'Trigger background task to process.'
        )
