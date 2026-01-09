"""
Storefront Password Protection Middleware (Concern #2)

Shopify pattern: "Infrastructure live, business not live"

Security Model:
- Intercepts ALL requests to storefront domains
- Checks if password protection is enabled
- Validates session before serving theme
- Session-based (not per-request password)

Flow:
1. User visits mikes-store.huzilerz.com
2. Middleware resolves DeployedSite from hostname
3. Check: Password enabled? → Check session
4. No session → Return password form (HTML)
5. User submits password → Validate → Set session
6. Redirect back → Middleware sees session → Serve theme
"""
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)


class StorefrontPasswordMiddleware(MiddlewareMixin):
    """
    Gate storefront access with password protection

    CRITICAL: Must run BEFORE theme is served
    Place high in MIDDLEWARE list (after session middleware)
    """

    # Paths that bypass password check (infrastructure/admin paths)
    BYPASS_PATHS = [
        '/admin/',
        '/graphql',  # Admin GraphQL (different domain)
        '/api/workspaces/hosting/storefront/unlock/',  # Password submission endpoint
        '/api/',  # Other API endpoints
        '/static/',
        '/media/',
        '/theme-media/',  # Theme preview images/screenshots
        '/__debug__/',  # Django Debug Toolbar
    ]

    def process_request(self, request):
        """
        Intercept request and check password protection

        Returns:
            HttpResponse: Password form if locked
            None: Continue to theme if unlocked
        """
        # Skip for bypass paths (admin, API, static files)
        if any(request.path.startswith(path) for path in self.BYPASS_PATHS):
            return None

        # Resolve DeployedSite from hostname
        site = self._resolve_deployed_site(request)

        # Attach site to request for downstream views (avoid double lookup)
        request.site = site
        
        if not site:
            # Not a storefront domain (maybe admin domain)
            return None

        # Check if password protection is enabled
        if not site.requires_password:
            # No password required → Continue to theme
            return None

        # Check session: Has user already entered password?
        session_key = f"storefront_access_{site.id}"

        if request.session.get(session_key) is True:
            # Session valid → Continue to theme
            logger.debug(f"Storefront access granted via session for site {site.id}")
            return None

        # No valid session → Show password form
        logger.info(
            f"Password required for site {site.id} ({site.subdomain}) - "
            f"showing password form to IP {self._get_client_ip(request)}"
        )

        return self._render_password_form(request, site)

    def _resolve_deployed_site(self, request):
        """
        Resolve DeployedSite from request hostname or X-Store-Hostname header

        Lookup Priority (matches StoreIdentificationMiddleware pattern):
        1. X-Store-Hostname header (sent by themes from different domain, e.g., localhost:3001)
        2. 'store' query param (DEBUG ONLY - for quick testing)
        3. Subdomain match (*.huzilerz.com)
        4. Custom domain match (verified custom domains)
        5. DEBUG mode: Direct subdomain lookup (for local development)

        Args:
            request: Django HTTP request

        Returns:
            DeployedSite or None

        Caching:
            Results cached for 60s to reduce DB hits

        Security:
            - All lookups filter by active status
            - Cache keys are isolated per hostname
            - Stale cache entries are automatically cleaned up
        """
        from workspace.hosting.models import DeployedSite
        from django.conf import settings
        from django.db import models

        # Step 1: Determine hostname
        # Priority:
        # A. X-Store-Hostname (explicit header for proxies/dev)
        # B. 'store' query param (DEBUG ONLY)
        # C. Host header
        
        hostname = None
        store_hostname = request.META.get('HTTP_X_STORE_HOSTNAME')

        if store_hostname:
            hostname = store_hostname.strip().lower()
        elif settings.DEBUG and request.GET.get('store'):
            hostname = request.GET.get('store').strip().lower()
        else:
            hostname = request.get_host().split(':')[0].lower()

        if not hostname:
            return None

        # Step 2: Check cache first (performance optimization)
        cache_key = f"password_site_lookup:{hostname}"
        cached_site_id = cache.get(cache_key)

        if cached_site_id:
            try:
                return DeployedSite.objects.select_related('workspace').get(
                    id=cached_site_id,
                    status='active'
                )
            except DeployedSite.DoesNotExist:
                # Stale cache - site was deleted or deactivated
                cache.delete(cache_key)

        # Step 3: Try subdomain match (*.huzilerz.com)
        if '.huzilerz.com' in hostname:
            subdomain = hostname.replace('.huzilerz.com', '')
            try:
                # Check both subdomain and custom_subdomain fields
                site = DeployedSite.objects.select_related('workspace').filter(
                    status='active'
                ).filter(
                    models.Q(subdomain=subdomain) | models.Q(custom_subdomain=subdomain)
                ).first()

                if site:
                    cache.set(cache_key, str(site.id), timeout=60)
                    return site

            except Exception as e:
                logger.warning(
                    f"Error looking up site by subdomain '{subdomain}': {str(e)}"
                )

        # Step 4: Try custom domain match
        try:
            site = DeployedSite.objects.select_related('workspace').get(
                custom_domains__domain=hostname,
                custom_domains__status='active',
                status='active'
            )
            cache.set(cache_key, str(site.id), timeout=60)
            return site
        except DeployedSite.DoesNotExist:
            pass
        except DeployedSite.MultipleObjectsReturned:
            # Edge case: multiple sites with same domain (data integrity issue)
            logger.error(
                f"Multiple DeployedSites found for domain '{hostname}' - "
                f"data integrity issue, returning first match"
            )
            site = DeployedSite.objects.select_related('workspace').filter(
                custom_domains__domain=hostname,
                custom_domains__status='active',
                status='active'
            ).first()
            if site:
                cache.set(cache_key, str(site.id), timeout=60)
                return site

        # Step 5: DEBUG mode - try direct subdomain lookup
        # This handles: localhost with X-Store-Hostname: sneakers
        if settings.DEBUG:
            try:
                # In dev mode, X-Store-Hostname may be just the subdomain (e.g., "sneakers")
                site = DeployedSite.objects.select_related('workspace').filter(
                    status='active'
                ).filter(
                    models.Q(subdomain=hostname) | models.Q(custom_subdomain=hostname)
                ).first()

                if site:
                    cache.set(cache_key, str(site.id), timeout=60)
                    logger.debug(
                        f"DEV mode: Resolved site '{site.subdomain}' from hostname '{hostname}'"
                    )
                    return site

            except Exception as e:
                logger.warning(
                    f"DEV mode: Error looking up site by direct hostname '{hostname}': {str(e)}"
                )

        # No site found for this hostname
        return None

    def _render_password_form(self, request, site):
        """
        Render password entry form using branded template

        Args:
            request: Django HTTP request
            site: DeployedSite instance

        Returns:
            HttpResponse: HTML password form

        Template Context:
            - site_name: Store name for display
            - description: Custom message from merchant (e.g., 'Coming soon!')
            - site_id: Site ID for form submission
            - next_url: URL to redirect to after successful login
            - unlock_url: Password validation endpoint
            - error: Error message if password was wrong
        """
        from django.template.loader import render_to_string
        from django.middleware.csrf import get_token

        # Get error message from session (if password was wrong)
        error = request.session.pop('password_error', None)

        # Ensure CSRF token is available
        csrf_token = get_token(request)

        # Build template context
        context = {
            'site_name': site.site_name or 'This Store',
            'description': site.password_description or '',
            'site_id': str(site.id),
            'next_url': request.get_full_path(),
            'unlock_url': '/api/workspaces/hosting/storefront/unlock/',
            'error': error,
            'csrf_token': csrf_token,
        }

        # Render branded template
        try:
            html = render_to_string('password_protected.html', context, request=request)
            return HttpResponse(html, status=200)
        except Exception as e:
            # Fallback to simple error page if template fails
            logger.error(f"Failed to render password template: {e}")
            return HttpResponse(
                "<h1>Password Required</h1><p>Please contact the store owner.</p>",
                status=200
            )

    def _get_client_ip(self, request):
        """Get client IP address for logging"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
