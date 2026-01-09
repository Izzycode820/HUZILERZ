# Blog Media Model
from django.db import models
from workspace.core.models.base_models import TenantScopedModel


class Media(TenantScopedModel):
    """Media files model for blog - images, videos, documents"""
    
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'), 
        ('document', 'Document'),
    ]
    
    # Core fields
    file = models.FileField(upload_to='blog/media/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True, help_text='Alt text for accessibility')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES, default='image')
    
    # Relationships
    post = models.ForeignKey(
        'blog.Post',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media_files',
        help_text='Nullable since media might also be used globally in workspace'
    )
    
    class Meta:
        db_table = 'workspace_blog_media'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'media_type']),
            models.Index(fields=['post']),
        ]
    
    def __str__(self):
        return f"{self.media_type.title()}: {self.file.name}"
    
    @property
    def file_size(self):
        """Get file size in bytes"""
        try:
            return self.file.size
        except (OSError, ValueError):
            return 0
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.file.name:
            return self.file.name.split('.')[-1].lower()
        return None