"""
Seed system permissions and roles
One-time setup command to initialize the permission system

Run this ONCE after deploying the new permission system:
    python manage.py seed_permissions

This command:
1. Creates all system permissions (product:create, order:refund, etc.)
2. Creates system roles (Owner, Admin, Staff, ReadOnly)
3. Assigns permissions to each role

Idempotent: Safe to run multiple times
"""

from django.core.management.base import BaseCommand
from workspace.core.services import RoleService


class Command(BaseCommand):
    help = 'Seed system permissions and roles (one-time setup)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-seed even if permissions already exist',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('SEEDING SYSTEM PERMISSIONS & ROLES'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        try:
            # Initialize system roles and permissions
            result = RoleService.initialize_system_roles_and_permissions()

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('[OK] SEEDING COMPLETED'))
            self.stdout.write('')
            self.stdout.write(f"  Permissions created: {result['permissions_created']}")
            self.stdout.write(f"  System roles created: {result['system_roles_created']}")
            self.stdout.write('')

            # Show created system roles
            from workspace.core.models import Role, RolePermission

            system_roles = Role.objects.filter(workspace=None, is_system=True)

            self.stdout.write(self.style.SUCCESS('System Roles:'))
            for role in system_roles:
                permission_count = RolePermission.objects.filter(role=role).count()
                self.stdout.write(f"  - {role.name}: {permission_count} permissions")

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('NEXT STEPS:'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write('1. Existing workspaces will need roles provisioned manually')
            self.stdout.write('2. New workspaces will auto-provision roles on creation')
            self.stdout.write('3. Workspace owners will automatically get Owner role')
            self.stdout.write('')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('[FAILED] SEEDING FAILED'))
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            self.stdout.write('')
            raise
