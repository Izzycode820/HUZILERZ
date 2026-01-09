# Blog Media Serializers
from rest_framework import serializers
from django.apps import apps


class MediaSerializer(serializers.ModelSerializer):
    """Media serializer"""
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = None  # Will be set in __init__
        fields = [
            'id', 'file_url', 'alt_text', 'media_type', 
            'file_size_mb', 'created_at'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Media')
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size_mb(self, obj):
        """Get file size in MB"""
        if obj.file_size:
            return round(obj.file_size / 1024 / 1024, 2)
        return 0


class MediaUploadSerializer(serializers.ModelSerializer):
    """Media upload serializer"""
    file = serializers.FileField()
    
    class Meta:
        model = None  # Will be set in __init__
        fields = ['file', 'alt_text', 'media_type']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Media')
    
    def validate_media_type(self, value):
        if value not in ['image', 'video', 'document']:
            raise serializers.ValidationError("Invalid media type")
        return value
    
    def create(self, validated_data):
        from ..services.media_service import MediaService
        
        workspace = self.context['workspace']
        file = validated_data['file']
        alt_text = validated_data.get('alt_text', '')
        media_type = validated_data.get('media_type', 'image')
        post = self.context.get('post')
        
        return MediaService.upload_media(
            workspace=workspace,
            file=file,
            alt_text=alt_text,
            post=post,
            media_type=media_type
        )