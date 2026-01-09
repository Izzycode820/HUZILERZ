"""
Django management command to validate production infrastructure setup
Ensures all required AWS resources are configured before deployment

Usage:
    python manage.py validate_infrastructure
    python manage.py validate_infrastructure --strict  # Exit 1 on any error
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from workspace.hosting.services.infrastructure_facade import InfrastructureFacade
import sys


class Command(BaseCommand):
    help = 'Validate production infrastructure configuration (DNS, SSL, CloudFront, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Exit with code 1 if any validation fails (CI/CD mode)',
        )

    def handle(self, *args, **options):
        strict_mode = options['strict']

        self.stdout.write(self.style.HTTP_INFO('\n' + '='*70))
        self.stdout.write(self.style.HTTP_INFO('  INFRASTRUCTURE VALIDATION'))
        self.stdout.write(self.style.HTTP_INFO('='*70 + '\n'))

        # Get current mode
        mode = InfrastructureFacade.get_mode()
        self.stdout.write(f"Infrastructure Mode: {self.style.WARNING(mode.upper())}\n")

        # Development mode - skip validation
        if mode == 'mock':
            self.stdout.write(self.style.WARNING('[!] Running in MOCK mode (development)'))
            self.stdout.write(self.style.WARNING('    Real AWS resources are NOT being used'))
            self.stdout.write(self.style.WARNING('    Skipping production validation checks\n'))

            self.stdout.write(self.style.SUCCESS('[OK] Mock mode configuration valid'))
            self.stdout.write(self.style.HTTP_INFO('\nTo validate production setup:'))
            self.stdout.write('   1. Set INFRASTRUCTURE_MODE=aws in .env')
            self.stdout.write('   2. Configure AWS resource IDs')
            self.stdout.write('   3. Run: python manage.py validate_infrastructure\n')
            return

        # Production mode - run comprehensive validation
        self.stdout.write(self.style.HTTP_INFO('Running production validation checks...\n'))

        errors = []
        warnings = []
        checks_passed = 0
        total_checks = 0

        # Check 1: Wildcard DNS Configuration
        total_checks += 1
        self.stdout.write('1. Wildcard DNS Configuration')
        use_wildcard = settings.USE_WILDCARD_DNS

        if use_wildcard:
            self.stdout.write(f'   [OK] USE_WILDCARD_DNS = {use_wildcard}')
            self.stdout.write('   [NOTE] Ensure *.huzilerz.com DNS record exists in Route53')
            checks_passed += 1
        else:
            warnings.append('USE_WILDCARD_DNS is False - per-workspace DNS will be created')
            self.stdout.write(self.style.WARNING('   [!] USE_WILDCARD_DNS = False'))
            checks_passed += 1

        # Check 2: Route53 Hosted Zone
        total_checks += 1
        self.stdout.write('\n2. AWS Route53 Hosted Zone')
        hosted_zone_id = settings.ROUTE53_HOSTED_ZONE_ID

        if hosted_zone_id:
            self.stdout.write(f'   [OK] ROUTE53_HOSTED_ZONE_ID: {hosted_zone_id}')
            checks_passed += 1
        else:
            errors.append('ROUTE53_HOSTED_ZONE_ID not configured')
            self.stdout.write(self.style.ERROR('   [X] ROUTE53_HOSTED_ZONE_ID: NOT SET'))
            self.stdout.write('      Set in .env: ROUTE53_HOSTED_ZONE_ID=Z1234567890ABC')

        # Check 3: CloudFront Distribution
        total_checks += 1
        self.stdout.write('\n3. CloudFront Distribution')
        cdn_config = settings.SHARED_POOL_CONFIG
        distribution_id = cdn_config.get('cdn_distribution')

        if distribution_id and distribution_id != 'E1234567890ABC':  # Not default
            self.stdout.write(f'   Distribution ID: {distribution_id}')
            self.stdout.write(f'   Domain: {cdn_config.get("cdn_distribution_domain")}')
            checks_passed += 1
        else:
            errors.append('SHARED_CLOUDFRONT_DISTRIBUTION_ID not configured (using default)')
            self.stdout.write(self.style.ERROR('    CloudFront Distribution: NOT CONFIGURED'))
            self.stdout.write('      Set in .env: SHARED_CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC')

        # Check 4: SSL Certificate
        total_checks += 1
        self.stdout.write('\n4. SSL Certificate (ACM)')
        ssl_cert_arn = settings.SHARED_SSL_CERTIFICATE_ARN

        if ssl_cert_arn:
            self.stdout.write(f'    Certificate ARN: {ssl_cert_arn}')
            checks_passed += 1
        else:
            errors.append('SHARED_SSL_CERTIFICATE_ARN not configured')
            self.stdout.write(self.style.ERROR('    SSL Certificate: NOT SET'))
            self.stdout.write('      Set in .env: SSL_CERTIFICATE_ARN=arn:aws:acm:...')

        # Check 5: S3 Buckets
        total_checks += 1
        self.stdout.write('\n5. S3 Buckets')
        media_bucket = cdn_config.get('media_bucket')
        storage_bucket = cdn_config.get('storage_bucket')

        if media_bucket != 'shared-pool-media' and storage_bucket != 'shared-pool-storage':
            self.stdout.write(f'    Media Bucket: {media_bucket}')
            self.stdout.write(f'    Storage Bucket: {storage_bucket}')
            checks_passed += 1
        else:
            warnings.append('S3 buckets using default names (may not exist)')
            self.stdout.write(self.style.WARNING(f'     Media Bucket: {media_bucket} (default)'))
            self.stdout.write(self.style.WARNING(f'     Storage Bucket: {storage_bucket} (default)'))
            self.stdout.write('      Set in .env: S3_MEDIA_BUCKET=your-media-bucket')
            checks_passed += 1

        # Check 6: AWS Credentials
        total_checks += 1
        self.stdout.write('\n6. AWS Credentials')

        if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
            self.stdout.write('    AWS_ACCESS_KEY_ID configured')
            checks_passed += 1
        else:
            errors.append('AWS_ACCESS_KEY_ID not configured')
            self.stdout.write(self.style.ERROR('    AWS_ACCESS_KEY_ID: NOT SET'))

        if hasattr(settings, 'AWS_SECRET_ACCESS_KEY') and settings.AWS_SECRET_ACCESS_KEY:
            self.stdout.write('    AWS_SECRET_ACCESS_KEY configured')
        else:
            errors.append('AWS_SECRET_ACCESS_KEY not configured')
            self.stdout.write(self.style.ERROR('    AWS_SECRET_ACCESS_KEY: NOT SET'))

        # Check 7: AWS Region
        total_checks += 1
        self.stdout.write('\n7. AWS Region')
        region = settings.AWS_DEFAULT_REGION

        if region == 'us-east-1':
            self.stdout.write(f'    AWS_DEFAULT_REGION: {region} (required for CloudFront)')
            checks_passed += 1
        else:
            warnings.append(f'AWS_DEFAULT_REGION is {region} (CloudFront requires us-east-1 for ACM)')
            self.stdout.write(self.style.WARNING(f'     AWS_DEFAULT_REGION: {region}'))
            self.stdout.write('      CloudFront SSL certificates must be in us-east-1')
            checks_passed += 1

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.HTTP_INFO('  VALIDATION SUMMARY'))
        self.stdout.write('='*70 + '\n')

        self.stdout.write(f'Total Checks: {total_checks}')
        self.stdout.write(f'Passed: {self.style.SUCCESS(str(checks_passed))}')

        if warnings:
            self.stdout.write(f'Warnings: {self.style.WARNING(str(len(warnings)))}')
            for warning in warnings:
                self.stdout.write(f'    {warning}')

        if errors:
            self.stdout.write(f'\nErrors: {self.style.ERROR(str(len(errors)))}')
            for error in errors:
                self.stdout.write(f'   {error}')

            self.stdout.write('\n' + self.style.ERROR(' PRODUCTION INFRASTRUCTURE NOT READY'))
            self.stdout.write('\nRequired Actions:')
            self.stdout.write('1. Complete AWS setup (see documentation/todo.wildcardsetup.md)')
            self.stdout.write('2. Update .env with AWS resource IDs')
            self.stdout.write('3. Run validation again\n')

            if strict_mode:
                raise CommandError('Infrastructure validation failed')
            sys.exit(1)
        else:
            if warnings:
                self.stdout.write('\n' + self.style.WARNING('  PRODUCTION INFRASTRUCTURE READY (with warnings)'))
            else:
                self.stdout.write('\n' + self.style.SUCCESS(' PRODUCTION INFRASTRUCTURE READY'))

            self.stdout.write('\nNext Steps:')
            self.stdout.write('1. Deploy application to production')
            self.stdout.write('2. Test workspace creation and theme deployment')
            self.stdout.write('3. Monitor CloudWatch logs\n')
