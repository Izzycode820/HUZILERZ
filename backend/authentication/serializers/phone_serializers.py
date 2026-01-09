"""
Enterprise Phone Authentication Serializers - 2025 Security Standards
Validation for phone OTP verification and phone-based authentication
"""
from rest_framework import serializers
from ..models import PhoneVerificationCode
import re


class PhoneVerificationRequestSerializer(serializers.Serializer):
    """Serializer for requesting phone verification codes"""
    
    SUPPORTED_CODE_TYPES = [
        PhoneVerificationCode.PHONE_VERIFICATION,
        PhoneVerificationCode.LOGIN_VERIFICATION,
        PhoneVerificationCode.PASSWORD_RESET,
        PhoneVerificationCode.PHONE_CHANGE,
    ]
    
    phone_number = serializers.CharField(
        max_length=20,
        min_length=8,
        help_text="Phone number to send verification code to (E.164 format recommended)"
    )
    
    code_type = serializers.ChoiceField(
        choices=SUPPORTED_CODE_TYPES,
        default=PhoneVerificationCode.PHONE_VERIFICATION,
        help_text="Type of verification code to send"
    )
    
    def validate_phone_number(self, value):
        """Validate phone number format and security"""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required")
        
        # Remove common formatting characters for validation
        cleaned = re.sub(r'[\s\-\(\)\.]', '', value.strip())
        
        # Length validation
        if len(cleaned) < 8:
            raise serializers.ValidationError("Phone number is too short")
        
        if len(cleaned) > 20:
            raise serializers.ValidationError("Phone number is too long")
        
        # Character validation - only digits and optional leading +
        if not re.match(r'^\+?[0-9]+$', cleaned):
            raise serializers.ValidationError("Phone number contains invalid characters")
        
        # Check for suspicious patterns (prevent injection)
        if re.search(r'[<>"\'\\]', value):
            raise serializers.ValidationError("Phone number contains invalid characters")
        
        return cleaned


class PhoneVerificationConfirmSerializer(serializers.Serializer):
    """Serializer for confirming phone verification codes"""
    
    phone_number = serializers.CharField(
        max_length=20,
        min_length=8,
        help_text="Phone number the code was sent to"
    )
    
    code_type = serializers.ChoiceField(
        choices=PhoneVerificationRequestSerializer.SUPPORTED_CODE_TYPES,
        default=PhoneVerificationCode.PHONE_VERIFICATION,
        help_text="Type of verification code"
    )
    
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="6-digit verification code from SMS"
    )
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not value:
            raise serializers.ValidationError("Phone number is required")
        
        cleaned = re.sub(r'[\s\-\(\)\.]', '', value.strip())
        
        if not re.match(r'^\+?[0-9]+$', cleaned):
            raise serializers.ValidationError("Invalid phone number format")
        
        return cleaned
    
    def validate_code(self, value):
        """Validate verification code format"""
        if not value:
            raise serializers.ValidationError("Verification code is required")
        
        # Clean code - extract only digits
        code = re.sub(r'\D', '', value.strip())
        
        if not code:
            raise serializers.ValidationError("Verification code must contain digits")
        
        if len(code) != 6:
            raise serializers.ValidationError("Verification code must be exactly 6 digits")
        
        return code


class PhoneChangeRequestSerializer(serializers.Serializer):
    """Serializer for requesting phone number change"""
    
    new_phone_number = serializers.CharField(
        max_length=20,
        min_length=8,
        help_text="New phone number"
    )
    
    def validate_new_phone_number(self, value):
        """Validate new phone number"""
        if not value or not value.strip():
            raise serializers.ValidationError("New phone number is required")
        
        # Normalize phone number
        cleaned = re.sub(r'[\s\-\(\)\.]', '', value.strip())
        
        # Length check
        if len(cleaned) < 8:
            raise serializers.ValidationError("Phone number is too short")
        
        if len(cleaned) > 20:
            raise serializers.ValidationError("Phone number is too long")
        
        # Format validation
        if not re.match(r'^\+?[0-9]+$', cleaned):
            raise serializers.ValidationError("Phone number contains invalid characters")
        
        return cleaned


