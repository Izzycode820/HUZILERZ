"""
CDN Cache Service
Manage CloudFront caching for workspace content
Provides traffic spike protection through aggressive caching
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class CDNCacheService:
    """
    CDN cache control for workspace content
    Protects backend from viral traffic spikes
    """

    # Cache TTLs by content type (seconds)
    CACHE_TTLS = {
        # Static assets (long cache)
        'product_image': 86400,          # 24 hours
        'theme_asset': 604800,           # 7 days
        'theme_css': 604800,             # 7 days
        'theme_js': 604800,              # 7 days
        'logo': 2592000,                 # 30 days
        'favicon': 2592000,              # 30 days

        # Dynamic content (short cache)
        'product_data': 300,             # 5 minutes
        'category_data': 600,          # 10 minutes
        'homepage': 300,                 # 5 minutes
        'product_listing': 600,          # 10 minutes

        # No cache
        'cart_data': 0,                  # Never cache
        'checkout': 0,                   # Never cache
        'user_account': 0,               # Never cache
        'graphql_mutation': 0,           # Never cache mutations
    }

    @staticmethod
    def get_cache_headers(workspace_id: str, content_type: str, custom_ttl: int = None) -> Dict[str, str]:
        """
        Get cache control headers based on content type

        Args:
            workspace_id: Workspace UUID
            content_type: Type of content (e.g., 'product_image', 'cart_data')
            custom_ttl: Optional custom TTL override

        Returns:
            Dictionary of cache headers
        """
        # Get TTL
        ttl = custom_ttl if custom_ttl is not None else CDNCacheService.CACHE_TTLS.get(content_type, 3600)

        if ttl == 0:
            # No cache
            return {
                'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Workspace-ID': workspace_id,
            }
        else:
            # Cache enabled
            return {
                'Cache-Control': f'public, max-age={ttl}, s-maxage={ttl}, stale-while-revalidate=86400',
                'X-Workspace-ID': workspace_id,
                'Vary': 'Accept-Encoding',
                'X-Content-Type': content_type,
            }

    @staticmethod
    def get_graphql_cache_headers(workspace_id: str, operation_type: str) -> Dict[str, str]:
        """
        Get cache headers for GraphQL responses

        Args:
            workspace_id: Workspace UUID
            operation_type: 'query', 'mutation', or 'subscription'

        Returns:
            Dictionary of cache headers
        """
        if operation_type == 'query':
            # Cache queries for 5 minutes
            ttl = 300
            return {
                'Cache-Control': f'private, max-age={ttl}',
                'X-Workspace-ID': workspace_id,
                'Vary': 'Authorization',
            }
        else:
            # Never cache mutations/subscriptions
            return {
                'Cache-Control': 'no-store, no-cache, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Workspace-ID': workspace_id,
            }

    @staticmethod
    def invalidate_workspace_cache(workspace_id: str, paths: List[str] = None) -> Dict[str, any]:
        """
        Invalidate CDN cache for workspace

        Args:
            workspace_id: Workspace UUID
            paths: Optional list of specific paths to invalidate (default: all)

        Returns:
            Invalidation result
        """
        from .infrastructure_facade import InfrastructureFacade

        try:
            infra_service = InfrastructureFacade.get_service()

            # Default to invalidating all workspace content
            if not paths:
                paths = ['/*']

            # Prefix paths with workspace folder
            workspace_paths = [f'/ws/{workspace_id}{path}' for path in paths]

            # Add GraphQL endpoint
            workspace_paths.append(f'/graphql?workspace={workspace_id}')

            result = infra_service.invalidate_cache(
                distribution_id='shared-pool-distribution',
                paths=workspace_paths
            )

            logger.info(f"Invalidated CDN cache for workspace {workspace_id}: {len(workspace_paths)} paths")
            return result

        except Exception as e:
            logger.error(f"Failed to invalidate CDN cache for workspace {workspace_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def invalidate_product_cache(workspace_id: str, product_id: str):
        """
        Invalidate cache for specific product

        Args:
            workspace_id: Workspace UUID
            product_id: Product ID
        """
        paths = [
            f'/products/{product_id}',
            f'/products/{product_id}/*',
            '/products',  # Product listing
            '/',  # Homepage (might feature this product)
        ]

        return CDNCacheService.invalidate_workspace_cache(workspace_id, paths)

    @staticmethod
    def invalidate_collection_cache(workspace_id: str, collection_id: str = None):
        """
        Invalidate cache for collection(s)

        Args:
            workspace_id: Workspace UUID
            collection_id: Optional specific collection ID
        """
        if collection_id:
            paths = [
                f'/collections/{collection_id}',
                f'/collections/{collection_id}/*',
            ]
        else:
            paths = ['/collections', '/collections/*']

        return CDNCacheService.invalidate_workspace_cache(workspace_id, paths)

    @staticmethod
    def warm_cache(workspace_id: str, urls: List[str]):
        """
        Pre-warm CDN cache by fetching URLs
        Useful after deployments or major updates

        Args:
            workspace_id: Workspace UUID
            urls: List of full URLs to warm
        """
        import requests
        from concurrent.futures import ThreadPoolExecutor

        def fetch_url(url):
            try:
                requests.get(url, timeout=10)
                logger.info(f"Cache warmed: {url}")
            except Exception as e:
                logger.warning(f"Cache warm failed for {url}: {str(e)}")

        # Warm cache in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(fetch_url, urls)

        logger.info(f"Cache warming completed for workspace {workspace_id}: {len(urls)} URLs")

    @staticmethod
    def get_theme_version_hash(customization) -> str:
        """
        Generate a version hash for a theme customization

        Uses last_edited_at timestamp to create a unique version identifier.
        When theme changes, last_edited_at updates automatically, invalidating cache.

        Args:
            customization: TemplateCustomization instance

        Returns:
            str: 8-character hash of theme version

        Examples:
            >>> from theme.models import TemplateCustomization
            >>> customization = TemplateCustomization.objects.get(id="...")
            >>> version_hash = CDNCacheService.get_theme_version_hash(customization)
            >>> # Use in cache key
            >>> cache_key = f"puck_data:{version_hash}"
        """
        import hashlib

        # Use last_edited_at as version identifier
        # This automatically updates on every save(), making cache keys version-specific
        version_string = str(customization.last_edited_at.isoformat())

        # Create short hash (8 chars is enough for uniqueness)
        version_hash = hashlib.md5(version_string.encode()).hexdigest()[:8]

        return version_hash
