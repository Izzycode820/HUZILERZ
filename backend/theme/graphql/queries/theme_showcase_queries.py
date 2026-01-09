"""
Theme Showcase GraphQL Queries - PUBLIC ACCESS

Browse theme store without authentication
Users can view themes before signing up (Shopify pattern)
"""

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from ..types.theme_showcase_types import ThemeType, ThemeDetailsType
from theme.models import Template


class ThemeFilterSet(django_filters.FilterSet):
    """
    FilterSet for public theme browsing

    Security: Only exposes safe, public fields
    Performance: Indexed fields for fast filtering
    Pattern: Matches CategoryFilterSet - no choice fields to avoid enum generation
    """
    class Meta:
        model = Template
        fields = {
            'name': ['icontains'],
            'slug': ['exact'],
        }


class ThemeShowcaseQueries(graphene.ObjectType):
    """
    Public theme store queries

    Security: No authentication required (public marketplace)
    Performance: Pagination + optimized queries
    Pattern: Matches CategoryQueries approach
    """

    themes = DjangoFilterConnectionField(
        ThemeType,
        filterset_class=ThemeFilterSet,
        # Add manual String arguments for choice fields to avoid enum generation
        template_type=graphene.String(),
        price_tier=graphene.String(),
        description="Browse theme store with pagination and filtering (PUBLIC)"
    )

    theme_details = graphene.Field(
        ThemeDetailsType,
        slug=graphene.String(required=True),
        description="Get detailed theme information by slug (PUBLIC)"
    )

    def resolve_themes(self, info, **kwargs):
        """
        Resolve themes for public browsing

        Security: Only shows active, published themes
        Performance: Optimized query with field selection
        Pattern: Manual filtering for choice fields (template_type, price_tier)
        """
        # Start with active themes
        queryset = Template.objects.filter(status='active')

        # Apply manual filters for choice fields (to avoid enum auto-generation)
        if kwargs.get('template_type'):
            queryset = queryset.filter(template_type=kwargs['template_type'])

        if kwargs.get('price_tier'):
            queryset = queryset.filter(price_tier=kwargs['price_tier'])

        # Optimize query with field selection
        return queryset.only(
            'id', 'name', 'slug', 'description',
            'template_type', 'price_tier', 'price_amount',
            'version', 'status',
            'preview_image', 'demo_url',
            'view_count', 'download_count', 'active_usage_count',
            'created_at', 'updated_at'
        ).order_by('-active_usage_count', '-created_at')

    def resolve_theme_details(self, info, slug):
        """
        Resolve detailed theme by slug

        Security: Only shows active themes
        Performance: Single query with view count increment
        """
        try:
            theme = Template.objects.get(
                slug=slug,
                status='active'
            )

            # Increment view count (analytics)
            theme.increment_view_count()

            return theme

        except Template.DoesNotExist:
            raise GraphQLError(f"Theme with slug '{slug}' not found")
