# Variant Service - Production Grade
# Business logic for variant operations following industry standards

from typing import Dict, Any, List, Optional
from django.db import transaction, models
from django.core.exceptions import PermissionDenied
from workspace.store.models.variant_model import ProductVariant
from workspace.store.utils.workspace_permissions import assert_permission
import logging

logger = logging.getLogger('workspace.store.variants')


class VariantService:
    """
    Service class for variant business logic
    Handles variant operations with proper validation and error handling
    """

    def __init__(self):
        self.max_batch_size = 500

    def create_variant(self, workspace, variant_data: Dict[str, Any],
                      user=None) -> Dict[str, Any]:
        """
        Create variant with validation and atomic transaction

        Args:
            workspace: Workspace object
            variant_data: Variant creation data
            user: Optional user performing operation

        Returns:
            Dict with success, variant data, and message
        """
        try:
            with transaction.atomic():
                workspace_id = str(workspace.id)

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'product:create')

                # Validate variant data
                validation_result = self._validate_variant_data(variant_data)
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'error': validation_result['error']
                    }

                # Check for duplicate SKU
                if ProductVariant.objects.filter(
                    sku=variant_data['sku'],
                    workspace_id=workspace_id
                ).exists():
                    return {
                        'success': False,
                        'error': 'Variant with this SKU already exists'
                    }

                # Check for duplicate options (all 3 options)
                if self._variant_options_exist(
                    workspace_id,
                    variant_data['product_id'],
                    variant_data.get('option1', ''),
                    variant_data.get('option2', ''),
                    variant_data.get('option3', '')
                ):
                    return {
                        'success': False,
                        'error': 'Variant with these options already exists for this product'
                    }

                # Create variant
                variant = ProductVariant.objects.create(
                    workspace_id=workspace_id,
                    product_id=variant_data['product_id'],
                    sku=variant_data['sku'],
                    option1=variant_data.get('option1', ''),
                    option2=variant_data.get('option2', ''),
                    option3=variant_data.get('option3', ''),
                    price=variant_data.get('price'),
                    track_inventory=variant_data.get('track_inventory', True),
                    is_active=variant_data.get('is_active', True),
                    position=variant_data.get('position', 0)
                )

                return {
                    'success': True,
                    'variant': variant,
                    'message': f'Variant {variant.sku} created successfully'
                }

        except Exception as e:
            logger.error(f"Variant creation failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Variant creation failed: {str(e)}'
            }

    def update_variant(self, workspace, variant_id: str,
                      update_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """Update variant with validation, inventory updates, and atomic transaction"""
        try:
            with transaction.atomic():
                workspace_id = str(workspace.id)

                # Get variant with workspace scoping
                variant = ProductVariant.objects.select_for_update().get(
                    id=variant_id,
                    workspace_id=workspace_id
                )

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'product:update')

                # Extract inventory_updates if provided (handle separately)
                inventory_updates = update_data.pop('inventory_updates', None)

                # Handle featured_media_id (convert to FK assignment)
                if 'featured_media_id' in update_data:
                    featured_media_id = update_data.pop('featured_media_id')
                    variant.featured_media_id = featured_media_id if featured_media_id else None

                # Update variant fields
                for field, value in update_data.items():
                    if hasattr(variant, field) and value is not None:
                        setattr(variant, field, value)

                variant.save()

                # Update inventory if provided (Shopify-style: separate inventory management)
                if inventory_updates:
                    from workspace.store.services.inventory_management_service import inventory_management_service

                    for inv_update in inventory_updates:
                        inventory_management_service.update_inventory(
                            workspace=workspace_id,
                            variant_id=variant_id,
                            location_id=inv_update.get('location_id'),
                            onhand=inv_update.get('onhand'),
                            available=inv_update.get('available'),
                            condition=inv_update.get('condition'),
                            user=user
                        )

                return {
                    'success': True,
                    'variant': variant,
                    'message': f'Variant {variant.sku} updated successfully'
                }

        except ProductVariant.DoesNotExist:
            logger.warning(f"Variant {variant_id} not found")
            return {
                'success': False,
                'error': 'Variant not found'
            }
        except Exception as e:
            logger.error(f"Variant update failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Variant update failed: {str(e)}'
            }

    def get_variants_by_product(self, workspace_id: str, product_id: str,
                               only_active=True) -> List[ProductVariant]:
        """Get all variants for a product with optimization"""
        queryset = ProductVariant.objects.filter(
            workspace_id=workspace_id,
            product_id=product_id
        )

        if only_active:
            queryset = queryset.filter(is_active=True)

        return queryset.select_related('product').order_by('position', 'id')

    def bulk_create_variants(self, workspace, product_id: str,
                            variants_data: List[Dict[str, Any]], user=None) -> Dict[str, Any]:
        """Bulk create variants from option matrix"""
        try:
            with transaction.atomic():
                workspace_id = str(workspace.id)

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'product:create')

                created_variants = []

                for i, variant_data in enumerate(variants_data):
                    # Validate each variant
                    validation_result = self._validate_variant_data(variant_data)
                    if not validation_result['valid']:
                        return {
                            'success': False,
                            'error': f'Variant {i+1}: {validation_result["error"]}'
                        }

                    # Check SKU uniqueness
                    if ProductVariant.objects.filter(
                        sku=variant_data['sku'],
                        workspace_id=workspace_id
                    ).exists():
                        return {
                            'success': False,
                            'error': f'Variant {i+1}: SKU already exists'
                        }

                    variant = ProductVariant(
                        workspace_id=workspace_id,
                        product_id=product_id,
                        sku=variant_data['sku'],
                        option1=variant_data.get('option1', ''),
                        option2=variant_data.get('option2', ''),
                        option3=variant_data.get('option3', ''),
                        price=variant_data.get('price'),
                        track_inventory=variant_data.get('track_inventory', True),
                        is_active=variant_data.get('is_active', True),
                        position=i
                    )

                    variant.save()
                    created_variants.append(variant)

                return {
                    'success': True,
                    'variants': created_variants,
                    'message': f'Created {len(created_variants)} variants successfully'
                }

        except Exception as e:
            logger.error(f"Bulk variant creation failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Bulk variant creation failed: {str(e)}'
            }


    def _validate_variant_data(self, variant_data: Dict) -> Dict[str, Any]:
        """Validate variant data before creation"""
        required_fields = ['product_id', 'sku']
        missing_fields = [field for field in required_fields if field not in variant_data]

        if missing_fields:
            return {
                'valid': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }

        # Validate SKU format
        sku = variant_data['sku']
        if len(sku) > 100:
            return {
                'valid': False,
                'error': 'SKU must be 100 characters or less'
            }

        return {'valid': True}

    def _variant_options_exist(self, workspace_id: str, product_id: str,
                              option1: str, option2: str, option3: str = '') -> bool:
        """Check if variant with same options already exists (checks all 3 options)"""
        return ProductVariant.objects.filter(
            workspace_id=workspace_id,
            product_id=product_id,
            option1=option1,
            option2=option2,
            option3=option3
        ).exists()


# Global instance for easy access
variant_service = VariantService()