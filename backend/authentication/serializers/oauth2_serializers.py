"""
Enterprise OAuth2 Serializers - 2025 Security Standards
Validation for Google and Apple OAuth2 authentication flows
"""
from rest_framework import serializers
import re


class OAuth2InitiateSerializer(serializers.Serializer):
    """Serializer for initiating OAuth2 flow"""
    
    SUPPORTED_PROVIDERS = ['google', 'apple']
    
    provider = serializers.ChoiceField(
        choices=SUPPORTED_PROVIDERS,
        help_text="OAuth2 provider to use for authentication"
    )
    
    redirect_uri = serializers.URLField(
        help_text="Callback URL where the authorization code will be sent"
    )
    
    state = serializers.CharField(
        max_length=256,
        required=False,
        help_text="Optional state parameter for CSRF protection"
    )
    
    def validate_redirect_uri(self, value):
        """Validate redirect URI format and security"""
        # Ensure HTTPS for production (allow HTTP for development)
        if not value.startswith(('https://', 'http://localhost', 'http://127.0.0.1')):
            raise serializers.ValidationError(
                "Redirect URI must use HTTPS or be localhost for development"
            )
        
        # Basic URL validation
        if len(value) > 2000:
            raise serializers.ValidationError("Redirect URI is too long")
        
        return value
    
    def validate_state(self, value):
        """Validate state parameter"""
        if value:
            # Remove potentially dangerous characters
            if re.search(r'[<>"\'/\\&]', value):
                raise serializers.ValidationError("State parameter contains invalid characters")
            
            if len(value) < 8:
                raise serializers.ValidationError("State parameter should be at least 8 characters")
        
        return value


class OAuth2CallbackSerializer(serializers.Serializer):
    """Serializer for OAuth2 callback processing"""
    
    code = serializers.CharField(
        max_length=512,
        required=False,
        help_text="Authorization code from OAuth2 provider"
    )
    
    state = serializers.CharField(
        max_length=256,
        help_text="State parameter from authorization request"
    )
    
    error = serializers.CharField(
        max_length=100,
        required=False,
        help_text="OAuth2 error code if authentication failed"
    )
    
    error_description = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Human-readable error description"
    )
    
    # Apple-specific fields
    user = serializers.CharField(
        required=False,
        help_text="Apple user data (JSON string) - only sent on first authorization"
    )
    
    id_token = serializers.CharField(
        required=False,
        help_text="Apple ID token (JWT)"
    )
    
    def validate(self, data):
        """Cross-field validation"""
        # Either code or error must be present
        if not data.get('code') and not data.get('error'):
            raise serializers.ValidationError(
                "Either 'code' or 'error' parameter is required"
            )
        
        # If error is present, code should not be
        if data.get('error') and data.get('code'):
            raise serializers.ValidationError(
                "Cannot have both 'error' and 'code' parameters"
            )
        
        return data
    
    def validate_code(self, value):
        """Validate authorization code format"""
        if value:
            # Remove whitespace
            value = value.strip()
            
            if len(value) < 10:
                raise serializers.ValidationError("Authorization code appears to be invalid")
            
            # Check for suspicious patterns
            if re.search(r'[<>"\'/\\]', value):
                raise serializers.ValidationError("Authorization code contains invalid characters")
        
        return value
    
    def validate_error(self, value):
        """Validate error code"""
        if value:
            # Common OAuth2 error codes
            valid_errors = [
                'access_denied',
                'invalid_request',
                'unsupported_response_type',
                'invalid_scope',
                'server_error',
                'temporarily_unavailable',
                'user_cancelled_authorize',
                'invalid_client'
            ]
            
            if value not in valid_errors:
                # Log suspicious error codes but don't reject
                pass
        
        return value


