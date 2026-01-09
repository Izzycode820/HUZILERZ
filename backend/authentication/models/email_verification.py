"""
Email Verification and Password Reset Models - 2025 Security Standards
Handles email OTP verification, password reset tokens, and email-based authentication
"""
import uuid
import secrets
import hashlib
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from .user import User


class EmailVerificationCode(models.Model):
    """
    Email OTP verification codes for account verification and authentication
    
    Features:
    - CSPRNG-generated codes
    - Rate limiting and attempt tracking
    - Automatic expiration and cleanup
    - Secure hashing with bcrypt
    - Anti-bruteforce protection
    """
    
    # Code types
    ACCOUNT_VERIFICATION = 'account_verification'
    PASSWORD_RESET = 'password_reset'
    EMAIL_CHANGE = 'email_change'
    LOGIN_VERIFICATION = 'login_verification'
    
    CODE_TYPES = [
        (ACCOUNT_VERIFICATION, 'Account Verification'),
        (PASSWORD_RESET, 'Password Reset'),
        (EMAIL_CHANGE, 'Email Change'),
        (LOGIN_VERIFICATION, 'Login Verification'),
    ]
    
    # Status choices
    PENDING = 'pending'
    VERIFIED = 'verified'
    EXPIRED = 'expired'
    REVOKED = 'revoked'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (VERIFIED, 'Verified'),
        (EXPIRED, 'Expired'),
        (REVOKED, 'Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_codes', null=True, blank=True)
    email = models.EmailField(help_text="Email address for verification")
    
    # Code storage and type
    code_type = models.CharField(max_length=20, choices=CODE_TYPES)
    code_hash = models.CharField(max_length=255, help_text="Hashed verification code")
    code_partial = models.CharField(max_length=4, help_text="First 4 digits for reference")
    
    # Security and rate limiting
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    attempt_count = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    # Request tracking
    requested_ip = models.GenericIPAddressField(null=True, blank=True)
    requested_user_agent = models.TextField(blank=True)
    verified_ip = models.GenericIPAddressField(null=True, blank=True)
    verified_user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_email_verification_codes'
        indexes = [
            models.Index(fields=['email', 'code_type', 'status']),
            models.Index(fields=['user', 'code_type']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F('created_at')),
                name='email_code_valid_expiration'
            ),
        ]
    
    def __str__(self):
        return f"{self.get_code_type_display()} - {self.email} ({self.status})"
    
    def is_expired(self):
        """Check if code has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if code can be used for verification"""
        return (
            self.status == self.PENDING and
            not self.is_expired() and
            self.attempt_count < self.max_attempts
        )
    
    def verify_code(self, raw_code, ip_address=None, user_agent=""):
        """
        Verify email code with security checks
        
        Args:
            raw_code: Raw verification code
            ip_address: Client IP for audit
            user_agent: Client user agent
            
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        # Update attempt tracking
        self.attempt_count += 1
        self.last_attempt_at = timezone.now()
        
        if not self.is_valid():
            self.save(update_fields=['attempt_count', 'last_attempt_at'])
            if self.is_expired():
                return False, "Verification code has expired"
            elif self.attempt_count >= self.max_attempts:
                self.status = self.REVOKED
                self.save(update_fields=['status'])
                return False, "Too many failed attempts. Code has been revoked."
            else:
                return False, "Verification code is no longer valid"
        
        # Verify code using Django's password verification
        if check_password(raw_code, self.code_hash):
            # Mark as verified
            self.status = self.VERIFIED
            self.verified_at = timezone.now()
            self.verified_ip = ip_address
            self.verified_user_agent = user_agent
            self.save(update_fields=[
                'status', 'verified_at', 'verified_ip', 'verified_user_agent',
                'attempt_count', 'last_attempt_at'
            ])
            
            # Log security event
            from .security_models import SecurityEvent
            SecurityEvent.log_event(
                event_type='email_code_verified',
                user=self.user,
                description=f'Email verification code verified: {self.get_code_type_display()}',
                risk_level=1,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'email': self.email,
                    'code_type': self.code_type,
                    'code_id': str(self.id),
                    'attempts': self.attempt_count
                }
            )
            
            return True, "Email verification code verified successfully"
        else:
            self.save(update_fields=['attempt_count', 'last_attempt_at'])
            
            # Log failed attempt
            from .security_models import SecurityEvent
            SecurityEvent.log_event(
                event_type='email_code_failed',
                user=self.user,
                description=f'Email verification code failed: {self.get_code_type_display()}',
                risk_level='medium',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'email': self.email,
                    'code_type': self.code_type,
                    'code_id': str(self.id),
                    'attempts': self.attempt_count
                }
            )
            
            return False, "Invalid verification code"
    
    def revoke(self, reason="Manual revocation"):
        """Revoke the verification code"""
        self.status = self.REVOKED
        self.save(update_fields=['status'])
    
    @classmethod
    def generate_secure_code(cls, length=6):
        """Generate cryptographically secure verification code"""
        # Generate numeric code for email OTP
        digits = '0123456789'
        return ''.join(secrets.choice(digits) for _ in range(length))
    
    @classmethod
    def create_verification_code(cls, email, code_type, user=None, expires_minutes=10, ip_address=None, user_agent=""):
        """
        Create a new email verification code
        
        Args:
            email: Email address
            code_type: Type of verification code
            user: User instance (optional)
            expires_minutes: Expiration time in minutes
            ip_address: Client IP for audit
            user_agent: Client user agent
            
        Returns:
            tuple: (EmailVerificationCode instance, raw_code)
        """
        # Revoke existing pending codes for same email and type
        cls.objects.filter(
            email=email,
            code_type=code_type,
            status=cls.PENDING
        ).update(
            status=cls.REVOKED
        )
        
        # Generate new code
        raw_code = cls.generate_secure_code()
        code_hash = make_password(raw_code)
        code_partial = raw_code[:4]
        
        # Set expiration
        expires_at = timezone.now() + timedelta(minutes=expires_minutes)
        
        # Create verification code
        verification_code = cls.objects.create(
            user=user,
            email=email,
            code_type=code_type,
            code_hash=code_hash,
            code_partial=code_partial,
            expires_at=expires_at,
            requested_ip=ip_address,
            requested_user_agent=user_agent
        )
        
        # Log security event
        from .security_models import SecurityEvent
        SecurityEvent.log_event(
            event_type='email_code_generated',
            user=user,
            description=f'Email verification code generated: {verification_code.get_code_type_display()}',
            risk_level=1,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'email': email,
                'code_type': code_type,
                'code_id': str(verification_code.id),
                'expires_minutes': expires_minutes
            }
        )
        
        return verification_code, raw_code
    
    @classmethod
    def cleanup_expired_codes(cls):
        """Clean up expired verification codes"""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now(),
            status=cls.PENDING
        ).update(
            status=cls.EXPIRED
        )
        return expired_count
    
    @classmethod
    def get_user_rate_limit_status(cls, email, code_type, time_window_minutes=60):
        """
        Check rate limiting status for user/email
        
        Args:
            email: Email address
            code_type: Type of verification code
            time_window_minutes: Time window for rate limiting
            
        Returns:
            dict: Rate limit status and information
        """
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Count recent codes
        recent_codes = cls.objects.filter(
            email=email,
            code_type=code_type,
            created_at__gte=time_threshold
        ).count()
        
        # Rate limits by code type
        rate_limits = {
            cls.ACCOUNT_VERIFICATION: 3,
            cls.PASSWORD_RESET: 5,
            cls.EMAIL_CHANGE: 3,
            cls.LOGIN_VERIFICATION: 10,
        }
        
        max_codes = rate_limits.get(code_type, 3)
        is_rate_limited = recent_codes >= max_codes
        
        return {
            'is_rate_limited': is_rate_limited,
            'recent_codes': recent_codes,
            'max_codes': max_codes,
            'time_window_minutes': time_window_minutes,
            'cooldown_until': None if not is_rate_limited else timezone.now() + timedelta(minutes=time_window_minutes)
        }


class PasswordResetToken(models.Model):
    """
    Secure password reset tokens with advanced security features
    
    Features:
    - Cryptographically secure token generation
    - Automatic expiration
    - Single-use enforcement
    - Rate limiting and attempt tracking
    - IP and device tracking
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    
    # Token storage
    token_hash = models.CharField(max_length=255, unique=True, help_text="Hashed reset token")
    token_partial = models.CharField(max_length=8, help_text="Partial token for reference")
    
    # Status and security
    is_used = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    attempt_count = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    # Request tracking
    requested_ip = models.GenericIPAddressField(null=True, blank=True)
    requested_user_agent = models.TextField(blank=True)
    used_ip = models.GenericIPAddressField(null=True, blank=True)
    used_user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_password_reset_tokens'
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Password Reset Token for {self.user.email} - {self.token_partial}****"
    
    def is_valid(self):
        """Check if token is valid for use"""
        return (
            not self.is_used and
            not self.is_expired and
            timezone.now() <= self.expires_at and
            self.attempt_count < self.max_attempts
        )
    
    def mark_used(self, ip_address=None, user_agent=""):
        """Mark token as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.used_ip = ip_address
        self.used_user_agent = user_agent
        self.save(update_fields=['is_used', 'used_at', 'used_ip', 'used_user_agent'])
    
    def verify_token(self, raw_token, ip_address=None, user_agent=""):
        """
        Verify password reset token
        
        Args:
            raw_token: Raw token string
            ip_address: Client IP for audit
            user_agent: Client user agent
            
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        self.attempt_count += 1
        
        if not self.is_valid():
            self.save(update_fields=['attempt_count'])
            if self.is_used:
                return False, "Reset token has already been used"
            elif timezone.now() > self.expires_at:
                self.is_expired = True
                self.save(update_fields=['is_expired', 'attempt_count'])
                return False, "Reset token has expired"
            else:
                return False, "Reset token is no longer valid"
        
        # Verify token
        if check_password(raw_token, self.token_hash):
            self.save(update_fields=['attempt_count'])
            return True, "Reset token verified successfully"
        else:
            self.save(update_fields=['attempt_count'])
            
            # Log failed attempt
            from .security_models import SecurityEvent
            SecurityEvent.log_event(
                event_type='password_reset_failed',
                user=self.user,
                description='Password reset token verification failed',
                risk_level='medium',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'token_id': str(self.id),
                    'attempts': self.attempt_count
                }
            )
            
            return False, "Invalid reset token"
    
    @classmethod
    def generate_secure_token(cls, length=32):
        """Generate cryptographically secure reset token"""
        return secrets.token_urlsafe(length)
    
    @classmethod
    def create_reset_token(cls, user, expires_hours=24, ip_address=None, user_agent=""):
        """
        Create password reset token for user
        
        Args:
            user: User instance
            expires_hours: Token expiration in hours
            ip_address: Client IP for audit
            user_agent: Client user agent
            
        Returns:
            tuple: (PasswordResetToken instance, raw_token)
        """
        # Invalidate existing tokens
        cls.objects.filter(
            user=user,
            is_used=False,
            is_expired=False
        ).update(is_expired=True)
        
        # Generate new token
        raw_token = cls.generate_secure_token()
        token_hash = make_password(raw_token)
        token_partial = raw_token[:8]
        
        # Set expiration
        expires_at = timezone.now() + timedelta(hours=expires_hours)
        
        # Create token
        reset_token = cls.objects.create(
            user=user,
            token_hash=token_hash,
            token_partial=token_partial,
            expires_at=expires_at,
            requested_ip=ip_address,
            requested_user_agent=user_agent
        )
        
        # Log security event
        from .security_models import SecurityEvent
        SecurityEvent.log_event(
            event_type='password_reset_requested',
            user=user,
            description='Password reset token generated',
            risk_level='medium',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'token_id': str(reset_token.id),
                'expires_hours': expires_hours
            }
        )
        
        return reset_token, raw_token
    
    @classmethod
    def cleanup_expired_tokens(cls):
        """Clean up expired reset tokens"""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now(),
            is_expired=False
        ).update(is_expired=True)
        return expired_count