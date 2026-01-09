"""
Hybrid Pricing API Views - Production Grade Implementation
Database-first with hardcoded fallback for maximum reliability and flexibility
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
import logging

from ..services.discount_service import DiscountService
from ..utils.error_handler import ProductionSafeErrorHandler

logger = logging.getLogger(__name__)

PLAN_METADATA_FALLBACK = {
    'free': {'tagline': 'Explore', 'description': 'Test the waters and get used to the system'},
    'beginning': {'tagline': 'Side Huzilerz', 'description': 'Become a Solopreneur'},
    'pro': {'tagline': 'Boss Huzilerz', 'description': 'Grow your business'},
    'enterprise': {'tagline': 'Host', 'description': 'Build your company'}
}

HARDCODED_FEATURE_MATRIX = [
    {
        'name': 'Core Features',
        'features': [
            {'name': 'Website Deployment', 'description': 'Deploy websites to production'},
            {'name': 'Custom Domains', 'description': 'Connect your own domain'},
            {'name': 'Storage', 'description': 'File and asset storage'},
            {'name': 'Bandwidth', 'description': 'Monthly traffic allowance'}
        ]
    },
    {
        'name': 'Advanced Features',
        'features': [
            {'name': 'Analytics', 'description': 'Traffic and performance insights'},
            {'name': 'White Label', 'description': 'Remove HUZILERZ branding'},
            {'name': 'API Access', 'description': 'Programmatic access to platform'},
            {'name': 'Workspaces', 'description': 'Separate project environments'}
        ]
    },
    {
        'name': 'Support & Service',
        'features': [
            {'name': 'Support Level', 'description': 'Customer support tier'},
            {'name': 'Priority Support', 'description': 'Faster response times'}
        ]
    }
]

@api_view(['GET'])
@permission_classes([AllowAny])
def get_pricing_plans(request):
    """
    Hybrid pricing plans endpoint - database first, hardcoded fallback
    Production-grade with performance optimization and error resilience
    """
    try:
        cache_key = 'pricing_plans_data_v2'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_fcfa')
        if not plans.exists():
            logger.error("No active subscription plans found")
            return Response({'error': 'No pricing plans available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        response_data = {}

        for plan in plans:
            metadata = _get_plan_metadata(plan)
            pricing_info = _calculate_plan_pricing(plan, request)

            plan_data = {
                'name': plan.name,
                'tagline': metadata.get('tagline', ''),
                'description': metadata.get('description', ''),
                'capabilities': _extract_plan_capabilities(plan),
                'limits': _extract_plan_limits(plan),
                'pricing': pricing_info
            }

            response_data[plan.tier] = plan_data

        cache.set(cache_key, response_data, timeout=1800)
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return ProductionSafeErrorHandler.safe_error_response(
            e, 'fetch pricing plans', 'Unable to load pricing information'
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_upgrade_prompts(request):
    """
    Database-driven upgrade prompts with manual serialization
    """
    try:
        user = request.user
        current_tier = 'free'

        if hasattr(user, 'subscription') and user.subscription:
            current_tier = user.subscription.plan.tier

        upgrade_prompts = UpgradePrompt.objects.filter(
            is_active=True,
            from_tiers__contains=[current_tier]
        ).order_by('-priority')

        prompts_data = []
        for prompt in upgrade_prompts:
            prompts_data.append({
                'id': prompt.id,
                'name': prompt.name,
                'message': prompt.message,
                'to_tier': prompt.to_tier,
                'priority': prompt.priority,
                'trigger_condition': prompt.trigger_condition,
                'preview_text': prompt.preview_text,
                'comparison_text': prompt.comparison_text,
                'psychology_type': prompt.psychology_type
            })

        return Response({
            'current_tier': current_tier,
            'upgrade_prompts': prompts_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return ProductionSafeErrorHandler.safe_error_response(
            e, 'fetch upgrade prompts'
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_feature_comparison(request):
    """
    Hybrid feature comparison - database first, hardcoded fallback
    """
    try:
        comparison_data = _build_feature_comparison()
        return Response(comparison_data, status=status.HTTP_200_OK)

    except Exception as e:
        return ProductionSafeErrorHandler.safe_error_response(
            e, 'fetch feature comparison'
        )


def _get_plan_metadata(plan):
    """
    Get plan metadata with database fallback to hardcoded
    """
    try:
        pricing_config = PricingConfiguration.objects.filter(is_active=True).first()
        if pricing_config and hasattr(pricing_config, 'plan_metadata'):
            return pricing_config.plan_metadata.get(plan.tier, {})
    except Exception as e:
        logger.debug(f"Database metadata lookup failed: {e}")

    return PLAN_METADATA_FALLBACK.get(plan.tier, {})

def _calculate_plan_pricing(plan, request):
    """
    Calculate plan pricing with user context
    """
    yearly_discount = DiscountService.calculate_yearly_discount(plan.price_fcfa, plan.tier)

    pricing_info = {
        'monthly': {
            'base_price': float(plan.price_fcfa),
            'currency': 'FCFA',
            'period': 'month',
            'display': f"{int(plan.price_fcfa):,} FCFA/month" if plan.price_fcfa > 0 else "Free Forever"
        },
        'yearly': {
            'base_price': float(plan.price_fcfa * 12),
            'discounted_price': float(yearly_discount.get('discounted_price', plan.price_fcfa * 12)),
            'savings': float(yearly_discount.get('discount_amount', 0)),
            'savings_percentage': float(yearly_discount.get('discount_percentage', 0)),
            'currency': 'FCFA',
            'period': 'year',
            'display': f"{int(yearly_discount.get('discounted_price', plan.price_fcfa * 12)):,} FCFA/year"
        }
    }

    if hasattr(request, 'user') and request.user.is_authenticated:
        if yearly_discount.get('discount_amount', 0) > 0:
            pricing_info['discount'] = {
                'type': 'yearly_billing',
                'name': yearly_discount.get('discount_name', 'Yearly Billing Discount'),
                'available': True
            }
    else:
        if plan.tier != 'free' and yearly_discount.get('discount_amount', 0) > 0:
            pricing_info['discount'] = {
                'type': 'yearly_billing_preview',
                'name': 'Save with Yearly Billing',
                'cta': 'Sign up to get yearly discount',
                'available': True
            }

    return pricing_info

def _build_feature_comparison():
    """
    Build feature comparison - database first, hardcoded fallback
    """
    try:
        if _database_available():
            return _build_database_feature_comparison()
    except Exception as e:
        logger.warning(f"Database feature comparison failed: {e}")

    return _build_hardcoded_feature_comparison()

def _database_available():
    """
    Check if database is accessible for feature queries
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return FeatureGroup.objects.filter(is_active=True).exists()
    except Exception:
        return False

