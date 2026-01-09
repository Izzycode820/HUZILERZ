"""
Batch Operations Views
Handle bulk operations for subscriptions, payments, and analytics
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.core.exceptions import ValidationError
import logging

from ..models import SubscriptionPlan, Subscription
from ..services.discount_service import DiscountService
from ..utils.rate_limiter import rate_limited_batch

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limited_batch
def batch_discount_calculation(request):
    """
    Calculate discounts for multiple subscription plans
    Useful for comparison tables and upgrade flows
    """
    try:
        plans = request.data.get('plans', [])
        template_purchase = request.data.get('template_purchase')
        seasonal_code = request.data.get('seasonal_code')
        
        if not plans:
            return Response({
                'error': 'Plans array required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(plans) > 10:
            return Response({
                'error': 'Maximum 10 plans per batch request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        
        with transaction.atomic():
            for plan_tier in plans:
                try:
                    subscription_plan = SubscriptionPlan.objects.get(
                        tier=plan_tier, 
                        is_active=True
                    )
                    
                    discount_result = DiscountService.calculate_yearly_discount(
                        subscription_plan.price_fcfa, subscription_plan.tier
                    )
                    
                    results.append({
                        'plan_tier': plan_tier,
                        'success': True,
                        'discount': {
                            'original_amount': float(subscription_plan.price_fcfa),
                            'final_amount': float(discount_result['discounted_price']),
                            'discount_amount': float(discount_result['discount_amount']),
                            'discount_percentage': float(discount_result['discount_percentage']),
                            'discount_name': discount_result.get('discount_name', 'Yearly Billing')
                        }
                    })
                    
                except SubscriptionPlan.DoesNotExist:
                    results.append({
                        'plan_tier': plan_tier,
                        'success': False,
                        'error': f'Plan {plan_tier} not found'
                    })
                except Exception as e:
                    results.append({
                        'plan_tier': plan_tier,
                        'success': False,
                        'error': str(e)
                    })
        
        return Response({
            'batch_results': results,
            'total_plans': len(plans),
            'successful_calculations': len([r for r in results if r['success']]),
            'failed_calculations': len([r for r in results if not r['success']])
        })
        
    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'batch discount calculation', request.user.id
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limited_batch
def batch_payment_status_check(request):
    """
    Check status of multiple payments
    Useful for payment history and reconciliation
    """
    try:
        payment_ids = request.data.get('payment_ids', [])
        
        if not payment_ids:
            return Response({
                'error': 'payment_ids array required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(payment_ids) > 50:
            return Response({
                'error': 'Maximum 50 payments per batch request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get payments belonging to the user
        payments = Payment.objects.filter(
            id__in=payment_ids,
            user=request.user
        )
        
        results = []
        found_payment_ids = set()
        
        for payment in payments:
            found_payment_ids.add(str(payment.id))
            results.append({
                'payment_id': str(payment.id),
                'status': payment.status,
                'amount': float(payment.amount),
                'payment_type': payment.payment_type,
                'gateway_used': payment.gateway_used,
                'created_at': payment.created_at.isoformat(),
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
                'can_retry': payment.can_retry,
                'success': True
            })
        
        # Add not found payments
        for payment_id in payment_ids:
            if payment_id not in found_payment_ids:
                results.append({
                    'payment_id': payment_id,
                    'success': False,
                    'error': 'Payment not found or access denied'
                })
        
        return Response({
            'batch_results': results,
            'total_requested': len(payment_ids),
            'found_payments': len([r for r in results if r['success']]),
            'not_found_payments': len([r for r in results if not r['success']])
        })
        
    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'batch payment status check', request.user.id
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limited_batch
def batch_feature_availability_check(request):
    """
    Check feature availability for multiple features
    Useful for UI state management and feature gates
    """
    try:
        features = request.data.get('features', [])
        
        if not features:
            return Response({
                'error': 'features array required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(features) > 20:
            return Response({
                'error': 'Maximum 20 features per batch request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        results = {}
        
        # Get user subscription
        try:
            subscription = user.subscription
            current_tier = subscription.plan.tier
        except (AttributeError, Subscription.DoesNotExist):
            current_tier = 'free'
            subscription = None
        
        # Check each feature
        from ..middleware.feature_gating import FeatureGatingMiddleware
        middleware = FeatureGatingMiddleware(None)
        
        for feature_name in features:
            if feature_name in middleware.FEATURE_GATES:
                gate_config = middleware.FEATURE_GATES[feature_name]
                required_tiers = gate_config.get('required_tiers', [])
                
                available = current_tier in required_tiers
                
                # Check usage limits if applicable
                usage_info = None
                if available and gate_config.get('usage_limits') and subscription:
                    from ..middleware.feature_gating import FeatureUsageTracker
                    usage_info = FeatureUsageTracker.get_feature_usage(
                        user, 
                        gate_config.get('feature_group', feature_name)
                    )
                    
                    if usage_info and usage_info['is_over_limit']:
                        available = False
                
                results[feature_name] = {
                    'available': available,
                    'current_tier': current_tier,
                    'required_tiers': required_tiers,
                    'usage_info': usage_info,
                    'upgrade_required': not available,
                    'minimum_required_tier': min(required_tiers) if required_tiers else None
                }
            else:
                results[feature_name] = {
                    'available': True,  # Unknown features are available by default
                    'current_tier': current_tier,
                    'required_tiers': [],
                    'upgrade_required': False
                }
        
        return Response({
            'feature_availability': results,
            'current_subscription_tier': current_tier,
            'has_active_subscription': subscription is not None,
            'total_features_checked': len(features)
        })
        
    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'batch feature availability check', request.user.id
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limited_batch
def batch_usage_analytics(request):
    """
    Get usage analytics for multiple resource types
    Useful for dashboard analytics and usage reports
    """
    try:
        resource_types = request.data.get('resource_types', [])
        date_range = request.data.get('date_range', 30)  # days
        
        if not resource_types:
            resource_types = ['storage_gb', 'bandwidth_gb', 'sites_count', 'custom_domains']
        
        if len(resource_types) > 10:
            return Response({
                'error': 'Maximum 10 resource types per batch request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        try:
            subscription = user.subscription
        except (AttributeError, Subscription.DoesNotExist):
            return Response({
                'error': 'No active subscription found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get usage records
        from datetime import timedelta
        from django.utils import timezone
        from ..models import UsageRecord
        
        start_date = timezone.now() - timedelta(days=date_range)
        
        usage_data = {}
        
        for resource_type in resource_types:
            # Get latest usage record for this resource
            latest_usage = UsageRecord.objects.filter(
                user=user,
                subscription=subscription,
                metric_type=resource_type,
                recorded_at__gte=start_date
            ).order_by('-recorded_at').first()
            
            if latest_usage:
                usage_data[resource_type] = {
                    'current_usage': float(latest_usage.current_usage),
                    'tier_limit': float(latest_usage.tier_limit),
                    'usage_percentage': float(latest_usage.usage_percentage),
                    'limit_exceeded': latest_usage.limit_exceeded,
                    'approaching_limit': latest_usage.is_approaching_limit,
                    'remaining_allowance': float(latest_usage.remaining_allowance),
                    'last_updated': latest_usage.recorded_at.isoformat()
                }
            else:
                # No usage data found, provide defaults
                tier_limit = getattr(subscription.plan, resource_type, 0)
                usage_data[resource_type] = {
                    'current_usage': 0.0,
                    'tier_limit': float(tier_limit),
                    'usage_percentage': 0.0,
                    'limit_exceeded': False,
                    'approaching_limit': False,
                    'remaining_allowance': float(tier_limit),
                    'last_updated': None
                }
        
        return Response({
            'usage_analytics': usage_data,
            'subscription_tier': subscription.plan.tier,
            'date_range_days': date_range,
            'total_resource_types': len(resource_types)
        })
        
    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'batch usage analytics', request.user.id
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_subscription_comparison(request):
    """
    Compare multiple subscription plans with current user context
    Useful for upgrade decision flows and plan comparison tables
    """
    try:
        target_plans = request.data.get('plans', ['free', 'beginning', 'pro', 'enterprise'])
        include_pricing = request.data.get('include_pricing', True)
        include_features = request.data.get('include_features', True)
        include_discounts = request.data.get('include_discounts', True)
        
        user = request.user
        current_tier = 'free'
        
        try:
            subscription = user.subscription
            current_tier = subscription.plan.tier
        except (AttributeError, Subscription.DoesNotExist):
            subscription = None
        
        comparison_data = {
            'current_tier': current_tier,
            'plans': {},
            'recommendations': []
        }
        
        for plan_tier in target_plans:
            try:
                plan = SubscriptionPlan.objects.get(tier=plan_tier, is_active=True)
                
                plan_data = {
                    'tier': plan.tier,
                    'name': plan.name,
                    'description': plan.description,
                    'is_current_plan': plan.tier == current_tier,
                    'is_upgrade': plan.price_fcfa > (subscription.plan.price_fcfa if subscription else 0),
                    'is_downgrade': subscription and plan.price_fcfa < subscription.plan.price_fcfa
                }
                
                if include_pricing:
                    plan_data['pricing'] = {
                        'price_fcfa': int(plan.price_fcfa),
                        'price_usd': float(plan.price_usd) if plan.price_usd else 0,
                        'display': f"{int(plan.price_fcfa):,} FCFA/month" if plan.price_fcfa > 0 else "Free Forever"
                    }
                    
                    if include_discounts and plan.tier != 'free':
                        discount_result = DiscountCalculator.calculate_subscription_discount(
                            user=user,
                            subscription_plan=plan
                        )
                        plan_data['discount'] = {
                            'available': len(discount_result.get('applied_discounts', [])) > 0,
                            'original_price': float(discount_result['original_amount']),
                            'discounted_price': float(discount_result['final_amount']),
                            'savings': float(discount_result['total_discount']),
                            'discount_percentage': float(discount_result['discount_percentage'])
                        }
                
                if include_features:
                    plan_data['features'] = {
                        'deployment_allowed': plan.deployment_allowed,
                        'max_workspaces': plan.max_workspaces,
                        'sites_limit': plan.sites_limit,
                        'storage_gb': plan.storage_gb,
                        'bandwidth_gb': plan.bandwidth_gb,
                        'custom_domains': plan.custom_domains,
                        'analytics_level': plan.analytics_level,
                        'white_label_enabled': plan.white_label_enabled,
                        'dedicated_support': plan.dedicated_support
                    }
                
                comparison_data['plans'][plan.tier] = plan_data
                
            except SubscriptionPlan.DoesNotExist:
                comparison_data['plans'][plan_tier] = {
                    'error': f'Plan {plan_tier} not found'
                }
        
        # Add recommendations based on current usage and tier
        if current_tier == 'free' and subscription:
            comparison_data['recommendations'].append({
                'type': 'upgrade',
                'target_tier': 'beginning',
                'reason': 'Enable website deployment',
                'benefits': ['Deploy your first website', 'Custom domain included']
            })
        elif current_tier == 'beginning':
            comparison_data['recommendations'].append({
                'type': 'upgrade',
                'target_tier': 'pro',
                'reason': 'Scale your business',
                'benefits': ['Multiple website deployments', 'Analytics insights', 'Higher limits']
            })
        
        return Response(comparison_data)
        
    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'batch subscription comparison', request.user.id
        )