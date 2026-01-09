# Root GraphQL schema for storefront
# IMPORTANT: Combines all queries and mutations

import graphene
from .queries.catalog_queries import ProductQueries
from .queries.category_queries import CategoryQueries
from .queries.cart_queries import CartQueries
from .queries.order_queries import OrderQueries
from .queries.puck_data_resolved_query import PuckDataResolvedQuery
from .queries.discount_queries import DiscountQueries
from .queries.checkout_queries import CheckoutQueries
from .queries.store_settings_queries import StoreSettingsQueries
from .queries.payment_queries import PaymentQueries
from .mutations.cart_mutations import CartMutations
from .mutations.checkout_mutations import CheckoutMutations
from .mutations.customer_auth_mutations import CustomerAuthMutations
from .mutations.customer_profile_mutations import CustomerProfileMutations
from .mutations.discount_mutations import DiscountMutations


class Query(
    ProductQueries,
    CategoryQueries,
    CartQueries,
    OrderQueries,
    PuckDataResolvedQuery,
    DiscountQueries,
    CheckoutQueries,
    StoreSettingsQueries,
    PaymentQueries,
    graphene.ObjectType
):
    """
    Root Query type

    Combines all query fields from different modules:
    - ProductQueries: Comprehensive product operations
    - CategoryQueries: Category operations
    - CartQueries: Shopping cart operations
    - OrderQueries: Order management operations
    - PuckDataResolvedQuery: Theme puck data with resolved section data
    - DiscountQueries: Discount validation and info
    - CheckoutQueries: Checkout operations (shipping, tracking)
    - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
    - PaymentQueries: Available payment methods
    """
    pass


class Mutation(
    CartMutations,
    CheckoutMutations,
    CustomerAuthMutations,
    CustomerProfileMutations,
    DiscountMutations,
    graphene.ObjectType
):
    """
    Root Mutation type

    Combines all mutation fields from different modules:
    - CartMutations: Shopping cart operations
    - CheckoutMutations: Checkout and order creation
    - CustomerAuthMutations: Customer signup/login/logout
    - CustomerProfileMutations: Customer profile management
    - DiscountMutations: Discount application and removal
    """
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)