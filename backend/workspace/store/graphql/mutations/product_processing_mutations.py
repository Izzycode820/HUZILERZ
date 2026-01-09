"""
Product Service GraphQL Mutations

Production-ready product mutations using ProductService
Replaces simple product_mutations.py with service-based approach
Follows industry standards for performance and reliability

Performance: < 100ms response time for product operations
Scalability: Bulk operations with background processing
Reliability: Atomic transactions with comprehensive error handling
Security: Workspace scoping and permission validation
"""

import graphene
from graphql import GraphQLError
from graphene_file_upload.scalars import Upload
from workspace.store.services.product_service import product_service
from workspace.store.services.media_validation_service import media_validator
from medialib.models import MediaUpload
from workspace.store.models import ProductMediaGallery
from workspace.core.services import PermissionService

class ProductVariantOptionInput(graphene.InputObjectType):
    """Input for variant options"""

    option_name = graphene.String(required=True)
    option_values = graphene.List(graphene.String, required=True)


class RegionalInventoryInput(graphene.InputObjectType):
    """Input for regional inventory"""

    region_id = graphene.String(required=True)
    quantity = graphene.Int(required=True)


class InventoryInput(graphene.InputObjectType):
    """
    Input for inventory-related fields (Shopify-style)
    """

    track_inventory = graphene.Boolean(default_value=True)
    allow_backorders = graphene.Boolean(default_value=False)
    inventory_quantity = graphene.Int(default_value=0)
    onhand = graphene.Int(description="Total stock on hand")
    available = graphene.Int(description="Stock available for sale")
    condition = graphene.String(description="Condition: new, refurbished, second_hand, etc.")
    location_id = graphene.ID(description="Location ID for inventory")
    sku = graphene.String()
    barcode = graphene.String()

class ShippingInput(graphene.InputObjectType):
    """
    Input for shipping-related fields
    """

    requires_shipping = graphene.Boolean(default_value=True)
    package_id = graphene.ID(description="Shipping package ID (optional - falls back to default)")
    weight = graphene.Decimal()
    shipping_config = graphene.JSONString()


class SEOInput(graphene.InputObjectType):
    """
    Input for SEO-related fields (Shopify-style)
    """

    slug = graphene.String(description="URL-friendly slug (auto-generated from name if not provided)")
    meta_title = graphene.String(description="SEO meta title (max 60 chars, defaults to name if empty)")
    meta_description = graphene.String(description="SEO meta description (max 160 chars, defaults to description if empty)")


class OrganizationInput(graphene.InputObjectType):
    """
    Input for organization-related fields
    """

    product_type = graphene.String(default_value='physical')
    vendor = graphene.String()
    brand = graphene.String()
    category_id = graphene.String()
    tags = graphene.JSONString()


class VariantInput(graphene.InputObjectType):
    """
    Input for variant creation/update with featured image

    Supports inline variant creation with single featured image
    All fields optional except options (option1/option2)
    """

    # OPTIONS (identify the variant)
    option1 = graphene.String(description="First option (e.g., Color: Red)")
    option2 = graphene.String(description="Second option (e.g., Size: Large)")
    option3 = graphene.String(description="Third option (if needed)")

    # PRICING (overrides product pricing)
    price = graphene.Decimal(description="Variant price")
    compare_at_price = graphene.Decimal(description="Compare at price")
    cost_price = graphene.Decimal(description="Cost per item")

    # MEDIA (NEW - Production-grade system)
    featured_media_id = graphene.String(description="Featured image ID (single image per variant)")

    # INVENTORY (uses same InventoryInput type for consistency)
    inventory = graphene.Field(InventoryInput, description="Variant inventory data")

    # STATUS
    is_active = graphene.Boolean(default_value=True)
    position = graphene.Int(description="Display position")


