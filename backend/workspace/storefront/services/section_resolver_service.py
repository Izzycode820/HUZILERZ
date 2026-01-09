"""
Section Data Resolver Service

Resolves section intent (from puck.data) into actual data for theme rendering.
This layer sits between Puck editor configuration and GraphQL queries.

Security: All inputs validated and sanitized
Performance: Efficient queries with select_related/prefetch_related
Robustness: Graceful error handling, no crashes
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db.models import Q, Prefetch, Count

from workspace.store.models import Product, Category

logger = logging.getLogger(__name__)


class SectionResolverService:
    """
    Theme-agnostic section data resolver

    Maps section data contracts to actual database queries.
    Each contract type has a dedicated resolver function.
    """

    # Maximum limits to prevent abuse/DoS
    MAX_PRODUCTS_PER_SECTION = 50
    MAX_CATEGORIES = 100

    # Standard data contracts - theme agnostic
    SUPPORTED_CONTRACTS = {
        'categoryProducts': 'Fetch products from a category',
        'newProducts': 'Fetch newest products',
        'featuredProducts': 'Fetch featured products',
        'allCategories': 'Fetch all categories with optional product preview',
        'productById': 'Fetch single product by ID',
        'productBySlug': 'Fetch single product by slug',
        'searchProducts': 'Search products by query',
        'featuredCategories': 'Fetch featured categories',
    }

    def __init__(self, workspace):
        """
        Initialize resolver with workspace context

        Args:
            workspace: Workspace model instance (for tenant isolation)
        """
        if not workspace:
            raise ValueError("Workspace is required for section resolver")

        self.workspace = workspace

        # Map contract types to resolver methods
        self._resolver_map: Dict[str, Callable] = {
            'categoryProducts': self._resolve_category_products,
            'newProducts': self._resolve_new_products,
            'featuredProducts': self._resolve_featured_products,
            'allCategories': self._resolve_all_categories,
            'productById': self._resolve_product_by_id,
            'productBySlug': self._resolve_product_by_slug,
            'searchProducts': self._resolve_search_products,
            'featuredCategories': self._resolve_featured_categories,
        }

    def resolve_section(self, section_type: str, section_props: Dict[str, Any],
                       data_contract: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Resolve a single section's data requirements

        Args:
            section_type: Section type name (for logging only, not used for routing)
            section_props: Section properties from puck.data
            data_contract: Data contract specification from puck.config

        Returns:
            Dict containing resolved data for the section

        Raises:
            ValidationError: If contract is invalid or unsupported
        """
        if not data_contract:
            logger.warning(
                f"Section '{section_type}' has no data contract, returning empty data",
                extra={'workspace_id': self.workspace.id, 'section_type': section_type}
            )
            return {}

        contract_resolver = data_contract.get('resolver')

        if not contract_resolver:
            logger.error(
                f"Data contract missing 'resolver' field for section '{section_type}'",
                extra={'workspace_id': self.workspace.id, 'section_type': section_type}
            )
            return {}

        if contract_resolver not in self._resolver_map:
            logger.error(
                f"Unsupported resolver type '{contract_resolver}' for section '{section_type}'",
                extra={
                    'workspace_id': self.workspace.id,
                    'section_type': section_type,
                    'resolver': contract_resolver,
                    'supported_resolvers': list(self._resolver_map.keys())
                }
            )
            return {}

        # Get resolver function
        resolver_func = self._resolver_map[contract_resolver]

        try:
            # Resolve data
            resolved_data = resolver_func(section_props)

            logger.info(
                f"Successfully resolved section data",
                extra={
                    'workspace_id': self.workspace.id,
                    'section_type': section_type,
                    'resolver': contract_resolver,
                    'data_size': len(str(resolved_data))
                }
            )

            return resolved_data

        except ValidationError as e:
            logger.warning(
                f"Validation error resolving section '{section_type}': {str(e)}",
                extra={
                    'workspace_id': self.workspace.id,
                    'section_type': section_type,
                    'resolver': contract_resolver,
                    'error': str(e)
                }
            )
            return {'error': 'Invalid section configuration'}

        except Exception as e:
            logger.error(
                f"Unexpected error resolving section '{section_type}': {str(e)}",
                extra={
                    'workspace_id': self.workspace.id,
                    'section_type': section_type,
                    'resolver': contract_resolver,
                },
                exc_info=True
            )
            # Graceful degradation - return empty data, don't crash
            return {}

    def _validate_limit(self, limit: Any, max_limit: int) -> int:
        """
        Validate and sanitize limit parameter

        Args:
            limit: User-provided limit
            max_limit: Maximum allowed limit

        Returns:
            Validated integer limit
        """
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 10  # Default

        # Clamp to safe range
        limit = max(1, min(limit, max_limit))

        return limit

    def _validate_slug(self, slug: str, field_name: str = 'slug') -> str:
        """
        Validate slug format to prevent injection attacks

        Args:
            slug: User-provided slug
            field_name: Field name for error messages

        Returns:
            Validated slug

        Raises:
            ValidationError: If slug is invalid
        """
        if not slug or not isinstance(slug, str):
            raise ValidationError(f"{field_name} is required and must be a string")

        # Django's slug validator (alphanumeric, hyphens, underscores only)
        try:
            validate_slug(slug)
        except ValidationError:
            raise ValidationError(f"{field_name} contains invalid characters")

        # Additional length check
        if len(slug) > 200:
            raise ValidationError(f"{field_name} is too long (max 200 characters)")

        return slug.lower().strip()

    def _get_base_product_queryset(self):
        """
        Get optimized base queryset for products

        Performance optimizations:
        - select_related for category (avoid N+1)
        - prefetch_related for media (avoid N+1)
        - Filter published and active only
        - Workspace isolation enforced

        Returns:
            Optimized Product queryset
        """
        return Product.objects.filter(
            workspace=self.workspace,
            status='published',
            is_active=True
        ).select_related(
            'category'
        ).prefetch_related(
            'media_gallery'
        ).only(
            # Limit fields to reduce memory usage
            'id', 'name', 'slug', 'price', 'compare_at_price',
            'category__name', 'category__slug',
            'created_at', 'updated_at'
        )

    def _serialize_product(self, product) -> Dict[str, Any]:
        """
        Serialize product model to dict for GraphQL response

        Args:
            product: Product model instance

        Returns:
            Serialized product dict
        """
        media_gallery = product.media_gallery.all()

        return {
            'id': str(product.id),
            'name': product.name,
            'slug': product.slug,
            'price': str(product.price),
            'compareAtPrice': str(product.compare_at_price) if product.compare_at_price else None,
            'mediaUploads': [
                {
                    'optimizedWebp': media.file_url if media.file_url else None,
                    'thumbnailWebp': media.file_url if media.file_url else None,
                }
                for media in media_gallery[:1]  # Only first image for performance
            ] if media_gallery else []
        }

    def _resolve_category_products(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve products from a specific category

        Contract props:
            - categorySlug (str): Category slug (REQUIRED)
            - limit (int): Max products to return

        Returns:
            Dict with 'products' list
        """
        # Contract-level validation - fail fast if required fields missing
        if 'categorySlug' not in props:
            raise ValidationError("categorySlug is required for categoryProducts contract")

        category_slug = self._validate_slug(props.get('categorySlug', ''), 'categorySlug')
        limit = self._validate_limit(props.get('limit', 10), self.MAX_PRODUCTS_PER_SECTION)

        try:
            # Fetch products with optimized query
            products = self._get_base_product_queryset().filter(
                category__slug=category_slug
            ).order_by('-created_at')[:limit]

            products_list = list(products)  # Execute query once

            logger.debug(
                f"Resolved category products",
                extra={
                    'workspace_id': self.workspace.id,
                    'category_slug': category_slug,
                    'limit': limit,
                    'found': len(products_list)
                }
            )

            return {
                'products': [self._serialize_product(p) for p in products_list]
            }

        except Exception as e:
            logger.error(
                f"Error fetching category products: {str(e)}",
                extra={
                    'workspace_id': self.workspace.id,
                    'category_slug': category_slug
                },
                exc_info=True
            )
            # Graceful degradation
            return {'products': []}

    def _resolve_new_products(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve newest products

        Contract props:
            - limit (int): Max products to return

        Returns:
            Dict with 'products' list
        """
        limit = self._validate_limit(props.get('limit', 12), self.MAX_PRODUCTS_PER_SECTION)

        try:
            products = self._get_base_product_queryset().order_by('-created_at')[:limit]

            products_list = list(products)

            logger.debug(
                f"Resolved new products",
                extra={
                    'workspace_id': self.workspace.id,
                    'limit': limit,
                    'found': len(products_list)
                }
            )

            return {
                'products': [self._serialize_product(p) for p in products_list]
            }

        except Exception as e:
            logger.error(
                f"Error fetching new products: {str(e)}",
                extra={'workspace_id': self.workspace.id},
                exc_info=True
            )
            return {'products': []}

    def _resolve_featured_products(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve featured products

        Contract props:
            - limit (int): Max products to return

        Returns:
            Dict with 'products' list
        """
        limit = self._validate_limit(props.get('limit', 8), self.MAX_PRODUCTS_PER_SECTION)

        try:
            # Assuming you have a 'featured' field or category
            # Adjust based on your actual Product model
            products = self._get_base_product_queryset().filter(
                # Add your featured logic here, e.g.:
                # is_featured=True
                # OR category__slug='featured'
                category__slug='featured'
            ).order_by('-created_at')[:limit]

            products_list = list(products)

            logger.debug(
                f"Resolved featured products",
                extra={
                    'workspace_id': self.workspace.id,
                    'limit': limit,
                    'found': len(products_list)
                }
            )

            return {
                'products': [self._serialize_product(p) for p in products_list]
            }

        except Exception as e:
            logger.error(
                f"Error fetching featured products: {str(e)}",
                extra={'workspace_id': self.workspace.id},
                exc_info=True
            )
            return {'products': []}

    def _resolve_all_categories(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve all categories with optional product preview

        Contract props:
            - productsLimit (int): Products per category for preview

        Returns:
            Dict with 'categories' list
        """
        products_limit = self._validate_limit(
            props.get('productsLimit', 4),
            20  # Max products per category
        )

        try:
            # Fetch categories with product preview
            categories = Category.objects.filter(
                workspace=self.workspace,
                is_visible=True
            ).select_related(
                'featured_media'  # Include category featured image
            ).prefetch_related(
                Prefetch(
                    'products',
                    queryset=Product.objects.filter(
                        status='published',
                        is_active=True
                    ).select_related('category').prefetch_related('media_gallery')[:products_limit],
                    to_attr='preview_products'
                )
            )[:self.MAX_CATEGORIES]

            categories_list = list(categories)

            logger.debug(
                f"Resolved categories",
                extra={
                    'workspace_id': self.workspace.id,
                    'found': len(categories_list)
                }
            )

            return {
                'categories': [
                    {
                        'id': str(cat.id),
                        'name': cat.name,
                        'slug': cat.slug,
                        'image': cat.featured_media.file_url if cat.featured_media else None,
                        'products': [
                            self._serialize_product(p) for p in cat.preview_products
                        ]
                    }
                    for cat in categories_list
                ]
            }

        except Exception as e:
            logger.error(
                f"Error fetching categories: {str(e)}",
                extra={'workspace_id': self.workspace.id},
                exc_info=True
            )
            return {'categories': []}

    def _resolve_product_by_id(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve single product by ID

        Contract props:
            - productId (str): Product ID (REQUIRED)

        Returns:
            Dict with 'product' object or None
        """
        # Contract-level validation - fail fast if required fields missing
        if 'productId' not in props or not props.get('productId'):
            raise ValidationError("productId is required for productById contract")

        product_id = props.get('productId')

        try:
            product = self._get_base_product_queryset().get(id=product_id)

            return {
                'product': self._serialize_product(product)
            }

        except Product.DoesNotExist:
            logger.warning(
                f"Product not found",
                extra={
                    'workspace_id': self.workspace.id,
                    'product_id': product_id
                }
            )
            return {'product': None}

        except Exception as e:
            logger.error(
                f"Error fetching product by ID: {str(e)}",
                extra={
                    'workspace_id': self.workspace.id,
                    'product_id': product_id
                },
                exc_info=True
            )
            return {'product': None}

    def _resolve_product_by_slug(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve single product by slug

        Contract props:
            - productSlug (str): Product slug (REQUIRED)

        Returns:
            Dict with 'product' object or None
        """
        # Contract-level validation - fail fast if required fields missing
        if 'productSlug' not in props:
            raise ValidationError("productSlug is required for productBySlug contract")

        product_slug = self._validate_slug(props.get('productSlug', ''), 'productSlug')

        try:
            product = self._get_base_product_queryset().get(slug=product_slug)

            return {
                'product': self._serialize_product(product)
            }

        except Product.DoesNotExist:
            logger.warning(
                f"Product not found",
                extra={
                    'workspace_id': self.workspace.id,
                    'product_slug': product_slug
                }
            )
            return {'product': None}

        except Exception as e:
            logger.error(
                f"Error fetching product by slug: {str(e)}",
                extra={
                    'workspace_id': self.workspace.id,
                    'product_slug': product_slug
                },
                exc_info=True
            )
            return {'product': None}

    def _resolve_search_products(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve products by search query

        Contract props:
            - query (str): Search query (REQUIRED, min 2 chars)
            - limit (int): Max products to return

        Returns:
            Dict with 'products' list
        """
        # Contract-level validation - fail fast if required fields missing
        if 'query' not in props:
            raise ValidationError("query is required for searchProducts contract")

        query = props.get('query', '').strip()
        limit = self._validate_limit(props.get('limit', 20), self.MAX_PRODUCTS_PER_SECTION)

        if not query or len(query) < 2:
            raise ValidationError("query must be at least 2 characters for searchProducts contract")

        # Sanitize query (prevent injection)
        if len(query) > 200:
            query = query[:200]

        try:
            products = self._get_base_product_queryset().filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__icontains=query)
            ).order_by('-created_at')[:limit]

            products_list = list(products)

            logger.debug(
                f"Resolved search products",
                extra={
                    'workspace_id': self.workspace.id,
                    'query': query,
                    'limit': limit,
                    'found': len(products_list)
                }
            )

            return {
                'products': [self._serialize_product(p) for p in products_list]
            }

        except Exception as e:
            logger.error(
                f"Error searching products: {str(e)}",
                extra={
                    'workspace_id': self.workspace.id,
                    'query': query
                },
                exc_info=True
            )
            return {'products': []}

    def _resolve_featured_categories(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve featured categories

        Contract props:
            - limit (int): Max categories to return

        Returns:
            Dict with 'categories' list
        """
        limit = self._validate_limit(props.get('limit', 6), self.MAX_CATEGORIES)

        try:
            # Fetch featured categories
            categories = Category.objects.filter(
                workspace=self.workspace,
                is_visible=True,
                is_featured=True
            ).select_related(
                'featured_media'
            ).annotate(
                items_count=Count(
                    'products',
                    filter=Q(products__is_active=True, products__status='published')
                )
            ).order_by('sort_order', 'name')[:limit]

            categories_list = list(categories)

            logger.debug(
                f"Resolved featured categories",
                extra={
                    'workspace_id': self.workspace.id,
                    'limit': limit,
                    'found': len(categories_list)
                }
            )

            return {
                'categories': [
                    {
                        'id': str(cat.id),
                        'name': cat.name,
                        'slug': cat.slug,
                        'image': cat.featured_media.file_url if cat.featured_media else None,
                        'productCount': cat.items_count
                    }
                    for cat in categories_list
                ]
            }

        except Exception as e:
            logger.error(
                f"Error fetching featured categories: {str(e)}",
                extra={'workspace_id': self.workspace.id},
                exc_info=True
            )
            return {'categories': []}
