"""
Django management command to run order tests
Usage: python manage.py test_orders
"""

from django.core.management.base import BaseCommand
from django.test.utils import get_runner
from django.conf import settings


class Command(BaseCommand):
    help = 'Run comprehensive order tests with real authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        verbosity = 2 if options['verbose'] else 1

        self.stdout.write(
            self.style.SUCCESS('🚀 Running Order Tests...')
        )
        self.stdout.write("=" * 50)

        # Run order tests
        test_runner = get_runner(settings)
        runner = test_runner(verbosity=verbosity, interactive=False)

        test_suite = runner.build_suite([
            'workspace.store.tests.orders.test_order_queries',
            'workspace.store.tests.orders.test_order_mutations'
        ])

        result = runner.run_suite(test_suite)

        self.stdout.write("=" * 50)
        if result.wasSuccessful():
            self.stdout.write(
                self.style.SUCCESS('✅ All order tests passed!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Some order tests failed!')
            )