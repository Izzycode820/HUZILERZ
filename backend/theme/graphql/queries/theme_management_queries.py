"""
Theme Management GraphQL Queries - AUTHENTICATED + WORKSPACE SCOPED

Manage user's theme library (customizations)
Requires authentication and workspace ownership
"""

import graphene
from graphql import GraphQLError
from ..types.theme_customization_types import ThemeCustomizationType
from theme.models import TemplateCustomization


class ThemeManagementQueries(graphene.ObjectType):
    """
    User's theme library queries

    Security: All queries automatically scoped to authenticated workspace
    Pattern: Same as ProductQueries - workspace injection via middleware
    """

    my_themes = graphene.List(
        ThemeCustomizationType,
        workspace_id=graphene.ID(required=True),
        description="Get all themes in user's library (published + drafts)"
    )

    theme_customization = graphene.Field(
        ThemeCustomizationType,
        id=graphene.ID(required=True),
        description="Get specific theme customization for Puck editor"
    )

    active_theme = graphene.Field(
        ThemeCustomizationType,
        workspace_id=graphene.ID(required=True),
        description="Get currently published theme for workspace"
    )

    def resolve_my_themes(self, info, workspace_id):
        """
        Resolve all themes in user's library

        Security: Validates user owns workspace
        Returns: All customizations (published + drafts) - Shopify pattern
        """
        workspace = info.context.workspace
        user = info.context.user

        # Validate workspace ID matches context workspace
        if str(workspace.id) != workspace_id:
            raise GraphQLError("Workspace ID mismatch - unauthorized access")

        # Get all themes for this workspace (active + drafts)
        return TemplateCustomization.objects.filter(
            workspace=workspace
        ).select_related(
            'template'  # Only template FK is exposed in GraphQL
        ).order_by(
            '-is_active',  # Active theme first
            '-last_edited_at'  # Then by most recently edited
        )

    def resolve_theme_customization(self, info, id):
        """
        Resolve specific theme customization

        Security: Validates customization belongs to user's workspace
        Use case: Load customization in Puck editor
        """
        workspace = info.context.workspace

        try:
            customization = TemplateCustomization.objects.select_related(
                'template'  # Only template FK is exposed in GraphQL
            ).get(id=id)

            # Validate ownership
            if customization.workspace.id != workspace.id:
                raise GraphQLError("Theme customization not found or unauthorized")

            return customization

        except TemplateCustomization.DoesNotExist:
            raise GraphQLError("Theme customization not found")

    def resolve_active_theme(self, info, workspace_id):
        """
        Resolve currently published theme

        Security: Validates workspace ownership
        Returns: The one active theme (Shopify: one published theme at a time)
        """
        workspace = info.context.workspace

        # Validate workspace ID matches context
        if str(workspace.id) != workspace_id:
            raise GraphQLError("Workspace ID mismatch - unauthorized access")

        # Get active theme (only one should exist due to DB constraint)
        active = TemplateCustomization.objects.filter(
            workspace=workspace,
            is_active=True
        ).select_related('template').first()

        if not active:
            # No theme published yet (new workspace)
            return None

        return active
