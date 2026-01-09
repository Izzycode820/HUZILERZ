"""
Security and Monitoring Models - Enterprise 2025 Standards
Models for comprehensive security event tracking and audit logging
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import validate_ipv46_address
import json

User = get_user_model()


class SecurityEvent(models.Model):
    """
    Comprehensive security event logging model
    """
    
    # Event types
    EVENT_TYPE_CHOICES = [
        # Authentication events
        ('LOGIN_SUCCESS', 'Successful login'),
        ('LOGIN_FAILED', 'Failed login attempt'),
        ('LOGIN_SUSPICIOUS', 'Suspicious login detected'),
        ('LOGOUT', 'User logout'),
        ('SESSION_EXPIRED', 'Session expired'),
        ('SESSION_REVOKED', 'Session manually revoked'),
        
        # MFA events
        ('MFA_SETUP', 'MFA device setup'),
        ('MFA_SUCCESS', 'MFA verification success'),
        ('MFA_FAILED', 'MFA verification failed'),
        ('MFA_LOCKOUT', 'MFA device locked out'),
        ('MFA_BACKUP_USED', 'Backup code used'),
        ('MFA_DISABLED', 'MFA disabled'),
        
        # Token events
        ('TOKEN_ISSUED', 'JWT token issued'),
        ('TOKEN_REFRESHED', 'JWT token refreshed'),
        ('TOKEN_BLACKLISTED', 'Token blacklisted'),
        ('TOKEN_REUSE_DETECTED', 'Refresh token reuse detected'),
        ('TOKEN_FAMILY_INVALIDATED', 'Token family invalidated'),
        
        # OAuth2 events
        ('OAUTH2_SUCCESS', 'OAuth2 authentication success'),
        ('OAUTH2_FAILED', 'OAuth2 authentication failed'),
        ('OAUTH2_ACCOUNT_LINKED', 'OAuth2 account linked'),
        
        # Email events
        ('EMAIL_VERIFICATION_SENT', 'Email verification code sent'),
        ('EMAIL_VERIFICATION_SUCCESS', 'Email verification success'),
        ('EMAIL_VERIFICATION_FAILED', 'Email verification failed'),
        ('PASSWORD_RESET_REQUESTED', 'Password reset requested'),
        ('PASSWORD_RESET_SUCCESS', 'Password reset completed'),
        
        # Security threats
        ('BRUTE_FORCE_DETECTED', 'Brute force attack detected'),
        ('RATE_LIMIT_EXCEEDED', 'Rate limit exceeded'),
        ('SUSPICIOUS_LOCATION', 'Login from suspicious location'),
        ('DEVICE_CHANGE_DETECTED', 'New device detected'),
        ('CONCURRENT_SESSION_LIMIT', 'Concurrent session limit reached'),
        
        # System events
        ('SECURITY_POLICY_CHANGED', 'Security policy updated'),
        ('ADMIN_ACTION', 'Administrative security action'),
        ('SYSTEM_ANOMALY', 'System security anomaly detected')
    ]
    
    # Risk levels
    RISK_LEVEL_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Event details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    event_description = models.CharField(max_length=255, default='Security event')
    risk_level = models.IntegerField(choices=RISK_LEVEL_CHOICES, default=1)
    
    # User context
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='security_events'
    )
    
    # Request context
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        validators=[validate_ipv46_address]
    )
    user_agent = models.TextField(null=True, blank=True)
    device_fingerprint = models.CharField(max_length=64, null=True, blank=True)
    
    # Location information
    location_info = models.JSONField(null=True, blank=True)  # Store GeoIP data
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_security_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['risk_level', 'timestamp']),
            models.Index(fields=['device_fingerprint']),
        ]
    
    def __str__(self):
        user_info = f" ({self.user.username})" if self.user else ""
        return f"{self.event_type}{user_info} - {self.timestamp}"
    
    @property
    def risk_level_display(self):
        """Get human-readable risk level"""
        return dict(self.RISK_LEVEL_CHOICES).get(self.risk_level, 'Unknown')
    
    @property
    def event_category(self):
        """Get event category based on event type"""
        if self.event_type.startswith('LOGIN'):
            return 'Authentication'
        elif self.event_type.startswith('MFA'):
            return 'Multi-Factor Authentication'
        elif self.event_type.startswith('TOKEN'):
            return 'Token Management'
        elif self.event_type.startswith('OAUTH2'):
            return 'OAuth2'
        elif self.event_type.startswith('EMAIL'):
            return 'Email Authentication'
        elif self.event_type in ['BRUTE_FORCE_DETECTED', 'RATE_LIMIT_EXCEEDED', 'SUSPICIOUS_LOCATION']:
            return 'Security Threat'
        else:
            return 'System'
    
    def mark_processed(self):
        """Mark event as processed"""
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['is_processed', 'processed_at'])
    
    @classmethod
    def log_event(cls, event_type, user=None, request=None, description=None, risk_level=1, **metadata):
        """
        Log a security event
        """
        event_data = {
            'event_type': event_type,
            'event_description': description or dict(cls.EVENT_TYPE_CHOICES).get(event_type, 'Security event'),
            'risk_level': risk_level,
            'user': user,
            'metadata': metadata
        }
        
        if request:
            event_data.update({
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
            })
        
        return cls.objects.create(**event_data)


class SessionInfo(models.Model):
    """
    Enhanced session information for security monitoring
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.UUIDField(unique=True, db_index=True)
    
    # User context
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='session_info'
    )
    
    # Session details
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    # Device and location
    ip_address = models.GenericIPAddressField(validators=[validate_ipv46_address])
    user_agent = models.TextField()
    device_fingerprint = models.CharField(max_length=64, db_index=True)
    device_info = models.JSONField(default=dict, blank=True)
    
    # Location information
    location_info = models.JSONField(null=True, blank=True)
    
    # MFA status
    mfa_verified = models.BooleanField(default=False)
    mfa_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Security flags
    is_suspicious = models.BooleanField(default=False)
    security_flags = models.JSONField(default=list, blank=True)
    
    # Token family for coordinated invalidation
    token_family = models.UUIDField(null=True, blank=True, db_index=True)
    
    class Meta:
        db_table = 'auth_session_info'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_id', 'is_active']),
            models.Index(fields=['token_family']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id} - {self.user.username}"
    
    def is_expired(self):
        """Check if session is expired"""
        return timezone.now() > self.expires_at
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def mark_suspicious(self, flags=None):
        """Mark session as suspicious"""
        self.is_suspicious = True
        if flags:
            self.security_flags.extend(flags)
        self.save(update_fields=['is_suspicious', 'security_flags'])
    
    def revoke(self):
        """Revoke session"""
        self.is_active = False
        self.save(update_fields=['is_active'])


