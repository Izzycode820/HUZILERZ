"""
Discount GraphQL Mutations for Admin Store API

Production-ready discount mutations using DiscountService
"""

import graphene
from graphql import GraphQLError
from ..types.discount_types import DiscountType
from workspace.store.services.discount_service import discount_service


class DiscountInput(graphene.InputObjectType):
    """Input for creating/updating discounts"""
    code = graphene.String(required=True)
    name = graphene.String(required=True)
    method = graphene.String()
    discount_type = graphene.String(required=True)

    # For amount_off_product
    discount_value_type = graphene.String()
    value = graphene.Decimal()

    # For buy_x_get_y - Customer buys
    customer_buys_type = graphene.String()
    customer_buys_quantity = graphene.Int()
    customer_buys_value = graphene.Decimal()
    customer_buys_product_ids = graphene.List(graphene.ID)

    # For buy_x_get_y - Customer gets
    customer_gets_quantity = graphene.Int()
    customer_gets_product_ids = graphene.List(graphene.ID)
    bxgy_discount_type = graphene.String()
    bxgy_value = graphene.Decimal()
    max_uses_per_order = graphene.Int()

    # Usage limits
    usage_limit = graphene.Int()
    usage_limit_per_customer = graphene.Int()

    # Active dates
    starts_at = graphene.DateTime()
    ends_at = graphene.DateTime()

    # Minimum purchase requirements (Page 2 - Shared)
    minimum_requirement_type = graphene.String()
    minimum_purchase_amount = graphene.Decimal()
    minimum_quantity_items = graphene.Int()

    # Customer targeting
    applies_to_all_customers = graphene.Boolean(default_value=True)
    customer_segmentation = graphene.JSONString()

    # Product targeting
    applies_to_all_products = graphene.Boolean(default_value=True)
    product_ids = graphene.List(graphene.ID)
    category_ids = graphene.List(graphene.ID)

    # Regional targeting
    applies_to_regions = graphene.List(graphene.String)
    applies_to_customer_types = graphene.List(graphene.String)

    # Maximum discount uses (Page 2 - Shared)
    limit_total_uses = graphene.Boolean()
    limit_one_per_customer = graphene.Boolean()

    # Combinations (Page 2 - Shared)
    can_combine_with_product_discounts = graphene.Boolean()
    can_combine_with_order_discounts = graphene.Boolean()

    # Status
    status = graphene.String(default_value='active')


