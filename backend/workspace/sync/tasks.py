"""
Celery Tasks for Workspace Synchronization
Async task processing for webhook delivery and sync operations
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
from celery import shared_task
from celery.exceptions import Retry
from django.utils import timezone
from django.apps import apps
from typing import Dict, Any, List, Optional
import asyncio
import logging

logger = logging.getLogger('workspace.sync.tasks')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def trigger_workspace_sync_async(
    self,
    workspace_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    data: Dict[str, Any],
    changed_fields: List[str],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async task to trigger workspace synchronization

    Args:
        workspace_id: UUID of the workspace
        event_type: Type of event (product.created, etc.)
        entity_type: Model name (Product, Post, etc.)
        entity_id: ID of the changed entity
        data: Event payload data
        changed_fields: List of changed field names
        user_id: User who triggered the change

    Returns:
        Dict with task result
    """
    try:
        # Import webhook service (avoid circular imports)
        from .services.webhook_service import webhook_service

        # Create async event loop for webhook delivery
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Send webhook to all deployed sites
            result = loop.run_until_complete(
                webhook_service.send_workspace_webhook(
                    workspace_id=workspace_id,
                    event_type=event_type,
                    data=data,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    user_id=user_id
                )
            )

            return {
                'success': True,
                'task_id': self.request.id,
                'workspace_id': workspace_id,
                'event_type': event_type,
                'webhook_result': result
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Sync task failed for workspace {workspace_id}: {str(e)}")

        # Retry task with exponential backoff
        try:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        except Exception:
            # Max retries reached
            return {
                'success': False,
                'task_id': self.request.id,
                'workspace_id': workspace_id,
                'error': str(e),
                'retries_exhausted': True
            }


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retry_failed_webhooks_task(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Periodic task to retry failed webhook deliveries

    Args:
        workspace_id: Optional workspace ID to limit retries

    Returns:
        Dict with retry results
    """
    try:
        from .services.webhook_service import webhook_service

        # Create async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                webhook_service.retry_failed_webhooks(workspace_id)
            )

            return {
                'success': True,
                'task_id': self.request.id,
                'retry_result': result
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Webhook retry task failed: {str(e)}")

        try:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        except Exception:
            return {
                'success': False,
                'task_id': self.request.id,
                'error': str(e),
                'retries_exhausted': True
            }


@shared_task(bind=True)
def start_polling_for_workspace_task(self, workspace_id: str) -> Dict[str, Any]:
    """
    Task to start polling for a specific workspace

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Dict with start result
    """
    try:
        from .services.polling_service import polling_service

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                polling_service.start_polling_for_workspace(workspace_id)
            )

            return {
                'success': True,
                'task_id': self.request.id,
                'polling_result': result
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Start polling task failed: {str(e)}")
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e)
        }


@shared_task(bind=True)
def stop_polling_for_workspace_task(self, workspace_id: str) -> Dict[str, Any]:
    """
    Task to stop polling for a specific workspace

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Dict with stop result
    """
    try:
        from .services.polling_service import polling_service

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                polling_service.stop_polling_for_workspace(workspace_id)
            )

            return {
                'success': True,
                'task_id': self.request.id,
                'polling_result': result
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Stop polling task failed: {str(e)}")
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e)
        }


@shared_task(bind=True)
def generate_sync_metrics_task(self, date_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate daily sync metrics for monitoring and analytics

    Args:
        date_str: Date in YYYY-MM-DD format (defaults to yesterday)

    Returns:
        Dict with metrics generation result
    """
    try:
        from datetime import datetime, timedelta
        from django.db import models

        # Parse date or default to yesterday
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = (timezone.now() - timedelta(days=1)).date()

        # Get models
        SyncEvent = apps.get_model('workspace_sync', 'SyncEvent')
        WebhookDelivery = apps.get_model('workspace_sync', 'WebhookDelivery')
        SyncMetrics = apps.get_model('workspace_sync', 'SyncMetrics')
        Workspace = apps.get_model('core', 'Workspace')

        metrics_created = 0

        # Generate metrics for each workspace
        for workspace in Workspace.objects.filter(is_active=True):
            # Get events for the date
            events_qs = SyncEvent.objects.filter(
                workspace=workspace,
                created_at__date=target_date
            )

            # Get webhook deliveries for the date
            deliveries_qs = WebhookDelivery.objects.filter(
                sync_event__workspace=workspace,
                created_at__date=target_date
            )

            # Calculate metrics
            events_generated = events_qs.count()
            events_processed = events_qs.filter(sync_status='completed').count()
            events_failed = events_qs.filter(sync_status='failed').count()

            webhooks_sent = deliveries_qs.count()
            webhooks_delivered = deliveries_qs.filter(delivery_status='delivered').count()
            webhooks_failed = deliveries_qs.filter(delivery_status='failed').count()

            # Calculate performance metrics
            successful_deliveries = deliveries_qs.filter(
                delivery_status='delivered',
                request_duration_ms__isnull=False
            )

            if successful_deliveries.exists():
                avg_delivery_time = successful_deliveries.aggregate(
                    avg=models.Avg('request_duration_ms')
                )['avg'] or 0
                max_delivery_time = successful_deliveries.aggregate(
                    max=models.Max('request_duration_ms')
                )['max'] or 0
            else:
                avg_delivery_time = 0
                max_delivery_time = 0

            # Create or update metrics
            metrics, created = SyncMetrics.objects.update_or_create(
                workspace=workspace,
                date=target_date,
                defaults={
                    'events_generated': events_generated,
                    'events_processed': events_processed,
                    'events_failed': events_failed,
                    'webhooks_sent': webhooks_sent,
                    'webhooks_delivered': webhooks_delivered,
                    'webhooks_failed': webhooks_failed,
                    'avg_delivery_time_ms': int(avg_delivery_time),
                    'max_delivery_time_ms': int(max_delivery_time),
                    'polls_completed': 0,  # Would be calculated from polling data
                    'polls_with_changes': 0
                }
            )

            if created:
                metrics_created += 1

        return {
            'success': True,
            'task_id': self.request.id,
            'date': target_date.isoformat(),
            'metrics_created': metrics_created,
            'workspaces_processed': Workspace.objects.filter(is_active=True).count()
        }

    except Exception as e:
        logger.error(f"Metrics generation task failed: {str(e)}")
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e)
        }


