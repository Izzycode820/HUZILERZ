"""
Comprehensive monitoring service for subscription system
Provides real-time metrics for super admin dashboard
"""
from django.core.cache import cache
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict
import logging
import json
from typing import Dict, List, Any, Optional

from ..models import Subscription, Payment, PaymentMethod, SubscriptionPlan
from ..utils.rate_limiter import RateLimitMonitor

logger = logging.getLogger(__name__)


class SubscriptionMonitoringService:
    """
    Central monitoring service for subscription system health and metrics
    Designed for super admin dashboard integration
    """
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """
        Get comprehensive system health status
        Returns real-time health metrics for dashboard
        """
        try:
            # Gateway health
            from ..gateways.fapshi import FapshiPaymentService
            gateway_status = FapshiPaymentService.get_gateway_status()
            
            # Database health
            db_health = SubscriptionMonitoringService._check_database_health()
            
            # Cache health
            cache_health = SubscriptionMonitoringService._check_cache_health()
            
            # Rate limiting health
            rate_limit_health = SubscriptionMonitoringService._get_rate_limit_health()
            
            # Overall system status
            all_healthy = (
                gateway_status.get('configured', False) and
                db_health['healthy'] and
                cache_health['healthy'] and
                rate_limit_health['healthy']
            )
            
            return {
                'overall_status': 'healthy' if all_healthy else 'degraded',
                'timestamp': timezone.now().isoformat(),
                'components': {
                    'payment_gateway': {
                        'status': 'healthy' if gateway_status.get('configured') else 'unhealthy',
                        'details': gateway_status
                    },
                    'database': db_health,
                    'cache': cache_health,
                    'rate_limiting': rate_limit_health
                }
            }
            
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return {
                'overall_status': 'error',
                'timestamp': timezone.now().isoformat(),
                'error': 'Health check failed'
            }
    
    @staticmethod
    def get_payment_metrics(hours=24) -> Dict[str, Any]:
        """
        Get payment processing metrics for dashboard
        """
        try:
            since = timezone.now() - timedelta(hours=hours)
            
            # Payment volume metrics
            payments = Payment.objects.filter(created_at__gte=since)
            
            # Success rates by status
            status_counts = payments.values('status').annotate(count=Count('id'))
            total_payments = payments.count()
            
            # Revenue metrics
            completed_payments = payments.filter(status='completed')
            total_revenue = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Gateway performance
            gateway_stats = payments.values('gateway_used').annotate(
                count=Count('id'),
                success_rate=Count('id', filter=Q(status='completed')) * 100.0 / Count('id')
            )
            
            # Payment method distribution
            method_stats = payments.exclude(payment_method__isnull=True).values(
                'payment_method__method_type'
            ).annotate(count=Count('id'))
            
            # Hourly breakdown for charts
            hourly_stats = SubscriptionMonitoringService._get_hourly_payment_stats(since)
            
            return {
                'period_hours': hours,
                'timestamp': timezone.now().isoformat(),
                'summary': {
                    'total_payments': total_payments,
                    'total_revenue_fcfa': float(total_revenue),
                    'success_rate': round(
                        (completed_payments.count() / total_payments * 100) if total_payments > 0 else 0, 2
                    )
                },
                'status_breakdown': list(status_counts),
                'gateway_performance': list(gateway_stats),
                'payment_methods': list(method_stats),
                'hourly_trends': hourly_stats
            }
            
        except Exception as e:
            logger.error(f"Payment metrics collection failed: {str(e)}")
            return {'error': 'Failed to collect payment metrics'}
    
    @staticmethod
    def get_subscription_metrics() -> Dict[str, Any]:
        """
        Get subscription tier distribution and growth metrics
        """
        try:
            # Active subscriptions by tier
            tier_distribution = Subscription.objects.filter(
                status='active'
            ).values('plan__tier').annotate(count=Count('id'))
            
            # Revenue by tier
            tier_revenue = {}
            for tier_data in tier_distribution:
                tier = tier_data['plan__tier']
                plan = SubscriptionPlan.objects.filter(tier=tier, is_active=True).first()
                if plan:
                    tier_revenue[tier] = {
                        'subscribers': tier_data['count'],
                        'monthly_revenue': float(plan.price_fcfa * tier_data['count']),
                        'plan_price': float(plan.price_fcfa)
                    }
            
            # Growth metrics (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            new_subscriptions = Subscription.objects.filter(
                created_at__gte=thirty_days_ago
            ).count()
            
            cancelled_subscriptions = Subscription.objects.filter(
                status='cancelled',
                updated_at__gte=thirty_days_ago
            ).count()
            
            # Churn rate calculation
            total_active = Subscription.objects.filter(status='active').count()
            churn_rate = (cancelled_subscriptions / total_active * 100) if total_active > 0 else 0
            
            return {
                'timestamp': timezone.now().isoformat(),
                'active_subscriptions': total_active,
                'tier_distribution': list(tier_distribution),
                'tier_revenue': tier_revenue,
                'growth_metrics': {
                    'new_subscriptions_30d': new_subscriptions,
                    'cancelled_subscriptions_30d': cancelled_subscriptions,
                    'churn_rate_percent': round(churn_rate, 2)
                },
                'total_monthly_revenue': sum(
                    tier['monthly_revenue'] for tier in tier_revenue.values()
                )
            }
            
        except Exception as e:
            logger.error(f"Subscription metrics collection failed: {str(e)}")
            return {'error': 'Failed to collect subscription metrics'}
    
    @staticmethod
    def get_rate_limit_analytics() -> Dict[str, Any]:
        """
        Get rate limiting analytics for monitoring abuse and system load
        """
        try:
            # Get rate limit metrics from our monitor
            metrics = RateLimitMonitor.get_rate_limit_metrics()
            
            # Real-time rate limit status
            current_limits = {}
            from ..utils.rate_limiter import payment_rate_limiter, fapshi_rate_limiter
            
            # Sample current rate limit status for different endpoints
            test_user_id = 1  # Sample user for testing limits
            payment_status = payment_rate_limiter.can_initiate_payment(test_user_id)
            status_check_status = payment_rate_limiter.can_check_status(test_user_id)
            webhook_status = payment_rate_limiter.can_process_webhook('test_ip')
            
            current_limits = {
                'payment_initiation': {
                    'can_proceed': payment_status[0],
                    'wait_time': payment_status[1] if not payment_status[0] else 0
                },
                'status_checks': {
                    'can_proceed': status_check_status[0],
                    'wait_time': status_check_status[1] if not status_check_status[0] else 0
                },
                'webhook_processing': {
                    'can_proceed': webhook_status[0],
                    'wait_time': webhook_status[1] if not webhook_status[0] else 0
                }
            }
            
            return {
                'timestamp': timezone.now().isoformat(),
                'rate_limit_hits_1h': metrics,
                'current_capacity': current_limits,
                'configured_limits': {
                    'payment_per_minute': 60,
                    'status_check_per_minute': 120,
                    'webhook_per_minute': 300
                }
            }
            
        except Exception as e:
            logger.error(f"Rate limit analytics collection failed: {str(e)}")
            return {'error': 'Failed to collect rate limit analytics'}
    
    @staticmethod
    def get_error_analytics(hours=24) -> Dict[str, Any]:
        """
        Get error analytics from logs and failed operations
        """
        try:
            since = timezone.now() - timedelta(hours=hours)
            
            # Payment failures
            failed_payments = Payment.objects.filter(
                status='failed',
                updated_at__gte=since
            )
            
            # Group by error types
            error_patterns = defaultdict(int)
            gateway_errors = defaultdict(int)
            
            for payment in failed_payments:
                if payment.failure_reason:
                    error_patterns[payment.failure_reason] += 1
                if payment.gateway_used:
                    gateway_errors[payment.gateway_used] += 1
            
            # Subscription creation failures
            recent_subscriptions = Subscription.objects.filter(created_at__gte=since)
            failed_subscriptions = recent_subscriptions.filter(status='failed').count()
            
            return {
                'period_hours': hours,
                'timestamp': timezone.now().isoformat(),
                'payment_failures': {
                    'total_count': failed_payments.count(),
                    'error_patterns': dict(error_patterns),
                    'gateway_breakdown': dict(gateway_errors)
                },
                'subscription_failures': {
                    'failed_count': failed_subscriptions,
                    'success_rate': round(
                        ((recent_subscriptions.count() - failed_subscriptions) / 
                         recent_subscriptions.count() * 100) if recent_subscriptions.count() > 0 else 100, 2
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error analytics collection failed: {str(e)}")
            return {'error': 'Failed to collect error analytics'}
    
    @staticmethod
    def _check_database_health() -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = timezone.now()
            
            # Simple query to test DB
            count = Subscription.objects.count()
            
            response_time = (timezone.now() - start_time).total_seconds()
            
            return {
                'healthy': response_time < 1.0,  # Consider healthy if under 1 second
                'response_time_ms': round(response_time * 1000, 2),
                'total_subscriptions': count
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    @staticmethod
    def _check_cache_health() -> Dict[str, Any]:
        """Check cache system health"""
        try:
            # Test cache write/read
            test_key = 'health_check_test'
            test_value = str(timezone.now().timestamp())
            
            cache.set(test_key, test_value, timeout=60)
            retrieved_value = cache.get(test_key)
            
            # Clean up
            cache.delete(test_key)
            
            return {
                'healthy': retrieved_value == test_value,
                'cache_backend': str(cache.__class__.__name__)
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    @staticmethod
    def _get_rate_limit_health() -> Dict[str, Any]:
        """Check rate limiting system health"""
        try:
            # Test rate limiter functionality
            from ..utils.rate_limiter import fapshi_rate_limiter
            
            test_result = fapshi_rate_limiter.can_make_request('health_check')
            
            return {
                'healthy': True,
                'rate_limiter_responsive': test_result[0],
                'wait_time': test_result[1]
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    @staticmethod
    def _get_hourly_payment_stats(since: datetime) -> List[Dict[str, Any]]:
        """Get hourly payment statistics for trend charts"""
        hourly_stats = []
        current_hour = since.replace(minute=0, second=0, microsecond=0)
        end_hour = timezone.now().replace(minute=0, second=0, microsecond=0)
        
        while current_hour <= end_hour:
            next_hour = current_hour + timedelta(hours=1)
            
            hour_payments = Payment.objects.filter(
                created_at__gte=current_hour,
                created_at__lt=next_hour
            )
            
            hourly_stats.append({
                'hour': current_hour.isoformat(),
                'total_payments': hour_payments.count(),
                'successful_payments': hour_payments.filter(status='completed').count(),
                'failed_payments': hour_payments.filter(status='failed').count(),
                'revenue_fcfa': float(
                    hour_payments.filter(status='completed').aggregate(
                        Sum('amount')
                    )['amount__sum'] or 0
                )
            })
            
            current_hour = next_hour
        
        return hourly_stats