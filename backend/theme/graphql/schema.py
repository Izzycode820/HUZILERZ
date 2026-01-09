"""
Theme GraphQL Schema

Combines public theme store and authenticated theme management
Routes:
- PUBLIC: Browse themes (/graphql/public or allow unauthenticated on main endpoint)
- AUTHENTICATED: Manage theme library (requires JWT + workspace)
"""

import graphene
from .queries.theme_showcase_queries import ThemeShowcaseQueries
from .queries.theme_management_queries import ThemeManagementQueries
from .queries.public_puck_data_query import PublicPuckDataQuery
from .mutations.theme_management_mutations import ThemeManagementMutations


class Query(
    PublicPuckDataQuery,
    ThemeShowcaseQueries,
    ThemeManagementQueries,
    graphene.ObjectType
):
    """
    Combined theme queries

    Public queries (no auth):
    - themes: Browse theme store
    - themeDetails: View single theme
    - publicPuckData: Fetch puck data for storefront (X-Store-Hostname header)

    Authenticated queries (requires workspace):
    - myThemes: User's theme library
    - themeCustomization: Get customization for editor
    - activeTheme: Currently published theme
    """
    pass


class Mutation(
    ThemeManagementMutations,
    graphene.ObjectType
):
    """
    Theme mutations (all require authentication + workspace scoping)

    - addTheme: Clone theme to library
    - updateThemeCustomization: Save Puck edits
    - publishTheme: Make theme live
    - unpublishTheme: Take theme offline
    - deleteTheme: Remove from library
    - duplicateTheme: Copy for experimentation
    - renameTheme: Change theme name
    """
    pass


# Schema instance
schema = graphene.Schema(query=Query, mutation=Mutation)