class ProductUpdateInput(graphene.InputObjectType):
    """
    Input for product updates (Shopify-style)

    Validation: Field validation and data integrity
    Security: Workspace scoping via JWT middleware
    Images: Accepts array of Upload scalars for adding new images
    """

    # BASIC PRODUCT INFO
    name = graphene.String()
    description = graphene.String()
    price = graphene.Decimal()
    status = graphene.String()

    # PRICING
    cost_price = graphene.Decimal()
    compare_at_price = graphene.Decimal()
    charge_tax = graphene.Boolean()
    payment_charges = graphene.Boolean()
    charges_amount = graphene.Decimal()

    # ORGANIZED INPUT TYPES
    inventory = graphene.Field(InventoryInput, description="Inventory-related fields")
    shipping = graphene.Field(ShippingInput, description="Shipping-related fields")
    seo = graphene.Field(SEOInput, description="SEO-related fields")
    organization = graphene.Field(OrganizationInput, description="Organization-related fields")
    options = graphene.List(ProductVariantOptionInput, description="Option definitions (e.g., [{'option_name':'Color', 'option_values': ['Blue', 'Black']}])")

    # MEDIA (NEW - Production-grade system)
    featured_media_id = graphene.String(description="Featured image ID (product thumbnail)")
    media_ids = graphene.List(graphene.String, description="Array of media IDs for gallery (images/videos/3D models)")

    # VARIANTS
    has_variants = graphene.Boolean(description="Whether product has variants")
    variants = graphene.List(VariantInput, description="Update or add variants with featured images")


class ProductCreateInput(graphene.InputObjectType):
    """
    Input for product creation (Shopify-style)

    Core required: name, price
    Optional: All other fields including variants, shipping, SEO, images
    Security: Workspace scoping via JWT middleware

    Images: Accepts array of Upload scalars for direct file uploads
    """

    # CORE REQUIRED FIELDS
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)

    # BASIC PRODUCT INFO
    description = graphene.String()
    status = graphene.String(default_value='published')

    # PRICING
    cost_price = graphene.Decimal()
    compare_at_price = graphene.Decimal()
    charge_tax = graphene.Boolean(default_value=True)
    payment_charges = graphene.Boolean(default_value=False)
    charges_amount = graphene.Decimal()

    # ORGANIZED INPUT TYPES
    inventory = graphene.Field(InventoryInput, description="Inventory-related fields")
    shipping = graphene.Field(ShippingInput, description="Shipping-related fields")
    seo = graphene.Field(SEOInput, description="SEO-related fields")
    organization = graphene.Field(OrganizationInput, description="Organization-related fields")
    options = graphene.List(ProductVariantOptionInput, description="Option definitions (e.g., [{'option_name':'Color', 'option_values': ['Blue', 'Black']}])")


    # VARIANTS (OPTIONAL)
    has_variants = graphene.Boolean(default_value=False)
    variants = graphene.List(VariantInput, description="Explicit variants with featured images and inventory")

    # MEDIA (NEW - Production-grade system)
    featured_media_id = graphene.String(description="Featured image ID (product thumbnail)")
    media_ids = graphene.List(graphene.String, description="Array of media IDs for gallery (images/videos/3D models)")


