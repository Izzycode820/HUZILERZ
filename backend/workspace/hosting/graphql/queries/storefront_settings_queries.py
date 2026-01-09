"""
Storefront Settings GraphQL Queries - AUTHENTICATED + WORKSPACE SCOPED

Provides unified settings data for UI forms:
- Password protection (enabled, plaintext password)
- SEO fields (title, description, keywords, image)
- Domain info (subdomain, custom domain, preview URL)

Single source of truth for storefront configuration UI
"""

import graphene
from graphql import GraphQLError
from ..types.storefront_settings_types import StorefrontSettingsType
from workspace.hosting.models import DeployedSite, WorkspaceInfrastructure, CustomDomain
import logging

logger = logging.getLogger(__name__)


class StorefrontSettingsQueries(graphene.ObjectType):
    """
    Storefront settings queries for UI forms

    Provides all settings needed by:
    - SEO Settings page
    - Password Protection page
    - Puck Editor (initial root.props values)
    """

    storefront_settings = graphene.Field(
        StorefrontSettingsType,
        workspace_id=graphene.ID(required=True),
        description="Get storefront settings (password, SEO, domain info)"
    )

    def resolve_storefront_settings(self, info, workspace_id):
        """
        Get storefront settings for UI

        Returns:
        - password: Plaintext password (if enabled)
        - password_enabled: Whether protection is on
        - seo_title/description/keywords/image_url: SEO metadata
        - assigned_domain: Current active domain
        - preview_url: Full URL to preview site
        - site_name: Store name

        Security: Workspace ownership validated
        Error Handling: Graceful defaults if data missing
        """
        workspace = info.context.workspace

        if str(workspace.id) != workspace_id:
            raise GraphQLError("Unauthorized")

        try:
            # Get deployed site with all SEO fields
            deployed_site = DeployedSite.objects.select_related('workspace').get(
                workspace=workspace
            )
        except DeployedSite.DoesNotExist:
            raise GraphQLError("Storefront not deployed yet")

        # Get active domain (custom domain or subdomain)
        assigned_domain = None

        # Check for primary custom domain
        primary_custom = CustomDomain.objects.filter(
            workspace=workspace,
            status='active',
            is_primary=True
        ).first()

        if primary_custom:
            assigned_domain = primary_custom.domain
        else:
            # Use subdomain from infrastructure
            try:
                infrastructure = WorkspaceInfrastructure.objects.get(workspace=workspace)
                subdomain = infrastructure.subdomain
                if not subdomain.endswith('.huzilerz.com'):
                    subdomain = f"{subdomain}.huzilerz.com"
                assigned_domain = subdomain
            except WorkspaceInfrastructure.DoesNotExist:
                assigned_domain = f"{workspace.slug}.huzilerz.com"

        # Build preview URL
        preview_url = f"https://{assigned_domain}"

        # Get SEO title (default to site_name or domain if empty)
        seo_title = deployed_site.seo_title or deployed_site.site_name or assigned_domain

        return StorefrontSettingsType(
            # Password protection
            password=deployed_site.password_plaintext or None,
            password_enabled=deployed_site.password_protection_enabled,
            password_description=deployed_site.password_description or '',

            # SEO fields
            seo_title=seo_title,
            seo_description=deployed_site.seo_description or '',
            seo_keywords=deployed_site.seo_keywords or '',
            seo_image_url=deployed_site.seo_image_url or '',

            # Domain info
            assigned_domain=assigned_domain,
            preview_url=preview_url,
            site_name=deployed_site.site_name or workspace.name,
        )
