# Blog Post Service
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.text import slugify
from django.utils import timezone
from django.apps import apps
import logging

logger = logging.getLogger('workspace.blog.services')


class PostService:
    """Service for blog post operations"""
    
    @staticmethod
    def create_post(workspace, user, **post_data):
        """Create a new blog post"""
        Post = apps.get_model('blog', 'Post')
        
        try:
            with transaction.atomic():
                # Ensure slug uniqueness
                original_slug = slugify(post_data['title'])
                slug = original_slug
                counter = 1
                
                while Post.objects.filter(workspace=workspace, slug=slug).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                
                post_data['slug'] = slug
                post_data['workspace'] = workspace
                
                post = Post.objects.create(**post_data)
                
                logger.info(f"Blog post created: {post.title} in {workspace.name}")
                return post
                
        except Exception as e:
            logger.error(f"Failed to create post: {str(e)}")
            raise ValidationError(f"Failed to create post: {str(e)}")
    
    @staticmethod
    def update_post(post, user, **update_data):
        """Update blog post"""
        try:
            with transaction.atomic():
                # Update fields
                for field, value in update_data.items():
                    if hasattr(post, field):
                        setattr(post, field, value)
                
                # Handle slug update if title changed
                if 'title' in update_data and update_data['title'] != post.title:
                    new_slug = slugify(update_data['title'])
                    if new_slug != post.slug:
                        Post = apps.get_model('blog', 'Post')
                        counter = 1
                        original_slug = new_slug
                        
                        while Post.objects.filter(
                            workspace=post.workspace, 
                            slug=new_slug
                        ).exclude(id=post.id).exists():
                            new_slug = f"{original_slug}-{counter}"
                            counter += 1
                        
                        post.slug = new_slug
                
                # Handle publishing
                if 'status' in update_data:
                    if update_data['status'] == 'published' and not post.published_at:
                        post.published_at = timezone.now()
                    elif update_data['status'] == 'draft':
                        post.published_at = None
                
                post.save()
                
                logger.info(f"Blog post updated: {post.title}")
                return post
                
        except Exception as e:
            logger.error(f"Failed to update post: {str(e)}")
            raise ValidationError(f"Failed to update post: {str(e)}")
    
    @staticmethod
    def delete_post(post, user):
        """Delete blog post"""
        try:
            with transaction.atomic():
                post_title = post.title
                workspace_name = post.workspace.name
                post.delete()
                
                logger.info(f"Blog post deleted: {post_title} from {workspace_name}")
                
        except Exception as e:
            logger.error(f"Failed to delete post: {str(e)}")
            raise ValidationError(f"Failed to delete post: {str(e)}")
    
    @staticmethod
    def get_workspace_posts(workspace, status=None, published_only=False):
        """Get posts for workspace"""
        Post = apps.get_model('blog', 'Post')
        
        queryset = Post.objects.filter(workspace=workspace)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if published_only:
            queryset = queryset.filter(
                status='published',
                published_at__lte=timezone.now()
            )
        
        return queryset.select_related('category').prefetch_related('tags')
    
    @staticmethod
    def search_posts(workspace, query):
        """Search posts by title and content"""
        from django.db.models import Q
        Post = apps.get_model('blog', 'Post')
        
        return Post.objects.filter(
            workspace=workspace,
            status='published'
        ).filter(
            Q(title__icontains=query) | Q(body__icontains=query)
        ).select_related('category').prefetch_related('tags')