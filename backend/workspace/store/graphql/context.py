"""
GraphQL Context Builder

Builds GraphQL context with workspace and DataLoaders
Critical for multi-tenant security and N+1 query prevention
"""

from .dataloaders import LoaderRegistry


def build_context(request):
    """
    Build GraphQL context with workspace and loaders

    This function is called for each GraphQL request
    and creates the context that resolvers can access
    """
    return {
        'request': request,
        'loaders': LoaderRegistry()
        # workspace and user_id are injected by AuthenticationMiddleware
    }