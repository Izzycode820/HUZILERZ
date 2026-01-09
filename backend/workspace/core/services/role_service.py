# Role Service - Workspace-scoped role and permission management

from django.apps import apps
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
import logging

logger = logging.getLogger('workspace.core.services')


class RoleService:
    """
    Service for workspace-scoped role creation and permission management
    Following industry standard: Roles are DATA, not logic

    Key principles:
    - Never check role names in code
    - Always check permissions
    - Roles are workspace-scoped
    - System roles are templates for workspace provisioning
    """

    @staticmethod
    def initialize_system_roles_and_permissions():
        """
        One-time system initialization
        Creates system roles and seeds permissions

        Should be run:
        - During initial deployment
        - After adding new permissions to the system

        Returns:
            Dict with created roles and permissions count
        """
        from workspace.core.models import Permission, Role

        logger.info("Initializing system roles and permissions...")

        # Seed permissions
        permissions_created = Permission.seed_default_permissions()
        logger.info(f"Seeded {permissions_created} permissions")

        # Create system roles
        system_roles = Role.create_system_roles()
        logger.info(f"Created {len(system_roles)} system roles")

        return {
            'permissions_created': permissions_created,
            'system_roles_created': len(system_roles)
        }

    @staticmethod
    def provision_workspace_roles(workspace):
        """
        Auto-provision default roles for new workspace
        Called automatically when workspace is created

        Args:
            workspace: Workspace instance

        Returns:
            Dict mapping role names to Role instances

        Raises:
            ValidationError: If system roles not initialized
        """
        from workspace.core.models import Role

        logger.info(f"Provisioning roles for workspace: {workspace.name}")

        try:
            workspace_roles = Role.provision_workspace_roles(workspace)
            logger.info(f"Provisioned {len(workspace_roles)} roles for {workspace.name}")
            return workspace_roles
        except Exception as e:
            logger.error(f"Failed to provision workspace roles: {str(e)}")
            raise ValidationError(f"Failed to provision workspace roles: {str(e)}")

    @staticmethod
    def create_owner_membership(workspace, owner_user):
        """
        Create owner membership for workspace creator
        Called automatically when workspace is created

        Args:
            workspace: Workspace instance
            owner_user: User instance (workspace creator)

        Returns:
            Membership instance

        Raises:
            ValidationError: If Owner role not found
        """
        from workspace.core.models import Membership, Role

        logger.info(f"Creating owner membership for {owner_user.email} in {workspace.name}")

        from django.db import transaction

        try:
            # Get Owner role for this workspace
            owner_role = Role.objects.get(workspace=workspace, name='Owner')

            with transaction.atomic():
                # Create membership (without roles first, then add via M2M)
                membership = Membership.objects.create(
                    user=owner_user,
                    workspace=workspace,
                    status=Membership.Status.ACTIVE
                )

                # Assign Owner role
                membership.set_roles([owner_role.id])

            logger.info(f"Created owner membership: {membership}")
            return membership

        except Role.DoesNotExist:
            logger.error(f"Owner role not found for workspace {workspace.name}")
            raise ValidationError(
                "Owner role not found. Ensure workspace roles are provisioned."
            )
        except Exception as e:
            logger.error(f"Failed to create owner membership: {str(e)}")
            raise ValidationError(f"Failed to create owner membership: {str(e)}")

    @staticmethod
    def get_workspace_roles(workspace):
        """
        Get all roles for a workspace

        Args:
            workspace: Workspace instance

        Returns:
            QuerySet of Role instances
        """
        from workspace.core.models import Role

        return Role.objects.filter(
            workspace=workspace,
            is_system=False
        ).prefetch_related('role_permissions').order_by('name')

    @staticmethod
    def create_custom_role(workspace, name, permission_keys, created_by=None):
        """
        Create custom role for workspace
        Only users with 'staff:role_change' permission can create roles

        Args:
            workspace: Workspace instance
            name: Role name
            permission_keys: List of permission key strings
            created_by: User creating the role (optional, for logging)

        Returns:
            Role instance

        Raises:
            ValidationError: If validation fails
        """
        from workspace.core.models import Role, Permission, RolePermission
        from django.db import transaction

        logger.info(f"Creating custom role '{name}' for workspace {workspace.name}")

        # Validate permission keys exist
        existing_permissions = set(
            Permission.objects.filter(key__in=permission_keys)
            .values_list('key', flat=True)
        )

        invalid_permissions = set(permission_keys) - existing_permissions
        if invalid_permissions:
            raise ValidationError(
                f"Invalid permissions: {', '.join(invalid_permissions)}"
            )

        try:
            with transaction.atomic():
                # Create role
                role = Role.objects.create(
                    workspace=workspace,
                    name=name,
                    is_system=False
                )

                # Assign permissions
                RolePermission.assign_permissions_to_role(
                    role=role,
                    permission_keys=permission_keys,
                    allow_system=False
                )

                logger.info(
                    f"Created custom role: {role.name} with {len(permission_keys)} permissions"
                    + (f" by {created_by.email}" if created_by else "")
                )

                return role

        except Exception as e:
            logger.error(f"Failed to create custom role: {str(e)}")
            raise ValidationError(f"Failed to create custom role: {str(e)}")

    @staticmethod
    def update_role_permissions(role, permission_keys, updated_by=None):
        """
        Update role permissions
        Cannot modify system roles

        Args:
            role: Role instance
            permission_keys: List of permission key strings
            updated_by: User updating the role (optional, for logging)

        Returns:
            Role instance

        Raises:
            ValidationError: If role is system role or validation fails
        """
        from workspace.core.models import RolePermission

        if role.is_system:
            raise ValidationError("Cannot modify system roles")

        logger.info(f"Updating permissions for role: {role.name}")

        try:
            # Update permissions (replaces existing)
            count = RolePermission.assign_permissions_to_role(
                role=role,
                permission_keys=permission_keys,
                allow_system=False
            )

            logger.info(
                f"Updated role {role.name} with {count} permissions"
                + (f" by {updated_by.email}" if updated_by else "")
            )

            return role

        except Exception as e:
            logger.error(f"Failed to update role permissions: {str(e)}")
            raise ValidationError(f"Failed to update role permissions: {str(e)}")

    @staticmethod
    def delete_custom_role(role, deleted_by=None):
        """
        Delete custom role
        Cannot delete system roles
        Prevents deletion if role has active memberships

        Args:
            role: Role instance
            deleted_by: User deleting the role (optional, for logging)

        Raises:
            ValidationError: If role is system role or has active memberships
        """
        from workspace.core.models import Membership

        if role.is_system:
            raise ValidationError("Cannot delete system roles")

        # Check for active memberships
        active_memberships = Membership.objects.filter(
            role=role,
            status=Membership.Status.ACTIVE
        ).count()

        if active_memberships > 0:
            raise ValidationError(
                f"Cannot delete role '{role.name}' - {active_memberships} active members have this role"
            )

        logger.info(
            f"Deleting custom role: {role.name}"
            + (f" by {deleted_by.email}" if deleted_by else "")
        )

        role.delete()

    @staticmethod
    def get_all_permissions():
        """
        Get all available permissions in the system

        Returns:
            QuerySet of Permission instances
        """
        from workspace.core.models import Permission

        return Permission.objects.all().order_by('key')

    @staticmethod
    def get_permissions_by_keys(permission_keys):
        """
        Get Permission instances by keys

        Args:
            permission_keys: List of permission key strings

        Returns:
            QuerySet of Permission instances
        """
        from workspace.core.models import Permission

        return Permission.objects.filter(key__in=permission_keys)