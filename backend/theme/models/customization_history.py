from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging
import json
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomizationHistory(models.Model):
    """
    Customization history model for tracking changes to template customizations.
    Provides audit trail and undo functionality for user modifications.
    """

    # Primary Key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="History ID",
        help_text="Unique identifier for the customization history entry"
    )

    # Action Type Choices
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_PUBLISH = 'publish'  # Publish to production
    ACTION_ARCHIVE = 'archive'  # Archive customization
    ACTION_DEPLOY = 'deploy'  # Legacy - use publish instead
    ACTION_REVERT = 'revert'
    ACTION_PREVIEW = 'preview'  # Set to preview mode

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_PUBLISH, 'Publish'),
        (ACTION_ARCHIVE, 'Archive'),
        (ACTION_DEPLOY, 'Deploy (Legacy)'),
        (ACTION_REVERT, 'Revert'),
        (ACTION_PREVIEW, 'Set Preview'),
    ]

    # Change Type Choices
    CHANGE_TYPE_PUCK = 'puck'
    CHANGE_TYPE_CSS = 'css'
    CHANGE_TYPE_JS = 'js'
    CHANGE_TYPE_STATUS = 'status'
    CHANGE_TYPE_ROLE = 'role'
    CHANGE_TYPE_MULTIPLE = 'multiple'

    CHANGE_TYPE_CHOICES = [
        (CHANGE_TYPE_PUCK, 'Puck Configuration'),
        (CHANGE_TYPE_CSS, 'Custom CSS'),
        (CHANGE_TYPE_JS, 'Custom JavaScript'),
        (CHANGE_TYPE_STATUS, 'Status'),
        (CHANGE_TYPE_ROLE, 'Role'),
        (CHANGE_TYPE_MULTIPLE, 'Multiple Changes'),
    ]

    # Core Relationships
    customization = models.ForeignKey(
        'TemplateCustomization',
        on_delete=models.CASCADE,
        related_name='history_entries',
        verbose_name="Customization",
        help_text="Customization this history entry belongs to"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customization_history_entries',
        verbose_name="User",
        help_text="User who performed the action"
    )

    # Action Information
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        verbose_name="Action",
        help_text="Type of action performed"
    )
    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
        db_index=True,
        verbose_name="Change Type",
        help_text="Type of change made"
    )

    # Change Data
    old_values = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Old Values",
        help_text="Previous values before the change"
    )
    new_values = models.JSONField(
        null=True,
        blank=True,
        verbose_name="New Values",
        help_text="New values after the change"
    )
    changes_summary = models.JSONField(
        default=dict,
        verbose_name="Changes Summary",
        help_text="Summary of what changed in this action"
    )

    # Context Information
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="User agent string from the request"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address",
        help_text="IP address of the user"
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Session ID",
        help_text="User session identifier"
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        db_table = 'theme_customization_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customization', 'created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['change_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Customization History"
        verbose_name_plural = "Customization History"

    def __str__(self):
        return f"{self.customization} - {self.action} by {self.user}"

    def clean(self):
        """Custom validation for the customization history model"""
        super().clean()

        # Validate old_values and new_values are valid JSON
        for field_name, field_value in [('old_values', self.old_values), ('new_values', self.new_values)]:
            if field_value is not None:
                try:
                    json.dumps(field_value)
                except (TypeError, ValueError) as e:
                    raise ValidationError({
                        field_name: f'Invalid JSON data: {e}'
                    })

        # Validate changes_summary structure
        if self.changes_summary:
            if not isinstance(self.changes_summary, dict):
                raise ValidationError({
                    'changes_summary': 'Changes summary must be a valid JSON object'
                })

    def save(self, *args, **kwargs):
        """Custom save method with validation and automatic field population"""
        # Auto-populate changes_summary if not provided
        if not self.changes_summary:
            self.changes_summary = self._generate_changes_summary()

        super().save(*args, **kwargs)

    def _generate_changes_summary(self):
        """Generate a summary of changes between old and new values"""
        try:
            summary = {
                'action': self.action,
                'change_type': self.change_type,
                'timestamp': self.created_at.isoformat() if self.created_at else None
            }

            if self.old_values and self.new_values:
                # Calculate differences for different change types
                if self.change_type == self.CHANGE_TYPE_PUCK:
                    summary['puck_changes'] = self._calculate_puck_changes()
                elif self.change_type == self.CHANGE_TYPE_CSS:
                    summary['css_changes'] = self._calculate_text_changes(
                        self.old_values.get('custom_css', ''),
                        self.new_values.get('custom_css', '')
                    )
                elif self.change_type == self.CHANGE_TYPE_JS:
                    summary['js_changes'] = self._calculate_text_changes(
                        self.old_values.get('custom_js', ''),
                        self.new_values.get('custom_js', '')
                    )
                elif self.change_type == self.CHANGE_TYPE_STATUS:
                    summary['status_change'] = {
                        'from': self.old_values.get('status'),
                        'to': self.new_values.get('status')
                    }

            return summary
        except Exception as e:
            logger.error(f"Error generating changes summary for history entry: {e}")
            return {'error': str(e)}

    def _calculate_puck_changes(self):
        """Calculate changes in Puck configuration"""
        try:
            old_puck = self.old_values.get('puck_config', {})
            new_puck = self.new_values.get('puck_config', {})

            changes = {
                'added_keys': [],
                'removed_keys': [],
                'modified_keys': [],
                'total_changes': 0
            }

            # Find added keys
            for key in new_puck.keys():
                if key not in old_puck:
                    changes['added_keys'].append(key)

            # Find removed keys
            for key in old_puck.keys():
                if key not in new_puck:
                    changes['removed_keys'].append(key)

            # Find modified keys
            for key in old_puck.keys():
                if key in new_puck and old_puck[key] != new_puck[key]:
                    changes['modified_keys'].append(key)

            changes['total_changes'] = (
                len(changes['added_keys']) +
                len(changes['removed_keys']) +
                len(changes['modified_keys'])
            )

            return changes
        except Exception as e:
            logger.error(f"Error calculating Puck changes: {e}")
            return {'error': str(e)}

    def _calculate_text_changes(self, old_text, new_text):
        """Calculate changes in text fields (CSS/JS)"""
        try:
            old_lines = old_text.split('\n') if old_text else []
            new_lines = new_text.split('\n') if new_text else []

            return {
                'old_line_count': len(old_lines),
                'new_line_count': len(new_lines),
                'line_count_change': len(new_lines) - len(old_lines),
                'old_size': len(old_text.encode('utf-8')) if old_text else 0,
                'new_size': len(new_text.encode('utf-8')) if new_text else 0,
                'size_change': len(new_text.encode('utf-8')) - len(old_text.encode('utf-8'))
            }
        except Exception as e:
            logger.error(f"Error calculating text changes: {e}")
            return {'error': str(e)}

    def get_readable_description(self):
        """Get human-readable description of the history entry"""
        try:
            action_display = dict(self.ACTION_CHOICES).get(self.action, self.action)
            change_display = dict(self.CHANGE_TYPE_CHOICES).get(self.change_type, self.change_type)

            if self.user:
                user_display = self.user.username
            else:
                user_display = "System"

            return f"{action_display} {change_display} by {user_display}"
        except Exception as e:
            logger.error(f"Error generating readable description for history entry {self.id}: {e}")
            return f"Action by {self.user.username if self.user else 'System'}"

    def can_be_undone(self):
        """Check if this action can be undone with error handling"""
        try:
            # Only update actions with old values can be undone
            return (
                self.action == self.ACTION_UPDATE and
                self.old_values is not None and
                self.change_type != self.CHANGE_TYPE_STATUS  # Status changes are handled differently
            )
        except Exception as e:
            logger.error(f"Error checking if history entry {self.id} can be undone: {e}")
            return False

    def undo(self, user):
        """Undo this action with error handling"""
        try:
            if not self.can_be_undone():
                logger.warning(f"Cannot undo history entry {self.id}")
                return False

            customization = self.customization

            # Apply old values based on change type
            if self.change_type == self.CHANGE_TYPE_PUCK:
                customization.puck_config = self.old_values.get('puck_config', {})
            elif self.change_type == self.CHANGE_TYPE_CSS:
                customization.custom_css = self.old_values.get('custom_css', '')
            elif self.change_type == self.CHANGE_TYPE_JS:
                customization.custom_js = self.old_values.get('custom_js', '')

            customization.last_modified_by = user
            customization.save()

            # Create a new history entry for the undo action
            CustomizationHistory.objects.create(
                customization=customization,
                user=user,
                action=self.ACTION_REVERT,
                change_type=self.change_type,
                old_values=self.new_values,
                new_values=self.old_values,
                changes_summary={'undo_of': self.id}
            )

            logger.info(f"Undid history entry {self.id} for customization {customization.id}")
            return True
        except Exception as e:
            logger.error(f"Error undoing history entry {self.id}: {e}")
            return False

    def get_change_details(self):
        """Get detailed information about the changes with error handling"""
        try:
            details = {
                'action': self.get_action_display(),
                'change_type': self.get_change_type_display(),
                'timestamp': self.created_at,
                'user': self.user.username if self.user else 'System',
                'summary': self.changes_summary
            }

            # Add specific details based on change type
            if self.change_type == self.CHANGE_TYPE_PUCK:
                puck_changes = self.changes_summary.get('puck_changes', {})
                details['puck_details'] = {
                    'added': len(puck_changes.get('added_keys', [])),
                    'removed': len(puck_changes.get('removed_keys', [])),
                    'modified': len(puck_changes.get('modified_keys', []))
                }
            elif self.change_type in [self.CHANGE_TYPE_CSS, self.CHANGE_TYPE_JS]:
                text_changes = self.changes_summary.get(f'{self.change_type}_changes', {})
                details['text_details'] = {
                    'line_count_change': text_changes.get('line_count_change', 0),
                    'size_change': text_changes.get('size_change', 0)
                }

            return details
        except Exception as e:
            logger.error(f"Error getting change details for history entry {self.id}: {e}")
            return {'error': str(e)}

    @property
    def is_recent(self):
        """Check if this entry is recent (within last hour) with error handling"""
        try:
            from django.utils import timezone
            from datetime import timedelta

            if not self.created_at:
                return False

            one_hour_ago = timezone.now() - timedelta(hours=1)
            return self.created_at >= one_hour_ago
        except Exception as e:
            logger.error(f"Error checking if history entry {self.id} is recent: {e}")
            return False

    @classmethod
    def log_action(cls, customization, user, action, change_type, old_values=None, new_values=None, **kwargs):
        """Helper method to create history entries with error handling"""
        try:
            history_entry = cls(
                customization=customization,
                user=user,
                action=action,
                change_type=change_type,
                old_values=old_values,
                new_values=new_values,
                **kwargs
            )
            history_entry.full_clean()
            history_entry.save()

            logger.info(f"Logged {action} action for customization {customization.id}")
            return history_entry
        except Exception as e:
            logger.error(f"Error logging action for customization {customization.id}: {e}")
            return None