"""
Enterprise MFA Policy Views - 2025 Security Standards
Handles MFA enforcement policies, compliance checking, and progressive enrollment
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from ..services import MFAPolicyService, SecurityService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mfa_policy(request):
    """
    Get comprehensive MFA policy for current user
    GET /api/auth/mfa/policy/
    """
    try:
        policy = MFAPolicyService.get_user_mfa_policy(request.user)
        
        # Log policy access for audit
        MFAPolicyService.log_policy_event(
            user=request.user,
            event_type='policy_accessed',
            details={'enforcement_level': policy['enforcement']['level']}
        )
        
        return Response({
            'success': True,
            'data': policy
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"MFA policy error for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to retrieve MFA policy',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_access_compliance(request):
    """
    Check if user's current MFA status allows access
    POST /api/auth/mfa/policy/check-access/
    """
    try:
        should_block, reason = MFAPolicyService.should_block_access(request.user)
        
        if should_block:
            # Log access blocked event
            MFAPolicyService.log_policy_event(
                user=request.user,
                event_type='access_blocked',
                details={
                    'reason': reason,
                    'ip_address': SecurityService.get_client_ip(request)
                }
            )
            
            return Response({
                'success': False,
                'access_allowed': False,
                'message': reason,
                'action_required': 'setup_mfa'
            }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'success': True,
                'access_allowed': True,
                'message': 'Access granted'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Access compliance check error for user {request.user.id}: {str(e)}")
        # Fail open - allow access in case of errors
        return Response({
            'success': True,
            'access_allowed': True,
            'message': 'Access granted (policy check failed)',
            'error': str(e)
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def acknowledge_mfa_prompt(request):
    """
    Mark MFA enrollment prompt as acknowledged by user
    POST /api/auth/mfa/policy/acknowledge-prompt/
    """
    try:
        prompt_type = request.data.get('prompt_type', 'unknown')
        action_taken = request.data.get('action_taken', 'dismissed')
        
        # Log prompt acknowledgment
        MFAPolicyService.log_policy_event(
            user=request.user,
            event_type='prompt_acknowledged',
            details={
                'prompt_type': prompt_type,
                'action_taken': action_taken,
                'ip_address': SecurityService.get_client_ip(request)
            }
        )
        
        return Response({
            'success': True,
            'message': 'Prompt acknowledgment recorded'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Prompt acknowledgment error for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to record prompt acknowledgment',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_enrollment_guidance(request):
    """
    Get personalized MFA enrollment guidance for user
    GET /api/auth/mfa/policy/enrollment-guidance/
    """
    try:
        policy = MFAPolicyService.get_user_mfa_policy(request.user)
        
        # Build guidance response
        guidance = {
            'should_enroll': not policy['mfa_enabled'],
            'urgency_level': policy['enrollment_prompts']['prompt_type'],
            'recommendations': policy['recommendations'],
            'compliance_status': policy['compliance'],
            'enforcement_level': policy['enforcement']['level'],
            'steps': []
        }
        
        # Add step-by-step enrollment guidance
        if not policy['mfa_enabled']:
            guidance['steps'] = [
                {
                    'step': 1,
                    'title': 'Install Authenticator App',
                    'description': 'Download Google Authenticator, Authy, or similar TOTP app',
                    'estimated_time': '2 minutes',
                    'optional': False
                },
                {
                    'step': 2,
                    'title': 'Setup TOTP Device',
                    'description': 'Scan QR code or manually enter setup key',
                    'action': 'setup_totp',
                    'estimated_time': '1 minute',
                    'optional': False
                },
                {
                    'step': 3,
                    'title': 'Confirm Setup',
                    'description': 'Enter verification code from your app',
                    'action': 'confirm_totp',
                    'estimated_time': '1 minute',
                    'optional': False
                },
                {
                    'step': 4,
                    'title': 'Save Backup Codes',
                    'description': 'Securely store your backup recovery codes',
                    'estimated_time': '2 minutes',
                    'optional': False
                }
            ]
        
        return Response({
            'success': True,
            'data': guidance
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Enrollment guidance error for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to retrieve enrollment guidance',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_risk_assessment(request):
    """
    Get user's security risk assessment
    GET /api/auth/mfa/policy/risk-assessment/
    """
    try:
        policy = MFAPolicyService.get_user_mfa_policy(request.user)
        risk_assessment = policy['risk_assessment']
        
        # Add additional context
        risk_assessment['mitigation_strategies'] = []
        
        # Generate mitigation strategies based on risk factors
        for factor in risk_assessment['factors']:
            if factor == 'superuser_access':
                risk_assessment['mitigation_strategies'].append({
                    'factor': factor,
                    'strategy': 'Enable MFA immediately - superuser accounts are high-value targets'
                })
            elif factor == 'new_account':
                risk_assessment['mitigation_strategies'].append({
                    'factor': factor,
                    'strategy': 'Set up MFA early to establish strong security habits'
                })
            elif factor == 'recent_security_events':
                risk_assessment['mitigation_strategies'].append({
                    'factor': factor,
                    'strategy': 'Review recent security events and enable MFA for protection'
                })
        
        return Response({
            'success': True,
            'data': risk_assessment
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Risk assessment error for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to retrieve risk assessment',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin endpoints
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_organization_mfa_stats(request):
    """
    Get organization-wide MFA statistics (admin only)
    GET /api/auth/mfa/policy/organization-stats/
    """
    try:
        stats = MFAPolicyService.get_organization_mfa_stats()
        
        return Response({
            'success': True,
            'data': stats
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Organization MFA stats error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to retrieve organization statistics',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_compliance_report(request):
    """
    Get detailed compliance report for all users (admin only)
    GET /api/auth/mfa/policy/compliance-report/
    """
    try:
        # Get all active users
        users = User.objects.filter(is_active=True)
        
        compliance_data = []
        summary_stats = {
            'total_users': 0,
            'compliant': 0,
            'non_compliant': 0,
            'grace_period': 0,
            'by_risk_level': {}
        }
        
        for user in users[:100]:  # Limit to prevent timeout
            policy = MFAPolicyService.get_user_mfa_policy(user)
            
            user_compliance = {
                'user_id': str(user.id),
                'email': user.email,
                'is_staff': user.is_staff,
                'mfa_enabled': policy['mfa_enabled'],
                'risk_level': policy['risk_assessment']['level'],
                'enforcement_level': policy['enforcement']['level'],
                'compliance_status': policy['compliance']['status']
            }
            
            compliance_data.append(user_compliance)
            
            # Update summary stats
            summary_stats['total_users'] += 1
            status = policy['compliance']['status']
            
            if status == 'compliant':
                summary_stats['compliant'] += 1
            elif status == 'non_compliant':
                summary_stats['non_compliant'] += 1
            elif status == 'grace_period':
                summary_stats['grace_period'] += 1
            
            # Risk level stats
            risk_level = policy['risk_assessment']['level']
            if risk_level not in summary_stats['by_risk_level']:
                summary_stats['by_risk_level'][risk_level] = 0
            summary_stats['by_risk_level'][risk_level] += 1
        
        return Response({
            'success': True,
            'data': {
                'summary': summary_stats,
                'detailed_compliance': compliance_data,
                'generated_at': MFAPolicyService.get_organization_mfa_stats()['generated_at']
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Compliance report error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to generate compliance report',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_policy_settings(request):
    """
    Update global MFA policy settings (admin only)
    POST /api/auth/mfa/policy/settings/
    """
    try:
        # This would update global policy settings
        # For now, just log the attempt
        MFAPolicyService.log_policy_event(
            user=request.user,
            event_type='policy_settings_updated',
            details={
                'settings_updated': request.data,
                'admin_user': request.user.email
            }
        )
        
        return Response({
            'success': True,
            'message': 'Policy settings update logged (feature in development)'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Policy settings update error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to update policy settings',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)