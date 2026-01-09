"""
Idempotency Service for Infrastructure Operations

Production-ready distributed locking and idempotency using Redis SET NX pattern.
Based on Redis official best practices and 2025 production patterns.

References:
- https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/
- https://www.vintasoftware.com/blog/celery-wild-tips-and-tricks-run-async-tasks-real-world
"""
import hashlib
import json
import logging
import uuid
import time
import random
from typing import Any, Dict, Optional, Callable
from functools import wraps
from django.core.cache import cache
from django.utils import timezone
from redis import Redis
from django.conf import settings

logger = logging.getLogger(__name__)


class IdempotencyService:
    """
    Production-grade service for ensuring idempotent infrastructure operations

    Features:
    - Distributed locking using Redis SET NX EX pattern
    - Unique lock tokens (UUID) for safe release
    - Lua script for atomic lock release
    - Result caching with TTL
    - Lock renewal for long-running tasks
    - Exponential backoff with jitter
    """

    # Lock timeouts: 2-3x expected execution time
    LOCK_TIMEOUT = 900  # 15 minutes for infrastructure tasks
    RESULT_TTL = 86400  # 24 hours

    # Retry configuration
    MAX_RETRIES = 5
    BASE_RETRY_DELAY = 0.1  # 100ms
    MAX_RETRY_DELAY = 5.0  # 5 seconds

    # Lua script for safe lock release (atomic)
    RELEASE_LOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    @staticmethod
    def _get_redis_client() -> Redis:
        """Get Redis client from cache backend"""
        from django_redis import get_redis_connection
        return get_redis_connection("default")

    @staticmethod
    def generate_idempotency_key(operation: str, resource_id: str, **kwargs) -> str:
        """
        Generate a unique idempotency key for an operation

        Args:
            operation: Name of the operation (e.g., 'provision_workspace')
            resource_id: ID of the resource being operated on
            **kwargs: Additional parameters to include in the key

        Returns:
            str: Idempotency key
        """
        # Filter only JSON-serializable parameters
        serializable_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, (str, int, float, bool, type(None), list, dict)):
                serializable_kwargs[k] = v
            else:
                # Use type name for non-serializable objects
                serializable_kwargs[k] = f"<{type(v).__name__}>"

        # Sort kwargs for consistency
        sorted_params = json.dumps(serializable_kwargs, sort_keys=True) if serializable_kwargs else ''

        # Create hash of parameters
        param_hash = hashlib.sha256(sorted_params.encode()).hexdigest()[:16]

        return f"idempotency:{operation}:{resource_id}:{param_hash}"

    @staticmethod
    def acquire_lock(idempotency_key: str, timeout: Optional[int] = None) -> Optional[str]:
        """
        Acquire a distributed lock using Redis SET NX EX pattern

        Args:
            idempotency_key: The idempotency key
            timeout: Lock timeout in seconds (default: LOCK_TIMEOUT)

        Returns:
            Optional[str]: Lock token (UUID) if acquired, None otherwise
        """
        timeout = timeout or IdempotencyService.LOCK_TIMEOUT
        lock_key = f"{idempotency_key}:lock"
        lock_token = str(uuid.uuid4())  # Unique token for safe release

        try:
            redis_client = IdempotencyService._get_redis_client()

            # SET key value NX EX timeout (atomic operation)
            acquired = redis_client.set(
                lock_key,
                lock_token,
                nx=True,  # Only set if not exists
                ex=timeout  # Expiration in seconds
            )

            if acquired:
                logger.debug(f"[Lock] Acquired lock for {idempotency_key} with token {lock_token[:8]}...")
                return lock_token
            else:
                logger.warning(f"[Lock] Failed to acquire lock for {idempotency_key} (already locked)")
                return None

        except Exception as e:
            logger.error(f"[Lock] Error acquiring lock for {idempotency_key}: {e}")
            return None

    @staticmethod
    def release_lock(idempotency_key: str, lock_token: str) -> bool:
        """
        Release a distributed lock using Lua script for atomic check-and-delete

        Args:
            idempotency_key: The idempotency key
            lock_token: The lock token received when acquiring

        Returns:
            bool: True if lock was released, False otherwise
        """
        lock_key = f"{idempotency_key}:lock"

        try:
            redis_client = IdempotencyService._get_redis_client()

            # Use Lua script for atomic release
            result = redis_client.eval(
                IdempotencyService.RELEASE_LOCK_SCRIPT,
                1,  # Number of keys
                lock_key,
                lock_token
            )

            if result == 1:
                logger.debug(f"[Lock] Released lock for {idempotency_key}")
                return True
            else:
                logger.warning(f"[Lock] Failed to release lock for {idempotency_key} (token mismatch or expired)")
                return False

        except Exception as e:
            logger.error(f"[Lock] Error releasing lock for {idempotency_key}: {e}")
            return False

    @staticmethod
    def renew_lock(idempotency_key: str, lock_token: str, timeout: Optional[int] = None) -> bool:
        """
        Renew/extend a lock for long-running operations

        Args:
            idempotency_key: The idempotency key
            lock_token: The lock token received when acquiring
            timeout: New timeout in seconds

        Returns:
            bool: True if renewed, False otherwise
        """
        timeout = timeout or IdempotencyService.LOCK_TIMEOUT
        lock_key = f"{idempotency_key}:lock"

        try:
            redis_client = IdempotencyService._get_redis_client()

            # Check if we still own the lock, then extend
            current_value = redis_client.get(lock_key)
            if current_value and current_value.decode() == lock_token:
                redis_client.expire(lock_key, timeout)
                logger.debug(f"[Lock] Renewed lock for {idempotency_key}")
                return True
            else:
                logger.warning(f"[Lock] Cannot renew lock for {idempotency_key} (not owned)")
                return False

        except Exception as e:
            logger.error(f"[Lock] Error renewing lock for {idempotency_key}: {e}")
            return False

    @staticmethod
    def get_cached_result(idempotency_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a previous successful execution

        Args:
            idempotency_key: The idempotency key

        Returns:
            Optional[Dict]: Cached result if exists, None otherwise
        """
        result_key = f"{idempotency_key}:result"

        try:
            cached = cache.get(result_key)

            if cached:
                logger.info(f"[Cache] Returning cached result for {idempotency_key}")
                cached['from_cache'] = True

            return cached

        except Exception as e:
            logger.error(f"[Cache] Error retrieving cached result for {idempotency_key}: {e}")
            return None

    @staticmethod
    def cache_result(idempotency_key: str, result: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache the result of a successful operation

        Only caches if result indicates success (no 'success': False or 'error' key)

        Args:
            idempotency_key: The idempotency key
            result: Result to cache
            ttl: Time to live in seconds (default: RESULT_TTL)
        """
        # Only cache successful results
        if result.get('success') is False or 'error' in result:
            logger.debug(f"[Cache] Skipping cache for failed operation {idempotency_key}")
            return

        ttl = ttl or IdempotencyService.RESULT_TTL
        result_key = f"{idempotency_key}:result"

        try:
            # Add timestamp to result
            result['cached_at'] = timezone.now().isoformat()

            cache.set(result_key, result, timeout=ttl)
            logger.debug(f"[Cache] Cached successful result for {idempotency_key} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"[Cache] Error caching result for {idempotency_key}: {e}")

    @staticmethod
    def clear_cache(idempotency_key: str):
        """
        Clear cached result and lock

        Args:
            idempotency_key: The idempotency key
        """
        result_key = f"{idempotency_key}:result"
        lock_key = f"{idempotency_key}:lock"

        try:
            cache.delete(result_key)
            redis_client = IdempotencyService._get_redis_client()
            redis_client.delete(lock_key)
            logger.debug(f"[Cache] Cleared cache for {idempotency_key}")

        except Exception as e:
            logger.error(f"[Cache] Error clearing cache for {idempotency_key}: {e}")

    @staticmethod
    def _retry_with_backoff(idempotency_key: str, max_retries: Optional[int] = None) -> Optional[str]:
        """
        Retry lock acquisition with exponential backoff and jitter

        Args:
            idempotency_key: The idempotency key
            max_retries: Maximum retry attempts

        Returns:
            Optional[str]: Lock token if acquired, None otherwise
        """
        max_retries = max_retries or IdempotencyService.MAX_RETRIES

        for attempt in range(max_retries):
            lock_token = IdempotencyService.acquire_lock(idempotency_key)

            if lock_token:
                return lock_token

            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = min(
                    IdempotencyService.BASE_RETRY_DELAY * (2 ** attempt),
                    IdempotencyService.MAX_RETRY_DELAY
                )
                jitter = random.uniform(0, delay * 0.1)  # 10% jitter
                sleep_time = delay + jitter

                logger.debug(f"[Lock] Retry {attempt + 1}/{max_retries} for {idempotency_key} after {sleep_time:.2f}s")
                time.sleep(sleep_time)

        logger.warning(f"[Lock] Failed to acquire lock for {idempotency_key} after {max_retries} attempts")
        return None


def idempotent_task(operation: str, resource_id_param: str = 'resource_id', ttl: Optional[int] = None):
    """
    Decorator for making Celery tasks idempotent with distributed locking

    Usage:
        @shared_task
        @idempotent_task(operation='provision_workspace', resource_id_param='workspace_id')
        def provision_workspace(workspace_id, **kwargs):
            # Task implementation
            pass

    Args:
        operation: Name of the operation
        resource_id_param: Name of the parameter containing the resource ID
        ttl: Result cache TTL in seconds

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract resource_id from args or kwargs
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            resource_id = bound_args.arguments.get(resource_id_param)

            if not resource_id:
                logger.warning(f"No {resource_id_param} found in {func.__name__}, skipping idempotency")
                return func(*args, **kwargs)

            # Generate idempotency key with only serializable params
            serializable_params = {}
            for k, v in bound_args.arguments.items():
                if k != resource_id_param:
                    if isinstance(v, (str, int, float, bool, type(None), list, dict)):
                        serializable_params[k] = v
                    else:
                        serializable_params[k] = f"<{type(v).__name__}>"

            idempotency_key = IdempotencyService.generate_idempotency_key(
                operation=operation,
                resource_id=str(resource_id),
                **serializable_params
            )

            logger.info(f"[Idempotency] Checking for {operation} on {resource_id}")

            # Check for cached result first
            cached_result = IdempotencyService.get_cached_result(idempotency_key)
            if cached_result:
                logger.info(f"[Idempotency] Returning cached result for {operation} on {resource_id}")
                return cached_result

            # Try to acquire lock with retry and backoff
            lock_token = IdempotencyService._retry_with_backoff(idempotency_key)

            if not lock_token:
                # Could not acquire lock after retries
                # Check again for cached result (might have completed while we waited)
                cached_result = IdempotencyService.get_cached_result(idempotency_key)
                if cached_result:
                    return cached_result

                logger.warning(f"[Idempotency] Operation {operation} on {resource_id} is locked, returning conflict")
                return {
                    'success': False,
                    'error': 'Operation already in progress or could not acquire lock',
                    'idempotency_conflict': True
                }

            try:
                # Execute the actual function
                logger.info(f"[Idempotency] Executing {operation} on {resource_id}")
                result = func(*args, **kwargs)

                # Cache successful result only
                if isinstance(result, dict):
                    IdempotencyService.cache_result(idempotency_key, result, ttl=ttl)

                return result

            except Exception as e:
                logger.error(f"[Idempotency] Error executing {operation} on {resource_id}: {e}")
                raise

            finally:
                # Always release lock with token verification
                IdempotencyService.release_lock(idempotency_key, lock_token)

        return wrapper
    return decorator


class IdempotencyManager:
    """
    Context manager for manual idempotency control with distributed locking

    Usage:
        with IdempotencyManager('provision_workspace', workspace_id) as manager:
            if manager.should_execute():
                # Perform operation
                result = do_work()
                manager.cache_result(result)

                # For long operations, renew lock periodically
                manager.renew_lock()
    """

    def __init__(self, operation: str, resource_id: str, **kwargs):
        self.operation = operation
        self.resource_id = resource_id
        self.kwargs = kwargs
        self.idempotency_key = IdempotencyService.generate_idempotency_key(
            operation, resource_id, **kwargs
        )
        self._lock_token = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._lock_token:
            IdempotencyService.release_lock(self.idempotency_key, self._lock_token)

    def get_cached_result(self) -> Optional[Dict[str, Any]]:
        """Get cached result if exists"""
        return IdempotencyService.get_cached_result(self.idempotency_key)

    def should_execute(self) -> bool:
        """
        Check if operation should be executed

        Returns:
            bool: True if should execute, False if cached or locked
        """
        # Check cache first
        if IdempotencyService.get_cached_result(self.idempotency_key):
            logger.info(f"[Idempotency] Found cached result for {self.operation}:{self.resource_id}")
            return False

        # Try to acquire lock with retry
        self._lock_token = IdempotencyService._retry_with_backoff(self.idempotency_key)

        if not self._lock_token:
            logger.warning(f"[Idempotency] Failed to acquire lock for {self.operation}:{self.resource_id}")
            return False

        return True

    def renew_lock(self, timeout: Optional[int] = None) -> bool:
        """Renew lock for long-running operations"""
        if not self._lock_token:
            return False
        return IdempotencyService.renew_lock(self.idempotency_key, self._lock_token, timeout)

    def cache_result(self, result: Dict[str, Any], ttl: Optional[int] = None):
        """Cache operation result"""
        IdempotencyService.cache_result(self.idempotency_key, result, ttl=ttl)

    def clear_cache(self):
        """Clear cached result"""
        IdempotencyService.clear_cache(self.idempotency_key)
