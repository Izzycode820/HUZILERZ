"""
Logging Middleware for GraphQL API

Provides structured logging for GraphQL requests
Critical for monitoring, debugging, and security
"""

import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    Log GraphQL requests and responses

    Monitoring: Track query performance and errors
    Security: Log authentication and authorization events
    Debugging: Provide detailed request/response information
    """

    def resolve(self, next, root, info, **kwargs):
        start_time = datetime.now()
        request = info.context

        # Log request details
        log_data = {
            'timestamp': start_time.isoformat(),
            'operation_name': info.operation.name if info.operation else 'anonymous',
            'field_name': info.field_name,
            'user_id': getattr(request, 'user_id', None),
            'workspace_id': str(getattr(request.workspace, 'id', None)) if hasattr(request, 'workspace') else None,
            'workspace_slug': getattr(request.workspace, 'slug', None) if hasattr(request, 'workspace') else None,  # Added for consistency
            'workspace_type': getattr(request.workspace, 'type', None) if hasattr(request, 'workspace') else None,  # Added to track store/service/etc
            'query': info.query,
            'variables': info.variable_values,
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT')
        }

        try:
            # Execute the resolver
            result = next(root, info, **kwargs)

            # Log successful response
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            log_data.update({
                'status': 'success',
                'duration_ms': round(duration_ms, 2),
                'response_time': end_time.isoformat()
            })

            logger.info("GraphQL request completed", extra=log_data)

            return result

        except Exception as e:
            # Log error
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            log_data.update({
                'status': 'error',
                'error_type': type(e).__name__,
                'error_message': str(e),
                'duration_ms': round(duration_ms, 2),
                'response_time': end_time.isoformat()
            })

            logger.error("GraphQL request failed", extra=log_data)

            # Re-raise the exception
            raise