"""
Provisioning Retry Service (Critical fix #5)

Provides manual retry functionality for failed workspace provisioning.
Used by admin panel and GraphQL mutations to trigger retries.
"""

import logging
from django.utils import timezone
from workspace.core.models import Workspace, ProvisioningRecord
from HUZILERZ.backend.workspace.core.tasks.workspace_hosting_provisioning import retry_failed_provisioning

logger = logging.getLogger(__name__)


class ProvisioningRetryService:
    """
    Service for managing provisioning retries
    Supports both manual (admin-triggered) and automatic (system-triggered) retries
    """

    @classmethod
    def retry_workspace_provisioning(cls, workspace_id, force=False):
        """
        Trigger manual retry of failed workspace provisioning (Critical fix #5)

        Args:
            workspace_id: UUID of workspace to retry
            force: If True, bypass retry count limits (admin override)

        Returns:
            dict: Retry result with status and details
        """
        try:
            workspace = Workspace.objects.select_related('provisioning').get(id=workspace_id)
            provisioning_record = workspace.provisioning

            # Validate current state
            if provisioning_record.status != 'failed':
                return {
                    'success': False,
                    'error': 'Only failed provisioning can be retried',
                    'current_status': provisioning_record.status
                }

            # Check retry eligibility
            can_retry, reason = provisioning_record.can_retry()

            if not can_retry and not force:
                return {
                    'success': False,
                    'error': f'Cannot retry: {reason}',
                    'retry_count': provisioning_record.retry_count,
                    'max_retries': provisioning_record.max_retries,
                    'hint': 'Use force=True to override retry limits (admin only)'
                }

            # Force retry if admin override (reset retry count)
            if force and not can_retry:
                logger.warning(
                    f"Admin force retry for workspace {workspace_id} "
                    f"(retry_count: {provisioning_record.retry_count})"
                )
                provisioning_record.retry_count = 0
                provisioning_record.save(update_fields=['retry_count', 'updated_at'])

            # Calculate next retry delay (for logging)
            retry_delay = provisioning_record.get_retry_delay()

            # Trigger retry task (immediate for manual retries)
            result = retry_failed_provisioning.apply_async(
                args=[str(workspace_id)],
                countdown=0  # Manual retries are immediate
            )

            logger.info(
                f"Manual provisioning retry triggered for workspace {workspace_id} "
                f"(task_id: {result.id}, attempt: {provisioning_record.retry_count + 1})"
            )

            return {
                'success': True,
                'message': 'Provisioning retry started',
                'workspace_id': str(workspace_id),
                'task_id': str(result.id),
                'retry_count': provisioning_record.retry_count + 1,
                'max_retries': provisioning_record.max_retries,
                'estimated_delay': retry_delay,
                'forced': force
            }

        except Workspace.DoesNotExist:
            logger.error(f"Workspace {workspace_id} not found for retry")
            return {
                'success': False,
                'error': 'Workspace not found'
            }
        except Exception as e:
            logger.error(f"Error triggering provisioning retry: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def get_retry_status(cls, workspace_id):
        """
        Get retry status and eligibility for workspace (Critical fix #5)

        Returns detailed retry information for UI display

        Returns:
            dict: Retry status information
        """
        try:
            workspace = Workspace.objects.select_related('provisioning').get(id=workspace_id)
            provisioning_record = workspace.provisioning

            can_retry, reason = provisioning_record.can_retry()

            return {
                'workspace_id': str(workspace_id),
                'provisioning_status': provisioning_record.status,
                'can_retry': can_retry,
                'retry_reason': reason,
                'retry_count': provisioning_record.retry_count,
                'max_retries': provisioning_record.max_retries,
                'last_retry_at': provisioning_record.last_retry_at.isoformat() if provisioning_record.last_retry_at else None,
                'next_retry_delay': provisioning_record.get_retry_delay() if provisioning_record.status == 'failed' else 0,
                'error_message': provisioning_record.error_message,
                'auto_retry_eligible': provisioning_record.should_auto_retry(),
            }

        except Workspace.DoesNotExist:
            return {
                'error': 'Workspace not found'
            }
        except Exception as e:
            logger.error(f"Error getting retry status: {e}", exc_info=True)
            return {
                'error': str(e)
            }

    @classmethod
    def get_failed_provisioning_workspaces(cls, limit=50):
        """
        Get all workspaces with failed provisioning that can be retried (Critical fix #5)

        Used by admin panel to show workspaces needing attention

        Args:
            limit: Maximum number of workspaces to return

        Returns:
            list: Failed provisioning records with retry information
        """
        try:
            failed_provisionings = ProvisioningRecord.objects.filter(
                status='failed'
            ).select_related('workspace').order_by('-updated_at')[:limit]

            results = []
            for provisioning in failed_provisionings:
                can_retry, reason = provisioning.can_retry()

                results.append({
                    'workspace_id': str(provisioning.workspace.id),
                    'workspace_name': provisioning.workspace.name,
                    'workspace_slug': provisioning.workspace.slug,
                    'error_message': provisioning.error_message,
                    'failed_at': provisioning.completed_at.isoformat() if provisioning.completed_at else None,
                    'retry_count': provisioning.retry_count,
                    'max_retries': provisioning.max_retries,
                    'can_retry': can_retry,
                    'retry_reason': reason,
                    'auto_retry_eligible': provisioning.should_auto_retry(),
                    'last_retry_at': provisioning.last_retry_at.isoformat() if provisioning.last_retry_at else None,
                })

            return {
                'success': True,
                'count': len(results),
                'workspaces': results
            }

        except Exception as e:
            logger.error(f"Error getting failed provisioning workspaces: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
