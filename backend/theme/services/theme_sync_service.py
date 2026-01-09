"""
Theme Sync Service
Syncs discovered themes to database.
Used by: python manage.py sync_themes

Features:
- Syncs themes from discovery service to database
- Handles create/update operations for Template records
- Comprehensive error handling and logging

After cleanup: Only database sync logic remains (no REST API formatting)
"""

import logging
from typing import Dict, List, Any
from pathlib import Path
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


class ThemeSyncService:
    """
    Syncs discovered themes to database.
    Used by: python manage.py sync_themes
    """




    @classmethod
    def sync_discovered_themes(cls, discovered_themes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync discovered themes with database
        """
        try:
            with transaction.atomic():
                stats = {
                    'created': 0,
                    'updated': 0,
                    'errors': 0,
                    'total_processed': len(discovered_themes)
                }

                for theme_data in discovered_themes:
                    try:
                        result = cls._sync_single_theme(theme_data)
                        if result == 'created':
                            stats['created'] += 1
                        elif result == 'updated':
                            stats['updated'] += 1
                    except Exception as e:
                        logger.error(f"Failed to sync theme {theme_data.get('name', 'Unknown')}: {str(e)}")
                        stats['errors'] += 1

                logger.info(f"Theme sync completed: {stats}")
                return stats

        except Exception as e:
            logger.error(f"Theme sync failed: {str(e)}")
            return {'error': str(e), 'created': 0, 'updated': 0, 'errors': 1}

    @classmethod
    def _sync_single_theme(cls, theme_data: Dict[str, Any]) -> str:
        """
        Sync single theme to database and create published template version
        """
        try:
            from ..models import Template, TemplateVersion
            from django.contrib.auth import get_user_model

            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()

            # Generate consistent slug
            from django.utils.text import slugify
            theme_name = theme_data.get('name', '').strip()
            template_type = theme_data.get('template_type', '').strip()

            if not theme_name or not template_type:
                logger.error(f"Missing required theme data - name: '{theme_name}', type: '{template_type}'")
                raise ValueError("Theme name and template type are required")

            # Generate enterprise-grade slug: type-name (e.g., "ecommerce-kendustore")
            base_slug = slugify(f"{template_type}-{theme_name}")

            if not base_slug:
                logger.error(f"Failed to generate valid slug for theme: {theme_data}")
                raise ValueError("Cannot generate valid slug from theme data")


            # Construct manifest_url from dev_path if available
            # Pattern: Same as entry file conversion in theme_discovery_service.py
            manifest_url = ''
            dev_path = theme_data.get('dev_path', '')
            if dev_path:
                # Convert to proxy URL for local development (browsers can't load file://)
                manifest_file = Path(dev_path) / 'theme-manifest.json'
                if manifest_file.exists():
                    # Get relative path from themes root (same as discovery service)
                    themes_root = Path(settings.THEMES_ROOT).resolve()
                    try:
                        relative_path = manifest_file.resolve().relative_to(themes_root)
                        manifest_url = f"http://localhost:8000/api/themes/local-proxy/{relative_path.as_posix()}"
                        logger.info(f"Generated proxy manifest_url: {manifest_url}")
                    except ValueError:
                        # File is not under themes_root, fallback to file:// (won't work in browser but better than nothing)
                        manifest_url = f"file:///{manifest_file.as_posix()}"
                        logger.warning(f"Manifest file not under themes root, using file:// URL: {manifest_url}")

            # Prepare theme data for database using NEW manifest-based fields
            theme_defaults = {
                'name': theme_data.get('name', 'Unnamed Theme'),
                'description': theme_data.get('description', ''),
                'template_type': theme_data.get('template_type', 'ecommerce'),
                'workspace_types': [theme_data.get('workspace_type', 'store')],
                # Metadata from manifest
                'features': theme_data.get('features', []),
                'tags': theme_data.get('tags', []),
                'compatibility': theme_data.get('compatibility', {}),
                'author': theme_data.get('author', ''),
                'license': theme_data.get('license', ''),
                # Pricing
                'price_tier': theme_data.get('price_tier', 'free'),
                'price_amount': theme_data.get('price_amount', 0.0),
                'version': theme_data.get('version', '1.0.0'),
                # Manifest URLs
                'manifest_url': manifest_url,
                # Puck data
                'puck_config': theme_data.get('puck_config', {}),
                'puck_data': theme_data.get('puck_data', {}),
                # Media
                'preview_image': theme_data.get('preview_image', ''),
                'demo_url': theme_data.get('demo_url', ''),
                'showcase_sections': theme_data.get('showcase_sections', []),
                # Status and metrics
                'status': 'active',
                'view_count': 0,
                'download_count': 0,
            }

            # Check if theme exists by slug
            try:
                theme = Template.objects.get(slug=base_slug)
                # Update existing theme
                for key, value in theme_defaults.items():
                    setattr(theme, key, value)
                theme.save()
                created = False
                logger.info(f"Updated existing theme: {theme.slug} (UUID: {theme.id})")
            except Template.DoesNotExist:
                # Create new theme - Django auto-generates UUID as primary key
                theme = Template.objects.create(
                    slug=base_slug,
                    **theme_defaults
                )
                created = True
                logger.info(f"Created new theme: {theme.slug} (UUID: {theme.id})")

            # Create published template version if it doesn't exist
            if created or not theme.versions.filter(status=TemplateVersion.STATUS_ACTIVE).exists():
                version_number = theme_data.get('version', '1.0.0')

                # Create template version
                TemplateVersion.objects.create(
                    template=theme,
                    version=version_number,
                    status=TemplateVersion.STATUS_ACTIVE,
                    changelog='Initial published version from theme sync',
                    cdn_path=f"themes/{theme.slug}/{version_number}/",
                    puck_config=theme.puck_config or {},
                    created_by=admin_user
                )
                logger.info(f"Created published template version {version_number} for theme: {theme.slug}")

            return 'created' if created else 'updated'

        except Exception as e:
            logger.error(f"Failed to sync theme to database: {str(e)}")
            raise