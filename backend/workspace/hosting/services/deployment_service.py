"""
Deployment Service
Implements pool-based deployment for all tiers (Shopify model)
"""
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import logging
import json
from decimal import Decimal

from ..models import HostingEnvironment, DeployedSite, DeploymentLog
from .resource_usage_service import ResourceUsageService
from .infrastructure_service import AWSInfrastructureService

logger = logging.getLogger(__name__)


class DeploymentService:
    """
    Main deployment orchestrator
    All deployments use shared pool infrastructure (Shopify model)
    """
    
    @staticmethod
    def can_user_deploy(user, workspace, template):
        """
        Check if user can deploy based on subscription and limits
        Implements the deployment gate strategy
        """
        try:
            # Check if user has hosting environment
            hosting_env = HostingEnvironment.objects.get(user=user)
        except HostingEnvironment.DoesNotExist:
            return {
                'allowed': False,
                'reason': 'no_hosting_environment',
                'message': 'No hosting environment found. Please contact support.'
            }
        
        # Check subscription deployment permission (KEY CONVERSION GATE)
        if not hosting_env.is_deployment_allowed:
            return {
                'allowed': False,
                'reason': 'subscription_required',
                'message': 'Website deployment requires a paid subscription plan',
                'upgrade_required': True,
                'current_tier': hosting_env.subscription.plan.tier,
                'upgrade_options': DeploymentService._get_upgrade_options(hosting_env.subscription.plan.tier)
            }
        
        # Check template design rights
        if template.is_owned_by_user and template.owned_by != user:
            return {
                'allowed': False,
                'reason': 'template_rights_required',
                'message': f'This template has exclusive design rights owned by {template.owned_by.username}',
                'template_owner': template.owned_by.username
            }
        
        
        # Check resource limits
        estimated_size = DeploymentService._estimate_deployment_size(template, workspace)
        resource_check = hosting_env.check_resource_limits(
            additional_storage_gb=estimated_size['storage_gb']
        )
        
        if not all(resource_check.values()):
            return {
                'allowed': False,
                'reason': 'resource_limits_exceeded',
                'message': 'Deployment would exceed your subscription resource limits',
                'limits_status': resource_check,
                'upgrade_required': True
            }
        
        return {'allowed': True}
    
    @staticmethod
    def deploy_site(user, workspace, customization):
        """
        Deploy site by publishing customization and setting up DNS/CDN routing
        No HTML generation - template runs from CDN with runtime puck_data fetching
        """
        try:
            hosting_env = HostingEnvironment.objects.get(user=user)
        except HostingEnvironment.DoesNotExist:
            raise ValueError("No hosting environment found")
        
        # Validate deployment eligibility (subscription validation - CRITICAL)
        deployment_check = DeploymentService.can_user_deploy(user, workspace, customization.template)
        if not deployment_check['allowed']:
            raise ValueError(f"Deployment not allowed: {deployment_check['message']}")
        
        with transaction.atomic():
            # Get or create deployed site record
            site, created = DeployedSite.objects.get_or_create(
                workspace=workspace,
                defaults={
                    'template': customization.template,
                    'customization': customization,
                    'hosting_environment': hosting_env,
                    'user': user,
                    'site_name': workspace.name,
                    'slug': workspace.slug,
                    'subdomain': DeploymentService._generate_subdomain(user, workspace.slug),
                    'template_cdn_url': customization.template.get_cdn_url() if hasattr(customization.template, 'get_cdn_url') else '',
                    'status': 'preview'  # Start in preview, publish makes it active
                }
            )
            
            # If site exists, ensure it references current customization
            if not created:
                site.customization = customization
                site.template = customization.template
                site.save()
            
            # Create deployment log
            deployment_log = DeploymentLog.objects.create(
                site=site,
                customization=customization,
                trigger='manual_publish',
                infrastructure_model=hosting_env.infrastructure_model,
                deployment_config=site.generate_deployment_config()
            )
            
            actions_performed = []
            
            try:
                # Step 1: Publish customization (sets is_active=True, idempotent)
                from theme.services.template_customization_service import TemplateCustomizationService
                published_customization = TemplateCustomizationService.publish_for_deployment(
                    workspace_id=workspace.id,
                    user=user
                )
                actions_performed.append('published_theme')
                logger.info(f"Published theme '{published_customization.theme_name}' for workspace {workspace.id}")
                
                # Step 2: Setup DNS/CDN routing (no static file upload)
                # All deployments use pool infrastructure
                result = DeploymentService._setup_pool_routing(site)
                
                actions_performed.extend(result.get('actions', []))
                
                if result['success']:
                    # Update site to active
                    site.status = 'active'
                    site.last_publish = timezone.now()
                    site.save()
                    
                    # Update hosting environment usage (bandwidth only, no storage)
                    hosting_env.active_sites_count += 1 if created else 0
                    # No storage increment - template is on CDN
                    hosting_env.save()
                    
                    # Mark deployment as successful
                    deployment_log.actions_log = actions_performed
                    deployment_log.mark_completed(success=True)
                    
                    logger.info(
                        f"Successfully deployed {site.site_name} using {hosting_env.infrastructure_model} model. "
                        f"Actions: {actions_performed}"
                    )
                    
                    return {
                        'success': True,
                        'site': site,
                        'live_url': site.live_url,
                        'preview_url': site.preview_url,
                        'deployment_id': deployment_log.id,
                        'actions': actions_performed
                    }
                else:
                    # Deployment failed
                    site.status = 'failed' if created else site.status
                    site.save()
                    
                    deployment_log.actions_log = actions_performed
                    deployment_log.mark_completed(success=False, error_message=result['error'])
                    
                    logger.error(f"Deployment failed for {site.site_name}: {result['error']}")
                    
                    return {
                        'success': False,
                        'error': result['error'],
                        'site': site
                    }
                    
            except Exception as deployment_error:
                # Handle deployment errors
                if created:
                    site.status = 'failed'
                    site.save()
                
                deployment_log.actions_log = actions_performed
                deployment_log.mark_completed(
                    success=False, 
                    error_message=str(deployment_error)
                )
                
                logger.error(f"Deployment error for {site.site_name}: {str(deployment_error)}")
                raise
    
    @staticmethod
    def _setup_pool_routing(site):
        """
        Setup DNS/CDN routing for pool infrastructure (all tiers)
        - Template runs from shared CDN, fetches puck_data at runtime
        - Folder-based isolation per workspace
        - Rate limiting enforced at application level
        """
        try:
            from .infrastructure_facade import InfrastructureFacade

            deployment_config = site.generate_deployment_config()
            actions = []
            workspace_id = str(site.workspace.id)

            # Get appropriate infrastructure service (mock or AWS)
            infra_service = InfrastructureFacade.get_service()

            # Configure CloudFront behavior for subdomain routing
            # Template is already on CDN, we just route subdomain to workspace folder
            cloudfront_result = infra_service.configure_pool_cloudfront(
                site.user.id,
                site.slug,
                deployment_config.get('cloudfront_behavior', {})
            )

            if cloudfront_result.get('success'):
                actions.append('configured_cloudfront_routing')

                # Setup DNS record for subdomain or custom domain
                if site.custom_domain:
                    # Configure custom domain with SSL
                    domain_result = infra_service.configure_custom_domain(
                        site.custom_domain,
                        cloudfront_result['distribution_domain']
                    )

                    if domain_result.get('success'):
                        actions.append('configured_custom_domain')
                        live_url = f"https://{site.custom_domain}"
                    else:
                        return {
                            'success': False,
                            'error': f"Custom domain configuration failed: {domain_result.get('error')}"
                        }
                else:
                    # Setup subdomain DNS
                    dns_result = infra_service.setup_dns_record(
                        subdomain=site.subdomain,
                        target=cloudfront_result['distribution_domain']
                    )

                    if dns_result.get('success'):
                        actions.append('configured_dns')
                        live_url = f"https://{site.subdomain}"
                    else:
                        return {
                            'success': False,
                            'error': f"DNS configuration failed: {dns_result.get('error')}"
                        }

                # Invalidate CloudFront cache for workspace path
                cache_result = infra_service.invalidate_cache(
                    distribution_id=cloudfront_result['distribution_id'],
                    paths=[f'/ws/{workspace_id}/*', f'/workspaces/{workspace_id}/*']
                )

                if cache_result.get('success'):
                    actions.append('invalidated_cache')

                return {
                    'success': True,
                    'live_url': live_url,
                    'actions': actions,
                    'routing_details': {
                        'cloudfront': cloudfront_result,
                        'workspace_path': f'/ws/{workspace_id}/',
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"CloudFront routing failed: {cloudfront_result.get('error')}"
                }

        except Exception as e:
            logger.error(f"Pool routing setup error: {str(e)}")
            return {
                'success': False,
                'error': f"Pool routing error: {str(e)}"
            }
    
    
    @staticmethod
    def _generate_subdomain(user, slug):
        """
        Generate unique subdomain for site
        Pattern: Try {slug}, then {slug}-{random-6char} if taken
        No UUIDs - short and clean!
        """
        import random
        import string

        # Try slug first (cleanest option)
        if not DeployedSite.objects.filter(subdomain=slug).exists():
            return slug

        # If taken, add random suffix (6 chars: lowercase + numbers)
        chars = string.ascii_lowercase + string.digits
        for _ in range(10):  # Try 10 times
            random_suffix = ''.join(random.choices(chars, k=6))
            subdomain = f"{slug}-{random_suffix}"
            if not DeployedSite.objects.filter(subdomain=subdomain).exists():
                return subdomain

        # Fallback: use counter (very unlikely to reach here)
        counter = 1
        while True:
            subdomain = f"{slug}-{counter}"
            if not DeployedSite.objects.filter(subdomain=subdomain).exists():
                return subdomain
            counter += 1
    
    @staticmethod
    def _estimate_deployment_size(template, workspace):
        """
        Estimate deployment resource requirements (bandwidth only - no storage)
        Templates run from CDN, only puck_data stored in DB
        """
        # Estimate monthly bandwidth based on workspace type and expected traffic
        base_bandwidth = Decimal('1.0')  # 1GB base monthly bandwidth

        # Template complexity factor (more complex = more API calls)
        if template.template_type in ['ecommerce', 'services']:
            base_bandwidth += Decimal('2.0')  # E-commerce needs more bandwidth

        # Workspace content factor (more pages = more traffic)
        # This would analyze workspace data to estimate traffic
        content_factor = Decimal('0.5')  # Placeholder

        return {
            'storage_gb': Decimal('0.0'),  # No storage - template on CDN, puck_data in DB
            'bandwidth_gb': base_bandwidth + content_factor
        }
    
    @staticmethod
    def _get_upgrade_options(current_tier):
        """Get upgrade options for current tier"""
        upgrade_map = {
            'free': ['beginning', 'pro', 'enterprise'],
            'beginning': ['pro', 'enterprise'],
            'pro': ['enterprise'],
            'enterprise': []
        }
        return upgrade_map.get(current_tier, [])