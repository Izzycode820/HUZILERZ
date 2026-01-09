"""
Enterprise Email Authentication Serializers - 2025 Security Standards
Validation for email OTP verification, password reset, and email-based authentication
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import EmailVerificationCode
import re


class EmailVerificationRequestSerializer(serializers.Serializer):
    """Serializer for requesting email verification codes"""
    
    SUPPORTED_CODE_TYPES = [
        EmailVerificationCode.ACCOUNT_VERIFICATION,
        EmailVerificationCode.LOGIN_VERIFICATION,
        EmailVerificationCode.EMAIL_CHANGE,
        EmailVerificationCode.PASSWORD_RESET,
    ]
    
    email = serializers.EmailField(
        help_text="Email address to send verification code to"
    )
    
    code_type = serializers.ChoiceField(
        choices=SUPPORTED_CODE_TYPES,
        help_text="Type of verification code to send"
    )
    
    def validate_email(self, value):
        """Validate email address format and security"""
        if not value or not value.strip():
            raise serializers.ValidationError("Email address is required")
        
        # Normalize email
        email = value.strip().lower()
        
        # Basic email validation (additional to DRF's EmailField)
        if len(email) > 254:  # RFC 5321 limit
            raise serializers.ValidationError("Email address is too long")
        
        # Check for suspicious patterns
        if re.search(r'[<>"\'/\\]', email):
            raise serializers.ValidationError("Email address contains invalid characters")
        
        # Block temporary/disposable email domains (basic list)
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email'
        ]
        
        domain = email.split('@')[1] if '@' in email else ''
        if domain.lower() in disposable_domains:
            raise serializers.ValidationError("Temporary email addresses are not allowed")
        
        return email


class EmailVerificationConfirmSerializer(serializers.Serializer):
    """Serializer for confirming email verification codes"""
    
    email = serializers.EmailField(
        help_text="Email address the code was sent to"
    )
    
    code_type = serializers.ChoiceField(
        choices=EmailVerificationRequestSerializer.SUPPORTED_CODE_TYPES,
        help_text="Type of verification code"
    )
    
    code = serializers.CharField(
        max_length=8,
        min_length=4,
        help_text="Verification code from email"
    )
    
    def validate_email(self, value):
        """Validate email address format"""
        return value.strip().lower() if value else value
    
    def validate_code(self, value):
        """Validate verification code format"""
        if not value:
            raise serializers.ValidationError("Verification code is required")
        
        # Remove any formatting
        code = re.sub(r'\D', '', value.strip())
        
        if not code:
            raise serializers.ValidationError("Verification code must contain digits")
        
        if len(code) < 4 or len(code) > 8:
            raise serializers.ValidationError("Verification code must be 4-8 digits")
        
        return code


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset requests"""
    
    email = serializers.EmailField(
        help_text="Email address of the account to reset password for"
    )
    
    def validate_email(self, value):
        """Validate email address"""
        if not value or not value.strip():
            raise serializers.ValidationError("Email address is required")
        
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset with token"""
    
    token = serializers.CharField(
        max_length=500,
        min_length=20,
        help_text="Password reset token from email"
    )
    
    new_password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        help_text="New password"
    )
    
    confirm_password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        help_text="Confirm new password"
    )
    
    def validate_token(self, value):
        """Validate reset token format"""
        if not value or not value.strip():
            raise serializers.ValidationError("Reset token is required")
        
        token = value.strip()
        
        # Basic security check
        if re.search(r'[<>"\'/\\]', token):
            raise serializers.ValidationError("Invalid token format")
        
        return token
    
    def validate_new_password(self, value):
        """Validate new password strength"""
        if not value:
            raise serializers.ValidationError("New password is required")
        
        # Use Django's password validation
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise serializers.ValidationError({
                    'confirm_password': 'Passwords do not match'
                })
        
        return data


class EmailChangeRequestSerializer(serializers.Serializer):
    """Serializer for requesting email address change"""
    
    new_email = serializers.EmailField(
        help_text="New email address"
    )
    
    def validate_new_email(self, value):
        """Validate new email address"""
        if not value or not value.strip():
            raise serializers.ValidationError("New email address is required")
        
        # Normalize email
        email = value.strip().lower()
        
        # Length check
        if len(email) > 254:
            raise serializers.ValidationError("Email address is too long")
        
        # Security checks
        if re.search(r'[<>"\'/\\]', email):
            raise serializers.ValidationError("Email address contains invalid characters")
        
        return email


class EmailChangeConfirmSerializer(serializers.Serializer):
    """Serializer for confirming email address change"""
    
    new_email = serializers.EmailField(
        help_text="New email address to confirm"
    )
    
    code = serializers.CharField(
        max_length=8,
        min_length=4,
        help_text="Verification code sent to new email"
    )
    
    def validate_new_email(self, value):
        """Validate new email address"""
        return value.strip().lower() if value else value
    
    def validate_code(self, value):
        """Validate verification code"""
        if not value:
            raise serializers.ValidationError("Verification code is required")
        
        # Clean code
        code = re.sub(r'\D', '', value.strip())
        
        if not code or len(code) < 4:
            raise serializers.ValidationError("Invalid verification code format")
        
        return code


# Response serializers
class EmailVerificationResponseSerializer(serializers.Serializer):
    """Response format for email verification operations"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(required=False)


