"""
GraphQL Schema for Admin Store API

Root schema that combines all queries and mutations
Critical for API endpoint configuration
"""

import graphene
from .queries.product_queries import ProductQueries
from .queries.inventory_queries import InventoryQueries
from .queries.order_queries import OrderQueries
from .queries.category_queries import CategoryQueries
from .queries.discount_queries import DiscountQueries
from .queries.shipping_queries import ShippingQueries
from .queries.sales_channel_queries import SalesChannelQueries
from .queries.bulk_operation_queries import BulkOperationQueries
from .queries.variant_queries import VariantQueries
from .queries.store_profile_queries import StoreProfileQueries
from .queries.payment_method_queries import PaymentMethodQueries
from medialib.graphql.queries.media_queries import MediaQueries  # Import from medialib
from workspace.core.graphql.queries.customer_queries import CustomerQueries
from workspace.core.graphql.queries.membership_queries import MembershipQueries
from workspace.analytics.graphql.queries.analytics_queries import AnalyticsQuery
from .mutations.product_processing_mutations import ProductProcessingMutations
from .mutations.inventory_management_mutations import InventoryManagementMutations
from .mutations.order_processing_mutations import OrderProcessingMutations
from .mutations.category_mutations import CategoryMutations
from .mutations.discount_mutations import DiscountMutations
from .mutations.shipping_mutations import ShippingMutations
from .mutations.location_mutations import LocationMutations
from .mutations.sales_channel_mutations import SalesChannelMutations
from workspace.core.graphql.mutations.customer_mutations import CustomerMutations
from workspace.core.graphql.mutations.membership_mutations import MembershipMutations
from .mutations.bulk_mutations import BulkMutations
from .mutations.document_processor_mutations import DocumentProcessorMutations
from .mutations.csv_parser_mutations import CSVParserMutations
from .mutations.product_import_mutations import ProductImportMutations
from .mutations.variant_mutations import VariantMutations
from .mutations.store_profile_mutations import StoreProfileMutations
from .mutations.payment_method_mutations import PaymentMethodMutations
from medialib.graphql.mutations.media_mutations import MediaMutations  # Import from medialib


class Query(
    ProductQueries,
    InventoryQueries,
    OrderQueries,
    CategoryQueries,
    DiscountQueries,
    ShippingQueries,
    SalesChannelQueries,
    BulkOperationQueries,
    VariantQueries,
    MediaQueries,
    CustomerQueries,
    MembershipQueries,
    AnalyticsQuery,
    StoreProfileQueries,
    PaymentMethodQueries,
    graphene.ObjectType
):
    """
    Root GraphQL Query

    Combines all query types for the admin store API
    All queries are automatically workspace-scoped via JWT middleware
    """
    pass


class Mutation(
    ProductProcessingMutations,
    InventoryManagementMutations,
    OrderProcessingMutations,
    CategoryMutations,
    DiscountMutations,
    ShippingMutations,
    LocationMutations,
    SalesChannelMutations,
    CustomerMutations,
    MembershipMutations,
    BulkMutations,
    DocumentProcessorMutations,
    CSVParserMutations,
    ProductImportMutations,
    VariantMutations,
    MediaMutations,
    StoreProfileMutations,
    PaymentMethodMutations,
    graphene.ObjectType
):
    """
    Root GraphQL Mutation

    Combines all mutation types for the admin store API
    All mutations use @transaction.atomic for data integrity
    """
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)