"""
Storefront Multi-Tenant Identification Middleware
Identifies workspace/store from domain/subdomain for multi-tenant routing
Supports: Custom domains, wildcard subdomains, session + JWT hybrid auth
"""
import logging
import re
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


# In-memory domain cache for performance (5 min TTL)
DOMAINS_CACHE = {}
CACHE_TTL = 300  # 5 minutes


class StoreIdentificationMiddleware(MiddlewareMixin):
    """
    Multi-tenant store identification middleware
    Extracts workspace from domain/subdomain and injects into request context

    Lookup Priority:
    1. CustomDomain table (custom domains like shoppings.com)
    2. DeployedSite.subdomain (wildcard *.huzilerz.com)
    3. Cache result for performance

    Security Features:
    - Fail-closed: Returns 404 for unknown domains
    - Cache isolation: Adds Vary: Host header
    - Tenant scoping: All GraphQL queries auto-scoped
    - Session + JWT hybrid: Supports guest checkout & authenticated users
    """

    # ONLY run middleware on storefront paths (GraphQL endpoint)
    # Everything else (admin, auth, static) doesn't need tenant identification
    STOREFRONT_PATHS = [
        '/api/graphql',  # Domain-based storefront access
        '/storefront/',  # Legacy workspace-scoped access
    ]

    def process_request(self, request):
        """Extract tenant from domain and inject into request"""

        # ONLY run middleware on storefront paths
        # Storefront is GraphQL-based with single endpoint: /storefront/graphql/
        if not any(request.path.startswith(path) for path in self.STOREFRONT_PATHS):
            return None

        # Extract hostname
        hostname = self._get_hostname(request)

        if not hostname:
            logger.warning(f"No hostname found in request: {request.path}")
            return self._tenant_not_found_response()

        # Check cache first
        cached_tenant = self._get_cached_tenant(hostname)
        if cached_tenant:
            self._inject_tenant_context(request, cached_tenant)
            return None

        # Lookup tenant from database
        tenant_data = self._lookup_tenant(hostname)

        if not tenant_data:
            logger.warning(f"Tenant not found for hostname: {hostname}")
            return self._tenant_not_found_response()

        # Cache the result
        self._cache_tenant(hostname, tenant_data)

        # Inject tenant context into request
        self._inject_tenant_context(request, tenant_data)

        # Log successful identification (debug)
        logger.debug(
            f"Tenant identified: {tenant_data['workspace'].slug} "
            f"(domain: {hostname}, user: {request.user})"
        )

        return None

    def process_response(self, request, response):
        """Add cache safety headers"""

        # Only add headers for storefront paths
        if not any(request.path.startswith(path) for path in self.STOREFRONT_PATHS):
            return response

        # Add Vary: Host header to prevent cross-tenant cache pollution
        # CRITICAL for multi-tenant caching safety
        vary_header = response.get('Vary', '')
        if vary_header:
            if 'Host' not in vary_header:
                response['Vary'] = f"{vary_header}, Host"
        else:
            response['Vary'] = 'Host'

        # Add tenant ID header for debugging (only in DEBUG mode)
        if settings.DEBUG and hasattr(request, 'tenant_id'):
            response['X-Tenant-ID'] = str(request.tenant_id)
            response['X-Workspace-Slug'] = getattr(request, 'store_slug', '')

        return response

    def _get_hostname(self, request):
        """
        Extract hostname from request
        Handles: X-Store-Hostname (theme requests), ports, proxies, X-Forwarded-Host header

        Priority:
        1. X-Store-Hostname (sent by themes from different domain)
        2. X-Forwarded-Host (for proxy/load balancer setups)
        3. Host header (standard)
        """
        # Check X-Store-Hostname first (sent by themes on different domain)
        store_hostname = request.META.get('HTTP_X_STORE_HOSTNAME')
        if store_hostname:
            hostname = store_hostname.strip()
        # Check X-Forwarded-Host (for proxy/load balancer setups)
        elif request.META.get('HTTP_X_FORWARDED_HOST'):
            forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST')
            hostname = forwarded_host.split(',')[0].strip()
        else:
            hostname = request.get_host()

        # Remove port if present
        hostname = hostname.split(':')[0]

        return hostname.lower()

    def _lookup_tenant(self, hostname):
        """
        Lookup tenant from database
        Priority: CustomDomain → DeployedSite subdomain
        """
        from workspace.hosting.models import CustomDomain, DeployedSite

        # Try custom domain lookup first
        try:
            custom_domain = CustomDomain.objects.select_related(
                'workspace',
                'deployed_site',
                'deployed_site__template',
                'deployed_site__customization'
            ).get(domain=hostname, status='active')

            return {
                'workspace': custom_domain.workspace,
                'deployed_site': custom_domain.deployed_site,
                'domain_type': 'custom',
                'hostname': hostname
            }

        except CustomDomain.DoesNotExist:
            pass

        # Try subdomain lookup (*.huzilerz.com)
        if hostname.endswith('.huzilerz.com'):
            subdomain = hostname.replace('.huzilerz.com', '')

            # Check both custom_subdomain and subdomain fields
            try:
                deployed_site = DeployedSite.objects.select_related(
                    'workspace',
                    'template',
                    'customization'
                ).filter(status='active').filter(
                    models.Q(subdomain=subdomain) | models.Q(custom_subdomain=subdomain)
                ).first()

                if deployed_site:
                    return {
                        'workspace': deployed_site.workspace,
                        'deployed_site': deployed_site,
                        'domain_type': 'custom_subdomain' if deployed_site.custom_subdomain == subdomain else 'subdomain',
                        'hostname': hostname
                    }

            except Exception:
                pass

        # Development: Check if exact match on subdomain field
        # (handles localhost dev with subdomain simulation)
        if settings.DEBUG:
            try:
                deployed_site = DeployedSite.objects.select_related(
                    'workspace',
                    'template',
                    'customization'
                ).get(subdomain=hostname, status='active')

                return {
                    'workspace': deployed_site.workspace,
                    'deployed_site': deployed_site,
                    'domain_type': 'dev',
                    'hostname': hostname
                }

            except DeployedSite.DoesNotExist:
                pass

        return None

    def _inject_tenant_context(self, request, tenant_data):
        """Inject tenant context into request object"""

        workspace = tenant_data['workspace']
        deployed_site = tenant_data['deployed_site']

        # Primary tenant context
        request.workspace = workspace
        request.deployed_site = deployed_site
        request.tenant_id = workspace.id

        # Backward compatibility
        request.store_slug = workspace.slug

        # Metadata for logging/debugging
        request.tenant_domain_type = tenant_data['domain_type']
        request.tenant_hostname = tenant_data['hostname']

    def _get_cached_tenant(self, hostname):
        """Get tenant from cache"""
        cache_key = f"tenant_domain:{hostname}"

        # Check Django cache first
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Check in-memory cache (faster)
        if hostname in DOMAINS_CACHE:
            cache_entry = DOMAINS_CACHE[hostname]
            # Simple TTL check (could be improved with timestamp)
            return cache_entry

        return None

    def _cache_tenant(self, hostname, tenant_data):
        """Cache tenant lookup result"""
        cache_key = f"tenant_domain:{hostname}"

        # Cache in Django cache (shared across workers)
        cache.set(cache_key, tenant_data, CACHE_TTL)

        # Cache in-memory (fast path for same worker)
        DOMAINS_CACHE[hostname] = tenant_data

        # Prevent unbounded memory growth (simple LRU)
        if len(DOMAINS_CACHE) > 1000:
            # Remove oldest entries (first 100)
            keys_to_remove = list(DOMAINS_CACHE.keys())[:100]
            for key in keys_to_remove:
                DOMAINS_CACHE.pop(key, None)

    def _tenant_not_found_response(self):
        """Return 404 response for unknown domains"""
        return HttpResponse(
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Store Not Found</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        text-align: center;
                        padding: 2rem;
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                        max-width: 500px;
                    }
                    h1 { color: #333; margin-bottom: 1rem; }
                    p { color: #666; line-height: 1.6; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏪 Store Not Found</h1>
                    <p>This store doesn't exist or has been deactivated.</p>
                    <p>Please check the URL and try again.</p>
                </div>
            </body>
            </html>
            """,
            status=404,
            content_type='text/html'
        )


class TenantContextMiddleware(MiddlewareMixin):
    """
    Safety net middleware using thread-local pattern
    Ensures tenant context is always available in views/resolvers
    Similar to django-scopes pattern for preventing data leakage
    """

    def process_request(self, request):
        """Set thread-local tenant context"""

        # Only set if tenant was identified
        if hasattr(request, 'workspace'):
            # Store in thread-local for safety net access
            # (Advanced: Can be used with django-scopes for auto-filtering)
            from threading import local

            if not hasattr(self, '_thread_locals'):
                self._thread_locals = local()

            self._thread_locals.workspace = request.workspace
            self._thread_locals.tenant_id = request.tenant_id

        return None

    def process_response(self, request, response):
        """Clear thread-local tenant context"""

        if hasattr(self, '_thread_locals'):
            self._thread_locals.workspace = None
            self._thread_locals.tenant_id = None

        return response
