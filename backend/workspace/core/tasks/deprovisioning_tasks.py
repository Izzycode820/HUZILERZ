"""
Workspace deprovisioning background tasks
Handles async infrastructure cleanup after workspace deletion grace period
"""
import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(
    name='workspace_core.deprovision_workspace',
    bind=True,
    max_retries=5,
    default_retry_delay=300  # 5 minutes
)
def deprovision_workspace(self, workspace_id):
    """
    Main workspace deprovisioning orchestrator
    Executes after 5-day grace period to cleanup all workspace infrastructure

    Steps:
    1. Suspend/cleanup WorkspaceInfrastructure
    2. Cleanup S3 files/folders
    3. Invalidate CDN cache
    4. Cleanup DNS records (if custom domains)
    5. Mark ProvisioningRecord as cancelled
    6. Finalize deprovisioning

    Args:
        workspace_id: UUID of workspace to deprovision

    Returns:
        dict: Deprovisioning result with status and details
    """
    from workspace.core.models import Workspace, DeProvisioningRecord, DeProvisioningLog

    try:
        workspace = Workspace.objects.select_related('owner', 'infrastructure').get(id=workspace_id)
        deprovisioning_record = workspace.deprovisioning

        # Safety check: Only deprovision suspended workspaces
        if workspace.status != 'suspended':
            logger.warning(
                f"Deprovisioning skipped for workspace {workspace.id}: "
                f"status is '{workspace.status}', expected 'suspended'"
            )
            deprovisioning_record.mark_cancelled()
            return {
                'status': 'cancelled',
                'reason': 'workspace_not_suspended',
                'workspace_id': str(workspace_id)
            }

        # Safety check: Respect grace period
        if not deprovisioning_record.is_overdue:
            logger.warning(
                f"Deprovisioning skipped for workspace {workspace.id}: "
                f"grace period not expired (scheduled for {deprovisioning_record.scheduled_for})"
            )
            return {
                'status': 'rescheduled',
                'scheduled_for': deprovisioning_record.scheduled_for.isoformat(),
                'workspace_id': str(workspace_id)
            }

        logger.info(f"Starting deprovisioning for workspace {workspace.id}")
        deprovisioning_record.mark_in_progress()

        # Execute cleanup chain
        cleanup_summary = {}

        # Step 1: Cleanup infrastructure
        try:
            result = cleanup_workspace_infrastructure.apply_async(
                args=[workspace_id],
                link=cleanup_s3_files.s(workspace_id),
                link_error=handle_deprovisioning_failure.s(workspace_id, 'cleanup_infrastructure')
            )
            cleanup_summary['infrastructure_cleanup_queued'] = True
        except Exception as e:
            logger.error(f"Failed to queue infrastructure cleanup: {e}")
            deprovisioning_record.mark_failed(str(e))
            raise

        return {
            'status': 'started',
            'workspace_id': str(workspace_id),
            'deprovisioning_id': str(deprovisioning_record.id),
            'cleanup_summary': cleanup_summary
        }

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found for deprovisioning")
        raise
    except Exception as e:
        logger.error(f"Deprovisioning failed for workspace {workspace_id}: {e}")
        raise self.retry(exc=e)


