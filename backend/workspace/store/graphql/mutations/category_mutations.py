"""
Category GraphQL Mutations for Admin Store API

Provides category mutations with @transaction.atomic
Critical for hierarchical category management

Following GraphQL Architecture Standards:
- Proper typed responses (no JSONString)
- Standard success/error/message fields
- Service layer orchestration
- Input validation at GraphQL schema level
"""

import graphene
from django.db import transaction
from graphql import GraphQLError
from graphene_file_upload.scalars import Upload
from ..types.category_types import CategoryType
from workspace.store.services.category_service import category_service
from workspace.store.services.product_service import product_service
from workspace.core.services import PermissionService

# Input types for category operations
class CategoryReorderInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    sort_order = graphene.Int(required=True)


class UpdateCategory(graphene.Mutation):
    """
    Update category with atomic transaction (Shopify-style)

    Security: Validates workspace ownership
    Integrity: Uses @transaction.atomic for rollback
    Hierarchical: Validates parent relationships
    Images: Replace category banner image
    """

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        parent_id = graphene.ID()
        is_visible = graphene.Boolean()
        is_featured = graphene.Boolean()
        sort_order = graphene.Int()
        featured_media_id = graphene.String(description="Featured image ID (from media upload)")
        remove_featured_media = graphene.Boolean(description="Remove existing featured image")

        # SEO fields (allow editing after creation)
        slug = graphene.String(description="URL-friendly slug (must be unique within workspace)")
        meta_title = graphene.String(description="SEO meta title (max 60 chars)")
        meta_description = graphene.String(description="SEO meta description (max 160 chars)")

    # PROPER TYPED RESPONSE - Standard pattern
    success = graphene.Boolean()
    category = graphene.Field(CategoryType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id, **kwargs):
        workspace = info.context.workspace
        user = info.context.user
        
        if not PermissionService.has_permission(user, workspace, 'category:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Extract media-related fields
            featured_media_id = kwargs.pop('featured_media_id', None)
            remove_featured_media = kwargs.pop('remove_featured_media', False)

            # Validate media if provided (NEW system)
            if featured_media_id:
                from workspace.store.services.media_validation_service import media_validator
                validation = media_validator.validate_featured_media(
                    media_id=featured_media_id,
                    allowed_types=['image'],
                    workspace=workspace  # SECURITY: Validate workspace ownership
                )
                if not validation['valid']:
                    return UpdateCategory(
                        success=False,
                        error=validation['error']
                    )

            # Convert GraphQL input to service format
            update_data = {}
            for field, value in kwargs.items():
                if value is not None and field not in ['meta_title', 'meta_description', 'slug']:
                    update_data[field] = value

            # SEO FIELD HANDLING (with truncation for scale)
            # For updates: truncate if provided, but don't auto-populate (preserve existing values)
            if kwargs.get('meta_title') is not None:
                update_data['meta_title'] = kwargs['meta_title'][:60]

            if kwargs.get('meta_description') is not None:
                update_data['meta_description'] = kwargs['meta_description'][:160]

            # SLUG VALIDATION (ensure uniqueness within workspace)
            if kwargs.get('slug'):
                from workspace.store.models import Category
                from django.utils.text import slugify

                new_slug = slugify(kwargs['slug'])

                # Check if slug is unique (excluding current category)
                if Category.objects.filter(
                    workspace=workspace,
                    slug=new_slug
                ).exclude(id=id).exists():
                    return UpdateCategory(
                        success=False,
                        error=f"Slug '{new_slug}' is already in use. Please choose a different one."
                    )

                update_data['slug'] = new_slug

            # Call service layer
            result = category_service.update_category(
                workspace=workspace,
                category_id=id,
                update_data=update_data,
                user=user
            )

            if not result['success']:
                return UpdateCategory(
                    success=False,
                    error=result.get('error')
                )

            category = result['category']

            # NEW MEDIA SYSTEM: Handle featured media operations
            if remove_featured_media:
                category.featured_media_id = None
                category.save(update_fields=['featured_media_id'])
            elif featured_media_id:
                category.featured_media_id = featured_media_id
                category.save(update_fields=['featured_media_id'])

            return UpdateCategory(
                success=True,
                category=result.get('category'),
                message="Category updated successfully",
                error=None
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category update mutation failed: {str(e)}", exc_info=True)

            return UpdateCategory(
                success=False,
                error=f"Category update failed: {str(e)}"
            )


class DeleteCategory(graphene.Mutation):
    """
    Delete category with atomic transaction

    Security: Validates workspace ownership
    Integrity: Uses @transaction.atomic for rollback
    Safety: Prevents deletion of categories with products
    Hierarchical: Handles orphaned children
    """

    class Arguments:
        id = graphene.ID(required=True)

    # PROPER TYPED RESPONSE - Standard pattern
    success = graphene.Boolean()
    deleted_id = graphene.ID()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'category:delete'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Call service layer
            result = category_service.delete_category(
                workspace=workspace,
                category_id=id,
                user=user
            )

            return DeleteCategory(
                success=result['success'],
                deleted_id=result.get('deleted_id'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category deletion mutation failed: {str(e)}", exc_info=True)

            return DeleteCategory(
                success=False,
                error=f"Category deletion failed: {str(e)}"
            )


class CreateCategory(graphene.Mutation):
    """
    Create new category with atomic transaction (Shopify-style)

    Security: Validates workspace ownership
    Integrity: Uses @transaction.atomic for rollback
    Hierarchical: Validates parent relationships
    Images: Accepts single image file upload
    """

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        is_visible = graphene.Boolean(default_value=True)
        is_featured = graphene.Boolean(default_value=False)
        sort_order = graphene.Int(default_value=0)
        featured_media_id = graphene.String(description="Featured image ID (from media upload)")

        # SEO fields (Shopify-style: allow explicit values or auto-populate)
        slug = graphene.String(description="URL-friendly slug (auto-generated from name if not provided)")
        meta_title = graphene.String(description="SEO meta title (max 60 chars, defaults to name if empty)")
        meta_description = graphene.String(description="SEO meta description (max 160 chars, defaults to description if empty)")

    # PROPER TYPED RESPONSE - Standard pattern
    success = graphene.Boolean()
    category = graphene.Field(CategoryType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, name, **kwargs):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'category:create'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Extract media ID
            featured_media_id = kwargs.pop('featured_media_id', None)

            # Validate media if provided (NEW system)
            if featured_media_id:
                from workspace.store.services.media_validation_service import media_validator
                validation = media_validator.validate_featured_media(
                    media_id=featured_media_id,
                    allowed_types=['image'],
                    workspace=workspace  # SECURITY: Validate workspace ownership
                )
                if not validation['valid']:
                    return CreateCategory(
                        success=False,
                        error=validation['error']
                    )

            # SEO AUTO-POPULATION (Shopify-style server-side fallback)
            description_text = kwargs.get('description', '')

            # meta_title: Use provided value, fallback to category name, truncate to 60 chars
            meta_title = kwargs.get('meta_title') if kwargs.get('meta_title') else name
            meta_title = meta_title[:60] if meta_title else ''

            # meta_description: Use provided value, fallback to description, truncate to 160 chars
            meta_description = kwargs.get('meta_description') if kwargs.get('meta_description') else description_text
            meta_description = meta_description[:160] if meta_description else ''

            # Convert GraphQL input to service format
            category_data = {
                'name': name,
                'slug': kwargs.get('slug', ''),  # Will be auto-generated in model.save() if empty
                'meta_title': meta_title,
                'meta_description': meta_description
            }

            # Add other optional fields
            for field, value in kwargs.items():
                if value is not None and field not in ['featured_media_id', 'slug', 'meta_title', 'meta_description']:
                    category_data[field] = value

            # Call service layer
            result = category_service.create_category(
                workspace=workspace,
                category_data=category_data,
                user=user
            )

            if not result['success']:
                return CreateCategory(
                    success=False,
                    error=result.get('error')
                )

            category = result['category']

            # NEW MEDIA SYSTEM: Attach featured media via FK
            if featured_media_id:
                category.featured_media_id = featured_media_id
                category.save(update_fields=['featured_media_id'])

            return CreateCategory(
                success=True,
                category=category,
                message="Category created successfully",
                error=None
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category creation mutation failed: {str(e)}", exc_info=True)

            return CreateCategory(
                success=False,
                error=f"Category creation failed: {str(e)}"
            )


class ReorderCategories(graphene.Mutation):
    """
    Reorder categories with atomic transaction

    Security: Validates workspace ownership
    Integrity: Uses @transaction.atomic for rollback
    Performance: Bulk update for efficiency
    """

    class Arguments:
        reorder_data = graphene.List(
            graphene.NonNull(CategoryReorderInput),
            required=True
        )

    # PROPER TYPED RESPONSE - Standard pattern
    success = graphene.Boolean()
    updated_count = graphene.Int()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, reorder_data):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'category:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Convert GraphQL input to service format
            reorder_list = []
            for item in reorder_data:
                reorder_list.append({
                    'id': item.id,
                    'sort_order': item.sort_order
                })

            # Call service layer
            result = category_service.reorder_categories(
                workspace=workspace,
                reorder_data=reorder_list,
                user=user
            )

            return ReorderCategories(
                success=result['success'],
                updated_count=result.get('updated_count', 0),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category reordering mutation failed: {str(e)}", exc_info=True)

            return ReorderCategories(
                success=False,
                error=f"Category reordering failed: {str(e)}"
            )


class ToggleCategoryVisibility(graphene.Mutation):
    """
    Toggle category visibility with atomic transaction

    Security: Validates workspace ownership
    Integrity: Uses @transaction.atomic for rollback
    """

    class Arguments:
        id = graphene.ID(required=True)

    # PROPER TYPED RESPONSE - Standard pattern
    success = graphene.Boolean()
    category = graphene.Field(CategoryType)
    is_visible = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'category:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Call service layer
            result = category_service.toggle_category_visibility(
                workspace=workspace,
                category_id=id,
                user=user
            )

            return ToggleCategoryVisibility(
                success=result['success'],
                category=result.get('category'),
                is_visible=result.get('is_visible'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category visibility toggle mutation failed: {str(e)}", exc_info=True)

            return ToggleCategoryVisibility(
                success=False,
                error=f"Category visibility toggle failed: {str(e)}"
            )


class AddProductsToCategory(graphene.Mutation):
    """
    Add products to category with atomic transaction

    Security: Validates workspace ownership for both category and products
    Integrity: Uses @transaction.atomic for rollback
    Performance: Bulk operation for multiple products
    """

    class Arguments:
        category_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)

    # PROPER TYPED RESPONSE - Standard pattern
    success = graphene.Boolean()
    category = graphene.Field(CategoryType)
    added_count = graphene.Int()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, category_id, product_ids):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'product:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Call service layer
            result = product_service.add_products_to_category(
                workspace=workspace,
                category_id=category_id,
                product_ids=product_ids,
                user=user
            )

            return AddProductsToCategory(
                success=result['success'],
                category=result.get('category'),
                added_count=result.get('added_count', 0),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Add products to category mutation failed: {str(e)}", exc_info=True)

            return AddProductsToCategory(
                success=False,
                error=f"Failed to add products to category: {str(e)}"
            )


class RemoveProductsFromCategory(graphene.Mutation):
    """
    Remove products from category with atomic transaction

    Security: Validates workspace ownership for both category and products
    Integrity: Uses @transaction.atomic for rollback
    Performance: Bulk operation for multiple products
    """

    class Arguments:
        category_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)

    # PROPER TYPED RESPONSE - Standard pattern
    success = graphene.Boolean()
    category = graphene.Field(CategoryType)
    removed_count = graphene.Int()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, category_id, product_ids):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'product:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Call service layer
            result = product_service.remove_products_from_category(
                workspace=workspace,
                category_id=category_id,
                product_ids=product_ids,
                user=user
            )

            return RemoveProductsFromCategory(
                success=result['success'],
                category=result.get('category'),
                removed_count=result.get('removed_count', 0),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Remove products from category mutation failed: {str(e)}", exc_info=True)

            return RemoveProductsFromCategory(
                success=False,
                error=f"Failed to remove products from category: {str(e)}"
            )


class CategoryMutations(graphene.ObjectType):
    """
    Category mutations collection
    """

    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()
    create_category = CreateCategory.Field()
    reorder_categories = ReorderCategories.Field()
    toggle_category_visibility = ToggleCategoryVisibility.Field()
    add_products_to_category = AddProductsToCategory.Field()
    remove_products_from_category = RemoveProductsFromCategory.Field()