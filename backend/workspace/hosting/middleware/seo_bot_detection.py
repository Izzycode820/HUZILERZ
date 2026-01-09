"""
SEO Bot Detection Middleware (Phase 4: SEO Implementation)

Dynamic Rendering Strategy (Google-approved):
- Detect search engine bots and social media crawlers
- Serve optimized HTML to bots (currently same as users)
- Serve SPA to regular users
- Log bot traffic for monitoring

Reference:
https://developers.google.com/search/docs/advanced/javascript/dynamic-rendering

Future Enhancement (Part 3 - Optional):
- Serve prerendered static HTML snapshots to bots
- Use Puppeteer/Playwright to generate snapshots
- Cache prerendered pages per theme version
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from workspace.hosting.services.seo_service import SEOService

logger = logging.getLogger(__name__)


class SEOBotMiddleware(MiddlewareMixin):
    """
    Detect search engine bots and prepare for dynamic rendering

    Currently:
    - Detects bots (Google, Bing, Facebook, etc.)
    - Logs bot traffic for monitoring
    - Sets request.is_bot flag for views to use

    Future (Part 3):
    - Serve prerendered HTML snapshots to bots
    - Implement cache warming for critical pages
    - Add bot-specific optimizations

    IMPORTANT:
    - Must run AFTER StorefrontPasswordMiddleware (bots can't enter passwords)
    - Must run BEFORE view processing (to set is_bot flag)
    """

    # Paths that should skip bot detection (no SEO value)
    SKIP_PATHS = [
        '/admin/',
        '/graphql',
        '/api/',
        '/static/',
        '/media/',
        '/theme-media/',  # Theme preview images/screenshots
        '/__debug__/',
        '/favicon.ico',
        '/robots.txt',
        '/sitemap.xml',
    ]

    def process_request(self, request):
        """
        Detect if request is from a bot and set request.is_bot flag

        Args:
            request: Django HTTP request

        Returns:
            None: Continue to view (bots and users get same response for now)
        """
        # Skip bot detection for non-storefront paths
        if any(request.path.startswith(path) for path in self.SKIP_PATHS):
            request.is_bot = False
            return None

        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Detect if request is from a bot
        is_bot = SEOService.is_bot_request(user_agent)
        request.is_bot = is_bot

        # Log bot traffic (useful for monitoring SEO crawl activity)
        if is_bot:
            logger.info(
                f"SEO Bot Detected | "
                f"Path: {request.path} | "
                f"Host: {request.get_host()} | "
                f"UA: {user_agent[:150]}"
            )

            # Optional: Track bot crawl metrics (future enhancement)
            # from workspace.hosting.services.metrics_service import MetricsService
            # MetricsService.track_bot_crawl(
            #     user_agent=user_agent,
            #     path=request.path,
            #     host=request.get_host()
            # )

        # For now, bots and users get the same response
        # The serve_storefront view already injects SEO meta tags server-side
        # This is sufficient for 70-80% of SEO benefits

        # Future: Serve prerendered HTML to bots here
        # if is_bot:
        #     prerendered_html = get_prerendered_page(request.path, site_id)
        #     if prerendered_html:
        #         return HttpResponse(prerendered_html, content_type='text/html')

        return None

    def process_response(self, request, response):
        """
        Add SEO-related headers to response

        Args:
            request: Django HTTP request
            response: Django HTTP response

        Returns:
            HttpResponse: Modified response with SEO headers
        """
        # Skip for non-HTML responses
        if not response.get('Content-Type', '').startswith('text/html'):
            return response

        # Add X-Robots-Tag header for additional SEO control
        # This complements the meta robots tag in the HTML
        if hasattr(request, 'is_bot') and request.is_bot:
            # Allow indexing for bots (unless overridden by suspended status)
            response['X-Robots-Tag'] = 'index, follow'

        # Add Link header for canonical URL (helps with duplicate content)
        if hasattr(request, 'get_host'):
            canonical = f"https://{request.get_host()}{request.path}"
            response['Link'] = f'<{canonical}>; rel="canonical"'

        return response


# Helper function for future prerendering implementation
def get_prerendered_page(path: str, site_id: str) -> str:
    """
    Get prerendered HTML snapshot for a page (future implementation)

    Args:
        path: Request path (e.g., '/', '/collections/shoes')
        site_id: DeployedSite UUID

    Returns:
        str: Prerendered HTML or None if not available

    TODO: Implement prerendering service
    - Use Puppeteer/Playwright to render React app
    - Cache result per (theme_version, path) key
    - Invalidate cache on theme publish
    - Warm cache for critical pages (homepage, top collections)
    """
    from django.core.cache import cache

    # Build cache key
    cache_key = f"prerender:{site_id}:{path}"

    # Try to get from cache
    prerendered_html = cache.get(cache_key)

    if prerendered_html:
        logger.debug(f"Serving prerendered HTML from cache: {cache_key}")
        return prerendered_html

    # Not in cache - would trigger async prerendering here
    # For now, return None (bot will get regular server-side injected HTML)
    logger.debug(f"No prerendered HTML for: {cache_key}")
    return None
