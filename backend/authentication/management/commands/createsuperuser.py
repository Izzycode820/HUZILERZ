"""
Custom createsuperuser command for HustlerzCamp - Simple Version
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import getpass

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser account'

    def handle(self, *args, **options):
        # Simple prompts
        name = input('Name (default: babayaga): ').strip() or 'babayaga'
        email = input('Email: ').strip().lower()
        
        # Validate email
        if not email:
            self.stdout.write(self.style.ERROR('Email is required!'))
            return
            
        # Check email exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR('User already exists!'))
            return
        
        password = getpass.getpass('Password: ')
        if len(password) < 8:
            self.stdout.write(self.style.ERROR('Password must be at least 8 characters!'))
            return

        # Create username from name
        username = name.lower().replace(' ', '')
        
        # Ensure unique username
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1

        # Create superuser
        user = User.objects.create_superuser(
            email=email,
            username=username,
            password=password,
            first_name=name.split()[0] if ' ' in name else name,
            last_name=' '.join(name.split()[1:]) if ' ' in name else '',
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Superuser created!\n'
                f'Login: {username} / [your password]'
            )
        )