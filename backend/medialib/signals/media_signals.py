"""
Media Cleanup Signals (NEW FK-based System)
============================================

Industry-standard Django signals for automatic media file cleanup.

Handles:
1. Deletion - Clean up orphaned media when entities deleted
2. File cleanup - Delete physical files when MediaUpload records deleted

Why signals?
- Automatic - No manual cleanup calls needed
- Reliable - Works with bulk deletes, cascade deletes, admin actions
- Production-ready - Industry standard approach (Django doesn't auto-delete files)

NEW FK-based Architecture:
- Entities (Product, Category) have featured_media_id FK to MediaUpload
- Media can be reused by multiple entities
- Only delete MediaUpload when NO entities reference it (orphan check)
- Physical files deleted when MediaUpload record is hard-deleted

How to Add New Entity Types:
1. Add featured_media_id FK field to your model
2. Create cleanup signal similar to cleanup_orphaned_product_media
3. Update is_media_still_referenced() to check your new FK
"""

from django.db.models.signals import post_delete
from django.dispatch import receiver
from workspace.store.models import Product, Category, ProductVariant
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# NEW MEDIA SYSTEM CLEANUP SIGNALS (FK-based)
# ============================================================================

@receiver(post_delete, sender=Product)
def cleanup_orphaned_product_media(sender, instance, **kwargs):
    """
    Clean up orphaned media when a product is deleted (NEW FK system)

    Checks:
    - product.featured_media
    - product.media_gallery (via ProductMediaGallery junction table)

    Only deletes MediaUpload if NOT referenced by any other entity
    """
    try:
        from medialib.models.media_upload_model import MediaUpload
        from workspace.store.models import ProductMediaGallery, ProductVariant
        from django.utils import timezone

        media_to_check = set()

        # Collect featured_media
        if instance.featured_media_id:
            media_to_check.add(instance.featured_media_id)

        # Collect gallery media
        gallery_media_ids = ProductMediaGallery.objects.filter(
            product_id=instance.id
        ).values_list('media_id', flat=True)
        media_to_check.update(gallery_media_ids)

        # Check each media if it's orphaned
        for media_id in media_to_check:
            if not is_media_still_referenced(media_id):
                MediaUpload.objects.filter(id=media_id).update(deleted_at=timezone.now())
                logger.info(f"Marked orphaned media {media_id} for cleanup after product {instance.id} deletion")

    except Exception as e:
        logger.error(f"Product media cleanup failed for {instance.id}: {str(e)}", exc_info=True)


@receiver(post_delete, sender=Category)
def cleanup_orphaned_category_media(sender, instance, **kwargs):
    """
    Clean up orphaned media when a category is deleted (NEW FK system)

    Checks:
    - category.featured_media

    Only deletes MediaUpload if NOT referenced by any other entity
    """
    try:
        from medialib.models.media_upload_model import MediaUpload
        from django.utils import timezone

        if instance.featured_media_id:
            if not is_media_still_referenced(instance.featured_media_id):
                MediaUpload.objects.filter(id=instance.featured_media_id).update(deleted_at=timezone.now())
                logger.info(f"Marked orphaned media {instance.featured_media_id} for cleanup after category {instance.id} deletion")

    except Exception as e:
        logger.error(f"Category media cleanup failed for {instance.id}: {str(e)}", exc_info=True)


@receiver(post_delete, sender=ProductVariant)
def cleanup_orphaned_variant_media(sender, instance, **kwargs):
    """
    Clean up orphaned media when a variant is deleted (NEW FK system)

    Checks:
    - variant.featured_media

    Only deletes MediaUpload if NOT referenced by any other entity
    """
    try:
        from medialib.models.media_upload_model import MediaUpload
        from django.utils import timezone

        if instance.featured_media_id:
            if not is_media_still_referenced(instance.featured_media_id):
                MediaUpload.objects.filter(id=instance.featured_media_id).update(deleted_at=timezone.now())
                logger.info(f"Marked orphaned media {instance.featured_media_id} for cleanup after variant {instance.id} deletion")

    except Exception as e:
        logger.error(f"Variant media cleanup failed for {instance.id}: {str(e)}", exc_info=True)


