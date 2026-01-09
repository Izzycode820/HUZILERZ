"""
Theme System URLs - GraphQL Endpoint

All theme operations are now handled through GraphQL.
REST endpoints have been migrated to GraphQL queries and mutations.

Endpoint: /api/themes/graphql

Public Queries (no auth):
- themes: Browse theme store
- themeDetails: View theme details

Authenticated Queries (requires workspace):
- myThemes: User's theme library
- themeCustomization: Get customization for editor
- activeTheme: Currently published theme

Mutations (all require auth + workspace):
- addTheme: Clone theme to library
- updateThemeCustomization: Save Puck edits
- publishTheme: Make theme live
- unpublishTheme: Take theme offline
- deleteTheme: Remove from library
- duplicateTheme: Copy for experimentation
- renameTheme: Change theme name
"""

from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from .graphql.schema import schema
from .graphql.middleware.auth import ThemeAuthMiddleware

urlpatterns = [
    # GraphQL endpoint for all theme operations
    # Hybrid authentication: public queries (themes, themeDetails) + authenticated operations
    path('graphql/', csrf_exempt(GraphQLView.as_view(
        graphiql=True,
        schema=schema,
        middleware=[ThemeAuthMiddleware()]
    )), name='theme-graphql'),
]