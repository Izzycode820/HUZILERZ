# GraphQL mutations for discount operations
# IMPORTANT: Uses atomic transactions for data consistency

import graphene
from django.db import transaction
from ..types.cart_types import CartType
from ..types.discount_types import ApplyDiscountResultType, DiscountValidationType
from workspace.storefront.models import Cart, GuestSession
from workspace.storefront.services.cart_service import CartService
import logging

logger = logging.getLogger(__name__)


class ApplyDiscountToCartInput(graphene.InputObjectType):
    """
    Input type for applying discount code to cart
    """
    session_id = graphene.String(required=True)
    discount_code = graphene.String(required=True)


class ApplyDiscountToCart(graphene.Mutation):
    """
    Apply discount code to cart
    
    Performance: Atomic transaction with proper locking
    Security: Validates discount before application
    """
    
    class Arguments:
        input = ApplyDiscountToCartInput(required=True)
    
    success = graphene.Boolean()
    error = graphene.String()
    message = graphene.String()
    cart = graphene.Field(CartType)
    
    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        """
        Apply discount mutation
        
        Reliability: Atomic transaction ensures consistency
        Security: Validates discount eligibility
        """
        try:
            # Get workspace from middleware
            workspace = info.context.workspace
            
            # Get session and cart
            session = GuestSession.objects.select_related('cart').get(
                session_id=input.session_id,
                workspace=workspace
            )
            
            if session.is_expired:
                return ApplyDiscountToCart(
                    success=False,
                    error="Session expired. Please create a new cart.",
                    cart=None
                )
            
            cart = session.cart
            if not cart:
                return ApplyDiscountToCart(
                    success=False,
                    error="Cart not found",
                    cart=None
                )
            
            # Get authenticated customer from session if available
            customer = None
            if hasattr(session, 'customer') and session.customer:
                customer = session.customer
            
            # Apply discount using CartService
            result = CartService.apply_discount(
                cart=cart,
                discount_code=input.discount_code,
                customer=customer
            )
            
            if not result['success']:
                return ApplyDiscountToCart(
                    success=False,
                    error=result['error'],
                    cart=cart
                )
            
            # Extend session on activity
            session.extend_expiration()
            
            # Refresh cart to get updated discount
            cart.refresh_from_db()
            
            logger.info(
                "Discount applied to cart",
                extra={
                    'session_id': input.session_id,
                    'discount_code': input.discount_code,
                    'workspace': workspace.slug
                }
            )
            
            return ApplyDiscountToCart(
                success=True,
                message=result.get('message', 'Discount applied successfully'),
                cart=cart
            )
            
        except GuestSession.DoesNotExist:
            return ApplyDiscountToCart(
                success=False,
                error="Session not found",
                cart=None
            )
        except Exception as e:
            logger.error(f"Failed to apply discount: {str(e)}", exc_info=True)
            return ApplyDiscountToCart(
                success=False,
                error=f"Failed to apply discount: {str(e)}",
                cart=None
            )


class RemoveDiscountFromCartInput(graphene.InputObjectType):
    """
    Input type for removing discount from cart
    """
    session_id = graphene.String(required=True)