class SecurityAlert(models.Model):
    """
    Security alerts and notifications
    """
    
    ALERT_TYPE_CHOICES = [
        ('BRUTE_FORCE', 'Brute Force Attack'),
        ('SUSPICIOUS_LOGIN', 'Suspicious Login'),
        ('MFA_COMPROMISE', 'MFA Compromise'),
        ('TOKEN_THEFT', 'Token Theft'),
        ('ACCOUNT_TAKEOVER', 'Account Takeover'),
        ('SYSTEM_ANOMALY', 'System Anomaly'),
        ('POLICY_VIOLATION', 'Policy Violation')
    ]
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical')
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Alert details
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # Context
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='security_alerts'
    )
    
    # Related events
    related_events = models.ManyToManyField(
        SecurityEvent,
        blank=True,
        related_name='alerts'
    )
    
    # Alert data
    alert_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_alerts'
    )
    
    class Meta:
        db_table = 'auth_security_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['alert_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.title}"
    
    def resolve(self, resolved_by=None, notes=None):
        """Resolve the alert"""
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        if notes:
            self.alert_data['resolution_notes'] = notes
        if resolved_by:
            self.alert_data['resolved_by'] = resolved_by.username
        self.save()


class AuditLog(models.Model):
    """
    Comprehensive audit logging for compliance
    """
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PERMISSION_CHANGE', 'Permission Change'),
        ('CONFIG_CHANGE', 'Configuration Change')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Action details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100)  # What was acted upon
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    
    # User context
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auth_audit_logs'  # Unique related_name to avoid clashes
    )
    
    # Request context
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        validators=[validate_ipv46_address]
    )
    user_agent = models.TextField(null=True, blank=True)
    
    # Change details
    changes = models.JSONField(default=dict, blank=True)  # Before/after values
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'auth_audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource', 'timestamp']),
        ]
    
    def __str__(self):
        user_info = f" by {self.user.username}" if self.user else ""
        return f"{self.action} {self.resource}{user_info} - {self.timestamp}"


