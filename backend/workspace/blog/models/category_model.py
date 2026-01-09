# Blog Category Model
from django.db import models
from django.utils.text import slugify
from workspace.core.models.base_models import TenantScopedModel


class Category(TenantScopedModel):
    """Blog category model"""
    
    # Core fields
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    
    # Override workspace field to specify related_name
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='blog_categories'
    )
    
    class Meta:
        db_table = 'workspace_blog_categories'
        unique_together = ['workspace', 'slug']
        ordering = ['name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return f"{self.workspace.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)