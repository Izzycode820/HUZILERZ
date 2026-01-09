from django.db import transaction
from django.utils import timezone
from workspace.core.models import ProvisioningRecord, ProvisioningLog
from workspace.hosting.models import WorkspaceInfrastructure, HostingEnvironment, DeployedSite
from workspace.hosting.services.idempotency_service import IdempotencyManager
from workspace.hosting.services.infrastructure_facade import InfrastructureFacade


class InfrastructureProvisioningService:
    """
    Service for provisioning infrastructure for workspaces
    All workspaces use shared pool infrastructure with path-based isolation
    """

    @classmethod
    def provision_for_workspace(cls, workspace, provisioning_record):
        """
        Provision pool infrastructure for workspace
        Called from background task
        """
        ProvisioningLog.log_step_started(
            provisioning=provisioning_record,
            step='assign_infrastructure',
            metadata={'workspace_id': str(workspace.id)}
        )

        try:
            # All workspaces get pool infrastructure regardless of tier
            infrastructure = cls._assign_pool_infrastructure(workspace)

            ProvisioningLog.log_step_completed(
                provisioning=provisioning_record,
                step='assign_infrastructure',
                metadata={
                    'workspace_id': str(workspace.id),
                    'infra_type': 'pool',
                    'subdomain': infrastructure.subdomain
                }
            )

            return infrastructure

        except Exception as e:
            ProvisioningLog.log_step_failed(
                provisioning=provisioning_record,
                step='assign_infrastructure',
                error=str(e),
                metadata={'workspace_id': str(workspace.id)}
            )
            raise

    @classmethod
    def _assign_pool_infrastructure(cls, workspace):
        """
        Assign shared pool infrastructure
        All workspaces use same infrastructure with folder-based isolation

        Pool infrastructure is shared by ALL users
        Configuration comes from Django settings (SHARED_POOL_CONFIG)

        PRODUCTION-GRADE: Idempotent, handles race conditions, atomic transactions
        """
        from django.conf import settings
        from django.core.exceptions import ValidationError
        import logging

        logger = logging.getLogger(__name__)

        with transaction.atomic():
            # Get user's subscription tier for rate limiting
            subscription = getattr(workspace.owner, 'subscription', None)
            subscription_tier = subscription.plan.tier if (subscription and hasattr(subscription, 'plan')) else 'free'

            # Get shared pool configuration from settings
            shared_pool_config = getattr(settings, 'SHARED_POOL_CONFIG', {
                'cdn_distribution': 'shared-pool-distribution',
                'cdn_distribution_domain': 'd123456abcdef.cloudfront.net',
                'media_bucket': 'shared-pool-media',
                'storage_bucket': 'shared-pool-storage',
                'api_gateway': 'shared-api-gateway'
            })

            workspace_id = str(workspace.id)

            # PRODUCTION-GRADE: Get or wait for hosting environment
            # Hosting environment should exist (created on user signup)
            # Use select_for_update to prevent race conditions
            try:
                hosting_env = HostingEnvironment.objects.select_for_update().get(user=workspace.owner)
                logger.info(f"Using existing HostingEnvironment {hosting_env.id} for workspace {workspace_id}")
            except HostingEnvironment.DoesNotExist:
                logger.error(
                    f"HostingEnvironment not found for user {workspace.owner.id}. "
                    f"This should have been created on signup."
                )
                raise ValidationError(
                    "No hosting environment found. Please contact support or try again in a few moments."
                )

            # PRODUCTION-GRADE: Idempotent infrastructure creation
            # Use get_or_create to handle race conditions and retries
            # Pool infrastructure is INSTANT - no async provisioning needed (Shopify model)
            infrastructure, infra_created = WorkspaceInfrastructure.objects.get_or_create(
                workspace=workspace,
                defaults={
                    'pool': hosting_env,
                    'subdomain': f"{workspace.slug}.huzilerz.com",
                    'preview_url': f"https://{workspace.slug}.preview.huzilerz.com",
                    'status': 'active',  # Pool infrastructure is instant - already provisioned (shared resources)
                    'activated_at': timezone.now(),  # Set activation time on creation
                    'infra_metadata': {
                        # Infrastructure type
                        'infrastructure_type': 'POOL',
                        'shared_infrastructure': True,

                        # Shared CDN (ONE distribution for all workspaces)
                        'cdn_distribution': shared_pool_config.get('cdn_distribution'),
                        'cdn_distribution_domain': shared_pool_config.get('cdn_distribution_domain'),

                        # Workspace-specific folders in shared buckets (Shopify model)
                        'media_product_path': f's3://{shared_pool_config.get("media_bucket")}/workspaces/{workspace_id}/products/',
                        'media_theme_path': f's3://{shared_pool_config.get("media_bucket")}/workspaces/{workspace_id}/themes/',
                        'storage_path': f's3://{shared_pool_config.get("storage_bucket")}/workspaces/{workspace_id}/',

                        # Cache namespace isolation
                        'cache_namespace': f'workspace:{workspace_id}',
                        'cache_prefix': f'ws:{workspace_id}:',

                        # Rate limiting (enforced at application level, not infrastructure)
                        'rate_limit_tier': subscription_tier,
                        'rate_limit_key': f'ratelimit:workspace:{workspace_id}',
                        'rate_limit_window_seconds': 60,

                        # Subdomain routing
                        'subdomain': f'{workspace.slug}.huzilerz.com',
                        'cloudfront_path_pattern': f'/ws/{workspace_id}/*',

                        # API Gateway routing (shared gateway with path-based routing)
                        'api_gateway_id': shared_pool_config.get('api_gateway'),
                        'api_path_prefix': f'/workspaces/{workspace_id}',

                        # User and tier info (for analytics/billing)
                        'user_id': workspace.owner.id,
                        'subscription_tier': subscription_tier,
                    }
                }
            )

            if infra_created:
                logger.info(f"Created new WorkspaceInfrastructure {infrastructure.id} (active) for workspace {workspace_id}")
            else:
                logger.info(f"Reusing existing WorkspaceInfrastructure {infrastructure.id} for workspace {workspace_id}")
                # No need to call mark_active() - already active or being reused

            # PRODUCTION-GRADE: Idempotent DeployedSite creation
            # Use get_or_create to handle race conditions and retries
            deployed_site, site_created = DeployedSite.objects.get_or_create(
                workspace=workspace,
                defaults={
                    'user': workspace.owner,
                    'hosting_environment': hosting_env,
                    'site_name': workspace.name,
                    'slug': workspace.slug,
                    'subdomain': workspace.slug,  # Will be used as subdomain.huzilerz.com
                    'status': 'preview',  # Start in preview, publish will activate (FREE tier conversion optimization)
                    'template_cdn_url': '',  # Will be set when template is published
                    'deployment_details': {
                        'provisioned_at': timezone.now().isoformat(),
                        'infrastructure_id': str(infrastructure.id),
                        'preview_url': infrastructure.preview_url,
                        'subdomain': infrastructure.subdomain,
                    }
                }
            )

            if site_created:
                logger.info(f"Created new DeployedSite {deployed_site.id} (preview) for workspace {workspace_id}")
            else:
                logger.info(f"Reusing existing DeployedSite {deployed_site.id} for workspace {workspace_id}")

            # PRODUCTION-GRADE: Update hosting environment site count atomically
            # This prevents race conditions when multiple workspaces are created simultaneously
            HostingEnvironment.objects.filter(id=hosting_env.id).update(
                active_sites_count=WorkspaceInfrastructure.objects.filter(
                    pool=hosting_env,
                    status='active'
                ).count()
            )

            # INFRASTRUCTURE SETUP: Setup actual AWS resources (DNS, CloudFront routing)
            # Uses InfrastructureFacade to automatically switch between mock (dev) and AWS (prod)
            # These calls are made AFTER database records to ensure rollback safety
            if infra_created:
                cls._setup_workspace_infrastructure(
                    workspace=workspace,
                    infrastructure=infrastructure,
                    hosting_env=hosting_env,
                    shared_pool_config=shared_pool_config
                )

            return infrastructure

    @classmethod
    def _setup_workspace_infrastructure(cls, workspace, infrastructure, hosting_env, shared_pool_config):
        """
        Setup actual infrastructure resources (DNS, CloudFront routing)

        Uses InfrastructureFacade to automatically route to:
        - MockAWSService in dev (INFRASTRUCTURE_MODE='mock')
        - AWSInfrastructureService in prod (INFRASTRUCTURE_MODE='aws')

        Handles errors gracefully - logs failures but doesn't crash provisioning
        Database records are already created, so workspace is functional even if AWS calls fail

        Args:
            workspace: Workspace instance
            infrastructure: WorkspaceInfrastructure instance
            hosting_env: HostingEnvironment instance
            shared_pool_config: Shared pool configuration dict
        """
        from django.conf import settings
        import logging

        logger = logging.getLogger(__name__)

        workspace_id = str(workspace.id)
        subdomain = workspace.slug
        full_subdomain = f"{subdomain}.huzilerz.com"

        # Get infrastructure service (automatically uses mock in dev, AWS in prod)
        infra_service = InfrastructureFacade.get_service()

        logger.info(
            f"Setting up infrastructure for workspace {workspace_id} "
            f"(Mode: {InfrastructureFacade.get_mode()})"
        )

        # 1. DNS Record Setup
        # For pool infrastructure, we have two options:
        # A) Wildcard DNS: One record *.huzilerz.com → CloudFront (recommended for pool)
        # B) Per-workspace DNS: Individual CNAME records (what we do here)

        # ============================================================================
        # ONE-TIME DNS SETUP REQUIRED (Shopify Model):
        # ============================================================================
        # In Your DNS Provider (Namecheap/Route53/GoDaddy), create ONE wildcard DNS record:
        #
        #   Type: CNAME
        #   Name: *
        #   Value: {your-cloudfront-domain}.cloudfront.net
        #   TTL: 300
        #
        # That's it! After this, ALL subdomains work automatically:
        #   - sneakers.huzilerz.com → works
        #   - myshop.huzilerz.com → works
        #   - anything.huzilerz.com → works
        #
        # No per-workspace DNS creation needed.
        # ============================================================================

        # Check if we should setup per-workspace DNS or rely on wildcard
        use_wildcard_dns = getattr(settings, 'USE_WILDCARD_DNS', True)  # Default to wildcard for pool

        if not use_wildcard_dns:
            # Per-workspace DNS record creation
            try:
                cloudfront_domain = shared_pool_config.get('cdn_distribution_domain', 'd123456abcdef.cloudfront.net')

                logger.info(f"Creating DNS record: {full_subdomain} → {cloudfront_domain}")

                dns_result = infra_service.setup_dns_record(
                    subdomain=full_subdomain,
                    target=cloudfront_domain
                )

                if dns_result.get('success') or dns_result.get('skipped'):
                    logger.info(f"DNS setup completed for {full_subdomain}")

                    # Store DNS result in infrastructure metadata
                    infrastructure.infra_metadata['dns_setup'] = {
                        'result': dns_result,
                        'setup_at': timezone.now().isoformat()
                    }
                    infrastructure.save(update_fields=['infra_metadata'])
                else:
                    logger.warning(
                        f"DNS setup failed for {full_subdomain}: {dns_result.get('error', 'Unknown error')}. "
                        f"Subdomain may not resolve until DNS is configured manually."
                    )

            except Exception as e:
                logger.error(f"Exception during DNS setup for {full_subdomain}: {str(e)}", exc_info=True)
                # Don't raise - workspace is still functional, DNS can be fixed later
        else:
            logger.info(
                f"Wildcard DNS enabled - skipping per-workspace DNS record creation for {full_subdomain}. "
                f"Ensure *.huzilerz.com wildcard DNS record points to CloudFront."
            )

        # 2. CloudFront Routing Configuration (Optional)
        # For wildcard DNS + path-based routing, CloudFront uses application routing
        # If you need per-workspace cache behaviors, enable this

        setup_cloudfront_behaviors = getattr(settings, 'SETUP_CLOUDFRONT_BEHAVIORS', False)

        if setup_cloudfront_behaviors:
            try:
                logger.info(f"Configuring CloudFront routing for workspace {workspace_id}")

                # This would add a cache behavior for the workspace path
                # For pool model with application routing, this is usually not needed
                cloudfront_result = infra_service.configure_pool_cloudfront(
                    user_id=workspace.owner.id,
                    slug=subdomain,
                    behavior_config={
                        'path_pattern': f'/ws/{workspace_id}/*',
                        'target_origin': shared_pool_config.get('cdn_distribution_domain'),
                    }
                )

                if cloudfront_result.get('success'):
                    logger.info(f"CloudFront routing configured for workspace {workspace_id}")

                    # Store CloudFront result in infrastructure metadata
                    infrastructure.infra_metadata['cloudfront_setup'] = {
                        'result': cloudfront_result,
                        'setup_at': timezone.now().isoformat()
                    }
                    infrastructure.save(update_fields=['infra_metadata'])
                else:
                    logger.warning(f"CloudFront routing setup failed: {cloudfront_result.get('error')}")

            except Exception as e:
                logger.error(f"Exception during CloudFront setup: {str(e)}", exc_info=True)
                # Don't raise - workspace is still functional with application routing
        else:
            logger.info(
                f"CloudFront behavior setup disabled - using application-level routing for workspace {workspace_id}"
            )

        logger.info(f"Infrastructure setup completed for workspace {workspace_id} ({full_subdomain})")

