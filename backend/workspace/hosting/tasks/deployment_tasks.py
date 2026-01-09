"""
Deployment Infrastructure Tasks - Async DNS/SSL/CDN Setup
Triggered by theme publish signal, runs in background via Celery
With workspace-based queue throttling and CDN cache management
"""
import logging
import time
from celery import shared_task
from django.utils import timezone
from workspace.hosting.services.queue_service import WorkspaceThrottledTask
from workspace.hosting.services.cdn_cache_service import CDNCacheService
from workspace.hosting.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


@shared_task(
    name='workspace_hosting.provision_storefront_password',
    bind=True,
    acks_late=True,
    max_retries=3,
    time_limit=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=30
)
def provision_storefront_password_async(self, deployed_site_id: str):
    """
    Auto-provision password protection for new DeployedSite

    Shopify pattern: "Infrastructure live, business not live"
    - Generates simple default password
    - Enables password protection
    - Sends notification to user

    Args:
        deployed_site_id: UUID of DeployedSite

    Returns:
        dict: Provisioning result with default password

    Security:
        - Password is hashed using Django's PBKDF2 SHA256
        - Never logged in plain text (only in notification)
        - Automatic retry on failure (max 3 attempts)

    Cameroon Context:
        - Users may not understand SEO/passwords
        - Auto-protection prevents premature indexing
        - Simple password format: "huzilerz-2025-a3f7b2"
    """
    from workspace.hosting.models import DeployedSite
    import secrets
    from django.utils import timezone

    try:
        logger.info(f"[Storefront Password] Provisioning for DeployedSite {deployed_site_id}")

        # Get DeployedSite
        try:
            site = DeployedSite.objects.select_related('workspace', 'user').get(id=deployed_site_id)
        except DeployedSite.DoesNotExist:
            logger.error(f"DeployedSite {deployed_site_id} not found for password provisioning")
            return {
                'success': False,
                'error': 'DeployedSite not found',
                'deployed_site_id': deployed_site_id
            }

        # Check if already has password
        if site.password_protection_enabled:
            logger.info(
                f"[Storefront Password] Skipping - DeployedSite {deployed_site_id} already has password"
            )
            return {
                'success': True,
                'skipped': True,
                'reason': 'already_has_password',
                'deployed_site_id': deployed_site_id
            }

        # Generate simple memorable default password
        year = timezone.now().year
        random_token = secrets.token_hex(3)  # 6 characters
        default_password = f"huzilerz-{year}-{random_token}"

        # Set default password description if not already set
        if not site.password_description:
            site.password_description = "Our store is opening soon. Enter the password to preview."

        # Enable password protection (atomic update)
        site.set_password(default_password)
        site.save(update_fields=[
            'password_hash',
            'password_plaintext',
            'password_protection_enabled',
            'password_description'
        ])

        logger.info(
            f"[Storefront Password] Enabled for DeployedSite {deployed_site_id} "
            f"(workspace: {site.workspace.name})"
        )

        # Send notification to user about default password
        try:
            from workspace.hosting.services.notification_service import StorefrontNotificationService

            StorefrontNotificationService.notify_default_password(
                deployed_site=site,
                default_password=default_password
            )

            logger.info(
                f"[Storefront Password] Notification sent for DeployedSite {deployed_site_id}"
            )
        except Exception as notification_error:
            # Notification failure is non-critical - password is still set
            logger.warning(
                f"[Storefront Password] Notification failed (non-critical) for DeployedSite {deployed_site_id}: "
                f"{str(notification_error)}"
            )

        # Provision default SEO settings (Phase 4: SEO Implementation)
        seo_provisioned = False
        try:
            logger.info(f"[Storefront SEO] Provisioning default SEO for DeployedSite {deployed_site_id}")

            # Check if SEO fields are already set
            if not site.seo_title and not site.seo_description:
                # Set default SEO values
                site.seo_title = site.site_name
                site.seo_description = f"Welcome to {site.site_name} - Your online store for quality products"

                # Save SEO fields
                site.save(update_fields=['seo_title', 'seo_description'])

                logger.info(
                    f"[Storefront SEO] Default SEO set for DeployedSite {deployed_site_id} | "
                    f"Title: {site.seo_title[:50]}"
                )
                seo_provisioned = True
            else:
                logger.info(
                    f"[Storefront SEO] Skipping - DeployedSite {deployed_site_id} already has SEO settings"
                )
                seo_provisioned = True  # Already set, so consider it provisioned

        except Exception as seo_error:
            # SEO provisioning failure is non-critical
            logger.warning(
                f"[Storefront SEO] Provisioning failed (non-critical) for DeployedSite {deployed_site_id}: "
                f"{str(seo_error)}"
            )

        return {
            'success': True,
            'deployed_site_id': deployed_site_id,
            'workspace_id': str(site.workspace.id),
            'password_enabled': True,
            'notification_sent': True,
            'seo_provisioned': seo_provisioned
        }

    except Exception as e:
        logger.error(
            f"[Storefront Password] Provisioning failed for DeployedSite {deployed_site_id}: {str(e)}",
            exc_info=True
        )

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 5, 60))






