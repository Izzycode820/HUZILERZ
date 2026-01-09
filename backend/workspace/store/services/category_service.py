"""
Category Service Layer - Shopify-like Business Logic for Category Operations

Following GraphQL Architecture Standards & Shopify Design Philosophy:
- Single Responsibility: Pure business logic only
- Performance: Optimized atomic operations
- Security: Input validation and workspace scoping
- Reliability: Atomic transactions and error handling
- Shopify-like: Focus on core CRUD operations, no complex tree building
"""

from typing import Dict, Any, List, Optional
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.text import slugify
from workspace.store.models import Category
from workspace.store.utils.workspace_permissions import assert_permission

class CategoryService:
    """
    Shopify-like Category Service - Focused on core business operations

    Production-Ready Features:
    - Atomic transactions for data integrity
    - Comprehensive error handling and logging
    - Input validation and sanitization
    - Workspace scoping for multi-tenant security
    - Performance-optimized queries with proper indexing
    """

    def __init__(self):
        self.max_batch_size = 500

    def create_category(self, workspace, category_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """
        Create category with validation and atomic transaction

        Args:
            workspace: Workspace instance
            category_data: Category creation data
            user: Optional user performing operation

        Returns:
            Dict with success, category data, and message
        """
        try:
            with transaction.atomic():
                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'category:create')
                # Validate category data
                validation_result = self._validate_category_data(category_data)
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'error': validation_result['error']
                    }

                # Create category (slug auto-generated in model.save() if not provided)
                category = Category.objects.create(
                    workspace=workspace,
                    name=category_data['name'],
                    slug=category_data.get('slug', ''),  # Model will auto-generate if empty
                    description=category_data.get('description', ''),
                    is_visible=category_data.get('is_visible', True),
                    is_featured=category_data.get('is_featured', False),
                    sort_order=category_data.get('sort_order', 0),
                    # SEO fields (auto-populated in mutation layer, passed through here)
                    meta_title=category_data.get('meta_title', ''),
                    meta_description=category_data.get('meta_description', '')
                )

                return {
                    'success': True,
                    'category': category,
                    'message': f'Category {category.name} created successfully'
                }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category creation failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Category creation failed: {str(e)}'
            }

    def update_category(self, workspace, category_id: str, update_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """
        Update category with validation and atomic transaction

        Args:
            workspace: Workspace instance
            category_id: Category ID to update
            update_data: Update data
            user: Optional user performing operation

        Returns:
            Dict with success, category data, and message
        """
        try:
            with transaction.atomic():
                # Get category with workspace scoping
                category = Category.objects.select_for_update().get(
                    id=category_id,
                    workspace=workspace
                )

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'category:update')

                # Remove parent_id if present (not supported in Shopify-like collections)
                if 'parent_id' in update_data:
                    del update_data['parent_id']

                # Update fields
                for field, value in update_data.items():
                    if hasattr(category, field) and value is not None:
                        setattr(category, field, value)

                category.save()

                return {
                    'success': True,
                    'category': category,
                    'message': f'Category {category.name} updated successfully'
                }

        except Category.DoesNotExist:
            return {
                'success': False,
                'error': 'Category not found'
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category update failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Category update failed: {str(e)}'
            }

    def delete_category(self, workspace, category_id: str, user=None) -> Dict[str, Any]:
        """
        Delete category with atomic transaction and safety checks

        Args:
            workspace: Workspace instance
            category_id: Category ID to delete
            move_children_to_parent: Whether to move children to parent category
            user: Optional user performing operation

        Returns:
            Dict with success, deleted ID, and moved children count
        """
        try:
            with transaction.atomic():
                # Get category with workspace scoping
                category = Category.objects.select_for_update().get(
                    id=category_id,
                    workspace=workspace
                )

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'category:delete')

                # Check if category has products
                if category.products.exists():
                    return {
                        'success': False,
                        'error': 'Cannot delete category with products. Move products first.'
                    }

                # Delete category
                category_id = category.id
                category.delete()

                return {
                    'success': True,
                    'deleted_id': category_id,
                    'message': f'Category deleted successfully'
                }

        except Category.DoesNotExist:
            return {
                'success': False,
                'error': 'Category not found'
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category deletion failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Category deletion failed: {str(e)}'
            }

    def reorder_categories(self, workspace, reorder_data: List[Dict[str, Any]], user=None) -> Dict[str, Any]:
        """
        Reorder categories with atomic transaction

        Args:
            workspace: Workspace instance
            reorder_data: List of {id, sort_order} dictionaries
            user: Optional user performing operation

        Returns:
            Dict with success and updated count
        """
        try:
            with transaction.atomic():
                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'category:update')

                if not reorder_data:
                    return {
                        'success': False,
                        'error': 'No reorder data provided'
                    }

                # Validate all categories belong to workspace
                category_ids = {item['id'] for item in reorder_data}
                valid_categories = Category.objects.filter(
                    id__in=category_ids,
                    workspace=workspace
                ).values_list('id', flat=True)

                invalid_categories = category_ids - set(valid_categories)
                if invalid_categories:
                    return {
                        'success': False,
                        'error': f'Invalid categories: {list(invalid_categories)}'
                    }

                # Update sort orders
                updated_count = 0
                for item in reorder_data:
                    try:
                        category = Category.objects.select_for_update().get(
                            id=item['id'],
                            workspace=workspace
                        )
                        category.sort_order = item['sort_order']
                        category.save()
                        updated_count += 1
                    except Category.DoesNotExist:
                        # Should not happen due to validation above
                        continue

                return {
                    'success': True,
                    'updated_count': updated_count,
                    'message': f'Successfully reordered {updated_count} categories'
                }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category reordering failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Category reordering failed: {str(e)}'
            }

    def toggle_category_visibility(self, workspace, category_id: str, user=None) -> Dict[str, Any]:
        """
        Toggle category visibility with atomic transaction

        Args:
            workspace: Workspace instance
            category_id: Category ID to toggle
            user: Optional user performing operation

        Returns:
            Dict with success, category data, and new visibility state
        """
        try:
            with transaction.atomic():
                # Get category with workspace scoping
                category = Category.objects.select_for_update().get(
                    id=category_id,
                    workspace=workspace
                )

                # Validate permissions
                if user:
                    assert_permission(workspace, user, 'category:update')

                # Toggle visibility
                category.is_visible = not category.is_visible
                category.save()

                return {
                    'success': True,
                    'category': category,
                    'is_visible': category.is_visible,
                    'message': f'Category visibility set to {category.is_visible}'
                }

        except Category.DoesNotExist:
            return {
                'success': False,
                'error': 'Category not found'
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category visibility toggle failed: {str(e)}", exc_info=True)

            return {
                'success': False,
                'error': f'Category visibility toggle failed: {str(e)}'
            }

    # HELPER METHODS

    def _validate_category_data(self, category_data: Dict) -> Dict[str, Any]:
        """Validate category data before creation"""
        required_fields = ['name']
        missing_fields = [field for field in required_fields if field not in category_data]

        if missing_fields:
            return {
                'valid': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }

        # Validate name length
        if len(category_data['name']) > 255:
            return {
                'valid': False,
                'error': 'Category name must be 255 characters or less'
            }

        return {'valid': True}


    def _generate_unique_slug(self, workspace, name: str) -> str:
        """Generate unique slug for category within workspace"""
        slug = slugify(name)
        original_slug = slug
        counter = 1

        while Category.objects.filter(workspace=workspace, slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

            if counter > 100:  # Safety limit
                raise ValidationError("Could not generate unique slug")

        return slug


# Global instance for easy access
category_service = CategoryService()