class ThreatIntelligence(models.Model):
    """
    Threat intelligence and IOCs (Indicators of Compromise)
    """
    
    IOC_TYPE_CHOICES = [
        ('IP', 'IP Address'),
        ('DOMAIN', 'Domain'),
        ('EMAIL', 'Email Address'),
        ('USER_AGENT', 'User Agent'),
        ('HASH', 'Hash'),
        ('URL', 'URL')
    ]
    
    THREAT_TYPE_CHOICES = [
        ('MALWARE', 'Malware'),
        ('PHISHING', 'Phishing'),
        ('BOTNET', 'Botnet'),
        ('BRUTE_FORCE', 'Brute Force'),
        ('CREDENTIAL_STUFFING', 'Credential Stuffing'),
        ('SUSPICIOUS_BEHAVIOR', 'Suspicious Behavior')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # IOC details
    ioc_type = models.CharField(max_length=20, choices=IOC_TYPE_CHOICES)
    ioc_value = models.CharField(max_length=255, db_index=True)
    threat_type = models.CharField(max_length=30, choices=THREAT_TYPE_CHOICES)
    
    # Threat information
    description = models.TextField()
    severity = models.IntegerField(choices=SecurityEvent.RISK_LEVEL_CHOICES)
    confidence = models.IntegerField(default=50)  # 0-100
    
    # Source information
    source = models.CharField(max_length=100)  # Where the intel came from
    source_url = models.URLField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'auth_threat_intelligence'
        unique_together = [['ioc_type', 'ioc_value']]
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['ioc_type', 'ioc_value']),
            models.Index(fields=['threat_type', 'is_active']),
            models.Index(fields=['severity', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.ioc_type}: {self.ioc_value} ({self.threat_type})"
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class SecurityMetrics(models.Model):
    """
    Security metrics aggregation for dashboards and reporting
    """
    
    METRIC_TYPE_CHOICES = [
        ('LOGIN_ATTEMPTS', 'Login Attempts'),
        ('LOGIN_SUCCESS', 'Successful Logins'),
        ('LOGIN_FAILED', 'Failed Logins'),
        ('MFA_USAGE', 'MFA Usage'),
        ('SUSPICIOUS_ACTIVITIES', 'Suspicious Activities'),
        ('SECURITY_ALERTS', 'Security Alerts'),
        ('UNIQUE_USERS', 'Unique Users'),
        ('UNIQUE_IPS', 'Unique IP Addresses')
    ]
    
    AGGREGATION_PERIOD_CHOICES = [
        ('HOURLY', 'Hourly'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Metric details
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES)
    aggregation_period = models.CharField(max_length=20, choices=AGGREGATION_PERIOD_CHOICES)
    
    # Time period
    period_start = models.DateTimeField(db_index=True)
    period_end = models.DateTimeField()
    
    # Metric values
    count = models.BigIntegerField(default=0)
    
    # Additional data
    breakdown = models.JSONField(default=dict, blank=True)  # Detailed breakdown
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_security_metrics'
        unique_together = [['metric_type', 'aggregation_period', 'period_start']]
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['metric_type', 'period_start']),
            models.Index(fields=['aggregation_period', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.metric_type} ({self.aggregation_period}) - {self.period_start.date()}: {self.count}"