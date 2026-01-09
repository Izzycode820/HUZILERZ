"""
Profile Serializers - Data validation for profile endpoints
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'avatar', 'bio', 'email_verified', 'phone_number', 'phone_verified',
            'two_factor_enabled', 'preferred_auth_method',
            'security_notifications', 'created_at', 'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'email_verified', 'phone_number', 'phone_verified',
            'created_at', 'last_login'
        ]


class UpdateProfileSerializer(serializers.Serializer):
    """Profile update request serializer"""
    first_name = serializers.CharField(
        max_length=30,
        required=False,
        help_text="User's first name"
    )
    last_name = serializers.CharField(
        max_length=30,
        required=False,
        help_text="User's last name"
    )
    username = serializers.CharField(
        max_length=150,
        required=False,
        help_text="Unique username"
    )
    bio = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="User's bio (up to 500 characters)"
    )
    avatar = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL to user's avatar image"
    )
    preferred_auth_method = serializers.ChoiceField(
        choices=[
            ('password', 'Password'),
            ('social', 'Social Login'),
            ('passwordless', 'Passwordless'),
        ],
        required=False,
        help_text="User's preferred authentication method"
    )
    security_notifications = serializers.BooleanField(
        required=False,
        help_text="Whether to receive security notifications"
    )

    def validate_username(self, value):
        """Validate username uniqueness"""
        if value:
            username = value.strip()
            user = self.context.get('user')
            if user and username != user.username:
                if User.objects.filter(username=username).exists():
                    raise serializers.ValidationError("Username is already taken.")
            return username
        return value

    def validate_first_name(self, value):
        """Validate and clean first name"""
        return value.strip() if value else value

    def validate_last_name(self, value):
        """Validate and clean last name"""
        return value.strip() if value else value


class ProfileResponseSerializer(serializers.Serializer):
    """Profile response serializer"""
    success = serializers.BooleanField()
    user = ProfileSerializer(required=False)
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)