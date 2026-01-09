"""
Storefront Settings GraphQL Types

Provides preview data for UI:
- Password protection settings
- SEO fields (title, description, keywords, image)
- Active domain info

Single source of truth for SEO/password data in UI forms
"""
import graphene


class StorefrontSettingsType(graphene.ObjectType):
    """
    Storefront settings for UI forms

    Used by:
    - SEO Settings page (edit SEO metadata)
    - Password Settings page (edit password protection)
    - Puck Editor (initial values for root.props)
    """
    # Password protection
    password = graphene.String(
        description="Current password (plaintext, for merchant to share)"
    )
    password_enabled = graphene.Boolean(
        required=True,
        description="Whether password protection is enabled"
    )
    password_description = graphene.String(
        description="Custom message shown to visitors on password page (e.g., 'Store coming soon!')"
    )

    # SEO fields (single source of truth)
    seo_title = graphene.String(
        required=True,
        description="SEO title tag (max 60 chars)"
    )
    seo_description = graphene.String(
        description="SEO meta description (max 160 chars)"
    )
    seo_keywords = graphene.String(
        description="SEO meta keywords (comma-separated)"
    )
    seo_image_url = graphene.String(
        description="SEO social share image URL"
    )

    # Domain info
    assigned_domain = graphene.String(
        required=True,
        description="Current active domain (subdomain or custom)"
    )
    preview_url = graphene.String(
        description="Full preview URL for the storefront"
    )
    site_name = graphene.String(
        description="Store name for display"
    )
