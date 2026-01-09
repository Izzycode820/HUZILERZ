"""
Membership Email Tasks
Handles async email sending for workspace membership events

Following industry pattern:
- Authorization is synchronous
- Side-effects (emails) are asynchronous
- Emails sent AFTER transaction commit

PRODUCTION EMAIL SETUP:
- Development: Django SMTP (console backend for testing)
- Production: AWS SES (Simple Email Service)
  * Cheapest option: $0.10 per 1,000 emails
  * Integrates with our AWS infrastructure
  * Handles deliverability, bounce management, DKIM/SPF
  * Scales automatically
  * Configure via django-ses or boto3

Alternative: SendGrid (generous free tier), but AWS SES is preferred
due to cost and infrastructure alignment.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    name='workspace.send_workspace_invitation_email'
)
def send_workspace_invitation_email(self, invite_id):
    """
    Send workspace invitation email
    Triggered after WorkspaceInvite is created and committed

    Args:
        invite_id: UUID string of WorkspaceInvite

    Retries: 3 times with 5 minute delay
    """
    try:
        from workspace.core.models import WorkspaceInvite

        # Get invite
        invite = WorkspaceInvite.objects.select_related(
            'workspace', 'invited_by'
        ).prefetch_related('roles').get(id=invite_id)

        # Get role names for display
        role_names = ', '.join([r.name for r in invite.roles.all()]) or 'Team Member'

        # Build invitation URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        invite_url = f"{frontend_url}/invite/accept?token={invite.token}"

        # Email subject
        subject = f"Invitation to join {invite.workspace.name}"

        # Email body
        inviter_name = invite.invited_by.email if invite.invited_by else 'Someone'
        message = f"""
Hi,

{inviter_name} has invited you to join the workspace "{invite.workspace.name}" as a {role_names}.

Click the link below to accept the invitation:
{invite_url}

This invitation will expire on {invite.expires_at.strftime('%B %d, %Y at %I:%M %p')}.

If you don't have an account yet, you'll be prompted to create one.

Best regards,
The Team
        """

        # HTML version (optional, for better formatting)
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">You've been invited!</h2>

                <p>Hi,</p>

                <p><strong>{inviter_name}</strong> has invited you to join the workspace
                <strong>"{invite.workspace.name}"</strong> as a <strong>{role_names}</strong>.</p>

                <div style="margin: 30px 0;">
                    <a href="{invite_url}"
                       style="background-color: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Accept Invitation
                    </a>
                </div>

                <p style="color: #666; font-size: 14px;">
                    This invitation will expire on {invite.expires_at.strftime('%B %d, %Y at %I:%M %p')}.
                </p>

                <p style="color: #666; font-size: 14px;">
                    If you don't have an account yet, you'll be prompted to create one.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #999; font-size: 12px;">
                    If you're having trouble clicking the button, copy and paste this URL into your browser:<br>
                    {invite_url}
                </p>
            </div>
        </body>
        </html>
        """

        # Send email
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invite.email],
            fail_silently=False
        )

        logger.info(
            f"✓ Invitation email sent to {invite.email} "
            f"for workspace {invite.workspace.name} (invite_id: {invite_id})"
        )

    except Exception as exc:
        logger.error(
            f"✗ Failed to send invitation email (invite_id: {invite_id}): {exc}"
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    name='workspace.send_role_changed_notification'
)
def send_role_changed_notification(self, membership_id, old_role_name, new_role_name, changed_by_email):
    """
    Send notification email when member's role is changed
    Triggered after membership role change is committed

    Args:
        membership_id: UUID string of Membership
        old_role_name: Previous role name
        new_role_name: New role name
        changed_by_email: Email of user who made the change

    Retries: 3 times with 5 minute delay
    """
    try:
        from workspace.core.models import Membership

        # Get membership
        membership = Membership.objects.select_related(
            'user', 'workspace'
        ).prefetch_related('roles').get(id=membership_id)

        subject = f"Your role in {membership.workspace.name} has been updated"

        message = f"""
Hi {membership.user.email},

Your role in the workspace "{membership.workspace.name}" has been changed from {old_role_name} to {new_role_name} by {changed_by_email}.

Your new permissions are now active.

Best regards,
The Team
        """

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Role Updated</h2>

                <p>Hi {membership.user.email},</p>

                <p>Your role in the workspace <strong>"{membership.workspace.name}"</strong> has been changed:</p>

                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;">
                        <span style="color: #ef4444; text-decoration: line-through;">{old_role_name}</span>
                        →
                        <span style="color: #10b981; font-weight: bold;">{new_role_name}</span>
                    </p>
                </div>

                <p style="color: #666; font-size: 14px;">
                    Changed by: <strong>{changed_by_email}</strong>
                </p>

                <p>Your new permissions are now active.</p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #999; font-size: 12px;">
                    If you have questions about this change, please contact {changed_by_email}.
                </p>
            </div>
        </body>
        </html>
        """

        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[membership.user.email],
            fail_silently=False
        )

        logger.info(
            f"✓ Role change notification sent to {membership.user.email} "
            f"({old_role_name} → {new_role_name})"
        )

    except Exception as exc:
        logger.error(
            f"✗ Failed to send role change notification (membership_id: {membership_id}): {exc}"
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    name='workspace.send_member_removed_notification'
)
def send_member_removed_notification(self, user_email, workspace_name, removed_by_email):
    """
    Send notification email when member is removed from workspace
    Triggered after membership is suspended/removed

    Args:
        user_email: Email of removed user
        workspace_name: Name of workspace
        removed_by_email: Email of user who removed them

    Retries: 3 times with 5 minute delay
    """
    try:
        subject = f"You've been removed from {workspace_name}"

        message = f"""
