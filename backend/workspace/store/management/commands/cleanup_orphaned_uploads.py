"""
Management command to clean up orphaned upload records

This command identifies and soft-deletes MediaUpload records that are:
1. Not soft-deleted (deleted_at__isnull=True)
2. Have no active entity references (entity no longer exists or is inactive)
3. Are older than 7 days (grace period for recovery)

Usage:
    python manage.py cleanup_orphaned_uploads

Recommended to run daily via cron or Celery beat.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up orphaned MediaUpload records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--grace-period',
            type=int,
            default=7,
            help='Grace period in days (default: 7)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        grace_period_days = options['grace_period']

        self.stdout.write(f"Starting orphaned upload cleanup (dry-run: {dry_run}, grace period: {grace_period_days} days)")

        try:
            from workspace.store.models import MediaUpload, Product, Category

            # Calculate grace period cutoff
            grace_period = timezone.now() - timedelta(days=grace_period_days)

            # Find uploads that are candidates for cleanup
            candidate_uploads = MediaUpload.objects.filter(
                deleted_at__isnull=True,  # Not already soft-deleted
                uploaded_at__lt=grace_period,  # Older than grace period
                status='completed'  # Only completed uploads
            )

            orphaned_count = 0
            processed_count = 0

            with transaction.atomic():
                for upload in candidate_uploads:
                    processed_count += 1

                    # Check if the entity still exists and is active
                    is_entity_active = self._check_entity_active(upload)

                    if not is_entity_active:
                        orphaned_count += 1

                        if dry_run:
                            self.stdout.write(
                                f"[DRY RUN] Would delete orphaned upload: {upload.id} "
                                f"({upload.entity_type} {upload.entity_id}) - {upload.original_filename}"
                            )
                        else:
                            # Soft delete the orphaned upload
                            upload.deleted_at = timezone.now()
                            upload.save(update_fields=['deleted_at'])

                            self.stdout.write(
                                f"Deleted orphaned upload: {upload.id} "
                                f"({upload.entity_type} {upload.entity_id}) - {upload.original_filename}"
                            )
                            logger.info(f"Cleaned up orphaned upload {upload.id}")

            # Summary
            self.stdout.write(f"\nCleanup Summary:")
            self.stdout.write(f"- Processed: {processed_count} uploads")
            self.stdout.write(f"- Orphaned: {orphaned_count} uploads")

            if dry_run:
                self.stdout.write(self.style.WARNING(f"DRY RUN: Would have deleted {orphaned_count} orphaned uploads"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Successfully deleted {orphaned_count} orphaned uploads"))

        except Exception as e:
            logger.error(f"Orphaned upload cleanup failed: {str(e)}", exc_info=True)
            self.stderr.write(self.style.ERROR(f"Cleanup failed: {str(e)}"))

    def _check_entity_active(self, upload):
        """
        Check if the entity referenced by this upload still exists and is active

        Returns:
            True if entity exists and is active, False otherwise
        """
        try:
            if upload.entity_type == 'product':
                from workspace.store.models import Product
                return Product.objects.filter(
                    id=upload.entity_id,
                    is_active=True
                ).exists()

            elif upload.entity_type == 'category':
                from workspace.store.models import Category
                return Category.objects.filter(
                    id=upload.entity_id,
                    is_active=True
                ).exists()

            # Add more entity types as needed
            else:
                # For unknown entity types, assume active (conservative approach)
                return True

        except Exception as e:
            logger.warning(f"Entity check failed for {upload.entity_type} {upload.entity_id}: {str(e)}")
            return False