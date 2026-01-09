"""
Cache Invalidation Tasks - CDN & Local Cache Management
Background tasks for invalidating and warming cache after theme changes

Security & Performance:
- Debounced invalidation (30s window) to prevent cache stampede
- Redis locks prevent duplicate invalidations
- Only invalidates active (published) themes
- Async execution to avoid blocking user requests
- Automatic retry on failure with exponential backoff
"""
import logging
import hashlib
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


@shared_task(
    name='workspace_hosting.invalidate_workspace_cache',
    bind=True,
    acks_late=True,
    max_retries=3,
    time_limit=60,
    soft_time_limit=50,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=30,
    retry_jitter=True
)
def invalidate_workspace_cache_async(self, workspace_id: str, reason: str = "manual") -> Dict[str, Any]:
    """
    Async cache invalidation with deduplication and debouncing

    Uses Redis lock to prevent duplicate invalidations within 30s window.
    This prevents cache stampede when users rapidly save theme edits.

    Args:
        workspace_id: UUID of workspace to invalidate cache for
        reason: Human-readable reason for invalidation (logging/debugging)

    Returns:
        dict: Invalidation result with status and metrics

    Raises:
        Exception: Retries on failure (max 3 times with exponential backoff)

    Examples:
        >>> # Queue invalidation with 5s delay (debounce rapid edits)
        >>> invalidate_workspace_cache_async.apply_async(
        ...     args=["ws-123", "theme_edit"],
        ...     countdown=5
        ... )
    """
    from workspace.hosting.services.cdn_cache_service import CDNCacheService
    from workspace.hosting.services.cache_service import WorkspaceCacheService
    from workspace.hosting.services.metrics_service import MetricsService

    # Generate lock key for deduplication
    lock_key = f"cache_invalidation_lock:ws:{workspace_id}"

    # Try to acquire lock (30s TTL = debounce window)
    # This ensures we only invalidate once per 30s even if multiple saves happen
    lock_acquired = cache.add(lock_key, "locked", timeout=30)

    if not lock_acquired:
        logger.info(
            f"[Cache Invalidation] Skipping duplicate invalidation for workspace {workspace_id} "
            f"(reason: {reason}, debounced within 30s window)"
        )
        return {
            "success": True,
            "skipped": True,
            "reason": "debounced",
            "workspace_id": workspace_id
        }

    try:
        logger.info(
            f"[Cache Invalidation] Starting for workspace {workspace_id} "
            f"(reason: {reason})"
        )

        # Track start time for metrics
        import time
        start_time = time.time()

        # Step 1: Invalidate CDN cache (CloudFront/shared pool)
        cdn_result = CDNCacheService.invalidate_workspace_cache(workspace_id)

        if cdn_result.get('success') is False:
            logger.warning(
                f"[Cache Invalidation] CDN invalidation failed for workspace {workspace_id}: "
                f"{cdn_result.get('error')}"
            )
            # Continue anyway - local cache invalidation is still valuable

        # Step 2: Invalidate local cache (Redis/in-memory)
        try:
            WorkspaceCacheService.clear_workspace_cache(workspace_id)
            logger.info(f"[Cache Invalidation] Local cache cleared for workspace {workspace_id}")
        except Exception as local_cache_error:
            logger.warning(
                f"[Cache Invalidation] Local cache invalidation failed (non-critical): "
                f"{local_cache_error}"
            )

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Track metrics
        try:
            MetricsService.track_cache_invalidation(
                workspace_id=workspace_id,
                reason=reason,
                duration_ms=duration_ms,
                success=True
            )
        except Exception as metrics_error:
            # Metrics failure is non-critical
            logger.debug(f"Metrics tracking failed (non-critical): {metrics_error}")

        logger.info(
            f"[Cache Invalidation] Completed for workspace {workspace_id} "
            f"in {duration_ms}ms (reason: {reason})"
        )

        return {
            "success": True,
            "skipped": False,
            "workspace_id": workspace_id,
            "reason": reason,
            "duration_ms": duration_ms,
            "cdn_invalidated": cdn_result.get('success', False),
            "local_cache_invalidated": True
        }

    except Exception as e:
        logger.error(
            f"[Cache Invalidation] Failed for workspace {workspace_id}: {str(e)}",
            exc_info=True
        )

        # Track failure in metrics
        try:
            MetricsService.track_cache_invalidation(
                workspace_id=workspace_id,
                reason=reason,
                duration_ms=0,
                success=False,
                error=str(e)
            )
        except:
            pass

        # Release lock on failure to allow retry
        cache.delete(lock_key)

        # Retry with exponential backoff (Celery handles this automatically)
        raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 5, 60))


