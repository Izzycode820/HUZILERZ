"""
Security and Risk Assessment Service
"""
from datetime import timedelta
from django.utils import timezone
from authentication.models import SecurityEvent


class SecurityService:
    """Security and risk assessment service"""
    
    @staticmethod
    def assess_login_risk(user, ip_address, device_info):
        """Assess risk level for login attempt"""
        risk_score = 0
        risk_factors = []
        
        # Check IP history
        recent_logins = SecurityEvent.objects.filter(
            user=user,
            event_type='login_success',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).values('ip_address').distinct()
        
        known_ips = [event['ip_address'] for event in recent_logins]
        
        if ip_address not in known_ips:
            risk_score += 30
            risk_factors.append('New IP address')
        
        # Check failed login attempts
        recent_failures = SecurityEvent.objects.filter(
            ip_address=ip_address,
            event_type='login_failed',
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_failures >= 3:
            risk_score += 50
            risk_factors.append('Multiple recent failures from this IP')
        
        # Check time of day (simple heuristic)
        current_hour = timezone.now().hour
        if current_hour < 6 or current_hour > 22:
            risk_score += 10
            risk_factors.append('Unusual login time')
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'critical'
        elif risk_score >= 40:
            risk_level = 'high'
        elif risk_score >= 20:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'requires_additional_verification': risk_score >= 40
        }
    
    @staticmethod
    def check_account_lockout(user, ip_address=None):
        """Check if account should be locked due to failed attempts"""
        # Check failed attempts for user in last hour
        user_failures = SecurityEvent.objects.filter(
            user=user,
            event_type='login_failed',
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        # Check failed attempts from IP in last hour
        ip_failures = 0
        if ip_address:
            ip_failures = SecurityEvent.objects.filter(
                ip_address=ip_address,
                event_type='login_failed',
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
        
        return {
            'should_lock_user': user_failures >= 5,
            'should_block_ip': ip_failures >= 10,
            'user_failure_count': user_failures,
            'ip_failure_count': ip_failures
        }
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def log_security_event(event_type, user=None, description="", risk_level=1, 
                          ip_address=None, user_agent="", metadata=None):
        """Log a security event"""
        # Convert string risk level to integer
        if isinstance(risk_level, str):
            risk_level_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            risk_level = risk_level_map.get(risk_level.lower(), 1)
        
        return SecurityEvent.log_event(
            event_type=event_type,
            user=user,
            description=description,
            risk_level=risk_level,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )