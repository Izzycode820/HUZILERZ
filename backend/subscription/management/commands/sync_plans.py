"""
Sync Subscription Plans from YAML to Database

Usage: python manage.py sync_plans

Syncs plans.yaml to SubscriptionPlan table:
- Creates missing plans
- Updates pricing
- Deactivates removed plans
- Validates YAML structure
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from subscription.models import SubscriptionPlan
from subscription.services.capability_engine import CapabilityEngine


class Command(BaseCommand):
    help = 'Sync subscription plans from plans.yaml to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate YAML without syncing to database',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting plan sync from plans.yaml...'))

        # Validate YAML first
        try:
            CapabilityEngine.validate_plans_yaml()
            self.stdout.write(self.style.SUCCESS('[OK] plans.yaml validation passed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] YAML validation failed: {str(e)}'))
            return

        if options['validate_only']:
            self.stdout.write(self.style.SUCCESS('Validation complete (--validate-only mode)'))
            return

        # Load plans from YAML
        plans_data = CapabilityEngine.load_plans_yaml()
        yaml_tiers = plans_data.get('tiers', {})

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for tier_slug, tier_data in yaml_tiers.items():
                # Map tier slug to display name
                tier_display_name = tier_slug.title()

                # Extract pricing structure (nested)
                pricing = tier_data.get('pricing', {})
                intro = pricing.get('intro', {})
                regular = pricing.get('regular', {})

                # Get prices from nested structure
                intro_price = Decimal(str(intro.get('price', 0)))
                intro_duration_days = int(intro.get('duration_days', 28))
                regular_price_monthly = Decimal(str(regular.get('monthly', 0)))
                regular_price_yearly = Decimal(str(regular.get('yearly', 0)))

                # Check if plan exists
                plan, created = SubscriptionPlan.objects.get_or_create(
                    tier=tier_slug,
                    defaults={
                        'name': tier_display_name,
                        'description': f'{tier_display_name} plan',
                        'intro_price': intro_price,
                        'intro_duration_days': intro_duration_days,
                        'regular_price_monthly': regular_price_monthly,
                        'regular_price_yearly': regular_price_yearly,
                        'is_active': True
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[CREATED] {tier_display_name} '
                            f'(Intro: {intro_price} FCFA, Monthly: {regular_price_monthly} FCFA)'
                        )
                    )
                else:
                    # Update existing plan
                    updated = False

                    if plan.intro_price != intro_price:
                        plan.intro_price = intro_price
                        updated = True

                    if plan.intro_duration_days != intro_duration_days:
                        plan.intro_duration_days = intro_duration_days
                        updated = True

                    if plan.regular_price_monthly != regular_price_monthly:
                        plan.regular_price_monthly = regular_price_monthly
                        updated = True

                    if plan.regular_price_yearly != regular_price_yearly:
                        plan.regular_price_yearly = regular_price_yearly
                        updated = True

                    if plan.name != tier_display_name:
                        plan.name = tier_display_name
                        updated = True

                    if not plan.is_active:
                        plan.is_active = True
                        updated = True

                    if updated:
                        plan.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'[UPDATED] {tier_display_name} '
                                f'(Intro: {intro_price} FCFA, Monthly: {regular_price_monthly} FCFA)'
                            )
                        )

            # Deactivate plans not in YAML
            db_tiers = set(SubscriptionPlan.objects.values_list('tier', flat=True))
            yaml_tier_slugs = set(yaml_tiers.keys())
            removed_tiers = db_tiers - yaml_tier_slugs

            if removed_tiers:
                SubscriptionPlan.objects.filter(tier__in=removed_tiers).update(is_active=False)
                self.stdout.write(
                    self.style.WARNING(f'[WARNING] Deactivated removed tiers: {", ".join(removed_tiers)}')
                )

        # Clear capability cache
        CapabilityEngine.clear_cache()

        # Invalidate JWT capabilities version hash (forces all clients to refetch)
        from subscription.services.subscription_claims_service import SubscriptionClaimsService
        SubscriptionClaimsService.handle_plans_yaml_update()
        self.stdout.write(self.style.SUCCESS('[OK] JWT capabilities version hash invalidated'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Sync Complete ==='))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Total active plans: {SubscriptionPlan.objects.filter(is_active=True).count()}')
        self.stdout.write(self.style.SUCCESS('[OK] Capability cache cleared\n'))
