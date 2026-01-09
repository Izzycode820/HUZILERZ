"""
GraphQL Queries for Bulk Operations

Data fetching and filtering for bulk operation history
Follows GraphQL architecture standards with workspace scoping
"""

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from workspace.store.graphql.types.bulk_operation_types import (
    BulkOperationType, BulkOperationConnection
)
from workspace.store.models.bulk_operation import BulkOperation


class BulkOperationFilterSet(django_filters.FilterSet):
    """
    FilterSet for BulkOperation with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django-filter 2.0+ for security
    """
    class Meta:
        model = BulkOperation
        fields = {
            'operation_type': ['exact'],
            'status': ['exact'],
        }


class BulkOperationQueries:
    """Bulk Operation GraphQL queries"""

    # Single bulk operation by ID
    bulk_operation = graphene.Field(
        BulkOperationType,
        id=graphene.String(required=True),
        description="Get bulk operation by ID"
    )

    # Paginated bulk operations list
    bulk_operations = DjangoFilterConnectionField(
        BulkOperationType,
        filterset_class=BulkOperationFilterSet,
        description="Get paginated list of bulk operations"
    )

    # Recent bulk operations (last 10)
    recent_bulk_operations = graphene.List(
        BulkOperationType,
        limit=graphene.Int(default_value=10),
        description="Get recent bulk operations"
    )

    def resolve_bulk_operation(self, info, id):
        """Resolve bulk operation by ID with workspace scoping"""
        workspace = info.context.workspace

        try:
            return BulkOperation.objects.get(
                id=id,
                workspace=workspace
            )
        except BulkOperation.DoesNotExist:
            return None

    def resolve_bulk_operations(self, info, **kwargs):
        """Resolve paginated bulk operations with workspace scoping and filtering"""
        workspace = info.context.workspace

        queryset = BulkOperation.objects.filter(
            workspace=workspace
        ).order_by('-created_at')

        # Apply filters
        operation_type = kwargs.get('operation_type')
        status = kwargs.get('status')

        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def resolve_recent_bulk_operations(self, info, limit):
        """Resolve recent bulk operations with workspace scoping"""
        workspace = info.context.workspace

        return BulkOperation.objects.filter(
            workspace=workspace
        ).order_by('-created_at')[:limit]