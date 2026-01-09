"""
SEO Management Mutations (Phase 4: SEO Implementation)

Handles:
- Storefront SEO meta tags (title, description, keywords)
- Open Graph images
- SEO validation and recommendations
"""
import graphene
from graphql import GraphQLError
from ..types.seo_inputs import UpdateStorefrontSEOInput
from ..types.seo_types import SEOSettingsType
import logging

logger = logging.getLogger(__name__)


class UpdateStorefrontSEO(graphene.Mutation):
    """
    Update SEO settings for a deployed storefront

    Allows merchants to optimize their store for search engines and social sharing.
    Fields are validated against Google's best practices:
    - Title: Max 60 chars (Google truncates at ~60)
    - Description: Max 160 chars (Google truncates at ~160)
    - Keywords: Optional (less important for modern SEO)

    Args:
        workspace_id: ID of workspace
        seo_title: Page title for search results (max 60 chars recommended)
        seo_description: Meta description for search snippets (max 160 chars recommended)
        seo_keywords: Comma-separated keywords (optional)
        seo_image_url: Open Graph image URL for social sharing

    Returns:
        success: Boolean
        message: Success/error message
        warnings: List of SEO warnings (e.g., "title too long")
        seo_settings: Updated SEO settings object

    Examples:
        # Update all SEO fields
        mutation {
          updateStorefrontSEO(
            workspaceId: "uuid",
            seoTitle: "My Amazing Store - Quality Products",
            seoDescription: "Shop our curated collection of quality products at amazing prices. Free shipping on orders over $50.",
            seoKeywords: "online store, quality products, free shipping",
            seoImageUrl: "https://cdn.huzilerz.com/my-store/og-image.jpg"
          ) {
            success
            message
            warnings
            seoSettings {
              title
              description
              keywords
              imageUrl
            }
          }
        }

        # Update only title and description
        mutation {
          updateStorefrontSEO(
            workspaceId: "uuid",
            seoTitle: "Best Shoes Online",
            seoDescription: "Find your perfect pair from our collection of premium footwear."
          ) {
            success
            message
          }
        }
    """

    class Arguments:
        input = UpdateStorefrontSEOInput(required=True)

    # Return fields
    success = graphene.Boolean()
    message = graphene.String()
    warnings = graphene.List(graphene.String)
    seo_settings = graphene.Field(SEOSettingsType)

    @staticmethod
    def mutate(root, info, input):
        user = info.context.user
        workspace = info.context.workspace

        # Validation: User must be authenticated
        if not user or not user.is_authenticated:
            raise GraphQLError("Authentication required")

        # Validation: Workspace must match context (ownership check)
        if str(workspace.id) != input.workspace_id:
            raise GraphQLError("Unauthorized: Workspace ownership validation failed")

        try:
            # Get DeployedSite for workspace
            from workspace.hosting.models import DeployedSite
            from workspace.hosting.services.seo_service import SEOService

            try:
                deployed_site = DeployedSite.objects.get(workspace=workspace)
            except DeployedSite.DoesNotExist:
                logger.error(f"DeployedSite not found for workspace {workspace.id}")
                return UpdateStorefrontSEO(
                    success=False,
                    message="Deployment not found. Please deploy your site first.",
                    warnings=[],
                    seo_settings=None
                )

            # Validate SEO fields
            validation = SEOService.validate_seo_fields(
                title=input.seo_title,
                description=input.seo_description,
                keywords=input.seo_keywords
            )

            # If validation errors, return them
            if not validation['valid']:
                return UpdateStorefrontSEO(
                    success=False,
                    message=f"Validation failed: {', '.join(validation['errors'])}",
                    warnings=validation['warnings'],
                    seo_settings=None
                )

            # Update fields (only update provided fields)
            update_fields = []

            if input.seo_title is not None:
                deployed_site.seo_title = input.seo_title
                update_fields.append('seo_title')

            if input.seo_description is not None:
                deployed_site.seo_description = input.seo_description
                update_fields.append('seo_description')

            if input.seo_keywords is not None:
                deployed_site.seo_keywords = input.seo_keywords
                update_fields.append('seo_keywords')

            if input.seo_image_url is not None:
                deployed_site.seo_image_url = input.seo_image_url
                update_fields.append('seo_image_url')

            # Save updated fields
            if update_fields:
                deployed_site.save(update_fields=update_fields)

                logger.info(
                    f"SEO settings updated for workspace {workspace.id} ({workspace.name}) "
                    f"by user {user.id} | Fields: {', '.join(update_fields)}"
                )

                # Invalidate cache to reflect SEO changes
                # (future enhancement - cache invalidation for SEO meta tags)
                # from workspace.hosting.services.cache_service import WorkspaceCacheService
                # WorkspaceCacheService.invalidate_seo_cache(deployed_site.id)

                # Build SEO settings response
                seo_settings = SEOSettingsType(
                    title=deployed_site.seo_title,
                    description=deployed_site.seo_description,
                    keywords=deployed_site.seo_keywords,
                    image_url=deployed_site.seo_image_url
                )

                return UpdateStorefrontSEO(
                    success=True,
                    message="SEO settings updated successfully",
                    warnings=validation['warnings'],
                    seo_settings=seo_settings
                )
            else:
                return UpdateStorefrontSEO(
                    success=False,
                    message="No fields provided to update",
                    warnings=[],
                    seo_settings=None
                )

        except Exception as e:
            logger.error(
                f"Error updating SEO settings for workspace {workspace.id}: {str(e)}",
                exc_info=True
            )
            return UpdateStorefrontSEO(
                success=False,
                message=f"Failed to update SEO settings: {str(e)}",
                warnings=[],
                seo_settings=None
            )


class SEOMutations(graphene.ObjectType):
    """
    SEO management mutations for deployed storefronts
    """
    update_storefront_seo = UpdateStorefrontSEO.Field()
