"""
SEO GraphQL Types (Phase 4: SEO Implementation)

Provides types for SEO settings and validation
"""
import graphene


class SEOSettingsType(graphene.ObjectType):
    """
    SEO settings for a deployed storefront

    Contains all SEO metadata used for:
    - Search engine optimization (Google, Bing, etc.)
    - Social media sharing (Facebook, Twitter, WhatsApp)
    - Open Graph previews
    """
    title = graphene.String(
        description="SEO title for search results (max 60 chars recommended)"
    )
    description = graphene.String(
        description="Meta description for search snippets (max 160 chars recommended)"
    )
    keywords = graphene.String(
        description="Comma-separated keywords (optional, less important for modern SEO)"
    )
    image_url = graphene.String(
        description="Open Graph image URL for social sharing previews"
    )


class SEOValidationResult(graphene.ObjectType):
    """
    SEO validation result with errors and warnings

    Used to provide feedback on SEO field quality:
    - Errors: Hard limits (e.g., title > 70 chars)
    - Warnings: Best practice violations (e.g., title > 60 chars)
    """
    valid = graphene.Boolean(
        required=True,
        description="Whether the SEO fields pass validation"
    )
    errors = graphene.List(
        graphene.String,
        required=True,
        description="List of validation errors (hard limits)"
    )
    warnings = graphene.List(
        graphene.String,
        required=True,
        description="List of best practice warnings"
    )
