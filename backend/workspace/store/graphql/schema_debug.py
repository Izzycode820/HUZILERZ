"""
DEBUG Schema - Tests each query individually to find the problematic one
"""

import graphene

# Test queries ONE by ONE
print("\n=== LOADING QUERIES ===")

try:
    print("Loading ProductQueries...")
    from .queries.product_queries import ProductQueries
    print("✓ ProductQueries OK")
except Exception as e:
    print(f"✗ ProductQueries FAILED: {e}")
    ProductQueries = None

try:
    print("Loading InventoryQueries...")
    from .queries.inventory_queries import InventoryQueries
    print("✓ InventoryQueries OK")
except Exception as e:
    print(f"✗ InventoryQueries FAILED: {e}")
    InventoryQueries = None

try:
    print("Loading OrderQueries...")
    from .queries.order_queries import OrderQueries
    print("✓ OrderQueries OK")
except Exception as e:
    print(f"✗ OrderQueries FAILED: {e}")
    OrderQueries = None

try:
    print("Loading CategoryQueries...")
    from .queries.category_queries import CategoryQueries
    print("✓ CategoryQueries OK")
except Exception as e:
    print(f"✗ CategoryQueries FAILED: {e}")
    CategoryQueries = None

try:
    print("Loading DiscountQueries...")
    from .queries.discount_queries import DiscountQueries
    print("✓ DiscountQueries OK")
except Exception as e:
    print(f"✗ DiscountQueries FAILED: {e}")
    DiscountQueries = None

try:
    print("Loading ShippingQueries...")
    from .queries.shipping_queries import ShippingQueries
    print("✓ ShippingQueries OK")
except Exception as e:
    print(f"✗ ShippingQueries FAILED: {e}")
    ShippingQueries = None

try:
    print("Loading SalesChannelQueries...")
    from .queries.sales_channel_queries import SalesChannelQueries
    print("✓ SalesChannelQueries OK")
except Exception as e:
    print(f"✗ SalesChannelQueries FAILED: {e}")
    SalesChannelQueries = None

try:
    print("Loading CustomerQueries...")
    from workspace.core.graphql.queries.customer_queries import CustomerQueries
    print("✓ CustomerQueries OK")
except Exception as e:
    print(f"✗ CustomerQueries FAILED: {e}")
    CustomerQueries = None

try:
    print("Loading AnalyticsQuery...")
    from workspace.analytics.graphql.queries.analytics_queries import AnalyticsQuery
    print("✓ AnalyticsQuery OK")
except Exception as e:
    print(f"✗ AnalyticsQuery FAILED: {e}")
    AnalyticsQuery = None

try:
    print("Loading BulkOperationQueries...")
    from .queries.bulk_operation_queries import BulkOperationQueries
    print("✓ BulkOperationQueries OK")
except Exception as e:
    print(f"✗ BulkOperationQueries FAILED: {e}")
    BulkOperationQueries = None

try:
    print("Loading VariantQueries...")
    from .queries.variant_queries import VariantQueries
    print("✓ VariantQueries OK")
except Exception as e:
    print(f"✗ VariantQueries FAILED: {e}")
    VariantQueries = None

print("\n=== LOADING MUTATIONS ===")

# Load mutations (less likely to have the issue)
from .mutations.product_processing_mutations import ProductProcessingMutations
from .mutations.inventory_management_mutations import InventoryManagementMutations
from .mutations.order_processing_mutations import OrderProcessingMutations
from .mutations.category_mutations import CategoryMutations
from .mutations.discount_mutations import DiscountMutations
from .mutations.shipping_mutations import ShippingMutations
from .mutations.sales_channel_mutations import SalesChannelMutations
from workspace.core.graphql.mutations.customer_mutations import CustomerMutations
from .mutations.bulk_mutations import BulkMutations
from .mutations.document_processor_mutations import DocumentProcessorMutations
from .mutations.csv_parser_mutations import CSVParserMutations
from .mutations.product_import_mutations import ProductImportMutations
from .mutations.variant_mutations import VariantMutations

print("\n=== BUILDING QUERY CLASS ===")

# Build query class with only loaded queries
query_bases = []
if ProductQueries:
    query_bases.append(ProductQueries)
if InventoryQueries:
    query_bases.append(InventoryQueries)
if OrderQueries:
    query_bases.append(OrderQueries)
if CategoryQueries:
    query_bases.append(CategoryQueries)
if DiscountQueries:
    query_bases.append(DiscountQueries)
if ShippingQueries:
    query_bases.append(ShippingQueries)
if SalesChannelQueries:
    query_bases.append(SalesChannelQueries)
if CustomerQueries:
    query_bases.append(CustomerQueries)
if AnalyticsQuery:
    query_bases.append(AnalyticsQuery)
if BulkOperationQueries:
    query_bases.append(BulkOperationQueries)
if VariantQueries:
    query_bases.append(VariantQueries)

query_bases.append(graphene.ObjectType)

Query = type('Query', tuple(query_bases), {'__doc__': 'Debug Query'})

print("\n=== BUILDING MUTATION CLASS ===")

class Mutation(
    ProductProcessingMutations,
    InventoryManagementMutations,
    OrderProcessingMutations,
    CategoryMutations,
    DiscountMutations,
    ShippingMutations,
    SalesChannelMutations,
    CustomerMutations,
    BulkMutations,
    DocumentProcessorMutations,
    CSVParserMutations,
    ProductImportMutations,
    VariantMutations,
    graphene.ObjectType
):
    pass

print("\n=== TESTING EACH QUERY CLASS INDIVIDUALLY ===")

# Test each query class separately to find the problematic one
test_queries = [
    ("ProductQueries", ProductQueries),
    ("InventoryQueries", InventoryQueries),
    ("OrderQueries", OrderQueries),
    ("CategoryQueries", CategoryQueries),
    ("DiscountQueries", DiscountQueries),
    ("ShippingQueries", ShippingQueries),
    ("SalesChannelQueries", SalesChannelQueries),
    ("CustomerQueries", CustomerQueries),
    ("AnalyticsQuery", AnalyticsQuery),
    ("BulkOperationQueries", BulkOperationQueries),
    ("VariantQueries", VariantQueries),
]

for name, query_class in test_queries:
    try:
        print(f"Testing schema with {name}...")
        TestQuery = type('TestQuery', (query_class, graphene.ObjectType), {})
        test_schema = graphene.Schema(query=TestQuery)
        print(f"  ✓ {name} schema OK")
    except Exception as e:
        print(f"  ✗ {name} FAILED: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n^^^ FOUND IT! {name} has the problematic field ^^^")
        raise

print("\n=== CREATING FULL SCHEMA ===")
print("All individual queries passed, testing combined schema...")

try:
    schema = graphene.Schema(query=Query, mutation=Mutation)
    print("✓ Schema created successfully!")
except Exception as e:
    print(f"✗ COMBINED SCHEMA FAILED!")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    raise
