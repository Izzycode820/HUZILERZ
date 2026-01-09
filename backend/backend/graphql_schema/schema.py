"""
Root GraphQL Schema
Combines all app-level schemas for the entire backend
"""

import graphene
from workspace.storefront.graphql.schema import Query as StorefrontQuery
from workspace.storefront.graphql.schema import Mutation as StorefrontMutation
from workspace.store.graphql.schema import Query as StoreQuery
from workspace.store.graphql.schema import Mutation as StoreMutation
from workspace.analytics.graphql.schema import Query as AnalyticsQuery
from notifications.graphql import NotificationQueries, NotificationMutations


class Query(
    StorefrontQuery,
    StoreQuery,
    AnalyticsQuery,
    NotificationQueries,
    graphene.ObjectType
):
    """Root query combining all apps"""
    pass


class Mutation(
    StorefrontMutation,
    StoreMutation,
    NotificationMutations,
    graphene.ObjectType
):
    """Root mutation combining all apps"""
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)