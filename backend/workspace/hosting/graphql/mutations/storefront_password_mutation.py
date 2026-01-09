"""
Deployment & Storefront Management Mutations

Handles:
- Storefront password protection (Concern #2)
- Deployment configuration
- Site visibility settings
"""
import graphene
from graphql import GraphQLError
from django.core.exceptions import ValidationError
from ..types.storefront_password_inputs import SetStorefrontPasswordInput
import logging

logger = logging.getLogger(__name__)


class SetStorefrontPassword(graphene.Mutation):
    """
    Set or update storefront password protection

    Shopify pattern: "Infrastructure live, business not live"
    Allows merchants to lock their storefront during development.

    Args:
        workspace_id: ID of workspace
        password: Plain text password (will be hashed)
                 Set to None or empty string to disable protection

    Returns:
        success: Boolean
        message: Success/error message
        password_enabled: Whether password protection is now active

    Security:
        - Password is hashed using Django's PBKDF2 SHA256
        - Never stored in plain text
        - Requires workspace ownership (validated by middleware)

    Examples:
        # Enable password protection
        mutation {
          setStorefrontPassword(
            workspaceId: "uuid",
            password: "my-secret-password"
          ) {
            success
            message
            passwordEnabled
          }
        }

        # Disable password protection
        mutation {
          setStorefrontPassword(
            workspaceId: "uuid",
            password: ""
          ) {
            success
            message
            passwordEnabled
          }
        }
    """

    class Arguments:
        input = SetStorefrontPasswordInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    password_enabled = graphene.Boolean()

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

            try:
                deployed_site = DeployedSite.objects.get(workspace=workspace)
            except DeployedSite.DoesNotExist:
                logger.error(f"DeployedSite not found for workspace {workspace.id}")
                return SetStorefrontPassword(
                    success=False,
                    message="Deployment not found. Please deploy your site first.",
                    password_enabled=False
                )

            # Track which fields to update
            update_fields = []

            # 1. Update Password (if provided)
            # Note: set_password automatically sets password_protection_enabled=True if password is not empty
            if input.password is not None:
                # Password strength validation
                if len(input.password) > 0 and len(input.password) < 6:
                    return SetStorefrontPassword(
                        success=False,
                        message="Password must be at least 6 characters",
                        password_enabled=deployed_site.password_protection_enabled
                    )
                
                if len(input.password) > 128:
                    return SetStorefrontPassword(
                        success=False,
                        message="Password must be less than 128 characters",
                        password_enabled=deployed_site.password_protection_enabled
                    )

                deployed_site.set_password(input.password)
                update_fields.extend(['password_hash', 'password_plaintext', 'password_protection_enabled'])

            # 2. Update Description (if provided)
            if input.description is not None:
                deployed_site.password_description = input.description
                update_fields.append('password_description')

            # 3. Update Enabled Status (if explicitly provided)
            # This overrides the auto-enable from set_password if both are present
            if input.enabled is not None:
                deployed_site.password_protection_enabled = input.enabled
                if 'password_protection_enabled' not in update_fields:
                    update_fields.append('password_protection_enabled')

            # Save changes
            if update_fields:
                deployed_site.save(update_fields=update_fields)
                
                action = "updated"
                if input.enabled is True:
                    action = "enabled"
                elif input.enabled is False:
                    action = "disabled"

                logger.info(
                    f"Storefront password settings {action} for workspace {workspace.id} ({workspace.name}) "
                    f"by user {user.id}"
                )

                return SetStorefrontPassword(
                    success=True,
                    message=f"Storefront password settings {action}",
                    password_enabled=deployed_site.password_protection_enabled
                )
            else:
                 return SetStorefrontPassword(
                    success=True,
                    message="No changes made",
                    password_enabled=deployed_site.password_protection_enabled
                )

        except Exception as e:
            logger.error(
                f"Error setting storefront password for workspace {workspace.id}: {str(e)}",
                exc_info=True
            )
            return SetStorefrontPassword(
                success=False,
                message=f"Failed to update password protection: {str(e)}",
                password_enabled=False
            )


class DeploymentMutations(graphene.ObjectType):
    """
    Deployment and storefront management mutations
    """
    set_storefront_password = SetStorefrontPassword.Field()
