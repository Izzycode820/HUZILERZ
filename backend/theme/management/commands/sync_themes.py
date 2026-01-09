"""
Sync themes from local file system to database
Production-ready management command for theme synchronization

Features:
- Uses ThemeDiscoveryService for scanning
- Integrates with ThemeSyncService for database sync
- Comprehensive error handling and logging
- Dry run mode for testing
- Force update option for existing themes
"""

import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

from ...services.theme_discovery_service import ThemeDiscoveryService
from ...services.theme_sync_service import ThemeSyncService


class Command(BaseCommand):
    help = 'Sync themes from local file system to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing themes'
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear discovery cache before scanning'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force_update = options.get('force', False)
        clear_cache = options.get('clear_cache', False)

        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING(' THEME SYNC STARTING'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))

        try:
            # Initialize discovery service
            self.stdout.write(' Initializing ThemeDiscoveryService...')
            discovery_service = ThemeDiscoveryService()

            # Always clear cache for management commands to ensure fresh discovery
            from django.core.cache import cache
            cache.clear()
            self.stdout.write(self.style.SUCCESS(' Cleared all caches\n'))

            # Discover themes from local file system
            self.stdout.write(' Scanning filesystem for theme manifests...')
            self.stdout.write(f' Base path: {discovery_service.THEMES_BASE_PATH}\n')

            discovery_result = discovery_service.discover_themes(force_refresh=True)

            if 'error' in discovery_result:
                self.stdout.write(
                    self.style.ERROR(f'Discovery failed: {discovery_result["error"]}')
                )
                return

            discovered_themes = discovery_result.get('themes', [])
            stats = discovery_result.get('stats', {})

            self.stdout.write(self.style.SUCCESS(f'\n Discovery complete!'))
            self.stdout.write(f' Scan stats:')
            self.stdout.write(f'  - Total scanned: {stats.get("total_scanned", 0)}')
            self.stdout.write(f'  - Valid themes: {stats.get("valid_themes", 0)}')
            self.stdout.write(f'  - Errors: {stats.get("errors", 0)}')
            self.stdout.write(f'  - Cache hits: {stats.get("cache_hits", 0)}')
            self.stdout.write(f'\n Found {len(discovered_themes)} valid themes to sync\n')

            if not discovered_themes:
                self.stdout.write(self.style.WARNING('⚠️  No themes found to sync'))
                self.stdout.write(self.style.NOTICE(f'\n💡 Check that theme-manifest.json files exist in: {discovery_service.THEMES_BASE_PATH}'))
                return

            # Process themes for database sync
            if dry_run:
                self._dry_run_sync(discovered_themes)
            else:
                self._sync_to_database(discovered_themes, force_update)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Theme synchronization failed: {str(e)}')
            )
            raise

    def _dry_run_sync(self, discovered_themes):
        """Show what would be synced without making changes"""
        self.stdout.write(self.style.WARNING('\nDRY RUN - No actual changes will be made'))
        self.stdout.write('=' * 50)

        for theme in discovered_themes:
            theme_name = theme.get('name', 'Unknown')
            template_type = theme.get('template_type', 'unknown')
            price_tier = theme.get('price_tier', 'free')
            version = theme.get('version', '1.0.0')

            self.stdout.write(f'[DRY RUN] Would sync: {theme_name}')
            self.stdout.write(f'  Type: {template_type}, Tier: {price_tier}, Version: {version}')
            self.stdout.write(f'  Slug: {theme.get("slug", "unknown")}')
            self.stdout.write('')

        self.stdout.write(f'[DRY RUN] Would sync {len(discovered_themes)} themes total')

    def _sync_to_database(self, discovered_themes, force_update):
        """Sync discovered themes to database"""
        self.stdout.write(' Syncing themes to database...\n')

        try:
            # Use ThemeSyncService for database synchronization
            sync_stats = ThemeSyncService.sync_discovered_themes(discovered_themes)

            # Display results
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS(' THEME SYNCHRONIZATION COMPLETE'))
            self.stdout.write('=' * 60)
            self.stdout.write(f'   Created: {sync_stats.get("created", 0)}')
            self.stdout.write(f'   Updated: {sync_stats.get("updated", 0)}')
            self.stdout.write(f'   Errors: {sync_stats.get("errors", 0)}')
            self.stdout.write(f'   Total Processed: {sync_stats.get("total_processed", 0)}')

            if sync_stats.get('errors', 0) > 0:
                self.stdout.write(
                    self.style.WARNING('\n  Some themes failed to sync. Check logs for details.')
                )
            else:
                self.stdout.write(self.style.SUCCESS('\n All themes synced successfully!'))

            # Clear discovery cache after successful sync
            from django.core.cache import cache
            cache.clear()
            self.stdout.write(self.style.SUCCESS(' Cleared discovery cache\n'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n Database sync failed: {str(e)}')
            )
            raise