from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Avg, F
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.utils import timezone
from datetime import timedelta
from ..models import Template, TemplateCategory
import logging

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for template business logic with error handling"""

    @staticmethod
    def get_templates_with_filters(
        category_id=None,
        template_type=None,
        price_tier=None,
        workspace_type=None,
        search_query=None,
        sort_by='created_at',
        sort_order='desc',
        limit=20,
        offset=0
    ):
        """
        Get templates with filtering, sorting, and pagination
        Industry Standard: Optimized queries with proper field selection

        Args:
            category_id: Filter by category ID
            template_type: Filter by template type
            price_tier: Filter by price tier
            workspace_type: Filter by workspace type
            search_query: Search in name and description
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            limit: Number of records to return
            offset: Number of records to skip

        Returns:
            QuerySet of Template instances

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting templates with filters: category={category_id}, type={template_type}, search={search_query}")

            # Build query with performance optimization - only select needed fields
            queryset = Template.objects.filter(status='active')

            # Apply filters with proper indexing
            if category_id:
                queryset = queryset.filter(categories__id=category_id)

            if template_type:
                queryset = queryset.filter(template_type=template_type)

            if price_tier:
                queryset = queryset.filter(price_tier=price_tier)

            if workspace_type:
                queryset = queryset.filter(workspace_types__contains=[workspace_type])

            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query)
                )

            # Apply sorting with validation
            valid_sort_fields = ['created_at', 'name', 'view_count', 'download_count', 'price_amount']
            if sort_by not in valid_sort_fields:
                sort_by = 'created_at'

            if sort_order == 'desc':
                sort_field = f'-{sort_by}'
            else:
                sort_field = sort_by

            queryset = queryset.order_by(sort_field)

            # Apply pagination with field optimization - only select fields needed for listing
            paginated_queryset = queryset.only(
                'id', 'name', 'slug', 'description', 'template_type', 'price_tier',
                'price_amount', 'view_count', 'download_count', 'active_usage_count',
                'preview_image', 'demo_url', 'version', 'created_at', 'updated_at'
            )[offset:offset + limit]

            logger.info(f"Retrieved {paginated_queryset.count()} templates with applied filters")
            return paginated_queryset

        except Exception as e:
            logger.error(f"Error getting templates with filters: {e}")
            raise ValidationError("Error retrieving templates")

    @staticmethod
    def get_template_detail(template_id):
        """
        Get detailed template information with related data
        Industry Standard: Proper error handling and performance optimization

        Args:
            template_id: ID of template

        Returns:
            Template instance with related data

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting detailed information for template {template_id}")

            # Validate inputs
            if not template_id:
                logger.warning("Template ID is required")
                raise ValidationError("Template ID is required")

            # Get template with related data for performance - use select_related
            # Exclude puck_config and puck_data (only for authenticated users after adding to library)
            template = Template.objects.filter(
                id=template_id,
                status='active'
            ).select_related(
                'created_by'
            ).only(
                # All metadata fields EXCEPT puck_config and puck_data
                'id', 'name', 'slug', 'description',
                'template_type', 'workspace_types',
                'price_tier', 'price_amount',
                'version', 'status',
                'preview_image', 'demo_url',
                'features', 'tags', 'compatibility',
                'author', 'license',
                'view_count', 'download_count', 'active_usage_count',
                'created_at', 'updated_at', 'created_by'
            ).first()

            if not template:
                logger.warning(f"Template {template_id} not found or not published")
                raise ValidationError("Template not found or not available")

            # Increment view count atomically
            template.increment_view_count()

            logger.info(f"Successfully retrieved template {template_id}")
            return template

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting template detail {template_id}: {e}")
            raise ValidationError("Error retrieving template details")


    @staticmethod
    def get_template_categories(template_type=None, is_featured=None, is_active=True):
        """
        Get template categories with filtering

        Args:
            template_type: Filter by template type
            is_featured: Filter by featured status
            is_active: Filter by active status

        Returns:
            QuerySet of TemplateCategory instances

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting template categories: type={template_type}, featured={is_featured}")

            queryset = TemplateCategory.objects.filter(is_active=is_active)

            # Apply filters
            if template_type:
                queryset = queryset.filter(template_type=template_type)

            if is_featured is not None:
                queryset = queryset.filter(is_featured=is_featured)

            # Order by sort order
            queryset = queryset.order_by('sort_order', 'name')

            logger.info(f"Retrieved {queryset.count()} template categories")
            return queryset

        except Exception as e:
            logger.error(f"Error getting template categories: {e}")
            raise ValidationError("Error retrieving template categories")

    
    @staticmethod
    def search_templates(
        search_query=None,
        category_ids=None,
        template_types=None,
        price_tiers=None,
        workspace_types=None,
        min_downloads=None,
        sort_by='relevance',
        sort_order='desc',
        limit=20,
        offset=0
    ):
        """
        Search templates with advanced filtering and ranking

        Args:
            search_query: Text search query
            category_ids: List of category IDs to filter
            template_types: List of template types to filter
            price_tiers: List of price tiers to filter
            workspace_types: List of workspace types to filter
            min_downloads: Minimum download count
            sort_by: Field to sort by (relevance, downloads, created_at, price, popularity)
            sort_order: 'asc' or 'desc'
            limit: Number of records to return
            offset: Number of records to skip

        Returns:
            QuerySet of Template instances with search ranking

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Searching templates: query='{search_query}', categories={category_ids}, types={template_types}")

            # Build base query with performance optimization
            queryset = Template.objects.filter(status='active')

            # Apply text search with PostgreSQL full-text search
            if search_query:
                # Use PostgreSQL search vectors for better performance
                search_vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
                search_query_obj = SearchQuery(search_query)

                queryset = queryset.annotate(
                    search_rank=SearchRank(search_vector, search_query_obj)
                ).filter(search_rank__gte=0.1)

            # Apply category filters
            if category_ids:
                queryset = queryset.filter(categories__id__in=category_ids)

            # Apply template type filters
            if template_types:
                queryset = queryset.filter(template_type__in=template_types)

            # Apply price tier filters
            if price_tiers:
                queryset = queryset.filter(price_tier__in=price_tiers)

            # Apply workspace type filters
            if workspace_types:
                workspace_q = Q()
                for ws_type in workspace_types:
                    workspace_q |= Q(workspace_types__contains=[ws_type])
                queryset = queryset.filter(workspace_q)

            # Apply download count filter
            if min_downloads:
                queryset = queryset.filter(download_count__gte=min_downloads)

            # Apply sorting
            valid_sort_fields = {
                'relevance': 'search_rank' if search_query else '-view_count',
                'downloads': 'download_count',
                'created_at': 'created_at',
                'price': 'price_amount',
                'popularity': '-view_count'
            }

            sort_field = valid_sort_fields.get(sort_by, '-view_count')
            if sort_order == 'desc' and not sort_field.startswith('-'):
                sort_field = f'-{sort_field}'
            elif sort_order == 'asc' and sort_field.startswith('-'):
                sort_field = sort_field[1:]

            queryset = queryset.order_by(sort_field)

            # Apply pagination with field optimization - exclude large JSON fields for performance
            paginated_queryset = queryset.only(
                'id', 'name', 'slug', 'description', 'template_type', 'price_tier',
                'price_amount', 'view_count', 'download_count', 'active_usage_count',
                'preview_image', 'demo_url', 'version', 'created_at', 'updated_at'
            )[offset:offset + limit]

            logger.info(f"Found {paginated_queryset.count()} templates matching search criteria")
            return paginated_queryset

        except Exception as e:
            logger.error(f"Error searching templates: {e}")
            raise ValidationError("Error performing template search")

    @staticmethod
    def get_templates_count(
        category_id=None,
        template_type=None,
        price_tier=None,
        workspace_type=None,
        search_query=None
    ):
        """
        Get total count of templates matching filters for pagination

        Args:
            category_id: Filter by category ID
            template_type: Filter by template type
            price_tier: Filter by price tier
            workspace_type: Filter by workspace type
            search_query: Search in name and description

        Returns:
            Integer count of matching templates

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting templates count with filters: category={category_id}, type={template_type}, search={search_query}")

            # Build query with same filters as get_templates_with_filters
            queryset = Template.objects.filter(status='active')

            # Apply filters
            if category_id:
                queryset = queryset.filter(categories__id=category_id)

            if template_type:
                queryset = queryset.filter(template_type=template_type)

            if price_tier:
                queryset = queryset.filter(price_tier=price_tier)

            if workspace_type:
                queryset = queryset.filter(workspace_types__contains=[workspace_type])

            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query)
                )

            count = queryset.count()
            logger.info(f"Found {count} templates matching filters")
            return count

        except Exception as e:
            logger.error(f"Error getting templates count: {e}")
            raise ValidationError("Error retrieving templates count")