class PhoneChangeConfirmSerializer(serializers.Serializer):
    """Serializer for confirming phone number change"""
    
    new_phone_number = serializers.CharField(
        max_length=20,
        min_length=8,
        help_text="New phone number to confirm"
    )
    
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="Verification code sent to new phone"
    )
    
    def validate_new_phone_number(self, value):
        """Validate new phone number"""
        if not value:
            raise serializers.ValidationError("New phone number is required")
        
        cleaned = re.sub(r'[\s\-\(\)\.]', '', value.strip())
        
        if not re.match(r'^\+?[0-9]+$', cleaned):
            raise serializers.ValidationError("Invalid phone number format")
        
        return cleaned
    
    def validate_code(self, value):
        """Validate verification code"""
        if not value:
            raise serializers.ValidationError("Verification code is required")
        
        # Clean code
        code = re.sub(r'\D', '', value.strip())
        
        if not code or len(code) != 6:
            raise serializers.ValidationError("Verification code must be exactly 6 digits")
        
        return code


# Response serializers
class PhoneVerificationResponseSerializer(serializers.Serializer):
    """Response format for phone verification operations"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    verification_id = serializers.UUIDField(required=False)
    expires_in_minutes = serializers.IntegerField(required=False)
    code_type = serializers.CharField(required=False)


class PhoneVerificationStatusSerializer(serializers.Serializer):
    """Serializer for phone verification status"""
    
    phone_verified = serializers.BooleanField()
    phone_number = serializers.CharField(allow_null=True)
    has_pending_verification = serializers.BooleanField()
    pending_expires_at = serializers.DateTimeField(allow_null=True, required=False)
    rate_limit = serializers.DictField(required=False)


class RateLimitInfoSerializer(serializers.Serializer):
    """Serializer for rate limit information"""
    
    is_limited = serializers.BooleanField()
    remaining_attempts = serializers.IntegerField()
    cooldown_until = serializers.DateTimeField(allow_null=True)


class SMSServiceStatusSerializer(serializers.Serializer):
    """Serializer for SMS service status"""
    
    available = serializers.BooleanField()
    configured = serializers.BooleanField()


# Validation mixins
class PhoneValidationMixin:
    """Mixin for common phone validation logic"""
    
    # List of invalid/test phone number prefixes
    BLOCKED_PREFIXES = [
        '+15555',  # US test numbers
        '+10000',  # Reserved
    ]
    
    @staticmethod
    def validate_phone_security(phone_number):
        """Comprehensive phone security validation"""
        if not phone_number:
            return False, "Phone number is required"
        
        # Normalize
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone_number.strip())
        
        # Length check
        if len(cleaned) < 8:
            return False, "Phone number is too short"
        
        if len(cleaned) > 20:
            return False, "Phone number is too long"
        
        # Format validation
        if not re.match(r'^\+?[0-9]+$', cleaned):
            return False, "Invalid phone number format"
        
        # Security checks - prevent injection
        if re.search(r'[<>"\'\\]', phone_number):
            return False, "Phone number contains invalid characters"
        
        # Check blocked prefixes
        for prefix in PhoneValidationMixin.BLOCKED_PREFIXES:
            if cleaned.startswith(prefix.replace('+', '')):
                return False, "Phone number is not allowed"
        
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
        
        if len(clean_code) != 6:
            return False, "Verification code must be exactly 6 digits"
        
        return True, clean_code
    
    @staticmethod
    def normalize_phone_number(phone_number, default_country_code="+237"):
        """Normalize phone number to E.164 format"""
        if not phone_number:
            return phone_number
        
        # Remove formatting
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone_number.strip())
        
        # Already has country code
        if cleaned.startswith('+'):
            return cleaned
        
        # Remove leading zero if present
        if cleaned.startswith('0'):
            cleaned = cleaned[1:]
        
        # Add default country code
        return f"{default_country_code}{cleaned}"
