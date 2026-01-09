"""
Shopify-Style Inventory Service

Simple, focused inventory service following Shopify's design principles
- Simple stock adjustments
- No cost tracking
- No complex transfer logic
- Fast and reliable operations
"""

from typing import Dict, Any, List
from django.db import transaction
from django.core.exceptions import PermissionDenied
import logging
from ..models import Inventory, ProductVariant, Location
from workspace.store.utils.workspace_permissions import assert_permission

logger = logging.getLogger('workspace.store.inventory')


class InventoryManagementService:
    """
    Shopify-style inventory service

    Design Principles:
    - Simple: Only essential operations
    - Fast: Minimal overhead
    - Reliable: Atomic operations
    - Shopify-compatible: Similar API patterns
    """

    def update_inventory(self, workspace, variant_id: str, location_id: str,
                        onhand: int = None, available: int = None,
                        condition: str = None, user=None) -> Dict[str, Any]:
        """
        Update inventory fields (onhand, available, condition)
        All fields are optional - only update what's provided
        """
        try:
            with transaction.atomic():
                # Get or create inventory record
                inventory, created = Inventory.objects.get_or_create(
                    variant_id=variant_id,
                    location_id=location_id,
                    workspace=workspace,
                    defaults={'quantity': 0}
                )

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions for inventory update")

                # Update only provided fields
                updated_fields = []

                if onhand is not None:
                    inventory.onhand = onhand
                    updated_fields.append('onhand')

                if available is not None:
                    inventory.available = available
                    updated_fields.append('available')

                if condition is not None:
                    inventory.condition = condition
                    updated_fields.append('condition')

                if updated_fields:
                    inventory.save(update_fields=updated_fields + ['updated_at'])

                    return {
                        'success': True,
                        'inventory': inventory,
                        'message': f"Updated {', '.join(updated_fields)}"
                    }
                else:
                    return {
                        'success': True,
                        'inventory': inventory,
                        'message': 'No fields to update'
                    }

        except Exception as e:
            logger.error(f"Inventory update failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Inventory update failed: {str(e)}'
            }

    def transfer_inventory(self, workspace, variant_id: str, from_location_id: str,
                          to_location_id: str, quantity: int, user=None) -> Dict[str, Any]:
        """
        Transfer inventory between locations
        """
        try:
            with transaction.atomic():
                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions for inventory transfer")

                # Get source inventory
                from_inventory = Inventory.objects.get(
                    variant_id=variant_id,
                    location_id=from_location_id,
                    workspace=workspace
                )

                # Check available stock
                available_qty = from_inventory.available or from_inventory.quantity
                if available_qty < quantity:
                    return {
                        'success': False,
                        'error': f'Insufficient stock. Available: {available_qty}, Requested: {quantity}'
                    }

                # Get or create destination inventory
                to_inventory, created = Inventory.objects.get_or_create(
                    variant_id=variant_id,
                    location_id=to_location_id,
                    workspace=workspace,
                    defaults={'quantity': 0, 'onhand': 0, 'available': 0}
                )

                # Transfer stock
                if from_inventory.onhand is not None:
                    from_inventory.onhand -= quantity
                if from_inventory.available is not None:
                    from_inventory.available -= quantity
                from_inventory.quantity -= quantity
                from_inventory.save()

                if to_inventory.onhand is not None:
                    to_inventory.onhand += quantity
                if to_inventory.available is not None:
                    to_inventory.available += quantity
                to_inventory.quantity += quantity
                to_inventory.save()

                return {
                    'success': True,
                    'from_inventory': from_inventory,
                    'to_inventory': to_inventory,
                    'message': f'Transferred {quantity} units'
                }

        except Inventory.DoesNotExist:
            return {
                'success': False,
                'error': 'Source inventory not found'
            }
        except Exception as e:
            logger.error(f"Inventory transfer failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Inventory transfer failed: {str(e)}'
            }

    def adjust_inventory(self, workspace, variant_id: str, location_id: str,
                        quantity: int, user=None) -> Dict[str, Any]:
        """
        Shopify-style: Adjust inventory quantity
        Positive quantity = increase, Negative quantity = decrease
        """
        try:
            with transaction.atomic():
                # Get inventory record
                inventory, created = Inventory.objects.get_or_create(
                    variant_id=variant_id,
                    location_id=location_id,
                    workspace=workspace,
                    defaults={'quantity': 0}
                )

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions for inventory adjustment")

                # Shopify-style: Simple adjustment
                success = inventory.adjust_stock(quantity)

                if success:
                    return {
                        'success': True,
                        'inventory': inventory,
                        'stock_status': inventory.stock_status,
                        'message': f'Stock adjusted by {quantity} units'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Insufficient stock for adjustment'
                    }

        except Inventory.DoesNotExist:
            logger.warning(f"Inventory not found for variant {variant_id} at location {location_id}")
            return {
                'success': False,
                'error': 'Inventory record not found'
            }
        except Exception as e:
            logger.error(f"Inventory adjustment failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Inventory adjustment failed: {str(e)}'
            }

    def set_inventory_quantity(self, workspace, variant_id: str, location_id: str,
                              new_quantity: int, user=None) -> Dict[str, Any]:
        """
        Shopify-style: Set specific inventory quantity
        """
        try:
            with transaction.atomic():
                # Get inventory record
                inventory, created = Inventory.objects.get_or_create(
                    variant_id=variant_id,
                    location_id=location_id,
                    workspace=workspace,
                    defaults={'quantity': 0}
                )

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'product:update')("Insufficient permissions for inventory update")

                # Shopify-style: Set specific quantity
                success = inventory.set_quantity(new_quantity)

                if success:
                    return {
                        'success': True,
                        'inventory': inventory,
                        'stock_status': inventory.stock_status,
                        'message': f'Stock set to {new_quantity} units'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to update stock quantity'
                    }

        except Inventory.DoesNotExist:
            logger.warning(f"Inventory not found for variant {variant_id} at location {location_id}")
            return {
                'success': False,
                'error': 'Inventory record not found'
            }
        except Exception as e:
            logger.error(f"Inventory set failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Inventory set failed: {str(e)}'
            }

    def get_inventory_summary(self, workspace, user=None) -> Dict[str, Any]:
        """
        Shopify-style: Simple inventory summary
        """
        try:
            # Validate permissions
            if user:
                assert_permission(workspace, user, 'product:view')

            # Simple summary (Shopify-style)
            total_items = Inventory.objects.filter(workspace=workspace).count()
            total_stock = sum(inv.quantity for inv in Inventory.objects.filter(workspace=workspace))

            low_stock_items = Inventory.objects.filter(
                workspace=workspace,
                quantity__gt=0,
                quantity__lte=5
            ).count()

            out_of_stock_items = Inventory.objects.filter(
                workspace=workspace,
                quantity=0
            ).count()

            return {
                'success': True,
                'summary': {
                    'total_items': total_items,
                    'total_stock': total_stock,
                    'low_stock_items': low_stock_items,
                    'out_of_stock_items': out_of_stock_items
                }
            }

        except Exception as e:
            logger.error(f"Inventory summary failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Inventory summary failed: {str(e)}'
            }

    def get_low_stock_items(self, workspace, user=None) -> Dict[str, Any]:
        """
        Shopify-style: Get low stock items using location-specific thresholds
        """
        try:
            # Validate permissions
            if user:
                assert_permission(workspace, user, 'product:view')

            # Get all inventory items that are not out of stock
            inventory_items = Inventory.objects.filter(
                workspace=workspace,
                quantity__gt=0
            ).select_related('variant', 'location')

            # Filter items that are below their location's threshold
            alerts = []
            for inventory in inventory_items:
                threshold = getattr(inventory.location, 'low_stock_threshold', 5)
                if inventory.quantity <= threshold:
                    alerts.append({
                        'variant_id': inventory.variant_id,
                        'variant_name': inventory.variant.name,
                        'location_id': inventory.location_id,
                        'location_name': inventory.location.name,
                        'current_quantity': inventory.quantity,
                        'stock_status': inventory.stock_status
                    })

            return {
                'success': True,
                'alerts': alerts,
                'total_alerts': len(alerts)
            }

        except Exception as e:
            logger.error(f"Low stock items failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Low stock items failed: {str(e)}'
            }


# Global instance for easy access
inventory_management_service = InventoryManagementService()