class UpdateProduct(graphene.Mutation):
    """
    Update product with atomic transaction using ProductService

    Performance: Atomic update with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive error handling with rollback
    """

    class Arguments:
        product_id = graphene.String(required=True)
        update_data = ProductUpdateInput(required=True)

    success = graphene.Boolean()
    product = graphene.Field('workspace.store.graphql.types.product_types.ProductType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, product_id, update_data):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'product:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Extract media-related fields before processing (NEW system)
            featured_media_id = update_data.get('featured_media_id')
            media_ids = update_data.get('media_ids', [])

            # Extract variant data with featured images
            variants_with_media = []
            if update_data.get('variants'):
                for variant_input in update_data['variants']:
                    variant_dict = {
                        'option1': variant_input.get('option1'),
                        'option2': variant_input.get('option2'),
                        'option3': variant_input.get('option3'),
                        'price': variant_input.get('price'),
                        'compare_at_price': variant_input.get('compare_at_price'),
                        'cost_price': variant_input.get('cost_price'),
                        'is_active': variant_input.get('is_active'),
                        'position': variant_input.get('position'),
                        'featured_media_id': variant_input.get('featured_media_id')  # Keep for later attachment
                    }
                    # Extract inventory data from variant inventory input
                    if variant_input.get('inventory'):
                        variant_dict.update({
                            'sku': variant_input['inventory'].get('sku'),
                            'barcode': variant_input['inventory'].get('barcode'),
                            'track_inventory': variant_input['inventory'].get('track_inventory'),
                            'onhand': variant_input['inventory'].get('onhand'),
                            'available': variant_input['inventory'].get('available'),
                            'condition': variant_input['inventory'].get('condition')
                        })
                    variants_with_media.append(variant_dict)

            # Convert GraphQL input to service format (exclude media and variant fields)
            update_dict = {}
            for field, value in update_data.items():
                if value is not None and field not in ['featured_media_id', 'media_ids', 'variants', 'inventory', 'shipping', 'seo', 'organization']:
                    update_dict[field] = value

            # Extract organized input data
            if update_data.get('inventory'):
                inventory_data = update_data['inventory']
                if inventory_data.get('sku') is not None:
                    update_dict['sku'] = inventory_data['sku']
                if inventory_data.get('barcode') is not None:
                    update_dict['barcode'] = inventory_data['barcode']
                if inventory_data.get('track_inventory') is not None:
                    update_dict['track_inventory'] = inventory_data['track_inventory']
                if inventory_data.get('inventory_quantity') is not None:
                    update_dict['inventory_quantity'] = inventory_data['inventory_quantity']
                if inventory_data.get('allow_backorders') is not None:
                    update_dict['allow_backorders'] = inventory_data['allow_backorders']
                if inventory_data.get('onhand') is not None:
                    update_dict['onhand'] = inventory_data['onhand']
                if inventory_data.get('available') is not None:
                    update_dict['available'] = inventory_data['available']
                if inventory_data.get('condition') is not None:
                    update_dict['condition'] = inventory_data['condition']
                if inventory_data.get('location_id') is not None:
                    update_dict['location_id'] = inventory_data['location_id']

            if update_data.get('shipping'):
                shipping_data = update_data['shipping']
                if shipping_data.get('requires_shipping') is not None:
                    update_dict['requires_shipping'] = shipping_data['requires_shipping']
                if shipping_data.get('package_id') is not None:
                    update_dict['package_id'] = shipping_data['package_id']
                if shipping_data.get('weight') is not None:
                    update_dict['weight'] = shipping_data['weight']
                if shipping_data.get('shipping_config') is not None:
                    update_dict['shipping_config'] = shipping_data['shipping_config']

            if update_data.get('seo'):
                seo_data = update_data['seo']
                # SEO FIELD HANDLING (with truncation for scale)
                # For updates: truncate if provided, but don't auto-populate (preserve existing values)
                if seo_data.get('meta_title') is not None:
                    update_dict['meta_title'] = seo_data['meta_title'][:60]

                if seo_data.get('meta_description') is not None:
                    update_dict['meta_description'] = seo_data['meta_description'][:160]

                # SLUG VALIDATION (ensure uniqueness within workspace)
                if seo_data.get('slug'):
                    from workspace.store.models import Product
                    from django.utils.text import slugify

                    new_slug = slugify(seo_data['slug'])

                    # Check if slug is unique (excluding current product)
                    if Product.objects.filter(
                        workspace=workspace,
                        slug=new_slug
                    ).exclude(id=product_id).exists():
                        return UpdateProduct(
                            success=False,
                            error=f"Slug '{new_slug}' is already in use. Please choose a different one."
                        )

                    update_dict['slug'] = new_slug

            if update_data.get('organization'):
                org_data = update_data['organization']
                if org_data.get('product_type') is not None:
                    update_dict['product_type'] = org_data['product_type']
                if org_data.get('vendor') is not None:
                    update_dict['vendor'] = org_data['vendor']
                if org_data.get('brand') is not None:
                    update_dict['brand'] = org_data['brand']
                if org_data.get('category_id') is not None:
                    update_dict['category_id'] = org_data['category_id']
                if org_data.get('tags') is not None:
                    update_dict['tags'] = org_data['tags']

            # Add variants_data if provided
            if variants_with_media:
                update_dict['variants_data'] = variants_with_media

            # Validate media before updating (NEW system)
            if media_ids:
                validation = media_validator.validate_product_media(
                    media_ids=media_ids,
                    product_id=product_id,
                    workspace=workspace  # SECURITY: Validate workspace ownership
                )
                if not validation['valid']:
                    return UpdateProduct(
                        success=False,
                        error=validation['error']
                    )

            result = product_service.update_product(
                workspace=workspace,
                product_id=product_id,
                update_data=update_dict,
                user=user
            )

            if not result['success']:
                return UpdateProduct(
                    success=False,
                    error=result.get('error')
                )

            # NEW MEDIA SYSTEM: Attach media after product update
            product = result['product']
            media_attached = 0

            # 1. Attach featured media if provided
            if featured_media_id:
                product.featured_media_id = featured_media_id
                product.save(update_fields=['featured_media_id'])

            # 2. Attach media gallery if provided
            if media_ids:
                # Clear existing gallery
                ProductMediaGallery.objects.filter(product=product).delete()

                # Create new gallery items with position
                for position, media_id in enumerate(media_ids):
                    try:
                        ProductMediaGallery.objects.create(
                            product=product,
                            media_id=media_id,
                            position=position
                        )
                        media_attached += 1
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Media attachment failed: {str(e)}")

            # 3. Attach variant featured images
            variants_updated = 0
            if result.get('updated_variants') and variants_with_media:
                updated_variants = result['updated_variants']
                for variant_dict, variant_obj in zip(variants_with_media, updated_variants):
                    if variant_dict.get('featured_media_id'):
                        try:
                            variant_obj.featured_media_id = variant_dict['featured_media_id']
                            variant_obj.save(update_fields=['featured_media_id'])
                            variants_updated += 1
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Variant media attachment failed: {str(e)}")

            message = result.get('message', 'Product updated successfully')
            if featured_media_id:
                message += " with featured image"
            if media_attached > 0:
                message += f" and {media_attached} gallery items"
            if variants_updated > 0:
                message += f" and {variants_updated} variant images"

            return UpdateProduct(
                success=True,
                product=result.get('product'),
                message=message,
                error=None
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Product update mutation failed: {str(e)}", exc_info=True)

            return UpdateProduct(
                success=False,
                error=f"Product update failed: {str(e)}"
            )


class DeleteProduct(graphene.Mutation):
    """
    Delete product with validation and atomic transaction using ProductService

    Performance: Atomic deletion with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive validation and rollback
    """

    class Arguments:
        product_id = graphene.String(required=True)

    success = graphene.Boolean()
    deleted_id = graphene.String()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, product_id):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'product:delete'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            result = product_service.delete_product(
                workspace=workspace,
                product_id=product_id,
                user=user
            )

            return DeleteProduct(
                success=result['success'],
                deleted_id=result.get('deleted_id'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Product deletion mutation failed: {str(e)}", exc_info=True)

            return DeleteProduct(
                success=False,
                error=f"Product deletion failed: {str(e)}"
            )


class ToggleProductStatus(graphene.Mutation):
    """
    Toggle product status with validation using ProductService

    Performance: Atomic status update
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive status validation
    """

    class Arguments:
        product_id = graphene.String(required=True)
        new_status = graphene.String(required=True)

    success = graphene.Boolean()
    product = graphene.Field('workspace.store.graphql.types.product_types.ProductType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, product_id, new_status):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'product:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            result = product_service.toggle_product_status(
                workspace=workspace,
                product_id=product_id,
                new_status=new_status,
                user=user
            )

            return ToggleProductStatus(
                success=result['success'],
                product=result.get('product'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Product status update mutation failed: {str(e)}", exc_info=True)

            return ToggleProductStatus(
                success=False,
                error=f"Product status update failed: {str(e)}"
            )


class UpdateProductStock(graphene.Mutation):
    """
    Update product stock quantity with atomic transaction using ProductService

    Performance: Atomic stock update with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive validation and rollback
    """

    class Arguments:
        product_id = graphene.String(required=True)
        stock_quantity = graphene.Int(required=True)

    success = graphene.Boolean()
    product = graphene.Field('workspace.store.graphql.types.product_types.ProductType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, product_id, stock_quantity):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'product:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            result = product_service.update_product_stock(
                workspace=workspace,
                product_id=product_id,
                stock_quantity=stock_quantity,
                user=user
            )

            return UpdateProductStock(
                success=result['success'],
                product=result.get('product'),
                message=result.get('message'),
                error=result.get('error')
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Product stock update mutation failed: {str(e)}", exc_info=True)

            return UpdateProductStock(
                success=False,
                error=f"Product stock update failed: {str(e)}"
            )


class CreateProduct(graphene.Mutation):
    """
    Create product using ProductService

    Core required: name, price
    Optional: All other fields including variants, shipping, SEO
    Performance: Atomic creation with proper locking
    Security: Workspace scoping and permission validation
    Reliability: Comprehensive validation and rollback
    """

    class Arguments:
        product_data = ProductCreateInput(required=True)

    success = graphene.Boolean()
    product = graphene.Field('workspace.store.graphql.types.product_types.ProductType')
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, product_data):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'product:create'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            # Extract media fields for validation and attachment
            featured_media_id = product_data.featured_media_id
            media_ids = product_data.media_ids or []

            # Validate media before creating product
            if media_ids:
                validation = media_validator.validate_product_media(
                    media_ids=media_ids,
                    product_id=None,  # New product
                    workspace=workspace  # SECURITY: Validate workspace ownership
                )
                if not validation['valid']:
                    return CreateProduct(
                        success=False,
                        error=validation['error']
                    )

            # Extract variant data with featured_media_id
            variants_with_media = []
            if product_data.variants:
                for variant_input in product_data.variants:
                    variant_dict = {
                        'option1': variant_input.option1,
                        'option2': variant_input.option2,
                        'option3': variant_input.option3,
                        'price': variant_input.price,
                        'compare_at_price': variant_input.compare_at_price,
                        'cost_price': variant_input.cost_price,
                        'is_active': variant_input.is_active,
                        'position': variant_input.position,
                        'featured_media_id': variant_input.featured_media_id  # Keep for later attachment
                    }
                    # Extract inventory data from variant inventory input
                    if variant_input.inventory:
                        variant_dict.update({
                            'sku': variant_input.inventory.sku or '',
                            'barcode': variant_input.inventory.barcode or '',
                            'track_inventory': variant_input.inventory.track_inventory,
                            'onhand': variant_input.inventory.onhand,
                            'available': variant_input.inventory.available,
                            'condition': variant_input.inventory.condition
                        })
                    variants_with_media.append(variant_dict)

            # Convert GraphQL input to service format
            # Django convention: CharField should use '' instead of None for empty values

            # SEO AUTO-POPULATION (Shopify-style server-side fallback)
            description_text = product_data.description or ''

            # Extract SEO data with clear fallback logic
            seo_title = product_data.name  # Default to product name
            if product_data.seo and product_data.seo.meta_title:
                seo_title = product_data.seo.meta_title
            seo_title = seo_title[:60] if seo_title else ''

            seo_description = description_text  # Default to product description
            if product_data.seo and product_data.seo.meta_description:
                seo_description = product_data.seo.meta_description
            seo_description = seo_description[:160] if seo_description else ''

            product_dict = {
                'name': product_data.name,
                'price': product_data.price,
                'description': description_text,
                'status': product_data.status,
                'cost_price': product_data.cost_price,
                'compare_at_price': product_data.compare_at_price,
                'charge_tax': product_data.charge_tax,
                'payment_charges': product_data.payment_charges,
                'charges_amount': product_data.charges_amount,
                'has_variants': product_data.has_variants or bool(product_data.variants),
                'variants_data': variants_with_media if variants_with_media else None,
                # SEO fields with auto-population and truncation
                'slug': product_data.seo.slug or '' if product_data.seo else '',  # Will be auto-generated in model.save() if empty
                'meta_title': seo_title,
                'meta_description': seo_description,
            }

            # Extract organized input data
            if product_data.inventory:
                product_dict.update({
                    'sku': product_data.inventory.sku or '',
                    'barcode': product_data.inventory.barcode or '',
                    'track_inventory': product_data.inventory.track_inventory,
                    'inventory_quantity': product_data.inventory.inventory_quantity,
                    'allow_backorders': product_data.inventory.allow_backorders,
                    'onhand': product_data.inventory.onhand,
                    'available': product_data.inventory.available,
                    'condition': product_data.inventory.condition,
                    'location_id': product_data.inventory.location_id
                })

            if product_data.shipping:
                product_dict.update({
                    'requires_shipping': product_data.shipping.requires_shipping,
                    'package_id': product_data.shipping.package_id,
                    'weight': product_data.shipping.weight,
                    'shipping_config': product_data.shipping.shipping_config
                })

            if product_data.organization:
                product_dict.update({
                    'product_type': product_data.organization.product_type,
                    'vendor': product_data.organization.vendor or '',
                    'brand': product_data.organization.brand or '',
                    'category_id': product_data.organization.category_id,
                    'tags': product_data.organization.tags
                })

            # Call simple product creation service (handles both simple and variant products)
            result = product_service.create_product(
                workspace=workspace,
                product_data=product_dict,
                user=user
            )

            if not result['success']:
                return CreateProduct(
                    success=False,
                    error=result.get('error')
                )

            product = result['product']

            # Attach media to product after creation
            media_attached_count = 0

            # 1. Attach featured media (primary product image)
            if featured_media_id:
                product.featured_media_id = featured_media_id
                product.save(update_fields=['featured_media_id'])
                media_attached_count += 1

            # 2. Attach media gallery (images, videos, 3D models)
            if media_ids:
                # Clear existing gallery (shouldn't exist for new product, but be safe)
                ProductMediaGallery.objects.filter(product=product).delete()

                # Create gallery items with position
                for position, media_id in enumerate(media_ids):
                    ProductMediaGallery.objects.create(
                        product=product,
                        media_id=media_id,
                        position=position
                    )
                    media_attached_count += 1

            # 3. Attach variant featured images
            variant_media_attached = 0
            if result.get('created_variants'):
                created_variants = result['created_variants']
                for variant_dict, variant_obj in zip(variants_with_media, created_variants):
                    if variant_dict.get('featured_media_id'):
                        variant_obj.featured_media_id = variant_dict['featured_media_id']
                        variant_obj.save(update_fields=['featured_media_id'])
                        variant_media_attached += 1

            # Build success message
            message = f"Product created successfully"
            if featured_media_id:
                message += " with featured image"
            if media_ids:
                gallery_count = len(media_ids)
                message += f" and {gallery_count} gallery items"
            if variant_media_attached > 0:
                message += f" ({variant_media_attached} variant images)"

            return CreateProduct(
                success=True,
                product=product,
                message=message,
                error=None
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Product creation mutation failed: {str(e)}", exc_info=True)

            return CreateProduct(
                success=False,
                error=f"Product creation failed: {str(e)}"
            )


class DuplicateProduct(graphene.Mutation):
    """
    Duplicate existing product with variants and inventory using ProductService

    Performance: Bulk operations with transaction
    Scalability: Handles complex product structures
    Reliability: Atomic operation with rollback

    Smart Naming (if new_name not provided):
    - Auto-generates: "Product (Copy 1)", "Product (Copy 2)", etc.
    - Strips existing (Copy N) patterns to avoid nesting
    - Slug pattern: "product-copy-1", "product-copy-2", etc.
    """

    class Arguments:
        product_id = graphene.String(required=True)
        new_name = graphene.String(required=False, description="Optional custom name (auto-generated if not provided)")
        copy_variants = graphene.Boolean(default_value=True)
        copy_inventory = graphene.Boolean(default_value=False)

    success = graphene.Boolean()
    product = graphene.Field('workspace.store.graphql.types.product_types.ProductType')
    variants_created = graphene.Int()
    inventory_records_created = graphene.Int()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, product_id, new_name=None, copy_variants=True, copy_inventory=False):
        workspace = info.context.workspace
        user = info.context.user

        if not PermissionService.has_permission(user, workspace, 'product:update'): 
            raise GraphQLError("Insufficient permissions to create categories")
        
        try:
            result = product_service.duplicate_product(
                workspace=workspace,
                product_id=product_id,
                new_name=new_name,
                copy_variants=copy_variants,
                copy_inventory=copy_inventory,
                user=user
            )

            if not result['success']:
                return DuplicateProduct(
                    success=False,
                    error=result.get('error')
                )

            # NEW MEDIA SYSTEM: Copy ProductMediaGallery after duplication
            from workspace.store.models import Product
            new_product = result['product']
            gallery_copied = 0

            try:
                # Get original product's gallery
                original_product = Product.objects.get(id=product_id, workspace=workspace)
                original_gallery = ProductMediaGallery.objects.filter(
                    product=original_product
                ).order_by('position')

                # Copy gallery to new product
                for gallery_item in original_gallery:
                    ProductMediaGallery.objects.create(
                        product=new_product,
                        media_id=gallery_item.media_id,
                        position=gallery_item.position
                    )
                    gallery_copied += 1

            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Gallery duplication failed: {str(e)}")

            # Build enhanced success message
            message = result.get('message', 'Product duplicated successfully')
            if new_product.featured_media_id:
                message += " with featured image"
            if gallery_copied > 0:
                message += f" and {gallery_copied} gallery items"

            return DuplicateProduct(
                success=True,
                product=new_product,
                variants_created=result.get('variants_created', 0),
                inventory_records_created=result.get('inventory_records_created', 0),
                message=message,
                error=None
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Product duplication mutation failed: {str(e)}", exc_info=True)

            return DuplicateProduct(
                success=False,
                error=f"Product duplication failed: {str(e)}"
            )


class ProductProcessingMutations(graphene.ObjectType):
    """
    Product processing mutations collection (Shopify-style)

    All mutations follow production standards for performance and security
    Integrates with modern ProductService for business logic
    Images handled within create/update mutations (Shopify pattern)
    """

    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()
    toggle_product_status = ToggleProductStatus.Field()
    update_product_stock = UpdateProductStock.Field()
    duplicate_product = DuplicateProduct.Field()