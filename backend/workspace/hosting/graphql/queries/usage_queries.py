"""
Resource Usage GraphQL Queries - AUTHENTICATED + USER SCOPED

Query hosting resource usage, quotas, and billing
Requires authentication and scoped to user's hosting environment
"""

import graphene
from graphql import GraphQLError
from ..types.usage_types import (
    HostingEnvironmentType,
    UsageSummaryType,
    UsageHistoryType,
    OverageCostType,
    ResourceUsageLogType
)
from workspace.hosting.models import HostingEnvironment, ResourceUsageLog


class UsageQueries(graphene.ObjectType):
    """
    Resource usage queries

    Security: All queries automatically scoped to authenticated user
    Pattern: Follows domain queries pattern with user-level scoping
    """

    my_hosting_environment = graphene.Field(
        HostingEnvironmentType,
        description="Get current user's hosting environment and resource quotas"
    )

    my_usage_summary = graphene.Field(
        UsageSummaryType,
        description="Get current usage summary with percentages (for dashboard)"
    )

    my_usage_history = graphene.Field(
        UsageHistoryType,
        days=graphene.Int(default_value=30),
        description="Get usage history for analytics charts (default 30 days)"
    )

    my_overage_cost = graphene.Field(
        OverageCostType,
        description="Calculate current overage costs for billing"
    )

    my_usage_logs = graphene.List(
        ResourceUsageLogType,
        days=graphene.Int(default_value=7),
        description="Get detailed usage logs (for debugging/support)"
    )

    check_upload_eligibility = graphene.Field(
        graphene.JSONString,
        file_size_bytes=graphene.Int(required=True),
        description="Check if user can upload file based on storage limits"
    )

    check_deployment_eligibility = graphene.Field(
        graphene.JSONString,
        description="Check if user can deploy new site based on limits"
    )

    def resolve_my_hosting_environment(self, info):
        """
        Resolve current user's hosting environment

        Security: Automatically scoped to authenticated user
        Use case: Display resource quotas and limits in settings
        """
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        try:
            hosting_env = HostingEnvironment.objects.select_related(
                'subscription',
                'subscription__plan'
            ).get(user=user)

            return hosting_env

        except HostingEnvironment.DoesNotExist:
            raise GraphQLError("Hosting environment not found. Please contact support.")

    def resolve_my_usage_summary(self, info):
        """
        Resolve current usage summary

        Security: Automatically scoped to authenticated user
        Use case: Dashboard widget showing usage with progress bars
        """
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        try:
            hosting_env = HostingEnvironment.objects.get(user=user)
            summary = hosting_env.get_usage_summary()

            from ..types.usage_types import (
                StorageUsageType,
                BandwidthUsageType,
                SitesUsageType,
                CustomDomainsUsageType
            )

            return UsageSummaryType(
                storage=StorageUsageType(**summary['storage']),
                bandwidth=BandwidthUsageType(**summary['bandwidth']),
                sites=SitesUsageType(**summary['sites']),
                custom_domains=CustomDomainsUsageType(**summary['custom_domains']),
                status=summary['status'],
                deployment_allowed=summary['deployment_allowed']
            )

        except HostingEnvironment.DoesNotExist:
            raise GraphQLError("Hosting environment not found")

    def resolve_my_usage_history(self, info, days=30):
        """
        Resolve usage history with time series data

        Security: Automatically scoped to authenticated user
        Use case: Usage charts in analytics dashboard (Chart.js / Recharts)
        """
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        try:
            hosting_env = HostingEnvironment.objects.get(user=user)
            return hosting_env.get_usage_history(days=days)

        except HostingEnvironment.DoesNotExist:
            raise GraphQLError("Hosting environment not found")

    def resolve_my_overage_cost(self, info):
        """
        Resolve current overage costs

        Security: Automatically scoped to authenticated user
        Use case: Show overage charges in billing page
        """
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        try:
            hosting_env = HostingEnvironment.objects.get(user=user)
            overage = hosting_env.calculate_overage_cost()

            return OverageCostType(**overage)

        except HostingEnvironment.DoesNotExist:
            raise GraphQLError("Hosting environment not found")

    def resolve_my_usage_logs(self, info, days=7):
        """
        Resolve detailed usage logs

        Security: Automatically scoped to authenticated user
        Use case: Debugging, support tickets, detailed analytics
        """
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        try:
            from django.utils import timezone

            hosting_env = HostingEnvironment.objects.get(user=user)
            start_date = timezone.now() - timezone.timedelta(days=days)

            logs = ResourceUsageLog.objects.filter(
                hosting_environment=hosting_env,
                recorded_at__gte=start_date
            ).select_related(
                'workspace',
                'site'
            ).order_by('-recorded_at')[:100]  # Limit to 100 most recent

            return logs

        except HostingEnvironment.DoesNotExist:
            raise GraphQLError("Hosting environment not found")

    def resolve_check_upload_eligibility(self, info, file_size_bytes):
        """
        Check if user can upload file

        Security: Automatically scoped to authenticated user
        Use case: Pre-flight check before file upload (show warning if near limit)
        """
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        try:
            from workspace.hosting.services.resource_usage_service import ResourceUsageService

            service = ResourceUsageService()
            result = service.check_upload_eligibility(user, file_size_bytes)

            return result

        except Exception as e:
            raise GraphQLError(f"Failed to check upload eligibility: {str(e)}")

    def resolve_check_deployment_eligibility(self, info):
        """
        Check if user can deploy new site

        Security: Automatically scoped to authenticated user
        Use case: Show upgrade prompt before deployment if limit reached
        """
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentication required")

        try:
            from workspace.hosting.services.resource_usage_service import ResourceUsageService

            service = ResourceUsageService()
            result = service.check_deployment_eligibility(user, {})

            return result

        except Exception as e:
            raise GraphQLError(f"Failed to check deployment eligibility: {str(e)}")
