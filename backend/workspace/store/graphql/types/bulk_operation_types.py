"""
GraphQL Types for Bulk Operations

Proper typed GraphQL objects for bulk operation data representation
Follows GraphQL architecture standards with DataLoader integration
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models.bulk_operation import BulkOperation
from workspace.store.graphql.types.common_types import BaseConnection


class BulkOperationType(DjangoObjectType):
    """
    GraphQL type for BulkOperation model

    Features:
    - All bulk operation fields with proper typing
    - Shopify-style operation types
    - Progress tracking and analytics
    - Custom computed fields
    """
    id = graphene.ID(required=True)

    class Meta:
        model = BulkOperation
        fields = (
            'id', 'workspace', 'user', 'operation_type', 'status',
            'total_items', 'processed_items', 'error_message',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    # Custom computed fields
    success_rate = graphene.Float()
    operation_type_display = graphene.String()
    is_completed = graphene.Boolean()
    is_failed = graphene.Boolean()
    is_processing = graphene.Boolean()

    def resolve_success_rate(self, info):
        """Calculate success rate percentage"""
        return self.success_rate

    def resolve_operation_type_display(self, info):
        """Get human-readable operation type"""
        return self.get_operation_type_display()

    def resolve_is_completed(self, info):
        """Check if operation is completed"""
        return self.status == 'success'

    def resolve_is_failed(self, info):
        """Check if operation failed"""
        return self.status == 'failed'

    def resolve_is_processing(self, info):
        """Check if operation is still processing"""
        return self.status == 'processing'


# Bulk Operation Connection for pagination
class BulkOperationConnection(graphene.relay.Connection):
    """Bulk operation connection with pagination support"""

    class Meta:
        node = BulkOperationType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()


# Response types for bulk operation mutations
class BulkOperationResponse(graphene.ObjectType):
    """
    Standard response type for bulk operation mutations

    Follows GraphQL architecture standards with proper typing
    """

    success = graphene.Boolean()
    operation = graphene.Field(BulkOperationType)
    message = graphene.String()
    error = graphene.String()


class BulkPublishResponse(graphene.ObjectType):
    """Response type for bulk publish operations"""

    success = graphene.Boolean()
    operation_id = graphene.String()
    processed_count = graphene.Int()
    message = graphene.String()
    error = graphene.String()


class BulkUpdateResponse(graphene.ObjectType):
    """Response type for bulk update operations"""

    success = graphene.Boolean()
    operation_id = graphene.String()
    processed_count = graphene.Int()
    message = graphene.String()
    error = graphene.String()


class BulkDeleteResponse(graphene.ObjectType):
    """Response type for bulk delete operations"""

    success = graphene.Boolean()
    operation_id = graphene.String()
    processed_count = graphene.Int()
    message = graphene.String()
    error = graphene.String()