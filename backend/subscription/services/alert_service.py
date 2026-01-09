"""
Comprehensive error logging and alerting system
Provides real-time alerts for critical subscription system events
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Alert categories for classification"""
    PAYMENT_FAILURE = "payment_failure"
    GATEWAY_DOWN = "gateway_down"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    SUBSCRIPTION_FAILURE = "subscription_failure"
    SECURITY_BREACH = "security_breach"
    SYSTEM_ERROR = "system_error"


class SubscriptionAlertService:
    """
    Central alerting service for subscription system
    Handles alert generation, deduplication, and notification
    """
    
    ALERT_THRESHOLDS = {
        AlertCategory.PAYMENT_FAILURE: {
            'count': 5,      # Alert after 5 failures in window
            'window_minutes': 15
        },
        AlertCategory.GATEWAY_DOWN: {
            'count': 1,      # Immediate alert
            'window_minutes': 5
        },
        AlertCategory.RATE_LIMIT_EXCEEDED: {
            'count': 10,     # Alert after 10 rate limit hits
            'window_minutes': 5
        },
        AlertCategory.CIRCUIT_BREAKER_OPEN: {
            'count': 1,      # Immediate alert
            'window_minutes': 1
        }
    }
    
    @classmethod
    def create_alert(
        cls,
        level: AlertLevel,
        category: AlertCategory,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        payment_id: Optional[str] = None
    ) -> bool:
        """
        Create new alert with deduplication
        
        Returns:
            True if alert was created (not deduplicated)
        """
        try:
            alert_data = {
                'level': level.value,
                'category': category.value,
                'message': message,
                'details': details or {},
                'user_id': user_id,
                'payment_id': payment_id,
                'timestamp': timezone.now().isoformat(),
                'source': 'subscription_system'
            }
            
            # Generate alert hash for deduplication
            alert_hash = cls._generate_alert_hash(level, category, message, details)
            
            # Check if this alert was recently sent
            if cls._is_duplicate_alert(alert_hash, category):
                logger.debug(f"Duplicate alert suppressed: {alert_hash}")
                return False
            
            # Store alert
            cls._store_alert(alert_data, alert_hash)
            
            # Send notifications based on level and category
            cls._send_notifications(alert_data)
            
            # Log structured alert
            cls._log_structured_alert(alert_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}")
            return False
    
    @classmethod
    def payment_failure_alert(
        cls, 
        payment_id: str, 
        user_id: int, 
        error_message: str,
        gateway: str = None
    ):
        """Create alert for payment failure"""
        details = {
            'payment_id': payment_id,
            'error_message': error_message,
            'gateway': gateway
        }
        
        cls.create_alert(
            AlertLevel.ERROR,
            AlertCategory.PAYMENT_FAILURE,
            f"Payment failed: {error_message[:100]}",
            details,
            user_id,
            payment_id
        )
    
    @classmethod
    def gateway_down_alert(cls, gateway_name: str, error_details: str):
        """Create alert for gateway outage"""
        cls.create_alert(
            AlertLevel.CRITICAL,
            AlertCategory.GATEWAY_DOWN,
            f"Payment gateway {gateway_name} is down",
            {'gateway': gateway_name, 'error': error_details}
        )
    
    @classmethod
    def rate_limit_alert(cls, endpoint: str, user_id: int = None, ip_address: str = None):
        """Create alert for rate limit exceeded"""
        details = {
            'endpoint': endpoint,
            'user_id': user_id,
            'ip_address': ip_address
        }
        
        cls.create_alert(
            AlertLevel.WARNING,
            AlertCategory.RATE_LIMIT_EXCEEDED,
            f"Rate limit exceeded on {endpoint}",
            details,
            user_id
        )
    
    @classmethod
    def circuit_breaker_alert(cls, circuit_name: str, failure_count: int):
        """Create alert for circuit breaker opening"""
        cls.create_alert(
            AlertLevel.CRITICAL,
            AlertCategory.CIRCUIT_BREAKER_OPEN,
            f"Circuit breaker {circuit_name} opened after {failure_count} failures",
            {'circuit_name': circuit_name, 'failure_count': failure_count}
        )
    
    @classmethod
    def security_alert(cls, event_type: str, details: Dict[str, Any]):
        """Create security-related alert"""
        cls.create_alert(
            AlertLevel.CRITICAL,
            AlertCategory.SECURITY_BREACH,
            f"Security event: {event_type}",
            details
        )
    
    @classmethod
    def get_recent_alerts(cls, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts for dashboard display"""
        try:
            alerts = []
            
            # Get alerts from cache (last 24 hours)
            for hour in range(hours):
                timestamp = timezone.now() - timedelta(hours=hour)
                hour_key = cls._get_hourly_alert_key(timestamp)
                hour_alerts = cache.get(hour_key, [])
                alerts.extend(hour_alerts)
            
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return alerts[:100]  # Limit to 100 most recent
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {str(e)}")
            return []
    
    @classmethod
    def get_alert_summary(cls, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for dashboard metrics"""
        try:
            alerts = cls.get_recent_alerts(hours)
            
            # Group by level and category
            level_counts = {}
            category_counts = {}
            
            for alert in alerts:
                level = alert.get('level', 'unknown')
                category = alert.get('category', 'unknown')
                
                level_counts[level] = level_counts.get(level, 0) + 1
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Calculate alert rates
            total_alerts = len(alerts)
            critical_alerts = level_counts.get('critical', 0)
            error_alerts = level_counts.get('error', 0)
            
            return {
                'total_alerts': total_alerts,
                'critical_alerts': critical_alerts,
                'error_alerts': error_alerts,
                'alert_rate_per_hour': round(total_alerts / hours, 2) if hours > 0 else 0,
                'level_breakdown': level_counts,
                'category_breakdown': category_counts,
                'health_score': max(0, 100 - (critical_alerts * 20) - (error_alerts * 5)),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert summary: {str(e)}")
            return {'error': 'Failed to get alert summary'}
    
    @classmethod
    def _generate_alert_hash(
        cls, 
        level: AlertLevel, 
        category: AlertCategory, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate hash for alert deduplication"""
        # Create hash based on level, category, and key details
        hash_input = f"{level.value}:{category.value}:{message}"
        
        if details:
            # Include critical details but ignore timestamps
            filtered_details = {
                k: v for k, v in details.items() 
                if k not in ['timestamp', 'created_at']
            }
            hash_input += f":{json.dumps(filtered_details, sort_keys=True)}"
        
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    @classmethod
    def _is_duplicate_alert(cls, alert_hash: str, category: AlertCategory) -> bool:
        """Check if alert is a duplicate within threshold window"""
        threshold = cls.ALERT_THRESHOLDS.get(category, {
            'count': 1,
            'window_minutes': 15
        })
        
        window_key = f"alert_dedup:{alert_hash}"
        last_sent = cache.get(window_key)
        
        if last_sent:
            time_diff = (timezone.now() - datetime.fromisoformat(last_sent)).total_seconds()
            if time_diff < (threshold['window_minutes'] * 60):
                return True
        
        # Mark this alert as sent
        cache.set(window_key, timezone.now().isoformat(), timeout=threshold['window_minutes'] * 60)
        return False
    
    @classmethod
    def _store_alert(cls, alert_data: Dict[str, Any], alert_hash: str):
        """Store alert in cache for retrieval"""
        timestamp = datetime.fromisoformat(alert_data['timestamp'])
        hour_key = cls._get_hourly_alert_key(timestamp)
        
        # Get existing alerts for this hour
        hour_alerts = cache.get(hour_key, [])
        
        # Add new alert with hash
        alert_data['alert_hash'] = alert_hash
        hour_alerts.append(alert_data)
        
        # Keep only last 50 alerts per hour to prevent memory issues
        if len(hour_alerts) > 50:
            hour_alerts = hour_alerts[-50:]
        
        # Store back in cache (expire after 48 hours)
        cache.set(hour_key, hour_alerts, timeout=48 * 3600)
    
    @classmethod
    def _get_hourly_alert_key(cls, timestamp: datetime) -> str:
        """Generate cache key for hourly alert storage"""
        hour_str = timestamp.strftime('%Y%m%d%H')
        return f"alerts:hour:{hour_str}"
    
    @classmethod
    def _send_notifications(cls, alert_data: Dict[str, Any]):
        """Send notifications for alert"""
        level = AlertLevel(alert_data['level'])
        category = AlertCategory(alert_data['category'])
        
        # Only send email notifications for critical alerts in production
        if level == AlertLevel.CRITICAL and not settings.DEBUG:
            cls._send_email_notification(alert_data)
        
        # Log all alerts to console/file
        cls._send_log_notification(alert_data)
    
    @classmethod
    def _send_email_notification(cls, alert_data: Dict[str, Any]):
        """Send email notification for critical alerts"""
        try:
            subject = f"[CRITICAL] {alert_data['message']}"
            
            body = f"""
Critical Alert from HUZILERZ Subscription System

Level: {alert_data['level'].upper()}
Category: {alert_data['category']}
Time: {alert_data['timestamp']}
Message: {alert_data['message']}

Details:
{json.dumps(alert_data.get('details', {}), indent=2)}

This alert requires immediate attention.
            """
            
            admin_emails = getattr(settings, 'SUBSCRIPTION_ADMIN_EMAILS', [])
            if admin_emails:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True
                )
                
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
    
    @classmethod
    def _send_log_notification(cls, alert_data: Dict[str, Any]):
        """Send alert to logging system"""
        level = AlertLevel(alert_data['level'])
        message = f"ALERT [{alert_data['category']}]: {alert_data['message']}"
        
        if level == AlertLevel.CRITICAL:
            logger.critical(message, extra={'alert_data': alert_data})
        elif level == AlertLevel.ERROR:
            logger.error(message, extra={'alert_data': alert_data})
        elif level == AlertLevel.WARNING:
            logger.warning(message, extra={'alert_data': alert_data})
        else:
            logger.info(message, extra={'alert_data': alert_data})
    
    @classmethod
    def _log_structured_alert(cls, alert_data: Dict[str, Any]):
        """Log structured alert data for analytics"""
        # Create structured log entry
        log_entry = {
            'event_type': 'subscription_alert',
            'alert_level': alert_data['level'],
            'alert_category': alert_data['category'],
            'message': alert_data['message'],
            'timestamp': alert_data['timestamp'],
            'details': alert_data.get('details', {})
        }
        
        # Log with structured format for log aggregation tools
        logger.info("STRUCTURED_ALERT", extra={'structured_data': log_entry})