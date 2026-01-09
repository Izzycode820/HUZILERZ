"""
Theme Management GraphQL Mutations - AUTHENTICATED + WORKSPACE SCOPED

Shopify-style theme library management
All mutations require authentication and workspace ownership
"""

import graphene
from graphql import GraphQLError
from django.core.exceptions import ValidationError
from django.db import transaction
from ..types.theme_customization_types import ThemeCustomizationType
from ..types.theme_inputs import UpdateThemeCustomizationInput
from theme.services.template_customization_service import TemplateCustomizationService
import logging

logger = logging.getLogger(__name__)


class AddTheme(graphene.Mutation):
    """
    Add theme to user's library (clone from theme store)

    Shopify pattern: "Use theme" button in theme store
    Creates draft customization with cloned puck data
    """

    class Arguments:
        workspace_id = graphene.ID(required=True)
        theme_slug = graphene.String(required=True)

    success = graphene.Boolean()
    customization = graphene.Field(ThemeCustomizationType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, workspace_id, theme_slug):
        # For user-level operations, workspace comes from args, not context
        user = info.context.user

        try:
            # Fetch and validate workspace from argument (not context)
            from workspace.core.models import Workspace, Membership
            try:
                workspace = Workspace.objects.get(id=workspace_id, status='active')
            except Workspace.DoesNotExist:
                raise GraphQLError("Workspace not found or inactive")

            # Validate user has access to this workspace
            if workspace.owner != user:
                try:
                    Membership.objects.get(
                        workspace=workspace,
                        user=user,
                        is_active=True
                    )
                except Membership.DoesNotExist:
                    raise GraphQLError("Access denied - you do not have permission to access this workspace")

            # Get template by slug
            from theme.models import Template
            try:
                template = Template.objects.get(slug=theme_slug, status='active')
            except Template.DoesNotExist:
                raise GraphQLError(f"Theme '{theme_slug}' not found")

            # Clone theme to workspace using service
            customization = TemplateCustomizationService.clone_template_to_workspace(
                template_id=template.id,
                workspace_id=workspace.id,
                user=user
            )

            return AddTheme(
                success=True,
                customization=customization,
                message=f"Theme '{template.name}' added to your library"
            )

        except ValidationError as e:
            return AddTheme(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Add theme mutation failed: {str(e)}", exc_info=True)
            return AddTheme(
                success=False,
                error=f"Failed to add theme: {str(e)}"
            )


class UpdateThemeCustomization(graphene.Mutation):
    """
    Update theme customization (save Puck editor changes)

    Auto-saves from Puck editor every 30s or manual save
    Updates puck_data and/or puck_config
    """

    class Arguments:
        id = graphene.ID(required=True)
        input = UpdateThemeCustomizationInput(required=True)

    success = graphene.Boolean()
    customization = graphene.Field(ThemeCustomizationType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate ownership
            from theme.models import TemplateCustomization
            try:
                customization = TemplateCustomization.objects.get(id=id)
            except TemplateCustomization.DoesNotExist:
                raise GraphQLError("Theme customization not found")

            if customization.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized: Theme does not belong to your workspace")

            # Update using service
            updated = TemplateCustomizationService.save_customizations(
                customization_id=id,
                puck_config=input.puck_config,
                puck_data=input.puck_data,
                user=user
            )

            return UpdateThemeCustomization(
                success=True,
                customization=updated,
                message="Theme customization saved"
            )

        except ValidationError as e:
            return UpdateThemeCustomization(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Update customization mutation failed: {str(e)}", exc_info=True)
            return UpdateThemeCustomization(
                success=False,
                error=f"Failed to update customization: {str(e)}"
            )


class PublishTheme(graphene.Mutation):
    """
    Publish theme (make it live on workspace)

    Shopify pattern: Only one published theme at a time
    Auto-unpublishes any other active theme
    """

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    customization = graphene.Field(ThemeCustomizationType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate ownership
            from theme.models import TemplateCustomization
            try:
                customization = TemplateCustomization.objects.get(id=id)
            except TemplateCustomization.DoesNotExist:
                raise GraphQLError("Theme customization not found")

            if customization.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized: Theme does not belong to your workspace")

            # Publish using service (handles unpublishing others)
            published = TemplateCustomizationService.publish_theme(
                customization_id=id,
                user=user
            )

            return PublishTheme(
                success=True,
                customization=published,
                message=f"Theme '{customization.theme_name}' is now live"
            )

        except ValidationError as e:
            return PublishTheme(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Publish theme mutation failed: {str(e)}", exc_info=True)
            return PublishTheme(
                success=False,
                error=f"Failed to publish theme: {str(e)}"
            )


class UnpublishTheme(graphene.Mutation):
    """
    Unpublish theme (take it offline)

    Workspace will have no active theme until another is published
    Use case: Maintenance mode or switching themes
    """

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id):
        workspace = info.context.workspace

        try:
            # Validate ownership
            from theme.models import TemplateCustomization
            try:
                customization = TemplateCustomization.objects.get(id=id)
            except TemplateCustomization.DoesNotExist:
                raise GraphQLError("Theme customization not found")

            if customization.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized: Theme does not belong to your workspace")

            # Unpublish using model method
            customization.unpublish()

            return UnpublishTheme(
                success=True,
                message=f"Theme '{customization.theme_name}' unpublished"
            )

        except ValidationError as e:
            return UnpublishTheme(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Unpublish theme mutation failed: {str(e)}", exc_info=True)
            return UnpublishTheme(
                success=False,
                error=f"Failed to unpublish theme: {str(e)}"
            )


class DeleteTheme(graphene.Mutation):
    """
    Delete theme from library

    Shopify pattern: Permanent deletion (no archive)
    Cannot delete active theme - must publish another first
    """

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate ownership
            from theme.models import TemplateCustomization
            try:
                customization = TemplateCustomization.objects.get(id=id)
            except TemplateCustomization.DoesNotExist:
                raise GraphQLError("Theme customization not found")

            if customization.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized: Theme does not belong to your workspace")

            theme_name = customization.theme_name

            # Delete using service (validates not active)
            TemplateCustomizationService.delete_theme(
                customization_id=id,
                user=user
            )

            return DeleteTheme(
                success=True,
                message=f"Theme '{theme_name}' deleted from library"
            )

        except ValidationError as e:
            return DeleteTheme(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Delete theme mutation failed: {str(e)}", exc_info=True)
            return DeleteTheme(
                success=False,
                error=f"Failed to delete theme: {str(e)}"
            )


class DuplicateTheme(graphene.Mutation):
    """
    Duplicate theme for experimentation

    Shopify pattern: Copy theme to try variations
    Creates new draft with copied puck data
    """

    class Arguments:
        id = graphene.ID(required=True)
        new_name = graphene.String()

    success = graphene.Boolean()
    customization = graphene.Field(ThemeCustomizationType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id, new_name=None):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate ownership
            from theme.models import TemplateCustomization
            try:
                customization = TemplateCustomization.objects.get(id=id)
            except TemplateCustomization.DoesNotExist:
                raise GraphQLError("Theme customization not found")

            if customization.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized: Theme does not belong to your workspace")

            # Duplicate using service
            duplicate = TemplateCustomizationService.duplicate_theme(
                customization_id=id,
                new_name=new_name,
                user=user
            )

            return DuplicateTheme(
                success=True,
                customization=duplicate,
                message=f"Theme duplicated as '{duplicate.theme_name}'"
            )

        except ValidationError as e:
            return DuplicateTheme(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Duplicate theme mutation failed: {str(e)}", exc_info=True)
            return DuplicateTheme(
                success=False,
                error=f"Failed to duplicate theme: {str(e)}"
            )


class RenameTheme(graphene.Mutation):
    """
    Rename theme in library

    User-friendly labels for theme organization
    """

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)

    success = graphene.Boolean()
    customization = graphene.Field(ThemeCustomizationType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, id, name):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate ownership
            from theme.models import TemplateCustomization
            try:
                customization = TemplateCustomization.objects.get(id=id)
            except TemplateCustomization.DoesNotExist:
                raise GraphQLError("Theme customization not found")

            if customization.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized: Theme does not belong to your workspace")

            # Rename using service
            renamed = TemplateCustomizationService.rename_theme(
                customization_id=id,
                new_name=name,
                user=user
            )

            return RenameTheme(
                success=True,
                customization=renamed,
                message=f"Theme renamed to '{name}'"
            )

        except ValidationError as e:
            return RenameTheme(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Rename theme mutation failed: {str(e)}", exc_info=True)
            return RenameTheme(
                success=False,
                error=f"Failed to rename theme: {str(e)}"
            )


class ThemeManagementMutations(graphene.ObjectType):
    """
    Theme management mutations collection

    Shopify-style theme library management
    All mutations require authentication + workspace scoping
    """

    add_theme = AddTheme.Field()
    update_theme_customization = UpdateThemeCustomization.Field()
    publish_theme = PublishTheme.Field()
    unpublish_theme = UnpublishTheme.Field()
    delete_theme = DeleteTheme.Field()
    duplicate_theme = DuplicateTheme.Field()
    rename_theme = RenameTheme.Field()
