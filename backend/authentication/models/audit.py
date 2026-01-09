"""
Audit Models - Security events and session tracking
"""
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .user import User


class UserSession(models.Model):
    """Track user sessions for analytics and security"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    
    # Session identification
    session_key = models.CharField(max_length=255, db_index=True)
    fingerprint = models.CharField(max_length=255, blank=True)  # Browser fingerprint
    
    # Device & location info
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)  # City, Country
    
    # Session data
    is_authenticated = models.BooleanField(default=False)
    authentication_method = models.CharField(
        max_length=50,
        choices=[
            ('password', 'Password'),
            ('social_google', 'Google'),
            ('social_facebook', 'Facebook'),
            ('passwordless', 'Passwordless'),
            ('guest', 'Guest'),
        ],
        default='guest'
    )
    
    # Activity tracking
    page_views = models.PositiveIntegerField(default=0)
    actions_count = models.PositiveIntegerField(default=0)  # Clicks, form submissions, etc.
    time_spent = models.DurationField(default=timedelta(0))
    
    # Conversion tracking
    showed_auth_prompt = models.BooleanField(default=False)
    auth_prompt_dismissed_count = models.PositiveSmallIntegerField(default=0)
    converted_to_user = models.BooleanField(default=False)
    conversion_trigger = models.CharField(
        max_length=50,
        choices=[
            ('wishlist', 'Added to Wishlist'),
            ('cart', 'Added to Cart'),
            ('checkout', 'Attempted Checkout'),
            ('store_visit', 'Store Visit'),
            ('product_inquiry', 'Product Inquiry'),
            ('social_prompt', 'Social Prompt'),
            ('voluntary', 'Voluntary Registration'),
        ],
        blank=True, null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user_sessions'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_authenticated', 'converted_to_user']),
        ]
    
    def __str__(self):
        user_info = f"User: {self.user.email}" if self.user else "Guest"
        return f"Session {self.session_key[:8]} - {user_info}"
    
    def update_activity(self, action_type='page_view'):
        """Update session activity"""
        if action_type == 'page_view':
            self.page_views += 1
        else:
            self.actions_count += 1
        
        self.last_activity = timezone.now()
        self.save(update_fields=['page_views', 'actions_count', 'last_activity'])
    
    def should_show_auth_prompt(self):
        """Determine if auth prompt should be shown"""
        if self.is_authenticated or self.showed_auth_prompt:
            return False
        
        # Show prompt after 3+ actions and certain triggers
        return (
            self.actions_count >= 3 or 
            self.page_views >= 5 or
            self.conversion_trigger in ['wishlist', 'cart', 'checkout']
        )
    
    def mark_auth_prompt_shown(self):
        """Mark that auth prompt was shown"""
        self.showed_auth_prompt = True
        self.save(update_fields=['showed_auth_prompt'])
    
    def dismiss_auth_prompt(self):
        """Track auth prompt dismissal"""
        self.auth_prompt_dismissed_count += 1
        self.save(update_fields=['auth_prompt_dismissed_count'])
    
    def mark_converted(self, trigger=None):
        """Mark session as converted to authenticated user"""
        self.converted_to_user = True
        self.is_authenticated = True
        if trigger:
            self.conversion_trigger = trigger
        self.save(update_fields=['converted_to_user', 'is_authenticated', 'conversion_trigger'])


# Legacy SecurityEvent model removed - using the comprehensive SecurityEvent from security_models.py
# This keeps only the UserSession model which is still needed for session tracking