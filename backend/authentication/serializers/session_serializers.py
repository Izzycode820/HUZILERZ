"""
Session Serializers - Data validation for session management
"""
from rest_framework import serializers


class SessionSerializer(serializers.Serializer):
    """Active session serializer"""
    id = serializers.UUIDField(help_text="Session ID")
    device_name = serializers.CharField(help_text="Device name/info")
    ip_address = serializers.IPAddressField(help_text="Last known IP address")
    last_used = serializers.DateTimeField(help_text="Last activity timestamp")
    created_at = serializers.DateTimeField(help_text="Session creation timestamp")
    is_current = serializers.BooleanField(help_text="Whether this is the current session")


class RevokeSessionSerializer(serializers.Serializer):
    """Revoke session request serializer"""
    session_id = serializers.UUIDField(
        help_text="ID of the session to revoke"
    )


class SessionsResponseSerializer(serializers.Serializer):
    """Active sessions response serializer"""
    success = serializers.BooleanField()
    sessions = SessionSerializer(many=True, required=False)
    error = serializers.CharField(required=False)


class SessionActionResponseSerializer(serializers.Serializer):
    """Session action response serializer"""
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)