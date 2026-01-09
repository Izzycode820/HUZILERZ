"""
Security Monitoring Views - Enterprise Security Dashboard
RESTful API endpoints for security monitoring and threat analysis
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import json

from ..services import SecurityMonitoringService
from ..models import SecurityEvent, SecurityAlert, SessionInfo, AuditLog
# TODO: Add decorators when available
# from ..decorators import require_mfa_if_enabled, rate_limit

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def security_dashboard(request):
    """
    Get security dashboard overview for current user
    """
    try:
        user = request.user
        
        # Generate security metrics for the user
        dashboard_data = {
            'user_id': user.id,
            'current_time': timezone.now(),
            
            # Session information
            'active_sessions': SessionInfo.objects.filter(
                user=user,
                is_active=True,
                expires_at__gt=timezone.now()
            ).count(),
            
            # Recent security events (last 7 days)
            'recent_events': SecurityEvent.objects.filter(
                user=user,
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).count(),
            
            # MFA status
            'mfa_enabled': hasattr(user, 'totp_devices') and user.totp_devices.filter(is_active=True).exists(),
            'mfa_devices': user.totp_devices.count() if hasattr(user, 'totp_devices') else 0,
            
            # Recent login locations (last 30 days)
            'recent_locations': list(
                SecurityEvent.objects.filter(
                    user=user,
                    event_type='LOGIN_SUCCESS',
                    timestamp__gte=timezone.now() - timedelta(days=30),
                    location_info__isnull=False
                ).values('location_info__country')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            ),
            
            # Security alerts
            'open_alerts': SecurityAlert.objects.filter(
                user=user,
                status='OPEN'
            ).count(),
            
            # Risk assessment
            'risk_score': SecurityMonitoringService.monitor_mfa_security(user).get('security_concerns', []),
        }
        
        return Response({
            'success': True,
            'data': dashboard_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to load security dashboard: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @require_mfa_if_enabled  # TODO: Add when decorators available
def user_security_events(request):
    """
    Get security events for current user with filtering and pagination
    """
    try:
        user = request.user
        
        # Query parameters
        days = int(request.GET.get('days', 30))
        event_type = request.GET.get('event_type')
        risk_level = request.GET.get('risk_level')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 50)), 100)  # Max 100 items
        
        # Base query
        events_query = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(days=days)
        )
        
        # Apply filters
        if event_type:
            events_query = events_query.filter(event_type=event_type)
        
        if risk_level:
            risk_level_int = SecurityMonitoringService.RISK_LEVELS.get(risk_level.upper())
            if risk_level_int:
                events_query = events_query.filter(risk_level=risk_level_int)
        
        # Pagination
        total_count = events_query.count()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        events = events_query.order_by('-timestamp')[start_index:end_index]
        
        # Serialize events
        events_data = []
        for event in events:
            events_data.append({
                'id': str(event.id),
                'event_type': event.event_type,
                'event_description': event.event_description,
                'risk_level': event.risk_level,
                'risk_level_display': event.risk_level_display,
                'event_category': event.event_category,
                'ip_address': event.ip_address,
                'location_info': event.location_info,
                'timestamp': event.timestamp,
                'metadata': event.metadata
            })
        
        return Response({
            'success': True,
            'data': {
                'events': events_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': 'Invalid parameter values'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to retrieve security events: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @require_mfa_if_enabled  # TODO: Add when decorators available
def active_sessions(request):
    """
    Get active sessions for current user
    """
    try:
        user = request.user
        
        # Get active sessions
        sessions = SessionInfo.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-last_activity')
        
        sessions_data = []
        current_session_id = request.session.get('session_id')
        
        for session in sessions:
            session_security = SecurityMonitoringService.check_session_security(session)
            
            sessions_data.append({
                'session_id': str(session.session_id),
                'is_current': str(session.session_id) == current_session_id,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'expires_at': session.expires_at,
                'ip_address': session.ip_address,
                'location_info': session.location_info,
                'device_info': session.device_info,
                'mfa_verified': session.mfa_verified,
                'is_suspicious': session.is_suspicious,
                'security_status': session_security
            })
        
        return Response({
            'success': True,
            'data': {
                'sessions': sessions_data,
                'total_count': len(sessions_data)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to retrieve active sessions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
# @require_mfa_if_enabled  # TODO: Add when decorators available
def revoke_session(request):
    """
    Revoke a specific session
    """
    try:
        user = request.user
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({
                'success': False,
                'error': 'Session ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find and revoke session
        try:
            session = SessionInfo.objects.get(
                session_id=session_id,
                user=user,
                is_active=True
            )
            
            session.revoke()
            
            # Log security event
            SecurityMonitoringService.log_security_event(
                'SESSION_REVOKED',
                user=user,
                request=request,
                revoked_session_id=session_id
            )
            
            return Response({
                'success': True,
                'message': 'Session revoked successfully'
            }, status=status.HTTP_200_OK)
            
        except SessionInfo.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Session not found or already inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to revoke session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @require_mfa_if_enabled  # TODO: Add when decorators available  
def security_report(request):
    """
    Generate security report for current user
    """
    try:
        user = request.user
        days = int(request.GET.get('days', 30))
        
        # Generate comprehensive security report
        report = SecurityMonitoringService.generate_security_report(user, days)
        
        return Response({
            'success': True,
            'data': report
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'success': False,
            'error': 'Invalid days parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to generate security report: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin-only endpoints
@api_view(['GET'])
@permission_classes([IsAdminUser])
# @require_mfa_if_enabled  # TODO: Add when decorators available
def admin_security_overview(request):
    """
    Admin security overview dashboard
    """
    try:
        # Time range
        days = int(request.GET.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        
        # Overall statistics
        overview_data = {
            'time_range_days': days,
            'generated_at': timezone.now(),
            
            # Event statistics
            'total_events': SecurityEvent.objects.filter(timestamp__gte=since).count(),
            'high_risk_events': SecurityEvent.objects.filter(
                timestamp__gte=since,
                risk_level__gte=SecurityMonitoringService.RISK_LEVELS['HIGH']
            ).count(),
            'failed_logins': SecurityEvent.objects.filter(
                timestamp__gte=since,
                event_type='LOGIN_FAILED'
            ).count(),
            'successful_logins': SecurityEvent.objects.filter(
                timestamp__gte=since,
                event_type='LOGIN_SUCCESS'
            ).count(),
            
            # User statistics
            'active_users': User.objects.filter(
                last_login__gte=since
            ).count(),
            'new_users': User.objects.filter(
                date_joined__gte=since
            ).count(),
            'mfa_enabled_users': User.objects.filter(
                totp_devices__is_active=True
            ).distinct().count() if hasattr(User, 'totp_devices') else 0,
            
            # Security alerts
            'open_alerts': SecurityAlert.objects.filter(status='OPEN').count(),
            'resolved_alerts': SecurityAlert.objects.filter(
                status='RESOLVED',
                resolved_at__gte=since
            ).count(),
            
            # Session statistics
            'active_sessions': SessionInfo.objects.filter(
                is_active=True,
                expires_at__gt=timezone.now()
            ).count(),
            'suspicious_sessions': SessionInfo.objects.filter(
                is_suspicious=True,
                is_active=True
            ).count(),
            
            # Top risk factors
            'top_risk_events': list(
                SecurityEvent.objects.filter(
                    timestamp__gte=since,
                    risk_level__gte=SecurityMonitoringService.RISK_LEVELS['MEDIUM']
                ).values('event_type')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
            
            # Geographic distribution
            'top_countries': list(
                SecurityEvent.objects.filter(
                    timestamp__gte=since,
                    location_info__isnull=False
                ).values('location_info__country')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
        }
        
        return Response({
            'success': True,
            'data': overview_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to generate admin security overview: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
# @require_mfa_if_enabled  # TODO: Add when decorators available
def security_alerts(request):
    """
    Get security alerts with filtering
    """
    try:
        # Query parameters
        status_filter = request.GET.get('status', 'OPEN')
        severity = request.GET.get('severity')
        alert_type = request.GET.get('alert_type')
        days = int(request.GET.get('days', 30))
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 50)), 100)
        
        # Base query
        alerts_query = SecurityAlert.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=days)
        )
        
        # Apply filters
        if status_filter != 'ALL':
            alerts_query = alerts_query.filter(status=status_filter)
        
        if severity:
            alerts_query = alerts_query.filter(severity=severity.upper())
            
        if alert_type:
            alerts_query = alerts_query.filter(alert_type=alert_type.upper())
        
        # Pagination
        total_count = alerts_query.count()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        alerts = alerts_query.order_by('-created_at')[start_index:end_index]
        
        # Serialize alerts
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': str(alert.id),
                'alert_type': alert.alert_type,
                'title': alert.title,
                'description': alert.description,
                'severity': alert.severity,
                'status': alert.status,
                'user': alert.user.username if alert.user else None,
                'created_at': alert.created_at,
                'updated_at': alert.updated_at,
                'resolved_at': alert.resolved_at,
                'assigned_to': alert.assigned_to.username if alert.assigned_to else None,
                'alert_data': alert.alert_data
            })
        
        return Response({
            'success': True,
            'data': {
                'alerts': alerts_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to retrieve security alerts: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
# @require_mfa_if_enabled  # TODO: Add when decorators available
def resolve_alert(request, alert_id):
    """
    Resolve a security alert
    """
    try:
        notes = request.data.get('notes', '')
        
        alert = SecurityAlert.objects.get(id=alert_id)
        alert.resolve(resolved_by=request.user, notes=notes)
        
        # Log audit event
        SecurityMonitoringService.log_security_event(
            'ADMIN_ACTION',
            user=request.user,
            request=request,
            action='resolve_alert',
            alert_id=alert_id
        )
        
        return Response({
            'success': True,
            'message': 'Alert resolved successfully'
        }, status=status.HTTP_200_OK)
        
    except SecurityAlert.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Alert not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to resolve alert: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @require_mfa_if_enabled  # TODO: Add when decorators available
# @rate_limit(key='security_health_check', rate='10/m')  # TODO: Add when decorators available
def security_health_check(request):
    """
    Security health check endpoint
    """
    try:
        user = request.user
        
        health_status = {
            'user_id': user.id,
            'timestamp': timezone.now(),
            'checks': {
                'mfa_enabled': hasattr(user, 'totp_devices') and user.totp_devices.filter(is_active=True).exists(),
                'recent_login': SecurityEvent.objects.filter(
                    user=user,
                    event_type='LOGIN_SUCCESS',
                    timestamp__gte=timezone.now() - timedelta(days=30)
                ).exists(),
                'no_recent_failures': SecurityEvent.objects.filter(
                    user=user,
                    event_type='LOGIN_FAILED',
                    timestamp__gte=timezone.now() - timedelta(hours=24)
                ).count() < 5,
                'no_suspicious_activity': not SecurityEvent.objects.filter(
                    user=user,
                    risk_level__gte=SecurityMonitoringService.RISK_LEVELS['HIGH'],
                    timestamp__gte=timezone.now() - timedelta(days=7)
                ).exists(),
                'sessions_secure': not SessionInfo.objects.filter(
                    user=user,
                    is_active=True,
                    is_suspicious=True
                ).exists()
            }
        }
        
        # Calculate overall health score
        passed_checks = sum(1 for check in health_status['checks'].values() if check)
        total_checks = len(health_status['checks'])
        health_score = (passed_checks / total_checks) * 100
        
        health_status['overall_health_score'] = health_score
        health_status['health_grade'] = (
            'EXCELLENT' if health_score >= 90 else
            'GOOD' if health_score >= 70 else
            'FAIR' if health_score >= 50 else
            'POOR'
        )
        
        return Response({
            'success': True,
            'data': health_status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Health check failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)