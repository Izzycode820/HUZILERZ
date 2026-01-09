"""
Django Management Command: Verify Media Cleanup Signals

Usage:
    python manage.py verify_media_signals

This command verifies that all media cleanup signals are properly registered.
"""

from django.core.management.base import BaseCommand
from workspace.store.signals.media_signals import verify_signals_connected


class Command(BaseCommand):
    help = 'Verify that media cleanup signals are properly registered'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Verifying media cleanup signals...'))

        all_connected = verify_signals_connected()

        if all_connected:
            self.stdout.write(
                self.style.SUCCESS('\n✓ All media cleanup signals are properly connected!')
            )
            self.stdout.write(
                self.style.SUCCESS(
                    '\nMedia files will be automatically cleaned up when:\n'
                    '  - Products are deleted\n'
                    '  - Categories are deleted\n'
                    '  - Collections are deleted\n'
                    '  - Media is removed from products\n'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n✗ Some signals are NOT connected!')
            )
            self.stdout.write(
                self.style.ERROR(
                    '\nCheck workspace/store/apps.py - '
                    'signals should be imported in the ready() method'
                )
            )
