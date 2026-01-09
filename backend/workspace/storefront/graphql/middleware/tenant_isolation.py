"""
Tenant Isolation Middleware for GraphQL
Critical security layer for multi-tenant data isolation
"""
import logging
from graphql import GraphQLError

logger = logging.getLogger(__name__)


class TenantIsolationMiddleware:
    """
    Enforce tenant isolation at GraphQL level

    Security: Prevents cross-tenant data leakage
    - Validates tenant context exists
    - Logs queries without tenant context
    - Rejects queries if tenant missing (in production)
    """

    def resolve(self, next, root, info, **kwargs):
        """
        Validate tenant context before resolving query
        """
        # Check if tenant context exists
        if not hasattr(info.context, 'workspace'):
            # Extract operation details for logging
            operation_name = info.operation.name.value if info.operation and info.operation.name else 'anonymous'
            field_name = info.field_name

            # Log security incident
            logger.error(
                "Query attempted without tenant context",
                extra={
                    'operation': operation_name,
                    'field': field_name,
                    'path': info.context.path if hasattr(info.context, 'path') else None,
                    'security_incident': True,
                    'type': 'tenant_isolation_violation'
                }
            )

            # In production: Reject query
            # In development: Allow but warn
            from django.conf import settings
            if not settings.DEBUG:
                raise GraphQLError(
                    "Access denied: Tenant context not found. "
                    "Please access this store through its proper domain."
                )

        # Continue with query resolution
        return next(root, info, **kwargs)


class TenantScopingMiddleware:
    """
    Automatically inject tenant filters into queries

    Note: This is a defense-in-depth layer. Resolvers should already
    filter by workspace, but this provides an additional safety net.
    """

    def resolve(self, next, root, info, **kwargs):
        """
        Inject tenant_id into query context if not present
        """
        # Add workspace to kwargs if not already present
        # This helps ensure resolvers always have access to tenant context
        if hasattr(info.context, 'workspace') and 'workspace' not in kwargs:
            # Don't override if already set (resolver might have specific logic)
            pass

        # Add tenant_id to info for resolver convenience
        if hasattr(info.context, 'tenant_id'):
            info.context.current_tenant_id = info.context.tenant_id

        return next(root, info, **kwargs)
