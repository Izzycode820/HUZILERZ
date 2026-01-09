"""
Enterprise Phone Authentication Views - 2025 Security Standards
Handles phone OTP verification and phone-based authentication

Production Standards:
- Consistent response format across all endpoints
- Serializer-based input validation
- Proper error handling with logging
- Rate limiting enforcement
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from ..services.sms_service import SMSService
from ..models import PhoneVerificationCode
from ..serializers import (
    PhoneVerificationRequestSerializer,
    PhoneVerificationConfirmSerializer,
    PhoneChangeRequestSerializer,
    PhoneChangeConfirmSerializer,
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def phone_response(success, message, data=None, status_code=status.HTTP_200_OK):
    """
    Consistent response format for phone verification endpoints
    
    Args:
        success: Boolean indicating success/failure
        message: User-friendly message
        data: Additional response data
        status_code: HTTP status code
        
    Returns:
        Response: DRF Response object
    """
    response_data = {
        'success': success,
        'message': message
    }
    if data:
        response_data.update(data)
    return Response(response_data, status=status_code)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_phone_verification(request):
    """
    Request phone verification code
    POST /api/auth/phone/verify-request/
    
    Body:
    {
        "phone_number": "+237612345678",
        "code_type": "phone_verification" | "login_verification"
    }
    
    Response:
    {
        "success": true,
        "message": "Verification code sent to +237****5678",
        "verification_id": "uuid",
        "expires_in_minutes": 10
    }
    """
    try:
        # Validate input using serializer
        serializer = PhoneVerificationRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Return first validation error
            first_error = next(iter(serializer.errors.values()))[0]
            return phone_response(
                False,
                str(first_error),
                data={'errors': serializer.errors},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        phone_number = validated_data['phone_number']
        code_type = validated_data['code_type']
        
        # Get user if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # Request verification
        result = SMSService.request_phone_verification(
            phone_number=phone_number,
            code_type=code_type,
            user=user,
            request=request
        )
        
        if result['success']:
            return phone_response(
                True,
                result['message'],
                data={
                    'verification_id': result.get('verification_id'),
                    'expires_in_minutes': result.get('expires_in_minutes'),
                    'code_type': result.get('code_type')
                }
            )
        else:
            # Check if rate limited
            if result.get('rate_limited'):
                return phone_response(
                    False,
                    result['message'],
                    data={
                        'rate_limited': True,
                        'cooldown_until': result.get('cooldown_until')
                    },
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            return phone_response(
                False,
                result['message'],
                data={'error_code': result.get('error_code')},
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Phone verification request error: {e}")
        return phone_response(
            False,
            'An error occurred processing your request',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_phone_code(request):
    """
    Verify phone verification code
    POST /api/auth/phone/verify-confirm/
    
    Body:
    {
        "phone_number": "+237612345678",
        "code_type": "phone_verification",
        "code": "123456"
    }
    
    Response:
    {
        "success": true,
        "message": "Phone verification code verified successfully",
        "verification_id": "uuid",
        "user_id": "uuid" (if user was associated)
    }
    """
    try:
        # Validate input using serializer
        serializer = PhoneVerificationConfirmSerializer(data=request.data)
        
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return phone_response(
                False,
                str(first_error),
                data={'errors': serializer.errors},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        phone_number = validated_data['phone_number']
        code_type = validated_data['code_type']
        code = validated_data['code']
        
        # Verify code
        result = SMSService.verify_phone_code(
            phone_number=phone_number,
            code_type=code_type,
            raw_code=code,
            request=request
        )
        
        if result['success']:
            # If user was associated with verification, update their phone_verified status
            if result.get('user_id'):
                try:
                    user = User.objects.get(id=result['user_id'])
                    # Update user's phone verification status if they have such field
                    if hasattr(user, 'phone_verified'):
                        user.phone_verified = True
                        user.save(update_fields=['phone_verified'])
                    if hasattr(user, 'phone_number'):
                        normalized_phone, _ = PhoneVerificationCode.normalize_phone_number(phone_number)
                        user.phone_number = normalized_phone
                        user.save(update_fields=['phone_number'])
                except User.DoesNotExist:
                    logger.warning(f"User not found for verification: {result.get('user_id')}")
            
            return phone_response(
                True,
                result['message'],
                data={
                    'verification_id': result.get('verification_id'),
                    'user_id': result.get('user_id')
                }
            )
        else:
            return phone_response(
                False,
                result['message'],
                data={'verification_id': result.get('verification_id')},
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Phone code verification error: {e}")
        return phone_response(
            False,
            'An error occurred processing your request',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_phone_verification_status(request):
    """
    Get phone verification status for current user
    GET /api/auth/phone/status/
    
    Response:
    {
        "success": true,
        "message": "Phone verification status retrieved",
        "phone_verified": true,
        "phone_number": "+237****5678",
        "has_pending_verification": false,
        "rate_limit": {...}
    }
    """
    try:
        user = request.user
        
        # Get user's phone number if available
        phone_number = getattr(user, 'phone_number', None)
        
        if not phone_number:
            return phone_response(
                True,
                'No phone number associated with account',
                data={
                    'phone_verified': False,
                    'phone_number': None,
                    'has_pending_verification': False
                }
            )
        
        # Get verification status
        status_result = SMSService.get_phone_verification_status(phone_number, user)
        
        # Mask phone for response
        masked_phone = SMSService._mask_phone(phone_number)
        
        return phone_response(
            True,
            'Phone verification status retrieved',
            data={
                'phone_verified': status_result.get('phone_verified', False),
                'phone_number': masked_phone,
                'has_pending_verification': status_result.get('has_pending_verification', False),
                'pending_expires_at': status_result.get('pending_expires_at'),
                'rate_limit': status_result.get('rate_limit', {})
            }
        )
        
    except Exception as e:
        logger.error(f"Phone verification status error: {e}")
        return phone_response(
            False,
            'An error occurred retrieving verification status',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_phone_change(request):
    """
    Request phone number change verification
    POST /api/auth/phone/change-request/
    
    Body:
    {
        "new_phone_number": "+237612345678"
    }
    
    Response:
    {
        "success": true,
        "message": "Verification code sent to +237****5678",
        "verification_id": "uuid",
        "expires_in_minutes": 10
    }
    """
    try:
        # Validate input using serializer
        serializer = PhoneChangeRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return phone_response(
                False,
                str(first_error),
                data={'errors': serializer.errors},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        new_phone_number = validated_data['new_phone_number']
        
        # Normalize and check if phone already in use
        normalized_phone, _ = PhoneVerificationCode.normalize_phone_number(new_phone_number)
        
        if hasattr(User, 'phone_number'):
            existing_user = User.objects.filter(phone_number=normalized_phone).exclude(
                id=request.user.id
            ).exists()
            if existing_user:
                return phone_response(
                    False,
                    'This phone number is already associated with another account',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Request verification
        result = SMSService.request_phone_verification(
            phone_number=new_phone_number,
            code_type=PhoneVerificationCode.PHONE_CHANGE,
            user=request.user,
            request=request
        )
        
        if result['success']:
            return phone_response(
                True,
                result['message'],
                data={
                    'verification_id': result.get('verification_id'),
                    'expires_in_minutes': result.get('expires_in_minutes')
                }
            )
        else:
            if result.get('rate_limited'):
                return phone_response(
                    False,
                    result['message'],
                    data={
                        'rate_limited': True,
                        'cooldown_until': result.get('cooldown_until')
                    },
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            return phone_response(
                False,
                result['message'],
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Phone change request error: {e}")
        return phone_response(
            False,
            'An error occurred processing your request',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_phone_change(request):
    """
    Confirm phone number change with verification code
    POST /api/auth/phone/change-confirm/
    
    Body:
    {
        "new_phone_number": "+237612345678",
        "code": "123456"
    }
    
    Response:
    {
        "success": true,
        "message": "Phone number updated successfully",
        "phone_number": "+237****5678"
    }
    """
    try:
        # Validate input using serializer
        serializer = PhoneChangeConfirmSerializer(data=request.data)
        
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return phone_response(
                False,
                str(first_error),
                data={'errors': serializer.errors},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        new_phone_number = validated_data['new_phone_number']
        code = validated_data['code']
        
        # Verify code
        result = SMSService.verify_phone_code(
            phone_number=new_phone_number,
            code_type=PhoneVerificationCode.PHONE_CHANGE,
            raw_code=code,
            request=request
        )
        
        if result['success']:
            # Update user's phone number
            user = request.user
            normalized_phone, _ = PhoneVerificationCode.normalize_phone_number(new_phone_number)
            
            fields_to_update = []
            if hasattr(user, 'phone_number'):
                user.phone_number = normalized_phone
                fields_to_update.append('phone_number')
            if hasattr(user, 'phone_verified'):
                user.phone_verified = True
                fields_to_update.append('phone_verified')
            
            if fields_to_update:
                user.save(update_fields=fields_to_update)
            
            return phone_response(
                True,
                'Phone number updated successfully',
                data={
                    'phone_number': SMSService._mask_phone(normalized_phone)
                }
            )
        else:
            return phone_response(
                False,
                result['message'],
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Phone change confirmation error: {e}")
        return phone_response(
            False,
            'An error occurred processing your request',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_phone_verification(request):
    """
    Resend phone verification code
    POST /api/auth/phone/resend/
    
    Body:
    {
        "phone_number": "+237612345678",
        "code_type": "phone_verification"
    }
    
    Response:
    {
        "success": true,
        "message": "Verification code resent",
        "verification_id": "uuid",
        "expires_in_minutes": 10
    }
    """
    # Delegate to request_phone_verification
    return request_phone_verification(request)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_sms_service_status(request):
    """
    Check if SMS service is available (health check)
    GET /api/auth/phone/service-status/
    
    Response:
    {
        "success": true,
        "message": "SMS service status",
        "available": true,
        "configured": true
    }
    """
    try:
        service_status = SMSService.is_service_available()
        
        return phone_response(
            True,
            'SMS service status retrieved',
            data={
                'available': service_status.get('available', False),
                'configured': service_status.get('configured', False)
            }
        )
        
    except Exception as e:
        logger.error(f"SMS service status check error: {e}")
        return phone_response(
            False,
            'Failed to check SMS service status',
            data={'available': False, 'configured': False},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