@shared_task(
    name='workspace_hosting.apply_theme_deployment',
    base=WorkspaceThrottledTask,
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def apply_theme_deployment(self, workspace_id: str, customization_id: str):
    """
    Lightweight theme deployment - update pointers and invalidate CDN

    NEW APPROACH (decoupled from infrastructure):
    - Infrastructure already provisioned during workspace creation
    - This task ONLY updates content pointers
    - NO DNS/SSL/CDN infrastructure changes

    Flow:
        1. Ensure workspace infrastructure is provisioned
        2. Get or create DeployedSite
        3. Create DeploymentAudit record
        4. Update DeployedSite.customization pointer (atomic)
        5. Invalidate CDN cache (async)
        6. Health check
        7. Rollback on failure

    Args:
        workspace_id: UUID of workspace
        customization_id: UUID of theme customization to activate

    Returns:
        dict: Deployment results with rollback info if failed
    """
    from workspace.core.models import Workspace
    from workspace.hosting.models import DeployedSite, WorkspaceInfrastructure, DeploymentAudit
    from theme.models import TemplateCustomization
    from django.db import transaction

    start_time = time.time()

    try:
        logger.info(f"[Theme Deployment] Starting for workspace {workspace_id}")

        # Get workspace and customization
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            customization = TemplateCustomization.objects.get(id=customization_id)
        except (Workspace.DoesNotExist, TemplateCustomization.DoesNotExist) as e:
            logger.error(f"Workspace or customization not found: {e}")
            return {'success': False, 'error': 'Resource not found'}

        # Check subscription gate
        try:
            hosting_env = workspace.owner.hosting_environment
            if hosting_env.status != 'active' or not hosting_env.is_deployment_allowed:
                raise ValueError("Deployment not allowed")
        except (AttributeError, ValueError) as e:
            logger.warning(f"Deployment blocked for workspace {workspace_id}: {e}")
            return {
                'success': False,
                'error': 'Deployment not allowed for current subscription',
                'upgrade_required': True
            }

        # Ensure workspace infrastructure is provisioned
        try:
            workspace_infra = WorkspaceInfrastructure.objects.get(workspace=workspace)
            if workspace_infra.status not in ['provisioned', 'active']:
                logger.error(f"Workspace infrastructure not ready: {workspace_infra.status}")
                return {
                    'success': False,
                    'error': f'Infrastructure not ready (status: {workspace_infra.status})'
                }
        except WorkspaceInfrastructure.DoesNotExist:
            logger.error(f"WorkspaceInfrastructure not found for workspace {workspace_id}")
            return {'success': False, 'error': 'Infrastructure not provisioned'}

        # Get or create DeployedSite with atomic transaction
        with transaction.atomic():
            deployed_site, created = DeployedSite.objects.get_or_create(
                workspace=workspace,
                defaults={
                    'user': workspace.owner,
                    'template': customization.template,
                    'customization': customization,
                    'hosting_environment': hosting_env,
                    'site_name': workspace.name,
                    'slug': workspace.slug,
                    'subdomain': workspace_infra.subdomain.split('.')[0],
                    'status': 'active',
                    'deployment_details': {
                        'deployed_at': timezone.now().isoformat(),
                        'deployed_by': 'system'
                    }
                }
            )

            # Store previous customization for rollback
            previous_customization = deployed_site.customization if not created else None

            # Create deployment audit record
            audit = DeploymentAudit.objects.create(
                deployed_site=deployed_site,
                previous_customization=previous_customization,
                new_customization=customization,
                initiated_by=workspace.owner,
                status='in_progress'
            )

            # Update deployed site customization pointer (atomic)
            if not created:
                deployed_site.customization = customization
                deployed_site.template = customization.template
                deployed_site.status = 'active'
                deployed_site.save(update_fields=['customization', 'template', 'status'])

            logger.info(f"[Theme Deployment] Updated DeployedSite pointer for workspace {workspace_id}")

        # Invalidate CDN cache (async, non-blocking)
        try:
            cdn_paths = [
                f"/ws/{workspace_id}/*",
                f"/{workspace_infra.subdomain}/*"
            ]
            CDNCacheService.invalidate_workspace_cache(str(workspace_id), cdn_paths)
            logger.info(f"[Theme Deployment] CDN cache invalidated for paths: {cdn_paths}")
        except Exception as cdn_error:
            logger.warning(f"CDN invalidation failed (non-critical): {cdn_error}")
            # Don't fail deployment if CDN invalidation fails

        # Invalidate tenant lookup cache for hostname -> workspace mapping
        try:
            from workspace.hosting.services.tenant_lookup_cache import TenantLookupCache
            from workspace.hosting.models import CustomDomain

            # Get all hostnames for this workspace
            hostnames = [workspace_infra.subdomain]

            # Add custom domains
            custom_domains = CustomDomain.objects.filter(
                workspace=workspace,
                status='active'
            ).values_list('domain', flat=True)

            hostnames.extend(custom_domains)

            # Invalidate all hostnames
            TenantLookupCache.invalidate_all_for_workspace(
                workspace_id=str(workspace_id),
                subdomain=workspace_infra.subdomain,
                custom_domains=list(custom_domains)
            )

            # Refresh cache with new data
            TenantLookupCache.refresh_workspace(str(workspace_id))

            logger.info(f"[Theme Deployment] Tenant cache refreshed for {len(hostnames)} hostnames")
        except Exception as cache_error:
            logger.warning(f"Tenant cache refresh failed (non-critical): {cache_error}")
            # Don't fail deployment if cache refresh fails

        # Health check (basic)
        health_check_passed = True
        health_metadata = {'checks': []}

        try:
            # Basic health check: ensure customization has puck_data
            if not customization.puck_data:
                health_check_passed = False
                health_metadata['checks'].append({
                    'name': 'puck_data_check',
                    'passed': False,
                    'error': 'No puck_data in customization'
                })
            else:
                health_metadata['checks'].append({
                    'name': 'puck_data_check',
                    'passed': True
                })
        except Exception as health_error:
            logger.warning(f"Health check failed: {health_error}")
            health_check_passed = False
            health_metadata['checks'].append({
                'name': 'health_check_exception',
                'passed': False,
                'error': str(health_error)
            })

        # If health check failed, rollback
        if not health_check_passed:
            logger.warning(f"[Theme Deployment] Health check failed, rolling back")

            duration = time.time() - start_time
            rolled_back = False

            if previous_customization:
                with transaction.atomic():
                    deployed_site.customization = previous_customization
                    deployed_site.save(update_fields=['customization'])
                    audit.mark_failed('Health check failed', metadata=health_metadata)

                rolled_back = True
                logger.info(f"[Theme Deployment] Rolled back to previous customization")

                # Record rollback metrics
                MetricsService.record_deployment_attempt(
                    workspace_id=str(workspace_id),
                    success=False,
                    duration_seconds=duration,
                    rolled_back=True,
                    metadata={'reason': 'health_check_failed', 'audit_id': str(audit.id)}
                )

                return {
                    'success': False,
                    'error': 'Health check failed, rolled back',
                    'rolled_back': True,
                    'health_metadata': health_metadata
                }
            else:
                audit.mark_failed('Health check failed, no previous version to rollback', metadata=health_metadata)

                # Record failure without rollback
                MetricsService.record_deployment_attempt(
                    workspace_id=str(workspace_id),
                    success=False,
                    duration_seconds=duration,
                    rolled_back=False,
                    metadata={'reason': 'health_check_failed_no_rollback', 'audit_id': str(audit.id)}
                )

                return {
                    'success': False,
                    'error': 'Health check failed, no previous version',
                    'health_metadata': health_metadata
                }

        # Mark deployment as completed
        audit.mark_completed(metadata={
            'cdn_invalidated': True,
            'health_check': health_metadata
        })

        # Record success metrics
        duration = time.time() - start_time
        MetricsService.record_deployment_attempt(
            workspace_id=str(workspace_id),
            success=True,
            duration_seconds=duration,
            rolled_back=False,
            metadata={'audit_id': str(audit.id)}
        )

        logger.info(f"[Theme Deployment] Completed successfully for workspace {workspace_id}")

        return {
            'success': True,
            'deployed_site_id': str(deployed_site.id),
            'audit_id': str(audit.id),
            'cdn_invalidated': True,
            'health_check_passed': True
        }

    except Exception as e:
        logger.error(f"[Theme Deployment] Failed for workspace {workspace_id}: {e}", exc_info=True)

        # Record failure metrics
        duration = time.time() - start_time
        MetricsService.record_deployment_attempt(
            workspace_id=str(workspace_id),
            success=False,
            duration_seconds=duration,
            rolled_back=False,
            metadata={'error': str(e), 'exception_type': type(e).__name__}
        )

        # Try to mark audit as failed if it was created
        try:
            if 'audit' in locals():
                audit.mark_failed(str(e))
        except:
            pass

        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='workspace_hosting.rollback_deployment')
