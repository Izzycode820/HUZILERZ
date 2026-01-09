"""
Workspace provisioning background tasks
Handles async infrastructure setup, admin area creation, and Puck workspace initialization
"""
import logging
import time
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from workspace.hosting.services.idempotency_service import idempotent_task
from workspace.hosting.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


@shared_task(
    name='workspace_core.provision_workspace',
    bind=True,
    max_retries=5,
    default_retry_delay=60
)
def provision_workspace(self, workspace_id):
    """
    Main workspace provisioning orchestrator
    Coordinates all provisioning steps for new workspace

    Steps:
    1. Assign infrastructure (pool/bridge/silo)
    2. Create notification settings
    3. Finalize provisioning

    Args:
        workspace_id: UUID of workspace to provision

    Returns:
        dict: Provisioning result with status and details
    """
    from workspace.core.models import Workspace, ProvisioningRecord, ProvisioningLog

    try:
        workspace = Workspace.objects.select_related('owner__subscription').get(id=workspace_id)
        provisioning_record = workspace.provisioning

        logger.info(f"Starting provisioning for workspace {workspace.id}")
        provisioning_record.mark_in_progress()

        # Step 1: Assign infrastructure
        try:
            assign_infrastructure.apply_async(
                args=[workspace_id],
                link=create_notification_settings.s(workspace_id),
                link_error=handle_provisioning_failure.s(workspace_id, 'assign_infrastructure')
            )
        except Exception as e:
            logger.error(f"Failed to queue infrastructure assignment: {e}")
            provisioning_record.mark_failed(str(e))
            raise

        return {
            'status': 'started',
            'workspace_id': str(workspace_id),
            'provisioning_id': str(provisioning_record.id)
        }

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found")
        raise
    except Exception as e:
        logger.error(f"Provisioning failed for workspace {workspace_id}: {e}")
        raise self.retry(exc=e)


@shared_task(
    name='workspace_core.assign_infrastructure',
    bind=True,
    max_retries=5,
    default_retry_delay=120
)
@idempotent_task(operation='assign_infrastructure', resource_id_param='workspace_id', ttl=1800)
def assign_infrastructure(self, workspace_id):
    """
    Assign infrastructure resources based on subscription tier
    Creates WorkspaceInfrastructure record

    Retries with exponential backoff on failure
    Idempotent - safe to retry without creating duplicate resources
    """
    from workspace.core.models import Workspace, ProvisioningRecord
    from workspace.hosting.services.provisioning_service import InfrastructureProvisioningService

    start_time = time.time()
    success = False

    try:
        workspace = Workspace.objects.select_related('owner__subscription').get(id=workspace_id)
        provisioning_record = workspace.provisioning

        logger.info(f"Assigning infrastructure for workspace {workspace.id}")

        # Provision infrastructure (always POOL)
        infrastructure = InfrastructureProvisioningService.provision_for_workspace(
            workspace=workspace,
            provisioning_record=provisioning_record
        )

        logger.info(
            f"Infrastructure assigned: POOL (shared) for workspace {workspace.id}"
        )

        success = True
        duration = time.time() - start_time

        # Record metrics
        MetricsService.record_provision_attempt(
            workspace_id=str(workspace_id),
            success=True,
            duration_seconds=duration,
            metadata={'subdomain': infrastructure.subdomain}
        )

        return {
            'status': 'completed',
            'workspace_id': str(workspace_id),
            'infrastructure_type': 'POOL',
            'subdomain': infrastructure.subdomain,
            'success': True
        }

    except Exception as e:
        duration = time.time() - start_time

        # Record failure metrics
        MetricsService.record_provision_attempt(
            workspace_id=str(workspace_id),
            success=False,
            duration_seconds=duration,
            metadata={'error': str(e)}
        )

        logger.error(f"Infrastructure assignment failed for workspace {workspace_id}: {e}")
        raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 60, 3600))


