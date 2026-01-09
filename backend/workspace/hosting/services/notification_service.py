"""
Storefront Notification Service (Concern #2)

Handles notifications for storefront events:
- Default password provisioning
- Password changes
- Site visibility changes

TODO: Implement notification delivery methods
- Email via existing email service
- In-app notifications
- SMS for Cameroon market (future)
"""
import logging

logger = logging.getLogger(__name__)


class StorefrontNotificationService:
    """
    Service for sending storefront-related notifications

    TODO: Implement actual notification delivery
    Current: Logs notification (placeholder)
    Future: Email, in-app, SMS
    """

    @staticmethod
    def notify_default_password(deployed_site, default_password: str):
        """
        Notify user about auto-generated storefront password

        Args:
            deployed_site: DeployedSite instance
            default_password: Plain text password (for notification only)

        TODO: Implement email delivery
        - Subject: "Your Storefront is Password Protected"
        - Body: Password + instructions to disable/change
        - Template: storefront_password_notification.html
        """
        logger.info(
            f"[TODO] Send password notification for DeployedSite {deployed_site.id} "
            f"to user {deployed_site.user.email} - "
            f"Password: {default_password}"
        )

        # TODO: Implement email sending
        # from core.services.email_service import EmailService
        # EmailService.send_storefront_password_notification(
        #     user=deployed_site.user,
        #     site_name=deployed_site.site_name,
        #     password=default_password,
        #     subdomain=deployed_site.subdomain
        # )
