"""
GraphQL queries for store settings (public storefront)
Follows codebase patterns from checkout_queries.py

Provides public store information for storefront themes:
- Store name and branding
- Contact information (WhatsApp, phone, email)
- Currency settings
"""

import graphene
import logging

from workspace.store.models import StoreProfile
from workspace.storefront.graphql.types.store_settings_types import StoreSettingsType

logger = logging.getLogger(__name__)


class StoreSettingsQueries(graphene.ObjectType):
    """
    Store settings queries for storefront

    Domain-based workspace identification via middleware
    Returns public store settings for theme use
    """

    store_settings = graphene.Field(
        StoreSettingsType,
        description="Get public store settings (name, WhatsApp, currency, etc.)"
    )

    def resolve_store_settings(self, info):
        """
        Get public store settings for current workspace

        Performance: Single query, highly cacheable
        Security: Workspace scoping via middleware, public fields only
        Reliability: Returns None on error, logs warning
        """
        try:
            workspace = info.context.workspace

            if not workspace:
                logger.warning("No workspace in context for store_settings query")
                return None

            # Get store profile
            try:
                profile = StoreProfile.objects.get(workspace=workspace)
            except StoreProfile.DoesNotExist:
                logger.warning(f"Store profile not found for workspace {workspace.id}")
                return None

            # Return public settings only
            return StoreSettingsType(
                store_name=profile.store_name,
                store_description=profile.store_description,
                whatsapp_number=profile.whatsapp_number,
                phone_number=profile.phone_number,
                support_email=profile.support_email,
                currency=profile.currency
            )

        except Exception as e:
            logger.error(
                f"Failed to get store settings: {str(e)}",
                exc_info=True
            )
            return None
