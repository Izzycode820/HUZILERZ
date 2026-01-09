"""
Shopify-inspired CSV Parser Service

Clean, focused service for CSV parsing with Shopify principles:
- Simple, synchronous parsing
- Pure data extraction (no business logic)
- Minimal error handling (just parsing errors)
- Returns raw data for import service to process
- Workspace scoping for multi-tenant security

Shopify Approach:
- Parse CSV → Return raw data → Import service handles business logic
- No async complexity
- No progress tracking (handled by job models)
- Simple column mapping
"""

import csv
import io
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
from workspace.store.models.csv_parser_model import CSVImportJob, CSVImportRow
from workspace.store.utils.workspace_permissions import assert_permission


class CSVParserService:
    """
    Shopify-inspired CSV parser - pure data extraction only

    Responsibilities:
    - Parse CSV file content
    - Map columns to standard field names
    - Extract and clean raw data
    - Return data for import service to validate and process

    Does NOT:
    - Validate business rules
    - Create products
    - Handle async processing
    - Track progress
    """

    # Shopify-style column mappings
    COLUMN_MAPPINGS = {
        'name': ['name', 'product_name', 'title'],
        'price': ['price', 'selling_price', 'cost'],
        'description': ['description', 'desc'],
        'category': ['category', 'category_name'],
        'brand': ['brand', 'manufacturer'],
        'sku': ['sku', 'code', 'product_id'],
        'barcode': ['barcode', 'upc', 'ean'],
        'stock_quantity': ['stock_quantity', 'quantity', 'stock', 'qty'],
        'cost_price': ['cost_price', 'wholesale_price', 'buy_price'],
        'compare_at_price': ['compare_at_price', 'original_price', 'msrp'],
        'weight': ['weight'],
        'condition': ['condition', 'state'],
        'featured_image': ['featured_image', 'image', 'main_image'],
        'tags': ['tags', 'keywords']
    }

    def parse_csv_content(self, workspace, file_content: bytes, filename: str, job: CSVImportJob, user=None) -> Dict[str, Any]:
        """
        Parse CSV content and return raw product data

        Shopify approach: Simple parsing, return data for import service
        """
        try:
            # Validate admin permissions for CSV import
            if user:
                assert_permission(workspace, user, 'product:create')

            # Basic file validation
            if len(file_content) == 0:
                return {
                    'success': False,
                    'error': 'File is empty',
                    'products': [],
                    'total_rows': 0
                }

            # Try UTF-8 first (Shopify standard)
            try:
                content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to Latin-1
                content = file_content.decode('latin-1')

            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(content))
            fieldnames = csv_reader.fieldnames or []

            # Map columns
            column_mappings = self._map_columns(fieldnames)

            # Validate required columns
            if 'name' not in column_mappings or 'price' not in column_mappings:
                missing = []
                if 'name' not in column_mappings:
                    missing.append('name')
                if 'price' not in column_mappings:
                    missing.append('price')

                return {
                    'success': False,
                    'error': f'Required columns missing: {", ".join(missing)}',
                    'products': [],
                    'total_rows': 0
                }

            # Process rows
            products = []
            parsing_errors = []
            row_number = 1  # Start after header

            for row in csv_reader:
                row_number += 1

                # Map CSV columns to expected fields
                mapped_row = {}
                for field, csv_column in column_mappings.items():
                    mapped_row[field] = row.get(csv_column, '')

                # Parse row data
                product_data, errors = self._parse_row_data(mapped_row, row_number)

                if product_data:
                    products.append(product_data)

                # Collect parsing errors
                for error in errors:
                    parsing_errors.append({
                        'row_number': row_number,
                        'error': error,
                        'type': 'parsing_error'
                    })

            # Update job with basic info
            job.total_rows = row_number - 1  # Exclude header
            job.save()

            return {
                'success': True,
                'products': products,
                'parsing_errors': parsing_errors,
                'total_rows': row_number - 1,
                'valid_rows': len(products),
                'column_mappings': column_mappings
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'CSV parsing failed: {str(e)}',
                'products': [],
                'total_rows': 0
            }

    def create_csv_import_job(self, workspace, filename: str, file_size: int, user=None) -> CSVImportJob:
        """
        Create a CSV import job with workspace scoping

        Shopify approach: Track import operations with proper workspace isolation
        """
        try:
            # Validate admin permissions
            if user:
                assert_permission(workspace, user, 'product:create')

            # Create import job
            job = CSVImportJob.objects.create(
                workspace=workspace,
                filename=filename,
                file_size=file_size,
                status='pending'
            )

            return job

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"CSV import job creation failed: {str(e)}", exc_info=True)
            raise

    def _parse_row_data(self, row_data: Dict[str, str], row_number: int) -> Tuple[Optional[Dict], List[str]]:
        """
        Parse a single CSV row into product data

        Only does basic parsing - no business validation
        """
        errors = []
        product = {}

        # Check required fields
        name = row_data.get('name', '').strip()
        if not name:
            errors.append(f'Row {row_number}: Missing product name')
            return None, errors

        price_str = row_data.get('price', '').strip()
        if not price_str:
            errors.append(f'Row {row_number}: Missing price')
            return None, errors

        # Parse price
        price = self._parse_price(price_str)
        if price is None:
            errors.append(f'Row {row_number}: Invalid price format')
            return None, errors

        # Set parsed fields
        product['name'] = name
        product['price'] = str(price)

        # Parse optional fields
        product['description'] = row_data.get('description', '').strip()
        product['category'] = row_data.get('category', '').strip()
        product['brand'] = row_data.get('brand', '').strip()
        product['sku'] = row_data.get('sku', '').strip()
        product['barcode'] = row_data.get('barcode', '').strip()
        product['condition'] = row_data.get('condition', '').strip().lower() or 'new'

        # Parse numeric fields
        stock_qty = self._parse_integer(row_data.get('stock_quantity', ''))
        product['stock_quantity'] = stock_qty if stock_qty is not None else 0

        cost_price = self._parse_price(row_data.get('cost_price', ''))
        if cost_price is not None:
            product['cost_price'] = str(cost_price)

        compare_at_price = self._parse_price(row_data.get('compare_at_price', ''))
        if compare_at_price is not None:
            product['compare_at_price'] = str(compare_at_price)

        # Physical dimensions
        weight = self._parse_decimal(row_data.get('weight', ''))
        if weight is not None:
            product['weight'] = str(weight)

        # Media
        featured_image = row_data.get('featured_image', '').strip()
        if featured_image:
            product['featured_image'] = featured_image

        # Tags
        product['tags'] = self._parse_tags(row_data.get('tags', ''))

        return product, errors

    def _map_columns(self, csv_columns: List[str]) -> Dict[str, str]:
        """Map CSV columns to expected product fields"""
        mappings = {}

        for field, possible_names in self.COLUMN_MAPPINGS.items():
            for csv_col in csv_columns:
                normalized_csv = self._normalize_column_name(csv_col)
                for possible_name in possible_names:
                    if normalized_csv == self._normalize_column_name(possible_name):
                        mappings[field] = csv_col
                        break
                if field in mappings:
                    break

        return mappings

    def _normalize_column_name(self, column: str) -> str:
        """Normalize column names for matching"""
        return column.lower().strip().replace(' ', '_').replace('-', '_')

    def _parse_price(self, value: str) -> Optional[Decimal]:
        """Parse price from string"""
        if not value or value.strip() == '':
            return None

        try:
            # Remove currency symbols and spaces
            cleaned = str(value).strip().replace('$', '').replace('€', '').replace('£', '').replace(',', '')
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def _parse_integer(self, value: str) -> Optional[int]:
        """Parse integer from string"""
        if not value or value.strip() == '':
            return None

        try:
            return int(float(str(value).strip().replace(',', '')))
        except (ValueError, TypeError):
            return None

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """Parse decimal from string"""
        if not value or value.strip() == '':
            return None

        try:
            return Decimal(str(value).strip().replace(',', ''))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _parse_tags(self, value: str) -> List[str]:
        """Parse tags from string"""
        if not value or value.strip() == '':
            return []

        tags = []
        for tag in str(value).replace(';', ',').split(','):
            cleaned_tag = tag.strip()
            if cleaned_tag:
                tags.append(cleaned_tag)

        return tags[:10]  # Limit to 10 tags


# Global instance for easy access
csv_parser_service = CSVParserService()