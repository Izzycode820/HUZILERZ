# Blog Tag Model
from django.db import models
from django.utils.text import slugify
from workspace.core.models.base_models import TenantScopedModel


class Tag(TenantScopedModel):
    """Blog tag model - optional if you want tags separate from categories"""
    
    # Core fields
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, blank=True)
    
    # Relationships (tags can be used across workspaces or workspace-specific)
    
    class Meta:
        db_table = 'workspace_blog_tags'
        unique_together = ['workspace', 'slug']
        ordering = ['name']
    
    def __str__(self):
        if self.workspace:
            return f"{self.workspace.name} - {self.name}"
        return f"Global - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)