def is_media_still_referenced(media_id: str) -> bool:
    """
    Check if MediaUpload is still referenced by any entity via FK relationships

    Checks all FK references:
    - Product.featured_media
    - Category.featured_media
    - ProductVariant.featured_media
    - ProductMediaGallery.media (M2M)

    Returns:
        True if media is still referenced, False if orphaned
    """
    from workspace.store.models import ProductVariant, ProductMediaGallery

    # Check Product.featured_media
    if Product.objects.filter(featured_media_id=media_id).exists():
        return True

    # Check Category.featured_media
    if Category.objects.filter(featured_media_id=media_id).exists():
        return True

    # Check ProductVariant.featured_media
    if ProductVariant.objects.filter(featured_media_id=media_id).exists():
        return True

    # Check ProductMediaGallery (M2M)
    if ProductMediaGallery.objects.filter(media_id=media_id).exists():
        return True

    return False  # Not referenced anywhere - orphaned


# ============================================================================
# UPDATE SIGNALS - Clean up when media is replaced or marked as deleted
# ============================================================================

@receiver(post_delete, sender='medialib.MediaUpload')
def cleanup_deleted_media_files(sender, instance, **kwargs):
    """
    Clean up physical files when MediaUpload record is deleted

    Triggered when:
    - Admin deletes specific image from product gallery
    - MediaUpload record is hard-deleted (not soft-delete)
    - Orphaned MediaUpload records are cleaned up

    Args:
        sender: MediaUpload model class
        instance: MediaUpload instance being deleted
        kwargs: Additional signal arguments
    """
    try:
        upload_id = str(instance.id)

        logger.info(f"Signal triggered: Cleaning up files for deleted MediaUpload {upload_id}")

        # Delete all file variations (original, optimized, thumbnails, tiny)
        from medialib.services.storage_service import storage_service

        files_to_delete = [
            instance.file_path,           # Original
            instance.optimized_path,      # Optimized
            instance.thumbnail_path,      # Thumbnail
        ]

        # Tiny thumbnail from metadata
        if instance.metadata and 'tiny_thumbnail_path' in instance.metadata:
            files_to_delete.append(instance.metadata['tiny_thumbnail_path'])

        deleted_count = 0
        for file_path in files_to_delete:
            if file_path:
                success = storage_service.delete_file(file_path)
                if success:
                    deleted_count += 1

        logger.info(f"Deleted {deleted_count} file variations for MediaUpload {upload_id}")

    except Exception as e:
        # Don't block deletion if file cleanup fails
        logger.error(
            f"Exception during MediaUpload file cleanup for {instance.id}: {str(e)}",
            exc_info=True
        )


# ============================================================================
# HELPER: Verify signals are registered
# ============================================================================

def verify_signals_connected():
    """
    Verify that all signals are properly connected

    Call this from Django management command or tests to verify setup:
        from medialib.signals.media_signals import verify_signals_connected
        verify_signals_connected()
    """
    from django.db.models.signals import post_delete
    from medialib.models.media_upload_model import MediaUpload

    signals_to_check = [
        (post_delete, Product, cleanup_orphaned_product_media),
        (post_delete, Category, cleanup_orphaned_category_media),
        (post_delete, ProductVariant, cleanup_orphaned_variant_media),
        (post_delete, MediaUpload, cleanup_deleted_media_files),
    ]

    print("\n=== Media Cleanup Signals Status (NEW FK System) ===")
    for signal, model, handler in signals_to_check:
        receivers = signal._live_receivers(model)
        connected = any(r() == handler for r in receivers)
        status = "✓ Connected" if connected else "✗ NOT Connected"
        print(f"{status}: {handler.__name__} for {model.__name__}")
    print("====================================================\n")

    return all(
        any(r() == handler for r in signal._live_receivers(model))
        for signal, model, handler in signals_to_check
    )
