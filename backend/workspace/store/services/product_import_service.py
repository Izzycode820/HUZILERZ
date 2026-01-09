"""
Product Import Service - Centralized bulk product import logic
Following Shopify's approach for handling bulk product uploads

Architecture:
- Single source of truth for ALL product import business logic
- Uses parsers (CSV, Document) for data extraction only
- Handles validation, category resolution, product creation
- Async job processing with Celery for large uploads
- Progress tracking via cache
- Comprehensive error reporting

Performance: Async processing with chunked batches (100 products/batch)
Scalability: Celery distributed task queue, Redis caching
Reliability: Retry mechanisms, atomic transactions, detailed error tracking
Security: Workspace scoping, input validation, file size limits
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from django.db import transaction, IntegrityError
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from workspace.store.utils.workspace_permissions import assert_permission

logger = logging.getLogger(__name__)

User = get_user_model()


@dataclass
class ImportProgress:
    """Real-time import progress tracking"""
    job_id: str
    status: str  # PENDING, PROCESSING, VALIDATING, IMPORTING, COMPLETED, FAILED
    stage: str  # parsing, validation, import
    current_item: int
    total_items: int
    percent_complete: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, str]]
    warnings: List[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class ImportResult:
    """Final result of bulk import operation"""
    success: bool
    job_id: str
    total_items: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, str]]
    warnings: List[str]
    processing_time: float
    bulk_operation_id: Optional[str] = None
    created_products: List[str] = None  # List of product IDs

    def to_dict(self):
        result = asdict(self)
        if self.created_products is None:
            result['created_products'] = []
        return result


class ProductImportService:
    """
    Centralized service for bulk product imports

    Responsibilities:
    - Orchestrates import pipeline (parse → validate → import)
    - Business logic for product validation
    - Category resolution and creation
    - Product creation with proper relationships
    - Progress tracking and error reporting
    - Async job management
    """

    # Batch size for chunked processing
    BATCH_SIZE = 100

    # Cache timeout for progress tracking (1 hour)
    PROGRESS_CACHE_TIMEOUT = 3600

    def __init__(self, workspace, user):
        """
        Initialize import service

        Args:
            workspace: Workspace instance
            user: User performing the import
        """
        self.workspace = workspace
        self.user = user

    def import_from_csv(
        self,
        file_content: bytes,
        filename: str,
        create_missing_categories: bool = True
    ) -> ImportResult:
        """
        Import products from CSV file with Shopify-inspired approach

        Args:
            file_content: CSV file bytes
            filename: Original filename
            create_missing_categories: Auto-create categories if not found

        Returns:
            ImportResult with import details
        """
        # Validate admin permissions
        if self.user:
            assert_permission(self.workspace, self.user, 'product:create')

        import time
        start_time = time.time()

        # Import new CSV parser service
        from .csv_parser_service import csv_parser_service

        # Create CSV import job
        job = csv_parser_service.create_csv_import_job(
            workspace=self.workspace,
            filename=filename,
            file_size=len(file_content),
            user=self.user
        )

        # Generate job ID
        job_id = f"import_csv_{self.workspace.id}_{int(time.time())}"

        try:
            # Stage 1: Parse CSV file with new service
            self._update_progress_sync(job_id, 'PROCESSING', 'parsing', 0, 0, 0, 0, [], [])

            parse_result = csv_parser_service.parse_csv_content(
                workspace=self.workspace,
                file_content=file_content,
                filename=filename,
                job=job,
                user=self.user
            )

            if not parse_result['success'] or not parse_result['products']:
                processing_time = time.time() - start_time
                return ImportResult(
                    success=False,
                    job_id=job_id,
                    total_items=parse_result['total_rows'],
                    successful_imports=0,
                    failed_imports=parse_result['total_rows'],
                    errors=parse_result['parsing_errors'],
                    warnings=[],
                    processing_time=processing_time
                )

            # Stage 2: Validate and enrich products
            self._update_progress_sync(
                job_id, 'VALIDATING', 'validation',
                0, len(parse_result['products']), 0, 0, [], []
            )

            validated_products, validation_errors = self._validate_products_batch_sync(
                parse_result['products'], create_missing_categories
            )

            # Stage 3: Import products to database
            self._update_progress_sync(
                job_id, 'IMPORTING', 'import',
                0, len(validated_products), 0, 0, validation_errors, []
            )

            import_result = self._import_products_batch_sync(
                validated_products, job_id, validation_errors
            )

            # Update job status
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.success_count = import_result['successful']
            job.error_count = import_result['failed']
            job.save()

            processing_time = time.time() - start_time

            # Mark as completed
            self._update_progress_sync(
                job_id, 'COMPLETED', 'completed',
                len(validated_products), len(validated_products),
                import_result['successful'], import_result['failed'],
                import_result['errors'], []
            )

            return ImportResult(
                success=import_result['successful'] > 0,
                job_id=job_id,
                total_items=len(parse_result['products']),
                successful_imports=import_result['successful'],
                failed_imports=import_result['failed'],
                errors=import_result['errors'],
                warnings=[],
                processing_time=processing_time,
                created_products=import_result['created_product_ids']
            )

        except Exception as e:
            logger.error(f"CSV import failed for workspace {self.workspace.id}: {str(e)}", exc_info=True)
            processing_time = time.time() - start_time

            # Update job status to failed
            job.status = 'failed'
            job.save()

            self._update_progress_sync(
                job_id, 'FAILED', 'failed', 0, 0, 0, 0,
                [{"type": "error", "message": f"Import failed: {str(e)}"}], []
            )

            return ImportResult(
                success=False,
                job_id=job_id,
                total_items=0,
                successful_imports=0,
                failed_imports=0,
                errors=[{"type": "error", "message": f"Import failed: {str(e)}"}],
                warnings=[],
                processing_time=processing_time
            )

    async def import_from_csv_async(
        self,
        file_content: bytes,
        filename: str,
        create_missing_categories: bool = True
    ) -> ImportResult:
        """
        Import products from CSV file with async processing

        Args:
            file_content: CSV file bytes
            filename: Original filename
            create_missing_categories: Auto-create categories if not found

        Returns:
            ImportResult with import details
        """
        # Validate admin permissions
        if self.user:
            assert_permission(self.workspace, self.user, 'product:create')

        import time
        start_time = time.time()

        # Import parser
        from .csv_parser import ModernCSVParser

        # Generate job ID
        job_id = f"import_csv_{self.workspace.id}_{int(time.time())}"

        try:
            # Stage 1: Parse CSV file
            await self._update_progress(job_id, 'PROCESSING', 'parsing', 0, 0, 0, 0, [], [])

            parser = ModernCSVParser()
            parse_result = await parser.parse_csv_file_async(
                file_content, filename, str(self.workspace.id)
            )

            if not parse_result.success or not parse_result.products:
                processing_time = time.time() - start_time
                return ImportResult(
                    success=False,
                    job_id=job_id,
                    total_items=parse_result.total_rows,
                    successful_imports=0,
                    failed_imports=parse_result.total_rows,
                    errors=parse_result.errors,
                    warnings=parse_result.warnings,
                    processing_time=processing_time
                )

            # Stage 2: Validate and enrich products
            await self._update_progress(
                job_id, 'VALIDATING', 'validation',
                0, len(parse_result.products), 0, 0, [], parse_result.warnings
            )

            validated_products, validation_errors = await self._validate_products_batch(
                parse_result.products, create_missing_categories
            )

            # Stage 3: Import products to database
            await self._update_progress(
                job_id, 'IMPORTING', 'import',
                0, len(validated_products), 0, 0, validation_errors, parse_result.warnings
            )

            import_result = await self._import_products_batch(
                validated_products, job_id, validation_errors
            )

            # Stage 4: Create bulk operation record
            bulk_operation = await self._create_bulk_operation_record(
                filename=filename,
                source_type='csv',
                total_products=len(parse_result.products),
                imported_products=import_result['successful'],
                products_data=parse_result.products,
                status='success' if import_result['successful'] > 0 else 'failed',
                error_message='; '.join([e.get('message', '') for e in import_result['errors'][:5]])
            )

            processing_time = time.time() - start_time

            # Mark as completed
            await self._update_progress(
                job_id, 'COMPLETED', 'completed',
                len(validated_products), len(validated_products),
                import_result['successful'], import_result['failed'],
                import_result['errors'], parse_result.warnings
            )

            return ImportResult(
                success=import_result['successful'] > 0,
                job_id=job_id,
                total_items=len(parse_result.products),
                successful_imports=import_result['successful'],
                failed_imports=import_result['failed'],
                errors=import_result['errors'],
                warnings=parse_result.warnings,
                processing_time=processing_time,
                bulk_operation_id=str(bulk_operation.id) if bulk_operation else None,
                created_products=import_result['created_product_ids']
            )

        except Exception as e:
            logger.error(f"CSV import failed for workspace {self.workspace.id}: {str(e)}", exc_info=True)
            processing_time = time.time() - start_time

            await self._update_progress(
                job_id, 'FAILED', 'failed', 0, 0, 0, 0,
                [{"type": "error", "message": f"Import failed: {str(e)}"}], []
            )

            return ImportResult(
                success=False,
                job_id=job_id,
                total_items=0,
                successful_imports=0,
                failed_imports=0,
                errors=[{"type": "error", "message": f"Import failed: {str(e)}"}],
                warnings=[],
                processing_time=processing_time
            )

    async def import_from_document_async(
        self,
        file_content: bytes,
        filename: str,
        create_missing_categories: bool = True
    ) -> ImportResult:
        """
        Import products from document (PDF, Image, Excel) with async processing

        Args:
            file_content: Document file bytes
            filename: Original filename
            create_missing_categories: Auto-create categories if not found

        Returns:
            ImportResult with import details
        """
        # Validate admin permissions
        if self.user:
            assert_permission(self.workspace, self.user, 'product:create')

        import time
        start_time = time.time()

        # Import processor
        from .document_processor import DocumentProcessor

        # Generate job ID
        job_id = f"import_doc_{self.workspace.id}_{int(time.time())}"

        try:
            # Stage 1: Process document
            await self._update_progress(job_id, 'PROCESSING', 'parsing', 0, 0, 0, 0, [], [])

            processor = DocumentProcessor()
            doc_result = processor.process_document(file_content, filename)

            if not doc_result.products:
                processing_time = time.time() - start_time
                return ImportResult(
                    success=False,
                    job_id=job_id,
                    total_items=0,
                    successful_imports=0,
                    failed_imports=0,
                    errors=[{"type": "error", "message": "No products found in document"}],
                    warnings=[],
                    processing_time=processing_time
                )

            # Convert ExtractedProduct to dict format
            products_data = [self._extracted_product_to_dict(p) for p in doc_result.products]

            # Stage 2: Validate and enrich products
            await self._update_progress(
                job_id, 'VALIDATING', 'validation',
                0, len(products_data), 0, 0, [], []
            )

            validated_products, validation_errors = await self._validate_products_batch(
                products_data, create_missing_categories
            )

            # Stage 3: Import products to database
            await self._update_progress(
                job_id, 'IMPORTING', 'import',
                0, len(validated_products), 0, 0, validation_errors, []
            )

            import_result = await self._import_products_batch(
                validated_products, job_id, validation_errors
            )

            # Stage 4: Create bulk operation record
            source_type = self._get_source_type(filename)
            bulk_operation = await self._create_bulk_operation_record(
                filename=filename,
                source_type=source_type,
                total_products=len(products_data),
                imported_products=import_result['successful'],
                products_data=products_data,
                status='success' if import_result['successful'] > 0 else 'failed',
                error_message='; '.join([e.get('message', '') for e in import_result['errors'][:5]])
            )

            processing_time = time.time() - start_time

            # Mark as completed
            await self._update_progress(
                job_id, 'COMPLETED', 'completed',
                len(validated_products), len(validated_products),
                import_result['successful'], import_result['failed'],
                import_result['errors'], []
            )

            return ImportResult(
                success=import_result['successful'] > 0,
                job_id=job_id,
                total_items=len(products_data),
                successful_imports=import_result['successful'],
                failed_imports=import_result['failed'],
                errors=import_result['errors'],
                warnings=[],
                processing_time=processing_time,
                bulk_operation_id=str(bulk_operation.id) if bulk_operation else None,
                created_products=import_result['created_product_ids']
            )

        except Exception as e:
            logger.error(f"Document import failed for workspace {self.workspace.id}: {str(e)}", exc_info=True)
            processing_time = time.time() - start_time

            await self._update_progress(
                job_id, 'FAILED', 'failed', 0, 0, 0, 0,
                [{"type": "error", "message": f"Import failed: {str(e)}"}], []
            )

            return ImportResult(
                success=False,
                job_id=job_id,
                total_items=0,
                successful_imports=0,
                failed_imports=0,
                errors=[{"type": "error", "message": f"Import failed: {str(e)}"}],
                warnings=[],
                processing_time=processing_time
            )

    async def _validate_products_batch(
        self,
        products: List[Dict[str, Any]],
        create_missing_categories: bool
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Validate and enrich products batch

        Returns:
            Tuple of (validated_products, errors)
        """
        validated = []
        errors = []

        for idx, product_data in enumerate(products):
            try:
                # Validate required fields
                if not product_data.get('name'):
                    errors.append({
                        "type": "error",
                        "row": idx + 1,
                        "message": "Product name is required"
                    })
                    continue

                if not product_data.get('price'):
                    errors.append({
                        "type": "error",
                        "row": idx + 1,
                        "message": f"Price is required for product '{product_data.get('name')}'"
                    })
                    continue

                # Resolve and create categories
                enriched_product = await self._enrich_product_with_categories(
                    product_data, create_missing_categories
                )

                validated.append(enriched_product)

            except Exception as e:
                errors.append({
                    "type": "error",
                    "row": idx + 1,
                    "message": f"Validation failed: {str(e)}"
                })

        return validated, errors

    async def _enrich_product_with_categories(
        self,
        product_data: Dict[str, Any],
        create_missing: bool
    ) -> Dict[str, Any]:
        """
        Resolve category names to category IDs, creating if needed
        """
        from workspace.store.models import Category

        enriched = product_data.copy()

        # Handle main category
        category_name = product_data.get('category', '').strip()
        if category_name:
            category = await self._get_or_create_category(
                category_name, None, create_missing
            )
            if category:
                enriched['category_id'] = category.id
            else:
                enriched['category_id'] = None

        # Handle sub-category
        sub_category_name = product_data.get('sub_category', '').strip()
        if sub_category_name and enriched.get('category_id'):
            sub_category = await self._get_or_create_category(
                sub_category_name, enriched['category_id'], create_missing
            )
            if sub_category:
                enriched['sub_category_id'] = sub_category.id

        return enriched

    async def _get_or_create_category(
        self,
        name: str,
        parent_id: Optional[int],
        create_if_missing: bool
    ):
        """Get or create category by name"""
        from workspace.store.models import Category
        from asgiref.sync import sync_to_async

        try:
            # Try to find existing category
            if parent_id:
                category = await sync_to_async(Category.objects.filter(
                    workspace=self.workspace,
                    name__iexact=name,
                    parent_id=parent_id
                ).first)()
            else:
                category = await sync_to_async(Category.objects.filter(
                    workspace=self.workspace,
                    name__iexact=name,
                    parent__isnull=True
                ).first)()

            if category:
                return category

            # Create if not found and allowed
            if create_if_missing:
                category = await sync_to_async(Category.objects.create)(
                    workspace=self.workspace,
                    name=name,
                    parent_id=parent_id,
                    created_by=self.user
                )
                logger.info(f"Created category '{name}' for workspace {self.workspace.id}")
                return category

            return None

        except Exception as e:
            logger.error(f"Category resolution failed for '{name}': {str(e)}")
            return None

    async def _import_products_batch(
        self,
        products: List[Dict[str, Any]],
        job_id: str,
        existing_errors: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Import products to database in batches

        Returns:
            Dict with successful, failed counts and errors
        """
        from workspace.store.models import Product
        from asgiref.sync import sync_to_async

        successful = 0
        failed = 0
        errors = existing_errors.copy()
        created_product_ids = []

        # Process in batches
        for batch_start in range(0, len(products), self.BATCH_SIZE):
            batch = products[batch_start:batch_start + self.BATCH_SIZE]

            for idx, product_data in enumerate(batch):
                try:
                    # Create product with atomic transaction
                    product = await self._create_product(product_data)

                    if product:
                        successful += 1
                        created_product_ids.append(str(product.id))
                    else:
                        failed += 1
                        errors.append({
                            "type": "error",
                            "message": f"Failed to create product '{product_data.get('name')}'"
                        })

                    # Update progress
                    current = batch_start + idx + 1
                    await self._update_progress(
                        job_id, 'IMPORTING', 'import',
                        current, len(products), successful, failed, errors, []
                    )

                except Exception as e:
                    failed += 1
                    errors.append({
                        "type": "error",
                        "message": f"Failed to import '{product_data.get('name')}': {str(e)}"
                    })
                    logger.error(f"Product import error: {str(e)}", exc_info=True)

        return {
            'successful': successful,
            'failed': failed,
            'errors': errors,
            'created_product_ids': created_product_ids
        }

    async def _create_product(self, product_data: Dict[str, Any]):
        """Create a single product in database"""
        from workspace.store.models import Product
        from asgiref.sync import sync_to_async

        try:
            # Prepare product fields
            product_fields = {
                'workspace': self.workspace,
                'created_by': self.user,
                'name': product_data['name'],
                'price': Decimal(str(product_data['price'])),
                'description': product_data.get('description', ''),
                'short_description': product_data.get('short_description', ''),
                'sku': product_data.get('sku', ''),
                'barcode': product_data.get('barcode', ''),
                'brand': product_data.get('brand', ''),
                'stock_quantity': product_data.get('stock_quantity', 0),
                'track_inventory': product_data.get('track_inventory', True),
                'allow_backorders': product_data.get('allow_backorders', False),
                'low_stock_threshold': product_data.get('low_stock_threshold', 5),
                'selling_type': product_data.get('selling_type', 'both'),
                'requires_shipping': product_data.get('requires_shipping', True),
                'is_digital': product_data.get('is_digital', False),
                'condition': product_data.get('condition', 'new'),
                'featured_image': product_data.get('featured_image', ''),
                'tags': product_data.get('tags', []),
                'status': product_data.get('status', 'draft'),
            }

            # Add optional decimal fields
            if product_data.get('cost_price'):
                product_fields['cost_price'] = Decimal(str(product_data['cost_price']))

            if product_data.get('compare_at_price'):
                product_fields['compare_at_price'] = Decimal(str(product_data['compare_at_price']))

            if product_data.get('weight'):
                product_fields['weight'] = Decimal(str(product_data['weight']))

            if product_data.get('length'):
                product_fields['length'] = Decimal(str(product_data['length']))

            if product_data.get('width'):
                product_fields['width'] = Decimal(str(product_data['width']))

            if product_data.get('height'):
                product_fields['height'] = Decimal(str(product_data['height']))

            # Add category relationships
            if product_data.get('category_id'):
                product_fields['category_id'] = product_data['category_id']

            if product_data.get('sub_category_id'):
                product_fields['sub_category_id'] = product_data['sub_category_id']

            # Create product with transaction
            @sync_to_async
            def create_product_sync():
                with transaction.atomic():
                    return Product.objects.create(**product_fields)

            product = await create_product_sync()
            logger.info(f"Created product '{product.name}' (ID: {product.id})")

            return product

        except IntegrityError as e:
            logger.error(f"Product creation failed (duplicate?): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Product creation failed: {str(e)}", exc_info=True)
            return None

    async def _create_bulk_operation_record(
        self,
        filename: str,
        source_type: str,
        total_products: int,
        imported_products: int,
        products_data: List[Dict],
        status: str,
        error_message: str
    ):
        """Create bulk operation record for history"""
        from workspace.store.models import BulkOperation
        from asgiref.sync import sync_to_async

        try:
            @sync_to_async
            def create_bulk_op():
                return BulkOperation.objects.create(
                    workspace=self.workspace,
                    user=self.user,
                    original_filename=filename,
                    source_type=source_type,
                    status=status,
                    total_products=total_products,
                    imported_products=imported_products,
                    products_data=products_data,
                    error_message=error_message
                )

            bulk_op = await create_bulk_op()
            return bulk_op

        except Exception as e:
            logger.error(f"Failed to create bulk operation record: {str(e)}")
            return None

    async def _update_progress(
        self,
        job_id: str,
        status: str,
        stage: str,
        current: int,
        total: int,
        successful: int,
        failed: int,
        errors: List[Dict],
        warnings: List[str]
    ):
        """Update progress in cache"""
        progress = ImportProgress(
            job_id=job_id,
            status=status,
            stage=stage,
            current_item=current,
            total_items=total,
            percent_complete=int((current / total) * 100) if total > 0 else 0,
            successful_imports=successful,
            failed_imports=failed,
            errors=errors[-10:],  # Keep last 10 errors
            warnings=warnings[:10]  # Keep first 10 warnings
        )

        cache_key = f"product_import_progress:{job_id}"
        cache.set(cache_key, progress.to_dict(), timeout=self.PROGRESS_CACHE_TIMEOUT)

    def _extracted_product_to_dict(self, extracted_product) -> Dict[str, Any]:
        """Convert ExtractedProduct dataclass to dict"""
        return {
            'name': extracted_product.name,
            'price': extracted_product.price,
            'cost_price': extracted_product.cost_price,
            'compare_at_price': extracted_product.compare_at_price,
            'category': extracted_product.category or '',
            'sub_category': extracted_product.sub_category or '',
            'brand': extracted_product.brand or '',
            'sku': extracted_product.sku or '',
            'description': extracted_product.description or '',
            'stock_quantity': extracted_product.stock_quantity,
            'selling_type': extracted_product.selling_type,
            'status': extracted_product.status,
            'condition': extracted_product.condition,
            'track_inventory': extracted_product.track_inventory,
            'allow_backorders': extracted_product.allow_backorders,
            'low_stock_threshold': extracted_product.low_stock_threshold,
            'requires_shipping': extracted_product.requires_shipping,
            'is_digital': extracted_product.is_digital,
            'featured_image': extracted_product.images[0] if extracted_product.images else '',
            'tags': []
        }

    def _get_source_type(self, filename: str) -> str:
        """Determine source type from filename"""
        ext = filename.lower().split('.')[-1]
        if ext == 'csv':
            return 'csv'
        elif ext in ['xlsx', 'xls']:
            return 'excel'
        elif ext == 'pdf':
            return 'pdf'
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            return 'image'
        return 'csv'

    @staticmethod
    def get_import_progress(job_id: str) -> Optional[Dict]:
        """Get import progress from cache"""
        cache_key = f"product_import_progress:{job_id}"
        return cache.get(cache_key)

    @staticmethod
    def clear_import_progress(job_id: str):
        """Clear import progress from cache"""
        cache_key = f"product_import_progress:{job_id}"
        cache.delete(cache_key)

    # Synchronous helper methods for new CSV import
    def _validate_products_batch_sync(
        self,
        products: List[Dict[str, Any]],
        create_missing_categories: bool
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Validate and enrich products batch (synchronous version)

        Returns:
            Tuple of (validated_products, errors)
        """
        validated = []
        errors = []

        for idx, product_data in enumerate(products):
            try:
                # Validate required fields
                if not product_data.get('name'):
                    errors.append({
                        "type": "error",
                        "row": idx + 1,
                        "message": "Product name is required"
                    })
                    continue

                if not product_data.get('price'):
                    errors.append({
                        "type": "error",
                        "row": idx + 1,
                        "message": f"Price is required for product '{product_data.get('name')}'"
                    })
                    continue

                # Resolve and create categories
                enriched_product = self._enrich_product_with_categories_sync(
                    product_data, create_missing_categories
                )

                validated.append(enriched_product)

            except Exception as e:
                errors.append({
                    "type": "error",
                    "row": idx + 1,
                    "message": f"Validation failed: {str(e)}"
                })

        return validated, errors

    def _enrich_product_with_categories_sync(
        self,
        product_data: Dict[str, Any],
        create_missing: bool
    ) -> Dict[str, Any]:
        """
        Resolve category names to category IDs, creating if needed (synchronous)
        """
        from workspace.store.models import Category

        enriched = product_data.copy()

        # Handle main category
        category_name = product_data.get('category', '').strip()
        if category_name:
            category = self._get_or_create_category_sync(
                category_name, None, create_missing
            )
            if category:
                enriched['category_id'] = category.id
            else:
                enriched['category_id'] = None

        # Handle sub-category
        sub_category_name = product_data.get('sub_category', '').strip()
        if sub_category_name and enriched.get('category_id'):
            sub_category = self._get_or_create_category_sync(
                sub_category_name, enriched['category_id'], create_missing
            )
            if sub_category:
                enriched['sub_category_id'] = sub_category.id

        return enriched

    def _get_or_create_category_sync(
        self,
        name: str,
        parent_id: Optional[int],
        create_if_missing: bool
    ):
        """Get or create category by name (synchronous)"""
        from workspace.store.models import Category

        try:
            # Try to find existing category
            if parent_id:
                category = Category.objects.filter(
                    workspace=self.workspace,
                    name__iexact=name,
                    parent_id=parent_id
                ).first()
            else:
                category = Category.objects.filter(
                    workspace=self.workspace,
                    name__iexact=name,
                    parent__isnull=True
                ).first()

            if category:
                return category

            # Create if not found and allowed
            if create_if_missing:
                category = Category.objects.create(
                    workspace=self.workspace,
                    name=name,
                    parent_id=parent_id,
                    created_by=self.user
                )
                logger.info(f"Created category '{name}' for workspace {self.workspace.id}")
                return category

            return None

        except Exception as e:
            logger.error(f"Category resolution failed for '{name}': {str(e)}")
            return None

    def _import_products_batch_sync(
        self,
        products: List[Dict[str, Any]],
        job_id: str,
        existing_errors: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Import products to database in batches (synchronous)

        Returns:
            Dict with successful, failed counts and errors
        """
        from workspace.store.models import Product

        successful = 0
        failed = 0
        errors = existing_errors.copy()
        created_product_ids = []

        # Process in batches
        for batch_start in range(0, len(products), self.BATCH_SIZE):
            batch = products[batch_start:batch_start + self.BATCH_SIZE]

            for idx, product_data in enumerate(batch):
                try:
                    # Create product with atomic transaction
                    product = self._create_product_sync(product_data)

                    if product:
                        successful += 1
                        created_product_ids.append(str(product.id))
                    else:
                        failed += 1
                        errors.append({
                            "type": "error",
                            "message": f"Failed to create product '{product_data.get('name')}'"
                        })

                    # Update progress
                    current = batch_start + idx + 1
                    self._update_progress_sync(
                        job_id, 'IMPORTING', 'import',
                        current, len(products), successful, failed, errors, []
                    )

                except Exception as e:
                    failed += 1
                    errors.append({
                        "type": "error",
                        "message": f"Failed to import '{product_data.get('name')}': {str(e)}"
                    })
                    logger.error(f"Product import error: {str(e)}", exc_info=True)

        return {
            'successful': successful,
            'failed': failed,
            'errors': errors,
            'created_product_ids': created_product_ids
        }

    def _create_product_sync(self, product_data: Dict[str, Any]):
        """Create a single product in database (synchronous)"""
        from workspace.store.models import Product
        from django.utils import timezone

        try:
            # Prepare product fields
            product_fields = {
                'workspace': self.workspace,
                'created_by': self.user,
                'name': product_data['name'],
                'price': Decimal(str(product_data['price'])),
                'description': product_data.get('description', ''),
                'short_description': product_data.get('short_description', ''),
                'sku': product_data.get('sku', ''),
                'barcode': product_data.get('barcode', ''),
                'brand': product_data.get('brand', ''),
                'stock_quantity': product_data.get('stock_quantity', 0),
                'track_inventory': product_data.get('track_inventory', True),
                'allow_backorders': product_data.get('allow_backorders', False),
                'low_stock_threshold': product_data.get('low_stock_threshold', 5),
                'selling_type': product_data.get('selling_type', 'both'),
                'requires_shipping': product_data.get('requires_shipping', True),
                'is_digital': product_data.get('is_digital', False),
                'condition': product_data.get('condition', 'new'),
                'featured_image': product_data.get('featured_image', ''),
                'tags': product_data.get('tags', []),
                'status': product_data.get('status', 'draft'),
            }

            # Add optional decimal fields
            if product_data.get('cost_price'):
                product_fields['cost_price'] = Decimal(str(product_data['cost_price']))

            if product_data.get('compare_at_price'):
                product_fields['compare_at_price'] = Decimal(str(product_data['compare_at_price']))

            if product_data.get('weight'):
                product_fields['weight'] = Decimal(str(product_data['weight']))

            # Add category relationships
            if product_data.get('category_id'):
                product_fields['category_id'] = product_data['category_id']

            if product_data.get('sub_category_id'):
                product_fields['sub_category_id'] = product_data['sub_category_id']

            # Create product with transaction
            with transaction.atomic():
                product = Product.objects.create(**product_fields)
                logger.info(f"Created product '{product.name}' (ID: {product.id})")
                return product

        except IntegrityError as e:
            logger.error(f"Product creation failed (duplicate?): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Product creation failed: {str(e)}", exc_info=True)
            return None

    def _update_progress_sync(
        self,
        job_id: str,
        status: str,
        stage: str,
        current: int,
        total: int,
        successful: int,
        failed: int,
        errors: List[Dict],
        warnings: List[str]
    ):
        """Update progress in cache (synchronous)"""
        progress = ImportProgress(
            job_id=job_id,
            status=status,
            stage=stage,
            current_item=current,
            total_items=total,
            percent_complete=int((current / total) * 100) if total > 0 else 0,
            successful_imports=successful,
            failed_imports=failed,
            errors=errors[-10:],  # Keep last 10 errors
            warnings=warnings[:10]  # Keep first 10 warnings
        )

        cache_key = f"product_import_progress:{job_id}"
        cache.set(cache_key, progress.to_dict(), timeout=self.PROGRESS_CACHE_TIMEOUT)