Hi {user_email},

You have been removed from the workspace "{workspace_name}" by {removed_by_email}.

You no longer have access to this workspace.

If you believe this was done in error, please contact {removed_by_email}.

Best regards,
The Team
        """

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #ef4444;">Access Removed</h2>

                <p>Hi {user_email},</p>

                <p>You have been removed from the workspace <strong>"{workspace_name}"</strong> by {removed_by_email}.</p>

                <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #991b1b;">
                        You no longer have access to this workspace.
                    </p>
                </div>

                <p>If you believe this was done in error, please contact <strong>{removed_by_email}</strong>.</p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            </div>
        </body>
        </html>
        """

        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False
        )

        logger.info(
            f"✓ Removal notification sent to {user_email} for workspace {workspace_name}"
        )

    except Exception as exc:
        logger.error(
            f"✗ Failed to send removal notification to {user_email}: {exc}"
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    name='workspace.send_welcome_to_workspace_email'
)
def send_welcome_to_workspace_email(self, membership_id):
    """
    Send welcome email when user accepts invitation and joins workspace
    Triggered after invite is accepted and membership is created

    Args:
        membership_id: UUID string of newly created Membership

    Retries: 3 times with 5 minute delay
    """
    try:
        from workspace.core.models import Membership

        # Get membership
        membership = Membership.objects.select_related(
            'user', 'workspace'
        ).prefetch_related('roles').get(id=membership_id)

        # Get role names for display
        role_names = ', '.join([r.name for r in membership.roles.all()]) or 'Team Member'

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        workspace_url = f"{frontend_url}/workspace/{membership.workspace.slug}"

        subject = f"Welcome to {membership.workspace.name}!"

        message = f"""
Hi {membership.user.email},

Welcome to "{membership.workspace.name}"!

You've joined as a {role_names}. You can now access the workspace at:
{workspace_url}

Best regards,
The Team
        """

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #10b981;">Welcome aboard! 🎉</h2>

                <p>Hi {membership.user.email},</p>

                <p>Welcome to <strong>"{membership.workspace.name}"</strong>!</p>

                <p>You've joined as a <strong>{role_names}</strong>.</p>

                <div style="margin: 30px 0;">
                    <a href="{workspace_url}"
                       style="background-color: #10b981; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Go to Workspace
                    </a>
                </div>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #999; font-size: 12px;">
                    Workspace URL: {workspace_url}
                </p>
            </div>
        </body>
        </html>
        """

        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[membership.user.email],
            fail_silently=False
        )

        logger.info(
            f"✓ Welcome email sent to {membership.user.email} "
            f"for workspace {membership.workspace.name}"
        )

    except Exception as exc:
        logger.error(
            f"✗ Failed to send welcome email (membership_id: {membership_id}): {exc}"
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
