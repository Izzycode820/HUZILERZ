"""
Store Profile Model - Store Settings Configuration

Stores workspace-level settings for store identity and contact information.
OneToOne relationship with Workspace (type='store').

Performance: Indexed on workspace for fast lookup
Security: Workspace scoping ensures tenant isolation
Validation: Cameroon phone number format validation
"""

import re
import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


# Cameroon phone number validator (+237 followed by 9 digits)
cameroon_phone_validator = RegexValidator(
    regex=r'^\+237[0-9]{9}$',
    message='Phone number must be in Cameroon format: +237XXXXXXXXX (9 digits after +237)',
    code='invalid_cameroon_phone'
)


def validate_cameroon_phone(value):
    """
    Validate Cameroon phone number format.
    Allows empty/None values (optional field).
    
    Format: +237XXXXXXXXX (exactly 9 digits after country code)
    """
    if not value:
        return  # Optional field
    
    pattern = r'^\+237[0-9]{9}$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Phone number must be in Cameroon format: +237XXXXXXXXX (9 digits after +237)',
            code='invalid_cameroon_phone'
        )


class StoreProfile(models.Model):
    """
    Store Profile - Workspace-level store settings
    
    Stores configuration for:
    - Store identity (name, description)
    - Contact information (emails, phones)
    - WhatsApp checkout settings
    - Regional defaults (currency, timezone)
    
    Created automatically during workspace provisioning.
    """
    
    CURRENCY_CHOICES = [
        ('XAF', 'Central African CFA franc'),
    ]
    
    TIMEZONE_CHOICES = [
        ('Africa/Douala', 'Douala (UTC+1)'),
        ('Africa/Lagos', 'Lagos (UTC+1)'),
    ]
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Workspace relationship (OneToOne)
    workspace = models.OneToOneField(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='store_profile',
        help_text='Workspace this profile belongs to'
    )
    
    # Store Identity
    store_name = models.CharField(
        max_length=255,
        help_text='Display name for the store'
    )
    store_description = models.TextField(
        blank=True,
        default='',
        help_text='Store description or tagline'
    )
    logo_url = models.URLField(
        blank=True,
        default='',
        help_text='URL to store logo image'
    )
    
    # Contact Information
    store_email = models.EmailField(
        blank=True,
        default='',
        help_text='Primary contact email for the store'
    )
    support_email = models.EmailField(
        blank=True,
        default='',
        help_text='Customer support email (optional)'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        validators=[validate_cameroon_phone],
        help_text='Store phone number (Cameroon format: +237XXXXXXXXX)'
    )
    
    # WhatsApp Settings (Critical for Cameroon checkout)
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        validators=[validate_cameroon_phone],
        help_text='WhatsApp number for order notifications (Cameroon format: +237XXXXXXXXX)'
    )
    
    # Regional Settings
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='XAF',
        help_text='Store currency (locked to XAF for Cameroon)'
    )
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='Africa/Douala',
        help_text='Store timezone for display purposes'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_profiles'
        verbose_name = 'Store Profile'
        verbose_name_plural = 'Store Profiles'
        indexes = [
            models.Index(fields=['workspace'], name='store_profile_workspace_idx'),
        ]
    
    def __str__(self):
        return f"{self.store_name} ({self.workspace.slug})"
    
    def clean(self):
        """Model-level validation"""
        super().clean()
        
        # Validate phone numbers if provided
        if self.phone_number:
            validate_cameroon_phone(self.phone_number)
        if self.whatsapp_number:
            validate_cameroon_phone(self.whatsapp_number)
    
    def save(self, *args, **kwargs):
        """Save with validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_or_create_for_workspace(cls, workspace):
        """
        Get or create store profile for workspace.
        Idempotent - safe for provisioning retries.
        
        Returns:
            tuple: (profile, created)
        """
        return cls.objects.get_or_create(
            workspace=workspace,
            defaults={
                'store_name': workspace.name,
                'currency': 'XAF',
                'timezone': 'Africa/Douala',
            }
        )
