"""
Sync API Views
API endpoints for workspace synchronization management and monitoring
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from django.core.paginator import Paginator
from workspace.core.models import Workspace
from .models import SyncEvent, WebhookDelivery, PollingState, SyncMetrics
from .tasks import (
    trigger_workspace_sync_async,
    retry_failed_webhooks_task,
    start_polling_for_workspace_task,
    stop_polling_for_workspace_task,
    health_check_sync_system_task
)
from .services.webhook_service import webhook_service
from .services.polling_service import polling_service
from .services.template_binding_service import template_binding_service
from .signals import trigger_manual_sync
import logging
import asyncio

logger = logging.getLogger('workspace.sync.views')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_workspace_sync(request, workspace_id):
    """
    Manually trigger workspace synchronization

    POST /api/workspaces/{workspace_id}/sync/trigger/
    {
        "event_type": "manual.sync",
        "entity_type": "Workspace",
        "data": { ... }
    }
    """
    try:
        # Verify workspace access
        workspace = get_object_or_404(
            Workspace.objects.filter(created_by=request.user),
            id=workspace_id
        )

        # Get request data
        event_type = request.data.get('event_type', 'manual.sync')
        entity_type = request.data.get('entity_type', 'Manual')
        data = request.data.get('data', {})

        # Trigger sync
        task = trigger_workspace_sync_async.delay(
            workspace_id=str(workspace_id),
            event_type=event_type,
            entity_type=entity_type,
            entity_id='manual',
            data=data,
            changed_fields=['manual_trigger'],
            user_id=str(request.user.id)
        )

        return Response({
            'success': True,
            'task_id': task.id,
            'workspace_id': str(workspace_id),
            'event_type': event_type,
            'message': 'Sync triggered successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to trigger manual sync: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_events_list(request, workspace_id):
    """
    Get list of sync events for workspace

    GET /api/workspaces/{workspace_id}/sync/events/
    ?status=pending&limit=20&offset=0
    """
    try:
        # Verify workspace access
        workspace = get_object_or_404(
            Workspace.objects.filter(created_by=request.user),
            id=workspace_id
        )

        # Build query
        events = SyncEvent.objects.filter(workspace=workspace).order_by('-created_at')

        # Apply filters
        sync_status = request.GET.get('status')
        if sync_status:
            events = events.filter(sync_status=sync_status)

        event_type = request.GET.get('event_type')
        if event_type:
            events = events.filter(event_type__icontains=event_type)

        # Pagination
        limit = min(int(request.GET.get('limit', 20)), 100)
        offset = int(request.GET.get('offset', 0))

        total_count = events.count()
        events_page = events[offset:offset + limit]

        # Serialize events
        events_data = []
        for event in events_page:
            events_data.append({
                'id': str(event.id),
                'event_type': event.event_type,
                'entity_type': event.entity_type,
                'entity_id': event.entity_id,
                'sync_status': event.sync_status,
                'retry_count': event.retry_count,
                'max_retries': event.max_retries,
                'error_message': event.error_message,
                'created_at': event.created_at.isoformat(),
                'completed_at': event.completed_at.isoformat() if event.completed_at else None,
                'webhook_deliveries_count': event.webhook_deliveries.count()
            })

        return Response({
            'events': events_data,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': offset + limit < total_count
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get sync events: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_event_detail(request, workspace_id, event_id):
    """
    Get detailed information about a sync event

    GET /api/workspaces/{workspace_id}/sync/events/{event_id}/
    """
    try:
        # Verify workspace access
        workspace = get_object_or_404(
            Workspace.objects.filter(created_by=request.user),
            id=workspace_id
        )

        # Get sync event
        event = get_object_or_404(
            SyncEvent.objects.filter(workspace=workspace),
            id=event_id
        )

        # Get webhook deliveries
        deliveries = event.webhook_deliveries.order_by('-created_at')
        deliveries_data = []

        for delivery in deliveries:
            deliveries_data.append({
                'id': str(delivery.id),
                'webhook_url': delivery.webhook_url,
                'delivery_status': delivery.delivery_status,
                'http_status_code': delivery.http_status_code,
                'response_body': delivery.response_body,
                'request_duration_ms': delivery.request_duration_ms,
                'attempt_number': delivery.attempt_number,
                'created_at': delivery.created_at.isoformat()
            })

        return Response({
            'event': {
                'id': str(event.id),
                'event_type': event.event_type,
                'entity_type': event.entity_type,
                'entity_id': event.entity_id,
                'sync_status': event.sync_status,
                'retry_count': event.retry_count,
                'max_retries': event.max_retries,
                'payload_data': event.payload_data,
                'error_message': event.error_message,
                'created_at': event.created_at.isoformat(),
                'completed_at': event.completed_at.isoformat() if event.completed_at else None
            },
            'webhook_deliveries': deliveries_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get sync event detail: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_sync_event(request, workspace_id, event_id):
    """
    Manually retry a failed sync event

    POST /api/workspaces/{workspace_id}/sync/events/{event_id}/retry/
    """
    try:
        # Verify workspace access
        workspace = get_object_or_404(
            Workspace.objects.filter(created_by=request.user),
            id=workspace_id
        )

        # Get sync event
        event = get_object_or_404(
            SyncEvent.objects.filter(workspace=workspace),
            id=event_id
        )

        # Check if event can be retried
        if event.sync_status not in ['failed', 'timeout']:
            return Response({
                'success': False,
                'error': f'Event cannot be retried (status: {event.sync_status})'
            }, status=status.HTTP_400_BAD_REQUEST)

        if event.retry_count >= event.max_retries:
            return Response({
                'success': False,
                'error': 'Event has reached maximum retry attempts'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Reset event status and trigger retry
        event.sync_status = 'pending'
        event.error_message = None
        event.save(update_fields=['sync_status', 'error_message'])

        # Trigger new sync with same data
        task = trigger_workspace_sync_async.delay(
            workspace_id=str(workspace_id),
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            data=event.payload_data,
            changed_fields=['retry'],
            user_id=str(request.user.id)
        )

        return Response({
            'success': True,
            'task_id': task.id,
            'event_id': str(event_id),
            'message': 'Event retry triggered successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to retry sync event: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workspace_sync_status(request, workspace_id):
    """
    Get current sync status for workspace

    GET /api/workspaces/{workspace_id}/sync/status/
    """
    try:
        # Verify workspace access
        workspace = get_object_or_404(
            Workspace.objects.filter(created_by=request.user),
            id=workspace_id
        )

        # Get recent sync stats
        from datetime import timedelta
        recent_cutoff = timezone.now() - timedelta(hours=24)

        recent_events = SyncEvent.objects.filter(
            workspace=workspace,
            created_at__gte=recent_cutoff
        )

        # Calculate stats
        total_events = recent_events.count()
        pending_events = recent_events.filter(sync_status='pending').count()
        completed_events = recent_events.filter(sync_status='completed').count()
        failed_events = recent_events.filter(sync_status='failed').count()

        # Get polling status
        try:
            polling_state = PollingState.objects.get(workspace=workspace)
            polling_status = {
                'is_active': polling_state.is_polling_active,
                'last_poll': polling_state.last_poll_at.isoformat() if polling_state.last_poll_at else None,
                'consecutive_failures': polling_state.consecutive_failures,
                'last_success': polling_state.last_successful_poll_at.isoformat() if polling_state.last_successful_poll_at else None
            }
        except PollingState.DoesNotExist:
            polling_status = {
                'is_active': False,
                'last_poll': None,
                'consecutive_failures': 0,
                'last_success': None
            }

        # Calculate success rate
        success_rate = 0
        if total_events > 0:
            success_rate = (completed_events / total_events) * 100

        return Response({
            'workspace_id': str(workspace_id),
            'sync_health': 'healthy' if success_rate >= 95 else 'degraded' if success_rate >= 80 else 'unhealthy',
            'success_rate': round(success_rate, 2),
            'recent_24h_stats': {
                'total_events': total_events,
                'pending': pending_events,
                'completed': completed_events,
                'failed': failed_events
            },
            'polling_status': polling_status,
            'last_updated': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get workspace sync status: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_workspace_polling(request, workspace_id):
    """
    Start polling for workspace

    POST /api/workspaces/{workspace_id}/sync/polling/start/
    """
    try:
        # Verify workspace access
        workspace = get_object_or_404(
            Workspace.objects.filter(created_by=request.user),
            id=workspace_id
        )

        # Trigger polling start task
        task = start_polling_for_workspace_task.delay(str(workspace_id))

        return Response({
            'success': True,
            'task_id': task.id,
            'workspace_id': str(workspace_id),
            'message': 'Polling start triggered successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to start workspace polling: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_workspace_polling(request, workspace_id):
    """
    Stop polling for workspace

    POST /api/workspaces/{workspace_id}/sync/polling/stop/
    """
    try:
        # Verify workspace access
        workspace = get_object_or_404(
            Workspace.objects.filter(created_by=request.user),
            id=workspace_id
        )

        # Trigger polling stop task
        task = stop_polling_for_workspace_task.delay(str(workspace_id))

        return Response({
            'success': True,
            'task_id': task.id,
            'workspace_id': str(workspace_id),
            'message': 'Polling stop triggered successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to stop workspace polling: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_metrics(request, workspace_id):
    """
    Get sync metrics for workspace

    GET /api/workspaces/{workspace_id}/sync/metrics/
    ?days=7&format=chart
    """
    try:
        # Verify workspace access
        workspace = get_object_or_404(
            Workspace.objects.filter(created_by=request.user),
            id=workspace_id
        )

        # Get date range
        days = int(request.GET.get('days', 7))
        from datetime import timedelta
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # Get metrics
        metrics = SyncMetrics.objects.filter(
            workspace=workspace,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        # Format response
        format_type = request.GET.get('format', 'table')

        if format_type == 'chart':
            # Chart format for frontend visualization
            chart_data = {
                'labels': [],
                'datasets': {
                    'events_generated': [],
                    'events_processed': [],
                    'events_failed': [],
                    'webhooks_delivered': [],
                    'webhooks_failed': [],
                    'avg_delivery_time': []
                }
            }

            for metric in metrics:
                chart_data['labels'].append(metric.date.isoformat())
                chart_data['datasets']['events_generated'].append(metric.events_generated)
                chart_data['datasets']['events_processed'].append(metric.events_processed)
                chart_data['datasets']['events_failed'].append(metric.events_failed)
                chart_data['datasets']['webhooks_delivered'].append(metric.webhooks_delivered)
                chart_data['datasets']['webhooks_failed'].append(metric.webhooks_failed)
                chart_data['datasets']['avg_delivery_time'].append(metric.avg_delivery_time_ms)

            return Response(chart_data, status=status.HTTP_200_OK)

        else:
            # Table format
            metrics_data = []
            for metric in metrics:
                metrics_data.append({
                    'date': metric.date.isoformat(),
                    'events_generated': metric.events_generated,
                    'events_processed': metric.events_processed,
                    'events_failed': metric.events_failed,
                    'webhooks_sent': metric.webhooks_sent,
                    'webhooks_delivered': metric.webhooks_delivered,
                    'webhooks_failed': metric.webhooks_failed,
                    'avg_delivery_time_ms': metric.avg_delivery_time_ms,
                    'max_delivery_time_ms': metric.max_delivery_time_ms,
                    'success_rate': round(
                        (metric.events_processed / max(metric.events_generated, 1)) * 100, 2
                    )
                })

            return Response({
                'metrics': metrics_data,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                }
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get sync metrics: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_template_config(request):
    """
    Validate template configuration for variable usage

    POST /api/sync/validate-template/
    {
        "template_config": { ... }
    }
    """
    try:
        template_config = request.data.get('template_config', {})

        if not template_config:
            return Response({
                'valid': False,
                'error': 'Template configuration is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate template
        validation_result = template_binding_service.validate_template_variables(
            template_config
        )

        return Response(validation_result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to validate template config: {str(e)}")
        return Response({
            'valid': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health(request):
    """
    Get overall sync system health

    GET /api/sync/health/
    """
    try:
        # Check cache for recent health data
        cache_key = 'sync_system_health'
        cached_health = cache.get(cache_key)

        if cached_health:
            return Response(cached_health, status=status.HTTP_200_OK)

        # Trigger health check task
        task = health_check_sync_system_task.delay()

        # For immediate response, calculate basic health
        from datetime import timedelta
        recent_cutoff = timezone.now() - timedelta(minutes=15)

        recent_events = SyncEvent.objects.filter(created_at__gte=recent_cutoff)
        recent_deliveries = WebhookDelivery.objects.filter(created_at__gte=recent_cutoff)

        total_events = recent_events.count()
        failed_events = recent_events.filter(sync_status='failed').count()
        total_deliveries = recent_deliveries.count()
        failed_deliveries = recent_deliveries.filter(delivery_status='failed').count()

        event_success_rate = 100.0
        if total_events > 0:
            event_success_rate = ((total_events - failed_events) / total_events) * 100

        delivery_success_rate = 100.0
        if total_deliveries > 0:
            delivery_success_rate = ((total_deliveries - failed_deliveries) / total_deliveries) * 100

        health_data = {
            'is_healthy': event_success_rate >= 95 and delivery_success_rate >= 90,
            'event_success_rate': round(event_success_rate, 2),
            'delivery_success_rate': round(delivery_success_rate, 2),
            'total_events_last_15min': total_events,
            'failed_events_last_15min': failed_events,
            'total_deliveries_last_15min': total_deliveries,
            'failed_deliveries_last_15min': failed_deliveries,
            'health_check_task_id': task.id,
            'checked_at': timezone.now().isoformat()
        }

        # Cache for 5 minutes
        cache.set(cache_key, health_data, 300)

        return Response(health_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        return Response({
            'is_healthy': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)