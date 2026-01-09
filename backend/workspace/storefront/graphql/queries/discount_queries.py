# GraphQL queries for discount operations
# IMPORTANT: Customer-facing discount validation and info

import graphene
from ..types.discount_types import DiscountValidationType
from workspace.store.services.discount_service import DiscountService
from workspace.storefront.models import GuestSession
import logging

logger = logging.getLogger(__name__)


class DiscountQueries(graphene.ObjectType):
    """
    Storefront discount queries
    
    Performance: Lightweight validation queries
    Security: Validates workspace and discount eligibility
    """
    
    validate_discount_code = graphene.Field(
        DiscountValidationType,
        session_id=graphene.String(required=True),
        discount_code=graphene.String(required=True),
        description="Validate discount code before applying to cart"
    )
    
    def resolve_validate_discount_code(self, info, session_id, discount_code):
        """
        Validate discount code for customer
        
        Performance: Quick validation without applying
        Security: Workspace scoping and eligibility checks
        """
        try:
            # Get workspace from middleware
            workspace = info.context.workspace
            
            # Get session and cart
            try:
                session = GuestSession.objects.select_related('cart').get(
                    session_id=session_id,
                    workspace=workspace
                )
            except GuestSession.DoesNotExist:
                return DiscountValidationType(
                    valid=False,
                    error="Session not found"
                )
            
            if session.is_expired:
                return DiscountValidationType(
                    valid=False,
                    error="Session expired. Please create a new cart."
                )
            
            cart = session.cart
            if not cart:
                return DiscountValidationType(
                    valid=False,
                    error="Cart not found"
                )
            
            # Get authenticated customer from session if available
            customer = None
            if hasattr(session, 'customer') and session.customer:
                customer = session.customer
            
            # Validate discount using store service
            validation = DiscountService.validate_discount_code(
                workspace=workspace,
                code=discount_code,
                customer=customer,
                cart=cart
            )
            
            if validation['valid']:
                discount = validation['discount']
                return DiscountValidationType(
                    valid=True,
                    discount_code=discount.code,
                    discount_name=discount.name,
                    discount_type=discount.discount_type,
                    message=validation.get('message', 'Discount code is valid')
                )
            else:
                return DiscountValidationType(
                    valid=False,
                    error=validation['error']
                )
                
        except Exception as e:
            logger.error(f"Discount validation failed: {str(e)}", exc_info=True)
            return DiscountValidationType(
                valid=False,
                error=f"Validation failed: {str(e)}"
            )
