"""
Enterprise Email Authentication Views - 2025 Security Standards
Handles email OTP verification, password reset, and email-based authentication
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ..services import EmailService, SecurityService
from ..serializers.email_serializers import (
    EmailVerificationRequestSerializer, EmailVerificationConfirmSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    EmailChangeRequestSerializer, EmailChangeConfirmSerializer
)
from ..models import EmailVerificationCode
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_email_verification(request):
    """
    Request email verification code
    POST /api/auth/email/verify-request/
    
    Body:
    {
        "email": "user@example.com",
        "code_type": "account_verification" | "login_verification" | "email_change"
    }
    """
    serializer = EmailVerificationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    code_type = serializer.validated_data['code_type']
    
    # All verification types require user to exist (they have an account)
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No active account found with this email address'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # For account verification, check if already verified
    if code_type == EmailVerificationCode.ACCOUNT_VERIFICATION and user.email_verified:
        return Response({
            'success': True,
            'message': 'Email already verified',
            'data': {
                'email_verified': True
            }
        }, status=status.HTTP_200_OK)
    
    # Request verification code
    result = EmailService.request_email_verification(
        email=email,
        code_type=code_type,
        user=user,
        request=request
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': result['message'],
            'data': {
                'verification_id': result['verification_id'],
                'expires_in_minutes': result['expires_in_minutes'],
                'code_type': result['code_type']
            }
        }, status=status.HTTP_200_OK)
    else:
        response_status = status.HTTP_429_TOO_MANY_REQUESTS if result.get('rate_limited') else status.HTTP_500_INTERNAL_SERVER_ERROR
        
        response_data = {
            'success': False,
            'message': result['message']
        }
        
        if result.get('rate_limited'):
            response_data['cooldown_until'] = result.get('cooldown_until')
        
        return Response(response_data, status=response_status)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_code(request):
    """
    Verify email verification code
    POST /api/auth/email/verify-confirm/
    
    Body:
    {
        "email": "user@example.com",
        "code_type": "account_verification",
        "code": "123456"
    }
    """
    serializer = EmailVerificationConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    code_type = serializer.validated_data['code_type']
    code = serializer.validated_data['code']
    
    # Verify email code
    result = EmailService.verify_email_code(
        email=email,
        code_type=code_type,
        raw_code=code,
        request=request
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': result['message'],
            'data': {
                'verification_id': result['verification_id'],
                'user_id': result.get('user_id'),
                'email_verified': True
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['message']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Request password reset
    POST /api/auth/password/reset-request/
    
    Body:
    {
        "email": "user@example.com"
    }
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    # Request password reset
    result = EmailService.request_password_reset(
        email=email,
        request=request
    )
    
    # Always return success for security (don't reveal if email exists)
    return Response({
        'success': True,
        'message': result['message']
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    """
    Confirm password reset with token
    POST /api/auth/password/reset-confirm/
    
    Body:
    {
        "token": "reset_token_here",
        "new_password": "new_password_here"
    }
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']
    
    # Validate password strength
    try:
        validate_password(new_password)
    except ValidationError as e:
        return Response({
            'success': False,
            'message': 'Password does not meet security requirements',
            'errors': {'new_password': list(e.messages)}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Reset password
    result = EmailService.reset_password_with_token(
        token=token,
        new_password=new_password,
        request=request
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': result['message'],
            'data': {
                'password_reset': True,
                'user_id': result.get('user_id')
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['message']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_email_change(request):
    """
    Request email address change
    POST /api/auth/email/change-request/
    
    Body:
    {
        "new_email": "newemail@example.com"
    }
    """
    serializer = EmailChangeRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    new_email = serializer.validated_data['new_email']
    
    # Check if new email is already in use
    if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
        return Response({
            'success': False,
            'message': 'This email address is already in use'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if it's the same email
    if request.user.email == new_email:
        return Response({
            'success': False,
            'message': 'New email address must be different from current email'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Request email change verification
    result = EmailService.request_email_verification(
        email=new_email,
        code_type=EmailVerificationCode.EMAIL_CHANGE,
        user=request.user,
        request=request
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': f'Verification code sent to {new_email}',
            'data': {
                'verification_id': result['verification_id'],
                'new_email': new_email,
                'expires_in_minutes': result['expires_in_minutes']
            }
        }, status=status.HTTP_200_OK)
    else:
        response_status = status.HTTP_429_TOO_MANY_REQUESTS if result.get('rate_limited') else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response({
            'success': False,
            'message': result['message']
        }, status=response_status)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_email_change(request):
    """
    Confirm email address change with verification code
    POST /api/auth/email/change-confirm/
    
    Body:
    {
        "new_email": "newemail@example.com",
        "code": "123456"
    }
    """
    serializer = EmailChangeConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    new_email = serializer.validated_data['new_email']
    code = serializer.validated_data['code']
    
    # Verify email change code
    result = EmailService.verify_email_code(
        email=new_email,
        code_type=EmailVerificationCode.EMAIL_CHANGE,
        raw_code=code,
        request=request
    )
    
    if result['success']:
        # Update user's email
        old_email = request.user.email
        request.user.email = new_email
        request.user.save()
        
        # Log email change event
        from ..models import SecurityEvent
        SecurityEvent.log_event(
            event_type='email_changed',
            user=request.user,
            description=f'Email changed from {old_email} to {new_email}',
            risk_level='medium',
            ip_address=SecurityService.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'old_email': old_email,
                'new_email': new_email,
                'verification_id': result['verification_id']
            }
        )
        
        return Response({
            'success': True,
            'message': 'Email address updated successfully',
            'data': {
                'new_email': new_email,
                'old_email': old_email
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['message']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_email_verification_status(request):
    """
    Get email verification status for current user
    GET /api/auth/email/status/
    """
    try:
        user = request.user
        
        # Get recent verification codes
        recent_codes = EmailVerificationCode.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        
        verification_status = {
            'user_email': user.email,
            'is_email_verified': getattr(user, 'is_email_verified', True),  # Assuming email is verified by default
            'recent_verifications': [
                {
                    'id': str(code.id),
                    'code_type': code.code_type,
                    'code_type_display': code.get_code_type_display(),
                    'status': code.status,
                    'created_at': code.created_at.isoformat(),
                    'expires_at': code.expires_at.isoformat(),
                    'verified_at': code.verified_at.isoformat() if code.verified_at else None
                } for code in recent_codes
            ]
        }
        
        return Response({
            'success': True,
            'data': verification_status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Email verification status error for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to retrieve email verification status',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_code(request):
    """
    Resend verification code for a pending verification
    POST /api/auth/email/resend/
    
    Body:
    {
        "email": "user@example.com",
        "code_type": "account_verification"
    }
    """
    serializer = EmailVerificationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    code_type = serializer.validated_data['code_type']
    
    # This essentially creates a new verification code (old one gets revoked)
    result = EmailService.request_email_verification(
        email=email,
        code_type=code_type,
        user=None,  # Will be determined based on code_type
        request=request
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': 'New verification code sent successfully',
            'data': {
                'verification_id': result['verification_id'],
                'expires_in_minutes': result['expires_in_minutes']
            }
        }, status=status.HTTP_200_OK)
    else:
        response_status = status.HTTP_429_TOO_MANY_REQUESTS if result.get('rate_limited') else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response({
            'success': False,
            'message': result['message']
        }, status=response_status)


# Admin/Management endpoints
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_expired_verifications(request):
    """
    Clean up expired verification codes and tokens (admin only)
    POST /api/auth/email/cleanup/
    """
    if not request.user.is_staff:
        return Response({
            'success': False,
            'message': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        result = EmailService.cleanup_expired_codes_and_tokens()
        
        return Response({
            'success': True,
            'message': 'Cleanup completed successfully',
            'data': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Email cleanup error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to cleanup expired verifications',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)