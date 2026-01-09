# AuditLog Model - Activity tracking for workspaces

import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Audit log for tracking all critical actions within workspaces
    Provides comprehensive activity tracking and compliance
    """
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('invite', 'Invite User'),
        ('remove', 'Remove User'),
        ('role_change', 'Role Change'),
        ('settings_change', 'Settings Change'),
        ('billing_change', 'Billing Change'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace_core.Workspace', on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    
    # Action details
    action = models.CharField(max_length=50, choices=ACTION_TYPES, help_text="Type of action performed")
    resource_type = models.CharField(max_length=100, blank=True, help_text="Type of resource affected")
    resource_id = models.CharField(max_length=255, blank=True, help_text="ID of affected resource")
    
    # Additional context
    description = models.TextField(blank=True, help_text="Human-readable description of the action")
    metadata = models.JSONField(default=dict, help_text="Additional action metadata")
    
    # Request context
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="IP address of the user")
    user_agent = models.TextField(blank=True, help_text="Browser user agent")
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['workspace', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['resource_type', '-timestamp']),
        ]
    
    def __str__(self):
        user_info = f"{self.user.email}" if self.user else "System"
        return f"{user_info} - {self.get_action_display()} - {self.workspace.name}"
    
    @classmethod
    def log_action(cls, workspace, user, action, resource_type=None, resource_id=None, 
                   description=None, metadata=None, request=None):
        """
        Convenience method to create audit log entries
        
        Args:
            workspace: Workspace instance
            user: User instance (can be None for system actions)
            action: Action type from ACTION_TYPES
            resource_type: Optional resource type
            resource_id: Optional resource ID
            description: Optional human-readable description
            metadata: Optional additional data
            request: Optional request object for IP and user agent
        """
        log_data = {
            'workspace': workspace,
            'user': user,
            'action': action,
            'resource_type': resource_type or '',
            'resource_id': resource_id or '',
            'description': description or '',
            'metadata': metadata or {},
        }
        
        if request:
            log_data['ip_address'] = cls._get_client_ip(request)
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(**log_data)
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_user_display(self):
        """Get display name for the user"""
        if self.user:
            return f"{self.user.get_full_name() or self.user.email}"
        return "System"