class OAuth2TokenRefreshSerializer(serializers.Serializer):
    """Serializer for OAuth2 token refresh"""
    
    provider = serializers.ChoiceField(
        choices=['google', 'apple'],
        help_text="OAuth2 provider"
    )
    
    refresh_token = serializers.CharField(
        max_length=1000,
        help_text="Valid refresh token from OAuth2 provider"
    )
    
    def validate_refresh_token(self, value):
        """Validate refresh token format"""
        value = value.strip()
        
        if len(value) < 20:
            raise serializers.ValidationError("Refresh token appears to be invalid")
        
        # Basic security check
        if re.search(r'[<>"\'/\\]', value):
            raise serializers.ValidationError("Refresh token contains invalid characters")
        
        return value


# Response serializers
class OAuth2UserSerializer(serializers.Serializer):
    """Serializer for OAuth2 user data"""
    
    id = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    is_new_user = serializers.BooleanField()


class OAuth2TokensSerializer(serializers.Serializer):
    """Serializer for OAuth2 authentication tokens"""
    
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default='Bearer')
    expires_in = serializers.IntegerField()


class OAuth2ProviderSerializer(serializers.Serializer):
    """Serializer for OAuth2 provider information"""
    
    name = serializers.CharField()
    display_name = serializers.CharField()
    icon = serializers.CharField()
    color = serializers.CharField()
    description = serializers.CharField()
    scopes = serializers.ListField(child=serializers.CharField())
    configured = serializers.BooleanField()


class OAuth2InitiateResponseSerializer(serializers.Serializer):
    """Response format for OAuth2 initiate"""
    
    success = serializers.BooleanField()
    data = serializers.DictField()


class OAuth2CallbackResponseSerializer(serializers.Serializer):
    """Response format for OAuth2 callback"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(required=False)


class OAuth2ProvidersResponseSerializer(serializers.Serializer):
    """Response format for OAuth2 providers list"""
    
    success = serializers.BooleanField()
    data = serializers.DictField()


# Apple-specific serializers
class AppleUserDataSerializer(serializers.Serializer):
    """Serializer for Apple user data (sent only on first authorization)"""
    
    name = serializers.DictField(required=False)
    email = serializers.EmailField(required=False)
    
    def validate_name(self, value):
        """Validate Apple name object"""
        if value:
            # Apple sends name as {"firstName": "John", "lastName": "Doe"}
            if not isinstance(value, dict):
                raise serializers.ValidationError("Name must be an object")
            
            # Sanitize name fields
            for key in ['firstName', 'lastName']:
                if key in value and value[key]:
                    if re.search(r'[<>"\'/\\]', value[key]):
                        raise serializers.ValidationError(f"Invalid characters in {key}")
        
        return value


class AppleIDTokenSerializer(serializers.Serializer):
    """Serializer for Apple ID Token validation"""
    
    # This would be used to validate the Apple ID Token (JWT)
    # In a full implementation, you'd decode and validate the JWT
    iss = serializers.CharField()  # Issuer (should be Apple)
    aud = serializers.CharField()  # Audience (your app's client ID)
    exp = serializers.IntegerField()  # Expiration time
    iat = serializers.IntegerField()  # Issued at time
    sub = serializers.CharField()  # Subject (user identifier)
    email = serializers.EmailField(required=False)
    email_verified = serializers.BooleanField(required=False)


# Validation mixins
class OAuth2ValidationMixin:
    """Mixin for common OAuth2 validation logic"""
    
    @staticmethod
    def validate_provider_support(provider):
        """Validate that provider is supported"""
        supported = ['google', 'apple']
        if provider not in supported:
            return False, f"Unsupported provider: {provider}. Supported: {', '.join(supported)}"
        return True, None
    
    @staticmethod
    def sanitize_oauth2_data(data):
        """Sanitize OAuth2 response data"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # Remove potentially dangerous characters
                    value = re.sub(r'[<>"\'/\\]', '', value)
                sanitized[key] = value
            return sanitized
        return data
    
    @staticmethod
    def validate_oauth2_state(state, expected_length=32):
        """Validate OAuth2 state parameter"""
        if not state:
            return False, "State parameter is required"
        
        if len(state) < expected_length:
            return False, f"State parameter should be at least {expected_length} characters"
        
        if re.search(r'[<>"\'/\\&]', state):
            return False, "State parameter contains invalid characters"
        
        return True, None