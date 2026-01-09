# GraphQL queries for cart operations
# IMPORTANT: Uses Cart and GuestSession models owned by storefront

import graphene
from ..types.cart_types import CartType
from workspace.storefront.models import Cart, GuestSession


class CartQueries(graphene.ObjectType):
    """
    Storefront cart queries

    Performance: Uses select_related for optimization
    Security: Validates session and workspace
    """

    cart = graphene.Field(
        CartType,
        session_id=graphene.String(required=True),
        description="Get cart by session ID"
    )

    def resolve_cart(self, info, session_id):
        """
        Resolve cart query

        Performance: Uses select_related for items and products
        Security: Validates session expiration, workspace identified by middleware
        """
        # Get workspace from middleware
        workspace = info.context.workspace

        # Get session with cart
        try:
            session = GuestSession.objects.select_related('cart').get(
                session_id=session_id,
                workspace=workspace
            )
        except GuestSession.DoesNotExist:
            raise Exception("Session not found")

        # Check session expiration
        if session.is_expired:
            raise Exception("Session expired. Please create a new cart.")

        # Extend session on activity
        session.extend_expiration()

        # Return cart with optimized query
        if session.cart:
            # Prefetch cart items with products
            cart = Cart.objects.select_related('workspace').prefetch_related(
                'items__product'
            ).get(id=session.cart.id)
            return cart

        return None