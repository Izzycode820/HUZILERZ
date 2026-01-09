# Abstract Base Models - DRY principles for workspace extensions

import uuid
from django.db import models
from django.conf import settings


class BaseWorkspaceExtension(models.Model):
    """
    Abstract base model for all workspace extensions
    Provides common fields and methods for Store, blog, service, restaurant models
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField(
        'workspace_core.Workspace', 
        on_delete=models.CASCADE, 
        related_name='%(class)s_extension'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.__class__.__name__} - {self.workspace.name}"
    
    @property
    def workspace_type(self):
        """Get workspace type"""
        return self.workspace.type
    
    @property
    def workspace_owner(self):
        """Get workspace owner"""
        return self.workspace.owner
    
    def can_user_access(self, user):
        """Check if user can access this extension"""
        return self.workspace.can_user_access(user)


class TenantScopedModel(models.Model):
    """
    Abstract base model for all models that belong to a workspace
    Ensures proper tenant isolation
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        help_text="Workspace this record belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', '-created_at']),
        ]
    
    def clean(self):
        """Validate tenant isolation"""
        if not hasattr(self, 'workspace') or not self.workspace:
            from django.core.exceptions import ValidationError
            raise ValidationError("All records must belong to a workspace")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TimestampedModel(models.Model):
    """
    Abstract base model providing timestamp fields
    """
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base model providing soft delete functionality
    """
    
    is_active = models.BooleanField(default=True, help_text="Whether this record is active")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this record was deleted")
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete this record"""
        from django.utils import timezone
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])
    
    def restore(self):
        """Restore soft deleted record"""
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=['is_active', 'deleted_at'])


class UserTrackingModel(models.Model):
    """
    Abstract base model for tracking user actions
    """
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_%(class)s_set',
        help_text="User who created this record"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_%(class)s_set',
        help_text="User who last updated this record"
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Note: In real implementation, you'd get current user from context
        # This is just the base structure
        super().save(*args, **kwargs)


class BaseWorkspaceContentModel(TenantScopedModel, SoftDeleteModel, UserTrackingModel):
    """
    Complete base model for workspace content
    Combines tenant scoping, soft delete, and user tracking
    """
    
    title = models.CharField(max_length=255, help_text="Content title")
    description = models.TextField(blank=True, help_text="Content description")
    
    # Status and visibility
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('archived', 'Archived'),
        ],
        default='draft'
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['workspace', 'status', '-created_at']),
            models.Index(fields=['workspace', 'is_active']),
        ]
    
    def publish(self):
        """Publish this content"""
        self.status = 'published'
        self.save(update_fields=['status'])
    
    def archive(self):
        """Archive this content"""
        self.status = 'archived'
        self.save(update_fields=['status'])
    
    @property
    def is_published(self):
        """Check if content is published"""
        return self.status == 'published' and self.is_active