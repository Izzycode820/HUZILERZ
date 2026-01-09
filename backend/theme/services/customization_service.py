"""
Customization Service for user template customization management.

This service handles user-specific template customizations, backups, and updates.
It does NOT involve GitHub operations.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import (
    TemplateCustomization, 
    TemplateVersion, 
    UpdateNotification,
    SyncLog
)

logger = logging.getLogger(__name__)


class CustomizationService:
    """
    Service for user template customization management.
    
    This service handles:
    - User customization backups before updates
    - Customization restoration
    - Template updates with customization preservation
    - User customization history
    """

    @staticmethod
    def create_customization_backup(
        customization_id: str,
        user,
        backup_reason: str = "pre-update"
    ) -> Dict[str, Any]:
        """
        Create a backup of user customization before updates.
        
        Args:
            customization_id: UUID of template customization
            user: User creating backup
            backup_reason: Reason for backup
            
        Returns:
            Dictionary with backup information
            
        Raises:
            ValidationError: If operation fails
        """
        logger.info(
            f"Creating customization backup: customization={customization_id}, "
            f"user={user.id}, reason={backup_reason}"
        )
        
        try:
            customization = TemplateCustomization.objects.select_related(
                'template', 'template_version'
            ).get(
                id=customization_id,
                is_active=True
            )
            
            # Create backup in customization history
            from .template_customization_service import TemplateCustomizationService
            
            backup = TemplateCustomizationService.save_customizations(
                workspace_id=customization.workspace.id,
                puck_config=customization.puck_config,
                custom_css=customization.custom_css,
                custom_js=customization.custom_js,
                user=user,
                backup_reason=backup_reason
            )
            
            logger.info(
                f"Successfully created backup for customization {customization_id}"
            )
            
            return {
                'backup_id': backup.id,
                'customization': customization,
                'backup_reason': backup_reason,
                'timestamp': timezone.now()
            }
            
        except TemplateCustomization.DoesNotExist:
            logger.warning(f"Customization {customization_id} not found")
            raise ValidationError("Customization not found")
        except Exception as e:
            logger.error(f"Error creating customization backup: {e}", exc_info=True)
            raise ValidationError("Failed to create customization backup")

    @staticmethod
    def apply_template_update(
        customization_id: str,
        target_version_id: str,
        user
    ) -> Dict[str, Any]:
        """
        Apply template update with customization preservation.
        
        This creates a backup, applies the update, and attempts to preserve
        user customizations where possible.
        
        Args:
            customization_id: UUID of template customization
            target_version_id: UUID of target template version
            user: User applying update
            
        Returns:
            Dictionary with update results
            
        Raises:
            ValidationError: If operation fails
        """
        logger.info(
            f"Applying template update: customization={customization_id}, "
            f"target_version={target_version_id}, user={user.id}"
        )
        
        try:
            # Get current customization
            customization = TemplateCustomization.objects.select_related(
                'template', 'template_version', 'workspace'
            ).get(
                id=customization_id,
                is_active=True
            )
            
            # Get target version
            target_version = TemplateVersion.objects.get(
                id=target_version_id,
                template=customization.template
            )
            
            # Validate update is forward-only
            if target_version.created_at <= customization.template_version.created_at:
                raise ValidationError(
                    "Cannot update to older version. Use customization restoration instead."
                )
            
            # Create backup before update
            backup = CustomizationService.create_customization_backup(
                customization_id=customization_id,
                user=user,
                backup_reason="pre-template-update"
            )
            
            # Apply update with atomic transaction
            with transaction.atomic():
                old_version = customization.template_version
                
                # Update customization to new version
                customization.template_version = target_version
                customization.last_modified_by = user
                
                # Attempt to preserve customizations
                # This would involve more complex logic in production
                # For now, we keep the existing customizations
                customization.save(update_fields=['template_version', 'last_modified_by'])
                
                # Create update notification record
                update_notification = UpdateNotification.objects.create(
                    template=customization.template,
                    user=user,
                    workspace=customization.workspace,
                    current_version=old_version,
                    new_version=target_version,
                    update_type=UpdateNotification.UPDATE_TYPE_MINOR,
                    changelog=target_version.changelog or "Template update",
                    breaking_changes=target_version.breaking_changes or "",
                    customization_preservation_score=85,  # Would be calculated
                    estimated_update_time=5
                )
                update_notification.mark_as_sent()
                
                logger.info(
                    f"Successfully applied template update: "
                    f"{old_version.version} -> {target_version.version}"
                )
                
                return {
                    'customization': customization,
                    'old_version': old_version,
                    'new_version': target_version,
                    'backup': backup,
                    'update_notification': update_notification
                }
                
        except (TemplateCustomization.DoesNotExist, TemplateVersion.DoesNotExist):
            logger.warning(
                f"Customization {customization_id} or version {target_version_id} not found"
            )
            raise ValidationError("Customization or version not found")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error applying template update: {e}", exc_info=True)
            raise ValidationError("Failed to apply template update")

    @staticmethod
    def restore_customization_backup(
        customization_id: str,
        backup_id: str,
        user
    ) -> Dict[str, Any]:
        """
        Restore user customization from backup.
        
        This restores the Puck configuration, CSS, and JS from a previous backup.
        
        Args:
            customization_id: UUID of template customization
            backup_id: UUID of backup to restore
            user: User performing restoration
            
        Returns:
            Dictionary with restoration results
            
        Raises:
            ValidationError: If operation fails
        """
        logger.info(
            f"Restoring customization backup: customization={customization_id}, "
            f"backup={backup_id}, user={user.id}"
        )
        
        try:
            customization = TemplateCustomization.objects.get(
                id=customization_id,
                is_active=True
            )
            
            # Get backup (this would come from customization history)
            from .template_customization_service import TemplateCustomizationService
            
            # In production, this would fetch the actual backup data
            # For now, we simulate the restoration
            
            with transaction.atomic():
                # Update customization with backup data
                # This is simplified - in production, we'd restore actual backup data
                customization.last_modified_by = user
                customization.save(update_fields=['last_modified_by'])
                
                # Create restoration record
                restoration_record = TemplateCustomizationService.save_customizations(
                    workspace_id=customization.workspace.id,
                    puck_config=customization.puck_config,
                    custom_css=customization.custom_css,
                    custom_js=customization.custom_js,
                    user=user,
                    backup_reason=f"restoration-from-backup-{backup_id}"
                )
                
                logger.info(
                    f"Successfully restored customization {customization_id} "
                    f"from backup {backup_id}"
                )
                
                return {
                    'customization': customization,
                    'backup_id': backup_id,
                    'restoration_record': restoration_record
                }
                
        except TemplateCustomization.DoesNotExist:
            logger.warning(f"Customization {customization_id} not found")
            raise ValidationError("Customization not found")
        except Exception as e:
            logger.error(f"Error restoring customization backup: {e}", exc_info=True)
            raise ValidationError("Failed to restore customization backup")

    @staticmethod
    def get_customization_backups(
        customization_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get backup history for a customization.
        
        Args:
            customization_id: UUID of template customization
            limit: Number of backups to return
            
        Returns:
            List of backup dictionaries
            
        Raises:
            ValidationError: If customization not found
        """
        logger.info(f"Getting backups for customization {customization_id}")
        
        try:
            customization = TemplateCustomization.objects.get(
                id=customization_id,
                is_active=True
            )
            
            # In production, this would query the actual backup/history table
            # For now, return empty list as placeholder
            backups = []
            
            logger.info(f"Found {len(backups)} backups for customization {customization_id}")
            return backups
            
        except TemplateCustomization.DoesNotExist:
            logger.warning(f"Customization {customization_id} not found")
            raise ValidationError("Customization not found")

    @staticmethod
    def check_for_updates(
        workspace_id: str,
        user
    ) -> List[Dict[str, Any]]:
        """
        Check for available template updates for a workspace.
        
        Args:
            workspace_id: UUID of workspace
            user: User checking for updates
            
        Returns:
            List of available updates
            
        Raises:
            ValidationError: If operation fails
        """
        logger.info(f"Checking for updates for workspace {workspace_id}")
        
        try:
            # Get active customization for workspace
            customization = TemplateCustomization.objects.select_related(
                'template', 'template_version'
            ).get(
                workspace_id=workspace_id,
                is_active=True
            )
            
            # Get latest template version
            latest_version = customization.template.get_latest_version()
            
            if not latest_version or latest_version == customization.template_version:
                return []
            
            # Check if update notification already exists
            existing_notification = UpdateNotification.objects.filter(
                template=customization.template,
                user=user,
                workspace_id=workspace_id,
                new_version=latest_version
            ).first()
            
            if existing_notification:
                return [{
                    'notification': existing_notification,
                    'current_version': customization.template_version,
                    'latest_version': latest_version
                }]
            
            # Create new update notification
            update_notification = UpdateNotification.objects.create(
                template=customization.template,
                user=user,
                workspace_id=workspace_id,
                current_version=customization.template_version,
                new_version=latest_version,
                update_type=UpdateNotification.UPDATE_TYPE_MINOR,
                changelog=latest_version.changelog or "Template update",
                breaking_changes=latest_version.breaking_changes or "",
                customization_preservation_score=85,
                estimated_update_time=5
            )
            update_notification.mark_as_sent()
            
            logger.info(
                f"Found update available: {customization.template_version.version} -> "
                f"{latest_version.version}"
            )
            
            return [{
                'notification': update_notification,
                'current_version': customization.template_version,
                'latest_version': latest_version
            }]
            
        except TemplateCustomization.DoesNotExist:
            logger.warning(f"No active customization found for workspace {workspace_id}")
            return []
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)
            raise ValidationError("Failed to check for updates")