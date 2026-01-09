# Blog Profile Model
from django.db import models
from workspace.core.models.base_models import BaseWorkspaceExtension


class BlogProfile(BaseWorkspaceExtension):
    """Blog workspace profile with blog-specific settings"""
    
    # Core settings
    blog_title = models.CharField(max_length=200, default='My Blog')
    tagline = models.CharField(max_length=300, blank=True)
    posts_per_page = models.PositiveIntegerField(default=10)
    allow_comments = models.BooleanField(default=True)
    moderate_comments = models.BooleanField(default=True)
    
    # SEO settings
    meta_description = models.TextField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Social settings
    social_sharing = models.BooleanField(default=True)
    
    # Relationships
    
    class Meta:
        db_table = 'workspace_blog_profiles'
        verbose_name = 'Blog Profile'
        verbose_name_plural = 'Blog Profiles'
    
    def __str__(self):
        return f"Blog Profile: {self.workspace.name}"