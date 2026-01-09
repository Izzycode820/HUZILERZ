# Logging middleware for GraphQL requests
# IMPORTANT: Structured logging for monitoring and debugging

import logging
import time
import json

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    Log all GraphQL requests/responses

    Observability: Structured logging for monitoring
    Performance: Track query execution time
    """

    def resolve(self, next, root, info, **kwargs):
        start_time = time.time()

        # Extract operation info
        operation_name = info.operation.name.value if info.operation and info.operation.name else 'anonymous'
        field_name = info.field_name

        # Extract tenant context (added for multi-tenant logging)
        tenant_id = getattr(info.context, 'tenant_id', None)
        workspace_slug = getattr(info.context, 'store_slug', None)
        user_id = getattr(info.context.user, 'id', None) if hasattr(info.context, 'user') else None

        # Log request
        logger.info(
            "GraphQL query started",
            extra={
                'operation': operation_name,
                'field': field_name,
                'variables': json.dumps(kwargs, default=str),
                'tenant_id': str(tenant_id) if tenant_id else None,
                'workspace_slug': workspace_slug,
                'user_id': str(user_id) if user_id else None,
                'type': 'request'
            }
        )

        try:
            result = next(root, info, **kwargs)

            # Log successful response
            execution_time = (time.time() - start_time) * 1000
            logger.info(
                "GraphQL query completed",
                extra={
                    'operation': operation_name,
                    'field': field_name,
                    'execution_time_ms': execution_time,
                    'tenant_id': str(tenant_id) if tenant_id else None,
                    'workspace_slug': workspace_slug,
                    'user_id': str(user_id) if user_id else None,
                    'success': True,
                    'type': 'response'
                }
            )

            # Alert if slow query (> 200ms)
            if execution_time > 200:
                logger.warning(
                    "Slow query detected",
                    extra={
                        'operation': operation_name,
                        'field': field_name,
                        'execution_time_ms': execution_time,
                        'tenant_id': str(tenant_id) if tenant_id else None,
                        'workspace_slug': workspace_slug,
                        'type': 'slow_query'
                    }
                )

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                "GraphQL query failed",
                extra={
                    'operation': operation_name,
                    'field': field_name,
                    'execution_time_ms': execution_time,
                    'tenant_id': str(tenant_id) if tenant_id else None,
                    'workspace_slug': workspace_slug,
                    'user_id': str(user_id) if user_id else None,
                    'error': str(e),
                    'success': False,
                    'type': 'error'
                }
            )
            raise


class PerformanceMiddleware:
    """
    Performance monitoring middleware

    Tracks query performance metrics
    """

    def resolve(self, next, root, info, **kwargs):
        start_time = time.time()

        try:
            result = next(root, info, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            # Track performance metrics
            if hasattr(info.context, 'performance_metrics'):
                info.context.performance_metrics.append({
                    'operation': info.operation.name.value if info.operation and info.operation.name else 'anonymous',
                    'field': info.field_name,
                    'execution_time_ms': execution_time
                })

            return result

        except Exception:
            execution_time = (time.time() - start_time) * 1000
            # Log error performance
            if hasattr(info.context, 'performance_metrics'):
                info.context.performance_metrics.append({
                    'operation': info.operation.name.value if info.operation and info.operation.name else 'anonymous',
                    'field': info.field_name,
                    'execution_time_ms': execution_time,
                    'error': True
                })
            raise