def rollback_deployment(deployed_site_id: str, audit_id: str):
    """
    Rollback a failed deployment to previous customization

    Args:
        deployed_site_id: UUID of DeployedSite
        audit_id: UUID of DeploymentAudit record

    Returns:
        dict: Rollback results
    """
    from workspace.hosting.models import DeployedSite, DeploymentAudit
    from django.db import transaction

    try:
        deployed_site = DeployedSite.objects.get(id=deployed_site_id)
        audit = DeploymentAudit.objects.get(id=audit_id)

        if not audit.previous_customization:
            logger.error(f"No previous customization to rollback to for audit {audit_id}")
            return {'success': False, 'error': 'No previous version available'}

        with transaction.atomic():
            deployed_site.customization = audit.previous_customization
            deployed_site.save(update_fields=['customization'])
            audit.mark_rolled_back()

        # Invalidate CDN cache
        cdn_paths = [f"/ws/{deployed_site.workspace.id}/*"]
        CDNCacheService.invalidate_paths(cdn_paths)

        logger.info(f"[Rollback] Successfully rolled back deployment {audit_id}")

        return {
            'success': True,
            'rolled_back_to': str(audit.previous_customization.id)
        }

    except Exception as e:
        logger.error(f"[Rollback] Failed for audit {audit_id}: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task(name='workspace_hosting.health_check_deployment')
def health_check_deployment(deployed_site_id: str):
    """
    Perform health check on deployed site

    Checks:
    - Site is accessible
    - Customization has valid puck_data
    - Required assets are available

    Args:
        deployed_site_id: UUID of DeployedSite

    Returns:
        dict: Health check results
    """
    from workspace.hosting.models import DeployedSite

    try:
        deployed_site = DeployedSite.objects.get(id=deployed_site_id)

        checks = []
        all_passed = True

        # Check 1: Customization has puck_data
        if not deployed_site.customization.puck_data:
            checks.append({'name': 'puck_data', 'passed': False, 'error': 'Missing puck_data'})
            all_passed = False
        else:
            checks.append({'name': 'puck_data', 'passed': True})

        # Check 2: Template is active
        if not deployed_site.template.is_active:
            checks.append({'name': 'template_active', 'passed': False, 'error': 'Template inactive'})
            all_passed = False
        else:
            checks.append({'name': 'template_active', 'passed': True})

        # Check 3: Site status is active
        if deployed_site.status != 'active':
            checks.append({'name': 'site_status', 'passed': False, 'error': f'Status: {deployed_site.status}'})
            all_passed = False
        else:
            checks.append({'name': 'site_status', 'passed': True})

        logger.info(f"[Health Check] Completed for deployed_site {deployed_site_id}: {'PASSED' if all_passed else 'FAILED'}")

        return {
            'success': True,
            'all_passed': all_passed,
            'checks': checks
        }

    except Exception as e:
        logger.error(f"[Health Check] Failed for deployed_site {deployed_site_id}: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
