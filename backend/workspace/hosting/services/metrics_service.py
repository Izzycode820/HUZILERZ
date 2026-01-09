"""
Metrics Service for Infrastructure Operations

Tracks key metrics for monitoring and alerting:
- Provisioning failures and success rates
- Deployment/publish failures and success rates
- Operation latency and performance
- Resource usage trends

Integration points:
- Django cache for fast metric storage
- Can be extended to export to Prometheus, DataDog, CloudWatch, etc.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Avg, Q
from functools import wraps

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for tracking and reporting infrastructure metrics

    Metrics are stored in cache with periodic aggregation to DB
    """

    # Metric key prefixes
    PROVISION_PREFIX = "metrics:provision"
    DEPLOYMENT_PREFIX = "metrics:deployment"
    PERFORMANCE_PREFIX = "metrics:performance"

    # Time windows for aggregation
    MINUTE = 60
    HOUR = 3600
    DAY = 86400

    @staticmethod
    def _get_metric_key(prefix: str, name: str, window: str = "hour") -> str:
        """Generate cache key for a metric"""
        timestamp = int(time.time())
        if window == "minute":
            bucket = timestamp // 60
        elif window == "hour":
            bucket = timestamp // 3600
        else:  # day
            bucket = timestamp // 86400

        return f"{prefix}:{name}:{window}:{bucket}"

    @classmethod
    def record_provision_attempt(cls, workspace_id: str, success: bool, duration_seconds: float, metadata: Optional[Dict] = None):
        """
        Record a provisioning attempt

        Args:
            workspace_id: UUID of workspace
            success: Whether provisioning succeeded
            duration_seconds: Time taken for provisioning
            metadata: Additional context
        """
        # Increment counters
        if success:
            cls._increment_counter(cls.PROVISION_PREFIX, "success", ["minute", "hour", "day"])
        else:
            cls._increment_counter(cls.PROVISION_PREFIX, "failure", ["minute", "hour", "day"])

        # Record duration
        cls._record_duration(cls.PROVISION_PREFIX, "duration", duration_seconds, ["minute", "hour"])

        # Log to database for historical analysis
        try:
            from workspace.core.models import ProvisioningLog
            from workspace.core.models import Workspace

            workspace = Workspace.objects.get(id=workspace_id)
            provisioning_record = getattr(workspace, 'provisioning', None)

            if provisioning_record:
                ProvisioningLog.objects.create(
                    provisioning=provisioning_record,
                    step='provision_complete',
                    status='completed' if success else 'failed',
                    metadata={
                        'duration_seconds': duration_seconds,
                        'success': success,
                        **(metadata or {})
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to log provision metric to DB: {e}")

        logger.info(
            f"[Metrics] Provision {'SUCCESS' if success else 'FAILURE'} "
            f"for workspace {workspace_id} in {duration_seconds:.2f}s"
        )

    @classmethod
    def record_deployment_attempt(cls, workspace_id: str, success: bool, duration_seconds: float, rolled_back: bool = False, metadata: Optional[Dict] = None):
        """
        Record a deployment/publish attempt

        Args:
            workspace_id: UUID of workspace
            success: Whether deployment succeeded
            duration_seconds: Time taken for deployment
            rolled_back: Whether deployment was rolled back
            metadata: Additional context
        """
        # Increment counters
        if success:
            cls._increment_counter(cls.DEPLOYMENT_PREFIX, "success", ["minute", "hour", "day"])
        else:
            cls._increment_counter(cls.DEPLOYMENT_PREFIX, "failure", ["minute", "hour", "day"])

        if rolled_back:
            cls._increment_counter(cls.DEPLOYMENT_PREFIX, "rollback", ["minute", "hour", "day"])

        # Record duration
        cls._record_duration(cls.DEPLOYMENT_PREFIX, "duration", duration_seconds, ["minute", "hour"])

        logger.info(
            f"[Metrics] Deployment {'SUCCESS' if success else 'FAILURE'} "
            f"for workspace {workspace_id} in {duration_seconds:.2f}s "
            f"{'(ROLLED BACK)' if rolled_back else ''}"
        )

    @classmethod
    def _increment_counter(cls, prefix: str, name: str, windows: list):
        """Increment a counter metric across multiple time windows"""
        for window in windows:
            key = cls._get_metric_key(prefix, name, window)
            try:
                cache.incr(key)
            except ValueError:
                # Key doesn't exist, set it
                ttl = cls.DAY if window == "day" else (cls.HOUR if window == "hour" else cls.MINUTE * 2)
                cache.set(key, 1, timeout=ttl * 2)  # Double TTL for safety

    @classmethod
    def _record_duration(cls, prefix: str, name: str, duration: float, windows: list):
        """Record duration metric with running average"""
        for window in windows:
            key = cls._get_metric_key(prefix, f"{name}_sum", window)
            count_key = cls._get_metric_key(prefix, f"{name}_count", window)

            ttl = cls.DAY if window == "day" else (cls.HOUR if window == "hour" else cls.MINUTE * 2)

            # Increment sum
            try:
                current = cache.get(key, 0)
                cache.set(key, current + duration, timeout=ttl * 2)
            except:
                cache.set(key, duration, timeout=ttl * 2)

            # Increment count
            try:
                cache.incr(count_key)
            except ValueError:
                cache.set(count_key, 1, timeout=ttl * 2)

    @classmethod
    def get_provision_metrics(cls, window: str = "hour") -> Dict[str, Any]:
        """
        Get provisioning metrics for a time window

        Args:
            window: "minute", "hour", or "day"

        Returns:
            Dict with success_count, failure_count, success_rate, avg_duration
        """
        success_key = cls._get_metric_key(cls.PROVISION_PREFIX, "success", window)
        failure_key = cls._get_metric_key(cls.PROVISION_PREFIX, "failure", window)
        duration_sum_key = cls._get_metric_key(cls.PROVISION_PREFIX, "duration_sum", window)
        duration_count_key = cls._get_metric_key(cls.PROVISION_PREFIX, "duration_count", window)

        success_count = cache.get(success_key, 0)
        failure_count = cache.get(failure_key, 0)
        duration_sum = cache.get(duration_sum_key, 0)
        duration_count = cache.get(duration_count_key, 0)

        total = success_count + failure_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        avg_duration = (duration_sum / duration_count) if duration_count > 0 else 0

        return {
            'success_count': success_count,
            'failure_count': failure_count,
            'total_count': total,
            'success_rate_percent': round(success_rate, 2),
            'avg_duration_seconds': round(avg_duration, 2),
            'window': window
        }

    @classmethod
    def get_deployment_metrics(cls, window: str = "hour") -> Dict[str, Any]:
        """
        Get deployment metrics for a time window

        Args:
            window: "minute", "hour", or "day"

        Returns:
            Dict with success_count, failure_count, rollback_count, success_rate, avg_duration
        """
        success_key = cls._get_metric_key(cls.DEPLOYMENT_PREFIX, "success", window)
        failure_key = cls._get_metric_key(cls.DEPLOYMENT_PREFIX, "failure", window)
        rollback_key = cls._get_metric_key(cls.DEPLOYMENT_PREFIX, "rollback", window)
        duration_sum_key = cls._get_metric_key(cls.DEPLOYMENT_PREFIX, "duration_sum", window)
        duration_count_key = cls._get_metric_key(cls.DEPLOYMENT_PREFIX, "duration_count", window)

        success_count = cache.get(success_key, 0)
        failure_count = cache.get(failure_key, 0)
        rollback_count = cache.get(rollback_key, 0)
        duration_sum = cache.get(duration_sum_key, 0)
        duration_count = cache.get(duration_count_key, 0)

        total = success_count + failure_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        avg_duration = (duration_sum / duration_count) if duration_count > 0 else 0

        return {
            'success_count': success_count,
            'failure_count': failure_count,
            'rollback_count': rollback_count,
            'total_count': total,
            'success_rate_percent': round(success_rate, 2),
            'avg_duration_seconds': round(avg_duration, 2),
            'window': window
        }

    @classmethod
    def get_all_metrics(cls, window: str = "hour") -> Dict[str, Any]:
        """Get all metrics for a time window"""
        return {
            'provisioning': cls.get_provision_metrics(window),
            'deployment': cls.get_deployment_metrics(window),
            'timestamp': timezone.now().isoformat(),
            'window': window
        }

    @classmethod
    def check_alert_thresholds(cls) -> Dict[str, Any]:
        """
        Check if any metrics exceed alert thresholds

        Returns:
            Dict with alert status and details
        """
        alerts = []

        # Check provision failure rate (last hour)
        provision_metrics = cls.get_provision_metrics("hour")
        if provision_metrics['total_count'] > 5 and provision_metrics['success_rate_percent'] < 80:
            alerts.append({
                'severity': 'high',
                'type': 'provision_failure_rate',
                'message': f"Provision success rate is {provision_metrics['success_rate_percent']}% (threshold: 80%)",
                'metric': provision_metrics
            })

        # Check deployment failure rate (last hour)
        deployment_metrics = cls.get_deployment_metrics("hour")
        if deployment_metrics['total_count'] > 5 and deployment_metrics['success_rate_percent'] < 90:
            alerts.append({
                'severity': 'high',
                'type': 'deployment_failure_rate',
                'message': f"Deployment success rate is {deployment_metrics['success_rate_percent']}% (threshold: 90%)",
                'metric': deployment_metrics
            })

        # Check average provision time (should be < 60 seconds)
        if provision_metrics['avg_duration_seconds'] > 60:
            alerts.append({
                'severity': 'medium',
                'type': 'slow_provisioning',
                'message': f"Average provision time is {provision_metrics['avg_duration_seconds']}s (threshold: 60s)",
                'metric': provision_metrics
            })

        # Check rollback rate
        if deployment_metrics['total_count'] > 0:
            rollback_rate = (deployment_metrics['rollback_count'] / deployment_metrics['total_count']) * 100
            if rollback_rate > 10:
                alerts.append({
                    'severity': 'medium',
                    'type': 'high_rollback_rate',
                    'message': f"Deployment rollback rate is {rollback_rate:.2f}% (threshold: 10%)",
                    'metric': deployment_metrics
                })

        return {
            'alert_count': len(alerts),
            'alerts': alerts,
            'checked_at': timezone.now().isoformat()
        }

    @classmethod
    def track_cache_invalidation(
        cls,
        workspace_id: str,
        reason: str,
        duration_ms: int,
        success: bool,
        error: str = None
    ):
        """
        Track cache invalidation metrics

        Args:
            workspace_id: Workspace UUID
            reason: Reason for invalidation (e.g., 'theme_publish', 'theme_edit')
            duration_ms: Time taken for invalidation in milliseconds
            success: Whether invalidation succeeded
            error: Optional error message if failed
        """
        prefix = "metrics:cache_invalidation"

        # Increment success/failure counters
        if success:
            cls._increment_counter(prefix, "success", ["minute", "hour", "day"])
        else:
            cls._increment_counter(prefix, "failure", ["minute", "hour", "day"])

        # Track duration (convert ms to seconds for consistency)
        duration_seconds = duration_ms / 1000.0
        cls._record_duration(prefix, "duration", duration_seconds, ["minute", "hour"])

        # Track by reason (for debugging which operations trigger most invalidations)
        cls._increment_counter(prefix, f"reason_{reason}", ["hour", "day"])

        logger.info(
            f"[Metrics] Cache invalidation {'SUCCESS' if success else 'FAILURE'} "
            f"for workspace {workspace_id} ({reason}) in {duration_ms}ms"
            f"{f' - Error: {error}' if error else ''}"
        )

    @classmethod
    def track_cache_warming(
        cls,
        workspace_id: str,
        total_urls: int,
        warmed: int,
        failed: int
    ):
        """
        Track cache warming metrics

        Args:
            workspace_id: Workspace UUID
            total_urls: Total number of URLs to warm
            warmed: Number of URLs successfully warmed
            failed: Number of URLs that failed to warm
        """
        prefix = "metrics:cache_warming"

        # Track success/failure counts
        if warmed > 0:
            cls._increment_counter(prefix, "urls_warmed", ["hour", "day"])
        if failed > 0:
            cls._increment_counter(prefix, "urls_failed", ["hour", "day"])

        # Track warming operations
        cls._increment_counter(prefix, "operations", ["hour", "day"])

        # Track success rate
        success_rate = (warmed / total_urls * 100) if total_urls > 0 else 0

        logger.info(
            f"[Metrics] Cache warming completed for workspace {workspace_id}: "
            f"{warmed}/{total_urls} URLs warmed ({success_rate:.1f}% success), "
            f"{failed} failed"
        )


def track_metric(operation: str, metric_type: str = 'provision'):
    """
    Decorator to automatically track metrics for operations

    Usage:
        @track_metric('provision_workspace', metric_type='provision')
        def provision_workspace(workspace_id):
            # Implementation
            pass

    Args:
        operation: Name of the operation
        metric_type: Type of metric ('provision' or 'deployment')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            rolled_back = False

            # Extract workspace_id from args/kwargs
            workspace_id = kwargs.get('workspace_id') or (args[0] if args else None)

            try:
                result = func(*args, **kwargs)

                # Determine success from result
                if isinstance(result, dict):
                    success = result.get('success', False)
                    rolled_back = result.get('rolled_back', False)
                else:
                    success = True

                return result

            except Exception as e:
                success = False
                raise

            finally:
                duration = time.time() - start_time

                # Record metric
                try:
                    if metric_type == 'provision':
                        MetricsService.record_provision_attempt(
                            workspace_id=str(workspace_id),
                            success=success,
                            duration_seconds=duration,
                            metadata={'operation': operation}
                        )
                    elif metric_type == 'deployment':
                        MetricsService.record_deployment_attempt(
                            workspace_id=str(workspace_id),
                            success=success,
                            duration_seconds=duration,
                            rolled_back=rolled_back,
                            metadata={'operation': operation}
                        )
                except Exception as metric_error:
                    logger.warning(f"Failed to record metric: {metric_error}")

        return wrapper
    return decorator
