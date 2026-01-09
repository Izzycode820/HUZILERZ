"""
Public Puck Data Query - NO AUTHENTICATION REQUIRED

Storefront themes use this to fetch user's customized puck.data.json
Uses X-Store-Hostname header for tenant identification (same as products)
"""

import graphene
import logging

logger = logging.getLogger(__name__)


class PuckDataResponse(graphene.ObjectType):
    """Response type for public puck data query"""
    success = graphene.Boolean()
    message = graphene.String()
    data = graphene.JSONString()


class PublicPuckDataQuery(graphene.ObjectType):
    """Public query to fetch puck data for storefront rendering"""

    public_puck_data = graphene.Field(
        PuckDataResponse,
        description="Fetch active theme's puck data for storefront (uses X-Store-Hostname header)"
    )

    def resolve_public_puck_data(self, info):
        """
        Fetch puck data for the active theme of the workspace identified by hostname

        Flow:
        1. Extract hostname from X-Store-Hostname header
        2. Look up DeployedSite by subdomain
        3. Get active customization (is_active=True)
        4. Return puck_data JSON

        No JWT required - public storefront data
        """
        try:
            request = info.context
            hostname = request.META.get('HTTP_X_STORE_HOSTNAME', '')

            if not hostname:
                logger.warning("Missing X-Store-Hostname header in puck data request")
                return PuckDataResponse(
                    success=False,
                    message="Missing X-Store-Hostname header",
                    data=None
                )

            # Extract subdomain from hostname
            # Production: johns-shop.huzilerz.com → johns-shop
            # Dev: johns-shop → johns-shop
            if '.huzilerz.com' in hostname:
                subdomain = hostname.replace('.huzilerz.com', '')
            else:
                # Dev mode: hostname is the subdomain directly
                subdomain = hostname

            logger.info(f"[PublicPuckData] Fetching puck data for subdomain: {subdomain}")

            # Look up DeployedSite by subdomain
            from workspace.hosting.models import DeployedSite
            from theme.models import TemplateCustomization

            try:
                deployed_site = DeployedSite.objects.select_related(
                    'workspace',
                    'customization',
                    'template'
                ).get(
                    subdomain=subdomain,
                    status='active'  # Only active sites
                )

                # Get active customization for this workspace
                active_customization = TemplateCustomization.objects.filter(
                    workspace=deployed_site.workspace,
                    is_active=True  # Only published theme
                ).first()

                if not active_customization:
                    logger.warning(f"No active theme found for subdomain: {subdomain}")
                    return PuckDataResponse(
                        success=False,
                        message=f"No active theme published for this workspace",
                        data=None
                    )

                # Return puck data
                puck_data = active_customization.puck_data or {}

                logger.info(f"✅ [PublicPuckData] Successfully fetched puck data for '{subdomain}' (theme: {active_customization.theme_name})")

                return PuckDataResponse(
                    success=True,
                    message=f"Puck data retrieved successfully",
                    data=puck_data
                )

            except DeployedSite.DoesNotExist:
                logger.warning(f"No active site found for subdomain: {subdomain}")
                return PuckDataResponse(
                    success=False,
                    message=f"No active site found for subdomain: {subdomain}",
                    data=None
                )

        except Exception as e:
            logger.error(f"Error fetching public puck data: {str(e)}", exc_info=True)
            return PuckDataResponse(
                success=False,
                message=f"Error fetching puck data: {str(e)}",
                data=None
            )
