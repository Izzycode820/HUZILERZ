"""
Storefront GraphQL View with Tenant Context Injection
"""
from graphene_file_upload.django import FileUploadGraphQLView


class StorefrontGraphQLView(FileUploadGraphQLView):
    """
    Custom GraphQL view that injects tenant context from StoreIdentificationMiddleware

    The middleware sets:
    - request.workspace
    - request.deployed_site
    - request.tenant_id
    - request.store_slug

    These are passed to GraphQL context so resolvers can access via:
    - info.context.workspace
    - info.context.deployed_site
    - info.context.tenant_id
    """

    def get_context(self, request):
        """
        Override to inject tenant context into GraphQL

        This method is called by graphene to create the context object
        that's available in resolvers as info.context
        """
        context = super().get_context(request)

        # Inject tenant context from middleware
        # These will be None if middleware didn't run (e.g., non-storefront paths)
        context.workspace = getattr(request, 'workspace', None)
        context.deployed_site = getattr(request, 'deployed_site', None)
        context.tenant_id = getattr(request, 'tenant_id', None)
        context.store_slug = getattr(request, 'store_slug', None)

        # Also inject metadata for debugging
        context.tenant_domain_type = getattr(request, 'tenant_domain_type', None)
        context.tenant_hostname = getattr(request, 'tenant_hostname', None)

        # Initialize performance metrics list
        context.performance_metrics = []

        return context
