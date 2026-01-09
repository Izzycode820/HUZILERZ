"""
Analytics GraphQL Schema

Schema definition for workspace analytics.
Integrated with store module schema for middleware inheritance.
"""

import graphene
from .queries.analytics_queries import AnalyticsQuery


class Query(AnalyticsQuery, graphene.ObjectType):
    """
    Analytics schema root query.
    
    Note: This schema is imported by store.graphql.schema
    for full middleware support and workspace auto-scoping.
    """
    pass


# Export schema (primarily for testing - production uses store schema)
schema = graphene.Schema(query=Query)