"""
CSV and Document Import Tasks

Background tasks for file-based product imports:
- CSV/Excel imports
- PDF/Image document imports
- Product import processing

Separate from core bulk operations for better organization.
"""

import logging
import asyncio
from celery import shared_task
from django.db import transaction
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def bulk_import_products_task(self, workspace_id, user_id, file_content, filename, create_missing_categories=True):
    """
    Background task for bulk product imports (Shopify-style)

    Handles CSV, Excel, PDF, and Image uploads
    Runs in separate worker process - can take hours without timeout
    Updates progress in cache for real-time tracking

    Performance: Non-blocking, chunked processing (100 products/batch)
    Scalability: Handles 10,000+ products via background worker
    Reliability: Retries on failure (max 3 times), atomic transactions
    Security: Workspace scoping, file validation

    Args:
        workspace_id: Workspace ID
        user_id: User performing import
        file_content: Raw file bytes
        filename: Original filename with extension
        create_missing_categories: Auto-create categories if not found

    Returns:
        dict: Import result with job_id, success counts, errors
    """
    from workspace.core.models import Workspace
    from django.contrib.auth import get_user_model
    from workspace.store.services.product_import_service import ProductImportService

    User = get_user_model()

    try:
        # Get workspace and user
        workspace = Workspace.objects.get(id=workspace_id)
        user = User.objects.get(id=user_id)

        # Initialize import service
        service = ProductImportService(workspace=workspace, user=user)

        # Update task state to STARTED
        self.update_state(
            state='STARTED',
            meta={
                'stage': 'initializing',
                'message': 'Starting product import...'
            }
        )

        # Detect file type (CSV vs Document)
        filename_lower = filename.lower()
        is_csv = filename_lower.endswith(('.csv', '.xlsx', '.xls'))

        # Run appropriate import method
        if is_csv:
            logger.info(f"Starting CSV import for workspace {workspace_id}, file: {filename}")
            result = service.import_from_csv(
                file_content=file_content,
                filename=filename,
                create_missing_categories=create_missing_categories
            )
        else:
            logger.info(f"Starting document import for workspace {workspace_id}, file: {filename}")
            result = asyncio.run(
                service.import_from_document_async(
                    file_content=file_content,
                    filename=filename,
                    create_missing_categories=create_missing_categories
                )
            )

        # Update final task state
        self.update_state(
            state='SUCCESS',
            meta={
                'job_id': result.job_id,
                'successful_imports': result.successful_imports,
                'failed_imports': result.failed_imports,
                'total_items': result.total_items,
                'processing_time': result.processing_time,
                'bulk_operation_id': result.bulk_operation_id,
                'created_product_ids': result.created_products or [],
                'errors': result.errors[:10],
                'warnings': result.warnings[:10]
            }
        )

        logger.info(
            f"Import completed for workspace {workspace_id}: "
            f"{result.successful_imports}/{result.total_items} products imported"
        )

        return {
            'status': 'completed',
            'success': result.success,
            'job_id': result.job_id,
            'successful_imports': result.successful_imports,
            'failed_imports': result.failed_imports,
            'total_items': result.total_items,
            'processing_time': result.processing_time,
            'bulk_operation_id': result.bulk_operation_id,
            'created_product_ids': result.created_products or [],
            'errors': result.errors[:10],
            'warnings': result.warnings[:10]
        }

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found")
        self.update_state(
            state='FAILURE',
            meta={'error': 'Workspace not found'}
        )
        return {'status': 'failed', 'error': 'Workspace not found'}

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        self.update_state(
            state='FAILURE',
            meta={'error': 'User not found'}
        )
        return {'status': 'failed', 'error': 'User not found'}

    except Exception as e:
        logger.error(f"Product import failed for workspace {workspace_id}: {str(e)}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        # Retry on failure
        raise self.retry(exc=e, countdown=60)