class CreateDiscount(graphene.Mutation):
    """Create discount with service layer orchestration"""

    class Arguments:
        input = DiscountInput(required=True)

    # PROPER TYPED RESPONSE - NOT JSONString
    success = graphene.Boolean()
    discount = graphene.Field(DiscountType)  # Proper DiscountType
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Normalize enum fields to lowercase to handle frontend/backend mismatch
            discount_type = input.discount_type.lower()
            method = input.method.lower() if input.method else 'discount_code'
            
            # Convert GraphQL input to service format
            discount_data = {
                'code': input.code,
                'name': input.name,
                'method': method,
                'discount_type': discount_type,
                'usage_limit': input.usage_limit,
                'usage_limit_per_customer': input.usage_limit_per_customer,
                'starts_at': input.starts_at,
                'ends_at': input.ends_at,
                'applies_to_all_customers': input.applies_to_all_customers,
                'customer_segmentation': input.customer_segmentation if input.customer_segmentation else {},
                'applies_to_all_products': input.applies_to_all_products,
                'product_ids': input.product_ids if input.product_ids else [],
                'category_ids': input.category_ids if input.category_ids else [],
                'applies_to_regions': input.applies_to_regions if input.applies_to_regions else [],
                'applies_to_customer_types': input.applies_to_customer_types if input.applies_to_customer_types else [],
                'status': input.status.lower() if input.status else 'active',
                'minimum_requirement_type': input.minimum_requirement_type.lower() if input.minimum_requirement_type else 'none',
                'minimum_purchase_amount': float(input.minimum_purchase_amount) if input.minimum_purchase_amount else None,
                'minimum_quantity_items': input.minimum_quantity_items,
                'limit_total_uses': input.limit_total_uses if input.limit_total_uses else False,
                'limit_one_per_customer': input.limit_one_per_customer if input.limit_one_per_customer else False,
                'can_combine_with_product_discounts': input.can_combine_with_product_discounts if input.can_combine_with_product_discounts else False,
                'can_combine_with_order_discounts': input.can_combine_with_order_discounts if input.can_combine_with_order_discounts else False,
            }

            # Add type-specific fields using NORMALIZED type
            if discount_type == 'amount_off_product':
                discount_data.update({
                    'discount_value_type': input.discount_value_type.lower() if input.discount_value_type else None,
                    'value': float(input.value) if input.value else None,
                })
            elif discount_type == 'buy_x_get_y':
                discount_data.update({
                    'customer_buys_type': input.customer_buys_type.lower() if input.customer_buys_type else None,
                    'customer_buys_quantity': input.customer_buys_quantity,
                    'customer_buys_value': float(input.customer_buys_value) if input.customer_buys_value else None,
                    'customer_buys_product_ids': input.customer_buys_product_ids if input.customer_buys_product_ids else [],
                    'customer_gets_quantity': input.customer_gets_quantity,
                    'customer_gets_product_ids': input.customer_gets_product_ids if input.customer_gets_product_ids else [],
                    'bxgy_discount_type': input.bxgy_discount_type.lower() if input.bxgy_discount_type else None,
                    'bxgy_value': float(input.bxgy_value) if input.bxgy_value else None,
                    'max_uses_per_order': input.max_uses_per_order,
                })

            # Call service layer with workspace object
            result = discount_service.create_discount(
                workspace=workspace,
                discount_data=discount_data,
                user=user
            )

            return CreateDiscount(
                success=result['success'],
                discount=result.get('discount'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Discount creation mutation failed: {str(e)}", exc_info=True)

            return CreateDiscount(
                success=False,
                error=f"Discount creation failed: {str(e)}"
            )


class UpdateDiscount(graphene.Mutation):
    """Update discount with service layer orchestration"""

    class Arguments:
        discount_id = graphene.String(required=True)
        update_data = DiscountInput(required=True)

    # PROPER TYPED RESPONSE - NOT JSONString
    success = graphene.Boolean()
    discount = graphene.Field(DiscountType)  # Proper DiscountType
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, discount_id, update_data):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Convert GraphQL input to service format with proper type conversion
            update_dict = {}
            decimal_fields = ['value', 'minimum_purchase_amount', 'customer_buys_value', 'bxgy_value']

            for field, value in update_data.items():
                if value is not None:
                    if field in decimal_fields:
                        update_dict[field] = float(value)
                    else:
                        update_dict[field] = value

            # Call service layer with workspace object
            result = discount_service.update_discount(
                workspace=workspace,
                discount_id=discount_id,
                update_data=update_dict,
                user=user
            )

            return UpdateDiscount(
                success=result['success'],
                discount=result.get('discount'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Discount update mutation failed: {str(e)}", exc_info=True)

            return UpdateDiscount(
                success=False,
                error=f"Discount update failed: {str(e)}"
            )


class DeleteDiscount(graphene.Mutation):
    """Delete discount with service layer orchestration"""

    class Arguments:
        discount_id = graphene.String(required=True)

    # PROPER TYPED RESPONSE - NOT JSONString
    success = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, discount_id):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Call service layer with workspace object
            result = discount_service.delete_discount(
                workspace=workspace,
                discount_id=discount_id,
                user=user
            )

            return DeleteDiscount(
                success=result['success'],
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Discount deletion mutation failed: {str(e)}", exc_info=True)

            return DeleteDiscount(
                success=False,
                error=f"Discount deletion failed: {str(e)}"
            )


class DiscountMutations(graphene.ObjectType):
    """All discount mutations"""
    create_discount = CreateDiscount.Field()
    update_discount = UpdateDiscount.Field()
    delete_discount = DeleteDiscount.Field()
