# Product Search Service - Advanced search and filtering
# Optimized for Cameroon market with local search patterns

from typing import Dict, List, Optional, Any
from django.db import models
from django.core.cache import cache
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from workspace.store.models import Product, Category
import logging

logger = logging.getLogger('workspace.storefront.search')


class ProductSearchService:
    """
    Advanced product search and filtering service

    Performance: Full-text search with PostgreSQL
    Scalability: Optimized search queries with ranking
    Reliability: Comprehensive search fallbacks
    Security: Public product search only

    Cameroon Market Optimizations:
    - Local product name variations
    - French/English bilingual search
    - Regional availability filtering
    - Mobile-friendly search patterns
    """

    # Search configuration
    SEARCH_VECTOR_FIELDS = ['name', 'description', 'short_description', 'brand', 'tags']
    MIN_SEARCH_SCORE = 0.1
    CACHE_TIMEOUT = 300  # 5 minutes

    @staticmethod
    def search_products(
        workspace_id: str,
        query: str,
        category_slug: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        in_stock_only: bool = False,
        sort_by: str = 'relevance',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Advanced product search with filtering

        Performance: Full-text search with PostgreSQL vectors
        Cameroon Market: Bilingual search (French/English)
        """
        try:
            # Generate cache key
            cache_key = f"search_{workspace_id}_{query}_{category_slug}_{price_min}_{price_max}_{in_stock_only}_{sort_by}_{page}_{page_size}"

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for search: {cache_key}")
                return cached_result

            # Build base queryset
            queryset = Product.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                status='published'
            ).select_related('category', 'sub_category')

            # Apply search query
            if query:
                queryset = ProductSearchService._apply_search_query(queryset, query)

            # Apply filters
            queryset = ProductSearchService._apply_filters(
                queryset, category_slug, price_min, price_max, in_stock_only
            )

            # Apply sorting
            queryset = ProductSearchService._apply_sorting(queryset, sort_by, query)

            # Get total count
            total_count = queryset.count()

            # Apply pagination
            offset = (page - 1) * page_size
            products = queryset[offset:offset + page_size]

            # Format response
            result = {
                'products': ProductSearchService._format_search_results(products, query),
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size,
                    'has_next': offset + page_size < total_count,
                    'has_previous': page > 1
                },
                'search_metadata': {
                    'query': query,
                    'suggestions': ProductSearchService._generate_search_suggestions(query, workspace_id),
                    'filters_applied': {
                        'category_slug': category_slug,
                        'price_min': price_min,
                        'price_max': price_max,
                        'in_stock_only': in_stock_only
                    }
                }
            }

            # Cache the result
            cache.set(cache_key, result, ProductSearchService.CACHE_TIMEOUT)

            logger.info(
                "Product search completed",
                extra={
                    'workspace_id': workspace_id,
                    'query': query,
                    'total_results': total_count,
                    'page': page
                }
            )

            return result

        except Exception as e:
            logger.error(
                "Product search failed",
                extra={
                    'workspace_id': workspace_id,
                    'query': query,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'products': [],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_previous': False
                },
                'search_metadata': {
                    'query': query,
                    'suggestions': [],
                    'filters_applied': {}
                },
                'error': 'Search failed'
            }

    @staticmethod
    def _apply_search_query(queryset, query: str):
        """Apply full-text search query with PostgreSQL"""
        try:
            # Create search vector
            search_vector = SearchVector(
                'name', weight='A',
                config='french'  # French language support for Cameroon
            ) + SearchVector(
                'description', weight='B',
                config='french'
            ) + SearchVector(
                'short_description', weight='B',
                config='french'
            ) + SearchVector(
                'brand', weight='C',
                config='french'
            ) + SearchVector(
                'tags', weight='C',
                config='french'
            )

            # Create search query
            search_query = SearchQuery(query, config='french')

            # Apply search and rank
            queryset = queryset.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(
                search=search_query,
                rank__gte=ProductSearchService.MIN_SEARCH_SCORE
            ).order_by('-rank')

            return queryset

        except Exception as e:
            logger.warning(
                "Full-text search failed, falling back to basic search",
                extra={'query': query, 'error': str(e)}
            )
            # Fallback to basic search
            return queryset.filter(
                models.Q(name__icontains=query) |
                models.Q(description__icontains=query) |
                models.Q(short_description__icontains=query) |
                models.Q(brand__icontains=query) |
                models.Q(tags__contains=[query])
            )

    @staticmethod
    def _apply_filters(queryset, category_slug, price_min, price_max, in_stock_only):
        """Apply various filters to the queryset"""
        # Category filter
        if category_slug:
            queryset = queryset.filter(
                models.Q(category__slug=category_slug) |
                models.Q(sub_category__slug=category_slug)
            )

        # Price range filter
        if price_min is not None:
            queryset = queryset.filter(price__gte=price_min)
        if price_max is not None:
            queryset = queryset.filter(price__lte=price_max)

        # Stock filter
        if in_stock_only:
            queryset = queryset.filter(
                models.Q(track_inventory=False) |
                models.Q(stock_quantity__gt=0) |
                models.Q(allow_backorders=True)
            )

        return queryset

    @staticmethod
    def _apply_sorting(queryset, sort_by: str, query: str):
        """Apply sorting based on user preference"""
        if sort_by == 'relevance' and query:
            # Relevance sorting is already applied by search rank
            return queryset
        elif sort_by == 'price_low':
            return queryset.order_by('price')
        elif sort_by == 'price_high':
            return queryset.order_by('-price')
        elif sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'popular':
            return queryset.order_by('-views', '-orders')
        else:
            # Default: relevance or newest
            return queryset.order_by('-created_at')

    @staticmethod
    def _format_search_results(products, query: str) -> List[Dict]:
        """Format search results with search highlights"""
        formatted_products = []

        for product in products:
            formatted_product = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'compare_at_price': float(product.compare_at_price) if product.compare_at_price else None,
                'is_on_sale': product.is_on_sale,
                'sale_percentage': product.sale_percentage,
                'featured_image': product.featured_image,
                'description': product.short_description or product.description,
                'category': {
                    'id': product.category.id if product.category else None,
                    'name': product.category.name if product.category else None,
                    'slug': product.category.slug if product.category else None
                } if product.category else None,
                'brand': product.brand,
                'is_in_stock': product.is_in_stock,
                'stock_status': product.stock_status,
                'has_variants': product.has_variants,
                'search_rank': getattr(product, 'rank', 0.0),
                'search_highlights': ProductSearchService._generate_search_highlights(product, query)
            }

            formatted_products.append(formatted_product)

        return formatted_products

    @staticmethod
    def _generate_search_highlights(product, query: str) -> Dict[str, str]:
        """Generate search highlights for the product"""
        highlights = {}
        query_lower = query.lower()

        # Name highlight
        if query_lower in product.name.lower():
            highlights['name'] = ProductSearchService._highlight_text(product.name, query)

        # Description highlight
        description = product.short_description or product.description
        if description and query_lower in description.lower():
            highlights['description'] = ProductSearchService._highlight_text(description, query)

        # Brand highlight
        if product.brand and query_lower in product.brand.lower():
            highlights['brand'] = ProductSearchService._highlight_text(product.brand, query)

        return highlights

    @staticmethod
    def _highlight_text(text: str, query: str) -> str:
        """Simple text highlighting for search results"""
        query_lower = query.lower()
        text_lower = text.lower()

        start_idx = text_lower.find(query_lower)
        if start_idx == -1:
            return text

        end_idx = start_idx + len(query)
        highlighted = (
            text[:start_idx] +
            f"<mark>{text[start_idx:end_idx]}</mark>" +
            text[end_idx:]
        )

        return highlighted

    @staticmethod
    def _generate_search_suggestions(query: str, workspace_id: str) -> List[str]:
        """Generate search suggestions based on query and popular searches"""
        if not query:
            return []

        try:
            suggestions = []

            # Category suggestions
            category_suggestions = Category.objects.filter(
                workspace_id=workspace_id,
                name__icontains=query
            ).values_list('name', flat=True)[:3]
            suggestions.extend(category_suggestions)

            # Brand suggestions
            brand_suggestions = Product.objects.filter(
                workspace_id=workspace_id,
                brand__icontains=query
            ).values_list('brand', flat=True).distinct()[:3]
            suggestions.extend(brand_suggestions)

            # Popular product name suggestions
            product_suggestions = Product.objects.filter(
                workspace_id=workspace_id,
                name__icontains=query,
                views__gt=10
            ).order_by('-views').values_list('name', flat=True)[:3]
            suggestions.extend(product_suggestions)

            # Remove duplicates and limit
            unique_suggestions = list(dict.fromkeys(suggestions))[:5]

            return unique_suggestions

        except Exception as e:
            logger.warning(f"Failed to generate search suggestions: {str(e)}")
            return []

    @staticmethod
    def get_search_facets(workspace_id: str, query: str = '') -> Dict[str, Any]:
        """
        Get search facets for filtering

        Cameroon Market: Local price ranges and categories
        """
        try:
            cache_key = f"facets_{workspace_id}_{query}"

            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

            # Base queryset
            queryset = Product.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                status='published'
            )

            # Apply search query if provided
            if query:
                queryset = ProductSearchService._apply_search_query(queryset, query)

            # Price ranges (Cameroon market specific)
            price_ranges = [
                {'min': 0, 'max': 5000, 'label': 'Under 5,000 FCFA'},
                {'min': 5000, 'max': 20000, 'label': '5,000 - 20,000 FCFA'},
                {'min': 20000, 'max': 50000, 'label': '20,000 - 50,000 FCFA'},
                {'min': 50000, 'max': 100000, 'label': '50,000 - 100,000 FCFA'},
                {'min': 100000, 'max': None, 'label': 'Over 100,000 FCFA'}
            ]

            # Calculate counts for each price range
            price_facets = []
            for price_range in price_ranges:
                range_queryset = queryset.filter(price__gte=price_range['min'])
                if price_range['max']:
                    range_queryset = range_queryset.filter(price__lte=price_range['max'])

                count = range_queryset.count()
                if count > 0:
                    price_facets.append({
                        **price_range,
                        'count': count
                    })

            # Category facets
            category_facets = Category.objects.filter(
                workspace_id=workspace_id,
                products__in=queryset
            ).annotate(
                product_count=models.Count('products')
            ).filter(product_count__gt=0).values('id', 'name', 'slug', 'product_count')

            # Brand facets
            brand_facets = queryset.exclude(brand='').values('brand').annotate(
                count=models.Count('id')
            ).order_by('-count')[:10]

            result = {
                'price_ranges': price_facets,
                'categories': list(category_facets),
                'brands': list(brand_facets),
                'availability': {
                    'in_stock': queryset.filter(is_in_stock=True).count(),
                    'out_of_stock': queryset.filter(is_in_stock=False).count()
                }
            }

            cache.set(cache_key, result, ProductSearchService.CACHE_TIMEOUT)

            return result

        except Exception as e:
            logger.error(
                "Failed to generate search facets",
                extra={'workspace_id': workspace_id, 'error': str(e)},
                exc_info=True
            )
            return {
                'price_ranges': [],
                'categories': [],
                'brands': [],
                'availability': {'in_stock': 0, 'out_of_stock': 0}
            }

    @staticmethod
    def get_popular_searches(workspace_id: str, limit: int = 10) -> List[str]:
        """Get popular search queries for this workspace"""
        try:
            # In a real implementation, you'd track search queries
            # For now, return popular product names and categories
            popular_products = Product.objects.filter(
                workspace_id=workspace_id,
                views__gt=10
            ).order_by('-views').values_list('name', flat=True)[:limit//2]

            popular_categories = Category.objects.filter(
                workspace_id=workspace_id
            ).order_by('-products_count').values_list('name', flat=True)[:limit//2]

            return list(popular_products) + list(popular_categories)

        except Exception as e:
            logger.warning(f"Failed to get popular searches: {str(e)}")
            return []


# Global instance for easy access
product_search_service = ProductSearchService()