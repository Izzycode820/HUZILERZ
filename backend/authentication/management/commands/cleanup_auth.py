"""
Django management command to cleanup authentication data
- Remove expired refresh tokens
- Clean up old sessions
- Archive security events
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.models import RefreshToken, UserSession, SecurityEvent


class Command(BaseCommand):
    help = 'Cleanup expired authentication data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep old sessions and events (default: 30)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_to_keep = options['days']
        
        self.stdout.write(f"Cleanup authentication data (dry_run={dry_run}, keep_days={days_to_keep})")
        
        # Cleanup expired refresh tokens
        expired_tokens = RefreshToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        if dry_run:
            self.stdout.write(f"Would delete {expired_tokens.count()} expired refresh tokens")
        else:
            deleted_count = expired_tokens.delete()[0]
            self.stdout.write(f"Deleted {deleted_count} expired refresh tokens")
        
        # Cleanup old inactive sessions
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        old_sessions = UserSession.objects.filter(
            last_activity__lt=cutoff_date,
            is_authenticated=False
        )
        
        if dry_run:
            self.stdout.write(f"Would delete {old_sessions.count()} old guest sessions")
        else:
            deleted_count = old_sessions.delete()[0]
            self.stdout.write(f"Deleted {deleted_count} old guest sessions")
        
        # Cleanup old low-risk security events
        old_events = SecurityEvent.objects.filter(
            created_at__lt=cutoff_date,
            risk_level=1,
            is_resolved=True
        )
        
        if dry_run:
            self.stdout.write(f"Would delete {old_events.count()} old low-risk security events")
        else:
            deleted_count = old_events.delete()[0]
            self.stdout.write(f"Deleted {deleted_count} old low-risk security events")
        
        # Stats
        active_tokens = RefreshToken.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        
        recent_sessions = UserSession.objects.filter(
            last_activity__gte=cutoff_date
        ).count()
        
        unresolved_events = SecurityEvent.objects.filter(
            is_resolved=False
        ).count()
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("CURRENT STATS:")
        self.stdout.write(f"Active refresh tokens: {active_tokens}")
        self.stdout.write(f"Recent user sessions: {recent_sessions}")
        self.stdout.write(f"Unresolved security events: {unresolved_events}")
        
        if unresolved_events > 0:
            self.stdout.write(
                self.style.WARNING(f"\nWarning: {unresolved_events} unresolved security events need attention!")
            )
        
        self.stdout.write(self.style.SUCCESS("Cleanup completed successfully!"))