"""
UX Serializers - Data validation for user experience endpoints
"""
from rest_framework import serializers


class AuthStatusResponseSerializer(serializers.Serializer):
    """Authentication status response serializer"""
    authenticated = serializers.BooleanField(help_text="Whether user is authenticated")
    show_prompt = serializers.BooleanField(help_text="Whether to show auth prompt")
    context = serializers.ChoiceField(
        choices=[
            ('general', 'General'),
            ('engaged_browsing', 'Engaged Browsing'),
            ('active_user', 'Active User'),
        ],
        help_text="Context for the auth prompt"
    )
    prompt_dismissed_count = serializers.IntegerField(
        help_text="Number of times prompt was dismissed",
        required=False
    )
    user = serializers.DictField(
        required=False,
        help_text="User data if authenticated"
    )


class PromptActionResponseSerializer(serializers.Serializer):
    """Auth prompt action response serializer"""
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class HealthCheckResponseSerializer(serializers.Serializer):
    """Health check response serializer"""
    status = serializers.CharField(help_text="Service status")
    service = serializers.CharField(help_text="Service name")
    version = serializers.CharField(help_text="Service version")
    timestamp = serializers.CharField(help_text="Current timestamp")