"""
Phone Verification Models - 2025 Security Standards
Handles phone OTP verification for account verification and authentication

Production Standards:
- Response time < 200ms for user-facing operations
- Proper indexing for query performance
- Rate limiting and attempt tracking
- Atomic transactions for race condition prevention
- Comprehensive logging and audit trails
"""
import uuid
import secrets
from datetime import timedelta
from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from .user import User
import logging

logger = logging.getLogger(__name__)


class PhoneVerificationCode(models.Model):
    """
    Phone OTP verification codes for account verification and authentication
    
    Features:
    - CSPRNG-generated codes
    - Rate limiting and attempt tracking
    - Automatic expiration and cleanup
    - Secure hashing with bcrypt
    - Anti-bruteforce protection
    - Comprehensive audit logging
    """
    
    # Code types
    PHONE_VERIFICATION = 'phone_verification'
    LOGIN_VERIFICATION = 'login_verification'
    PASSWORD_RESET = 'password_reset'
    PHONE_CHANGE = 'phone_change'
    
    CODE_TYPES = [
        (PHONE_VERIFICATION, 'Phone Verification'),
        (LOGIN_VERIFICATION, 'Login Verification'),
        (PASSWORD_RESET, 'Password Reset'),
        (PHONE_CHANGE, 'Phone Change'),
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
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='phone_verification_codes', 
        null=True, 
        blank=True,
        db_index=True
    )
    phone_number = models.CharField(
        max_length=20, 
        db_index=True,
        help_text="Phone number for verification (E.164 format)"
    )
    country_code = models.CharField(
        max_length=5, 
        default="+237",
        help_text="Country code for phone number"
    )
    
    # Code storage and type
    code_type = models.CharField(max_length=20, choices=CODE_TYPES, db_index=True)
    code_hash = models.CharField(max_length=255, help_text="Hashed verification code")
    code_partial = models.CharField(max_length=4, help_text="First 4 digits for reference")
    
    # Security and rate limiting
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    attempt_count = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    # Request tracking for audit
    requested_ip = models.GenericIPAddressField(null=True, blank=True)
    requested_user_agent = models.TextField(blank=True, default='')
    verified_ip = models.GenericIPAddressField(null=True, blank=True)
    verified_user_agent = models.TextField(blank=True, default='')
    
    # Timestamps with indexes for cleanup queries
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_phone_verification_codes'
        indexes = [
            models.Index(fields=['phone_number', 'code_type', 'status']),
            models.Index(fields=['user', 'code_type']),
            models.Index(fields=['expires_at', 'status']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F('created_at')),
                name='phone_code_valid_expiration'
            ),
        ]
    
    def __str__(self):
        return f"{self.get_code_type_display()} - {self.phone_number} ({self.status})"
    
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
        Verify phone code with security checks
        
        Uses atomic transaction to prevent race conditions during
        concurrent verification attempts.
        
        Args:
            raw_code: Raw verification code
            ip_address: Client IP for audit
            user_agent: Client user agent
            
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        with transaction.atomic():
            # Re-fetch with lock to prevent race conditions
            locked_self = PhoneVerificationCode.objects.select_for_update().get(pk=self.pk)
            
            # Update attempt tracking
            locked_self.attempt_count += 1
            locked_self.last_attempt_at = timezone.now()
            
            if not locked_self.is_valid():
                locked_self.save(update_fields=['attempt_count', 'last_attempt_at'])
                
                if locked_self.is_expired():
                    logger.warning(
                        f"Phone verification code expired: {locked_self.id}, "
                        f"phone: {locked_self.phone_number}"
                    )
                    return False, "Verification code has expired"
                elif locked_self.attempt_count >= locked_self.max_attempts:
                    locked_self.status = locked_self.REVOKED
                    locked_self.save(update_fields=['status'])
                    logger.warning(
                        f"Phone verification code revoked due to max attempts: {locked_self.id}, "
                        f"phone: {locked_self.phone_number}, attempts: {locked_self.attempt_count}"
                    )
                    return False, "Too many failed attempts. Code has been revoked."
                else:
                    return False, "Verification code is no longer valid"
            
            # Verify code using Django's password verification
            if check_password(raw_code, locked_self.code_hash):
                # Mark as verified
                locked_self.status = locked_self.VERIFIED
                locked_self.verified_at = timezone.now()
                locked_self.verified_ip = ip_address
                locked_self.verified_user_agent = user_agent or ''
                locked_self.save(update_fields=[
                    'status', 'verified_at', 'verified_ip', 'verified_user_agent',
                    'attempt_count', 'last_attempt_at'
                ])
                
                # Copy updated values back to self
                self.status = locked_self.status
                self.verified_at = locked_self.verified_at
                self.attempt_count = locked_self.attempt_count
                
                # Log security event
                try:
                    from .security_models import SecurityEvent
                    SecurityEvent.log_event(
                        event_type='phone_code_verified',
                        user=locked_self.user,
                        description=f'Phone verification code verified: {locked_self.get_code_type_display()}',
                        risk_level=1,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            'phone': locked_self.phone_number,
                            'code_type': locked_self.code_type,
                            'code_id': str(locked_self.id),
                            'attempts': locked_self.attempt_count
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to log security event: {e}")
                
                logger.info(
                    f"Phone verification code verified successfully: {locked_self.id}, "
                    f"phone: {locked_self.phone_number}"
                )
                return True, "Phone verification code verified successfully"
            else:
                locked_self.save(update_fields=['attempt_count', 'last_attempt_at'])
                
                # Copy updated values back to self
                self.attempt_count = locked_self.attempt_count
                
                # Log failed attempt
                try:
                    from .security_models import SecurityEvent
                    SecurityEvent.log_event(
                        event_type='phone_code_failed',
                        user=locked_self.user,
                        description=f'Phone verification code failed: {locked_self.get_code_type_display()}',
                        risk_level='medium',
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            'phone': locked_self.phone_number,
                            'code_type': locked_self.code_type,
                            'code_id': str(locked_self.id),
                            'attempts': locked_self.attempt_count
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to log security event: {e}")
                
                logger.warning(
                    f"Phone verification code failed: {locked_self.id}, "
                    f"phone: {locked_self.phone_number}, attempt: {locked_self.attempt_count}"
                )
                return False, "Invalid verification code"
    
    def revoke(self, reason="Manual revocation"):
        """Revoke the verification code"""
        self.status = self.REVOKED
        self.save(update_fields=['status'])
        logger.info(f"Phone verification code revoked: {self.id}, reason: {reason}")
    
    @classmethod
    def generate_secure_code(cls, length=6):
        """Generate cryptographically secure verification code using CSPRNG"""
        digits = '0123456789'
        return ''.join(secrets.choice(digits) for _ in range(length))
    
    @classmethod
    def normalize_phone_number(cls, phone_number, country_code="+237"):
        """
        Normalize phone number to E.164 format
        
        Args:
            phone_number: Raw phone number
            country_code: Country code (default Cameroon)
            
        Returns:
            tuple: (normalized_number, country_code)
        """
        # Remove all non-digit characters except leading +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # If already has country code
        if cleaned.startswith('+'):
            # Extract country code (first 1-4 digits after +)
            for i in range(1, min(5, len(cleaned))):
                potential_code = cleaned[:i+1]
                if potential_code in ['+1', '+33', '+44', '+237', '+234', '+254']:
                    return cleaned, potential_code
            return cleaned, country_code
        
        # Remove leading 0 if present (common in local formats)
        if cleaned.startswith('0'):
            cleaned = cleaned[1:]
        
        # Add country code
        normalized = f"{country_code}{cleaned}"
        return normalized, country_code
    
    @classmethod
    def create_verification_code(cls, phone_number, code_type, user=None, 
                                  expires_minutes=10, ip_address=None, 
                                  user_agent="", country_code="+237"):
        """
        Create a new phone verification code
        
        Uses atomic transaction to ensure consistent state when
        revoking existing codes and creating new ones.
        
        Args:
            phone_number: Phone number
            code_type: Type of verification code
            user: User instance (optional)
            expires_minutes: Expiration time in minutes
            ip_address: Client IP for audit
            user_agent: Client user agent
            country_code: Country code for phone
            
        Returns:
            tuple: (PhoneVerificationCode instance, raw_code)
        """
        # Normalize phone number
        normalized_phone, detected_country = cls.normalize_phone_number(phone_number, country_code)
        
        with transaction.atomic():
            # Revoke existing pending codes for same phone and type
            revoked_count = cls.objects.filter(
                phone_number=normalized_phone,
                code_type=code_type,
                status=cls.PENDING
            ).update(
                status=cls.REVOKED
            )
            
            if revoked_count > 0:
                logger.info(
                    f"Revoked {revoked_count} pending phone verification codes for "
                    f"phone: {normalized_phone}, type: {code_type}"
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
                phone_number=normalized_phone,
                country_code=detected_country,
                code_type=code_type,
                code_hash=code_hash,
                code_partial=code_partial,
                expires_at=expires_at,
                requested_ip=ip_address,
                requested_user_agent=user_agent or ''
            )
        
        # Log security event (outside transaction to avoid blocking)
        try:
            from .security_models import SecurityEvent
            SecurityEvent.log_event(
                event_type='phone_code_generated',
                user=user,
                description=f'Phone verification code generated: {verification_code.get_code_type_display()}',
                risk_level=1,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'phone': normalized_phone,
                    'code_type': code_type,
                    'code_id': str(verification_code.id),
                    'expires_minutes': expires_minutes
                }
            )
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
        
        logger.info(
            f"Phone verification code created: {verification_code.id}, "
            f"phone: {normalized_phone}, type: {code_type}, expires: {expires_minutes}min"
        )
        
        return verification_code, raw_code
    
    @classmethod
    def cleanup_expired_codes(cls):
        """
        Clean up expired verification codes
        
        Should be called periodically via management command or Celery task.
        """
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now(),
            status=cls.PENDING
        ).update(
            status=cls.EXPIRED
        )
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired phone verification codes")
        
        return expired_count
    
    @classmethod
    def get_rate_limit_status(cls, phone_number, code_type, time_window_minutes=60):
        """
        Check rate limiting status for phone number
        
        Prevents abuse by limiting how many codes can be requested
        within a time window.
        
        Args:
            phone_number: Phone number to check
            code_type: Type of verification code
            time_window_minutes: Time window for rate limiting
            
        Returns:
            dict: Rate limit status and information
        """
        # Normalize phone number for consistent lookup
        normalized_phone, _ = cls.normalize_phone_number(phone_number)
        
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Count recent codes - using index on (phone_number, code_type, created_at)
        recent_codes = cls.objects.filter(
            phone_number=normalized_phone,
            code_type=code_type,
            created_at__gte=time_threshold
        ).count()
        
        # Rate limits by code type (SMS is expensive, so stricter limits)
        rate_limits = {
            cls.PHONE_VERIFICATION: 3,
            cls.PASSWORD_RESET: 3,
            cls.PHONE_CHANGE: 2,
            cls.LOGIN_VERIFICATION: 5,
        }
        
        max_codes = rate_limits.get(code_type, 3)
        is_rate_limited = recent_codes >= max_codes
        
        if is_rate_limited:
            logger.warning(
                f"Rate limit hit for phone: {normalized_phone}, "
                f"type: {code_type}, count: {recent_codes}"
            )
        
        return {
            'is_rate_limited': is_rate_limited,
            'recent_codes': recent_codes,
            'max_codes': max_codes,
            'time_window_minutes': time_window_minutes,
            'cooldown_until': None if not is_rate_limited else (
                timezone.now() + timedelta(minutes=time_window_minutes)
            )
        }
