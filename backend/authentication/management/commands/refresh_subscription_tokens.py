"""
Management command to refresh JWT tokens with subscription claims
Useful for migrating existing tokens or batch updates
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refresh JWT tokens with subscription claims for all users or specific user'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='Refresh tokens for specific user ID'
        )
        
        parser.add_argument(
            '--email',
            type=str,
            help='Refresh tokens for specific user email'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing users (default: 100)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be refreshed without actually doing it'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh even if tokens are recently updated'
        )
    
    def handle(self, *args, **options):
        """Execute the command"""
        try:
            if options['user_id']:
                self.refresh_user_tokens_by_id(options['user_id'], options)
            elif options['email']:
                self.refresh_user_tokens_by_email(options['email'], options)
            else:
                self.refresh_all_user_tokens(options)
                
        except Exception as e:
            logger.error(f"Token refresh command failed: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Command failed: {str(e)}')
            )
            return
    
    def refresh_user_tokens_by_id(self, user_id, options):
        """Refresh tokens for specific user by ID"""
        try:
            user = User.objects.get(id=user_id)
            self.refresh_user_subscription_claims(user, options)
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} not found')
            )
    
    def refresh_user_tokens_by_email(self, email, options):
        """Refresh tokens for specific user by email"""
        try:
            user = User.objects.get(email=email)
            self.refresh_user_subscription_claims(user, options)
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found')
            )
    
    def refresh_all_user_tokens(self, options):
        """Refresh tokens for all active users"""
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        total_users = User.objects.filter(is_active=True).count()
        
        self.stdout.write(
            f'Processing {total_users} active users in batches of {batch_size}'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual changes will be made')
            )
        
        processed = 0
        success_count = 0
        error_count = 0
        
        for batch_start in range(0, total_users, batch_size):
            batch_end = min(batch_start + batch_size, total_users)
            
            self.stdout.write(
                f'Processing batch {batch_start + 1}-{batch_end} of {total_users}'
            )
            
            users_batch = User.objects.filter(
                is_active=True
            )[batch_start:batch_end]
            
            for user in users_batch:
                try:
                    if not dry_run:
                        result = self.refresh_user_subscription_claims(user, options, verbose=False)
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        self.stdout.write(f'Would refresh: {user.email}')
                        success_count += 1
                    
                    processed += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f'Failed to refresh tokens for user {user.id}: {str(e)}')
            
            # Progress update
            self.stdout.write(
                f'Batch complete. Processed: {processed}, Success: {success_count}, Errors: {error_count}'
            )
        
        # Final summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Token refresh complete. Total processed: {processed}, '
                f'Success: {success_count}, Errors: {error_count}'
            )
        )
    
    def refresh_user_subscription_claims(self, user, options, verbose=True):
        """
        Refresh subscription claims for a specific user
        
        Args:
            user: User instance
            options: Command options
            verbose: Whether to output progress messages
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from subscription.services.subscription_claims_service import SubscriptionClaimsService
            from authentication.services.jwt_subscription_service import JWTSubscriptionService
            
            dry_run = options.get('dry_run', False)
            force = options.get('force', False)
            
            if verbose:
                self.stdout.write(f'Processing user: {user.email} (ID: {user.id})')
            
            # Check if user has subscription
            has_subscription = False
            subscription_info = "No subscription"
            
            try:
                from subscription.models import Subscription
                subscription = Subscription.objects.filter(
                    user=user,
                    status__in=['active', 'grace_period']
                ).first()
                
                if subscription:
                    has_subscription = True
                    subscription_info = f"{subscription.plan.tier} - {subscription.status}"
            except Exception:
                pass
            
            if verbose:
                self.stdout.write(f'  Subscription: {subscription_info}')
            
            if not dry_run:
                # Clear existing cache
                JWTSubscriptionService.invalidate_subscription_cache(user.id)
                
                # Generate new claims
                new_claims = SubscriptionClaimsService.refresh_user_subscription_claims(user.id)
                
                if new_claims:
                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Claims refreshed for {user.email}')
                        )
                        self.stdout.write(f'    Tier: {new_claims.get("tier", "unknown")}')
                        self.stdout.write(f'    Features: {new_claims.get("features_bitmap", 0)}')
                    
                    return True
                else:
                    if verbose:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Failed to refresh claims for {user.email}')
                        )
                    return False
            else:
                if verbose:
                    self.stdout.write(f'  Would refresh claims for {user.email}')
                return True
                
        except Exception as e:
            if verbose:
                self.stdout.write(
                    self.style.ERROR(f'  Error processing {user.email}: {str(e)}')
                )
            logger.error(f'Token refresh error for user {user.id}: {str(e)}')
            return False
    
    def validate_subscription_claims(self, user):
        """
        Validate subscription claims for debugging
        
        Args:
            user: User instance
            
        Returns:
            dict: Validation result
        """
        try:
            from authentication.services.jwt_subscription_service import JWTSubscriptionService
            
            claims = JWTSubscriptionService.create_subscription_claims(user)
            
            validation_result = {
                'valid': True,
                'tier': claims.get('tier', 'unknown'),
                'status': claims.get('status', 'unknown'),
                'features_count': bin(claims.get('features_bitmap', 0)).count('1'),
                'expires_at': claims.get('expires_at'),
                'usage_hash': claims.get('usage_hash')
            }
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }