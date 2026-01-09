"""
Domain Mapping Service
Maps customer domains/subdomains to workspace slugs for storefront identification

NOTE: Most domain routing logic now handled by StoreIdentificationMiddleware.
This service remains for backward compatibility and utility functions.
"""
import logging
from django.conf import settings
from workspace.core.models import Workspace
from workspace.hosting.models import DeployedSite, CustomDomain

logger = logging.getLogger(__name__)

class DomainMappingService:
    """
    Maps domains/subdomains to workspace slugs for storefront identification

    Patterns:
    - Subdomain: user-123-johns-electronics.huzilerz.com → johns-electronics
    - Custom Domain: mikeshoes.cm → mikeshoes
    """

    @staticmethod
    def get_workspace_from_domain(domain: str) -> Workspace:
        """
        Get workspace from domain/subdomain

        Args:
            domain: Full domain (e.g., "user-123-johns-electronics.huzilerz.com")

        Returns:
            Workspace object

        Raises:
            Workspace.DoesNotExist: If no workspace found
        """
        try:
            # Check if it's a custom domain
            if not domain.endswith('.huzilerz.com'):
                return DomainMappingService._get_workspace_from_custom_domain(domain)

            # It's our subdomain - extract workspace slug
            workspace_slug = DomainMappingService._extract_workspace_slug_from_subdomain(domain)

            # Get workspace
            workspace = Workspace.objects.get(
                slug=workspace_slug,
                type='store',
                status='active'
            )

            logger.info(f"Mapped domain {domain} to workspace {workspace_slug}")
            return workspace

        except Workspace.DoesNotExist:
            logger.error(f"No workspace found for domain: {domain}")
            raise

    @staticmethod
    def _get_workspace_from_custom_domain(domain: str) -> Workspace:
        """
        Get workspace from custom domain using CustomDomain model

        Args:
            domain: Custom domain (e.g., "mikeshoes.cm")

        Returns:
            Workspace object
        """
        try:
            # Find custom domain record (new model)
            custom_domain = CustomDomain.objects.select_related(
                'workspace',
                'deployed_site'
            ).get(
                domain=domain,
                status='active'
            )

            workspace = custom_domain.workspace
            logger.info(f"Mapped custom domain {domain} to workspace {workspace.slug}")
            return workspace

        except CustomDomain.DoesNotExist:
            logger.error(f"No custom domain found: {domain}")
            raise Workspace.DoesNotExist(f"No workspace found for domain: {domain}")

    @staticmethod
    def _extract_workspace_slug_from_subdomain(subdomain: str) -> str:
        """
        Extract workspace slug from subdomain

        NEW Pattern: {workspace_slug}.huzilerz.com or {workspace_slug}-{random}.huzilerz.com
        Legacy Pattern: user-{user_id}-{workspace_slug}.huzilerz.com (still supported)

        Args:
            subdomain: Full subdomain (e.g., "johns-electronics.huzilerz.com")

        Returns:
            Workspace slug (e.g., "johns-electronics")
        """
        # Remove domain suffix
        subdomain_part = subdomain.replace('.huzilerz.com', '')

        # New pattern: Just use subdomain directly (or lookup from DeployedSite)
        # The middleware handles the actual lookup with custom_subdomain support
        # This service is now mostly for backward compatibility

        # Try to find DeployedSite to get correct workspace slug
        try:
            from django.db.models import Q
            deployed_site = DeployedSite.objects.filter(
                Q(subdomain=subdomain_part) | Q(custom_subdomain=subdomain_part),
                status='active'
            ).select_related('workspace').first()

            if deployed_site:
                return deployed_site.workspace.slug
        except Exception as e:
            logger.warning(f"Could not find DeployedSite for subdomain {subdomain_part}: {e}")

        # Fallback: use subdomain as-is (for legacy patterns)
        return subdomain_part

    @staticmethod
    def get_store_slug_from_domain(domain: str) -> str:
        """
        Get store slug from domain (for GraphQL queries)

        Args:
            domain: Full domain

        Returns:
            Store slug string
        """
        try:
            workspace = DomainMappingService.get_workspace_from_domain(domain)
            return workspace.slug
        except Workspace.DoesNotExist:
            # Fallback: try to extract from domain directly
            if domain.endswith('.huzilerz.com'):
                return DomainMappingService._extract_workspace_slug_from_subdomain(domain)
            else:
                # For custom domains, remove TLD
                return domain.split('.')[0]

    @staticmethod
    def validate_domain_access(domain: str, workspace_slug: str) -> bool:
        """
        Validate that domain has access to workspace

        Security check to prevent domain spoofing

        Args:
            domain: Request domain
            workspace_slug: Requested workspace slug

        Returns:
            True if access allowed, False otherwise
        """
        try:
            # Get workspace from domain
            workspace_from_domain = DomainMappingService.get_workspace_from_domain(domain)

            # Get workspace from slug
            workspace_from_slug = Workspace.objects.get(
                slug=workspace_slug,
                type='store',
                status='active'
            )

            # Check if they match
            return workspace_from_domain.id == workspace_from_slug.id

        except (Workspace.DoesNotExist, DeployedSite.DoesNotExist):
            return False

    @staticmethod
    def get_all_domains_for_workspace(workspace_slug: str) -> list:
        """
        Get all domains (subdomains + custom domains) for a workspace

        Args:
            workspace_slug: Workspace slug

        Returns:
            List of domain strings with metadata
        """
        try:
            workspace = Workspace.objects.get(slug=workspace_slug)
            domains = []

            # Get deployed sites with subdomains
            deployed_sites = DeployedSite.objects.filter(
                workspace=workspace,
                status='active'
            ).prefetch_related('custom_domains')

            for site in deployed_sites:
                # Add primary subdomain (auto-generated or custom)
                active_subdomain = site.active_subdomain
                if active_subdomain:
                    domains.append({
                        'domain': f"{active_subdomain}.huzilerz.com",
                        'type': 'subdomain',
                        'is_primary': not site.has_custom_domain,
                        'is_custom_subdomain': bool(site.custom_subdomain)
                    })

                # Add all custom domains from CustomDomain model
                custom_domains = site.custom_domains.filter(status='active')
                for custom_domain in custom_domains:
                    domains.append({
                        'domain': custom_domain.domain,
                        'type': 'custom_domain',
                        'is_primary': custom_domain.is_primary,
                        'verified': custom_domain.status == 'active',
                        'ssl_enabled': custom_domain.ssl_enabled
                    })

            return domains

        except Workspace.DoesNotExist:
            logger.error(f"Workspace not found: {workspace_slug}")
            return []