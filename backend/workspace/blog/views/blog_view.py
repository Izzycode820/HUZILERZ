# Blog Views
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.apps import apps
from django.db.models import Q

from ..serializers.post_serializer import (
    PostListSerializer, PostDetailSerializer, PostCreateUpdateSerializer
)
from ..serializers.comment_serializer import (
    CommentSerializer, CommentCreateSerializer, CommentModerationSerializer
)
from ..serializers.media_serializer import MediaSerializer, MediaUploadSerializer
from ..services.post_service import PostService
from ..services.comment_service import CommentService
from ..services.media_service import MediaService


class BlogViewSet(viewsets.ModelViewSet):
    """Blog management viewset"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        workspace = self.get_workspace()
        return PostService.get_workspace_posts(workspace)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer
    
    def get_workspace(self):
        """Get workspace from URL params or user context"""
        # This would typically come from URL pattern or user's current workspace
        # For now, we'll assume it's passed in context
        return self.request.user.current_workspace  # Adjust based on your auth system
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['workspace'] = self.get_workspace()
        return context
    
    def list(self, request, *args, **kwargs):
        """List posts with filtering and search"""
        queryset = self.get_queryset()
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(body__icontains=search)
            )
        
        # Filter by category
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create new blog post"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        
        # Return full post details
        detail_serializer = PostDetailSerializer(post, context=self.get_serializer_context())
        
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Get or create comments for a post"""
        post = self.get_object()
        
        if request.method == 'GET':
            comments = CommentService.get_post_comments(post, status='approved')
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Check if comments are allowed
            if not post.workspace.blog_profile.allow_comments:
                return Response(
                    {'error': 'Comments are disabled for this blog'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = CommentCreateSerializer(
                data=request.data,
                context={'request': request, 'post': post}
            )
            serializer.is_valid(raise_exception=True)
            comment = serializer.save()
            
            response_serializer = CommentSerializer(comment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get blog categories for workspace"""
        workspace = self.get_workspace()
        Category = apps.get_model('blog', 'Category')
        
        categories = Category.objects.filter(workspace=workspace)
        
        from ..serializers.post_serializer import CategorySerializer
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tags(self, request):
        """Get blog tags for workspace"""
        workspace = self.get_workspace()
        Tag = apps.get_model('blog', 'Tag')
        
        tags = Tag.objects.filter(workspace=workspace)
        
        from ..serializers.post_serializer import TagSerializer
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'post'], parser_classes=[MultiPartParser, FormParser])
    def media(self, request):
        """Get or upload media files"""
        workspace = self.get_workspace()
        
        if request.method == 'GET':
            media_type = request.query_params.get('type')
            media_files = MediaService.get_workspace_media(
                workspace, media_type=media_type
            )
            serializer = MediaSerializer(
                media_files, many=True, context={'request': request}
            )
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = MediaUploadSerializer(
                data=request.data,
                context={'workspace': workspace, 'request': request}
            )
            serializer.is_valid(raise_exception=True)
            media = serializer.save()
            
            response_serializer = MediaSerializer(
                media, context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CommentModerationViewSet(viewsets.ModelViewSet):
    """Comment moderation viewset for blog owners"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CommentModerationSerializer
    
    def get_queryset(self):
        workspace = self.get_workspace()
        return CommentService.get_workspace_comments(workspace)
    
    def get_workspace(self):
        """Get workspace from URL params or user context"""
        return self.request.user.current_workspace  # Adjust based on your auth system
    
    @action(detail=True, methods=['post'])
    def moderate(self, request, pk=None):
        """Moderate a comment"""
        comment = self.get_object()
        status_value = request.data.get('status')
        
        if not status_value:
            return Response(
                {'error': 'Status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            updated_comment = CommentService.moderate_comment(
                comment, status_value, request.user
            )
            serializer = CommentSerializer(updated_comment)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )