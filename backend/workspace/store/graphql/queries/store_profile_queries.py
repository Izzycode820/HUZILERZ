"""
Store Profile GraphQL Queries

Query for retrieving store profile settings.
Workspace-scoped via JWT middleware.
"""

import graphene
import logging
from ..types.store_profile_types import StoreProfileType
from workspace.store.services.store_profile_service import store_profile_service

logger = logging.getLogger(__name__)


class StoreProfileQueries(graphene.ObjectType):
    """
    Store Profile queries for admin dashboard.
    All queries are automatically workspace-scoped via JWT middleware.
    """
    
    store_profile = graphene.Field(
        StoreProfileType,
        description="Get store profile settings for current workspace"
    )
    
    def resolve_store_profile(self, info):
        """
        Resolve store profile for current workspace.
        
        Returns:
            StoreProfile or None if not found
        """
        workspace = info.context.workspace
        
        if not workspace:
            logger.warning("No workspace in context for store_profile query")
            return None
        
        result = store_profile_service.get_store_profile(workspace)
        
        if result['success']:
            return result['profile']
        else:
            logger.warning(f"Store profile not found: {result.get('error')}")
            return None
