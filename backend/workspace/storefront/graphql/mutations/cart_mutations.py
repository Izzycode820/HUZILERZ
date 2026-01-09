# GraphQL mutations for cart operations
# IMPORTANT: Uses atomic transactions for data consistency

import graphene
from django.db import transaction
from ..types.cart_types import CartType, CartCreationResultType
from ..types.common_types import MutationResult
from workspace.storefront.models import Cart, GuestSession
from workspace.store.models import Product, ProductVariant
from workspace.storefront.services.cart_service import CartService


class AddToCartInput(graphene.InputObjectType):
    """
    Input type for adding items to cart with variant support
    """
    session_id = graphene.String(required=True)
    product_id = graphene.ID(required=True)
    variant_id = graphene.ID()
    quantity = graphene.Int(required=True)


class UpdateCartItemInput(graphene.InputObjectType):
    """
    Input type for updating cart item quantities with variant support
    """
    session_id = graphene.String(required=True)
    product_id = graphene.ID(required=True)
    variant_id = graphene.ID()
    quantity = graphene.Int(required=True)


class CreateCart(graphene.Mutation):
    """
    Create new guest cart and session

    Security: Rate limited to prevent abuse
    Performance: Atomic transaction
    """

    class Arguments:
        pass

    session_id = graphene.String()
    expires_at = graphene.DateTime()
    cart = graphene.Field(CartType)

    @staticmethod
    @transaction.atomic
    def mutate(root, info):
        """
        Create cart mutation

        Reliability: Atomic transaction ensures consistency
        Logging: Logs cart creation for analytics
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Get workspace from middleware
            workspace = info.context.workspace

            # Get client info from request context
            request = info.context
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Create session and cart
            session = GuestSession.create_session(
                workspace=workspace,
                ip_address=ip_address,
                user_agent=user_agent
            )

            cart = Cart.objects.create(
                workspace=workspace,
                session_id=session.session_id,
                currency='XAF',
                is_active=True
            )

            session.cart = cart
            session.save(update_fields=['cart'])

            # Log for analytics
            logger.info(
                "Cart created",
                extra={
                    'session_id': session.session_id,
                    'workspace': workspace.slug,
                    'ip_address': ip_address
                }
            )

            return CreateCart(
                session_id=session.session_id,
                expires_at=session.expires_at,
                cart=cart
            )

        except Exception as e:
            logger.error(f"Failed to create cart: {str(e)}")
            raise Exception("Failed to create cart")


class AddToCart(graphene.Mutation):
    """
    Add product to cart with variant support

    Performance: Uses select_for_update to prevent race conditions
    Security: Validates stock availability
    """

    class Arguments:
        input = AddToCartInput(required=True)

    cart = graphene.Field(CartType)

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        """
        Add to cart mutation with variant support

        Reliability: Atomic transaction prevents inventory issues
        Performance: Locks product/variant rows to prevent race conditions
        """
        from workspace.core.models import Workspace
        import logging

        logger = logging.getLogger(__name__)

        # Validate quantity
        if input.quantity <= 0:
            raise Exception("Quantity must be greater than 0")

        try:
            # Get workspace from middleware
            workspace = info.context.workspace

            # Get session and cart
            session = GuestSession.objects.select_related('cart').get(
                session_id=input.session_id,
                workspace=workspace
            )

            if session.is_expired:
                raise Exception("Session expired. Please create a new cart.")

            # Get product and variant with lock (prevent race conditions)
            product = Product.objects.select_for_update().get(
                id=input.product_id,
                workspace=workspace,
                status='published',
                is_active=True
            )

            # Get variant if provided
            variant = None
            if input.variant_id:
                variant = ProductVariant.objects.select_for_update().get(
                    id=input.variant_id,
                    product=product,
                    is_active=True
                )

            # Add to cart using CartService with variant support
            cart = session.cart
            CartService.add_item(
                cart=cart,
                product=product,
                quantity=input.quantity,
                variant=variant,
                session_id=input.session_id
            )

            # Extend session on activity
            session.extend_expiration()

            logger.info(
                "Item added to cart",
                extra={
                    'session_id': input.session_id,
                    'product_id': input.product_id,
                    'variant_id': input.variant_id,
                    'quantity': input.quantity
                }
            )

            return AddToCart(cart=cart)

        except (Workspace.DoesNotExist, GuestSession.DoesNotExist, Product.DoesNotExist):
            raise Exception("Resource not found")
        except ValueError as e:
            # Business logic errors (insufficient stock, etc.)
            raise Exception(str(e))
        except Exception as e:
            logger.error(f"Failed to add to cart: {str(e)}")
            raise Exception("Failed to add item to cart")


class UpdateCartItem(graphene.Mutation):
    """
    Update cart item quantity with variant support
    """

    class Arguments:
        input = UpdateCartItemInput(required=True)

    cart = graphene.Field(CartType)

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        """
        Update cart item mutation with variant support
        """
        from workspace.core.models import Workspace

        try:
            # Get workspace from middleware
            workspace = info.context.workspace

            session = GuestSession.objects.select_related('cart').get(
                session_id=input.session_id,
                workspace=workspace
            )

            if session.is_expired:
                raise Exception("Session expired. Please create a new cart.")

            cart = session.cart
            CartService.update_item_quantity(
                cart=cart,
                product_id=input.product_id,
                quantity=input.quantity,
                variant_id=input.variant_id,
                session_id=input.session_id
            )

            # Extend session on activity
            session.extend_expiration()

            return UpdateCartItem(cart=cart)

        except (Workspace.DoesNotExist, GuestSession.DoesNotExist):
            raise Exception("Resource not found")
        except ValueError as e:
            raise Exception(str(e))


class RemoveFromCartInput(graphene.InputObjectType):
    """
    Input type for removing items from cart with variant support
    """
    session_id = graphene.String(required=True)
    product_id = graphene.ID(required=True)
    variant_id = graphene.ID()


class RemoveFromCart(graphene.Mutation):
    """
    Remove item from cart with variant support
    """

    class Arguments:
        input = RemoveFromCartInput(required=True)

    cart = graphene.Field(CartType)

    @staticmethod
    def mutate(root, info, input):
        """
        Remove from cart mutation with variant support
        """
        from workspace.core.models import Workspace

        try:
            # Get workspace from middleware
            workspace = info.context.workspace

            session = GuestSession.objects.select_related('cart').get(
                session_id=input.session_id,
                workspace=workspace
            )

            if session.is_expired:
                raise Exception("Session expired. Please create a new cart.")

            cart = session.cart
            success = CartService.remove_item(
                cart=cart,
                product_id=input.product_id,
                variant_id=input.variant_id,
                session_id=input.session_id
            )

            if not success:
                raise Exception("Item not found in cart")

            # Extend session on activity
            session.extend_expiration()

            return RemoveFromCart(cart=cart)

        except (Workspace.DoesNotExist, GuestSession.DoesNotExist):
            raise Exception("Resource not found")


class ClearCartInput(graphene.InputObjectType):
    """
    Input type for clearing cart
    """
    session_id = graphene.String(required=True)


class ClearCart(graphene.Mutation):
    """
    Clear all items from cart
    """

    class Arguments:
        input = ClearCartInput(required=True)

    cart = graphene.Field(CartType)

    @staticmethod
    def mutate(root, info, input):
        """
        Clear cart mutation
        """
        from workspace.core.models import Workspace

        try:
            # Get workspace from middleware
            workspace = info.context.workspace

            session = GuestSession.objects.select_related('cart').get(
                session_id=input.session_id,
                workspace=workspace
            )

            if session.is_expired:
                raise Exception("Session expired. Please create a new cart.")

            cart = session.cart
            CartService.clear_cart(cart)

            # Extend session on activity
            session.extend_expiration()

            return ClearCart(cart=cart)

        except (Workspace.DoesNotExist, GuestSession.DoesNotExist):
            raise Exception("Resource not found")


class CartMutations(graphene.ObjectType):
    """
    Collection of cart mutations
    """
    create_cart = CreateCart.Field()
    add_to_cart = AddToCart.Field()
    update_cart_item = UpdateCartItem.Field()
    remove_from_cart = RemoveFromCart.Field()
    clear_cart = ClearCart.Field()
    
    # Discount mutations (imported from discount_mutations)
    # Note: These are re-exported here for convenience but defined in discount_mutations.py
    # To use: import from discount_mutations and add fields here