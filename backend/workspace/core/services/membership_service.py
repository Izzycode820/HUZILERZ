# Membership Service - Invitation flow and permission-based member management

from django.db import transaction
from django.apps import apps
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger('workspace.core.services')


class MembershipService:
    """
    Service for managing workspace memberships following industry standard pattern

    Key principles (from guide):
    - NO owner bypass logic
    - All actions require permissions (staff:invite, staff:remove, staff:role_change)
    - Invitation flow: invite -> accept -> membership created
    - No membership exists before acceptance
    - Authorization evaluated per request via membership -> role -> permissions
    """

    @staticmethod
    def invite_staff(workspace, inviter, email, role_ids):
        """
        Invite user to workspace with specific roles (supports multiple like Shopify)
        Requires 'staff:invite' permission

        Args:
            workspace: Workspace instance
            inviter: User sending invite
            email: Email of user to invite
            role_ids: List of role IDs to assign (supports multiple)

        Returns:
            WorkspaceInvite instance

        Raises:
            PermissionDenied: If inviter lacks permission
            ValidationError: If validation fails
        """
        from workspace.core.models import WorkspaceInvite, Role, Membership

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(inviter, workspace, 'staff:invite'):
            raise PermissionDenied("Insufficient permissions to invite users")

        # Check staff limit capability
        from subscription.services.gating import check_staff_limit
        allowed, error_msg = check_staff_limit(workspace)
        if not allowed:
            raise PermissionDenied(error_msg)

        # Ensure role_ids is a list
        if isinstance(role_ids, str):
            role_ids = [role_ids]

        if not role_ids:
            raise ValidationError("Must provide at least one role")

        # Get and validate all roles belong to workspace
        roles = Role.objects.filter(id__in=role_ids, workspace=workspace)

        if roles.count() != len(role_ids):
            raise ValidationError("One or more roles not found in workspace")

        # CRITICAL: Prevent privilege escalation
        # Only Owner role can invite as Owner or Admin
        inviter_membership = Membership.get_user_active_membership(inviter, workspace)
        inviter_role_names = {role.name for role in inviter_membership.roles.all()}

        role_names = {role.name for role in roles}

        if 'Owner' in role_names and 'Owner' not in inviter_role_names:
            raise PermissionDenied("Only workspace Owner can invite other Owners")

        if 'Admin' in role_names and 'Owner' not in inviter_role_names:
            raise PermissionDenied("Only workspace Owner can invite Admins")

        # RATE LIMITING: Once per email per workspace per 20 minutes (industry standard)
        cache_key = f"invite_rate_limit:{workspace.id}:{email.lower()}"
        if cache.get(cache_key):
            raise PermissionDenied(
                "Rate limit exceeded. You can invite this email again in 20 minutes."
            )

        # Check if user already has active membership
        User = apps.get_model(settings.AUTH_USER_MODEL)
        try:
            existing_user = User.objects.get(email=email)
            existing_membership = Membership.get_user_active_membership(existing_user, workspace)
            if existing_membership:
                raise ValidationError(f"User '{email}' is already an active member of this workspace")
        except User.DoesNotExist:
            # User doesn't exist yet - they'll be invited to sign up
            pass

        # Check for pending invite
        pending_invite = WorkspaceInvite.objects.filter(
            workspace=workspace,
            email=email,
            status__in=[WorkspaceInvite.Status.CREATED, WorkspaceInvite.Status.SENT],
            expires_at__gt=timezone.now()
        ).first()

        if pending_invite:
            raise ValidationError(f"User '{email}' already has a pending invitation")

        try:
            with transaction.atomic():
                # Create invitation (without roles first, then add via M2M)
                invite = WorkspaceInvite.objects.create(
                    workspace=workspace,
                    invited_by=inviter,
                    email=email
                )

                # Assign roles to invitation
                invite.set_roles(role_ids)

                # Mark as sent (before triggering email)
                invite.mark_sent()

                # Trigger async email task AFTER transaction commit
                # Using transaction.on_commit ensures email only sends if DB commit succeeds
                from django.db import transaction as db_transaction
                from workspace.core.tasks import send_workspace_invitation_email

                db_transaction.on_commit(
                    lambda: send_workspace_invitation_email.delay(str(invite.id))
                )

                # Set rate limit cache (20 minutes = 1200 seconds)
                cache.set(cache_key, True, timeout=1200)

                # Log invitation
                role_names_str = ', '.join(role_names)
                AuditLog = apps.get_model('workspace_core', 'AuditLog')
                AuditLog.log_action(
                    workspace=workspace,
                    user=inviter,
                    action='invite_staff',
                    resource_type='workspace_invite',
                    resource_id=str(invite.id),
                    description=f"Invited '{email}' as {role_names_str}",
                    metadata={'email': email, 'roles': list(role_names)}
                )

                logger.info(f"Invited {email} to {workspace.name} as {role_names_str} by {inviter.email}")
                return invite

        except Exception as e:
            logger.error(f"Failed to invite user: {str(e)}")
            raise ValidationError(f"Failed to invite user: {str(e)}")

    @staticmethod
    def accept_invite(token, user):
        """
        Accept invitation and create membership
        User must be authenticated

        Args:
            token: Invitation token
            user: User accepting invite

        Returns:
            Membership instance

        Raises:
            ValidationError: If invite invalid or expired
        """
        from workspace.core.models import WorkspaceInvite

        # Get invite by token
        invite = WorkspaceInvite.get_by_token(token)
        if not invite:
            raise ValidationError("Invalid invitation token")

        # Edge case protection: Check staff limit AGAIN before acceptance
        # This handles: race conditions, plan downgrades between invite and accept, etc.
        from subscription.services.gating import check_staff_limit
        # Use include_pending=False since this invite will be consumed
        allowed, error_msg = check_staff_limit(invite.workspace, include_pending=False)
        if not allowed:
            raise ValidationError(
                "This workspace has reached its staff limit. "
            )

        # Accept invite (creates membership)
        try:
            with transaction.atomic():
                membership = invite.accept(user)

                # Log acceptance
                AuditLog = apps.get_model('workspace_core', 'AuditLog')
                AuditLog.log_action(
                    workspace=invite.workspace,
                    user=user,
                    action='accept_invite',
                    resource_type='membership',
                    resource_id=str(membership.id),
                    description=f"User '{user.email}' accepted invitation",
                    metadata={'invite_id': str(invite.id)}
                )

                # Send welcome email AFTER transaction commit
                from django.db import transaction as db_transaction
                from workspace.core.tasks import send_welcome_to_workspace_email

                db_transaction.on_commit(
                    lambda: send_welcome_to_workspace_email.delay(str(membership.id))
                )

                logger.info(f"User {user.email} accepted invite to {invite.workspace.name}")
                return membership

        except Exception as e:
            logger.error(f"Failed to accept invite: {str(e)}")
            raise

    @staticmethod
    def change_staff_role(workspace, changer, member_id, new_role_id):
        """
        Change member's role in workspace
        Requires 'staff:role_change' permission

        Args:
            workspace: Workspace instance
            changer: User making the change
            member_id: Membership ID to change
            new_role_id: New role ID

        Returns:
            Updated Membership instance

        Raises:
            PermissionDenied: If changer lacks permission
            ValidationError: If validation fails
        """
        from workspace.core.models import Membership, Role

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(changer, workspace, 'staff:role_change'):
            raise PermissionDenied("Insufficient permissions to change user roles")

        # Get membership
        try:
            membership = Membership.objects.select_related('user').prefetch_related('roles').get(
                id=member_id,
                workspace=workspace,
                status=Membership.Status.ACTIVE
            )
        except Membership.DoesNotExist:
            raise ValidationError("Membership not found")

        # Get new role
        try:
            new_role = Role.objects.get(id=new_role_id, workspace=workspace)
        except Role.DoesNotExist:
            raise ValidationError(f"Role not found in workspace {workspace.name}")

        # CRITICAL: Prevent self-privilege escalation
        if changer == membership.user:
            raise ValidationError("Cannot change your own role")

        # CRITICAL: Cannot change Owner role
        member_role_names = {role.name for role in membership.roles.all()}
        if 'Owner' in member_role_names:
            raise ValidationError("Cannot change workspace Owner role")

        # CRITICAL: Cannot assign Owner role
        if new_role.name == 'Owner':
            raise ValidationError("Cannot assign Owner role. Owner is the workspace creator.")

        # CRITICAL: Only Owner can assign Admin role
        changer_membership = Membership.get_user_active_membership(changer, workspace)
        changer_role_names = {role.name for role in changer_membership.roles.all()}
        if new_role.name == 'Admin' and 'Owner' not in changer_role_names:
            raise PermissionDenied("Only workspace Owner can assign Admin role")

        old_role_names = ', '.join(member_role_names)

        try:
            with transaction.atomic():
                # Replace all roles with the new single role
                membership.set_roles([new_role_id])

                # Log role change
                AuditLog = apps.get_model('workspace_core', 'AuditLog')
                AuditLog.log_action(
                    workspace=workspace,
                    user=changer,
                    action='change_staff_role',
                    resource_type='membership',
                    resource_id=str(membership.id),
                    description=f"Changed '{membership.user.email}' role from {old_role_names} to {new_role.name}",
                    metadata={'old_roles': list(member_role_names), 'new_role': new_role.name}
                )

                # Send role change notification AFTER transaction commit
                from django.db import transaction as db_transaction
                from workspace.core.tasks import send_role_changed_notification

                db_transaction.on_commit(
                    lambda: send_role_changed_notification.delay(
                        str(membership.id),
                        old_role_names,
                        new_role.name,
                        changer.email
                    )
                )

                logger.info(f"Changed {membership.user.email} role from {old_role_names} to {new_role.name} in {workspace.name}")
                return membership

        except Exception as e:
            logger.error(f"Failed to change user role: {str(e)}")
            raise ValidationError(f"Failed to change user role: {str(e)}")

    @staticmethod
    def suspend_staff(workspace, suspender, member_id, reason=''):
        """
        Suspend member from workspace (temporary, can be reactivated)
        Requires 'staff:suspend' permission

        Args:
            workspace: Workspace instance
            suspender: User suspending the member
            member_id: Membership ID to suspend
            reason: Optional reason for suspension

        Raises:
            PermissionDenied: If suspender lacks permission
            ValidationError: If validation fails
        """
        from workspace.core.models import Membership

        # Input validation - fail fast
        if workspace is None:
            raise ValidationError("Workspace cannot be None")
        if suspender is None:
            raise ValidationError("Suspender cannot be None")
        if not member_id:
            raise ValidationError("Member ID is required")

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(suspender, workspace, 'staff:suspend'):
            raise PermissionDenied("Insufficient permissions to suspend users")

        # Get membership with select_for_update to prevent race conditions
        try:
            with transaction.atomic():
                membership = Membership.objects.select_for_update().select_related('user').prefetch_related('roles').get(
                    id=member_id,
                    workspace=workspace
                )

                # CRITICAL: Can only suspend ACTIVE memberships
                if membership.status != Membership.Status.ACTIVE:
                    raise ValidationError(f"Cannot suspend member with status: {membership.status}")

                # CRITICAL: Cannot suspend workspace Owner
                role_names = {role.name for role in membership.roles.all()}
                if 'Owner' in role_names:
                    raise ValidationError("Cannot suspend workspace Owner")

                # CRITICAL: Cannot suspend yourself
                if suspender == membership.user:
                    raise ValidationError("Cannot suspend yourself")

                # Store user email for logging/notification
                suspended_user_email = membership.user.email

                # Suspend membership
                membership.suspend(suspended_by=suspender, reason=reason)

                # Log suspension
                AuditLog = apps.get_model('workspace_core', 'AuditLog')
                AuditLog.log_action(
                    workspace=workspace,
                    user=suspender,
                    action='suspend_staff',
                    resource_type='membership',
                    resource_id=str(membership.id),
                    description=f"Suspended '{suspended_user_email}' from workspace",
                    metadata={'reason': reason} if reason else {}
                )

                # Send suspension notification AFTER transaction commit
                from django.db import transaction as db_transaction
                from workspace.core.tasks import send_member_suspended_notification

                db_transaction.on_commit(
                    lambda: send_member_suspended_notification.delay(
                        suspended_user_email,
                        workspace.name,
                        suspender.email,
                        reason
                    )
                )

                logger.warning(
                    f"Suspended {suspended_user_email} from {workspace.name} by {suspender.email}",
                    extra={
                        'workspace_id': str(workspace.id),
                        'membership_id': str(membership.id),
                        'suspender_id': str(suspender.id),
                        'reason': reason
                    }
                )

        except Membership.DoesNotExist:
            logger.error(f"Membership {member_id} not found in workspace {workspace.id}")
            raise ValidationError("Membership not found")
        except Exception as e:
            logger.error(f"Failed to suspend user: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def reactivate_staff(workspace, reactivator, member_id):
        """
        Reactivate suspended member
        Requires 'staff:reactivate' permission

        Args:
            workspace: Workspace instance
            reactivator: User reactivating the member
            member_id: Membership ID to reactivate

        Returns:
            Reactivated Membership instance

        Raises:
            PermissionDenied: If reactivator lacks permission
            ValidationError: If validation fails
        """
        from workspace.core.models import Membership

        # Input validation - fail fast
        if workspace is None:
            raise ValidationError("Workspace cannot be None")
        if reactivator is None:
            raise ValidationError("Reactivator cannot be None")
        if not member_id:
            raise ValidationError("Member ID is required")

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(reactivator, workspace, 'staff:reactivate'):
            raise PermissionDenied("Insufficient permissions to reactivate users")

        # Get membership with select_for_update to prevent race conditions
        try:
            with transaction.atomic():
                membership = Membership.objects.select_for_update().select_related('user').prefetch_related('roles').get(
                    id=member_id,
                    workspace=workspace
                )

                # CRITICAL: Can only reactivate SUSPENDED memberships
                if membership.status != Membership.Status.SUSPENDED:
                    raise ValidationError(f"Cannot reactivate member with status: {membership.status}. Must be SUSPENDED.")

                # Store user email for logging/notification
                reactivated_user_email = membership.user.email
                old_reason = membership.suspension_reason

                # Reactivate membership
                membership.reactivate()

                # Log reactivation
                AuditLog = apps.get_model('workspace_core', 'AuditLog')
                AuditLog.log_action(
                    workspace=workspace,
                    user=reactivator,
                    action='reactivate_staff',
                    resource_type='membership',
                    resource_id=str(membership.id),
                    description=f"Reactivated '{reactivated_user_email}' in workspace",
                    metadata={'previous_suspension_reason': old_reason} if old_reason else {}
                )

                # Send reactivation notification AFTER transaction commit
                from django.db import transaction as db_transaction
                from workspace.core.tasks import send_member_reactivated_notification

                db_transaction.on_commit(
                    lambda: send_member_reactivated_notification.delay(
                        reactivated_user_email,
                        workspace.name,
                        reactivator.email
                    )
                )

                logger.info(
                    f"Reactivated {reactivated_user_email} in {workspace.name} by {reactivator.email}",
                    extra={
                        'workspace_id': str(workspace.id),
                        'membership_id': str(membership.id),
                        'reactivator_id': str(reactivator.id)
                    }
                )

                return membership

        except Membership.DoesNotExist:
            logger.error(f"Membership {member_id} not found in workspace {workspace.id}")
            raise ValidationError("Membership not found")
        except Exception as e:
            logger.error(f"Failed to reactivate user: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def remove_staff(workspace, remover, member_id):
        """
        Permanently remove member from workspace (cannot be reactivated)
        Requires 'staff:remove' permission

        CRITICAL: This is permanent removal. For temporary suspension, use suspend_staff()

        Args:
            workspace: Workspace instance
            remover: User removing the member
            member_id: Membership ID to remove

        Raises:
            PermissionDenied: If remover lacks permission
            ValidationError: If validation fails
        """
        from workspace.core.models import Membership

        # Input validation - fail fast
        if workspace is None:
            raise ValidationError("Workspace cannot be None")
        if remover is None:
            raise ValidationError("Remover cannot be None")
        if not member_id:
            raise ValidationError("Member ID is required")

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(remover, workspace, 'staff:remove'):
            raise PermissionDenied("Insufficient permissions to remove users")

        # Get membership with select_for_update to prevent race conditions
        try:
            with transaction.atomic():
                membership = Membership.objects.select_for_update().select_related('user').prefetch_related('roles').get(
                    id=member_id,
                    workspace=workspace
                )

                # CRITICAL: Can only remove ACTIVE or SUSPENDED memberships
                if membership.status not in [Membership.Status.ACTIVE, Membership.Status.SUSPENDED]:
                    raise ValidationError(f"Cannot remove member with status: {membership.status}")

                # CRITICAL: Cannot remove workspace Owner
                role_names = {role.name for role in membership.roles.all()}
                if 'Owner' in role_names:
                    raise ValidationError("Cannot remove workspace Owner. Transfer ownership first.")

                # CRITICAL: Cannot remove yourself
                if remover == membership.user:
                    raise ValidationError("Cannot remove yourself. Transfer ownership first.")

                # Store user email for logging/notification
                removed_user_email = membership.user.email

                # Permanently remove membership
                membership.remove(removed_by=remover)

                # Log removal
                AuditLog = apps.get_model('workspace_core', 'AuditLog')
                AuditLog.log_action(
                    workspace=workspace,
                    user=remover,
                    action='remove_staff',
                    resource_type='membership',
                    resource_id=str(membership.id),
                    description=f"Permanently removed '{removed_user_email}' from workspace"
                )

                # Send removal notification AFTER transaction commit
                from django.db import transaction as db_transaction
                from workspace.core.tasks import send_member_removed_notification

                db_transaction.on_commit(
                    lambda: send_member_removed_notification.delay(
                        removed_user_email,
                        workspace.name,
                        remover.email
                    )
                )

                logger.warning(
                    f"Permanently removed {removed_user_email} from {workspace.name} by {remover.email}",
                    extra={
                        'workspace_id': str(workspace.id),
                        'membership_id': str(membership.id),
                        'remover_id': str(remover.id)
                    }
                )

        except Membership.DoesNotExist:
            logger.error(f"Membership {member_id} not found in workspace {workspace.id}")
            raise ValidationError("Membership not found")
        except Exception as e:
            logger.error(f"Failed to remove user: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_workspace_members(workspace, requester):
        """
        Get all workspace members
        Requires 'staff:view' permission

        Args:
            workspace: Workspace instance
            requester: User requesting members list

        Returns:
            QuerySet of Membership instances

        Raises:
            PermissionDenied: If requester lacks permission
        """
        from workspace.core.models import Membership

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(requester, workspace, 'staff:view'):
            raise PermissionDenied("Insufficient permissions to view workspace members")

        return Membership.objects.filter(
            workspace=workspace,
            status=Membership.Status.ACTIVE
        ).select_related('user').prefetch_related('roles', 'roles__role_permissions').order_by('-joined_at')

    @staticmethod
    def get_pending_invites(workspace, requester):
        """
        Get pending invitations for workspace
        Requires 'staff:view' permission

        Args:
            workspace: Workspace instance
            requester: User requesting invites list

        Returns:
            QuerySet of WorkspaceInvite instances

        Raises:
            PermissionDenied: If requester lacks permission
        """
        from workspace.core.models import WorkspaceInvite

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(requester, workspace, 'staff:view'):
            raise PermissionDenied("Insufficient permissions to view pending invitations")

        return WorkspaceInvite.get_pending_invites(workspace)

    @staticmethod
    def cancel_invite(workspace, canceller, invite_id):
        """
        Cancel pending invitation
        Requires 'staff:invite' permission

        Args:
            workspace: Workspace instance
            canceller: User cancelling the invite
            invite_id: Invite ID to cancel

        Raises:
            PermissionDenied: If canceller lacks permission
            ValidationError: If validation fails
        """
        from workspace.core.models import WorkspaceInvite

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(canceller, workspace, 'staff:invite'):
            raise PermissionDenied("Insufficient permissions to cancel invitations")

        # Get invite
        try:
            invite = WorkspaceInvite.objects.get(id=invite_id, workspace=workspace)
        except WorkspaceInvite.DoesNotExist:
            raise ValidationError("Invitation not found")

        try:
            invite.cancel()

            # Log cancellation
            AuditLog = apps.get_model('workspace_core', 'AuditLog')
            AuditLog.log_action(
                workspace=workspace,
                user=canceller,
                action='cancel_invite',
                resource_type='workspace_invite',
                resource_id=str(invite.id),
                description=f"Cancelled invitation for '{invite.email}'"
            )

            logger.info(f"Cancelled invite for {invite.email} in {workspace.name} by {canceller.email}")

        except Exception as e:
            logger.error(f"Failed to cancel invite: {str(e)}")
            raise

    @staticmethod
    def resend_invite(workspace, resender, invite_id):
        """
        Resend invitation
        Requires 'staff:invite' permission

        Args:
            workspace: Workspace instance
            resender: User resending the invite
            invite_id: Invite ID to resend

        Returns:
            Updated WorkspaceInvite instance

        Raises:
            PermissionDenied: If resender lacks permission
            ValidationError: If validation fails
        """
        from workspace.core.models import WorkspaceInvite

        # CRITICAL: Check permission (NO owner bypass)
        from .permission_service import PermissionService
        if not PermissionService.has_permission(resender, workspace, 'staff:invite'):
            raise PermissionDenied("Insufficient permissions to resend invitations")

        # Get invite
        try:
            invite = WorkspaceInvite.objects.get(id=invite_id, workspace=workspace)
        except WorkspaceInvite.DoesNotExist:
            raise ValidationError("Invitation not found")

        try:
            invite.resend()

            # Log resend
            AuditLog = apps.get_model('workspace_core', 'AuditLog')
            AuditLog.log_action(
                workspace=workspace,
                user=resender,
                action='resend_invite',
                resource_type='workspace_invite',
                resource_id=str(invite.id),
                description=f"Resent invitation to '{invite.email}'"
            )

            # Send email again AFTER transaction commit
            from django.db import transaction as db_transaction
            from workspace.core.tasks import send_workspace_invitation_email

            db_transaction.on_commit(
                lambda: send_workspace_invitation_email.delay(str(invite.id))
            )

            logger.info(f"Resent invite to {invite.email} in {workspace.name} by {resender.email}")
            return invite

        except Exception as e:
            logger.error(f"Failed to resend invite: {str(e)}")
            raise

