# Core Workspace Serializers - DRF serialization

from rest_framework import serializers
from ..models import Workspace, Membership, Role, AuditLog


class RoleSerializer(serializers.ModelSerializer):
    """Role serializer"""
    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions']
        read_only_fields = ['id', 'name']


class MembershipSerializer(serializers.ModelSerializer):
    """Membership serializer with user and role details"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    permissions = serializers.ListField(source='role.permissions', read_only=True)

    class Meta:
        model = Membership
        fields = [
            'id', 'user_id', 'user_email', 'user_name',
            'workspace', 'role', 'role_name', 'permissions', 'is_active',
            'joined_at'
        ]
        read_only_fields = ['joined_at']


class WorkspaceSerializer(serializers.ModelSerializer):
    """Workspace serializer with member count and user permissions"""
    member_count = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    provisioning_status = serializers.SerializerMethodField()
    deletion_info = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'id', 'name', 'slug', 'type', 'status', 'permissions',
            'member_count', 'domain', 'preview_url', 'provisioning_complete',
            'provisioning_status', 'deleted_at', 'deletion_scheduled_for',
            'deletion_info', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'status', 'provisioning_complete',
            'deleted_at', 'deletion_scheduled_for',
            'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        """Custom field names for frontend compatibility"""
        data = super().to_representation(instance)
        # Rename fields to match frontend interface
        data['createdAt'] = data.pop('created_at')
        data['updatedAt'] = data.pop('updated_at')
        data['provisioningComplete'] = data.pop('provisioning_complete')
        data['provisioningStatus'] = data.pop('provisioning_status')
        data['previewUrl'] = data.pop('preview_url')
        data['memberCount'] = data.pop('member_count')
        data['deletedAt'] = data.pop('deleted_at')
        data['deletionScheduledFor'] = data.pop('deletion_scheduled_for')
        data['deletionInfo'] = data.pop('deletion_info')
        return data

    def get_member_count(self, obj):
        """Get active member count"""
        try:
            return obj.memberships.filter(is_active=True).count()
        except:
            return 1  # Default to owner only

    def get_permissions(self, obj):
        """Get current user's permissions in workspace"""
        try:
            request = self.context.get('request')
            if not request or not request.user:
                return []

            user = request.user
            if obj.owner == user:
                return ['read', 'write', 'admin']

            membership = obj.memberships.filter(user=user, is_active=True).first()
            if membership and membership.role:
                return membership.role.permissions or ['read']
            return ['read']
        except:
            return ['read']

    def get_domain(self, obj):
        """Get workspace storefront domain"""
        try:
            if hasattr(obj, 'infrastructure') and obj.infrastructure:
                return obj.infrastructure.get_full_domain()
            return None
        except:
            return None

    def get_preview_url(self, obj):
        """Get workspace preview URL"""
        try:
            if hasattr(obj, 'infrastructure') and obj.infrastructure:
                return obj.infrastructure.get_preview_url()
            return None
        except:
            return None

    def get_provisioning_status(self, obj):
        """Get workspace provisioning status details"""
        try:
            if obj.provisioning_complete:
                return {'status': 'completed', 'message': 'Workspace ready'}

            if hasattr(obj, 'provisioning') and obj.provisioning:
                provisioning = obj.provisioning
                return {
                    'status': provisioning.status,
                    'message': self._get_status_message(provisioning.status)
                }

            return {'status': 'unknown', 'message': 'Setting up workspace'}
        except:
            return {'status': 'unknown', 'message': 'Setting up workspace'}

    def _get_status_message(self, status):
        """Get user-friendly status message"""
        messages = {
            'queued': 'Setting up your workspace...',
            'in_progress': 'Almost ready...',
            'completed': 'Workspace ready',
            'failed': 'Setup incomplete. Please retry.',
            'cancelled': 'Setup cancelled'
        }
        return messages.get(status, 'Setting up workspace')

    def get_deletion_info(self, obj):
        """Get workspace deletion information"""
        if obj.status != 'suspended' or not obj.deleted_at:
            return None

        from django.utils import timezone
        try:
            # Calculate days remaining in grace period
            if obj.deletion_scheduled_for:
                now = timezone.now()
                if now < obj.deletion_scheduled_for:
                    time_delta = obj.deletion_scheduled_for - now
                    days_remaining = time_delta.days
                    hours_remaining = time_delta.seconds // 3600

                    return {
                        'isDeleted': True,
                        'deletedAt': obj.deleted_at.isoformat(),
                        'scheduledFor': obj.deletion_scheduled_for.isoformat(),
                        'daysRemaining': days_remaining,
                        'hoursRemaining': hours_remaining,
                        'canRestore': True,
                        'gracePeriodDays': 5,
                        'message': f'Workspace will be permanently deleted in {days_remaining} days, {hours_remaining} hours'
                    }
                else:
                    return {
                        'isDeleted': True,
                        'deletedAt': obj.deleted_at.isoformat(),
                        'scheduledFor': obj.deletion_scheduled_for.isoformat(),
                        'daysRemaining': 0,
                        'hoursRemaining': 0,
                        'canRestore': False,
                        'gracePeriodDays': 5,
                        'message': 'Grace period expired. Deprovisioning in progress. Contact support for assistance.'
                    }

            return {
                'isDeleted': True,
                'deletedAt': obj.deleted_at.isoformat(),
                'canRestore': False,
                'message': 'Workspace is deleted'
            }
        except:
            return None


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'workspace', 'workspace_name', 'user', 'user_email',
            'action', 'resource_type', 'resource_id', 'description',
            'metadata', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['timestamp']