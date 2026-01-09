"""
SEO Service (Phase 4: Prerendering/SEO)

Generates SEO meta tags for storefront HTML injection.
Achieves 70-80% of Shopify SEO benefits with minimal complexity.

Strategy:
- Server-side meta tag injection (crawlers see real HTML)
- Bot detection for dynamic rendering
- Version-based cache invalidation

Reference: HYDROGEN THEME (DONE ALL BUT 4 PrerenderingSEO dont DEL).md
"""
import logging
from typing import Dict, Optional
from django.utils.html import escape

logger = logging.getLogger(__name__)


class SEOService:
    """
    Service for generating SEO meta tags for storefront pages

    Provides:
    - Meta tag generation (title, description, OG tags)
    - Structured data markup (JSON-LD for Google)
    - Safe HTML escaping
    - Fallback defaults for missing data
    """

    # Default values for sites without custom SEO
    DEFAULT_DESCRIPTION_TEMPLATE = "Welcome to {site_name} - Your online store for quality products"
    DEFAULT_IMAGE_URL = "https://cdn.huzilerz.com/assets/default-og-image.jpg"  # TODO: Create default OG image

    @staticmethod
    def generate_meta_tags(deployed_site, request=None) -> Dict[str, str]:
        """
        Generate complete SEO meta tags for a deployed site

        Args:
            deployed_site: DeployedSite instance
            request: HttpRequest (optional, for dynamic URL generation)

        Returns:
            dict: {
                'title': str,
                'description': str,
                'keywords': str,
                'image': str,
                'url': str,
                'site_name': str,
                'og_type': str,
                'twitter_card': str
            }
        """
        # Get SEO values with fallbacks
        title = deployed_site.seo_title or deployed_site.site_name
        description = deployed_site.seo_description or SEOService.DEFAULT_DESCRIPTION_TEMPLATE.format(
            site_name=deployed_site.site_name
        )
        keywords = deployed_site.seo_keywords or ""
        image = deployed_site.seo_image_url or SEOService.DEFAULT_IMAGE_URL

        # Build canonical URL
        # Fix: DeployedSite has a reverse relationship to CustomDomain (one-to-many)
        # We need to find the primary verified custom domain
        primary_domain = deployed_site.custom_domains.filter(
            is_primary=True,
            status='verified'
        ).first()

        if primary_domain:
            base_url = f"https://{primary_domain.domain}"
        else:
            base_url = f"https://{deployed_site.subdomain}.huzilerz.com"

        # Build path from request if available
        path = request.path if request else "/"
        canonical_url = f"{base_url}{path}"

        # Escape all user-provided values for XSS protection
        meta = {
            'title': escape(title),
            'description': escape(description),
            'keywords': escape(keywords) if keywords else '',
            'image': escape(image),
            'url': canonical_url,
            'site_name': escape(deployed_site.site_name),
            'og_type': 'website',  # 'product' for product pages in future
            'twitter_card': 'summary_large_image'
        }

        logger.debug(f"Generated SEO meta tags for site {deployed_site.id}: {meta['title']}")
        return meta

    @staticmethod
    def generate_structured_data(deployed_site) -> Dict:
        """
        Generate JSON-LD structured data for Google Rich Results

        Args:
            deployed_site: DeployedSite instance

        Returns:
            dict: JSON-LD schema.org markup

        Note: Returns Organization schema for homepage
        Future: Add Product, BreadcrumbList schemas for other pages
        """
        # Fix: DeployedSite has a reverse relationship to CustomDomain (one-to-many)
        primary_domain = deployed_site.custom_domains.filter(
            is_primary=True,
            status='verified'
        ).first()

        if primary_domain:
            url = f"https://{primary_domain.domain}"
        else:
            url = f"https://{deployed_site.subdomain}.huzilerz.com"

        structured_data = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": deployed_site.site_name,
            "url": url,
            "logo": deployed_site.seo_image_url or SEOService.DEFAULT_IMAGE_URL,
            "description": deployed_site.seo_description or SEOService.DEFAULT_DESCRIPTION_TEMPLATE.format(
                site_name=deployed_site.site_name
            )
        }

        # Add contact point if user has business info (future enhancement)
        # structured_data["contactPoint"] = {
        #     "@type": "ContactPoint",
        #     "contactType": "customer service",
        #     "email": deployed_site.workspace.business_email
        # }

        return structured_data

    @staticmethod
    def is_bot_request(user_agent: str) -> bool:
        """
        Detect if request is from a search engine bot or social media crawler

        Args:
            user_agent: HTTP User-Agent header string

        Returns:
            bool: True if bot detected, False for regular users

        Note: Google approves dynamic rendering (serving different HTML to bots)
        Reference: https://developers.google.com/search/docs/advanced/javascript/dynamic-rendering
        """
        if not user_agent:
            return False

        # List of bot signatures (lowercase for case-insensitive matching)
        BOT_SIGNATURES = [
            'googlebot',          # Google Search
            'bingbot',            # Bing Search
            'slurp',              # Yahoo Search
            'duckduckbot',        # DuckDuckGo
            'baiduspider',        # Baidu (China)
            'yandexbot',          # Yandex (Russia)
            'facebookexternalhit',  # Facebook/WhatsApp preview
            'twitterbot',         # Twitter cards
            'linkedinbot',        # LinkedIn preview
            'pinterest',          # Pinterest
            'whatsapp',           # WhatsApp link preview
            'telegrambot',        # Telegram preview
            'slackbot',           # Slack unfurling
            'discordbot',         # Discord embeds
            'googlebot-image',    # Google Images
            'googlebot-video',    # Google Videos
            'lighthouse',         # Lighthouse SEO audit
            'gtmetrix',           # Performance testing
            'pagespeed',          # PageSpeed Insights
        ]

        user_agent_lower = user_agent.lower()
        is_bot = any(bot in user_agent_lower for bot in BOT_SIGNATURES)

        if is_bot:
            logger.info(f"Bot detected: {user_agent[:100]}")

        return is_bot

    @staticmethod
    def validate_seo_fields(title: str = None, description: str = None, keywords: str = None) -> Dict:
        """
        Validate SEO field values and return errors/warnings

        Args:
            title: SEO title (max 60 chars recommended)
            description: Meta description (max 160 chars recommended)
            keywords: Comma-separated keywords (optional)

        Returns:
            dict: {
                'valid': bool,
                'errors': list,
                'warnings': list
            }
        """
        errors = []
        warnings = []

        # Title validation
        if title is not None:
            if len(title) > 60:
                warnings.append(f"Title is {len(title)} characters. Google truncates at ~60 characters.")
            if len(title) > 70:
                errors.append("Title exceeds 70 characters (hard limit)")
            if len(title) < 10:
                warnings.append("Title is very short. Consider adding more context.")

        # Description validation
        if description is not None:
            if len(description) > 160:
                warnings.append(f"Description is {len(description)} characters. Google truncates at ~160 characters.")
            if len(description) > 200:
                errors.append("Description exceeds 200 characters (hard limit)")
            if len(description) < 50:
                warnings.append("Description is short. Consider adding more detail.")

        # Keywords validation (less important for modern SEO)
        if keywords is not None and len(keywords) > 255:
            errors.append("Keywords exceed 255 characters")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    @staticmethod
    def get_theme_cdn_url(deployed_site) -> str:
        """
        Get CDN URL for theme bundle based on site configuration

        Args:
            deployed_site: DeployedSite instance

        Returns:
            str: CDN URL for theme JavaScript bundle

        Note: Uses version hash for cache busting
        """
        if not deployed_site.customization:
            # No theme published yet - return default
            logger.warning(f"Site {deployed_site.id} has no customization, returning default theme URL")
            return "https://cdn.huzilerz.com/themes/default/bundle.js"

        # Get version hash from customization
        from workspace.hosting.services.cdn_cache_service import CDNCacheService
        version_hash = CDNCacheService.get_theme_version_hash(deployed_site.customization)

        # Build versioned CDN URL
        template_id = deployed_site.template.id if deployed_site.template else 'default'
        cdn_url = f"https://cdn.huzilerz.com/themes/{template_id}/{version_hash}/bundle.js"

        return cdn_url