def _build_database_feature_comparison():
    """
    Database-driven feature comparison
    """
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_fcfa')
    feature_groups = FeatureGroup.objects.filter(is_active=True).prefetch_related(
        'plan_features__subscription_plan'
    ).order_by('display_order')

    comparison_data = {
        'plans': [],
        'feature_categories': []
    }

    for plan in plans:
        comparison_data['plans'].append({
            'id': plan.tier,
            'name': plan.name,
            'price': {
                'amount': int(plan.price_fcfa),
                'display': f"{int(plan.price_fcfa):,} FCFA" if plan.price_fcfa > 0 else "Free"
            },
            'popular': plan.tier == 'pro'
        })

    for group in feature_groups:
        category = {
            'name': group.name,
            'icon': group.icon,
            'features': []
        }

        for plan in plans:
            plan_feature = group.plan_features.filter(subscription_plan=plan).first()
            if plan_feature:
                category['features'].append({
                    'plan_id': plan.tier,
                    'display': plan_feature.display_text,
                    'description': plan_feature.description,
                    'enabled': plan_feature.is_enabled
                })

        comparison_data['feature_categories'].append(category)

    return comparison_data

def _build_hardcoded_feature_comparison():
    """
    Hardcoded feature comparison fallback
    """
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_fcfa')

    comparison_data = {
        'plans': [],
        'feature_categories': []
    }

    for plan in plans:
        comparison_data['plans'].append({
            'id': plan.tier,
            'name': plan.name,
            'price': {
                'amount': int(plan.price_fcfa),
                'display': f"{int(plan.price_fcfa):,} FCFA" if plan.price_fcfa > 0 else "Free"
            },
            'popular': plan.tier == 'pro'
        })

    for category in HARDCODED_FEATURE_MATRIX:
        features = []
        for feature in category['features']:
            feature_values = {}
            for tier_data in comparison_data['plans']:
                tier = tier_data['id']
                feature_values[tier] = _get_hardcoded_feature_value(feature['name'], tier)

            features.append({
                'name': feature['name'],
                'description': feature['description'],
                'values': feature_values
            })

        comparison_data['feature_categories'].append({
            'name': category['name'],
            'features': features
        })

    return comparison_data

