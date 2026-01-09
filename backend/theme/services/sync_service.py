from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from ..models import Template, TemplateVersion, TemplateCustomization, UpdateNotification, SyncLog
from .github_integration_service import GitHubIntegrationService
import logging
import json

logger = logging.getLogger(__name__)


class SyncService:
    """Service for template sync system with Git-to-CDN pipeline and user update management"""

    @staticmethod
    def trigger_template_sync(template_id, user=None, sync_type=SyncLog.SYNC_TYPE_MANUAL):
        """
        Trigger template sync from Git to CDN

        Args:
            template_id: ID of template to sync
            user: User triggering the sync (optional)
            sync_type: Type of sync operation

        Returns:
            SyncLog instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Triggering {sync_type} sync for template {template_id}")

            # Get template with error handling
            try:
                template = Template.objects.get(id=template_id)
            except Template.DoesNotExist:
                logger.warning(f"Template {template_id} not found")
                raise ValidationError("Template not found")

            # Create sync log
            sync_log = SyncLog.objects.create(
                template=template,
                triggered_by=user,
                sync_type=sync_type,
                status=SyncLog.STATUS_PENDING,
                source_version="latest",  # Would be actual Git commit/tag
                target_version="pending",  # Will be updated during sync
            )

            # Start sync process (in production this would be async)
            sync_log.start_sync()

            # Simulate sync process
            try:
                # Update progress
                sync_log.update_progress(10, 100)

                # Get latest Git information (simulated)
                git_info = SyncService._get_git_info(template)
                sync_log.source_version = git_info['commit_hash']
                sync_log.git_tag = git_info['tag']

                # Process files (simulated)
                sync_log.update_progress(50, 100)

                # Deploy to CDN (simulated)
                cdn_path = SyncService._deploy_to_cdn(template, git_info)
                sync_log.cdn_path = cdn_path

                # Update template version
                SyncService._update_template_version(template, git_info, cdn_path)

                # Create update notifications for users
                SyncService._create_update_notifications(template)

                # Complete sync
                sync_log.update_progress(100, 100)
                sync_log.complete_sync(cdn_path=cdn_path)

                logger.info(f"Successfully completed sync for template {template_id}")
                return sync_log

            except Exception as e:
                sync_log.fail_sync(str(e))
                logger.error(f"Sync failed for template {template_id}: {e}")
                raise ValidationError(f"Sync failed: {e}")

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error triggering sync for template {template_id}: {e}")
            raise ValidationError("An unexpected error occurred")

    @staticmethod
    def check_for_updates(workspace_id, user):
        """
        Check for available template updates for a workspace

        Args:
            workspace_id: ID of workspace
            user: User checking for updates

        Returns:
            List of UpdateNotification instances

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Checking for updates for workspace {workspace_id} by user {user.id}")

            # Get active customizations for workspace
            customizations = TemplateCustomization.objects.filter(
                workspace_id=workspace_id,
                is_active=True
            ).select_related('template', 'template_version')

            if not customizations:
                logger.info(f"No active customizations found for workspace {workspace_id}")
                return []

            updates = []

            for customization in customizations:
                # Check if newer version exists
                latest_version = customization.template.get_latest_version()
                if not latest_version or latest_version == customization.template_version:
                    continue

                # Check if update notification already exists
                existing_notification = UpdateNotification.objects.filter(
                    template=customization.template,
                    user=user,
                    workspace_id=workspace_id,
                    new_version=latest_version
                ).first()

                if existing_notification:
                    updates.append(existing_notification)
                    continue

                # Create new update notification
                update_notification = SyncService._create_update_notification(
                    template=customization.template,
                    user=user,
                    workspace_id=workspace_id,
                    current_version=customization.template_version,
                    new_version=latest_version
                )

                updates.append(update_notification)

            logger.info(f"Found {len(updates)} available updates for workspace {workspace_id}")
            return updates

        except Exception as e:
            logger.error(f"Error checking for updates for workspace {workspace_id}: {e}")
            raise ValidationError("Error checking for updates")

    @staticmethod
    def apply_template_update(notification_id, user):
        """
        Apply template update for user workspace

        Args:
            notification_id: ID of update notification
            user: User applying the update

        Returns:
            Updated TemplateCustomization instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Applying template update {notification_id} by user {user.id}")

            # Get update notification
            try:
                notification = UpdateNotification.objects.get(
                    id=notification_id,
                    user=user
                )
            except UpdateNotification.DoesNotExist:
                logger.warning(f"Update notification {notification_id} not found for user {user.id}")
                raise ValidationError("Update notification not found")

            # Check if notification can be acted upon
            if not notification.is_actionable:
                logger.warning(f"Update notification {notification_id} is not actionable")
                raise ValidationError("This update cannot be applied")

            # Get active customization
            customization = TemplateCustomization.objects.filter(
                template=notification.template,
                workspace=notification.workspace,
                is_active=True
            ).first()

            if not customization:
                logger.warning(f"No active customization found for template {notification.template.id} in workspace {notification.workspace.id}")
                raise ValidationError("No active customization found")

            # Apply update with atomic transaction
            with transaction.atomic():
                # Update customization to new version
                old_version = customization.template_version
                customization.template_version = notification.new_version
                customization.last_modified_by = user
                customization.save(update_fields=['template_version', 'last_modified_by'])

                # Mark notification as accepted
                notification.accept()

                # Log update action in customization history
                from .template_customization_service import TemplateCustomizationService
                TemplateCustomizationService.save_customizations(
                    workspace_id=notification.workspace.id,
                    puck_config=customization.puck_config,
                    custom_css=customization.custom_css,
                    custom_js=customization.custom_js,
                    user=user
                )

                logger.info(f"Successfully applied update {notification_id} from version {old_version.version} to {notification.new_version.version}")
                return customization

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error applying template update {notification_id}: {e}")
            raise ValidationError("Error applying template update")



    @staticmethod
    def get_sync_history(template_id=None, limit=50, offset=0):
        """
        Get sync operation history

        Args:
            template_id: Filter by template ID (optional)
            limit: Number of records to return
            offset: Number of records to skip

        Returns:
            QuerySet of SyncLog instances

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting sync history: template={template_id}, limit={limit}, offset={offset}")

            queryset = SyncLog.objects.all()

            if template_id:
                queryset = queryset.filter(template_id=template_id)

            # Apply pagination
            paginated_queryset = queryset[offset:offset + limit]

            logger.info(f"Retrieved {paginated_queryset.count()} sync log entries")
            return paginated_queryset

        except Exception as e:
            logger.error(f"Error getting sync history: {e}")
            raise ValidationError("Error retrieving sync history")

    @staticmethod
    def _get_git_info(template):
        """Simulate getting Git information for template"""
        # In production, this would fetch actual Git commit/tag info
        return {
            'commit_hash': 'abc123def456',
            'tag': f'v{template.version}',
            'message': f'Update {template.name} to version {template.version}',
            'author': 'system'
        }

    @staticmethod
    def _deploy_to_cdn(template, git_info):
        """Deploy template to CDN and generate theme manifest"""
        # In production, this would upload files to CDN
        cdn_path = f"/themes/{template.slug}/{git_info['tag']}/"
        logger.info(f"Simulated CDN deployment to {cdn_path}")

        # Generate and deploy theme manifest
        manifest_data = SyncService._generate_theme_manifest(template, git_info, cdn_path)
        logger.info(f"Generated theme manifest for {template.slug}")

        # Update template with manifest and entry URLs
        SyncService._update_template_manifest_urls(template, cdn_path)

        return cdn_path

    @staticmethod
    def _generate_theme_manifest(template, git_info, cdn_path):
        """Generate theme-manifest.json for the template"""
        # Base CDN URL (in production this would be actual CDN domain)
        cdn_base_url = f"https://cdn.example.com{cdn_path}"

        manifest = {
            "id": template.slug,
            "name": template.name,
            "version": template.version,
            "puckCompatibility": ">=0.8.0 <2.0.0",
            "description": template.description,
            "icon": f"{cdn_base_url}assets/icon-64.png",
            "assetsBase": cdn_base_url,
            "template_type": template.template_type,
            "price_tier": template.price_tier,
            "workspace_types": template.workspace_types,
            "lastUpdated": git_info.get('message', 'Template update'),
            "git_commit_hash": git_info.get('commit_hash', ''),
            "git_tag": git_info.get('tag', '')
        }

        # In production, this would write the manifest file to CDN
        logger.info(f"Generated theme manifest for {template.slug}: {manifest}")
        return manifest

    @staticmethod
    def _update_template_manifest_urls(template, cdn_path):
        """Update template with manifest URLs"""
        # Base CDN URL
        cdn_base_url = f"https://cdn.example.com{cdn_path}"

        # Update template fields
        template.manifest_url = f"{cdn_base_url}theme-manifest.json"
        template.cdn_base_url = cdn_base_url

        # Save the template
        template.save(update_fields=['manifest_url', 'cdn_base_url'])
        logger.info(f"Updated template {template.slug} with manifest URLs")

    @staticmethod
    def _update_template_version(template, git_info, cdn_path):
        """Update template version in database"""
        try:
            # Create or update template version
            version, created = TemplateVersion.objects.update_or_create(
                template=template,
                version=template.version,
                defaults={
                    'status': TemplateVersion.STATUS_PUBLISHED,
                    'cdn_path': cdn_path,
                    'git_commit_hash': git_info['commit_hash'],
                    'git_tag': git_info['tag'],
                    'changelog': git_info['message']
                }
            )

            if created:
                logger.info(f"Created new template version {version.version} for template {template.id}")
            else:
                logger.info(f"Updated template version {version.version} for template {template.id}")

        except Exception as e:
            logger.error(f"Error updating template version for template {template.id}: {e}")
            raise

    @staticmethod
    def _create_update_notifications(template):
        """Create update notifications for all users using this template"""
        try:
            latest_version = template.get_latest_version()
            if not latest_version:
                return

            # Get all active customizations for this template
            customizations = TemplateCustomization.objects.filter(
                template=template,
                is_active=True,
                template_version__lt=latest_version  # Only users on older versions
            ).select_related('workspace', 'user')

            notifications_created = 0

            for customization in customizations:
                # Check if notification already exists
                existing = UpdateNotification.objects.filter(
                    template=template,
                    user=customization.user,
                    workspace=customization.workspace,
                    new_version=latest_version
                ).exists()

                if not existing:
                    SyncService._create_update_notification(
                        template=template,
                        user=customization.user,
                        workspace_id=customization.workspace.id,
                        current_version=customization.template_version,
                        new_version=latest_version
                    )
                    notifications_created += 1

            logger.info(f"Created {notifications_created} update notifications for template {template.id}")

        except Exception as e:
            logger.error(f"Error creating update notifications for template {template.id}: {e}")

    @staticmethod
    def _create_update_notification(template, user, workspace_id, current_version, new_version):
        """Create individual update notification"""
        try:
            # Determine update type based on version changes
            update_type = SyncService._determine_update_type(current_version, new_version)

            # Calculate customization preservation score
            preservation_score = SyncService._calculate_preservation_score(current_version, new_version)

            notification = UpdateNotification.objects.create(
                template=template,
                user=user,
                workspace_id=workspace_id,
                current_version=current_version,
                new_version=new_version,
                update_type=update_type,
                changelog=new_version.changelog or "Bug fixes and improvements",
                breaking_changes=new_version.breaking_changes or "",
                customization_preservation_score=preservation_score,
                estimated_update_time=5  # Default 5 minutes
            )

            # Mark as sent immediately
            notification.mark_as_sent()

            logger.info(f"Created update notification {notification.id} for user {user.id}")
            return notification

        except Exception as e:
            logger.error(f"Error creating update notification for user {user.id}: {e}")
            raise

    @staticmethod
    def _determine_update_type(current_version, new_version):
        """Determine update type based on version changes"""
        # Simple heuristic based on version numbers
        # In production, this would analyze actual changes
        current_parts = current_version.version.split('.')
        new_parts = new_version.version.split('.')

        if len(current_parts) != 3 or len(new_parts) != 3:
            return UpdateNotification.UPDATE_TYPE_MINOR

        if current_parts[0] != new_parts[0]:
            return UpdateNotification.UPDATE_TYPE_MAJOR
        elif current_parts[1] != new_parts[1]:
            return UpdateNotification.UPDATE_TYPE_MINOR
        else:
            return UpdateNotification.UPDATE_TYPE_MINOR

    @staticmethod
    def _calculate_preservation_score(current_version, new_version):
        """Calculate customization preservation score (0-100)"""
        # In production, this would analyze actual template changes
        # For now, return a high score for minor updates, lower for major
        update_type = SyncService._determine_update_type(current_version, new_version)

        if update_type == UpdateNotification.UPDATE_TYPE_MINOR:
            return 95
        elif update_type == UpdateNotification.UPDATE_TYPE_MAJOR:
            return 75
        elif update_type == UpdateNotification.UPDATE_TYPE_BREAKING:
            return 50
        else:
            return 85