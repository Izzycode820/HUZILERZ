"""
User Model - Core user authentication and profile management
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from django.apps import apps


class User(AbstractUser):
    """Extended User model with modern authentication features"""
    
    # Core fields
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Profile
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    
    # Authentication preferences
    preferred_auth_method = models.CharField(
        max_length=50,
        choices=[
            ('password', 'Password'),
            ('social', 'Social Login'),
            ('passwordless', 'Passwordless'),
        ],
        default='password'
    )
    
    # Security settings
    two_factor_enabled = models.BooleanField(default=False)
    security_notifications = models.BooleanField(default=True)
    
    # Account status
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    is_guest_converted = models.BooleanField(default=False)
    guest_actions_count = models.PositiveIntegerField(default=0)
    
    # Intro pricing tracking (one-time offer per user lifetime)
    intro_pricing_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user first used intro pricing (one-time offer)"
    )
    intro_tier_used = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
        null=True,
        blank=True,
        help_text="Which tier was used with intro pricing"
    )

    # Trial tracking (reserved for future zero-payment trials)
    trial_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user first used trial (reserved for future free trials)"
    )
    trial_tier_used = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
        null=True,
        blank=True,
        help_text="Which tier was used for trial (reserved for future)"
    )
    
    # Remove subscription caching - will be handled by subscription service
    
    # Timestamps
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_users'
    
    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def increment_guest_actions(self):
        """Track guest user engagement for conversion prompts"""
        self.guest_actions_count += 1
        self.save(update_fields=['guest_actions_count'])
    
    def should_prompt_registration(self):
        """Determine if user should be prompted to register"""
        return (
            not self.is_authenticated and 
            self.guest_actions_count >= 3 and 
            not self.is_guest_converted
        )
    
    def is_intro_pricing_eligible(self):
        """Check if user is eligible for intro pricing (one-time offer)"""
        return self.intro_pricing_used_at is None

    def mark_intro_pricing_used(self, tier):
        """
        Mark that user has used their intro pricing offer

        Thread-safe implementation using select_for_update() to prevent race conditions
        CRITICAL: This is a one-time offer - must be atomic to prevent double usage

        Returns: True if flag was newly set, False if already set
        """
        from django.db import transaction

        with transaction.atomic():
            # Lock the user row to prevent concurrent modifications
            # This ensures atomicity: check-and-set happens as one operation
            user = User.objects.select_for_update().get(pk=self.pk)

            if user.intro_pricing_used_at is None:
                user.intro_pricing_used_at = timezone.now()
                user.intro_tier_used = tier
                user.save(update_fields=['intro_pricing_used_at', 'intro_tier_used'])
                # Update the current instance to reflect the change
                self.intro_pricing_used_at = user.intro_pricing_used_at
                self.intro_tier_used = user.intro_tier_used
                return True  # Flag was newly set

            # Already set - no action needed
            self.intro_pricing_used_at = user.intro_pricing_used_at
            self.intro_tier_used = user.intro_tier_used
            return False  # Flag was already set

    def is_trial_eligible(self):
        """Check if user is eligible for trial (reserved for future free trials)"""
        return self.trial_used_at is None

    def mark_trial_used(self, tier):
        """
        Mark that user has used their trial (reserved for future)

        Thread-safe implementation using select_for_update() to prevent race conditions
        CRITICAL: This is a one-time offer - must be atomic to prevent double usage

        Returns: True if flag was newly set, False if already set
        """
        from django.db import transaction

        with transaction.atomic():
            # Lock the user row to prevent concurrent modifications
            # This ensures atomicity: check-and-set happens as one operation
            user = User.objects.select_for_update().get(pk=self.pk)

            if user.trial_used_at is None:
                user.trial_used_at = timezone.now()
                user.trial_tier_used = tier
                user.save(update_fields=['trial_used_at', 'trial_tier_used'])
                # Update the current instance to reflect the change
                self.trial_used_at = user.trial_used_at
                self.trial_tier_used = user.trial_tier_used
                return True  # Flag was newly set

            # Already set - no action needed
            self.trial_used_at = user.trial_used_at
            self.trial_tier_used = user.trial_tier_used
            return False  # Flag was already set
    
    def get_subscription(self):
        """Get user's active subscription object (data access only)"""
        try:
            return self.subscription
        except:
            return None