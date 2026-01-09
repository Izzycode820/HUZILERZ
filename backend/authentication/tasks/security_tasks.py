"""
Security Monitoring Celery Tasks - Enterprise Automation
Automated security monitoring, alerting, and maintenance tasks
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Count, Q
from celery import shared_task
from django.core.cache import cache

from ..models import (
    SecurityEvent, SecurityAlert, SessionInfo, 
    ThreatIntelligence, SecurityMetrics
)
from ..services import SecurityMonitoringService

User = get_user_model()
logger = logging.getLogger('authentication.security.tasks')


@shared_task(bind=True, max_retries=3)
def analyze_security_events(self):
    """
    Analyze recent security events for patterns and threats
    """
    try:
        logger.info("Starting security events analysis")
        
        # Analyze events from the last hour
        since = timezone.now() - timedelta(hours=1)
        
        recent_events = SecurityEvent.objects.filter(
            timestamp__gte=since,
            is_processed=False
        ).order_by('timestamp')
        
        processed_count = 0
        alerts_created = 0
        
        for event in recent_events:
            try:
                # Check for brute force patterns
                if event.event_type == 'LOGIN_FAILED':
                    if SecurityMonitoringService.detect_brute_force(
                        user=event.user, 
                        ip_address=event.ip_address
                    ):
                        alert = SecurityAlert.objects.create(
                            alert_type='BRUTE_FORCE',
                            title=f'Brute force attack detected',
                            description=f'Multiple failed login attempts from {event.ip_address}',
                            severity='HIGH',
                            user=event.user,
                            alert_data={
                                'ip_address': event.ip_address,
                                'event_id': str(event.id),
                                'detection_time': timezone.now().isoformat()
                            }
                        )
                        alert.related_events.add(event)
                        alerts_created += 1
                
                # Check for suspicious login patterns
                if event.event_type == 'LOGIN_SUCCESS' and event.user:
                    is_suspicious, factors = SecurityMonitoringService.detect_suspicious_login(
                        event.user, 
                        None  # We don't have the request object in background task
                    )
                    
                    if is_suspicious:
                        alert = SecurityAlert.objects.create(
                            alert_type='SUSPICIOUS_LOGIN',
                            title=f'Suspicious login detected for {event.user.username}',
                            description=f'Login with suspicious patterns: {", ".join(factors)}',
                            severity='MEDIUM',
                            user=event.user,
                            alert_data={
                                'suspicion_factors': factors,
                                'ip_address': event.ip_address,
                                'location_info': event.location_info,
                                'event_id': str(event.id)
                            }
                        )
                        alert.related_events.add(event)
                        alerts_created += 1
                
                # Check against threat intelligence
                if event.ip_address:
                    threat_intel = ThreatIntelligence.objects.filter(
                        ioc_type='IP',
                        ioc_value=event.ip_address,
                        is_active=True
                    ).first()
                    
                    if threat_intel:
                        alert = SecurityAlert.objects.create(
                            alert_type='SYSTEM_ANOMALY',
                            title=f'Known threat IP detected: {event.ip_address}',
                            description=f'Event from known malicious IP: {threat_intel.description}',
                            severity='CRITICAL',
                            user=event.user,
                            alert_data={
                                'threat_intel_id': str(threat_intel.id),
                                'threat_type': threat_intel.threat_type,
                                'confidence': threat_intel.confidence,
                                'source': threat_intel.source
                            }
                        )
                        alert.related_events.add(event)
                        alerts_created += 1
                        
                        # Update threat intelligence last seen
                        threat_intel.update_last_seen()
                
                # Mark event as processed
                event.mark_processed()
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing security event {event.id}: {str(e)}")
                continue
        
        logger.info(f"Processed {processed_count} security events, created {alerts_created} alerts")
        
        return {
            'processed_events': processed_count,
            'alerts_created': alerts_created,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Security events analysis failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)  # Retry in 5 minutes


@shared_task(bind=True, max_retries=3)
def cleanup_expired_sessions(self):
    """
    Clean up expired sessions and log security events
    """
    try:
        logger.info("Starting expired sessions cleanup")
        
        # Find expired sessions
        expired_sessions = SessionInfo.objects.filter(
            is_active=True,
            expires_at__lt=timezone.now()
        )
        
        cleanup_count = 0
        
        for session in expired_sessions:
            try:
                # Log session expiration
                SecurityMonitoringService.log_security_event(
                    'SESSION_EXPIRED',
                    user=session.user,
                    session_id=str(session.session_id),
                    ip_address=session.ip_address,
                    expired_at=timezone.now().isoformat()
                )
                
                # Deactivate session
                session.is_active = False
                session.save(update_fields=['is_active'])
                
                cleanup_count += 1
                
            except Exception as e:
                logger.error(f"Error cleaning up session {session.session_id}: {str(e)}")
                continue
        
        logger.info(f"Cleaned up {cleanup_count} expired sessions")
        
        return {
            'cleaned_sessions': cleanup_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def generate_security_metrics(self):
    """
    Generate security metrics for dashboards and reporting
    """
    try:
        logger.info("Generating security metrics")
        
        now = timezone.now()
        
        # Generate hourly metrics
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        
        # Login metrics
        login_attempts = SecurityEvent.objects.filter(
            event_type__in=['LOGIN_SUCCESS', 'LOGIN_FAILED'],
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()
        
        successful_logins = SecurityEvent.objects.filter(
            event_type='LOGIN_SUCCESS',
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()
        
        failed_logins = SecurityEvent.objects.filter(
            event_type='LOGIN_FAILED',
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()
        
        # MFA metrics
        mfa_events = SecurityEvent.objects.filter(
            event_type__startswith='MFA_',
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()
        
        # High-risk events
        high_risk_events = SecurityEvent.objects.filter(
            risk_level__gte=SecurityMonitoringService.RISK_LEVELS['HIGH'],
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()
        
        # Unique users and IPs
        unique_users = SecurityEvent.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end,
            user__isnull=False
        ).values('user').distinct().count()
        
        unique_ips = SecurityEvent.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end,
            ip_address__isnull=False
        ).values('ip_address').distinct().count()
        
        # Create or update metrics
        metrics_data = [
            ('LOGIN_ATTEMPTS', login_attempts),
            ('LOGIN_SUCCESS', successful_logins),
            ('LOGIN_FAILED', failed_logins),
            ('MFA_USAGE', mfa_events),
            ('SUSPICIOUS_ACTIVITIES', high_risk_events),
            ('UNIQUE_USERS', unique_users),
            ('UNIQUE_IPS', unique_ips)
        ]
        
        created_metrics = 0
        
        for metric_type, count in metrics_data:
            metric, created = SecurityMetrics.objects.get_or_create(
                metric_type=metric_type,
                aggregation_period='HOURLY',
                period_start=hour_start,
                defaults={
                    'period_end': hour_end,
                    'count': count,
                    'metadata': {
                        'generated_at': now.isoformat(),
                        'period_duration_minutes': 60
                    }
                }
            )
            
            if not created:
                metric.count = count
                metric.updated_at = now
                metric.save()
            
            created_metrics += 1
        
        logger.info(f"Generated {created_metrics} security metrics for {hour_start}")
        
        return {
            'generated_metrics': created_metrics,
            'period': hour_start.isoformat(),
            'timestamp': now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Security metrics generation failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def monitor_concurrent_sessions(self):
    """
    Monitor for users exceeding concurrent session limits
    """
    try:
        logger.info("Monitoring concurrent sessions")
        
        # Get session limit from settings
        max_concurrent_sessions = getattr(settings, 'MAX_CONCURRENT_SESSIONS', 5)
        
        # Find users with too many active sessions
        users_with_excess_sessions = User.objects.annotate(
            active_session_count=Count('session_info', 
                filter=Q(
                    session_info__is_active=True,
                    session_info__expires_at__gt=timezone.now()
                )
            )
        ).filter(active_session_count__gt=max_concurrent_sessions)
        
        alerts_created = 0
        
        for user in users_with_excess_sessions:
            # Check if we already have a recent alert for this user
            recent_alert = SecurityAlert.objects.filter(
                alert_type='CONCURRENT_SESSION_LIMIT',
                user=user,
                created_at__gte=timezone.now() - timedelta(hours=1),
                status='OPEN'
            ).exists()
            
            if not recent_alert:
                alert = SecurityAlert.objects.create(
                    alert_type='CONCURRENT_SESSION_LIMIT',
                    title=f'User {user.username} exceeded concurrent session limit',
                    description=f'User has {user.active_session_count} active sessions (limit: {max_concurrent_sessions})',
                    severity='MEDIUM',
                    user=user,
                    alert_data={
                        'active_sessions': user.active_session_count,
                        'session_limit': max_concurrent_sessions,
                        'detection_time': timezone.now().isoformat()
                    }
                )
                
                # Log security event
                SecurityMonitoringService.log_security_event(
                    'CONCURRENT_SESSION_LIMIT',
                    user=user,
                    active_sessions=user.active_session_count,
                    session_limit=max_concurrent_sessions
                )
                
                alerts_created += 1
        
        logger.info(f"Created {alerts_created} concurrent session limit alerts")
        
        return {
            'alerts_created': alerts_created,
            'users_checked': users_with_excess_sessions.count(),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Concurrent session monitoring failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3) 
def update_threat_intelligence(self):
    """
    Update threat intelligence database from external sources
    """
    try:
        logger.info("Updating threat intelligence")
        
        # This is a placeholder for threat intel integration
        # In production, you would integrate with services like:
        # - AbuseIPDB
        # - VirusTotal
        # - AlienVault OTX
        # - Internal threat feeds
        
        updated_indicators = 0
        
        # Example: Mark old indicators as inactive
        old_indicators = ThreatIntelligence.objects.filter(
            is_active=True,
            last_seen__lt=timezone.now() - timedelta(days=30)
        )
        
        for indicator in old_indicators:
            indicator.is_active = False
            indicator.save(update_fields=['is_active'])
            updated_indicators += 1
        
        logger.info(f"Updated {updated_indicators} threat intelligence indicators")
        
        return {
            'updated_indicators': updated_indicators,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Threat intelligence update failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def generate_daily_security_digest(self):
    """
    Generate daily security digest and send notifications
    """
    try:
        logger.info("Generating daily security digest")
        
        yesterday = timezone.now() - timedelta(days=1)
        
        # Generate comprehensive digest
        digest = {
            'date': yesterday.date().isoformat(),
            'total_events': SecurityEvent.objects.filter(
                timestamp__gte=yesterday.replace(hour=0, minute=0, second=0),
                timestamp__lt=yesterday.replace(hour=23, minute=59, second=59)
            ).count(),
            
            'critical_alerts': SecurityAlert.objects.filter(
                severity='CRITICAL',
                created_at__gte=yesterday.replace(hour=0, minute=0, second=0),
                created_at__lt=yesterday.replace(hour=23, minute=59, second=59)
            ).count(),
            
            'high_risk_events': SecurityEvent.objects.filter(
                risk_level__gte=SecurityMonitoringService.RISK_LEVELS['HIGH'],
                timestamp__gte=yesterday.replace(hour=0, minute=0, second=0),
                timestamp__lt=yesterday.replace(hour=23, minute=59, second=59)
            ).count(),
            
            'failed_logins': SecurityEvent.objects.filter(
                event_type='LOGIN_FAILED',
                timestamp__gte=yesterday.replace(hour=0, minute=0, second=0),
                timestamp__lt=yesterday.replace(hour=23, minute=59, second=59)
            ).count(),
            
            'new_users': User.objects.filter(
                date_joined__gte=yesterday.replace(hour=0, minute=0, second=0),
                date_joined__lt=yesterday.replace(hour=23, minute=59, second=59)
            ).count(),
            
            'mfa_enrollments': SecurityEvent.objects.filter(
                event_type='MFA_SETUP',
                timestamp__gte=yesterday.replace(hour=0, minute=0, second=0),
                timestamp__lt=yesterday.replace(hour=23, minute=59, second=59)
            ).count()
        }
        
        # Cache digest for dashboard access
        cache.set(
            f"security_digest:{yesterday.date().isoformat()}",
            digest,
            timeout=86400 * 7  # Keep for a week
        )
        
        # Here you would typically send notifications
        # via email, Slack, etc. based on your notification system
        
        logger.info(f"Generated security digest for {yesterday.date()}")
        
        return digest
        
    except Exception as e:
        logger.error(f"Daily security digest generation failed: {str(e)}")
        raise self.retry(countdown=3600, exc=e)  # Retry in 1 hour


@shared_task(bind=True, max_retries=3)
def archive_old_security_events(self):
    """
    Archive old security events to maintain performance
    """
    try:
        logger.info("Archiving old security events")
        
        # Archive events older than configured retention period
        retention_days = getattr(settings, 'SECURITY_EVENT_RETENTION_DAYS', 90)
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # In production, you might move these to a separate archival table
        # or external storage instead of deleting
        old_events = SecurityEvent.objects.filter(
            timestamp__lt=cutoff_date,
            is_processed=True
        )
        
        archived_count = old_events.count()
        
        # Delete old events (in production, consider archiving instead)
        old_events.delete()
        
        # Also clean up old metrics
        old_metrics = SecurityMetrics.objects.filter(
            period_start__lt=cutoff_date
        )
        
        archived_metrics = old_metrics.count()
        old_metrics.delete()
        
        logger.info(f"Archived {archived_count} security events and {archived_metrics} metrics")
        
        return {
            'archived_events': archived_count,
            'archived_metrics': archived_metrics,
            'cutoff_date': cutoff_date.isoformat(),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Security event archival failed: {str(e)}")
        raise self.retry(countdown=3600, exc=e)


# Periodic task scheduling would be configured in your celery beat configuration
# Example celery beat schedule:
"""
CELERY_BEAT_SCHEDULE = {
    'analyze-security-events': {
        'task': 'authentication.tasks.security_tasks.analyze_security_events',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-expired-sessions': {
        'task': 'authentication.tasks.security_tasks.cleanup_expired_sessions',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'generate-security-metrics': {
        'task': 'authentication.tasks.security_tasks.generate_security_metrics',
        'schedule': crontab(minute=0),  # Every hour
    },
    'monitor-concurrent-sessions': {
        'task': 'authentication.tasks.security_tasks.monitor_concurrent_sessions',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'update-threat-intelligence': {
        'task': 'authentication.tasks.security_tasks.update_threat_intelligence',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'generate-daily-security-digest': {
        'task': 'authentication.tasks.security_tasks.generate_daily_security_digest',
        'schedule': crontab(minute=0, hour=1),  # Daily at 1 AM
    },
    'archive-old-security-events': {
        'task': 'authentication.tasks.security_tasks.archive_old_security_events',
        'schedule': crontab(minute=0, hour=2, day_of_week=0),  # Weekly on Sunday at 2 AM
    },
}
"""