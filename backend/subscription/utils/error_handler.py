"""
Production-safe error handling utilities
Prevents information disclosure while maintaining logging
"""
import logging
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class ProductionSafeErrorHandler:
    """
    Handle errors safely for production environments
    Logs detailed errors server-side, returns generic messages to users
    """
    
    @staticmethod
    def handle_view_error(error: Exception, context: str = None, user_id: int = None) -> Response:
        """
        Handle view-level errors with production-safe responses
        
        Args:
            error: The exception that occurred
            context: Description of what operation failed
            user_id: User ID for logging context
            
        Returns:
            Response with appropriate error message
        """
        # Log detailed error server-side
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'user_id': user_id
        }
        
        logger.error(f"View error in {context}: {str(error)}", extra=error_details)
        
        # Return production-safe response
        if settings.DEBUG:
            # Development: return detailed error
            return Response({
                'error': 'Internal server error',
                'debug_info': {
                    'error_type': type(error).__name__,
                    'message': str(error),
                    'context': context
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Production: generic error message
            return Response({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred. Please try again later.',
                'support': 'If this issue persists, please contact support.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_payment_error(error: Exception, payment_id: str = None, user_id: int = None) -> dict:
        """
        Handle payment-related errors safely
        
        Returns:
            Dictionary with error information
        """
        # Log detailed error
        error_context = {
            'payment_id': payment_id,
            'user_id': user_id,
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
        
        logger.error(f"Payment processing error: {str(error)}", extra=error_context)
        
        # Return safe error response
        if settings.DEBUG:
            return {
                'success': False,
                'error': 'Payment processing failed',
                'error_code': 'payment_error',
                'debug_info': str(error)
            }
        else:
            return {
                'success': False,
                'error': 'Payment processing failed',
                'error_code': 'payment_error',
                'message': 'Unable to process payment at this time. Please try again.'
            }
    
    @staticmethod
    def handle_subscription_error(error: Exception, user_id: int = None) -> dict:
        """
        Handle subscription operation errors safely
        """
        # Log detailed error
        logger.error(f"Subscription operation error: {str(error)}", extra={
            'user_id': user_id,
            'error_type': type(error).__name__,
            'error_message': str(error)
        })
        
        # Return safe response
        if settings.DEBUG:
            return {
                'success': False,
                'error': 'Subscription operation failed',
                'debug_detail': str(error)
            }
        else:
            return {
                'success': False,
                'error': 'Subscription operation failed',
                'message': 'Unable to complete subscription operation. Please try again.'
            }
    
    @staticmethod
    def safe_error_response(
        error: Exception, 
        operation: str, 
        user_friendly_message: str = None
    ) -> Response:
        """
        Generic safe error response for any operation
        
        Args:
            error: The exception
            operation: Description of failed operation
            user_friendly_message: Custom user message
            
        Returns:
            Production-safe Response
        """
        # Log the actual error
        logger.error(f"Error in {operation}: {str(error)}", extra={
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error)
        })
        
        # Determine user message
        message = user_friendly_message or f"Failed to {operation.lower()}. Please try again."
        
        if settings.DEBUG:
            return Response({
                'error': f"Failed to {operation}",
                'message': message,
                'debug_error': str(error),
                'error_type': type(error).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'error': f"Failed to {operation}",
                'message': message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)