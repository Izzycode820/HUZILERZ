from django.core.management.base import BaseCommand
from workspace.hosting.models import HostingPlan


class Command(BaseCommand):
    help = 'Create default hosting plans for TaaS platform'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing plans and recreate',
        )
    
    def handle(self, *args, **options):
        if options['reset']:
            HostingPlan.objects.all().delete()
            self.stdout.write(self.style.WARNING('Deleted all existing hosting plans'))
        
        plans_data = [
            {
                'name': 'starter',
                'display_name': 'Starter',
                'storage_limit_gb': 1,
                'bandwidth_limit_gb': 10,
                'max_sites': 3,
                'max_custom_domains': 1,
                'ssl_included': True,
                'cdn_included': True,
                'priority_support': False,
                'price_monthly': 9.99,
            },
            {
                'name': 'professional',
                'display_name': 'Professional',
                'storage_limit_gb': 5,
                'bandwidth_limit_gb': 50,
                'max_sites': 10,
                'max_custom_domains': 5,
                'ssl_included': True,
                'cdn_included': True,
                'priority_support': False,
                'price_monthly': 29.99,
            },
            {
                'name': 'business',
                'display_name': 'Business',
                'storage_limit_gb': 15,
                'bandwidth_limit_gb': 150,
                'max_sites': 25,
                'max_custom_domains': 15,
                'ssl_included': True,
                'cdn_included': True,
                'priority_support': True,
                'price_monthly': 79.99,
            },
            {
                'name': 'enterprise',
                'display_name': 'Enterprise',
                'storage_limit_gb': 50,
                'bandwidth_limit_gb': 500,
                'max_sites': 100,
                'max_custom_domains': 50,
                'ssl_included': True,
                'cdn_included': True,
                'priority_support': True,
                'price_monthly': 199.99,
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for plan_data in plans_data:
            plan, created = HostingPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created plan: {plan.display_name}')
                )
            else:
                # Update existing plan with new data
                for key, value in plan_data.items():
                    setattr(plan, key, value)
                plan.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated plan: {plan.display_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {created_count} plans created, {updated_count} plans updated'
            )
        )