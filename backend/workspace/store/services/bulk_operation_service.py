"""
Shopify-inspired Bulk Operation Service

Core bulk operations only:
- Bulk publish/unpublish products
- Bulk update prices
- Bulk update inventory
- Bulk delete products

No file processing, no complex history tracking.
"""

from typing import Dict, Any, List, Optional
from django.db import transaction
from django.core.exceptions import PermissionDenied
from workspace.store.models import Product, ProductVariant
from workspace.store.models.bulk_operation import BulkOperation
from workspace.store.utils.workspace_permissions import assert_permission


class BulkOperationService:
    """Shopify-style bulk operation service"""

    def __init__(self):
        self.max_batch_size = 1000

    def bulk_publish_products(self, workspace, product_ids: List[str],
                            user=None) -> Dict[str, Any]:
        """
        Bulk publish products (Shopify: bulk publish)
        """
        try:
            with transaction.atomic():
                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions for bulk publish")

                # Validate products exist and belong to workspace
                valid_products = Product.objects.filter(
                    id__in=product_ids,
                    workspace=workspace
                )

                if valid_products.count() != len(product_ids):
                    return {
                        'success': False,
                        'error': 'Some products not found or access denied'
                    }

                # Bulk update
                updated_count = valid_products.update(status='published')

                # Create operation record
                operation = BulkOperation.objects.create(
                    workspace=workspace,
                    user=user,
                    operation_type='bulk_publish',
                    status='success',
                    total_items=len(product_ids),
                    processed_items=updated_count
                )

                return {
                    'success': True,
                    'operation_id': str(operation.id),
                    'processed_count': updated_count,
                    'message': f'Successfully published {updated_count} products'
                }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Bulk publish failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Bulk publish failed: {str(e)}'
            }

    def bulk_unpublish_products(self, workspace, product_ids: List[str],
                              user=None) -> Dict[str, Any]:
        """
        Bulk unpublish products (Shopify: bulk unpublish)
        """
        try:
            with transaction.atomic():
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions for bulk unpublish")

                valid_products = Product.objects.filter(
                    id__in=product_ids,
                    workspace=workspace
                )

                if valid_products.count() != len(product_ids):
                    return {
                        'success': False,
                        'error': 'Some products not found or access denied'
                    }

                updated_count = valid_products.update(status='draft')

                operation = BulkOperation.objects.create(
                    workspace=workspace,
                    user=user,
                    operation_type='bulk_unpublish',
                    status='success',
                    total_items=len(product_ids),
                    processed_items=updated_count
                )

                return {
                    'success': True,
                    'operation_id': str(operation.id),
                    'processed_count': updated_count,
                    'message': f'Successfully unpublished {updated_count} products'
                }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Bulk unpublish failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Bulk unpublish failed: {str(e)}'
            }

    def bulk_update_prices(self, workspace, price_updates: List[Dict],
                         user=None) -> Dict[str, Any]:
        """
        Bulk update product prices (Shopify: bulk price updates)

        price_updates format: [{'product_id': 'uuid', 'new_price': 99.99}]
        """
        try:
            with transaction.atomic():
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions")

                product_ids = [update['product_id'] for update in price_updates]

                # Validate products
                valid_products = Product.objects.filter(
                    id__in=product_ids,
                    workspace=workspace
                )

                if valid_products.count() != len(product_ids):
                    return {
                        'success': False,
                        'error': 'Some products not found or access denied'
                    }

                # Validate prices
                for update in price_updates:
                    if update['new_price'] < 0:
                        return {
                            'success': False,
                            'error': 'Price cannot be negative'
                        }

                # Bulk update prices
                updated_count = 0
                for product in valid_products:
                    update_data = next(
                        (u for u in price_updates if u['product_id'] == str(product.id)),
                        None
                    )
                    if update_data:
                        product.price = update_data['new_price']
                        product.save()
                        updated_count += 1

                operation = BulkOperation.objects.create(
                    workspace=workspace,
                    user=user,
                    operation_type='bulk_price_update',
                    status='success',
                    total_items=len(price_updates),
                    processed_items=updated_count
                )

                return {
                    'success': True,
                    'operation_id': str(operation.id),
                    'processed_count': updated_count,
                    'message': f'Successfully updated prices for {updated_count} products'
                }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Bulk price update failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Bulk price update failed: {str(e)}'
            }

    def bulk_delete_products(self, workspace, product_ids: List[str],
                           user=None) -> Dict[str, Any]:
        """
        Bulk delete products (Shopify: bulk delete)
        """
        try:
            with transaction.atomic():
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions")

                valid_products = Product.objects.filter(
                    id__in=product_ids,
                    workspace=workspace
                )

                if valid_products.count() != len(product_ids):
                    return {
                        'success': False,
                        'error': 'Some products not found or access denied'
                    }

                # Get count before deletion for operation record
                delete_count = valid_products.count()

                # Bulk delete
                deleted_count, _ = valid_products.delete()

                operation = BulkOperation.objects.create(
                    workspace=workspace,
                    user=user,
                    operation_type='bulk_delete',
                    status='success',
                    total_items=len(product_ids),
                    processed_items=deleted_count
                )

                return {
                    'success': True,
                    'operation_id': str(operation.id),
                    'processed_count': deleted_count,
                    'message': f'Successfully deleted {deleted_count} products'
                }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Bulk delete failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Bulk delete failed: {str(e)}'
            }

    def bulk_update_inventory(self, workspace, inventory_updates: List[Dict],
                            user=None) -> Dict[str, Any]:
        """
        Bulk update inventory (Shopify: bulk inventory updates)

        inventory_updates format: [
            {'variant_id': 'uuid', 'location_id': 'uuid', 'quantity': 10}
        ]
        """
        try:
            with transaction.atomic():
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions")

                variant_ids = [update['variant_id'] for update in inventory_updates]

                # Validate variants
                valid_variants = ProductVariant.objects.filter(
                    id__in=variant_ids,
                    product__workspace=workspace
                )

                if valid_variants.count() != len(variant_ids):
                    return {
                        'success': False,
                        'error': 'Some variants not found or access denied'
                    }

                # Validate quantities
                for update in inventory_updates:
                    if update['quantity'] < 0:
                        return {
                            'success': False,
                            'error': 'Quantity cannot be negative'
                        }

                # Bulk update inventory
                updated_count = 0
                for variant in valid_variants:
                    update_data = next(
                        (u for u in inventory_updates if u['variant_id'] == str(variant.id)),
                        None
                    )
                    if update_data:
                        # Update inventory logic here (simplified)
                        variant.quantity = update_data['quantity']
                        variant.save()
                        updated_count += 1

                operation = BulkOperation.objects.create(
                    workspace=workspace,
                    user=user,
                    operation_type='bulk_inventory_update',
                    status='success',
                    total_items=len(inventory_updates),
                    processed_items=updated_count
                )

                return {
                    'success': True,
                    'operation_id': str(operation.id),
                    'processed_count': updated_count,
                    'message': f'Successfully updated inventory for {updated_count} variants'
                }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Bulk inventory update failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Bulk inventory update failed: {str(e)}'
            }

# Global instance for easy access
bulk_operation_service = BulkOperationService()