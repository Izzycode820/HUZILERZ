# Blog Comment Service
from django.db import transaction
from django.core.exceptions import ValidationError
from django.apps import apps
import logging

logger = logging.getLogger('workspace.blog.services')


class CommentService:
    """Service for blog comment operations"""
    
    @staticmethod
    def create_comment(post, user=None, guest_name=None, guest_email=None, body=None):
        """Create a new comment"""
        Comment = apps.get_model('blog', 'Comment')
        
        if not body:
            raise ValidationError("Comment body is required")
        
        if not user and not (guest_name and guest_email):
            raise ValidationError("Either user or guest information is required")
        
        try:
            with transaction.atomic():
                comment_data = {
                    'post': post,
                    'body': body,
                    'status': 'pending' if post.workspace.blog_profile.moderate_comments else 'approved'
                }
                
                if user:
                    comment_data['user'] = user
                else:
                    comment_data['guest_name'] = guest_name
                    comment_data['guest_email'] = guest_email
                
                comment = Comment.objects.create(**comment_data)
                
                logger.info(f"Comment created on post: {post.title}")
                return comment
                
        except Exception as e:
            logger.error(f"Failed to create comment: {str(e)}")
            raise ValidationError(f"Failed to create comment: {str(e)}")
    
    @staticmethod
    def moderate_comment(comment, status, user):
        """Moderate a comment (approve, reject, mark as spam)"""
        if status not in ['pending', 'approved', 'spam']:
            raise ValidationError("Invalid comment status")
        
        try:
            with transaction.atomic():
                comment.status = status
                comment.save()
                
                logger.info(f"Comment {comment.id} status changed to {status}")
                return comment
                
        except Exception as e:
            logger.error(f"Failed to moderate comment: {str(e)}")
            raise ValidationError(f"Failed to moderate comment: {str(e)}")
    
    @staticmethod
    def delete_comment(comment, user):
        """Delete a comment"""
        try:
            with transaction.atomic():
                post_title = comment.post.title
                comment.delete()
                
                logger.info(f"Comment deleted from post: {post_title}")
                
        except Exception as e:
            logger.error(f"Failed to delete comment: {str(e)}")
            raise ValidationError(f"Failed to delete comment: {str(e)}")
    
    @staticmethod
    def get_post_comments(post, status='approved'):
        """Get comments for a post"""
        Comment = apps.get_model('blog', 'Comment')
        
        queryset = Comment.objects.filter(post=post)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('user').order_by('created_at')
    
    @staticmethod
    def get_workspace_comments(workspace, status=None):
        """Get all comments for workspace"""
        Comment = apps.get_model('blog', 'Comment')
        Post = apps.get_model('blog', 'Post')
        
        queryset = Comment.objects.filter(post__workspace=workspace)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('post', 'user').order_by('-created_at')