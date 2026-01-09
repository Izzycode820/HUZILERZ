# Blog Comment Serializers
from rest_framework import serializers
from django.apps import apps


class CommentSerializer(serializers.ModelSerializer):
    """Comment serializer"""
    author_name = serializers.ReadOnlyField()
    author_email = serializers.ReadOnlyField()
    
    class Meta:
        model = None  # Will be set in __init__
        fields = [
            'id', 'body', 'status', 'created_at', 
            'author_name', 'author_email'
        ]
        read_only_fields = ['status', 'created_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Comment')


class CommentCreateSerializer(serializers.ModelSerializer):
    """Comment creation serializer"""
    guest_name = serializers.CharField(required=False, allow_blank=True)
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    
    class Meta:
        model = None  # Will be set in __init__
        fields = ['body', 'guest_name', 'guest_email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Comment')
    
    def validate(self, data):
        user = self.context['request'].user
        
        # If user is not authenticated, require guest info
        if not user.is_authenticated:
            if not data.get('guest_name') or not data.get('guest_email'):
                raise serializers.ValidationError(
                    "Guest name and email are required for anonymous comments"
                )
        
        return data
    
    def create(self, validated_data):
        from ..services.comment_service import CommentService
        
        post = self.context['post']
        user = self.context['request'].user
        
        if user.is_authenticated:
            return CommentService.create_comment(
                post=post,
                user=user,
                body=validated_data['body']
            )
        else:
            return CommentService.create_comment(
                post=post,
                guest_name=validated_data['guest_name'],
                guest_email=validated_data['guest_email'],
                body=validated_data['body']
            )


class CommentModerationSerializer(serializers.ModelSerializer):
    """Comment moderation serializer"""
    
    class Meta:
        model = None  # Will be set in __init__
        fields = ['status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Comment')
    
    def validate_status(self, value):
        if value not in ['pending', 'approved', 'spam']:
            raise serializers.ValidationError("Invalid status")
        return value
    
    def update(self, instance, validated_data):
        from ..services.comment_service import CommentService
        
        user = self.context['request'].user
        status = validated_data['status']
        
        return CommentService.moderate_comment(instance, status, user)