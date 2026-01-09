"""
Enterprise MFA API Views - 2025 Security Standards
Handles TOTP setup, verification, backup codes, and MFA management
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from ..services import MFAService, SecurityService
from ..serializers.mfa_serializers import (
    TOTPSetupSerializer, TOTPConfirmSerializer, MFAVerifySerializer,
    BackupCodeRegenerateSerializer
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_totp(request):
    """
    Setup TOTP device for user
    POST /api/auth/mfa/totp/setup/
    """
    serializer = TOTPSetupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    device_name = serializer.validated_data.get('device_name', 'Authenticator App')
    force_reset = serializer.validated_data.get('force_reset', False)
    
    # Get client info for audit
    ip_address = SecurityService.get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Setup TOTP device
    result = MFAService.setup_totp_device(
        user=request.user,
        device_name=device_name,
        force_reset=force_reset
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': 'TOTP device setup initiated',
            'data': {
                'device_id': result['device_id'],
                'device_name': result['device_name'],
                'qr_code_base64': result['qr_code_base64'],
                'manual_entry_key': result['manual_entry_key'],
                'issuer': result['issuer'],
                'account_name': result['account_name'],
                'setup_instructions': result['setup_instructions']
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['message'],
            'device_status': result.get('device_status')
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_totp(request):
    """
    Confirm TOTP device setup with verification token
    POST /api/auth/mfa/totp/confirm/
    """
    serializer = TOTPConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    ip_address = SecurityService.get_client_ip(request)
    
    # Confirm TOTP device
    result = MFAService.confirm_totp_device(
        user=request.user,
        token=token,
        ip_address=ip_address
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': result['message'],
            'data': {
                'device_confirmed': result['device_confirmed'],
                'backup_codes': result['backup_codes'],
                'backup_codes_info': result['backup_codes_info']
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['message']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_mfa(request):
    """
    Verify MFA token (TOTP or backup code)
    POST /api/auth/mfa/verify/
    """
    serializer = MFAVerifySerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    ip_address = SecurityService.get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Verify MFA token
    result = MFAService.verify_mfa_token(
        user=request.user,
        token=token,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result['success']:
        response_data = {
            'success': True,
            'message': result['message'],
            'method': result['method']
        }
        
        # Add remaining backup codes info if used backup code
        if result['method'] == 'backup_code':
            response_data['remaining_backup_codes'] = result.get('remaining_codes', 0)
            
            # Warning if low on backup codes
            if result.get('remaining_codes', 0) <= 2:
                response_data['warning'] = 'Low backup codes remaining. Consider regenerating.'
        
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['message']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mfa_status(request):
    """
    Get comprehensive MFA status for user
    GET /api/auth/mfa/status/
    """
    status_data = MFAService.get_mfa_status(request.user)
    
    return Response({
        'success': True,
        'data': status_data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_backup_codes(request):
    """
    Regenerate backup codes for user
    POST /api/auth/mfa/backup-codes/regenerate/
    """
    serializer = BackupCodeRegenerateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Optional current MFA token for high-security regeneration
    current_token = serializer.validated_data.get('current_mfa_token')
    ip_address = SecurityService.get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Verify current MFA token if provided (recommended for security)
    if current_token:
        verify_result = MFAService.verify_mfa_token(
            user=request.user,
            token=current_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not verify_result['success']:
            return Response({
                'success': False,
                'message': 'Invalid current MFA token'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Regenerate backup codes
    result = MFAService.regenerate_backup_codes(
        user=request.user,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': result['message'],
            'data': {
                'backup_codes': result['backup_codes'],
                'codes_generated': result['codes_generated'],
                'expiration_days': result['expiration_days'],
                'warning': 'Store these codes securely. Previous codes are now invalid.'
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['message']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_mfa(request):
    """
    Disable MFA for user (requires current MFA token)
    POST /api/auth/mfa/disable/
    """
    serializer = MFAVerifySerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    confirmation_token = serializer.validated_data['token']
    ip_address = SecurityService.get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Disable MFA with confirmation
    result = MFAService.disable_mfa(
        user=request.user,
        confirmation_token=confirmation_token,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': result['message'],
            'security_warning': result['security_warning']
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['message']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def backup_codes_status(request):
    """
    Get backup codes status and usage statistics
    GET /api/auth/mfa/backup-codes/status/
    """
    from ..models import BackupCode
    
    # Get backup codes statistics
    backup_codes = BackupCode.objects.filter(user=request.user)
    
    status_data = {
        'total_codes': backup_codes.count(),
        'unused_codes': backup_codes.filter(status=BackupCode.UNUSED).count(),
        'used_codes': backup_codes.filter(status=BackupCode.USED).count(),
        'expired_codes': backup_codes.filter(status=BackupCode.EXPIRED).count(),
        'revoked_codes': backup_codes.filter(status=BackupCode.REVOKED).count(),
    }
    
    # Get recent usage
    recent_usage = backup_codes.filter(
        status=BackupCode.USED
    ).order_by('-used_at')[:5].values(
        'code_partial', 'used_at', 'used_ip'
    )
    
    # Recommendations
    recommendations = []
    if status_data['unused_codes'] <= 2:
        recommendations.append("Consider regenerating backup codes - you have few remaining")
    if status_data['unused_codes'] == 0:
        recommendations.append("URGENT: No backup codes available - regenerate immediately")
    
    return Response({
        'success': True,
        'data': {
            'status': status_data,
            'recent_usage': list(recent_usage),
            'recommendations': recommendations
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  
def unlock_totp_device(request):
    """
    Unlock TOTP device (admin or self-unlock after lockout period)
    POST /api/auth/mfa/totp/unlock/
    """
    from ..models import TOTPDevice
    
    try:
        device = TOTPDevice.objects.get(user=request.user)
        
        if not device.is_locked:
            return Response({
                'success': False,
                'message': 'Device is not locked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to unlock device
        unlocked = device.unlock_device(force=False)
        
        if unlocked:
            return Response({
                'success': True,
                'message': 'TOTP device unlocked successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Device lockout period has not expired',
                'lockout_until': device.lockout_until.isoformat() if device.lockout_until else None
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except TOTPDevice.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No TOTP device found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"TOTP unlock error for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to unlock device'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin/Management endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mfa_security_report(request):
    """
    Get comprehensive MFA security report (for security dashboard)
    GET /api/auth/mfa/security/report/
    """
    # Only allow for staff users or users viewing their own report
    if not request.user.is_staff:
        # Return user's own security report
        user = request.user
    else:
        # Staff can view any user's report (implement user_id parameter if needed)
        user = request.user
    
    # Get comprehensive security data
    mfa_status = MFAService.get_mfa_status(user)
    
    # Additional security metrics
    from ..models import SecurityEvent, TOTPDevice, BackupCode
    
    recent_events = SecurityEvent.objects.filter(
        user=user,
        event_type__in=[
            'totp_setup_initiated', 'totp_device_confirmed', 'mfa_verification_failed',
            'backup_code_used', 'backup_codes_generated', 'mfa_disabled'
        ]
    ).order_by('-created_at')[:10]
    
    security_report = {
        'user_id': str(user.id),
        'mfa_status': mfa_status,
        'security_score': mfa_status.get('security_score', 0),
        'recent_security_events': [
            {
                'event_type': event.event_type,
                'description': event.description,
                'risk_level': event.risk_level,
                'created_at': event.created_at.isoformat(),
                'ip_address': event.ip_address,
                'metadata': event.metadata
            } for event in recent_events
        ],
        'recommendations': []
    }
    
    # Generate recommendations
    if not mfa_status['mfa_enabled']:
        security_report['recommendations'].append({
            'priority': 'high',
            'type': 'enable_mfa',
            'message': 'Enable MFA to significantly improve account security'
        })
    
    if mfa_status['backup_codes']['unused'] <= 2:
        security_report['recommendations'].append({
            'priority': 'medium',
            'type': 'regenerate_backup_codes',
            'message': 'Regenerate backup codes - few remaining'
        })
    
    return Response({
        'success': True,
        'data': security_report
    }, status=status.HTTP_200_OK)