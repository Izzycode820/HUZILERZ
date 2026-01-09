"""
Enterprise Security Monitoring Service - 2025 Standards
Comprehensive security event tracking, threat detection, and audit logging
"""
import logging
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.cache import cache
from django.contrib.gis.geoip2 import GeoIP2
from django.core.exceptions import ValidationError
import ipaddress
import re
from user_agents import parse as parse_user_agent
from ..models import SecurityEvent, SessionInfo, TOTPDevice, BackupCode

User = get_user_model()

# Security event logger
security_logger = logging.getLogger('authentication.security')


class SecurityMonitoringService:
    """
    Enterprise security monitoring with real-time threat detection
    """
    
    # Security event types
    EVENT_TYPES = {
        # Authentication events
        'LOGIN_SUCCESS': 'Successful login',
        'LOGIN_FAILED': 'Failed login attempt',
        'LOGIN_SUSPICIOUS': 'Suspicious login detected',
        'LOGOUT': 'User logout',
        'SESSION_EXPIRED': 'Session expired',
        'SESSION_REVOKED': 'Session manually revoked',
        
        # MFA events
        'MFA_SETUP': 'MFA device setup',
        'MFA_SUCCESS': 'MFA verification success',
        'MFA_FAILED': 'MFA verification failed',
        'MFA_LOCKOUT': 'MFA device locked out',
        'MFA_BACKUP_USED': 'Backup code used',
        'MFA_DISABLED': 'MFA disabled',
        
        # Token events
        'TOKEN_ISSUED': 'JWT token issued',
        'TOKEN_REFRESHED': 'JWT token refreshed',
        'TOKEN_BLACKLISTED': 'Token blacklisted',
        'TOKEN_REUSE_DETECTED': 'Refresh token reuse detected',
        'TOKEN_FAMILY_INVALIDATED': 'Token family invalidated',
        
        # OAuth2 events
        'OAUTH2_SUCCESS': 'OAuth2 authentication success',
        'OAUTH2_FAILED': 'OAuth2 authentication failed',
        'OAUTH2_ACCOUNT_LINKED': 'OAuth2 account linked',
        
        # Email events
        'EMAIL_VERIFICATION_SENT': 'Email verification code sent',
        'EMAIL_VERIFICATION_SUCCESS': 'Email verification success',
        'EMAIL_VERIFICATION_FAILED': 'Email verification failed',
        'PASSWORD_RESET_REQUESTED': 'Password reset requested',
        'PASSWORD_RESET_SUCCESS': 'Password reset completed',
        
        # Security threats
        'BRUTE_FORCE_DETECTED': 'Brute force attack detected',
        'RATE_LIMIT_EXCEEDED': 'Rate limit exceeded',
        'SUSPICIOUS_LOCATION': 'Login from suspicious location',
        'DEVICE_CHANGE_DETECTED': 'New device detected',
        'CONCURRENT_SESSION_LIMIT': 'Concurrent session limit reached',
        
        # System events
        'SECURITY_POLICY_CHANGED': 'Security policy updated',
        'ADMIN_ACTION': 'Administrative security action',
        'SYSTEM_ANOMALY': 'System security anomaly detected'
    }
    
    # Risk levels
    RISK_LEVELS = {
        'LOW': 1,
        'MEDIUM': 2,
        'HIGH': 3,
        'CRITICAL': 4
    }
    
    @classmethod
    def log_security_event(cls, event_type: str, user: Optional[User] = None, 
                          request=None, **kwargs) -> 'SecurityEvent':
        """
        Log a comprehensive security event
        """
        try:
            # Extract request information
            ip_address = cls._extract_ip_address(request) if request else None
            user_agent = cls._extract_user_agent(request) if request else None
            device_fingerprint = cls._extract_device_fingerprint(request) if request else None
            
            # Analyze threat level
            risk_level = cls._calculate_risk_level(event_type, user, ip_address, **kwargs)
            
            # Create security event
            event_data = {
                'event_type': event_type,
                'event_description': cls.EVENT_TYPES.get(event_type, 'Unknown event'),
                'user': user,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'device_fingerprint': device_fingerprint,
                'risk_level': risk_level,
                'metadata': cls._prepare_metadata(request, **kwargs),
                'location_info': cls._get_location_info(ip_address) if ip_address else None,
                'timestamp': timezone.now()
            }
            
            # Store in database
            security_event = SecurityEvent.objects.create(**event_data)
            
            # Log to security logger
            security_logger.info(
                f"Security Event: {event_type} | User: {user.username if user else 'Anonymous'} | "
                f"IP: {ip_address} | Risk: {risk_level} | ID: {security_event.id}"
            )
            
            # Check for automated responses
            cls._check_automated_responses(security_event)
            
            return security_event
            
        except Exception as e:
            security_logger.error(f"Failed to log security event: {str(e)}")
            # Don't raise to avoid breaking the main flow
            return None
    
    @classmethod
    def detect_brute_force(cls, user: Optional[User] = None, ip_address: str = None, 
                          time_window: int = 300) -> bool:
        """
        Detect brute force attacks
        """
        if not user and not ip_address:
            return False
        
        try:
            since = timezone.now() - timedelta(seconds=time_window)
            
            # Check failed login attempts
            failed_events = SecurityEvent.objects.filter(
                event_type='LOGIN_FAILED',
                timestamp__gte=since
            )
            
            if user:
                failed_events = failed_events.filter(user=user)
            
            if ip_address:
                failed_events = failed_events.filter(ip_address=ip_address)
            
            failed_count = failed_events.count()
            
            # Threshold for brute force detection
            threshold = getattr(settings, 'BRUTE_FORCE_THRESHOLD', 5)
            
            if failed_count >= threshold:
                cls.log_security_event(
                    'BRUTE_FORCE_DETECTED',
                    user=user,
                    ip_address=ip_address,
                    failed_attempts=failed_count,
                    time_window=time_window
                )
                return True
            
            return False
            
        except Exception as e:
            security_logger.error(f"Brute force detection error: {str(e)}")
            return False
    
    @classmethod
    def detect_suspicious_login(cls, user: User, request) -> Tuple[bool, List[str]]:
        """
        Detect suspicious login patterns
        """
        suspicion_factors = []
        
        try:
            ip_address = cls._extract_ip_address(request)
            user_agent = cls._extract_user_agent(request)
            device_fingerprint = cls._extract_device_fingerprint(request)
            
            # Check for new location
            if cls._is_new_location(user, ip_address):
                suspicion_factors.append("New geographic location")
            
            # Check for new device
            if cls._is_new_device(user, device_fingerprint):
                suspicion_factors.append("New device or browser")
            
            # Check for unusual time
            if cls._is_unusual_time(user):
                suspicion_factors.append("Unusual login time")
            
            # Check for rapid location changes
            if cls._rapid_location_change(user, ip_address):
                suspicion_factors.append("Rapid location change detected")
            
            # Check for suspicious user agent
            if cls._is_suspicious_user_agent(user_agent):
                suspicion_factors.append("Suspicious browser or automation detected")
            
            is_suspicious = len(suspicion_factors) >= 2
            
            if is_suspicious:
                cls.log_security_event(
                    'LOGIN_SUSPICIOUS',
                    user=user,
                    request=request,
                    suspicion_factors=suspicion_factors
                )
            
            return is_suspicious, suspicion_factors
            
        except Exception as e:
            security_logger.error(f"Suspicious login detection error: {str(e)}")
            return False, []
    
    @classmethod
    def monitor_mfa_security(cls, user: User, device: TOTPDevice = None, 
                           backup_code: BackupCode = None) -> Dict[str, Any]:
        """
        Monitor MFA security metrics
        """
        try:
            mfa_stats = {
                'user_id': user.id,
                'total_devices': user.totp_devices.count(),
                'active_devices': user.totp_devices.filter(is_active=True).count(),
                'locked_devices': user.totp_devices.filter(
                    lockout_until__gt=timezone.now()
                ).count(),
                'backup_codes_remaining': user.backup_codes.filter(
                    is_used=False
                ).count(),
                'recent_mfa_failures': cls._get_recent_mfa_failures(user),
                'mfa_enrollment_date': user.totp_devices.first().created_at if user.totp_devices.exists() else None,
                'last_successful_mfa': cls._get_last_successful_mfa(user)
            }
            
            # Check for MFA security concerns
            security_concerns = []
            
            if mfa_stats['locked_devices'] > 0:
                security_concerns.append("MFA devices locked out")
            
            if mfa_stats['backup_codes_remaining'] <= 2:
                security_concerns.append("Low backup codes remaining")
            
            if mfa_stats['recent_mfa_failures'] >= 5:
                security_concerns.append("High MFA failure rate")
            
            mfa_stats['security_concerns'] = security_concerns
            
            return mfa_stats
            
        except Exception as e:
            security_logger.error(f"MFA security monitoring error: {str(e)}")
            return {}
    
    @classmethod
    def generate_security_report(cls, user: User = None, days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive security report
        """
        try:
            since = timezone.now() - timedelta(days=days)
            
            base_query = SecurityEvent.objects.filter(timestamp__gte=since)
            if user:
                base_query = base_query.filter(user=user)
            
            report = {
                'report_period_days': days,
                'generated_at': timezone.now(),
                'user_scope': user.username if user else 'All users',
                
                # Event statistics
                'total_events': base_query.count(),
                'events_by_type': dict(
                    base_query.values('event_type').annotate(
                        count=models.Count('id')
                    ).values_list('event_type', 'count')
                ),
                'events_by_risk_level': dict(
                    base_query.values('risk_level').annotate(
                        count=models.Count('id')
                    ).values_list('risk_level', 'count')
                ),
                
                # Security metrics
                'successful_logins': base_query.filter(
                    event_type='LOGIN_SUCCESS'
                ).count(),
                'failed_logins': base_query.filter(
                    event_type='LOGIN_FAILED'
                ).count(),
                'mfa_events': base_query.filter(
                    event_type__startswith='MFA_'
                ).count(),
                'suspicious_activities': base_query.filter(
                    risk_level__gte=cls.RISK_LEVELS['HIGH']
                ).count(),
                
                # Geographic analysis
                'unique_locations': base_query.exclude(
                    location_info__isnull=True
                ).values('location_info__country').distinct().count(),
                'top_countries': list(
                    base_query.exclude(location_info__isnull=True)
                    .values('location_info__country')
                    .annotate(count=models.Count('id'))
                    .order_by('-count')[:10]
                ),
                
                # Device analysis
                'unique_devices': base_query.exclude(
                    device_fingerprint__isnull=True
                ).values('device_fingerprint').distinct().count(),
                
                # Time analysis
                'peak_activity_hour': cls._get_peak_activity_hour(base_query),
                
                # Recent high-risk events
                'recent_high_risk_events': list(
                    base_query.filter(
                        risk_level__gte=cls.RISK_LEVELS['HIGH']
                    ).order_by('-timestamp')[:10].values(
                        'event_type', 'timestamp', 'ip_address', 
                        'risk_level', 'event_description'
                    )
                )
            }
            
            return report
            
        except Exception as e:
            security_logger.error(f"Security report generation error: {str(e)}")
            return {'error': 'Failed to generate security report'}
    
    @classmethod
    def check_session_security(cls, session_info: SessionInfo) -> Dict[str, Any]:
        """
        Check session security status
        """
        try:
            security_status = {
                'session_id': str(session_info.session_id),
                'is_active': session_info.is_active,
                'created_at': session_info.created_at,
                'last_activity': session_info.last_activity,
                'ip_address': session_info.ip_address,
                'device_fingerprint': session_info.device_fingerprint,
                'is_suspicious': False,
                'security_flags': []
            }
            
            # Check for suspicious patterns
            if session_info.last_activity < timezone.now() - timedelta(hours=24):
                security_status['security_flags'].append("Long inactive session")
            
            # Check for IP changes
            recent_events = SecurityEvent.objects.filter(
                user=session_info.user,
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).exclude(ip_address=session_info.ip_address)
            
            if recent_events.exists():
                security_status['security_flags'].append("IP address changes detected")
                security_status['is_suspicious'] = True
            
            return security_status
            
        except Exception as e:
            security_logger.error(f"Session security check error: {str(e)}")
            return {'error': 'Failed to check session security'}
    
    # Helper methods
    @staticmethod
    def _extract_ip_address(request) -> Optional[str]:
        """Extract real IP address from request"""
        if not request:
            return None
        
        # Check for forwarded IP
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            ip = forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Validate IP address
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            return None
    
    @staticmethod
    def _extract_user_agent(request) -> Optional[str]:
        """Extract user agent from request"""
        return request.META.get('HTTP_USER_AGENT') if request else None
    
    @staticmethod
    def _extract_device_fingerprint(request) -> Optional[str]:
        """Generate device fingerprint"""
        if not request:
            return None
        
        fingerprint_data = [
            request.META.get('HTTP_USER_AGENT', ''),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('HTTP_ACCEPT_ENCODING', ''),
            request.META.get('HTTP_ACCEPT', '')
        ]
        
        fingerprint_string = '|'.join(fingerprint_data)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
    
    @classmethod
    def _calculate_risk_level(cls, event_type: str, user: Optional[User], 
                             ip_address: str = None, **kwargs) -> int:
        """Calculate risk level for security event"""
        risk = cls.RISK_LEVELS['LOW']
        
        # High-risk event types
        high_risk_events = [
            'LOGIN_SUSPICIOUS', 'BRUTE_FORCE_DETECTED', 'TOKEN_REUSE_DETECTED',
            'MFA_LOCKOUT', 'CONCURRENT_SESSION_LIMIT'
        ]
        
        if event_type in high_risk_events:
            risk = cls.RISK_LEVELS['HIGH']
        
        # Critical event types
        critical_events = ['TOKEN_FAMILY_INVALIDATED', 'ADMIN_ACTION']
        
        if event_type in critical_events:
            risk = cls.RISK_LEVELS['CRITICAL']
        
        # Additional risk factors
        if kwargs.get('failed_attempts', 0) > 10:
            risk = max(risk, cls.RISK_LEVELS['HIGH'])
        
        if kwargs.get('suspicion_factors'):
            risk = max(risk, cls.RISK_LEVELS['MEDIUM'])
        
        return risk
    
    @staticmethod
    def _prepare_metadata(request, **kwargs) -> Dict[str, Any]:
        """Prepare metadata for security event"""
        metadata = dict(kwargs)
        
        if request:
            metadata.update({
                'path': request.path,
                'method': request.method,
                'query_params': dict(request.GET),
                'content_type': request.content_type
            })
        
        # Remove sensitive data
        sensitive_keys = ['password', 'token', 'secret', 'key']
        for key in list(metadata.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                metadata[key] = '[REDACTED]'
        
        return metadata
    
    @staticmethod
    def _get_location_info(ip_address: str) -> Optional[Dict[str, str]]:
        """Get location information for IP address"""
        try:
            g = GeoIP2()
            city_info = g.city(ip_address)
            country_info = g.country(ip_address)
            
            return {
                'city': city_info.get('city', ''),
                'country': country_info.get('country_name', ''),
                'country_code': country_info.get('country_code', ''),
                'timezone': city_info.get('time_zone', '')
            }
        except Exception:
            return None
    
    @classmethod
    def _check_automated_responses(cls, security_event: 'SecurityEvent'):
        """Check for automated security responses"""
        if security_event.risk_level >= cls.RISK_LEVELS['HIGH']:
            # Cache high-risk event for monitoring
            cache.set(
                f"high_risk_event:{security_event.id}",
                {
                    'event_type': security_event.event_type,
                    'user_id': security_event.user.id if security_event.user else None,
                    'timestamp': security_event.timestamp.isoformat()
                },
                timeout=86400  # 24 hours
            )
        
        # Additional automated responses can be added here
        # e.g., email notifications, Slack alerts, etc.
    
    # Additional helper methods for suspicious activity detection
    @staticmethod
    def _is_new_location(user: User, ip_address: str) -> bool:
        """Check if login is from a new location"""
        if not ip_address:
            return False
        
        # Check recent successful logins from different locations
        recent_logins = SecurityEvent.objects.filter(
            user=user,
            event_type='LOGIN_SUCCESS',
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).exclude(ip_address=ip_address)
        
        return recent_logins.exists()
    
    @staticmethod
    def _is_new_device(user: User, device_fingerprint: str) -> bool:
        """Check if login is from a new device"""
        if not device_fingerprint:
            return False
        
        recent_sessions = SessionInfo.objects.filter(
            user=user,
            device_fingerprint=device_fingerprint,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        return not recent_sessions.exists()
    
    @staticmethod
    def _is_unusual_time(user: User) -> bool:
        """Check if login time is unusual for user"""
        current_hour = timezone.now().hour
        
        # Get user's typical login hours
        typical_hours = SecurityEvent.objects.filter(
            user=user,
            event_type='LOGIN_SUCCESS',
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).extra(
            select={'hour': 'EXTRACT(hour FROM timestamp)'}
        ).values_list('hour', flat=True)
        
        if not typical_hours:
            return False
        
        # Simple heuristic: unusual if current hour not in typical hours
        return current_hour not in set(typical_hours)
    
    @staticmethod
    def _rapid_location_change(user: User, current_ip: str) -> bool:
        """Check for rapid location changes"""
        recent_event = SecurityEvent.objects.filter(
            user=user,
            event_type='LOGIN_SUCCESS',
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).exclude(ip_address=current_ip).first()
        
        return recent_event is not None
    
    @staticmethod
    def _is_suspicious_user_agent(user_agent: str) -> bool:
        """Check for suspicious user agents"""
        if not user_agent:
            return True
        
        # Parse user agent
        parsed = parse_user_agent(user_agent)
        
        # Check for automation tools
        automation_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'automated',
            'python-requests', 'curl', 'wget'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in automation_patterns)
    
    @staticmethod
    def _get_recent_mfa_failures(user: User, hours: int = 24) -> int:
        """Get recent MFA failures for user"""
        return SecurityEvent.objects.filter(
            user=user,
            event_type='MFA_FAILED',
            timestamp__gte=timezone.now() - timedelta(hours=hours)
        ).count()
    
    @staticmethod
    def _get_last_successful_mfa(user: User) -> Optional[datetime]:
        """Get timestamp of last successful MFA"""
        event = SecurityEvent.objects.filter(
            user=user,
            event_type='MFA_SUCCESS'
        ).order_by('-timestamp').first()
        
        return event.timestamp if event else None
    
    @staticmethod
    def _get_peak_activity_hour(queryset) -> Optional[int]:
        """Get peak activity hour from events"""
        try:
            from django.db.models import Count
            
            hourly_stats = queryset.extra(
                select={'hour': 'EXTRACT(hour FROM timestamp)'}
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('-count')
            
            return hourly_stats.first()['hour'] if hourly_stats else None
        except Exception:
            return None


class SecurityAlerting:
    """
    Security alerting and notification system
    """
    
    @staticmethod
    def send_security_alert(event_type: str, user: User, details: Dict[str, Any]):
        """
        Send security alert (implement based on your notification system)
        """
        # This would integrate with your notification system
        # e.g., email, Slack, SMS, etc.
        security_logger.warning(
            f"SECURITY ALERT: {event_type} for user {user.username} - {details}"
        )
    
    @staticmethod
    def generate_daily_security_digest() -> Dict[str, Any]:
        """
        Generate daily security digest
        """
        yesterday = timezone.now() - timedelta(days=1)
        
        digest = {
            'date': yesterday.date(),
            'total_events': SecurityEvent.objects.filter(
                timestamp__gte=yesterday
            ).count(),
            'high_risk_events': SecurityEvent.objects.filter(
                timestamp__gte=yesterday,
                risk_level__gte=SecurityMonitoringService.RISK_LEVELS['HIGH']
            ).count(),
            'failed_logins': SecurityEvent.objects.filter(
                timestamp__gte=yesterday,
                event_type='LOGIN_FAILED'
            ).count(),
            'new_users': User.objects.filter(
                date_joined__gte=yesterday
            ).count()
        }
        
        return digest