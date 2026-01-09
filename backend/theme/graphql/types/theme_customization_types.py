"""
Theme Customization GraphQL Types - AUTHENTICATED + WORKSPACE SCOPED

Provides types for user's theme library and customizations
Requires authentication and workspace ownership validation
"""

import graphene
from graphene_django import DjangoObjectType
from theme.models import TemplateCustomization
from .common_types import BaseConnection


class ThemeCustomizationType(DjangoObjectType):
    """
    User's theme customization in their library

    Contains user's puck data/config for the Puck editor
    Workspace-scoped - only accessible to workspace owner
    """

    id = graphene.ID(required=True)

    # Computed fields
    theme_slug = graphene.String()
    is_published = graphene.Boolean()
    is_draft = graphene.Boolean()
    can_delete = graphene.Boolean()

    # Password protection fields (from DeployedSite)
    # Only meaningful for published themes - returns False/None for drafts
    is_password_protected = graphene.Boolean(
        description="Whether the published storefront is password protected"
    )
    storefront_password = graphene.String(
        description="Current password for password-protected storefront (for merchant to share)"
    )

    class Meta:
        model = TemplateCustomization
        fields = (
            'id',

            # Relationships (template only - workspace/users accessed via context)
            'template', 'theme_name',

            # User's customized data (for Puck editor)
            'puck_config', 'puck_data',

            # Status
            'is_active',

            # Timestamps
            'published_at', 'created_at', 'last_edited_at',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        """Return plain UUID"""
        return str(self.id)

    def resolve_theme_slug(self, info):
        """
        Get theme slug for registry lookup

        Frontend uses this to load components:
        THEME_REGISTRY[themeSlug] → import('@themes/sneakers')
        """
        return self.template.slug if self.template else None

    def resolve_is_published(self, info):
        """Check if this theme is currently published (live)"""
        return self.is_active

    def resolve_is_draft(self, info):
        """Check if this theme is a draft (not published)"""
        return not self.is_active

    def resolve_can_delete(self, info):
        """
        Check if this theme can be deleted

        Active (published) themes cannot be deleted
        Must publish another theme first
        """
        return not self.is_active

    def resolve_is_password_protected(self, info):
        """
        Check if workspace's deployed site requires password

        Returns:
            bool: True if password protection is enabled, False otherwise

        Error Handling:
            Returns False if DeployedSite doesn't exist (graceful degradation)

        Performance:
            Uses select_related workspace from parent query when available
        """
        try:
            from workspace.hosting.models import DeployedSite

            # Get active deployed site for this workspace
            deployed_site = DeployedSite.objects.filter(
                workspace=self.workspace,
                status='active'
            ).only('password_protection_enabled', 'password_hash').first()

            if deployed_site:
                return deployed_site.requires_password

            return False

        except Exception:
            # Graceful degradation - don't crash if lookup fails
            return False

    def resolve_storefront_password(self, info):
        """
        Return current plaintext password for merchant to share

        Shopify pattern: Password is shown to merchant so they can share it

        Returns:
            str or None: Password if protected, None otherwise

        Security:
            Only returns password if protection is enabled
            Password is only meaningful when requires_password is True

        Error Handling:
            Returns None if DeployedSite doesn't exist (graceful degradation)
        """
        try:
            from workspace.hosting.models import DeployedSite

            # Get active deployed site for this workspace
            deployed_site = DeployedSite.objects.filter(
                workspace=self.workspace,
                status='active'
            ).only(
                'password_protection_enabled',
                'password_hash',
                'password_plaintext'
            ).first()

            if deployed_site and deployed_site.requires_password:
                return deployed_site.password_plaintext

            return None

        except Exception:
            # Graceful degradation - don't crash if lookup fails
            return None


class ThemeCustomizationConnection(graphene.relay.Connection):
    """
    Theme customization connection for user's library
    """
    class Meta:
        node = ThemeCustomizationType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        """Return total count of user's themes"""
        return self.iterable.count()
