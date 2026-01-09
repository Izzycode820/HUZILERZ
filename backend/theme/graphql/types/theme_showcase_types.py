"""
Theme Showcase GraphQL Types - PUBLIC ACCESS

Provides types for browsing the theme store
No authentication required - public marketplace
"""

import graphene
from graphene_django import DjangoObjectType
from django.conf import settings
from theme.models import Template
from .common_types import BaseConnection


class ShowcaseSectionType(graphene.ObjectType):
    """
    Showcase section with title, description, and image
    Used in theme details page
    """
    title = graphene.String()
    description = graphene.String()
    image = graphene.String()

    def resolve_image(self, info):
        """
        Convert relative path to full URL for frontend consumption
        Same logic as preview_image resolver
        """
        image_path = self.get('image')
        if not image_path:
            return None

        # If already a full URL, return as-is
        if image_path.startswith(('http://', 'https://')):
            return image_path

        # Get base URL from settings (environment-aware)
        base_url = getattr(settings, 'THEMES_CDN_URL', None)

        if not base_url:
            # Fallback to local media URL in development
            request = info.context
            scheme = 'https' if request.is_secure() else 'http'
            host = request.get_host()
            media_url = getattr(settings, 'THEMES_MEDIA_URL', '/theme-media/')
            base_url = f"{scheme}://{host}{media_url}"

        # Construct full URL
        return f"{base_url.rstrip('/')}/{image_path.lstrip('/')}"


class FeatureCategoryType(graphene.ObjectType):
    """
    Feature category with items list
    Used for nested features structure
    """
    category = graphene.String()
    items = graphene.List(graphene.String)


class ThemeType(DjangoObjectType):
    """
    Public theme type for theme store listing

    Contains light metadata for browsing
    NO puck data (that's only for user customizations)
    """

    id = graphene.ID(required=True)

    class Meta:
        model = Template
        fields = (
            'id', 'name', 'slug', 'description',
            'template_type', 'price_tier', 'price_amount',
            'version', 'status',
            'preview_image', 'demo_url',
            'view_count', 'download_count', 'active_usage_count',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        """Return plain UUID instead of encoded ID"""
        return str(self.id)

    def resolve_preview_image(self, info):
        """
        Convert relative path to full URL for frontend consumption

        Development: http://localhost:8000/theme-media/{relative_path}
        Production: https://cdn.yoursite.com/themes/{relative_path}
        """
        if not self.preview_image:
            return None

        # If already a full URL, return as-is
        if self.preview_image.startswith(('http://', 'https://')):
            return self.preview_image

        # Get base URL from settings (environment-aware)
        base_url = getattr(settings, 'THEMES_CDN_URL', None)

        if not base_url:
            # Fallback to local media URL in development
            request = info.context
            scheme = 'https' if request.is_secure() else 'http'
            host = request.get_host()
            media_url = getattr(settings, 'THEMES_MEDIA_URL', '/theme-media/')
            base_url = f"{scheme}://{host}{media_url}"

        # Construct full URL
        return f"{base_url.rstrip('/')}/{self.preview_image.lstrip('/')}"


class ThemeDetailsType(DjangoObjectType):
    """
    Detailed theme type for single theme view

    Contains full metadata for decision-making
    Still NO puck data (user gets that after adding to library)
    """

    id = graphene.ID(required=True)

    # Add computed fields
    is_free = graphene.Boolean()
    is_paid = graphene.Boolean()

    # Override fields with custom types
    showcase_sections = graphene.List(ShowcaseSectionType)
    features = graphene.List(FeatureCategoryType)

    class Meta:
        model = Template
        fields = (
            # Core info
            'id', 'name', 'slug', 'description',

            # Type & compatibility
            'template_type', 'workspace_types',

            # Pricing
            'price_tier', 'price_amount',

            # Version & status
            'version', 'status',

            # Preview & demo
            'preview_image', 'demo_url',

            # Metadata from manifest
            'features', 'tags', 'compatibility',
            'author', 'license',

            # Showcase sections
            'showcase_sections',

            # Metrics
            'view_count', 'download_count', 'active_usage_count',

            # Timestamps
            'created_at', 'updated_at'
        )

    def resolve_id(self, info):
        """Return plain UUID"""
        return str(self.id)

    def resolve_is_free(self, info):
        """Check if theme is free tier"""
        return self.price_tier == Template.PRICE_TIER_FREE

    def resolve_is_paid(self, info):
        """Check if theme is paid/exclusive tier"""
        return self.price_tier in [Template.PRICE_TIER_PAID, Template.PRICE_TIER_EXCLUSIVE]

    def resolve_showcase_sections(self, info):
        """Return showcase sections as list of dicts for ShowcaseSectionType"""
        return self.showcase_sections or []

    def resolve_features(self, info):
        """Return features as list of dicts for FeatureCategoryType"""
        return self.features or []

    def resolve_preview_image(self, info):
        """
        Convert relative path to full URL for frontend consumption

        Development: http://localhost:8000/theme-media/{relative_path}
        Production: https://cdn.yoursite.com/themes/{relative_path}
        """
        if not self.preview_image:
            return None

        # If already a full URL, return as-is
        if self.preview_image.startswith(('http://', 'https://')):
            return self.preview_image

        # Get base URL from settings (environment-aware)
        base_url = getattr(settings, 'THEMES_CDN_URL', None)

        if not base_url:
            # Fallback to local media URL in development
            request = info.context
            scheme = 'https' if request.is_secure() else 'http'
            host = request.get_host()
            media_url = getattr(settings, 'THEMES_MEDIA_URL', '/theme-media/')
            base_url = f"{scheme}://{host}{media_url}"

        # Construct full URL
        return f"{base_url.rstrip('/')}/{self.preview_image.lstrip('/')}"


class ThemeConnection(graphene.relay.Connection):
    """
    Theme connection for paginated theme store
    """
    class Meta:
        node = ThemeType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        """Return total count for pagination UI"""
        return self.iterable.count()
