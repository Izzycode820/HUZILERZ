from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging
import json
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


class TemplateCustomization(models.Model):
    """
    Template customization model for storing user-specific template modifications.
    Each workspace gets its own customization record that references a master template.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Customization ID",
        help_text="Unique identifier for the customization"
    )


    # Core Relationships
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='template_customizations',
        verbose_name="Workspace",
        help_text="Workspace this customization belongs to"
    )
    template = models.ForeignKey(
        'Template',
        on_delete=models.CASCADE,
        related_name='customizations',
        verbose_name="Template",
        help_text="Master template being customized"
    )
    # Note: template_version is optional for now (future feature)
    template_version = models.ForeignKey(
        'TemplateVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customizations',
        verbose_name="Template Version",
        help_text="Specific template version being customized (optional)"
    )
    theme_name = models.CharField(
        max_length=255,
        verbose_name="Theme Name",
        help_text="User-friendly name for this theme (can be renamed)"
    )

    # Customization Data
    puck_config = models.JSONField(
        default=dict,
        verbose_name="Puck Configuration",
        help_text="User customizations stored as Puck configuration"
    )
    puck_data = models.JSONField(
        default=dict,
        verbose_name="Puck Data",
        help_text="Current page layout and content data for Puck editor"
    )

    # Status (Shopify model: drafts by default, only one active published theme)
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Is Active",
        help_text="Whether this theme is currently published and live on the workspace"
    )

    # Deployment Tracking
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Published At",
        help_text="When this customization was last published to production"
    )

    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='modified_customizations',
        verbose_name="Last Modified By",
        help_text="User who last modified this customization"
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_customizations',
        verbose_name="Created By",
        help_text="User who created this customization"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    last_edited_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Edited At",
        help_text="When customization was last modified"
    )

    class Meta:
        db_table = 'theme_template_customizations'
        ordering = ['workspace', '-last_edited_at']
        indexes = [
            models.Index(fields=['workspace', 'template']),
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['published_at']),
            models.Index(fields=['last_edited_at']),
        ]
        constraints = [
            # Ensure only one active (published) theme per workspace
            models.UniqueConstraint(
                fields=['workspace'],
                condition=models.Q(is_active=True),
                name='unique_active_theme_per_workspace'
            )
        ]
        verbose_name = "Template Customization"
        verbose_name_plural = "Template Customizations"

    def __str__(self):
        return f"{self.workspace.name} - {self.theme_name}"

    def clean(self):
        """Custom validation for the template customization model"""
        super().clean()

        # Validate workspace and template compatibility
        if self.workspace and self.template:
            workspace_type = self.workspace.workspace_type
            if workspace_type not in self.template.workspace_types:
                raise ValidationError({
                    'template': f'Template {self.template.name} is not compatible with workspace type {workspace_type}'
                })

        # Validate Puck configuration structure
        if self.puck_config:
            try:
                # Basic validation that it's a valid JSON structure
                json.dumps(self.puck_config)

                # Check for required fields if any
                if not isinstance(self.puck_config, dict):
                    raise ValidationError({
                        'puck_config': 'Puck configuration must be a valid JSON object'
                    })
            except (TypeError, ValueError) as e:
                raise ValidationError({
                    'puck_config': f'Invalid Puck configuration: {e}'
                })

    def save(self, *args, **kwargs):
        """Custom save method with validation"""
        # Ensure only one active customization per workspace (transaction handled by DB constraint)
        # But we do it here too for immediate feedback
        if self.is_active:
            TemplateCustomization.objects.filter(
                workspace=self.workspace,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

    def publish(self, user=None):
        """
        Publish this theme (make it live on workspace).
        Automatically unpublishes any other active theme (handled by save() method).
        """
        from django.utils import timezone

        try:
            # Set as active (save() method automatically unpublishes other themes - see line 170-174)
            self.is_active = True
            self.published_at = timezone.now()

            if user:
                self.last_modified_by = user

            self.save()  # Triggers save() which unpublishes others (existing logic is correct)
            logger.info(f"Published theme '{self.theme_name}' for workspace {self.workspace.id}")
            return True
        except Exception as e:
            logger.error(f"Error publishing theme {self.id}: {e}")
            raise

    def unpublish(self):
        """
        Unpublish this theme (take it offline).
        Workspace will have no active theme until another is published.
        """
        try:
            self.is_active = False
            self.save(update_fields=['is_active'])
            logger.info(f"Unpublished theme '{self.theme_name}' for workspace {self.workspace.id}")
            return True
        except Exception as e:
            logger.error(f"Error unpublishing theme {self.id}: {e}")
            raise

    def duplicate(self, new_name=None, user=None):
        """
        Create a copy of this customization for experimentation.
        Useful for A/B testing or trying variations without affecting live theme.
        """
        try:
            duplicate = TemplateCustomization(
                workspace=self.workspace,
                template=self.template,
                template_version=self.template_version,
                theme_name=new_name or f"{self.theme_name} Copy",
                puck_config=self.puck_config.copy() if self.puck_config else {},
                puck_data=self.puck_data.copy() if self.puck_data else {},
                is_active=False,  # Duplicates are always drafts
                created_by=user or self.created_by,
                last_modified_by=user or self.last_modified_by
            )
            duplicate.save()
            logger.info(f"Duplicated theme '{self.theme_name}' → '{duplicate.theme_name}'")
            return duplicate
        except Exception as e:
            logger.error(f"Error duplicating theme {self.id}: {e}")
            raise

    def can_delete(self):
        """
        Check if this customization can be deleted.
        Active (published) themes cannot be deleted - must publish another first.
        """
        return not self.is_active

    def delete(self, *args, **kwargs):
        """
        Override delete to prevent deletion of active themes.
        """
        if not self.can_delete():
            raise ValidationError(
                "Cannot delete active theme. Please publish another theme first."
            )

        logger.info(f"Deleting theme '{self.theme_name}' for workspace {self.workspace.id}")
        super().delete(*args, **kwargs)

    @property
    def theme_slug(self):
        """
        Get the theme slug for registry lookup.
        Used by frontend to load correct components from THEME_REGISTRY.
        """
        return self.template.slug if self.template else None

    @property
    def is_published(self):
        """Check if this theme is currently published (live)."""
        return self.is_active

    @property
    def is_draft(self):
        """Check if this theme is a draft (not published)."""
        return not self.is_active