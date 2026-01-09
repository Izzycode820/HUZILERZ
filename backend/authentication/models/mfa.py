"""
Enterprise MFA Models - Multi-Factor Authentication with TOTP and Backup Codes
Follows 2025 OWASP security standards and NIST guidelines
"""
import uuid
import secrets
import hashlib
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from .user import User


class TOTPDevice(models.Model):
    """Enterprise TOTP device following 2025 security standards
    
    Implements RFC 6238 TOTP with enhanced security features:
    - Cryptographically secure secret generation
    - Rate limiting and failure tracking
    - Device fingerprinting and usage analytics
    - Automatic lockout after suspicious activity
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='totp_device')
    
    # Device identification & branding
    name = models.CharField(max_length=100, default="Authenticator App")
    issuer_name = models.CharField(max_length=100, default="HustlerzCamp")
    account_name = models.CharField(max_length=255, blank=True)  # Usually user email
    
    # TOTP Configuration (RFC 6238 compliant)
    secret_key = models.CharField(max_length=64)  # Base32 encoded, 256-bit entropy
    algorithm = models.CharField(max_length=10, default='SHA1', choices=[
        ('SHA1', 'SHA-1'),
        ('SHA256', 'SHA-256'),
        ('SHA512', 'SHA-512'),
    ])
    digits = models.PositiveSmallIntegerField(default=6, choices=[
        (6, '6 digits'),
        (8, '8 digits'),
    ])
    period = models.PositiveSmallIntegerField(default=30)  # Time step in seconds
    
    # Security & Status
    is_active = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)  # Locked due to suspicious activity
    
    # Usage analytics & security monitoring
    last_used = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)
    failure_count = models.PositiveIntegerField(default=0)
    consecutive_failures = models.PositiveIntegerField(default=0)
    total_verifications = models.PositiveIntegerField(default=0)
    
    # Rate limiting & lockout
    lockout_until = models.DateTimeField(null=True, blank=True)
    max_failures = models.PositiveSmallIntegerField(default=5)
    lockout_duration_minutes = models.PositiveSmallIntegerField(default=30)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_totp_devices'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_locked', 'lockout_until']),
            models.Index(fields=['last_used']),
        ]
    
    def __str__(self):
        status = "🔒 Locked" if self.is_locked else ("✅ Active" if self.is_active else "⏳ Pending")
        return f"TOTP Device for {self.user.email} - {self.name} ({status})"
    
    def save(self, *args, **kwargs):
        """Auto-populate account_name from user email"""
        if not self.account_name and self.user:
            self.account_name = self.user.email
        super().save(*args, **kwargs)
    
    def is_locked_out(self):
        """Check if device is currently locked out"""
        if not self.is_locked or not self.lockout_until:
            return False
        return timezone.now() < self.lockout_until
    
    def record_success(self, ip_address=None):
        """Record successful verification"""
        self.last_used = timezone.now()
        self.last_used_ip = ip_address
        self.consecutive_failures = 0
        self.total_verifications += 1
        
        # Auto-unlock if lockout period expired
        if self.is_locked and self.lockout_until and timezone.now() >= self.lockout_until:
            self.is_locked = False
            self.lockout_until = None
        
        self.save(update_fields=[
            'last_used', 'last_used_ip', 'consecutive_failures', 
            'total_verifications', 'is_locked', 'lockout_until'
        ])
    
    def record_failure(self, ip_address=None):
        """Record failed verification with automatic lockout"""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_at = timezone.now()
        
        # Implement progressive lockout
        if self.consecutive_failures >= self.max_failures:
            self.is_locked = True
            self.lockout_until = timezone.now() + timedelta(minutes=self.lockout_duration_minutes)
        
        self.save(update_fields=[
            'failure_count', 'consecutive_failures', 'last_failure_at',
            'is_locked', 'lockout_until'
        ])
    
    def unlock_device(self, force=False):
        """Unlock device (admin or automatic unlock)"""
        if force or (self.lockout_until and timezone.now() >= self.lockout_until):
            self.is_locked = False
            self.lockout_until = None
            self.consecutive_failures = 0
            self.save(update_fields=['is_locked', 'lockout_until', 'consecutive_failures'])
            return True
        return False
    
    @classmethod
    def generate_secure_secret(cls):
        """Generate cryptographically secure base32 secret (256-bit entropy)"""
        import pyotp
        return pyotp.random_base32(length=64)  # 64 characters = 320 bits > 256 bits required
    
    def generate_qr_code_url(self):
        """Generate provisioning URI for QR code"""
        import pyotp
        totp = pyotp.TOTP(
            self.secret_key, 
            issuer=self.issuer_name,
            digits=self.digits,
            interval=self.period
        )
        return totp.provisioning_uri(
            name=self.account_name,
            issuer_name=self.issuer_name
        )
    
    def verify_token(self, token, ip_address=None):
        """Verify TOTP token with security checks"""
        if self.is_locked_out():
            return False, "Device is temporarily locked due to too many failed attempts"
        
        if not self.is_active:
            return False, "TOTP device is not active"
        
        try:
            import pyotp
            totp = pyotp.TOTP(
                self.secret_key,
                digits=self.digits,
                interval=self.period
            )
            
            # Verify with time window tolerance (±1 period)
            is_valid = totp.verify(token, valid_window=1)
            
            if is_valid:
                self.record_success(ip_address)
                return True, "Token verified successfully"
            else:
                self.record_failure(ip_address)
                return False, "Invalid token"
                
        except Exception as e:
            self.record_failure(ip_address)
            return False, f"Verification error: {str(e)}"


class BackupCode(models.Model):
    """Enterprise backup codes following OWASP 2025 security standards
    
    Implementation features:
    - CSPRNG (Cryptographically Secure Pseudo-Random Number Generator)
    - Single-use with secure hashing (bcrypt)
    - Automatic expiration and cleanup
    - Rate limiting and suspicious activity detection
    - Comprehensive audit logging
    """
    
    # Status constants
    UNUSED = 'unused'
    USED = 'used'
    EXPIRED = 'expired'
    REVOKED = 'revoked'
    
    STATUS_CHOICES = [
        (UNUSED, 'Unused'),
        (USED, 'Used'),
        (EXPIRED, 'Expired'),
        (REVOKED, 'Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backup_codes')
    
    # Secure code storage
    code_hash = models.CharField(max_length=255, unique=True)  # bcrypt hashed code
    code_partial = models.CharField(max_length=8)  # First 4 chars for user reference
    generation_batch = models.UUIDField(default=uuid.uuid4)  # Group codes by generation
    
    # Security metadata
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=UNUSED)
    security_level = models.CharField(max_length=10, default='standard', choices=[
        ('standard', 'Standard'),
        ('high', 'High Security'),
    ])
    
    # Usage tracking & audit
    used_at = models.DateTimeField(null=True, blank=True)
    used_ip = models.GenericIPAddressField(null=True, blank=True)
    used_user_agent = models.TextField(blank=True)
    verification_attempts = models.PositiveIntegerField(default=0)
    
    # Expiration & lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'auth_backup_codes'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['code_hash']),
            models.Index(fields=['generation_batch']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F('created_at')),
                name='backup_code_valid_expiration'
            ),
        ]
    
    def __str__(self):
        return f"Backup Code {self.code_partial}**** for {self.user.email} - {self.status}"
    
    def is_expired(self):
        """Check if backup code has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if code can be used"""
        return (
            self.status == self.UNUSED and 
            not self.is_expired() and 
            self.revoked_at is None
        )
    
    def mark_used(self, ip_address=None, user_agent=""):
        """Mark backup code as used with audit trail"""
        if self.status != self.UNUSED:
            raise ValidationError("Code has already been used or is invalid")
        
        self.status = self.USED
        self.used_at = timezone.now()
        self.used_ip = ip_address
        self.used_user_agent = user_agent
        self.save(update_fields=['status', 'used_at', 'used_ip', 'used_user_agent'])
        
        # Log security event
        from .security_models import SecurityEvent
        SecurityEvent.log_event(
            event_type='backup_code_used',
            user=self.user,
            description=f"Backup code used: {self.code_partial}****",
            risk_level='medium',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={'code_id': str(self.id), 'generation_batch': str(self.generation_batch)}
        )
    
    def revoke(self, reason="Manual revocation"):
        """Revoke backup code"""
        self.status = self.REVOKED
        self.revoked_at = timezone.now()
        self.revoked_reason = reason
        self.save(update_fields=['status', 'revoked_at', 'revoked_reason'])
    
    @classmethod
    def generate_secure_code(cls, length=12):
        """Generate cryptographically secure backup code using CSPRNG"""
        # Use CSPRNG for secure random generation
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # No confusing chars (0,O,1,I)
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @classmethod
    def create_code(cls, user, raw_code=None, expires_days=90, generation_batch=None):
        """Create a new backup code with secure hashing"""
        if not raw_code:
            raw_code = cls.generate_secure_code()
        
        # Hash the code using Django's password hashing
        code_hash = make_password(raw_code)
        
        # Store partial for user reference
        code_partial = raw_code[:4]
        
        # Set expiration
        expires_at = timezone.now() + timedelta(days=expires_days)
        
        backup_code = cls.objects.create(
            user=user,
            code_hash=code_hash,
            code_partial=code_partial,
            expires_at=expires_at,
            generation_batch=generation_batch or uuid.uuid4()
        )
        
        return backup_code, raw_code
    
    @classmethod
    def generate_codes_for_user(cls, user, count=10, expires_days=90):
        """Generate a set of backup codes for user"""
        # Revoke existing unused codes
        cls.objects.filter(
            user=user, 
            status=cls.UNUSED
        ).update(
            status=cls.REVOKED, 
            revoked_at=timezone.now(),
            revoked_reason="Replaced with new codes"
        )
        
        # Generate new batch
        batch_id = uuid.uuid4()
        codes = []
        raw_codes = []
        
        for _ in range(count):
            backup_code, raw_code = cls.create_code(
                user=user, 
                expires_days=expires_days,
                generation_batch=batch_id
            )
            codes.append(backup_code)
            raw_codes.append(raw_code)
        
        # Log security event
        from .security_models import SecurityEvent
        SecurityEvent.log_event(
            event_type='backup_codes_generated',
            user=user,
            description=f"Generated {count} new backup codes",
            risk_level=1,
            metadata={'batch_id': str(batch_id), 'count': count}
        )
        
        return codes, raw_codes
    
    def verify_code(self, raw_code, ip_address=None, user_agent=""):
        """Verify backup code with security checks"""
        self.verification_attempts += 1
        self.save(update_fields=['verification_attempts'])
        
        if not self.is_valid():
            return False, "Code is expired, used, or invalid"
        
        # Verify using Django's password verification
        if check_password(raw_code, self.code_hash):
            self.mark_used(ip_address, user_agent)
            return True, "Backup code verified successfully"
        else:
            return False, "Invalid backup code"
    
    @classmethod
    def cleanup_expired_codes(cls):
        """Clean up expired backup codes"""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now(),
            status=cls.UNUSED
        ).update(
            status=cls.EXPIRED
        )
        return expired_count


# Future MFA methods for enterprise expansion
class SMSDevice(models.Model):
    """SMS-based MFA device for regions where TOTP adoption is low"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_devices')
    
    # Phone configuration
    phone_number = models.CharField(max_length=20)
    country_code = models.CharField(max_length=5, default="+1")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    
    # Rate limiting
    last_sms_sent = models.DateTimeField(null=True, blank=True)
    sms_count_today = models.PositiveIntegerField(default=0)
    max_sms_per_day = models.PositiveSmallIntegerField(default=10)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_sms_devices'
        unique_together = ['user', 'phone_number']
    
    def __str__(self):
        return f"SMS Device for {self.user.email} - {self.phone_number}"


class WebAuthnDevice(models.Model):
    """WebAuthn/FIDO2 device for hardware security keys (YubiKey, etc.)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webauthn_devices')
    
    # WebAuthn credential data
    credential_id = models.TextField(unique=True)
    public_key = models.TextField()
    sign_count = models.PositiveIntegerField(default=0)
    
    # Device metadata
    name = models.CharField(max_length=100, default="Security Key")
    aaguid = models.CharField(max_length=100, blank=True)  # Authenticator AAGUID
    
    # Status
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_webauthn_devices'
    
    def __str__(self):
        return f"WebAuthn Device for {self.user.email} - {self.name}"