@shared_task(
    name='workspace_core.cleanup_workspace_infrastructure',
    bind=True,
    max_retries=5,
    default_retry_delay=180
)
def cleanup_workspace_infrastructure(self, workspace_id):
    """
    Suspend/cleanup WorkspaceInfrastructure
    Marks infrastructure as suspended (soft delete)

    Retries with exponential backoff on failure
    """
    from workspace.core.models import Workspace, DeProvisioningRecord, DeProvisioningLog
    from workspace.hosting.models import WorkspaceInfrastructure

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        deprovisioning_record = workspace.deprovisioning

        DeProvisioningLog.log_step_started(
            deprovisioning=deprovisioning_record,
            step='cleanup_infrastructure',
            metadata={'workspace_id': str(workspace_id)}
        )

        logger.info(f"Cleaning up infrastructure for workspace {workspace.id}")

        # Get workspace infrastructure
        try:
            infrastructure = workspace.infrastructure

            # Mark infrastructure as suspended (soft delete)
            infrastructure.status = 'suspended'
            infrastructure.save(update_fields=['status', 'updated_at'])

            DeProvisioningLog.log_step_completed(
                deprovisioning=deprovisioning_record,
                step='cleanup_infrastructure',
                metadata={
                    'workspace_id': str(workspace_id),
                    'infrastructure_id': str(infrastructure.id),
                    'tier_type': infrastructure.tier_type,
                    'subdomain': infrastructure.subdomain
                }
            )

            logger.info(
                f"Infrastructure suspended for workspace {workspace.id}: "
                f"{infrastructure.subdomain}"
            )

        except WorkspaceInfrastructure.DoesNotExist:
            # Infrastructure doesn't exist (already cleaned or never created)
            DeProvisioningLog.log_step_skipped(
                deprovisioning=deprovisioning_record,
                step='cleanup_infrastructure',
                reason='infrastructure_not_found',
                metadata={'workspace_id': str(workspace_id)}
            )
            logger.info(f"No infrastructure found for workspace {workspace.id}")

        return {
            'status': 'completed',
            'workspace_id': str(workspace_id),
            'infrastructure_suspended': True
        }

    except Exception as e:
        logger.error(f"Infrastructure cleanup failed for workspace {workspace_id}: {e}")

        # Log failure
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            DeProvisioningLog.log_step_failed(
                deprovisioning=workspace.deprovisioning,
                step='cleanup_infrastructure',
                error=str(e),
                attempt=self.request.retries + 1
            )
        except:
            pass

        raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 60, 3600))


