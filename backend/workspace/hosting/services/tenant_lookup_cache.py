"""
Tenant Lookup Cache Service

Fast Redis-based cache for mapping hostnames to workspace/tenant information.
Critical for production performance - avoids DB queries on every request.

Cache Keys:
- tenant:hostname:{hostname} -> {workspace_id, tenant_theme_id, puck_data_version, subdomain}

Invalidation Events:
- Theme activation
- Domain changes
- Custom domain addition/removal
- Workspace updates
"""
import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class TenantLookupCache:
    """
    High-performance tenant lookup cache

    Stores hostname -> workspace mapping with auto-invalidation
    """

    # Cache TTLs
    HOSTNAME_TTL = 3600  # 1 hour for hostname lookups
    WORKSPACE_TTL = 1800  # 30 minutes for workspace data
    CUSTOM_DOMAIN_TTL = 7200  # 2 hours for custom domains (change less frequently)

    # Key prefixes
    HOSTNAME_PREFIX = "tenant:hostname"
    WORKSPACE_PREFIX = "tenant:workspace"
    CUSTOM_DOMAIN_PREFIX = "tenant:custom_domain"

    @staticmethod
    def _hostname_key(hostname: str) -> str:
        """Generate cache key for hostname lookup"""
        # Normalize hostname (lowercase, strip www)
        normalized = hostname.lower().strip().replace('www.', '')
        return f"{TenantLookupCache.HOSTNAME_PREFIX}:{normalized}"

    @staticmethod
    def _workspace_key(workspace_id: str) -> str:
        """Generate cache key for workspace data"""
        return f"{TenantLookupCache.WORKSPACE_PREFIX}:{workspace_id}"

    @staticmethod
    def _custom_domain_key(domain: str) -> str:
        """Generate cache key for custom domain"""
        normalized = domain.lower().strip()
        return f"{TenantLookupCache.CUSTOM_DOMAIN_PREFIX}:{normalized}"

    @classmethod
    def get_workspace_by_hostname(cls, hostname: str) -> Optional[Dict[str, Any]]:
        """
        Fast lookup of workspace by hostname

        Args:
            hostname: The hostname (subdomain.huzilerz.com or custom.com)

        Returns:
            Dict with workspace_id, tenant_theme_id, puck_data_version, etc.
            None if not found in cache
        """
        cache_key = cls._hostname_key(hostname)
        cached = cache.get(cache_key)

        if cached:
            logger.debug(f"[TenantCache] HIT for hostname {hostname}")
            cached['from_cache'] = True
            return cached

        logger.debug(f"[TenantCache] MISS for hostname {hostname}")
        return None

    @classmethod
    def set_workspace_for_hostname(
        cls,
        hostname: str,
        workspace_id: str,
        tenant_theme_id: Optional[str] = None,
        puck_data_version: Optional[int] = None,
        subdomain: Optional[str] = None,
        custom_domain: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Cache workspace information for a hostname

        Args:
            hostname: The hostname
            workspace_id: UUID of workspace
            tenant_theme_id: UUID of active theme customization
            puck_data_version: Version number for cache busting
            subdomain: The subdomain slug
            custom_domain: True if this is a custom domain
            metadata: Additional metadata to cache
        """
        cache_key = cls._hostname_key(hostname)

        data = {
            'workspace_id': str(workspace_id),
            'tenant_theme_id': str(tenant_theme_id) if tenant_theme_id else None,
            'puck_data_version': puck_data_version,
            'subdomain': subdomain,
            'custom_domain': custom_domain,
            'cached_at': timezone.now().isoformat(),
            'metadata': metadata or {}
        }

        # Use longer TTL for custom domains (they change less frequently)
        ttl = cls.CUSTOM_DOMAIN_TTL if custom_domain else cls.HOSTNAME_TTL

        cache.set(cache_key, data, timeout=ttl)
        logger.info(f"[TenantCache] SET hostname {hostname} -> workspace {workspace_id} (TTL: {ttl}s)")

    @classmethod
    def get_workspace_data(cls, workspace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached workspace data

        Args:
            workspace_id: UUID of workspace

        Returns:
            Dict with workspace configuration
        """
        cache_key = cls._workspace_key(workspace_id)
        cached = cache.get(cache_key)

        if cached:
            logger.debug(f"[TenantCache] HIT for workspace {workspace_id}")
            return cached

        logger.debug(f"[TenantCache] MISS for workspace {workspace_id}")
        return None

    @classmethod
    def set_workspace_data(
        cls,
        workspace_id: str,
        plan_tier: str,
        enabled_payment_methods: list,
        features: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Cache workspace configuration data

        Args:
            workspace_id: UUID of workspace
            plan_tier: Subscription plan tier
            enabled_payment_methods: List of payment methods
            features: Enabled features dict
            metadata: Additional metadata
        """
        cache_key = cls._workspace_key(workspace_id)

        data = {
            'workspace_id': str(workspace_id),
            'plan_tier': plan_tier,
            'enabled_payment_methods': enabled_payment_methods,
            'features': features or {},
            'metadata': metadata or {},
            'cached_at': timezone.now().isoformat()
        }

        cache.set(cache_key, data, timeout=cls.WORKSPACE_TTL)
        logger.info(f"[TenantCache] SET workspace {workspace_id} config")

    @classmethod
    def invalidate_hostname(cls, hostname: str):
        """
        Invalidate cache for a specific hostname

        Args:
            hostname: The hostname to invalidate
        """
        cache_key = cls._hostname_key(hostname)
        cache.delete(cache_key)
        logger.info(f"[TenantCache] INVALIDATED hostname {hostname}")

    @classmethod
    def invalidate_workspace(cls, workspace_id: str):
        """
        Invalidate all cache entries for a workspace

        This includes:
        - Workspace configuration
        - All hostnames pointing to this workspace

        Args:
            workspace_id: UUID of workspace
        """
        # Invalidate workspace data
        workspace_key = cls._workspace_key(workspace_id)
        cache.delete(workspace_key)

        # Note: Can't easily invalidate all hostnames pointing to workspace
        # without storing reverse mapping. For now, rely on TTL expiration.
        # For immediate update, manually invalidate specific hostnames.

        logger.info(f"[TenantCache] INVALIDATED workspace {workspace_id}")

    @classmethod
    def invalidate_all_for_workspace(cls, workspace_id: str, subdomain: Optional[str] = None, custom_domains: Optional[list] = None):
        """
        Comprehensive invalidation for a workspace and all its hostnames

        Args:
            workspace_id: UUID of workspace
            subdomain: The subdomain (e.g., "mystore.huzilerz.com")
            custom_domains: List of custom domains
        """
        # Invalidate workspace config
        cls.invalidate_workspace(workspace_id)

        # Invalidate subdomain
        if subdomain:
            cls.invalidate_hostname(subdomain)

        # Invalidate custom domains
        if custom_domains:
            for domain in custom_domains:
                cls.invalidate_hostname(domain)

        logger.info(
            f"[TenantCache] INVALIDATED ALL for workspace {workspace_id} "
            f"(subdomain: {subdomain}, custom_domains: {len(custom_domains) if custom_domains else 0})"
        )

    @classmethod
    def refresh_workspace(cls, workspace_id: str):
        """
        Refresh cache for a workspace by fetching fresh data from DB

        Args:
            workspace_id: UUID of workspace
        """
        from workspace.core.models import Workspace
        from workspace.hosting.models import WorkspaceInfrastructure, DeployedSite

        try:
            workspace = Workspace.objects.select_related(
                'owner__subscription__plan'
            ).get(id=workspace_id)

            # Get infrastructure
            try:
                infra = WorkspaceInfrastructure.objects.get(workspace=workspace)
                subdomain = infra.subdomain
            except WorkspaceInfrastructure.DoesNotExist:
                logger.warning(f"No infrastructure found for workspace {workspace_id}")
                return

            # Get deployed site
            try:
                deployed_site = DeployedSite.objects.select_related(
                    'customization'
                ).get(workspace=workspace)
                tenant_theme_id = deployed_site.customization.id if deployed_site.customization else None
                puck_data_version = deployed_site.customization.last_edited_at.timestamp() if deployed_site.customization else 0
            except DeployedSite.DoesNotExist:
                tenant_theme_id = None
                puck_data_version = 0

            # Cache hostname lookup
            cls.set_workspace_for_hostname(
                hostname=subdomain,
                workspace_id=workspace_id,
                tenant_theme_id=tenant_theme_id,
                puck_data_version=int(puck_data_version),
                subdomain=subdomain,
                custom_domain=False
            )

            # Cache custom domains if any
            from workspace.hosting.models import CustomDomain
            custom_domains = CustomDomain.objects.filter(
                workspace=workspace,
                status='active'
            )

            for custom_domain in custom_domains:
                cls.set_workspace_for_hostname(
                    hostname=custom_domain.domain_name,
                    workspace_id=workspace_id,
                    tenant_theme_id=tenant_theme_id,
                    puck_data_version=int(puck_data_version),
                    subdomain=subdomain,
                    custom_domain=True
                )

            # Cache workspace config
            subscription = getattr(workspace.owner, 'subscription', None)
            plan_tier = subscription.plan.tier if subscription else 'free'

            cls.set_workspace_data(
                workspace_id=workspace_id,
                plan_tier=plan_tier,
                enabled_payment_methods=[],  # Populate from workspace settings
                features={},  # Populate from plan
                metadata={
                    'workspace_name': workspace.name,
                    'workspace_slug': workspace.slug
                }
            )

            logger.info(f"[TenantCache] REFRESHED workspace {workspace_id}")

        except Workspace.DoesNotExist:
            logger.error(f"[TenantCache] Workspace {workspace_id} not found during refresh")

    @classmethod
    def warm_cache_for_all_workspaces(cls):
        """
        Warm cache for all active workspaces

        Use sparingly - typically only on deployment or cache flush
        """
        from workspace.core.models import Workspace

        active_workspaces = Workspace.objects.filter(
            status='active'
        ).values_list('id', flat=True)

        count = 0
        for workspace_id in active_workspaces:
            try:
                cls.refresh_workspace(str(workspace_id))
                count += 1
            except Exception as e:
                logger.error(f"[TenantCache] Failed to warm cache for workspace {workspace_id}: {e}")

        logger.info(f"[TenantCache] Warmed cache for {count} workspaces")

        return {'warmed': count, 'total': len(active_workspaces)}
