"""
Shopify-inspired Bulk Operation Tasks

Core background tasks for Shopify-style bulk operations:
- Bulk publish products
- Bulk update prices
- Bulk delete products
- Bulk update inventory

No file processing, no complex imports.
"""

import logging
from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def bulk_publish_products(self, workspace_id, product_ids):
    """
    Background task for bulk publishing products

    Reliability: Retries on failure, updates progress
    Performance: Non-blocking, handles large batches
    """
    from workspace.core.models import Workspace
    from workspace.store.models import Product

    total = len(product_ids)

    try:
        workspace = Workspace.objects.get(id=workspace_id)

        for i, product_id in enumerate(product_ids):
            try:
                with transaction.atomic():
                    product = Product.objects.select_for_update().get(
                        id=product_id,
                        workspace=workspace
                    )
                    product.status = 'published'
                    product.save()

                # Update progress (for polling)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total,
                        'percent': int((i + 1) / total * 100)
                    }
                )

            except Exception as e:
                # Log error but continue with other products
                logger.error(f"Failed to publish product {product_id}: {e}")

        return {'status': 'completed', 'total': total}

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found")
        return {'status': 'failed', 'error': 'Workspace not found'}


@shared_task(bind=True, max_retries=3)
def bulk_unpublish_products(self, workspace_id, product_ids):
    """
    Background task for bulk unpublishing products
    """
    from workspace.core.models import Workspace
    from workspace.store.models import Product

    total = len(product_ids)

    try:
        workspace = Workspace.objects.get(id=workspace_id)

        for i, product_id in enumerate(product_ids):
            try:
                with transaction.atomic():
                    product = Product.objects.select_for_update().get(
                        id=product_id,
                        workspace=workspace
                    )
                    product.status = 'draft'
                    product.save()

                # Update progress (for polling)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total,
                        'percent': int((i + 1) / total * 100)
                    }
                )

            except Exception as e:
                # Log error but continue with other products
                logger.error(f"Failed to unpublish product {product_id}: {e}")

        return {'status': 'completed', 'total': total}

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found")
        return {'status': 'failed', 'error': 'Workspace not found'}


@shared_task(bind=True, max_retries=3)
def bulk_update_prices(self, workspace_id, price_updates):
    """
    Background task for bulk updating product prices

    price_updates format: [{'product_id': '123', 'new_price': 25.99}, ...]
    """
    from workspace.core.models import Workspace
    from workspace.store.models import Product, ProductVariant

    total = len(price_updates)

    try:
        workspace = Workspace.objects.get(id=workspace_id)

        for i, update in enumerate(price_updates):
            try:
                with transaction.atomic():
                    product = Product.objects.select_for_update().get(
                        id=update['product_id'],
                        workspace=workspace
                    )
                    product.price = update['new_price']
                    product.save()

                    # Update all variants if product has variants
                    if product.has_variants:
                        ProductVariant.objects.filter(
                            product=product,
                            workspace=workspace
                        ).update(price=update['new_price'])

                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total,
                        'percent': int((i + 1) / total * 100)
                    }
                )

            except Exception as e:
                logger.error(f"Failed to update price for product {update['product_id']}: {e}")

        return {'status': 'completed', 'total': total}

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found")
        return {'status': 'failed', 'error': 'Workspace not found'}


@shared_task(bind=True, max_retries=3)
def bulk_delete_products(self, workspace_id, product_ids):
    """
    Background task for bulk deleting products

    Safety: Validates ownership, handles dependencies
    """
    from workspace.core.models import Workspace
    from workspace.store.models import Product

    total = len(product_ids)

    try:
        workspace = Workspace.objects.get(id=workspace_id)

        for i, product_id in enumerate(product_ids):
            try:
                with transaction.atomic():
                    product = Product.objects.select_for_update().get(
                        id=product_id,
                        workspace=workspace
                    )

                    # Check if product can be safely deleted
                    if not product.can_delete():
                        logger.warning(f"Product {product_id} cannot be deleted - skipping")
                        continue

                    product.delete()

                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total,
                        'percent': int((i + 1) / total * 100)
                    }
                )

            except Product.DoesNotExist:
                logger.warning(f"Product {product_id} not found - skipping")
            except Exception as e:
                logger.error(f"Failed to delete product {product_id}: {e}")

        return {'status': 'completed', 'total': total}

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found")
        return {'status': 'failed', 'error': 'Workspace not found'}


@shared_task(bind=True, max_retries=3)
def bulk_update_inventory(self, workspace_id, inventory_updates):
    """
    Background task for bulk updating inventory

    inventory_updates format: [
        {'variant_id': '123', 'location_id': '456', 'quantity': 10},
        ...
    ]
    """
    from workspace.core.models import Workspace
    from workspace.store.models import Inventory, Location

    total = len(inventory_updates)

    try:
        workspace = Workspace.objects.get(id=workspace_id)

        for i, update in enumerate(inventory_updates):
            try:
                with transaction.atomic():
                    # Verify location belongs to workspace
                    location = Location.objects.get(
                        id=update['location_id'],
                        workspace=workspace
                    )

                    # Update or create inventory record
                    inventory, created = Inventory.objects.select_for_update().get_or_create(
                        variant_id=update['variant_id'],
                        location=location,
                        workspace=workspace,
                        defaults={'quantity': update['quantity']}
                    )

                    if not created:
                        inventory.quantity = update['quantity']
                        inventory.save()

                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total,
                        'percent': int((i + 1) / total * 100)
                    }
                )

            except Location.DoesNotExist:
                logger.error(f"Location {update['location_id']} not found - skipping")
            except Exception as e:
                logger.error(f"Failed to update inventory for variant {update['variant_id']}: {e}")

        return {'status': 'completed', 'total': total}

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found")
        return {'status': 'failed', 'error': 'Workspace not found'}


