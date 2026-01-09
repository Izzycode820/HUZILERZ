"""
Customer GraphQL Queries for Workspace

Provides customer queries with workspace auto-scoping
"""

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from ..types.customer_types import CustomerType, CustomerConnection
from workspace.core.models.customer_model import Customer
from workspace.store.utils.workspace_permissions import assert_permission


class CustomerFilterSet(django_filters.FilterSet):
    """
    FilterSet for Customer with explicit field definitions

    Security: Explicitly defines filterable fields
    Best Practice: Required by django-filter 2.0+
    """
    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains'],
            'phone': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'customer_type': ['exact'],
            'region': ['exact'],
            'is_active': ['exact'],
        }


class CustomerQueries(graphene.ObjectType):
    """
    Customer queries with workspace auto-scoping

    Security: All queries automatically scoped to authenticated workspace
    Performance: Uses select_related for N+1 query prevention
    """

    customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilterSet,
        description="List all customers with pagination and filtering"
    )

    customer = graphene.Field(
        CustomerType,
        id=graphene.ID(required=True),
        description="Get single customer by ID"
    )

    customer_by_phone = graphene.Field(
        CustomerType,
        phone=graphene.String(required=True),
        description="Get customer by phone number"
    )

    recent_customers = graphene.List(
        CustomerType,
        limit=graphene.Int(default_value=50),
        description="Get recent customers"
    )

    def resolve_customers(self, info, **kwargs):
        """
        Resolve customers with workspace auto-scoping

        Performance: Uses select_related and proper indexing
        Security: Automatically scoped to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:view')

        return Customer.objects.filter(
            workspace=workspace,
            is_active=True
        ).select_related('workspace').order_by('-created_at')

    def resolve_customer(self, info, id):
        """
        Resolve single customer with workspace validation

        Security: Ensures customer belongs to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:view')

        try:
            return Customer.objects.select_related('workspace').get(
                id=id,
                workspace=workspace
            )
        except Customer.DoesNotExist:
            raise GraphQLError("Customer not found")

    def resolve_customer_by_phone(self, info, phone):
        """
        Resolve customer by phone with workspace validation

        Performance: Phone field is indexed
        """
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:view')

        try:
            return Customer.objects.select_related('workspace').get(
                workspace=workspace,
                phone=phone
            )
        except Customer.DoesNotExist:
            raise GraphQLError(f"Customer with phone {phone} not found")

    def resolve_recent_customers(self, info, limit):
        """
        Resolve recent customers

        Performance: Limited query with proper indexing
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # Validate permissions
        assert_permission(workspace, user, 'customer:view')

        return Customer.objects.filter(
            workspace=workspace,
            is_active=True
        ).select_related('workspace').order_by('-created_at')[:limit]
