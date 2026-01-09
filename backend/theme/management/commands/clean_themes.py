"""
Clean all theme-related data from database and caches
Management command to provide a fresh start for theme system

Usage:
    python manage.py clean_themes
    python manage.py clean_themes --keep-customizations
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import transaction

from theme.models.template import Template
from theme.models.template_version import TemplateVersion
from theme.models.template_asset import TemplateAsset
from theme.models.template_category import TemplateCategory
from theme.models.template_customization import TemplateCustomization
from theme.models.customization_history import CustomizationHistory
from theme.models.sync_models import UpdateNotification, SyncLog


class Command(BaseCommand):
    help = 'Clean all theme-related data from database and caches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-customizations',
            action='store_true',
            help='Keep user customizations (only clean theme templates)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        keep_customizations = options.get('keep_customizations', False)
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('🧹 THEME CLEANUP STARTING'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))

        if dry_run:
            self.stdout.write(self.style.NOTICE('🔍 DRY RUN MODE - No actual deletions\n'))

        try:
            with transaction.atomic():
                # Count records before deletion
                template_count = Template.objects.count()
                version_count = TemplateVersion.objects.count()
                asset_count = TemplateAsset.objects.count()
                category_count = TemplateCategory.objects.count()
                customization_count = TemplateCustomization.objects.count()
                history_count = CustomizationHistory.objects.count()
                notification_count = UpdateNotification.objects.count()
                sync_log_count = SyncLog.objects.count()

                self.stdout.write('📊 Current database state:')
                self.stdout.write(f'  - Templates: {template_count}')
                self.stdout.write(f'  - Template Versions: {version_count}')
                self.stdout.write(f'  - Template Assets: {asset_count}')
                self.stdout.write(f'  - Categories: {category_count}')
                self.stdout.write(f'  - Customizations: {customization_count}')
                self.stdout.write(f'  - Customization History: {history_count}')
                self.stdout.write(f'  - Update Notifications: {notification_count}')
                self.stdout.write(f'  - Sync Logs: {sync_log_count}\n')

                if not dry_run:
                    # Delete in correct order (respect foreign keys)
                    if not keep_customizations:
                        self.stdout.write('🗑️  Deleting customization history...')
                        CustomizationHistory.objects.all().delete()

                        self.stdout.write('🗑️  Deleting update notifications...')
                        UpdateNotification.objects.all().delete()

                        self.stdout.write('🗑️  Deleting customizations...')
                        TemplateCustomization.objects.all().delete()

                    self.stdout.write('🗑️  Deleting sync logs...')
                    SyncLog.objects.all().delete()

                    self.stdout.write('🗑️  Deleting template assets...')
                    TemplateAsset.objects.all().delete()

                    self.stdout.write('🗑️  Deleting template versions...')
                    TemplateVersion.objects.all().delete()

                    self.stdout.write('🗑️  Deleting templates...')
                    Template.objects.all().delete()

                    # Keep categories as they can be reused
                    # TemplateCategory.objects.all().delete()

                    self.stdout.write(self.style.SUCCESS('\n✅ Database cleaned successfully'))

                    # Clear Redis cache
                    self.stdout.write('\n🧹 Clearing Redis cache...')
                    cache.clear()
                    self.stdout.write(self.style.SUCCESS('✅ Cache cleared successfully'))

                else:
                    self.stdout.write(self.style.NOTICE('\n🔍 DRY RUN: Would delete all records above'))

            self.stdout.write(self.style.WARNING('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('✅ CLEANUP COMPLETE'))
            self.stdout.write(self.style.WARNING('='*60 + '\n'))

            if not dry_run:
                self.stdout.write(self.style.SUCCESS(
                    '\n💡 Next step: Run "python manage.py sync_themes" to discover themes from filesystem\n'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during cleanup: {str(e)}'))
            raise
