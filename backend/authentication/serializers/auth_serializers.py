"""
Authentication Serializers - Data validation for auth endpoints
"""
import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Login request serializer"""
    email = serializers.EmailField(
        max_length=255,
        help_text="User's email address"
    )
    password = serializers.CharField(
        max_length=128,
        style={'input_type': 'password'},
        help_text="User's password"
    )
    remember_me = serializers.BooleanField(
        default=False,
        help_text="Keep user logged in for extended period"
    )

    def validate_email(self, value):
        """Validate and normalize email"""
        return value.lower().strip()


class RegisterSerializer(serializers.Serializer):
    """User registration serializer"""
    email = serializers.EmailField(
        max_length=255,
        help_text="User's email address"
    )
    password = serializers.CharField(
        max_length=128,
        style={'input_type': 'password'},
        help_text="User's password (minimum 8 characters)"
    )
    first_name = serializers.CharField(
        max_length=30,
        help_text="User's first name"
    )
    last_name = serializers.CharField(
        max_length=30,
        help_text="User's last name"
    )
    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="User's phone number (E.164 format preferred)"
    )
    username = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="Optional username (will be generated from email if not provided)"
    )

    def validate_email(self, value):
        """Validate and normalize email"""
        email = value.lower().strip()
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        
        return email

    def validate_password(self, value):
        """Validate password strength"""
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        return value

    def validate_phone_number(self, value):
        """Validate and normalize phone number"""
        if not value:
            return value
        
        # Remove formatting characters
        cleaned = ''.join(c for c in value if c.isdigit() or c == '+')
        
        # Basic validation: 8-15 digits, optionally starting with +
        if not re.match(r'^\+?[0-9]{8,15}$', cleaned):
            raise serializers.ValidationError("Please enter a valid phone number.")
        
        # Check if phone already exists
        if User.objects.filter(phone_number=cleaned).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        
        return cleaned

    def validate_username(self, value):
        """Validate username uniqueness if provided"""
        if value:
            username = value.strip()
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError("Username is already taken.")
            return username
        return value

    def validate_first_name(self, value):
        """Validate first name"""
        return value.strip()

    def validate_last_name(self, value):
        """Validate last name"""
        return value.strip()


class RefreshTokenSerializer(serializers.Serializer):
    """Refresh token request serializer"""
    # No fields needed as refresh token comes from httpOnly cookie
    pass


class WorkspaceSwitchSerializer(serializers.Serializer):
    """Workspace switch request serializer"""
    workspace_id = serializers.UUIDField(
        help_text="UUID of the workspace to switch to"
    )


class TokenResponseSerializer(serializers.Serializer):
    """Token response serializer for documentation"""
    success = serializers.BooleanField()
    access_token = serializers.CharField(help_text="JWT access token")
    token_type = serializers.CharField(default="Bearer")
    expires_in = serializers.IntegerField(help_text="Token expiration time in seconds")
    message = serializers.CharField(required=False)


class UserDataSerializer(serializers.Serializer):
    """User data serializer for responses"""
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()
    email_verified = serializers.BooleanField()
    two_factor_enabled = serializers.BooleanField()


class AuthResponseSerializer(serializers.Serializer):
    """Complete authentication response serializer"""
    success = serializers.BooleanField()
    user = UserDataSerializer(required=False)
    access_token = serializers.CharField(required=False)
    token_type = serializers.CharField(required=False)
    expires_in = serializers.IntegerField(required=False)
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class WorkspaceMembershipSerializer(serializers.Serializer):
    """Workspace membership data (v3.0 - Header-Based Context)"""
    role = serializers.ChoiceField(
        choices=['owner', 'admin', 'member', 'viewer'],
        help_text="User's role in the workspace"
    )
    permissions = serializers.ListField(
        child=serializers.CharField(),
        help_text="User's permissions in the workspace"
    )
    joined_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="When the user joined the workspace"
    )


class WorkspaceDetailsSerializer(serializers.Serializer):
    """Workspace details data (v3.0 - Header-Based Context)"""
    id = serializers.UUIDField(help_text="Workspace UUID")
    name = serializers.CharField(help_text="Workspace name")
    type = serializers.ChoiceField(
        choices=['store', 'blog', 'services', 'portfolio'],
        help_text="Workspace type"
    )
    status = serializers.ChoiceField(
        choices=['active', 'suspended'],
        help_text="Workspace status"
    )
    owner_id = serializers.CharField(help_text="Owner user ID")
    created_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Workspace creation date"
    )


class WorkspaceSwitchResponseSerializer(serializers.Serializer):
    """
    Workspace switch response (v3.0 - NO tokens)

    Industry Standard: Shopify/Stripe/Linear
    - Backend validates access and returns workspace details
    - Frontend updates Zustand + sends X-Workspace-Id header
    """
    success = serializers.BooleanField()
    workspace = WorkspaceDetailsSerializer(required=False)
    membership = WorkspaceMembershipSerializer(required=False)
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class LeaveWorkspaceResponseSerializer(serializers.Serializer):
    """
    Leave workspace response (v3.0 - NO tokens)

    Stateless operation - just logs the event
    """
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)