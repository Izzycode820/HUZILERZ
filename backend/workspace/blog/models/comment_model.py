# Blog Comment Model
from django.db import models
from django.contrib.auth import get_user_model
from workspace.core.models.base_models import TenantScopedModel

User = get_user_model()


class Comment(TenantScopedModel):
    """Blog comment model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('spam', 'Spam'),
    ]
    
    # Core fields
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Relationships
    post = models.ForeignKey(
        'blog.Post',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Nullable for guest commenters'
    )
    
    # Guest commenter fields (when user is null)
    guest_name = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)
    
    class Meta:
        db_table = 'workspace_blog_comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        author = self.user.email if self.user else self.guest_email
        return f"Comment by {author} on {self.post.title}"
    
    @property
    def author_name(self):
        """Get the commenter's name"""
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.email
        return self.guest_name
    
    @property
    def author_email(self):
        """Get the commenter's email"""
        return self.user.email if self.user else self.guest_email