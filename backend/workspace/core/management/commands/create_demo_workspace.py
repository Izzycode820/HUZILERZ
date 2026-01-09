"""
Management command to create demo workspace for theme preview
Creates workspace, template customization, and deployed site for demo purposes

Usage:
    python manage.py create_demo_workspace --theme=sneakers
    python manage.py create_demo_workspace --theme=sneakers --force
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from workspace.core.models import Workspace
from theme.models import Template, TemplateCustomization
from workspace.hosting.models import DeployedSite, HostingEnvironment

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo workspace for theme preview (admin-managed)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--theme',
            type=str,
            default='sneakers',
            help='Theme slug to create demo for (default: sneakers)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate if demo workspace already exists'
        )

    def handle(self, *args, **options):
        theme_slug = options['theme']
        force = options['force']

        self.stdout.write(f'\nCreating demo workspace for theme: {theme_slug}\n')

        try:
            with transaction.atomic():
                # Step 1: Get admin user (owner)
                admin_user = self._get_admin_user()
                self.stdout.write(f'Admin user: {admin_user.email}')

                # Step 2: Check if demo workspace already exists
                workspace_slug = f'{theme_slug}-demo'
                if Workspace.objects.filter(slug=workspace_slug).exists():
                    if not force:
                        raise CommandError(
                            f'Demo workspace "{workspace_slug}" already exists. Use --force to recreate.'
                        )
                    else:
                        self.stdout.write(self.style.WARNING(f'Deleting existing demo workspace: {workspace_slug}'))
                        Workspace.objects.filter(slug=workspace_slug).delete()

                # Step 3: Get theme template
                template = self._get_theme_template(theme_slug)
                self.stdout.write(f'Template: {template.name} v{template.version}')

                # Step 4: Verify template has puck config/data (from sync_themes)
                if not template.puck_config or not template.puck_data:
                    raise CommandError(
                        f'Template "{template.name}" missing puck config/data in database.\n'
                        f'Run: python manage.py sync_themes'
                    )
                self.stdout.write(f'Template has puck config/data in database')

                # Step 5: Create demo workspace
                workspace = self._create_demo_workspace(admin_user, theme_slug)
                self.stdout.write(f'Workspace created: {workspace.slug}')

                # Step 6: Create template customization (clone from Template DB)
                customization = self._create_template_customization(
                    workspace, template
                )
                self.stdout.write(f'Template customization created (cloned from DB)')

                # Step 7: Get hosting environment (admin subscription)
                hosting_env = self._get_hosting_environment(admin_user)
                self.stdout.write(f'Hosting environment ready')

                # Step 8: Create deployed site
                deployed_site = self._create_deployed_site(
                    workspace, template, customization, hosting_env, admin_user
                )
                self.stdout.write(f'Deployed site created: {deployed_site.subdomain}.huzilerz.com')

                # Success summary
                self.stdout.write(self.style.SUCCESS('\nDemo workspace created successfully'))
                self.stdout.write(f'Workspace: {workspace.name} ({workspace.slug})')
                self.stdout.write(f'Subdomain: {deployed_site.subdomain}.huzilerz.com')
                self.stdout.write(f'Local URL: http://localhost:3001')
                self.stdout.write(f'Status: {workspace.status}')
                self.stdout.write(f'\nNote: Populate with demo data using: python manage.py seed_sneakers_demo\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {str(e)}\n'))
            raise

    def _get_admin_user(self):
        """Get first superuser as owner (all admins can access via workspace dashboard)"""
        admin_user = User.objects.filter(is_superuser=True).first()

        if not admin_user:
            raise CommandError(
                'No superuser found. Please create a superuser first: '
                'python manage.py createsuperuser'
            )

        return admin_user

    def _get_theme_template(self, theme_slug):
        """Get theme template from database"""
        try:
            template = Template.objects.get(slug=theme_slug)
            return template
        except Template.DoesNotExist:
            raise CommandError(
                f'Template "{theme_slug}" not found. '
                f'Run sync_themes first: python manage.py sync_themes'
            )

    def _create_demo_workspace(self, owner, theme_slug):
        """Create demo workspace (admin-managed, accessible to all admins)"""
        # Workspace name: "Sneakers Demo" (capitalized theme name + Demo)
        theme_name = theme_slug.capitalize()
        workspace_name = f'{theme_name} Demo'
        workspace_slug = f'{theme_slug}-demo'

        workspace = Workspace.objects.create(
            name=workspace_name,
            slug=workspace_slug,
            type='store',
            owner=owner,  # One admin as owner, but all admins can access
            status='active',
            description=f'Demo workspace for {theme_name} theme with production-ready mock data',
            is_demo=True,
            is_admin_managed=True,
        )
        return workspace

    def _create_template_customization(self, workspace, template):
        """Create template customization by cloning Template's puck config/data from DB"""
        from theme.models import TemplateVersion

        # Get active/published template version
        template_version = template.versions.filter(
            status=TemplateVersion.STATUS_ACTIVE
        ).first()

        if not template_version:
            raise CommandError(
                f'No active template version found for template: {template.name}\n'
                f'Run: python manage.py sync_themes'
            )

        customization = TemplateCustomization.objects.create(
            workspace=workspace,
            template=template,
            template_version=template_version,  # Required field
            puck_config=template.puck_config,   # Clone from Template DB
            puck_data=template.puck_data,       # Clone from Template DB
            role=TemplateCustomization.ROLE_ACTIVE,
            status=TemplateCustomization.STATUS_PUBLISHED,
            is_active=True,
            version=1,
        )
        return customization

    def _get_hosting_environment(self, admin_user):
        """Get or create hosting environment for demo (admin-managed, no restrictions)"""
        # For admin demo workspaces, use existing environment or create one tied to admin's subscription
        from subscription.models import Subscription, SubscriptionPlan

        # Get or create admin subscription (for demo purposes)
        admin_subscription = Subscription.objects.filter(user=admin_user).first()

        if not admin_subscription:
            # Create enterprise plan for admin demos (unlimited resources)
            plan, _ = SubscriptionPlan.objects.get_or_create(
                tier='enterprise',
                defaults={
                    'name': 'Enterprise Plan',
                    'price_monthly': 0,  # Free for admin
                    'max_workspaces': 999,
                    'sites_limit': 999,
                    'deployment_allowed': True,
                }
            )

            # Create admin subscription (never expires for demos)
            from datetime import datetime, timezone as dt_timezone
            from django.utils import timezone

            admin_subscription = Subscription.objects.create(
                user=admin_user,
                plan=plan,
                status='active',
                started_at=timezone.now(),
                expires_at=datetime(9999, 12, 31, 23, 59, 59, tzinfo=dt_timezone.utc),  # Sentinel date: never expires
            )

        # Get or create hosting environment for admin
        hosting_env = HostingEnvironment.objects.filter(
            user=admin_user,
            subscription=admin_subscription
        ).first()

        if not hosting_env:
            hosting_env = HostingEnvironment.objects.create(
                subscription=admin_subscription,
                user=admin_user,
                infrastructure_model='SILO',  # Best infrastructure for demos
                status='active',
                storage_limit_gb=999,
                bandwidth_limit_gb=999,
                sites_limit=999,
                custom_domains_limit=999,
            )

        return hosting_env

    def _create_deployed_site(self, workspace, template, customization, hosting_env, user):
        """Create deployed site linking workspace, template, and customization (admin-managed, skip validations)"""
        # Create instance without saving (to bypass validations for admin demo)
        deployed_site = DeployedSite(
            workspace=workspace,
            template=template,
            customization=customization,
            hosting_environment=hosting_env,
            user=user,
            site_name=workspace.name,
            slug=workspace.slug,
            subdomain=workspace.slug,  # sneakers-demo
            status='active',
            template_dev_url='http://localhost:3001',
            template_cdn_url='',  # Empty for dev, will be set for production
        )

        # Save with skip_validation=True to bypass subscription/rate limit checks for admin demos
        deployed_site.save(skip_validation=True)
        return deployed_site
