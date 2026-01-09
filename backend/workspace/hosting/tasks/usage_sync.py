"""
Usage synchronization tasks
Sync cached usage data to database for billing and limit enforcement
"""
import logging
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from django.db.models import F, Q, Count, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from decimal import Decimal

logger = logging.getLogger(__name__)


@shared_task(name='workspace_hosting.sync_bandwidth_usage')
def sync_bandwidth_usage():
    """
    Sync bandwidth from cache to HostingEnvironment
    Runs every 5 minutes via celery beat
    """
    from workspace.hosting.models import HostingEnvironment

    synced_count = 0
    error_count = 0

    # Get all active hosting environments
    hosting_envs = HostingEnvironment.objects.filter(
        status__in=['active', 'grace_period']
    )

    for hosting_env in hosting_envs:
        try:
            bandwidth_cache_key = f'bandwidth:hosting_env:{hosting_env.id}'
            requests_cache_key = f'requests:hosting_env:{hosting_env.id}'

            # Get cached bandwidth and requests
            cached_bandwidth_gb = cache.get(bandwidth_cache_key, Decimal('0'))
            cached_requests = cache.get(requests_cache_key, 0)

            if cached_bandwidth_gb > 0:
                # Increment bandwidth atomically
                hosting_env.increment_bandwidth_usage(float(cached_bandwidth_gb))

                # Clear cache after sync
                cache.delete(bandwidth_cache_key)
                cache.delete(requests_cache_key)

                logger.debug(
                    f"Synced {cached_bandwidth_gb}GB bandwidth for hosting_env {hosting_env.id}"
                )
                synced_count += 1

        except Exception as e:
            logger.error(
                f"Failed to sync bandwidth for hosting_env {hosting_env.id}: {e}",
                exc_info=True
            )
            error_count += 1
            continue

    logger.info(
        f"Bandwidth sync complete: {synced_count} synced, {error_count} errors"
    )

    return {
        'synced_count': synced_count,
        'error_count': error_count
    }


@shared_task(name='workspace_hosting.sync_storage_usage')
def sync_storage_usage():
    """
    Calculate storage from S3 and sync to HostingEnvironment
    Runs daily at 2 AM via celery beat
    """
    from workspace.hosting.models import HostingEnvironment
    from workspace.hosting.services.resource_usage_service import ResourceUsageService

    usage_service = ResourceUsageService()
    synced_count = 0
    error_count = 0

    hosting_envs = HostingEnvironment.objects.filter(
        status__in=['active', 'grace_period']
    )

    for hosting_env in hosting_envs:
        try:
            # Calculate storage from S3
            storage_gb = usage_service._calculate_storage_usage(hosting_env)

            # Update storage atomically
            HostingEnvironment.objects.filter(pk=hosting_env.pk).update(
                storage_used_gb=Decimal(str(storage_gb)),
                last_usage_sync=timezone.now()
            )

            logger.debug(
                f"Synced {storage_gb}GB storage for hosting_env {hosting_env.id}"
            )
            synced_count += 1

        except Exception as e:
            logger.error(
                f"Failed to sync storage for hosting_env {hosting_env.id}: {e}",
                exc_info=True
            )
            error_count += 1
            continue

    logger.info(
        f"Storage sync complete: {synced_count} synced, {error_count} errors"
    )

    return {
        'synced_count': synced_count,
        'error_count': error_count
    }


@shared_task(name='workspace_hosting.sync_site_counts')
def sync_site_counts():
    """
    Update active site counts for all hosting environments
    Runs every 15 minutes via celery beat
    """
    from workspace.hosting.models import HostingEnvironment, DeployedSite
    from django.db.models import Count

    try:
        updated_count = 0

        # Get site counts per hosting environment
        site_counts = dict(
            DeployedSite.objects.filter(
                status__in=['deploying', 'active', 'maintenance']
            ).values('hosting_environment').annotate(
                cnt=Count('id')
            ).values_list('hosting_environment', 'cnt')
        )

        # Update each hosting environment (Django doesn't support Subquery in update())
        hosting_envs = HostingEnvironment.objects.filter(
            status__in=['active', 'grace_period']
        )

        for hosting_env in hosting_envs:
            new_count = site_counts.get(hosting_env.pk, 0)
            if hosting_env.active_sites_count != new_count:
                hosting_env.active_sites_count = new_count
                hosting_env.save(update_fields=['active_sites_count', 'updated_at'])
                updated_count += 1

        logger.info(f"Site counts synced successfully: {updated_count} updated")

        return {'success': True, 'updated_count': updated_count}

    except Exception as e:
        logger.error(f"Failed to sync site counts: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task(name='workspace_hosting.enforce_limits_on_overage')
def enforce_limits_on_overage():
    """
    Enforce limits when users exceed their quotas
    Runs every hour via celery beat
    """
    from workspace.hosting.models import HostingEnvironment

    enforced_count = 0
    error_count = 0

    # Find hosting environments exceeding storage limits
    # Check against capabilities (not deprecated fields)
    over_limit_envs = []
    for hosting_env in HostingEnvironment.objects.filter(status='active'):
        storage_limit = Decimal(str(hosting_env.capabilities.get('storage_gb', 0)))
        if storage_limit > 0 and hosting_env.storage_used_gb > storage_limit:
            over_limit_envs.append(hosting_env)

    for hosting_env in over_limit_envs:
        try:
            # Check overage severity - uses capabilities
            storage_limit = Decimal(str(hosting_env.capabilities.get('storage_gb', 0)))
            storage_overage_pct = (
                (hosting_env.storage_used_gb - storage_limit) /
                storage_limit * 100
            )

            # Soft limit: 10-20% overage - Warning email only
            if storage_overage_pct <= 20:
                logger.warning(
                    f"Soft limit breach for hosting_env {hosting_env.id}: "
                    f"storage {storage_overage_pct:.1f}%"
                )
                # TODO: Send warning email

            # Hard limit: >20% overage - Suspend new deployments
            else:
                logger.error(
                    f"Hard limit breach for hosting_env {hosting_env.id}: "
                    f"storage {storage_overage_pct:.1f}%"
                )

                # Put in grace period
                hosting_env.status = 'grace_period'
                hosting_env.grace_period_end = timezone.now() + timezone.timedelta(days=7)
                hosting_env.save(update_fields=['status', 'grace_period_end', 'updated_at'])

                # TODO: Send urgent notification email

            enforced_count += 1

        except Exception as e:
            logger.error(
                f"Failed to enforce limits for hosting_env {hosting_env.id}: {e}",
                exc_info=True
            )
            error_count += 1
            continue

    logger.info(
        f"Limit enforcement complete: {enforced_count} processed, {error_count} errors"
    )

    return {
        'enforced_count': enforced_count,
        'error_count': error_count
    }


@shared_task(name='workspace_hosting.reset_monthly_bandwidth')
def reset_monthly_bandwidth():
    """
    Reset bandwidth counters at start of billing cycle
    Runs on 1st of each month via celery beat
    """
    from workspace.hosting.models import HostingEnvironment

    try:
        updated_count = HostingEnvironment.objects.filter(
            status__in=['active', 'grace_period']
        ).update(
            bandwidth_used_gb=0,
            updated_at=timezone.now()
        )

        logger.info(f"Reset bandwidth for {updated_count} hosting environments")

        return {
            'success': True,
            'reset_count': updated_count
        }

    except Exception as e:
        logger.error(f"Failed to reset monthly bandwidth: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
