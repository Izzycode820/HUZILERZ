"""
Django management command to setup authentication system
- Create superuser if needed
- Configure settings
- Run initial migrations
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import secrets

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup authentication system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a superuser if none exists',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Superuser email',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Superuser password',
        )

    def handle(self, *args, **options):
        self.stdout.write("Setting up authentication system...")
        
        # Check JWT settings
        if not hasattr(settings, 'JWT_SECRET_KEY'):
            self.stdout.write(
                self.style.WARNING(
                    "JWT_SECRET_KEY not found in settings. Generate one with: "
                    "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            )
        
        # Check token lifetime settings
        if not hasattr(settings, 'ACCESS_TOKEN_LIFETIME_MINUTES'):
            self.stdout.write(
                self.style.WARNING(
                    "ACCESS_TOKEN_LIFETIME_MINUTES not set. Add to settings.py: ACCESS_TOKEN_LIFETIME_MINUTES = 30"
                )
            )
        
        if not hasattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS'):
            self.stdout.write(
                self.style.WARNING(
                    "REFRESH_TOKEN_LIFETIME_DAYS not set. Add to settings.py: REFRESH_TOKEN_LIFETIME_DAYS = 7"
                )
            )
        
        # Create superuser if requested
        if options['create_superuser']:
            if not User.objects.filter(is_superuser=True).exists():
                email = options.get('email') or input('Superuser email: ')
                password = options.get('password') or input('Superuser password: ')
                
                if email and password:
                    try:
                        superuser = User.objects.create_superuser(
                            email=email,
                            username=email.split('@')[0],
                            password=password,
                            first_name='Super',
                            last_name='User'
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'Superuser created: {superuser.email}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to create superuser: {e}')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR('Email and password are required')
                    )
            else:
                self.stdout.write('Superuser already exists')
        
        # Show configuration summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("AUTHENTICATION CONFIGURATION:")
        self.stdout.write(f"JWT Secret Key: {'✓ Set' if hasattr(settings, 'JWT_SECRET_KEY') else '✗ Missing'}")
        self.stdout.write(f"Access Token Lifetime: {getattr(settings, 'ACCESS_TOKEN_LIFETIME_MINUTES', 'Not set')} minutes")
        self.stdout.write(f"Refresh Token Lifetime: {getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 'Not set')} days")
        self.stdout.write(f"Debug Mode: {settings.DEBUG}")
        
        superuser_count = User.objects.filter(is_superuser=True).count()
        user_count = User.objects.count()
        
        self.stdout.write(f"\nUsers: {user_count} total, {superuser_count} superusers")
        
        self.stdout.write(self.style.SUCCESS("\nAuthentication setup completed!"))