@shared_task(
    name='workspace_core.cleanup_s3_files',
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def cleanup_s3_files(self, previous_result, workspace_id):
    """
    Cleanup S3 files for workspace
    Archives or deletes files based on INFRASTRUCTURE_MODE

    In mock mode: Skip (no S3 files)
    In AWS mode: Archive to cold storage or delete
    """
    from workspace.core.models import Workspace, DeProvisioningRecord, DeProvisioningLog
    from workspace.hosting.services.infrastructure_cleanup_service import InfrastructureCleanupService
    from django.conf import settings

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        deprovisioning_record = workspace.deprovisioning

        DeProvisioningLog.log_step_started(
            deprovisioning=deprovisioning_record,
            step='cleanup_s3_files',
            metadata={'workspace_id': str(workspace_id)}
        )

        # Skip in mock mode (no actual S3 files)
        if settings.INFRASTRUCTURE_MODE == 'mock':
            DeProvisioningLog.log_step_skipped(
                deprovisioning=deprovisioning_record,
                step='cleanup_s3_files',
                reason='mock_mode_active',
                metadata={'infrastructure_mode': 'mock'}
            )
            logger.info(f"S3 cleanup skipped for workspace {workspace.id} (mock mode)")
            return {
                'status': 'skipped',
                'reason': 'mock_mode',
                'workspace_id': str(workspace_id)
            }

        logger.info(f"Cleaning up S3 files for workspace {workspace.id}")

        # Execute S3 cleanup
        result = InfrastructureCleanupService.cleanup_s3_workspace_files(workspace)

        DeProvisioningLog.log_step_completed(
            deprovisioning=deprovisioning_record,
            step='cleanup_s3_files',
            metadata={
                'workspace_id': str(workspace_id),
                'files_deleted': result.get('files_deleted', 0),
                'storage_freed_gb': result.get('storage_freed_gb', 0)
            }
        )

        logger.info(
            f"S3 cleanup completed for workspace {workspace.id}: "
            f"{result.get('files_deleted', 0)} files deleted"
        )

        return {
            'status': 'completed',
            'workspace_id': str(workspace_id),
            's3_cleanup': result
        }

    except Exception as e:
        logger.error(f"S3 cleanup failed for workspace {workspace_id}: {e}")

        # Log failure
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            DeProvisioningLog.log_step_failed(
                deprovisioning=workspace.deprovisioning,
                step='cleanup_s3_files',
                error=str(e),
                attempt=self.request.retries + 1
            )
        except:
            pass

        raise self.retry(exc=e)


@shared_task(
    name='workspace_core.invalidate_workspace_cdn_cache',
    bind=True,
    max_retries=3,
    default_retry_delay=120
)
def invalidate_workspace_cdn_cache(self, previous_result, workspace_id):
    """
    Invalidate CDN cache for deleted workspace
    Ensures no stale content is served
    """
    from workspace.core.models import Workspace, DeProvisioningRecord, DeProvisioningLog
    from workspace.hosting.services.cdn_cache_service import CDNCacheService
    from django.conf import settings

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        deprovisioning_record = workspace.deprovisioning

        DeProvisioningLog.log_step_started(
            deprovisioning=deprovisioning_record,
            step='invalidate_cdn_cache',
            metadata={'workspace_id': str(workspace_id)}
        )

        # Skip in mock mode
        if settings.INFRASTRUCTURE_MODE == 'mock':
            DeProvisioningLog.log_step_skipped(
                deprovisioning=deprovisioning_record,
                step='invalidate_cdn_cache',
                reason='mock_mode_active',
                metadata={'infrastructure_mode': 'mock'}
            )
            logger.info(f"CDN cache invalidation skipped for workspace {workspace.id} (mock mode)")
            return {
                'status': 'skipped',
                'reason': 'mock_mode',
                'workspace_id': str(workspace_id)
            }

        logger.info(f"Invalidating CDN cache for workspace {workspace.id}")

        # Invalidate CDN cache
        result = CDNCacheService.invalidate_workspace_cache(workspace_id=str(workspace_id))

        DeProvisioningLog.log_step_completed(
            deprovisioning=deprovisioning_record,
            step='invalidate_cdn_cache',
            metadata={
                'workspace_id': str(workspace_id),
                'invalidation_result': result
            }
        )

        logger.info(f"CDN cache invalidated for workspace {workspace.id}")

        return {
            'status': 'completed',
            'workspace_id': str(workspace_id),
            'cdn_invalidation': result
        }

    except Exception as e:
        logger.error(f"CDN cache invalidation failed for workspace {workspace_id}: {e}")

        # Log failure
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            DeProvisioningLog.log_step_failed(
                deprovisioning=workspace.deprovisioning,
                step='invalidate_cdn_cache',
                error=str(e),
                attempt=self.request.retries + 1
            )
        except:
            pass

        raise self.retry(exc=e)


@shared_task(
    name='workspace_core.cleanup_dns_records',
    bind=True,
    max_retries=3,
    default_retry_delay=180
)
def cleanup_dns_records(self, previous_result, workspace_id):
    """
    Cleanup DNS records for workspace
    Removes Route53 records if custom domains were configured
    """
    from workspace.core.models import Workspace, DeProvisioningRecord, DeProvisioningLog
    from workspace.hosting.services.infrastructure_cleanup_service import InfrastructureCleanupService
    from django.conf import settings

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        deprovisioning_record = workspace.deprovisioning

        DeProvisioningLog.log_step_started(
            deprovisioning=deprovisioning_record,
            step='cleanup_dns_records',
            metadata={'workspace_id': str(workspace_id)}
        )

        # Skip in mock mode
        if settings.INFRASTRUCTURE_MODE == 'mock':
            DeProvisioningLog.log_step_skipped(
                deprovisioning=deprovisioning_record,
                step='cleanup_dns_records',
                reason='mock_mode_active',
                metadata={'infrastructure_mode': 'mock'}
            )
            logger.info(f"DNS cleanup skipped for workspace {workspace.id} (mock mode)")
            return {
                'status': 'skipped',
                'reason': 'mock_mode',
                'workspace_id': str(workspace_id)
            }

        logger.info(f"Cleaning up DNS records for workspace {workspace.id}")

        # Execute DNS cleanup
        result = InfrastructureCleanupService.cleanup_dns_records(workspace)

        DeProvisioningLog.log_step_completed(
            deprovisioning=deprovisioning_record,
            step='cleanup_dns_records',
            metadata={
                'workspace_id': str(workspace_id),
                'records_deleted': result.get('records_deleted', 0)
            }
        )

        logger.info(
            f"DNS cleanup completed for workspace {workspace.id}: "
            f"{result.get('records_deleted', 0)} records deleted"
        )

        return {
            'status': 'completed',
            'workspace_id': str(workspace_id),
            'dns_cleanup': result
        }

    except Exception as e:
        logger.error(f"DNS cleanup failed for workspace {workspace_id}: {e}")

        # Log failure
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            DeProvisioningLog.log_step_failed(
                deprovisioning=workspace.deprovisioning,
                step='cleanup_dns_records',
                error=str(e),
                attempt=self.request.retries + 1
            )
        except:
            pass

        raise self.retry(exc=e)


@shared_task(
    name='workspace_core.finalize_deprovisioning',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def finalize_deprovisioning(self, previous_result, workspace_id):
    """
    Finalize deprovisioning after all cleanup tasks complete
    Marks ProvisioningRecord as cancelled and DeProvisioningRecord as completed
    """
    from workspace.core.models import Workspace, ProvisioningRecord, DeProvisioningRecord

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        deprovisioning_record = workspace.deprovisioning

        logger.info(f"Finalizing deprovisioning for workspace {workspace.id}")

        with transaction.atomic():
            # Mark provisioning record as cancelled
            try:
                provisioning = workspace.provisioning
                provisioning.status = 'cancelled'
                provisioning.save(update_fields=['status', 'updated_at'])
            except ProvisioningRecord.DoesNotExist:
                logger.warning(f"No provisioning record found for workspace {workspace.id}")

            # Mark deprovisioning as completed
            cleanup_summary = {
                'infrastructure_suspended': True,
                's3_files_cleaned': True,
                'cdn_cache_invalidated': True,
                'dns_records_cleaned': True,
                'completed_at': timezone.now().isoformat()
            }
            deprovisioning_record.mark_completed(cleanup_summary)

        logger.info(
            f"Deprovisioning completed for workspace {workspace.id} "
            f"(status: {workspace.status})"
        )

        return {
            'status': 'completed',
            'workspace_id': str(workspace_id),
            'deprovisioning_id': str(deprovisioning_record.id),
            'cleanup_summary': cleanup_summary
        }

    except Exception as e:
        logger.error(f"Failed to finalize deprovisioning for workspace {workspace_id}: {e}")
        raise self.retry(exc=e)


@shared_task(
    name='workspace_core.handle_deprovisioning_failure',
    bind=True
)
def handle_deprovisioning_failure(self, workspace_id, failed_step):
    """
    Handle deprovisioning failure
    Marks deprovisioning as failed for admin review
    """
    from workspace.core.models import Workspace

    try:
        workspace = Workspace.objects.get(id=workspace_id)
        deprovisioning_record = workspace.deprovisioning

        error_message = f"Deprovisioning failed at step: {failed_step}"
        deprovisioning_record.mark_failed(error_message)

        logger.error(
            f"Deprovisioning failed for workspace {workspace.id} at step {failed_step}. "
            f"Manual intervention required."
        )

        # TODO: Send notification to admins for manual review

    except Exception as e:
        logger.error(f"Failed to handle deprovisioning failure for workspace {workspace_id}: {e}")


@shared_task(
    name='workspace_core.scan_overdue_deprovisionings',
    bind=True
)
def scan_overdue_deprovisionings(self):
    """
    Celery Beat task to scan for overdue deprovisionings
    Runs every hour to check if any workspaces need deprovisioning
    """
    from workspace.core.models import DeProvisioningRecord

    try:
        # Find all scheduled deprovisionings that are overdue
        overdue = DeProvisioningRecord.objects.filter(
            status='scheduled',
            scheduled_for__lte=timezone.now()
        ).select_related('workspace')

        count = overdue.count()
        logger.info(f"Found {count} overdue deprovisionings")

        # Queue deprovisioning for each overdue workspace
        for deprovisioning in overdue:
            try:
                deprovision_workspace.apply_async(
                    args=[str(deprovisioning.workspace_id)],
                    countdown=10  # Small delay to avoid thundering herd
                )
                logger.info(f"Queued deprovisioning for workspace {deprovisioning.workspace_id}")
            except Exception as e:
                logger.error(
                    f"Failed to queue deprovisioning for workspace {deprovisioning.workspace_id}: {e}"
                )

        return {
            'status': 'completed',
            'overdue_count': count,
            'queued': count
        }

    except Exception as e:
        logger.error(f"Failed to scan overdue deprovisionings: {e}")
        raise self.retry(exc=e)
