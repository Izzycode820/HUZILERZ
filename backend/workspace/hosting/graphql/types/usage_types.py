"""
Resource Usage GraphQL Types - For Queries

Provides types for hosting resource usage and quota tracking
Requires authentication and scoped to user's hosting environment
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.hosting.models import HostingEnvironment, ResourceUsageLog
from .common_types import BaseConnection


class StorageUsageType(graphene.ObjectType):
    """Storage usage details"""
    used_gb = graphene.Float(required=True)
    limit_gb = graphene.Float(required=True)
    percentage = graphene.Float(required=True)
    remaining_gb = graphene.Float(required=True)


class BandwidthUsageType(graphene.ObjectType):
    """Bandwidth usage details"""
    used_gb = graphene.Float(required=True)
    limit_gb = graphene.Float(required=True)
    percentage = graphene.Float(required=True)
    remaining_gb = graphene.Float(required=True)


class SitesUsageType(graphene.ObjectType):
    """Sites usage details"""
    active_count = graphene.Int(required=True)
    limit = graphene.Int(required=True)
    percentage = graphene.Float(required=True)
    remaining = graphene.Int(required=True)


class CustomDomainsUsageType(graphene.ObjectType):
    """Custom domains usage details"""
    count = graphene.Int(required=True)
    limit = graphene.Int(required=True)


class UsageSummaryType(graphene.ObjectType):
    """Complete usage summary with all resources"""
    storage = graphene.Field(StorageUsageType, required=True)
    bandwidth = graphene.Field(BandwidthUsageType, required=True)
    sites = graphene.Field(SitesUsageType, required=True)
    custom_domains = graphene.Field(CustomDomainsUsageType, required=True)
    status = graphene.String(required=True)
    deployment_allowed = graphene.Boolean(required=True)


class UsageDataPointType(graphene.ObjectType):
    """Single data point in usage history"""
    recorded_at = graphene.DateTime(required=True)
    storage_used_gb = graphene.Float(required=True)
    bandwidth_used_gb = graphene.Float(required=True)
    requests_count = graphene.Int()
    avg_response_time_ms = graphene.Int()


class UsageHistoryType(graphene.ObjectType):
    """Usage history with time series data"""
    period_days = graphene.Int(required=True)
    data_points = graphene.List(UsageDataPointType, required=True)
    current_usage = graphene.Field(UsageSummaryType, required=True)


class OverageCostType(graphene.ObjectType):
    """Overage cost calculation for billing"""
    total_overage_usd = graphene.Float(required=True)
    storage_overage_gb = graphene.Float(required=True)
    bandwidth_overage_gb = graphene.Float(required=True)


class HostingEnvironmentType(DjangoObjectType):
    """
    Hosting environment resource quota tracker

    Workspace-scoped - only accessible to user who owns the hosting environment
    Tracks resource limits and current usage per subscription tier
    """

    id = graphene.ID(required=True)

    # Computed fields
    storage_usage_percentage = graphene.Float()
    bandwidth_usage_percentage = graphene.Float()
    is_deployment_allowed = graphene.Boolean()

    # Complex computed fields
    usage_summary = graphene.Field(UsageSummaryType)
    usage_history = graphene.Field(
        UsageHistoryType,
        days=graphene.Int(default_value=30)
    )
    overage_cost = graphene.Field(OverageCostType)

    class Meta:
        model = HostingEnvironment
        fields = (
            'id',

            # Core identity
            'user',
            'subscription',

            # Status
            'status',
            'grace_period_end',

            # Hosting capabilities (from YAML via CapabilityEngine)
            'capabilities',

            # Current usage
            'storage_used_gb',
            'bandwidth_used_gb',
            'active_sites_count',

            # Timestamps
            'created_at',
            'updated_at',
            'last_usage_sync',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        """Return plain UUID"""
        return str(self.id)

    def resolve_storage_usage_percentage(self, info):
        """Calculate storage usage percentage"""
        return float(self.storage_usage_percentage)

    def resolve_bandwidth_usage_percentage(self, info):
        """Calculate bandwidth usage percentage"""
        return float(self.bandwidth_usage_percentage)


    def resolve_is_deployment_allowed(self, info):
        """Check if deployment is allowed based on subscription"""
        return self.is_deployment_allowed

    def resolve_usage_summary(self, info):
        """Get complete usage summary"""
        summary = self.get_usage_summary()
        return UsageSummaryType(
            storage=StorageUsageType(**summary['storage']),
            bandwidth=BandwidthUsageType(**summary['bandwidth']),
            sites=SitesUsageType(**summary['sites']),
            custom_domains=CustomDomainsUsageType(**summary['custom_domains']),
            status=summary['status'],
            deployment_allowed=summary['deployment_allowed']
        )

    def resolve_usage_history(self, info, days=30):
        """Get usage history with time series data"""
        history = self.get_usage_history(days=days)

        data_points = [
            UsageDataPointType(
                recorded_at=point['recorded_at'],
                storage_used_gb=float(point['storage_used_gb']),
                bandwidth_used_gb=float(point['bandwidth_used_gb']),
                requests_count=point.get('requests_count'),
                avg_response_time_ms=point.get('avg_response_time_ms')
            )
            for point in history['data_points']
        ]

        current = history['current_usage']
        current_usage = UsageSummaryType(
            storage=StorageUsageType(**current['storage']),
            bandwidth=BandwidthUsageType(**current['bandwidth']),
            sites=SitesUsageType(**current['sites']),
            custom_domains=CustomDomainsUsageType(**current['custom_domains']),
            status=current['status'],
            deployment_allowed=current['deployment_allowed']
        )

        return UsageHistoryType(
            period_days=history['period_days'],
            data_points=data_points,
            current_usage=current_usage
        )

    def resolve_overage_cost(self, info):
        """Calculate overage costs"""
        overage = self.calculate_overage_cost()
        return OverageCostType(**overage)


class ResourceUsageLogType(DjangoObjectType):
    """
    Resource usage log entry

    Historical usage data for analytics and billing
    """

    id = graphene.ID(required=True)

    class Meta:
        model = ResourceUsageLog
        fields = (
            'id',
            'hosting_environment',
            'workspace',
            'site',
            'storage_used_gb',
            'bandwidth_used_gb',
            'requests_count',
            'estimated_cost_usd',
            'avg_response_time_ms',
            'error_rate_percentage',
            'recorded_at',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        """Return plain UUID/ID"""
        return str(self.id)