class RemoveDiscountFromCart(graphene.Mutation):
    """
    Remove discount from cart
    
    Performance: Atomic transaction
    """
    
    class Arguments:
        input = RemoveDiscountFromCartInput(required=True)
    
    success = graphene.Boolean()
    error = graphene.String()
    message = graphene.String()
    cart = graphene.Field(CartType)
    
    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        """
        Remove discount mutation
        """
        try:
            # Get workspace from middleware
            workspace = info.context.workspace
            
            # Get session and cart
            session = GuestSession.objects.select_related('cart').get(
                session_id=input.session_id,
                workspace=workspace
            )
            
            if session.is_expired:
                return RemoveDiscountFromCart(
                    success=False,
                    error="Session expired. Please create a new cart.",
                    cart=None
                )
            
            cart = session.cart
            if not cart:
                return RemoveDiscountFromCart(
                    success=False,
                    error="Cart not found",
                    cart=None
                )
            
            # Remove discount using CartService
            result = CartService.remove_discount(cart=cart)
            
            if not result['success']:
                return RemoveDiscountFromCart(
                    success=False,
                    error=result['error'],
                    cart=cart
                )
            
            # Extend session on activity
            session.extend_expiration()
            
            # Refresh cart
            cart.refresh_from_db()
            
            logger.info(
                "Discount removed from cart",
                extra={
                    'session_id': input.session_id,
                    'workspace': workspace.slug
                }
            )
            
            return RemoveDiscountFromCart(
                success=True,
                message=result.get('message', 'Discount removed successfully'),
                cart=cart
            )
            
        except GuestSession.DoesNotExist:
            return RemoveDiscountFromCart(
                success=False,
                error="Session not found",
                cart=None
            )
        except Exception as e:
            logger.error(f"Failed to remove discount: {str(e)}", exc_info=True)
            return RemoveDiscountFromCart(
                success=False,
                error=f"Failed to remove discount: {str(e)}",
                cart=None
            )


class ApplyAutomaticDiscountsInput(graphene.InputObjectType):
    """
    Input type for applying automatic discounts
    """
    session_id = graphene.String(required=True)


class ApplyAutomaticDiscounts(graphene.Mutation):
    """
    Apply best automatic discount to cart
    
    Performance: Evaluates all automatic discounts and applies best one
    """
    
    class Arguments:
        input = ApplyAutomaticDiscountsInput(required=True)
    
    success = graphene.Boolean()
    error = graphene.String()
    message = graphene.String()
    cart = graphene.Field(CartType)
    discount_applied = graphene.Boolean()
    
    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        """
        Apply automatic discounts mutation
        """
        try:
            # Get workspace from middleware
            workspace = info.context.workspace
            
            # Get session and cart
            session = GuestSession.objects.select_related('cart').get(
                session_id=input.session_id,
                workspace=workspace
            )
            
            if session.is_expired:
                return ApplyAutomaticDiscounts(
                    success=False,
                    error="Session expired. Please create a new cart.",
                    cart=None,
                    discount_applied=False
                )
            
            cart = session.cart
            if not cart:
                return ApplyAutomaticDiscounts(
                    success=False,
                    error="Cart not found",
                    cart=None,
                    discount_applied=False
                )
            
            # Get authenticated customer from session if available
            customer = None
            if hasattr(session, 'customer') and session.customer:
                customer = session.customer
            
            # Apply automatic discounts using CartService
            result = CartService.apply_automatic_discounts(
                cart=cart,
                customer=customer
            )
            
            if not result['success']:
                return ApplyAutomaticDiscounts(
                    success=False,
                    error=result['error'],
                    cart=cart,
                    discount_applied=False
                )
            
            # Extend session on activity
            session.extend_expiration()
            
            # Refresh cart
            cart.refresh_from_db()
            
            logger.info(
                "Automatic discounts evaluated",
                extra={
                    'session_id': input.session_id,
                    'discount_applied': result.get('discount_applied', False),
                    'workspace': workspace.slug
                }
            )
            
            return ApplyAutomaticDiscounts(
                success=True,
                message=result.get('message', 'Automatic discounts evaluated'),
                cart=cart,
                discount_applied=result.get('discount_applied', False)
            )
            
        except GuestSession.DoesNotExist:
            return ApplyAutomaticDiscounts(
                success=False,
                error="Session not found",
                cart=None,
                discount_applied=False
            )
        except Exception as e:
            logger.error(f"Failed to apply automatic discounts: {str(e)}", exc_info=True)
            return ApplyAutomaticDiscounts(
                success=False,
                error=f"Failed to apply automatic discounts: {str(e)}",
                cart=None,
                discount_applied=False
            )


class DiscountMutations(graphene.ObjectType):
    """
    Collection of discount mutations for storefront
    """
    apply_discount_to_cart = ApplyDiscountToCart.Field()
    remove_discount_from_cart = RemoveDiscountFromCart.Field()
    apply_automatic_discounts = ApplyAutomaticDiscounts.Field()