class PasswordResetResponseSerializer(serializers.Serializer):
    """Response format for password reset operations"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(required=False)


class EmailVerificationStatusSerializer(serializers.Serializer):
    """Serializer for email verification status"""
    
    user_email = serializers.EmailField()
    is_email_verified = serializers.BooleanField()
    recent_verifications = serializers.ListField(
        child=serializers.DictField()
    )


class VerificationCodeSerializer(serializers.Serializer):
    """Serializer for verification code information"""
    
    id = serializers.UUIDField()
    code_type = serializers.CharField()
    code_type_display = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    verified_at = serializers.DateTimeField(allow_null=True)


# Validation mixins
class EmailValidationMixin:
    """Mixin for common email validation logic"""
    
    @staticmethod
    def validate_email_security(email):
        """Comprehensive email security validation"""
        if not email:
            return False, "Email is required"
        
        # Normalize
        email = email.strip().lower()
        
        # Length check
        if len(email) > 254:
            return False, "Email address is too long"
        
        # Format validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Invalid email format"
        
        # Security checks
        if re.search(r'[<>"\'/\\]', email):
            return False, "Email contains invalid characters"
        
        # Domain checks
        domain = email.split('@')[1] if '@' in email else ''
        
        # Block certain domains
        blocked_domains = [
            'example.com', 'test.com', 'localhost'
        ]
        
        if domain in blocked_domains:
            return False, "Email domain not allowed"
        
        return True, None
    
    @staticmethod
    def validate_verification_code_format(code):
        """Validate verification code format"""
        if not code:
            return False, "Verification code is required"
        
        # Clean code
        clean_code = re.sub(r'\D', '', str(code).strip())
        
        if not clean_code:
            return False, "Verification code must contain digits"
        
        if len(clean_code) < 4 or len(clean_code) > 8:
            return False, "Verification code must be 4-8 digits"
        
        return True, clean_code
    
    @staticmethod
    def sanitize_email_input(email):
        """Sanitize email input"""
        if not email:
            return email
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>"\'/\\]', '', email.strip())
        return sanitized.lower()


# Rate limiting serializers
class RateLimitInfoSerializer(serializers.Serializer):
    """Serializer for rate limit information"""
    
    is_rate_limited = serializers.BooleanField()
    recent_codes = serializers.IntegerField()
    max_codes = serializers.IntegerField()
    time_window_minutes = serializers.IntegerField()
    cooldown_until = serializers.DateTimeField(allow_null=True)


class EmailSecurityStatsSerializer(serializers.Serializer):
    """Serializer for email security statistics"""
    
    total_codes_sent = serializers.IntegerField()
    successful_verifications = serializers.IntegerField()
    failed_attempts = serializers.IntegerField()
    expired_codes = serializers.IntegerField()
    rate_limited_requests = serializers.IntegerField()


# Enhanced validation serializers
class SecureEmailRequestSerializer(serializers.Serializer):
    """Enhanced email request with security features"""
    
    email = serializers.EmailField()
    request_id = serializers.UUIDField(required=False)
    client_fingerprint = serializers.CharField(max_length=64, required=False)
    
    def validate_email(self, value):
        """Enhanced email validation"""
        is_valid, message = EmailValidationMixin.validate_email_security(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return value
    
    def validate_client_fingerprint(self, value):
        """Validate client fingerprint"""
        if value:
            # Basic validation for fingerprint
            if not re.match(r'^[a-zA-Z0-9]+$', value):
                raise serializers.ValidationError("Invalid client fingerprint format")
        return value