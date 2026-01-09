"""
Analytics Query Resolvers

GraphQL queries for workspace analytics.
Follows workspace auto-scoping pattern from store module.

Security: All queries automatically scoped to authenticated workspace via JWT middleware
Performance: Uses StoreMetricsService with caching
"""

import graphene
from graphene import ObjectType, Field, Int
from graphql import GraphQLError
from workspace.core.services import PermissionService
from ..types import StoreAnalytics
from ...services import StoreMetricsService
import logging

logger = logging.getLogger(__name__)


class AnalyticsQuery(ObjectType):
    """
    Analytics queries with workspace auto-scoping.
    
    Security: All queries automatically scoped to authenticated workspace
    Pattern: Follows store module query pattern (workspace from context, not args)
    """
    
    store_analytics = Field(
        StoreAnalytics,
        days=Int(default_value=30, description="Number of days for metrics (1-365)"),
        description="Get store analytics dashboard data (tier-gated)"
    )
    
    def resolve_store_analytics(self, info, days=30):
        """
        Resolve store analytics with workspace auto-scoping.
        
        Pattern: Uses workspace from info.context (set by JWT middleware)
        No workspace_id parameter needed - auto-scoped like all store queries
        
        Args:
            info: GraphQL resolve info (contains workspace from context)
            days: Number of days for metrics
            
        Returns:
            StoreAnalytics with tier-appropriate data
            
        Raises:
            GraphQLError: Permission denied or error fetching analytics
        """
        workspace = info.context.workspace
        user = info.context.user
        
        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'analytics:view'):
            raise GraphQLError("Insufficient permissions to view analytics")
        
        # Get analytics data via service
        try:
            service = StoreMetricsService(workspace)
            dashboard_data = service.get_dashboard_data(days)
            
            logger.info(
                f"Generated analytics for workspace {workspace.id} "
                f"(level: {dashboard_data.get('analytics_level')}, days: {days})"
            )
            
            return dashboard_data
            
        except Exception as e:
            logger.error(
                f"Error generating analytics for workspace {workspace.id}: {str(e)}",
                exc_info=True
            )
            raise GraphQLError(f"Failed to fetch analytics: {str(e)}")
