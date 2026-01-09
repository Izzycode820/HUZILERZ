
"""
Custom Domain Management Service
Handles custom domain addition, verification, and SSL provisioning
"""
import logging
import uuid
import re
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone

from workspace.hosting.models import CustomDomain, DeployedSite, HostingEnvironment

logger = logging.getLogger(__name__)


class CustomDomainService:
    """
    Service for managing custom domains
    - Add custom domain with DNS verification
    - Verify domain ownership via DNS TXT records
    - Manage SSL certificates
    - Set primary domains
    """

    @staticmethod
    def add_custom_domain(workspace, deployed_site, domain, user):
        """
        Add custom domain to deployed site

        Args:
            workspace: Workspace instance
            deployed_site: DeployedSite instance
            domain: Domain name (e.g., "shoppings.com")
            user: User instance

        Returns:
            dict with CustomDomain instance and DNS instructions

        Raises:
            ValidationError: If domain is invalid or already in use
            PermissionDenied: If user exceeds custom domain limits
        """
        # Validate domain format
        if not CustomDomainService._is_valid_domain(domain):
            raise ValidationError(f"Invalid domain format: {domain}")

        # Check if domain is already in use
        if CustomDomain.objects.filter(domain=domain).exists():
            raise ValidationError(f"Domain {domain} is already in use")

        # Check subscription limits - reads from capabilities DB record
        hosting_env = deployed_site.hosting_environment
        if not CustomDomainService._can_add_domain(workspace, hosting_env):
            raise PermissionDenied(
                "Custom domains are not available on your current plan. "
                "Upgrade to Pro or Enterprise to use custom domains."
            )

        # Generate verification token
        verification_token = uuid.uuid4().hex

        try:
            with transaction.atomic():
                # Create CustomDomain record
                custom_domain = CustomDomain.objects.create(
                    workspace=workspace,
                    deployed_site=deployed_site,
                    domain=domain,
                    status='pending',
                    verification_token=verification_token,
                    verification_method='txt',
                    created_by=user
                )

                # Generate DNS records
                dns_records = custom_domain.generate_dns_records()
                custom_domain.dns_records = dns_records
                custom_domain.save()

                logger.info(
                    f"Custom domain added: {domain} for workspace {workspace.slug} "
                    f"by user {user.email}"
                )

                return {
                    'custom_domain': custom_domain,
                    'dns_records': dns_records,
                    'verification_instructions': CustomDomainService._get_verification_instructions(
                        domain, verification_token
                    )
                }

        except Exception as e:
            logger.error(f"Failed to add custom domain {domain}: {str(e)}")
            raise ValidationError(f"Failed to add custom domain: {str(e)}")

    @staticmethod
    def verify_domain(custom_domain_id, user):
        """
        Verify domain ownership via DNS TXT record check

        Args:
            custom_domain_id: CustomDomain UUID
            user: User instance

        Returns:
            dict with verification status

        Raises:
            ValidationError: If verification fails
            PermissionDenied: If user doesn't own the domain
        """
        try:
            custom_domain = CustomDomain.objects.select_related(
                'workspace', 'deployed_site'
            ).get(id=custom_domain_id)

            # Check ownership
            if custom_domain.workspace.owner != user:
                raise PermissionDenied("You don't have permission to verify this domain")

            # Check if already verified
            if custom_domain.status == 'active':
                return {
                    'verified': True,
                    'message': 'Domain is already verified and active',
                    'verified_at': custom_domain.verified_at
                }

            # Perform DNS verification
            verification_result = CustomDomainService._check_dns_verification(
                custom_domain.domain,
                custom_domain.verification_token
            )

            if verification_result['verified']:
                with transaction.atomic():
                    custom_domain.status = 'verified'
                    custom_domain.verified_at = timezone.now()
                    custom_domain.save()

                    logger.info(
                        f"Domain verified: {custom_domain.domain} for workspace "
                        f"{custom_domain.workspace.slug}"
                    )

                    # Auto-activate after verification (industry standard UX)
                    # SSL provisioning happens in background, but domain is active immediately
                    CustomDomainService._auto_activate_domain(custom_domain)

                return {
                    'verified': True,
                    'status': 'active',
                    'message': 'Domain verified and activated successfully!',
                    'verified_at': custom_domain.verified_at,
                    'live_url': f'https://{custom_domain.domain}',
                    'ssl_status': 'provisioning' if not custom_domain.ssl_enabled else 'active'
                }
            else:
                return {
                    'verified': False,
                    'message': verification_result['message'],
                    'instructions': CustomDomainService._get_verification_instructions(
                        custom_domain.domain,
                        custom_domain.verification_token
                    )
                }

        except CustomDomain.DoesNotExist:
            raise ValidationError("Custom domain not found")
        except Exception as e:
            logger.error(f"Domain verification failed: {str(e)}")
            raise ValidationError(f"Verification failed: {str(e)}")

    @staticmethod
    def _auto_activate_domain(custom_domain):
        """
        Internal method: Auto-activate domain after verification
        Used by both manual verify and background task

        Args:
            custom_domain: CustomDomain instance

        Returns:
            None
        """
        if custom_domain.status == 'verified':
            custom_domain.status = 'active'
            custom_domain.save()

            logger.info(f"Domain auto-activated: {custom_domain.domain}")

            # Trigger SSL provisioning
            from workspace.hosting.services.infrastructure_facade import InfrastructureFacade
            try:
                ssl_result = InfrastructureFacade.provision_ssl(custom_domain.domain)
                if ssl_result.get('success'):
                    custom_domain.ssl_certificate_arn = ssl_result.get('certificate_arn')
                    custom_domain.ssl_provisioned_at = timezone.now()
                    custom_domain.save(update_fields=['ssl_certificate_arn', 'ssl_provisioned_at', 'updated_at'])
                    logger.info(f"SSL provisioned for {custom_domain.domain}: {ssl_result.get('certificate_arn')}")
            except Exception as e:
                logger.error(f"SSL provisioning failed for {custom_domain.domain}: {str(e)}", exc_info=True)

    @staticmethod
    def auto_verify_pending_domains():
        """
        Background task: Auto-verify all pending domains
        Called by Celery task every 15 minutes

        Returns:
            dict with verification stats
        """
        pending_domains = CustomDomain.objects.filter(status='pending')

        verified_count = 0
        failed_count = 0

        for domain in pending_domains:
            try:
                verification_result = CustomDomainService._check_dns_verification(
                    domain.domain,
                    domain.verification_token
                )

                if verification_result['verified']:
                    with transaction.atomic():
                        domain.status = 'verified'
                        domain.verified_at = timezone.now()
                        domain.save()

                        # Auto-activate immediately
                        CustomDomainService._auto_activate_domain(domain)

                        verified_count += 1

                        logger.info(
                            f"Background task: Domain auto-verified and activated: {domain.domain}"
                        )
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Background task: Failed to verify {domain.domain}: {str(e)}")
                failed_count += 1

        return {
            'total_pending': pending_domains.count(),
            'verified': verified_count,
            'failed': failed_count
        }

    @staticmethod
    def set_primary_domain(custom_domain_id, user):
        """
        Set a custom domain as primary for the deployed site

        Args:
            custom_domain_id: CustomDomain UUID
            user: User instance

        Returns:
            dict with status
        """
        try:
            custom_domain = CustomDomain.objects.select_related(
                'workspace', 'deployed_site'
            ).get(id=custom_domain_id)

            # Check ownership
            if custom_domain.workspace.owner != user:
                raise PermissionDenied("You don't have permission to modify this domain")

            # Check if active
            if custom_domain.status != 'active':
                raise ValidationError("Only active domains can be set as primary")

            with transaction.atomic():
                # Unset other primary domains for this site
                CustomDomain.objects.filter(
                    deployed_site=custom_domain.deployed_site,
                    is_primary=True
                ).update(is_primary=False)

                # Set this as primary
                custom_domain.is_primary = True
                custom_domain.save()

                logger.info(
                    f"Primary domain set: {custom_domain.domain} for site "
                    f"{custom_domain.deployed_site.id}"
                )

            return {
                'success': True,
                'message': f'{custom_domain.domain} is now the primary domain',
                'primary_url': f'https://{custom_domain.domain}'
            }

        except CustomDomain.DoesNotExist:
            raise ValidationError("Custom domain not found")

    @staticmethod
    def delete_custom_domain(custom_domain_id, user):
        """
        Delete custom domain

        Args:
            custom_domain_id: CustomDomain UUID
            user: User instance

        Returns:
            dict with deletion status
        """
        try:
            custom_domain = CustomDomain.objects.select_related('workspace').get(
                id=custom_domain_id
            )

            # Check ownership
            if custom_domain.workspace.owner != user:
                raise PermissionDenied("You don't have permission to delete this domain")

            domain_name = custom_domain.domain

            # Remove SSL certificate from ACM if provisioned
            if custom_domain.ssl_certificate_arn:
                from workspace.hosting.services.infrastructure_facade import InfrastructureFacade
                try:
                    service = InfrastructureFacade.get_service()
                    if hasattr(service, 'acm_client'):
                        service.acm_client.delete_certificate(
                            CertificateArn=custom_domain.ssl_certificate_arn
                        )
                        logger.info(f"Deleted SSL certificate for {domain_name}")
                except Exception as e:
                    logger.warning(f"Failed to delete SSL certificate for {domain_name}: {str(e)}")

            custom_domain.delete()

            logger.info(f"Custom domain deleted: {domain_name} by user {user.email}")

            return {
                'deleted': True,
                'message': f'Domain {domain_name} has been removed'
            }

        except CustomDomain.DoesNotExist:
            raise ValidationError("Custom domain not found")

    @staticmethod
    def list_domains_for_workspace(workspace, user):
        """
        List all custom domains for a workspace

        Args:
            workspace: Workspace instance
            user: User instance

        Returns:
            QuerySet of CustomDomain instances
        """
        # Check ownership
        if workspace.owner != user:
            raise PermissionDenied("You don't have permission to view these domains")

        return CustomDomain.objects.filter(
            workspace=workspace
        ).select_related('deployed_site').order_by('-is_primary', '-created_at')

    @staticmethod
    def _is_valid_domain(domain):
        """
        Validate domain format

        Args:
            domain: Domain string

        Returns:
            bool
        """
        # Basic domain validation regex
        domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'

        if not re.match(domain_pattern, domain):
            return False

        # Check length
        if len(domain) > 253:
            return False

        # Disallow our own domain
        if domain.endswith('.huzilerz.com'):
            return False

        return True

    @staticmethod
    def _can_add_domain(workspace, hosting_env):
        """
        Check if workspace can add custom domains - reads from capabilities DB record

        Args:
            workspace: Workspace instance
            hosting_env: HostingEnvironment instance

        Returns:
            bool: True if custom domains are allowed on this tier
        """
        # Check capabilities from DB record (boolean permission)
        # Pro and Enterprise tiers have custom_domain: true in YAML
        return hosting_env.capabilities.get('custom_domain', False)

    @staticmethod
    def _check_dns_verification(domain, verification_token):
        """
        Check DNS TXT record for verification token
        Production-ready with multiple fallback resolvers and comprehensive error handling

        Args:
            domain: Domain name
            verification_token: Expected token value

        Returns:
            dict with verification result
        """
        try:
            import dns.resolver
            import dns.exception
        except ImportError:
            logger.error("dnspython library not installed. Run: pip install dnspython")
            return {
                'verified': False,
                'message': 'DNS verification system is not configured. Please contact support.'
            }

        txt_record_name = f"_huzilerz-verify.{domain}"

        # Configure resolver with production-ready settings
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10  # 10 second timeout
        resolver.lifetime = 30  # Total 30 seconds including retries

        # Fallback DNS servers for reliability (Google, Cloudflare, Quad9)
        resolver.nameservers = [
            '8.8.8.8',      # Google Primary
            '8.8.4.4',      # Google Secondary
            '1.1.1.1',      # Cloudflare Primary
            '1.0.0.1',      # Cloudflare Secondary
            '9.9.9.9',      # Quad9
        ]

        try:
            # Query TXT records
            logger.info(f"Checking DNS TXT record for {txt_record_name}")
            answers = resolver.resolve(txt_record_name, 'TXT')

            # Check each TXT record for the verification token
            for rdata in answers:
                # TXT records are returned as quoted strings, need to decode
                txt_value = b''.join(rdata.strings).decode('utf-8')

                logger.debug(f"Found TXT record: {txt_value}")

                # Check if verification token matches
                if txt_value.strip() == verification_token.strip():
                    logger.info(f"DNS verification successful for {domain}")
                    return {
                        'verified': True,
                        'message': 'Domain verified successfully via DNS TXT record'
                    }

            # Token not found in any TXT records
            logger.warning(
                f"DNS verification failed for {domain}: Token mismatch. "
                f"Expected: {verification_token}"
            )
            return {
                'verified': False,
                'message': f'TXT record found but verification token does not match. '
                          f'Please ensure you added the exact token: {verification_token}'
            }

        except dns.resolver.NXDOMAIN:
            # Domain or subdomain doesn't exist
            logger.info(f"DNS verification pending for {domain}: TXT record not found (NXDOMAIN)")
            return {
                'verified': False,
                'message': f'TXT record _huzilerz-verify not found. Please add the TXT record to your DNS. '
                          f'DNS propagation can take up to 48 hours.'
            }

        except dns.resolver.NoAnswer:
            # Domain exists but no TXT records
            logger.info(f"DNS verification pending for {domain}: No TXT records (NoAnswer)")
            return {
                'verified': False,
                'message': f'No TXT record found for _huzilerz-verify. '
                          f'Please add the verification TXT record to your DNS settings.'
            }

        except dns.resolver.Timeout:
            # DNS query timed out
            logger.warning(f"DNS verification timeout for {domain}")
            return {
                'verified': False,
                'message': 'DNS lookup timed out. Please try again in a few minutes. '
                          'If the issue persists, check your DNS provider status.'
            }

        except dns.exception.DNSException as e:
            # Other DNS-related errors
            logger.error(f"DNS error during verification for {domain}: {str(e)}", exc_info=True)
            return {
                'verified': False,
                'message': f'DNS lookup error: {str(e)}. Please try again later.'
            }

        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error during DNS verification for {domain}: {str(e)}", exc_info=True)
            return {
                'verified': False,
                'message': 'An unexpected error occurred during verification. Please try again or contact support.'
            }

    @staticmethod
    def _get_verification_instructions(domain, verification_token):
        """
        Generate DNS verification instructions for user

        Args:
            domain: Domain name
            verification_token: Verification token

        Returns:
            dict with instructions
        """
        return {
            'step_1': {
                'title': 'Add TXT Record',
                'description': f'Go to your domain registrar (GoDaddy, Namecheap, etc.) and add a TXT record',
                'record_type': 'TXT',
                'name': f'_huzilerz-verify.{domain}',
                'value': verification_token,
                'ttl': 3600
            },
            'step_2': {
                'title': 'Add CNAME Record',
                'description': 'Point your domain to our servers',
                'record_type': 'CNAME',
                'name': domain,
                'value': 'huzilerz.com',
                'ttl': 3600
            },
            'step_3': {
                'title': 'Verify Domain',
                'description': 'After adding the records, click the "Verify" button. DNS propagation can take up to 48 hours.',
            },
            'example_txt_record': {
                'Type': 'TXT',
                'Host': f'_huzilerz-verify',
                'Value': verification_token,
                'TTL': '1 Hour'
            },
            'example_cname_record': {
                'Type': 'CNAME',
                'Host': '@',
                'Value': 'huzilerz.com',
                'TTL': '1 Hour'
            }
        }

    @staticmethod
    def get_domain_status(custom_domain_id, user):
        """
        Get detailed status of a custom domain

        Args:
            custom_domain_id: CustomDomain UUID
            user: User instance

        Returns:
            dict with domain status and details
        """
        try:
            custom_domain = CustomDomain.objects.select_related(
                'workspace', 'deployed_site'
            ).get(id=custom_domain_id)

            # Check ownership
            if custom_domain.workspace.owner != user:
                raise PermissionDenied("You don't have permission to view this domain")

            return {
                'domain': custom_domain.domain,
                'status': custom_domain.status,
                'is_primary': custom_domain.is_primary,
                'verified': custom_domain.status in ['verified', 'active'],
                'verified_at': custom_domain.verified_at,
                'ssl_enabled': custom_domain.ssl_enabled,
                'ssl_provisioned_at': custom_domain.ssl_provisioned_at,
                'dns_records': custom_domain.dns_records,
                'created_at': custom_domain.created_at,
                'actions_available': CustomDomainService._get_available_actions(custom_domain)
            }

        except CustomDomain.DoesNotExist:
            raise ValidationError("Custom domain not found")

    @staticmethod
    def _get_available_actions(custom_domain):
        """
        Get available actions for a custom domain based on its status

        Args:
            custom_domain: CustomDomain instance

        Returns:
            list of available action strings
        """
        actions = ['delete']

        if custom_domain.status == 'pending':
            actions.append('verify')

        if custom_domain.status == 'verified':
            actions.extend(['activate', 'verify_again'])

        if custom_domain.status == 'active':
            if not custom_domain.is_primary:
                actions.append('set_primary')

        return actions