@shared_task(bind=True)
def cleanup_old_sync_data_task(self, days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old sync data to manage database size

    Args:
        days_to_keep: Number of days of data to retain

    Returns:
        Dict with cleanup results
    """
    try:
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Get models
        SyncEvent = apps.get_model('workspace_sync', 'SyncEvent')
        WebhookDelivery = apps.get_model('workspace_sync', 'WebhookDelivery')

        # Delete old completed sync events
        deleted_events = SyncEvent.objects.filter(
            created_at__lt=cutoff_date,
            sync_status='completed'
        ).delete()

        # Delete old successful webhook deliveries
        deleted_deliveries = WebhookDelivery.objects.filter(
            created_at__lt=cutoff_date,
            delivery_status='delivered'
        ).delete()

        return {
            'success': True,
            'task_id': self.request.id,
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_events': deleted_events[0] if deleted_events else 0,
            'deleted_deliveries': deleted_deliveries[0] if deleted_deliveries else 0
        }

    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e)
        }


@shared_task(bind=True)
def health_check_sync_system_task(self) -> Dict[str, Any]:
    """
    Health check task for the sync system
    Monitors system health and sends alerts if needed

    Returns:
        Dict with health check results
    """
    try:
        from datetime import timedelta

        # Get models
        SyncEvent = apps.get_model('workspace_sync', 'SyncEvent')
        WebhookDelivery = apps.get_model('workspace_sync', 'WebhookDelivery')
        PollingState = apps.get_model('workspace_sync', 'PollingState')

        # Check recent sync performance
        last_hour = timezone.now() - timedelta(hours=1)

        recent_events = SyncEvent.objects.filter(created_at__gte=last_hour)
        recent_deliveries = WebhookDelivery.objects.filter(created_at__gte=last_hour)

        # Calculate health metrics
        total_events = recent_events.count()
        failed_events = recent_events.filter(sync_status='failed').count()

        total_deliveries = recent_deliveries.count()
        failed_deliveries = recent_deliveries.filter(delivery_status='failed').count()

        # Calculate success rates
        event_success_rate = 100.0
        if total_events > 0:
            event_success_rate = ((total_events - failed_events) / total_events) * 100

        delivery_success_rate = 100.0
        if total_deliveries > 0:
            delivery_success_rate = ((total_deliveries - failed_deliveries) / total_deliveries) * 100

        # Check polling health
        polling_states = PollingState.objects.filter(is_polling_active=True)
        healthy_polling = polling_states.filter(consecutive_failures__lt=5).count()

        # Determine overall health
        is_healthy = (
            event_success_rate >= 95.0 and
            delivery_success_rate >= 90.0 and
            (healthy_polling / max(polling_states.count(), 1)) >= 0.9
        )

        health_data = {
            'is_healthy': is_healthy,
            'event_success_rate': round(event_success_rate, 2),
            'delivery_success_rate': round(delivery_success_rate, 2),
            'total_events_last_hour': total_events,
            'failed_events_last_hour': failed_events,
            'total_deliveries_last_hour': total_deliveries,
            'failed_deliveries_last_hour': failed_deliveries,
            'active_polling_workspaces': polling_states.count(),
            'healthy_polling_workspaces': healthy_polling,
            'checked_at': timezone.now().isoformat()
        }

        # Log health status
        if is_healthy:
            logger.info(f"Sync system health check: HEALTHY ({event_success_rate:.1f}% events, {delivery_success_rate:.1f}% deliveries)")
        else:
            logger.warning(f"Sync system health check: UNHEALTHY ({event_success_rate:.1f}% events, {delivery_success_rate:.1f}% deliveries)")

        return {
            'success': True,
            'task_id': self.request.id,
            'health_data': health_data
        }

    except Exception as e:
        logger.error(f"Health check task failed: {str(e)}")
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e)
        }


@shared_task(bind=True)
def update_deployed_site_data_task(
    self,
    site_id: str,
    workspace_id: str,
    changed_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update deployed site with changed workspace data

    Args:
        site_id: ID of the deployed site
        workspace_id: ID of the workspace
        changed_data: Data that has changed

    Returns:
        Dict with update result
    """
    try:
        from .services.template_binding_service import template_binding_service

        result = template_binding_service.update_deployed_site_data(
            site_id=site_id,
            workspace_id=workspace_id,
            changed_data=changed_data
        )

        return {
            'success': True,
            'task_id': self.request.id,
            'update_result': result
        }

    except Exception as e:
        logger.error(f"Site update task failed: {str(e)}")
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e)
        }


# Periodic task schedules (to be configured in Celery beat)
def setup_periodic_tasks():
    """
    Setup periodic tasks for sync system maintenance
    This would be called from your main Celery configuration
    """
    from celery.schedules import crontab

    # These would be added to CELERY_BEAT_SCHEDULE in settings
    periodic_tasks = {
        'retry-failed-webhooks': {
            'task': 'workspace.sync.tasks.retry_failed_webhooks_task',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
        'generate-daily-metrics': {
            'task': 'workspace.sync.tasks.generate_sync_metrics_task',
            'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        },
        'cleanup-old-sync-data': {
            'task': 'workspace.sync.tasks.cleanup_old_sync_data_task',
            'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Weekly on Sunday at 2 AM
        },
        'health-check-sync-system': {
            'task': 'workspace.sync.tasks.health_check_sync_system_task',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
        }
    }

    return periodic_tasks