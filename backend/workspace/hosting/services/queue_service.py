"""
Workspace Queue Service
Background job throttling per workspace
Prevents queue saturation in shared pool infrastructure
"""
import redis
from celery import Task
from django.conf import settings
from typing import Optional


class WorkspaceQueueService:
    """
    Background job throttling per workspace
    Prevents one workspace from saturating Celery queue
    """

    # Max concurrent jobs per tier
    TIER_JOB_LIMITS = {
        'free': 2,
        'beginning': 5,
        'pro': 15,
        'enterprise': 50,
    }

    def __init__(self):
        redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
        redis_port = getattr(settings, 'REDIS_PORT', 6379)

        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )

    def can_enqueue_job(self, workspace_id: str, tier: str) -> bool:
        """
        Check if workspace can enqueue more jobs

        Args:
            workspace_id: Workspace UUID
            tier: Subscription tier

        Returns:
            True if workspace can enqueue job
        """
        limit = self.TIER_JOB_LIMITS.get(tier, 2)

        # Count active jobs for workspace
        active_jobs_key = f"queue:ws:{workspace_id}:active"
        active_count = int(self.redis_client.get(active_jobs_key) or 0)

        return active_count < limit

    def track_job_start(self, workspace_id: str):
        """
        Track job start

        Args:
            workspace_id: Workspace UUID
        """
        key = f"queue:ws:{workspace_id}:active"
        self.redis_client.incr(key)
        self.redis_client.expire(key, 7200)  # 2 hours max job duration

    def track_job_end(self, workspace_id: str):
        """
        Track job completion

        Args:
            workspace_id: Workspace UUID
        """
        key = f"queue:ws:{workspace_id}:active"
        current = int(self.redis_client.get(key) or 0)
        if current > 0:
            self.redis_client.decr(key)

    def get_active_job_count(self, workspace_id: str) -> int:
        """
        Get number of active jobs for workspace

        Args:
            workspace_id: Workspace UUID

        Returns:
            Number of active jobs
        """
        key = f"queue:ws:{workspace_id}:active"
        return int(self.redis_client.get(key) or 0)


class WorkspaceThrottledTask(Task):
    """
    Base Celery task with workspace throttling
    Use this instead of @task for workspace-specific jobs
    """

    def apply_async(self, args=None, kwargs=None, **options):
        """
        Override apply_async to check queue limits

        Usage:
            @app.task(base=WorkspaceThrottledTask)
            def my_task(workspace_id, tier, **kwargs):
                # Task logic
                pass
        """
        workspace_id = kwargs.get('workspace_id') if kwargs else None
        tier = kwargs.get('tier', 'free') if kwargs else 'free'

        if workspace_id:
            queue_service = WorkspaceQueueService()

            # Check if workspace can enqueue job
            if not queue_service.can_enqueue_job(workspace_id, tier):
                # Queue full, delay job
                if 'countdown' not in options:
                    options['countdown'] = 30  # Retry after 30 seconds

        return super().apply_async(args, kwargs, **options)

    def on_success(self, retval, task_id, args, kwargs):
        """Track job completion on success"""
        workspace_id = kwargs.get('workspace_id')
        if workspace_id:
            queue_service = WorkspaceQueueService()
            queue_service.track_job_end(workspace_id)

        return super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Track job completion on failure"""
        workspace_id = kwargs.get('workspace_id')
        if workspace_id:
            queue_service = WorkspaceQueueService()
            queue_service.track_job_end(workspace_id)

        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def __call__(self, *args, **kwargs):
        """Track job start when executed"""
        workspace_id = kwargs.get('workspace_id')
        if workspace_id:
            queue_service = WorkspaceQueueService()
            queue_service.track_job_start(workspace_id)

        return super().__call__(*args, **kwargs)