def _get_hardcoded_feature_value(feature_name, tier):
    """
    Get hardcoded feature values for fallback
    """
    feature_matrix = {
        'Website Deployment': {
            'free': False, 'beginning': True, 'pro': True, 'enterprise': True
        },
        'Custom Domains': {
            'free': "Not included", 'beginning': "1 domain", 'pro': "5 domains", 'enterprise': "Unlimited"
        },
        'Storage': {
            'free': "0.5 GB", 'beginning': "10 GB", 'pro': "100 GB", 'enterprise': "1 TB"
        },
        'Bandwidth': {
            'free': "0 GB", 'beginning': "100 GB", 'pro': "1 TB", 'enterprise': "Unlimited"
        },
        'Analytics': {
            'free': "None", 'beginning': "Basic", 'pro': "Advanced", 'enterprise': "Advanced"
        },
        'White Label': {
            'free': False, 'beginning': False, 'pro': True, 'enterprise': True
        },
        'API Access': {
            'free': False, 'beginning': False, 'pro': True, 'enterprise': True
        },
        'Workspaces': {
            'free': "1 workspace", 'beginning': "2 workspaces", 'pro': "10 workspaces", 'enterprise': "Unlimited"
        },
        'Support Level': {
            'free': "Community", 'beginning': "Standard", 'pro': "Standard", 'enterprise': "Enterprise"
        },
        'Priority Support': {
            'free': False, 'beginning': False, 'pro': False, 'enterprise': True
        }
    }

    return feature_matrix.get(feature_name, {}).get(tier, "Not available")

def _extract_plan_capabilities(plan):
    """
    Extract plan capabilities consistently
    """
    return {
        'deployment_allowed': plan.deployment_allowed,
        'custom_domains_allowed': plan.custom_domains > 0,
        'analytics_enabled': plan.analytics_level != 'none',
        'white_label_enabled': plan.white_label_enabled,
        'dedicated_support': plan.dedicated_support,
        'api_access': plan.tier in ['pro', 'enterprise'],
        'priority_support': plan.tier == 'enterprise',
    }

def _extract_plan_limits(plan):
    """
    Extract plan limits consistently
    """
    return {
        'storage_gb': float(plan.storage_gb),
        'bandwidth_gb': float(plan.bandwidth_gb),
        'deployed_sites': plan.sites_limit,
        'workspaces': plan.max_workspaces,
        'custom_domains': plan.custom_domains,
        'analytics_level': plan.analytics_level,
        'support_level': 'enterprise' if plan.dedicated_support else ('standard' if plan.tier != 'free' else 'community')
    }

def _check_template_bonus_eligibility(user):
    """
    Check template bonus eligibility safely
    """
    try:
        if hasattr(user, 'trial_eligibility'):
            return user.trial_eligibility.is_template_bonus_eligible
        return True
    except Exception:
        return True