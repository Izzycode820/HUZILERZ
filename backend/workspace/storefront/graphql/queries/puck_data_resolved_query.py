"""
Puck Data Resolved Query - PUBLIC, NO AUTHENTICATION REQUIRED

Fetches merchant's customized puck.data.json and resolves all section data requirements.
This is the SINGLE QUERY that powers storefront rendering.

Uses X-Store-Hostname header for tenant identification (same as product queries).

Architecture:
  1. Load puck.data from active theme customization
  2. Loop through sections
  3. SectionResolverService resolves data for each section
  4. Inject resolvedData into each section
  5. Return enriched puck.data

Security: Public endpoint, hostname-based workspace isolation
Performance: Efficient queries via SectionResolverService
"""

import graphene
import logging
from typing import Dict, Any

from workspace.storefront.services.section_resolver_service import SectionResolverService

logger = logging.getLogger(__name__)


class PuckDataResolvedResponse(graphene.ObjectType):
    """Response type for resolved puck data query"""
    success = graphene.Boolean()
    message = graphene.String()
    data = graphene.JSONString()


class PuckDataResolvedQuery(graphene.ObjectType):
    """
    Public query to fetch puck data with resolved section data for storefront rendering

    This is the PRIMARY query for all storefront page rendering.
    Returns puck.data structure with injected resolvedData for each section.
    """

    public_puck_data_resolved = graphene.Field(
        PuckDataResolvedResponse,
        description=(
            "Fetch active theme's puck data with resolved section data for storefront "
            "(uses X-Store-Hostname header for workspace identification)"
        )
    )

    def resolve_public_puck_data_resolved(self, info):
        """
        Fetch puck data and resolve all section data requirements

        Flow:
        1. Extract hostname from X-Store-Hostname header
        2. Look up DeployedSite by subdomain
        3. Get active theme customization (is_active=True)
        4. Load puck_data JSON
        5. For each section in puck_data.content:
           - Extract data contract
           - Call SectionResolverService
           - Inject resolvedData into section
        6. Return enriched puck_data

        No JWT required - public storefront data
        Workspace isolation via hostname

        Returns:
            PuckDataResolvedResponse with enriched puck.data
        """
        try:
            request = info.context
            hostname = request.META.get('HTTP_X_STORE_HOSTNAME', '')

            if not hostname:
                logger.warning(
                    "Missing X-Store-Hostname header in puck data resolved request",
                    extra={'endpoint': 'public_puck_data_resolved'}
                )
                return PuckDataResolvedResponse(
                    success=False,
                    message="Missing X-Store-Hostname header",
                    data=None
                )

            # Extract subdomain from hostname
            # Production: johns-shop.huzilerz.com -> johns-shop
            # Dev: johns-shop -> johns-shop
            if '.huzilerz.com' in hostname:
                subdomain = hostname.replace('.huzilerz.com', '')
            else:
                # Dev mode: hostname is the subdomain directly
                subdomain = hostname

            logger.info(
                "Fetching resolved puck data",
                extra={
                    'subdomain': subdomain,
                    'endpoint': 'public_puck_data_resolved'
                }
            )

            # Import models here to avoid circular imports
            from workspace.hosting.models import DeployedSite
            from theme.models import TemplateCustomization

            try:
                # Look up DeployedSite by subdomain
                deployed_site = DeployedSite.objects.select_related(
                    'workspace',
                    'customization',
                    'template'
                ).get(
                    subdomain=subdomain,
                    status='active'
                )

                workspace = deployed_site.workspace

                # Get active customization for this workspace
                active_customization = TemplateCustomization.objects.filter(
                    workspace=workspace,
                    is_active=True
                ).first()

                if not active_customization:
                    logger.warning(
                        "No active theme found",
                        extra={
                            'subdomain': subdomain,
                            'workspace_id': workspace.id
                        }
                    )
                    return PuckDataResolvedResponse(
                        success=False,
                        message="No active theme published for this workspace",
                        data=None
                    )

                # Get puck data
                puck_data = active_customization.puck_data or {}

                if not puck_data:
                    logger.warning(
                        "Empty puck data",
                        extra={
                            'subdomain': subdomain,
                            'workspace_id': workspace.id,
                            'theme_name': active_customization.theme_name
                        }
                    )
                    return PuckDataResolvedResponse(
                        success=True,
                        message="Theme has no puck data configured",
                        data={}
                    )

                # Initialize section resolver service for this workspace
                resolver_service = SectionResolverService(workspace)

                # Resolve data for each section
                sections = puck_data.get('content', [])
                resolved_count = 0
                error_count = 0

                for section in sections:
                    section_type = section.get('type')
                    section_props = section.get('props', {})

                    # Check if section has a data contract
                    # 1. Check root level (legacy support)
                    # 2. Check props level (new architecture, favored by Puck editor)
                    data_contract = section.get('dataContract') or section_props.get('dataContract')

                    if not data_contract:
                        # Section has no data requirements (e.g., static banners)
                        logger.debug(
                            "Section has no data contract, skipping resolution",
                            extra={
                                'workspace_id': workspace.id,
                                'section_type': section_type
                            }
                        )
                        continue

                    try:
                        # Resolve section data via SectionResolverService
                        resolved_data = resolver_service.resolve_section(
                            section_type=section_type,
                            section_props=section_props,
                            data_contract=data_contract
                        )

                        # Inject resolved data into section props
                        # Puck's render function receives props only, so we merge resolved data into props
                        # This allows components to receive both intent (categorySlug, limit) and data (products)
                        for key, value in resolved_data.items():
                            section['props'][key] = value

                        resolved_count += 1

                        logger.debug(
                            "Section data resolved successfully",
                            extra={
                                'workspace_id': workspace.id,
                                'section_type': section_type,
                                'resolver': data_contract.get('resolver')
                            }
                        )

                    except Exception as e:
                        # Graceful degradation - log error but don't crash
                        error_count += 1
                        # Inject empty data into props to prevent component crashes
                        # Component will handle empty arrays gracefully
                        section['props']['products'] = []

                        logger.error(
                            "Error resolving section data",
                            extra={
                                'workspace_id': workspace.id,
                                'section_type': section_type,
                                'error': str(e)
                            },
                            exc_info=True
                        )

                logger.info(
                    "Successfully resolved puck data",
                    extra={
                        'subdomain': subdomain,
                        'workspace_id': workspace.id,
                        'theme_name': active_customization.theme_name,
                        'total_sections': len(sections),
                        'resolved_sections': resolved_count,
                        'errors': error_count
                    }
                )

                return PuckDataResolvedResponse(
                    success=True,
                    message="Puck data with resolved sections retrieved successfully",
                    data=puck_data
                )

            except DeployedSite.DoesNotExist:
                logger.warning(
                    "No active site found for subdomain",
                    extra={'subdomain': subdomain}
                )
                return PuckDataResolvedResponse(
                    success=False,
                    message=f"No active site found for subdomain: {subdomain}",
                    data=None
                )

        except Exception as e:
            logger.error(
                "Unexpected error in public_puck_data_resolved",
                extra={'error': str(e)},
                exc_info=True
            )
            return PuckDataResolvedResponse(
                success=False,
                message=f"Error fetching resolved puck data: {str(e)}",
                data=None
            )
