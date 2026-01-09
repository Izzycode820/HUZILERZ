"""
Standardized response utilities for consistent API responses
Industry Standard: Consistent response format across all endpoints
"""
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    """
    Standard success response format

    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code

    Returns:
        Response object with standardized format
    """
    response_data = {
        "success": True,
        "message": message,
        "data": data or {}
    }

    logger.info(f"Success response: {message}")
    return Response(response_data, status=status_code)


def error_response(
    error_code="INTERNAL_SERVER_ERROR",
    message="An error occurred",
    details=None,
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
):
    """
    Standard error response format

    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code

    Returns:
        Response object with standardized error format
    """
    error_data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or message
        }
    }

    logger.warning(f"Error response - Code: {error_code}, Message: {message}")
    return Response(error_data, status=status_code)


def validation_error_response(errors, message="Validation failed"):
    """
    Standard validation error response

    Args:
        errors: Validation errors
        message: Error message

    Returns:
        Response object with validation error format
    """
    return error_response(
        error_code="VALIDATION_ERROR",
        message=message,
        details=errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


def not_found_response(resource_name, resource_id=None):
    """
    Standard not found response

    Args:
        resource_name: Name of the resource
        resource_id: ID of the resource

    Returns:
        Response object with not found format
    """
    message = f"{resource_name} not found"
    if resource_id:
        message = f"{resource_name} with ID {resource_id} not found"

    return error_response(
        error_code="NOT_FOUND",
        message=message,
        status_code=status.HTTP_404_NOT_FOUND
    )


def unauthorized_response(message="Authentication required"):
    """
    Standard unauthorized response

    Args:
        message: Error message

    Returns:
        Response object with unauthorized format
    """
    return error_response(
        error_code="UNAUTHORIZED",
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED
    )


def forbidden_response(message="Access forbidden"):
    """
    Standard forbidden response

    Args:
        message: Error message

    Returns:
        Response object with forbidden format
    """
    return error_response(
        error_code="FORBIDDEN",
        message=message,
        status_code=status.HTTP_403_FORBIDDEN
    )