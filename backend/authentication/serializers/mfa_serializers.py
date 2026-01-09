"""
Enterprise MFA Serializers - 2025 Security Standards
Comprehensive validation for TOTP, backup codes, and MFA management
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class TOTPSetupSerializer(serializers.Serializer):
    """Serializer for TOTP device setup"""
    
    device_name = serializers.CharField(
        max_length=100,
        required=False,
        default="Authenticator App",
        help_text="Human-readable name for the TOTP device"
    )
    
    force_reset = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Force reset existing TOTP device"
    )
    
    def validate_device_name(self, value):
        """Validate device name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Device name cannot be empty")
        
        # Sanitize device name (basic security)
        if re.search(r'[<>"\']', value):
            raise serializers.ValidationError("Device name contains invalid characters")
        
        return value.strip()


class TOTPConfirmSerializer(serializers.Serializer):
    """Serializer for TOTP device confirmation"""
    
    token = serializers.CharField(
        max_length=8,
        min_length=6,
        help_text="6-digit TOTP token from authenticator app"
    )
    
    def validate_token(self, value):
        """Validate TOTP token format"""
        # Remove any spaces or formatting
        token = re.sub(r'\D', '', value)
        
        if not token:
            raise serializers.ValidationError("Token is required")
        
        if len(token) != 6:
            raise serializers.ValidationError("Token must be exactly 6 digits")
        
        if not token.isdigit():
            raise serializers.ValidationError("Token must contain only digits")
        
        return token


class MFAVerifySerializer(serializers.Serializer):
    """Serializer for MFA token verification (TOTP or backup code)"""
    
    token = serializers.CharField(
        max_length=20,
        min_length=6,
        help_text="TOTP token (6 digits) or backup code (8-16 characters)"
    )
    
    def validate_token(self, value):
        """Validate MFA token (TOTP or backup code)"""
        # Remove whitespace
        token = value.strip().replace(' ', '').replace('-', '')
        
        if not token:
            raise serializers.ValidationError("Token is required")
        
        # Check if it's a TOTP token (6 digits)
        if token.isdigit() and len(token) == 6:
            return token
        
        # Check if it's a backup code (alphanumeric, 8-16 chars)
        if len(token) >= 8 and len(token) <= 16:
            # Backup codes should be alphanumeric
            if re.match(r'^[A-Z0-9]+$', token.upper()):
                return token.upper()
            else:
                raise serializers.ValidationError("Invalid backup code format")
        
        raise serializers.ValidationError(
            "Token must be a 6-digit TOTP code or 8-16 character backup code"
        )


class BackupCodeRegenerateSerializer(serializers.Serializer):
    """Serializer for backup code regeneration"""
    
    current_mfa_token = serializers.CharField(
        max_length=20,
        min_length=6,
        required=False,
        help_text="Current MFA token for security verification (recommended)"
    )
    
    count = serializers.IntegerField(
        min_value=5,
        max_value=20,
        required=False,
        default=10,
        help_text="Number of backup codes to generate (5-20)"
    )
    
    def validate_current_mfa_token(self, value):
        """Validate current MFA token if provided"""
        if value:
            # Use same validation as MFAVerifySerializer
            verify_serializer = MFAVerifySerializer(data={'token': value})
            if not verify_serializer.is_valid():
                raise serializers.ValidationError("Invalid MFA token format")
            return verify_serializer.validated_data['token']
        return value


# Response serializers
class TOTPDeviceSerializer(serializers.Serializer):
    """Enhanced TOTP device serializer"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    is_active = serializers.BooleanField()
    is_confirmed = serializers.BooleanField()
    is_locked = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    activated_at = serializers.DateTimeField(allow_null=True)
    last_used = serializers.DateTimeField(allow_null=True)
    failure_count = serializers.IntegerField()
    total_verifications = serializers.IntegerField()
    lockout_until = serializers.DateTimeField(allow_null=True)


class BackupCodeSerializer(serializers.Serializer):
    """Enhanced backup code serializer"""
    id = serializers.UUIDField()
    code_partial = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    used_at = serializers.DateTimeField(allow_null=True)
    expires_at = serializers.DateTimeField()


class MFAStatusSerializer(serializers.Serializer):
    """Enhanced MFA status response serializer"""
    mfa_enabled = serializers.BooleanField()
    totp_device = TOTPDeviceSerializer(allow_null=True)
    backup_codes = serializers.DictField()
    enforcement = serializers.DictField()
    security_score = serializers.IntegerField(min_value=0, max_value=100)


class SecurityEventSerializer(serializers.Serializer):
    """Serializer for security events"""
    event_type = serializers.CharField()
    description = serializers.CharField()
    risk_level = serializers.CharField()
    created_at = serializers.DateTimeField()
    ip_address = serializers.IPAddressField(allow_null=True)
    metadata = serializers.JSONField()


class MFASecurityReportSerializer(serializers.Serializer):
    """Serializer for comprehensive MFA security report"""
    user_id = serializers.UUIDField()
    mfa_status = MFAStatusSerializer()
    security_score = serializers.IntegerField(min_value=0, max_value=100)
    recent_security_events = SecurityEventSerializer(many=True)
    recommendations = serializers.ListField(
        child=serializers.DictField()
    )


# Response format serializers
class TOTPSetupResponseSerializer(serializers.Serializer):
    """Response format for TOTP setup"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(required=False, allow_null=True)


class MFAVerifyResponseSerializer(serializers.Serializer):
    """Response format for MFA verification"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    method = serializers.CharField(allow_null=True)
    remaining_backup_codes = serializers.IntegerField(required=False)
    warning = serializers.CharField(required=False)


class BackupCodeResponseSerializer(serializers.Serializer):
    """Response format for backup code operations"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(required=False)