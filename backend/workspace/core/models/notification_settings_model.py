import uuid
from django.db import models


class WorkspaceNotificationSettings(models.Model):
    """
    Notification settings for workspace
    Handles SMS, WhatsApp, and Email notification preferences
    All notifications OFF by default - user enables what they need
    """
    SMS_PROVIDERS = [
        ('mtn', 'MTN Cameroon'),
        ('orange', 'Orange Cameroon'),
        ('camtel', 'Camtel'),
        
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )

    # SMS Settings
    sms_enabled = models.BooleanField(
        default=False,
        help_text="Enable SMS notifications"
    )
    sms_provider = models.CharField(
        max_length=20,
        choices=SMS_PROVIDERS,
        blank=True,
        help_text="SMS provider for Cameroon market"
    )
    sms_sender_name = models.CharField(
        max_length=11,
        blank=True,
        help_text="Sender name for SMS (max 11 chars)"
    )
    sms_api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="API key for SMS provider (encrypted)"
    )

    # WhatsApp Settings
    whatsapp_enabled = models.BooleanField(
        default=False,
        help_text="Enable WhatsApp notifications"
    )
    whatsapp_business_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="WhatsApp Business phone number with country code"
    )
    whatsapp_api_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="WhatsApp Business API token (encrypted)"
    )

    # Email Settings
    email_enabled = models.BooleanField(
        default=False,
        help_text="Enable email notifications (rarely used in Cameroon)"
    )
    email_sender_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name shown in email sender field"
    )
    email_sender_address = models.EmailField(
        blank=True,
        help_text="Email address for sending notifications"
    )

    # Notification Event Preferences
    notification_events = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-event notification channel preferences"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_notification_settings'

    def __str__(self):
        return f"Notification settings for {self.workspace.name}"

    def get_default_notification_events(self):
        """
        Default notification events for Cameroon e-commerce
        All channels OFF by default - user enables what they need
        """
        return {
            'order_confirmed': {
                'sms': False,
                'whatsapp': False,
                'email': False,
                'enabled': False
            },
            'order_shipped': {
                'sms': False,
                'whatsapp': False,
                'email': False,
                'enabled': False
            },
            'order_delivered': {
                'sms': False,
                'whatsapp': False,
                'email': False,
                'enabled': False
            },
            'payment_received': {
                'sms': False,
                'whatsapp': False,
                'email': False,
                'enabled': False
            },
            'payment_failed': {
                'sms': False,
                'whatsapp': False,
                'email': False,
                'enabled': False
            },
            'low_stock_alert': {
                'sms': False,
                'whatsapp': False,
                'email': False,
                'enabled': False
            },
            'new_customer': {
                'sms': False,
                'whatsapp': False,
                'email': False,
                'enabled': False
            },
        }

    def save(self, *args, **kwargs):
        """Initialize default notification events if empty"""
        if not self.notification_events:
            self.notification_events = self.get_default_notification_events()
        super().save(*args, **kwargs)

    def is_channel_enabled(self, channel):
        """Check if a notification channel is enabled and configured"""
        if channel == 'sms':
            return self.sms_enabled and bool(self.sms_provider and self.sms_api_key)
        elif channel == 'whatsapp':
            return self.whatsapp_enabled and bool(self.whatsapp_business_number)
        elif channel == 'email':
            return self.email_enabled and bool(self.email_sender_address)
        return False

    def should_send_notification(self, event_type, channel):
        """Check if notification should be sent for event on channel"""
        if not self.is_channel_enabled(channel):
            return False

        event_config = self.notification_events.get(event_type, {})
        return event_config.get('enabled', False) and event_config.get(channel, False)
