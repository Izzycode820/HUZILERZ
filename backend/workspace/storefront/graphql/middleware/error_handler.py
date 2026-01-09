# Error handling middleware for GraphQL
# IMPORTANT: Centralized error handling and sanitization

import logging
from graphql import GraphQLError

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware:
    """
    Centralized error handling middleware

    Security: Sanitizes error messages for production
    Observability: Structured error logging
    """

    def resolve(self, next, root, info, **kwargs):
        try:
            return next(root, info, **kwargs)

        except Exception as e:
            # Extract tenant context for security audit
            tenant_id = getattr(info.context, 'tenant_id', None)
            workspace_slug = getattr(info.context, 'store_slug', None)
            user_id = getattr(info.context.user, 'id', None) if hasattr(info.context, 'user') else None

            # Log the original error with tenant context
            logger.error(
                "GraphQL error occurred",
                extra={
                    'operation': info.operation.name.value if info.operation and info.operation.name else 'anonymous',
                    'field': info.field_name,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'variables': kwargs,
                    'tenant_id': str(tenant_id) if tenant_id else None,
                    'workspace_slug': workspace_slug,
                    'user_id': str(user_id) if user_id else None,
                }
            )

            # Sanitize error for production
            sanitized_error = self._sanitize_error(e)
            raise sanitized_error

    def _sanitize_error(self, error):
        """
        Sanitize error messages for production

        Security: Hide sensitive information
        User Experience: Provide helpful error messages
        """
        # GraphQLError instances already have user-friendly messages - pass through as-is
        if isinstance(error, GraphQLError):
            return error

        error_type = type(error).__name__

        # Database errors (Django ORM exceptions)
        if 'database' in str(error).lower() or 'sql' in str(error).lower():
            return GraphQLError("Database error occurred. Please try again.")

        # Authentication errors
        if 'permission' in str(error).lower() or 'auth' in str(error).lower():
            return GraphQLError("Access denied.")

        # Validation errors
        if 'validation' in str(error).lower() or 'invalid' in str(error).lower():
            return GraphQLError(str(error))

        # Business logic errors (keep as-is)
        if isinstance(error, ValueError):
            return GraphQLError(str(error))

        # Unknown errors (non-GraphQL exceptions)
        return GraphQLError("An unexpected error occurred. Please try again.")


class ValidationMiddleware:
    """
    Input validation middleware

    Security: Validates mutation inputs
    Note: Django ORM already protects against SQL injection.
    This provides additional defense-in-depth validation.
    """

    def resolve(self, next, root, info, **kwargs):
        # Validate mutation inputs
        if info.operation and info.operation.operation == 'mutation':
            self._validate_mutation_inputs(info, kwargs)

        return next(root, info, **kwargs)

    def _validate_mutation_inputs(self, info, kwargs):
        """
        Validate mutation inputs

        Security: Basic input validation (Django ORM handles SQL injection)
        """
        for key, value in kwargs.items():
            # Validate string inputs (length, characters)
            if isinstance(value, str):
                # Check for excessively long strings
                if len(value) > 10000:
                    raise GraphQLError(f"Input too long in field: {key}")

                # Check for null bytes (can cause issues)
                if '\x00' in value:
                    raise GraphQLError(f"Invalid characters in field: {key}")

            # Validate numeric inputs (prevent overflow)
            if isinstance(value, (int, float)):
                if not self._is_valid_number(value):
                    raise GraphQLError(f"Numeric value out of range in field: {key}")

            # Validate lists (prevent DoS via large arrays)
            if isinstance(value, list):
                if len(value) > 1000:
                    raise GraphQLError(f"Too many items in field: {key}")

    def _is_valid_number(self, value):
        """
        Validate numeric inputs (prevent integer overflow)
        """
        # Check for reasonable bounds
        if isinstance(value, int):
            # Django IntegerField max: 2147483647
            return -2147483648 <= value <= 2147483647
        elif isinstance(value, float):
            return -1e308 <= value <= 1e308
        return True