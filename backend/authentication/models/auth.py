"""
Authentication Models - Token management and session handling
"""
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .user import User


class RefreshToken(models.Model):
    """Secure refresh token management"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    
    # Token data
    token_hash = models.CharField(max_length=255, unique=True, db_index=True)
    jti = models.UUIDField(default=uuid.uuid4, unique=True)  # JWT ID for revocation
    
    # Metadata
    device_name = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Security
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.CharField(max_length=50, null=True, blank=True)  # 'user', 'admin', 'system'
    
    class Meta:
        db_table = 'auth_refresh_tokens'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['token_hash']),
        ]
    
    def __str__(self):
        return f"RefreshToken for {self.user.email} - {self.device_name}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def revoke(self, revoked_by='user'):
        """Revoke this refresh token"""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.save(update_fields=['is_active', 'revoked_at', 'revoked_by'])
    
    @classmethod
    def create_token(cls, user, token_hash, device_info=None, ip_address=None):
        """Create a new refresh token"""
        device_info = device_info or {}
        return cls.objects.create(
            user=user,
            token_hash=token_hash,
            device_name=device_info.get('device_name', '') if isinstance(device_info, dict) else '',
            user_agent=device_info.get('user_agent', '') if isinstance(device_info, dict) else '',
            ip_address=ip_address,
            expires_at=timezone.now() + timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)
        )
    
    @classmethod
    def cleanup_expired(cls):
        """Clean up expired tokens"""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).update(is_active=False, revoked_by='system', revoked_at=timezone.now())
        return expired_count