@shared_task(
    name='workspace_core.create_notification_settings',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def create_notification_settings(self, previous_result, workspace_id):
    """
    Create notification settings for workspace
    All channels OFF by default - user enables what they need
    """
    from workspace.core.models import Workspace, ProvisioningRecord, ProvisioningLog, WorkspaceNotificationSettings

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        provisioning_record = workspace.provisioning

        ProvisioningLog.log_step_started(
            provisioning=provisioning_record,
            step='create_notification_settings',
            metadata={'workspace_id': str(workspace_id)}
        )

        logger.info(f"Creating notification settings for workspace {workspace.id}")

        # Create notification settings (idempotent)
        notification_settings, created = WorkspaceNotificationSettings.objects.get_or_create(
            workspace=workspace,
            defaults={
                'sms_enabled': False,
                'whatsapp_enabled': False,
                'email_enabled': False,
            }
        )

        ProvisioningLog.log_step_completed(
            provisioning=provisioning_record,
            step='create_notification_settings',
            metadata={
                'workspace_id': str(workspace_id),
                'notification_settings_id': str(notification_settings.id),
                'created': created
            }
        )

        logger.info(f"Notification settings created for workspace {workspace.id}")

        # Chain to store profile creation (for store workspaces)
        create_store_profile.apply_async(
            args=[{'status': 'completed'}, workspace_id]
        )

        return {
            'status': 'completed',
            'workspace_id': str(workspace_id),
            'notification_settings_id': str(notification_settings.id)
        }

    except Exception as e:
        ProvisioningLog.log_step_failed(
            provisioning=provisioning_record,
            step='create_notification_settings',
            error=str(e),
            attempt=self.request.retries + 1,
            metadata={'workspace_id': str(workspace_id)}
        )
        logger.error(f"Notification settings creation failed for workspace {workspace_id}: {e}")
        raise self.retry(exc=e)


@shared_task(
    name='workspace_core.create_store_profile',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def create_store_profile(self, previous_result, workspace_id):
    """
    Create store profile for workspace.
    Only creates for store-type workspaces, skips for others.
    Idempotent - uses get_or_create.
    """
    from workspace.core.models import Workspace, ProvisioningLog
    from workspace.store.models import StoreProfile

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        provisioning_record = workspace.provisioning

        ProvisioningLog.log_step_started(
            provisioning=provisioning_record,
            step='create_store_profile',
            metadata={'workspace_id': str(workspace_id)}
        )

        # Only create store profile for store workspaces
        if workspace.type == 'store':
            logger.info(f"Creating store profile for workspace {workspace.id}")

            # Create store profile (idempotent)
            store_profile, created = StoreProfile.get_or_create_for_workspace(workspace)

            ProvisioningLog.log_step_completed(
                provisioning=provisioning_record,
                step='create_store_profile',
                metadata={
                    'workspace_id': str(workspace_id),
                    'store_profile_id': str(store_profile.id),
                    'created': created
                }
            )

            logger.info(f"Store profile {'created' if created else 'retrieved'} for workspace {workspace.id}")
        else:
            # Skip for non-store workspaces
            ProvisioningLog.log_step_completed(
                provisioning=provisioning_record,
                step='create_store_profile',
                metadata={
                    'workspace_id': str(workspace_id),
                    'skipped': True,
                    'reason': f'workspace type is {workspace.type}'
                }
            )
            logger.info(f"Skipped store profile for non-store workspace {workspace.id}")

        # Chain to finalize provisioning
        finalize_provisioning.apply_async(
            args=[{'status': 'completed'}, workspace_id]
        )

        return {
            'status': 'completed',
            'workspace_id': str(workspace_id),
            'workspace_type': workspace.type
        }

    except Exception as e:
        ProvisioningLog.log_step_failed(
            provisioning=provisioning_record,
            step='create_store_profile',
            error=str(e),
            attempt=self.request.retries + 1,
            metadata={'workspace_id': str(workspace_id)}
        )
        logger.error(f"Store profile creation failed for workspace {workspace_id}: {e}")
        raise self.retry(exc=e)

@shared_task(
    name='workspace_core.finalize_provisioning',
    bind=True,
    max_retries=1
)
def finalize_provisioning(self, previous_result, workspace_id):
    """
    Finalize workspace provisioning
    Mark provisioning complete and activate workspace
    """
    from workspace.core.models import Workspace, ProvisioningRecord

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        provisioning_record = workspace.provisioning

        logger.info(f"Finalizing provisioning for workspace {workspace.id}")

        with transaction.atomic():
            # Mark provisioning complete
            provisioning_record.mark_completed()

            # Activate workspace
            workspace.status = 'active'
            workspace.provisioning_complete = True
            workspace.save(update_fields=['status', 'provisioning_complete', 'updated_at'])

        logger.info(f"Provisioning completed for workspace {workspace.id}")

        return {
            'status': 'success',
            'workspace_id': str(workspace_id),
            'completed_at': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Provisioning finalization failed for workspace {workspace_id}: {e}")
        provisioning_record.mark_failed(str(e))
        raise


@shared_task(
    name='workspace_core.handle_provisioning_failure',
    bind=True
)
def handle_provisioning_failure(self, task_id, workspace_id, failed_step):
    """
    Handle provisioning failure with auto-retry logic (Critical fix #5)
    - Marks provisioning as failed
    - Schedules auto-retry with exponential backoff if eligible
    - Alerts admin if max retries exceeded
    """
    from workspace.core.models import Workspace, ProvisioningRecord

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        provisioning_record = workspace.provisioning

        error_msg = f"Provisioning failed at step: {failed_step}"
        logger.error(f"{error_msg} for workspace {workspace_id}")

        provisioning_record.mark_failed(error_msg)

        # Check if auto-retry should be triggered (Critical fix #5)
        if provisioning_record.should_auto_retry():
            retry_delay = provisioning_record.get_retry_delay()
            logger.info(
                f"Scheduling auto-retry #{provisioning_record.retry_count + 1} "
                f"for workspace {workspace_id} in {retry_delay} seconds"
            )

            # Schedule retry with exponential backoff
            retry_failed_provisioning.apply_async(
                args=[str(workspace_id)],
                countdown=retry_delay
            )
        else:
            can_retry, reason = provisioning_record.can_retry()
            if not can_retry:
                logger.error(
                    f"Max retries exceeded for workspace {workspace_id}. "
                    f"Manual intervention required. Reason: {reason}"
                )
                # TODO: Send admin alert email/notification
            else:
                logger.info(
                    f"Auto-retry limit reached for workspace {workspace_id}. "
                    f"Manual retry available via admin panel."
                )

    except Exception as e:
        logger.error(f"Failed to handle provisioning failure for {workspace_id}: {e}")


@shared_task(
    name='workspace_core.retry_failed_provisioning',
    bind=True
)
def retry_failed_provisioning(self, workspace_id):
    """
    Retry failed workspace provisioning (Critical fix #5)
    - Validates retry is allowed (checks retry count vs max_retries)
    - Resets provisioning status with retry tracking
    - Restarts provisioning process
    - Can be triggered automatically (with backoff) or manually (admin panel)
    """
    from workspace.core.models import Workspace

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        provisioning_record = workspace.provisioning

        if provisioning_record.status != 'failed':
            logger.warning(f"Cannot retry non-failed provisioning for workspace {workspace_id}")
            return {'status': 'skipped', 'reason': 'not_failed'}

        # Check if retry is allowed (Critical fix #5)
        can_retry, reason = provisioning_record.can_retry()
        if not can_retry:
            logger.error(
                f"Cannot retry provisioning for workspace {workspace_id}: {reason}"
            )
            return {
                'status': 'blocked',
                'reason': reason,
                'retry_count': provisioning_record.retry_count,
                'max_retries': provisioning_record.max_retries
            }

        logger.info(
            f"Retrying failed provisioning for workspace {workspace.id} "
            f"(attempt {provisioning_record.retry_count + 1}/{provisioning_record.max_retries})"
        )

        # Reset provisioning (increments retry_count)
        try:
            provisioning_record.retry()
        except ValueError as e:
            logger.error(f"Retry validation failed: {e}")
            return {'status': 'error', 'reason': str(e)}

        # Restart provisioning
        provision_workspace.apply_async(args=[workspace_id])

        logger.info(
            f"[SUCCESS] Provisioning retry #{provisioning_record.retry_count} "
            f"started for workspace {workspace_id}"
        )

        return {
            'status': 'retried',
            'workspace_id': str(workspace_id),
            'retry_count': provisioning_record.retry_count
        }

    except Exception as e:
        logger.error(f"Failed to retry provisioning for workspace {workspace_id}: {e}")
        raise