@shared_task(
    name='workspace_hosting.warm_cache',
    bind=True,
    acks_late=True,
    max_retries=2,
    time_limit=120,
    soft_time_limit=110
)
def warm_cache_async(self, workspace_id: str, urls: List[str]) -> Dict[str, Any]:
    """
    Pre-warm CDN cache by fetching critical URLs

    Called after cache invalidation to prevent cache stampede.
    Fetches homepage, product listings, etc. to populate CDN edge cache.

    Args:
        workspace_id: UUID of workspace
        urls: List of full URLs to warm (e.g., ["https://store.huzilerz.com/"])

    Returns:
        dict: Warming result with success/failure counts

    Examples:
        >>> # Queue cache warming 2s after invalidation
        >>> warm_cache_async.apply_async(
        ...     args=["ws-123", ["https://store.huzilerz.com/", "https://store.huzilerz.com/products"]],
        ...     countdown=2
        ... )
    """
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed

    logger.info(
        f"[Cache Warming] Starting for workspace {workspace_id} "
        f"({len(urls)} URLs)"
    )

    results = {
        "success": True,
        "workspace_id": workspace_id,
        "total_urls": len(urls),
        "warmed": 0,
        "failed": 0,
        "errors": []
    }

    def fetch_url(url: str) -> Dict[str, Any]:
        """Fetch single URL with timeout and error handling"""
        try:
            response = requests.get(
                url,
                timeout=10,
                headers={
                    'User-Agent': 'Huzilerz-CacheWarmer/1.0',
                    'X-Cache-Warm': 'true'
                }
            )
            response.raise_for_status()

            logger.info(f"[Cache Warming] Warmed: {url} (status: {response.status_code})")
            return {"url": url, "success": True, "status": response.status_code}

        except requests.exceptions.Timeout:
            logger.warning(f"[Cache Warming] Timeout warming {url}")
            return {"url": url, "success": False, "error": "timeout"}

        except requests.exceptions.RequestException as e:
            logger.warning(f"[Cache Warming] Failed warming {url}: {str(e)}")
            return {"url": url, "success": False, "error": str(e)}

    # Warm cache in parallel (max 5 concurrent requests)
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all URLs
        future_to_url = {executor.submit(fetch_url, url): url for url in urls}

        # Collect results as they complete
        for future in as_completed(future_to_url):
            result = future.result()

            if result["success"]:
                results["warmed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "url": result["url"],
                    "error": result.get("error", "unknown")
                })

    # Log summary
    logger.info(
        f"[Cache Warming] Completed for workspace {workspace_id}: "
        f"{results['warmed']}/{results['total_urls']} warmed, "
        f"{results['failed']} failed"
    )

    # Track metrics
    try:
        from workspace.hosting.services.metrics_service import MetricsService
        MetricsService.track_cache_warming(
            workspace_id=workspace_id,
            total_urls=results["total_urls"],
            warmed=results["warmed"],
            failed=results["failed"]
        )
    except Exception as metrics_error:
        logger.debug(f"Metrics tracking failed (non-critical): {metrics_error}")

    return results


@shared_task(
    name='workspace_hosting.invalidate_on_content_change',
    bind=True,
    acks_late=True,
    max_retries=3,
    time_limit=60
)
def invalidate_on_content_change(self, workspace_id: str, content_type: str, content_id: str = None) -> Dict[str, Any]:
    """
    Invalidate cache when workspace content changes

    Triggered by signals when products, collections, or pages are modified.
    Only invalidates if workspace has an active (published) theme.

    Args:
        workspace_id: UUID of workspace
        content_type: Type of content changed ('product', 'collection', 'page')
        content_id: Optional ID of specific content item

    Returns:
        dict: Invalidation result

    Security:
        - Only invalidates active themes (draft changes don't affect live site)
        - Authenticated via signal sender (trusted internal call)

    Examples:
        >>> # Product updated - invalidate product pages
        >>> invalidate_on_content_change.delay("ws-123", "product", "prod-456")
    """
    from workspace.core.models import Workspace
    from theme.models import TemplateCustomization

    try:
        # Check if workspace has active theme (published)
        workspace = Workspace.objects.get(id=workspace_id)
        active_theme = TemplateCustomization.objects.filter(
            workspace=workspace,
            is_active=True
        ).first()

        if not active_theme:
            logger.info(
                f"[Cache Invalidation] Skipping for workspace {workspace_id} - "
                f"no active theme (content change won't affect live site)"
            )
            return {
                "success": True,
                "skipped": True,
                "reason": "no_active_theme"
            }

        # Queue invalidation with debouncing
        reason = f"{content_type}_change"
        if content_id:
            reason = f"{content_type}_{content_id}_change"

        # Delegate to main invalidation task with 5s debounce
        # NOTE: Fire-and-forget pattern - never call .get() inside a task (causes deadlock)
        task = invalidate_workspace_cache_async.apply_async(
            args=[workspace_id, reason],
            countdown=5  # 5s delay to debounce rapid content changes
        )
        
        return {
            "success": True,
            "queued": True,
            "task_id": task.id,
            "reason": reason
        }

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found for content invalidation")
        return {"success": False, "error": "workspace_not_found"}

    except Exception as e:
        logger.error(f"Content change invalidation failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=10)


# Export all tasks
__all__ = [
    'invalidate_workspace_cache_async',
    'warm_cache_async',
    'invalidate_on_content_change',
]
