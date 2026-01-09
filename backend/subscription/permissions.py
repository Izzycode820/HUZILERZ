"""
Django REST Framework permissions for subscription-based access control
"""
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class SubscriptionPermission(permissions.BasePermission):
    """
    Base subscription permission class
    """
    required_tiers = []
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user_tier = request.user.get_subscription_tier()
        if user_tier not in self.required_tiers:
            # Provide detailed error for API clients
            tier_limits = request.user.get_tier_limits()
            raise PermissionDenied({
                'error': 'subscription_required',
                'message': f'This feature requires {" or ".join(self.required_tiers)} subscription',
                'current_tier': user_tier,
                'required_tiers': self.required_tiers,
                'user_limits': tier_limits,
                'upgrade_url': '/subscription/plans/'
            })
        
        return True


class DeploymentPermission(permissions.BasePermission):
    """
    Permission for deployment features (main conversion gate)
    """
    message = "Website deployment requires a paid subscription"
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if not request.user.can_deploy_sites():
            raise PermissionDenied({
                'error': 'deployment_blocked',
                'message': self.message,
                'current_tier': request.user.get_subscription_tier(),
                'conversion_trigger': True,
                'upgrade_options': {
                    'beginning': {
                        'name': 'Launch Your Business',
                        'price_fcfa': 10000,
                        'benefits': ['1 website deployment', 'Custom domain', 'SSL certificate']
                    },
                    'pro': {
                        'name': 'Scale Multiple Ventures',
                        'price_fcfa': 25000, 
                        'benefits': ['3 website deployments', 'Core analytics', 'Priority support']
                    },
                    'enterprise': {
                        'name': 'Unlimited Growth',
                        'price_fcfa': 50000,
                        'benefits': ['Unlimited deployments', 'Enhanced analytics', '24/7 support']
                    }
                }
            })
        
        return True


class AnalyticsPermission(SubscriptionPermission):
    """
    Permission for analytics features (Pro+ only)
    """
    required_tiers = ['pro', 'enterprise']
    message = "Analytics features require Pro or Enterprise subscription"


class BeginningPlusPermission(SubscriptionPermission):
    """
    Permission for Beginning tier and above
    """
    required_tiers = ['beginning', 'pro', 'enterprise']


class ProPlusPermission(SubscriptionPermission):
    """
    Permission for Pro tier and above
    """
    required_tiers = ['pro', 'enterprise']


class EnterprisePermission(SubscriptionPermission):
    """
    Permission for Enterprise tier only
    """
    required_tiers = ['enterprise']


class TemplateUsagePermission(permissions.BasePermission):
    """
    Permission to check if user can use a specific template
    """
    def has_object_permission(self, request, view, obj):
        # obj should be a Template instance
        if not obj.can_be_used_by_user(request.user):
            raise PermissionDenied({
                'error': 'template_access_denied',
                'message': 'This template requires purchase or subscription',
                'template_name': obj.name,
                'is_free': obj.is_free,
                'price': str(obj.price),
                'user_discount': obj.get_discount_for_user(request.user),
                'stacked_benefits': obj.get_stacked_benefits_for_user(request.user)
            })
        
        return True


class TemplateDeploymentPermission(permissions.BasePermission):
    """
    Permission to check if user can deploy a specific template
    """
    def has_object_permission(self, request, view, obj):
        # obj should be a Template instance
        if not obj.can_be_deployed_by_user(request.user):
            user_tier = request.user.get_subscription_tier()
            
            if user_tier == 'free':
                raise PermissionDenied({
                    'error': 'deployment_blocked', 
                    'message': 'Template deployment requires a paid subscription',
                    'template_name': obj.name,
                    'conversion_trigger': True
                })
            else:
                raise PermissionDenied({
                    'error': 'template_deployment_denied',
                    'message': 'You need to purchase design rights or upgrade subscription',
                    'template_name': obj.name,
                    'required_action': 'purchase_design_rights' if obj.can_be_purchased() else 'upgrade_subscription'
                })
        
        return True


# Convenience permission combinations
class WorkspaceManagementPermission(permissions.BasePermission):
    """
    Permission for workspace management features
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # obj should be a Workspace instance
        # Check if user can access this workspace based on subscription
        workspace_tier = obj.current_tier
        user_tier = request.user.get_subscription_tier()
        
        # Owner always has access
        if obj.owner == request.user:
            return True
        
        # Members need at least the workspace's tier level
        if hasattr(obj, 'members') and request.user in obj.members.all():
            tier_hierarchy = ['free', 'beginning', 'pro', 'enterprise']
            user_tier_level = tier_hierarchy.index(user_tier) if user_tier in tier_hierarchy else 0
            workspace_tier_level = tier_hierarchy.index(workspace_tier) if workspace_tier in tier_hierarchy else 0
            
            if user_tier_level >= workspace_tier_level:
                return True
        
        return False