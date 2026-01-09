"""
Django Admin Configuration for Authentication App
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from .models import User, RefreshToken, UserSession
# Note: SecurityEvent has been moved to security_models and redesigned


class SubscriptionInline(admin.StackedInline):
    """Inline subscription details for user"""
    from subscription.models import Subscription
    model = Subscription
    extra = 0
    can_delete = False
    readonly_fields = (
        'plan_link', 'status', 'billing_cycle', 'started_at',
        'expires_at', 'last_manual_renewal', 'days_remaining'
    )
    fields = (
        'plan_link', 'status', 'billing_cycle', 'started_at',
        'expires_at', 'last_manual_renewal', 'days_remaining'
    )

    def plan_link(self, obj):
        if not obj or not obj.plan:
            return 'No plan'
        url = reverse('admin:subscription_subscription_change', args=[obj.id])
        return format_html(
            '<a href="{}">{} ({})</a>',
            url, obj.plan.name, obj.plan.tier
        )
    plan_link.short_description = 'Plan'

    def days_remaining(self, obj):
        if not obj:
            return '-'
        days = obj.days_until_expiry
        if days is None:
            return 'Never (Free)'
        if days == 0:
            return format_html('<span style="color: red;">EXPIRED</span>')
        if days <= 5:
            return format_html('<span style="color: orange;">{} days</span>', days)
        return f'{days} days'
    days_remaining.short_description = 'Days Left'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User Admin with modern authentication fields"""

    list_display = (
        'email', 'username', 'first_name', 'last_name',
        'subscription_status', 'is_active', 'email_verified',
        'two_factor_enabled', 'created_at', 'last_login'
    )
    
    list_filter = (
        'is_active', 'is_staff', 'is_superuser',
        'email_verified', 'phone_verified', 'two_factor_enabled',
        'preferred_auth_method', 'created_at'
    )
    
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'avatar', 'bio', 'phone_number')
        }),
        ('Verification Status', {
            'fields': ('email_verified', 'phone_verified')
        }),
        ('Security Settings', {
            'fields': ('two_factor_enabled', 'preferred_auth_method', 'security_notifications')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'password_changed_at', 'created_at')
        }),
        ('Guest Conversion', {
            'fields': ('is_guest_converted', 'guest_actions_count')
        }),
    )
    
    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('created_at', 'password_changed_at', 'last_login')

    inlines = [SubscriptionInline]

    actions = ['activate_users', 'deactivate_users', 'reset_2fa', 'delete_users_with_cleanup']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subscription', 'subscription__plan')

    def subscription_status(self, obj):
        try:
            subscription = obj.subscription
            if not subscription or not subscription.plan:
                return format_html('<span style="color: gray;">{}</span>', 'No subscription')

            status_colors = {
                'active': 'green',
                'pending_payment': 'orange',
                'grace_period': 'orange',
                'expired': 'red',
                'suspended': 'gray',
                'cancelled': 'gray',
            }
            color = status_colors.get(subscription.status, 'gray')

            url = reverse('admin:subscription_subscription_change', args=[subscription.id])
            return format_html(
                '<a href="{}" style="color: {}; font-weight: bold;">{} - {}</a>',
                url, color, subscription.plan.tier.upper(), subscription.status.upper()
            )
        except Exception:
            return format_html('<span style="color: gray;">{}</span>', 'No subscription')
    subscription_status.short_description = 'Subscription'

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def reset_2fa(self, request, queryset):
        updated = queryset.update(two_factor_enabled=False)
        self.message_user(request, f'2FA reset for {updated} users.')
    reset_2fa.short_description = 'Reset 2FA for selected users'

    def delete_users_with_cleanup(self, request, queryset):
        """
        Delete users with CASCADE cleanup
        DeployedSite has PROTECT on hosting_environment to prevent accidental data loss
        """
        from django.db import transaction
        from django.db.models.deletion import ProtectedError

        users_to_delete = list(queryset.values_list('id', 'email'))
        total_users = len(users_to_delete)

        if not total_users:
            self.message_user(request, 'No users selected.', level='warning')
            return

        deleted_count = 0
        failed_users = []

        for user_id, email in users_to_delete:
            try:
                with transaction.atomic():
                    user = queryset.get(id=user_id)
                    user.delete()
                    deleted_count += 1

            except ProtectedError as e:
                failed_users.append(f"{email} (has active deployments - delete sites first)")
            except Exception as e:
                failed_users.append(f"{email} ({str(e)})")
                continue

        # Show results
        if deleted_count > 0:
            self.message_user(
                request,
                f'Deleted {deleted_count} user(s)',
                level='success'
            )

        if failed_users:
            self.message_user(
                request,
                f'Failed: {", ".join(failed_users)}',
                level='error'
            )

    delete_users_with_cleanup.short_description = 'Delete selected users (with cleanup)'

    def delete_queryset(self, request, queryset):
        """
        Override default delete action to use our custom cleanup logic
        This is called when admin uses 'Delete selected users' action
        """
        self.delete_users_with_cleanup(request, queryset)


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """Refresh Token Management"""
    
    list_display = (
        'id', 'user_email', 'device_name', 'ip_address',
        'is_active_status', 'last_used', 'expires_at'
    )
    
    list_filter = (
        'is_active', 'created_at', 'expires_at', 'revoked_by'
    )
    
    search_fields = (
        'user__email', 'user__username', 'device_name',
        'ip_address', 'user_agent'
    )
    
    readonly_fields = (
        'token_hash', 'jti', 'created_at', 'last_used',
        'revoked_at', 'revoked_by'
    )
    
    ordering = ('-created_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def is_active_status(self, obj):
        if obj.is_active and not obj.is_expired():
            return format_html('<span style="color: green;">●</span> Active')
        elif obj.is_expired():
            return format_html('<span style="color: red;">●</span> Expired')
        else:
            return format_html('<span style="color: orange;">●</span> Revoked')
    is_active_status.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['revoke_tokens', 'cleanup_expired_tokens']
    
    def revoke_tokens(self, request, queryset):
        updated = queryset.filter(is_active=True).update(
            is_active=False,
            revoked_by='admin',
            revoked_at=timezone.now()
        )
        self.message_user(request, f'{updated} tokens revoked.')
    revoke_tokens.short_description = 'Revoke selected tokens'
    
    def cleanup_expired_tokens(self, request, queryset):
        updated = RefreshToken.cleanup_expired()
        self.message_user(request, f'{updated} expired tokens cleaned up.')
    cleanup_expired_tokens.short_description = 'Cleanup expired tokens'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User Session Analytics"""
    
    list_display = (
        'session_key_short', 'user_info', 'device_type', 'browser',
        'is_authenticated', 'page_views', 'actions_count',
        'converted_status', 'created_at'
    )
    
    list_filter = (
        'is_authenticated', 'device_type', 'browser',
        'converted_to_user', 'authentication_method',
        'conversion_trigger', 'created_at'
    )
    
    search_fields = (
        'user__email', 'session_key', 'ip_address', 'location'
    )
    
    readonly_fields = (
        'session_key', 'fingerprint', 'created_at',
        'last_activity', 'ended_at'
    )
    
    ordering = ('-created_at',)
    
    def session_key_short(self, obj):
        return f"{obj.session_key[:8]}..."
    session_key_short.short_description = 'Session'
    
    def user_info(self, obj):
        if obj.user:
            return obj.user.email
        return "Guest User"
    user_info.short_description = 'User'
    
    def converted_status(self, obj):
        if obj.converted_to_user:
            return format_html('<span style="color: green;">✓ Converted</span>')
        elif obj.showed_auth_prompt:
            return format_html('<span style="color: orange;">⚠ Prompted</span>')
        else:
            return format_html('<span style="color: gray;">- Not Prompted</span>')
    converted_status.short_description = 'Conversion'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['end_sessions']
    
    def end_sessions(self, request, queryset):
        updated = queryset.update(ended_at=timezone.now())
        self.message_user(request, f'{updated} sessions ended.')
    end_sessions.short_description = 'End selected sessions'


# SecurityEvent admin moved to security_models - will be registered separately
# The new SecurityEvent model has different fields and enhanced security features


# Add workspace admin integration
from workspace.core.models import Workspace, Membership, Role


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    """Workspace Management"""
    
    list_display = (
        'name', 'type', 'owner_email', 'status', 
        'member_count', 'created_at'
    )
    
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('name', 'owner__email', 'slug')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def owner_email(self, obj):
        return obj.owner.email
    owner_email.short_description = 'Owner'
    
    def member_count(self, obj):
        return obj.memberships.count()
    member_count.short_description = 'Members'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """Workspace Membership Management"""

    list_display = (
        'user_email', 'workspace_name', 'role_name',
        'status', 'joined_at'
    )

    list_filter = ('status', 'joined_at')
    search_fields = ('user__email', 'workspace__name')
    readonly_fields = ('joined_at', 'updated_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def workspace_name(self, obj):
        return obj.workspace.name
    workspace_name.short_description = 'Workspace'

    def role_name(self, obj):
        role = obj.roles.first()
        return role.name if role else 'No role'
    role_name.short_description = 'Role'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'workspace').prefetch_related('roles')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Role Management"""

    list_display = ('name', 'workspace_name', 'is_system', 'permission_count', 'created_at')
    list_filter = ('is_system', 'created_at')
    search_fields = ('name', 'workspace__name')
    readonly_fields = ('created_at', 'updated_at')

    def workspace_name(self, obj):
        return obj.workspace.name if obj.workspace else 'System Role'
    workspace_name.short_description = 'Workspace'

    def permission_count(self, obj):
        from workspace.core.models import RolePermission
        return RolePermission.objects.filter(role=obj).count()
    permission_count.short_description = 'Permissions'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('workspace')


# Customize admin site
admin.site.site_header = "HustlerzCamp Authentication Admin"
admin.site.site_title = "HustlerzCamp Admin"
admin.site.index_title = "Authentication & Security Management"