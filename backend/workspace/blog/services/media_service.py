# Blog Media Service
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.apps import apps
import logging
import os

logger = logging.getLogger('workspace.blog.services')


class MediaService:
    """Service for blog media operations"""
    
    ALLOWED_IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    ALLOWED_VIDEO_TYPES = ['mp4', 'avi', 'mov', 'wmv', 'flv']
    ALLOWED_DOCUMENT_TYPES = ['pdf', 'doc', 'docx', 'txt', 'rtf']
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def upload_media(workspace, file, alt_text='', post=None, media_type='image'):
        """Upload media file"""
        Media = apps.get_model('blog', 'Media')
        
        # Validate file
        if not MediaService._validate_file(file, media_type):
            raise ValidationError("Invalid file type or size")
        
        try:
            with transaction.atomic():
                media = Media.objects.create(
                    workspace=workspace,
                    post=post,
                    file=file,
                    alt_text=alt_text,
                    media_type=media_type
                )
                
                logger.info(f"Media uploaded: {file.name} to {workspace.name}")
                return media
                
        except Exception as e:
            logger.error(f"Failed to upload media: {str(e)}")
            raise ValidationError(f"Failed to upload media: {str(e)}")
    
    @staticmethod
    def delete_media(media, user):
        """Delete media file"""
        try:
            with transaction.atomic():
                # Delete file from storage
                if media.file:
                    default_storage.delete(media.file.name)
                
                file_name = media.file.name
                workspace_name = media.workspace.name
                media.delete()
                
                logger.info(f"Media deleted: {file_name} from {workspace_name}")
                
        except Exception as e:
            logger.error(f"Failed to delete media: {str(e)}")
            raise ValidationError(f"Failed to delete media: {str(e)}")
    
    @staticmethod
    def get_workspace_media(workspace, media_type=None, post=None):
        """Get media for workspace"""
        Media = apps.get_model('blog', 'Media')
        
        queryset = Media.objects.filter(workspace=workspace)
        
        if media_type:
            queryset = queryset.filter(media_type=media_type)
        
        if post:
            queryset = queryset.filter(post=post)
        elif post is None:
            # Get only unattached media
            queryset = queryset.filter(post__isnull=True)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def attach_media_to_post(media, post):
        """Attach media to a post"""
        try:
            media.post = post
            media.save()
            
            logger.info(f"Media {media.id} attached to post: {post.title}")
            return media
            
        except Exception as e:
            logger.error(f"Failed to attach media to post: {str(e)}")
            raise ValidationError(f"Failed to attach media to post: {str(e)}")
    
    @staticmethod
    def _validate_file(file, media_type):
        """Validate uploaded file"""
        if not file:
            return False
        
        # Check file size
        if file.size > MediaService.MAX_FILE_SIZE:
            raise ValidationError(f"File size too large. Maximum size is {MediaService.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Check file extension
        file_extension = os.path.splitext(file.name)[1][1:].lower()
        
        if media_type == 'image' and file_extension not in MediaService.ALLOWED_IMAGE_TYPES:
            raise ValidationError(f"Invalid image type. Allowed types: {', '.join(MediaService.ALLOWED_IMAGE_TYPES)}")
        elif media_type == 'video' and file_extension not in MediaService.ALLOWED_VIDEO_TYPES:
            raise ValidationError(f"Invalid video type. Allowed types: {', '.join(MediaService.ALLOWED_VIDEO_TYPES)}")
        elif media_type == 'document' and file_extension not in MediaService.ALLOWED_DOCUMENT_TYPES:
            raise ValidationError(f"Invalid document type. Allowed types: {', '.join(MediaService.ALLOWED_DOCUMENT_TYPES)}")
        
        return True