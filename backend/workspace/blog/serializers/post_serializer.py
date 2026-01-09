# Blog Post Serializers
from rest_framework import serializers
from django.apps import apps


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    
    class Meta:
        model = None  # Will be set in __init__
        fields = ['id', 'name', 'slug']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Category')


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer"""
    
    class Meta:
        model = None  # Will be set in __init__
        fields = ['id', 'name', 'slug']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Tag')


class PostListSerializer(serializers.ModelSerializer):
    """Post list serializer - lightweight for listing"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()
    
    class Meta:
        model = None  # Will be set in __init__
        fields = [
            'id', 'title', 'slug', 'status', 'published_at', 
            'created_at', 'category', 'tags', 'comments_count', 'excerpt'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Post')
    
    def get_comments_count(self, obj):
        return obj.comments.filter(status='approved').count()
    
    def get_excerpt(self, obj):
        """Get first 150 characters of body"""
        if len(obj.body) > 150:
            return obj.body[:150] + '...'
        return obj.body


class PostDetailSerializer(serializers.ModelSerializer):
    """Post detail serializer - full content"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    media_files = serializers.SerializerMethodField()
    
    class Meta:
        model = None  # Will be set in __init__
        fields = [
            'id', 'title', 'slug', 'body', 'status', 'published_at',
            'created_at', 'updated_at', 'category', 'tags', 'media_files'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Post')
    
    def get_media_files(self, obj):
        from .media_serializer import MediaSerializer
        return MediaSerializer(obj.media_files.all(), many=True).data


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Post create/update serializer"""
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = None  # Will be set in __init__
        fields = [
            'title', 'body', 'status', 'category_id', 'tag_ids'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = apps.get_model('blog', 'Post')
    
    def validate(self, data):
        # Validate category belongs to workspace
        if 'category_id' in data and data['category_id']:
            Category = apps.get_model('blog', 'Category')
            workspace = self.context.get('workspace')
            try:
                category = Category.objects.get(
                    id=data['category_id'], 
                    workspace=workspace
                )
                data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError("Invalid category for this workspace")
        
        # Validate tags belong to workspace
        if 'tag_ids' in data and data['tag_ids']:
            Tag = apps.get_model('blog', 'Tag')
            workspace = self.context.get('workspace')
            tags = Tag.objects.filter(
                id__in=data['tag_ids'],
                workspace=workspace
            )
            if len(tags) != len(data['tag_ids']):
                raise serializers.ValidationError("Some tags are invalid for this workspace")
            data['tags'] = tags
        
        return data
    
    def create(self, validated_data):
        from ..services.post_service import PostService
        
        workspace = self.context['workspace']
        user = self.context['request'].user
        
        # Remove many-to-many fields
        tags = validated_data.pop('tags', [])
        tag_ids = validated_data.pop('tag_ids', None)
        category_id = validated_data.pop('category_id', None)
        
        # Create post
        post = PostService.create_post(workspace, user, **validated_data)
        
        # Set tags
        if tags:
            post.tags.set(tags)
        
        return post
    
    def update(self, instance, validated_data):
        from ..services.post_service import PostService
        
        user = self.context['request'].user
        
        # Remove many-to-many fields
        tags = validated_data.pop('tags', None)
        tag_ids = validated_data.pop('tag_ids', None)
        category_id = validated_data.pop('category_id', None)
        
        # Update post
        post = PostService.update_post(instance, user, **validated_data)
        
        # Update tags if provided
        if tags is not None:
            post.tags.set(tags)
        
        return post