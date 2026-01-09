"""
Custom Domain Background Tasks
Auto-verification, SSL provisioning, domain health checks,
purchase processing, and renewal management
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    name='workspace_hosting.auto_verify_domains',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def auto_verify_domains(self):
    """
    Auto-verify pending custom domains

    Runs every 15 minutes via Celery Beat
    Checks DNS records and auto-activates verified domains

    Returns:
        dict: Verification statistics
    """
    from workspace.hosting.services.custom_domain_service import CustomDomainService

    try:
        logger.info("Starting auto-verification of pending domains")

        result = CustomDomainService.auto_verify_pending_domains()

        logger.info(
            f"Auto-verification complete: {result['verified']} verified, "
            f"{result['failed']} failed, {result['total_pending']} total pending"
        )

        return result

    except Exception as e:
        logger.error(f"Auto-verification task failed: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e)


@shared_task(
    name='workspace_hosting.provision_ssl_certificates',
    bind=True,
    max_retries=5,
    default_retry_delay=300  # 5 minutes
)
def provision_ssl_certificates(self):
    """
    Provision SSL certificates for active domains

    Runs every hour via Celery Beat
    Uses AWS ACM (prod) or mock certificates (dev)

    Returns:
        dict: SSL provisioning statistics
    """
    from workspace.hosting.models import CustomDomain
    from workspace.hosting.services.infrastructure_facade import InfrastructureFacade

    try:
        logger.info("Starting SSL certificate provisioning")

        # Get appropriate infrastructure service (mock or AWS)
        infra_service = InfrastructureFacade.get_service()
        mode = InfrastructureFacade.get_mode()

        # Get active domains without SSL
        domains_needing_ssl = CustomDomain.objects.filter(
            status='active',
            ssl_enabled=False
        ).select_related('deployed_site', 'deployed_site__user')

        provisioned_count = 0
        failed_count = 0
        provisioned_domains = []
        failed_domains = []

        logger.info(
            f"Found {domains_needing_ssl.count()} domains needing SSL provisioning (mode: {mode})"
        )

        for domain in domains_needing_ssl:
            try:
                logger.info(f"Provisioning SSL for: {domain.domain}")

                # Provision SSL certificate via infrastructure service
                ssl_result = infra_service.provision_ssl_for_domain(
                    domain=domain.domain
                )

                if ssl_result.get('success'):
                    # Update domain with SSL information
                    domain.ssl_enabled = True
                    domain.ssl_provisioned_at = timezone.now()

                    # Store certificate details in metadata
                    domain.metadata = domain.metadata or {}
                    domain.metadata['ssl_certificate'] = {
                        'certificate_id': ssl_result.get('certificate_id'),
                        'certificate_arn': ssl_result.get('certificate_arn'),
                        'status': ssl_result.get('status'),
                        'validation_method': ssl_result.get('validation_method'),
                        'provisioned_at': ssl_result.get('provisioned_at').isoformat() if ssl_result.get('provisioned_at') else None,
                        'expires_at': ssl_result.get('expires_at').isoformat() if ssl_result.get('expires_at') else None
                    }

                    # Store validation records if DNS validation
                    if ssl_result.get('validation_records'):
                        domain.metadata['ssl_validation_records'] = ssl_result['validation_records']

                    domain.save()

                    provisioned_count += 1
                    provisioned_domains.append(domain.domain)

                    logger.info(
                        f"SSL provisioned successfully for {domain.domain}: "
                        f"cert_id={ssl_result.get('certificate_id')}"
                    )
                else:
                    error_msg = ssl_result.get('error', 'Unknown error')
                    logger.error(f"Failed to provision SSL for {domain.domain}: {error_msg}")
                    failed_count += 1
                    failed_domains.append({
                        'domain': domain.domain,
                        'error': error_msg
                    })

            except Exception as e:
                logger.error(f"Failed to provision SSL for {domain.domain}: {str(e)}", exc_info=True)
                failed_count += 1
                failed_domains.append({
                    'domain': domain.domain,
                    'error': str(e)
                })

        result = {
            'total_pending': domains_needing_ssl.count(),
            'provisioned': provisioned_count,
            'failed': failed_count,
            'mode': mode,
            'provisioned_domains': provisioned_domains,
            'failed_domains': failed_domains[:5]  # Limit to first 5 failures
        }

        logger.info(
            f"SSL provisioning complete: {result['provisioned']} provisioned, "
            f"{result['failed']} failed (mode: {mode})"
        )

        return result

    except Exception as e:
        logger.error(f"SSL provisioning task failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    name='workspace_hosting.check_domain_health',
    bind=True
)
def check_domain_health(self):
    """
    Health check for all active domains

    Runs daily via Celery Beat
    Checks if DNS records are still correct
    Alerts if domains are misconfigured

    Returns:
        dict: Health check statistics
    """
    from workspace.hosting.models import CustomDomain
    from datetime import timedelta

    try:
        import dns.resolver
        import dns.exception
    except ImportError:
        logger.error("dnspython library not installed. Skipping health checks.")
        return {
            'total_checked': 0,
            'healthy': 0,
            'unhealthy': 0,
            'error': 'dnspython not installed'
        }

    try:
        logger.info("Starting domain health checks")

        active_domains = CustomDomain.objects.filter(status='active').select_related('deployed_site')

        healthy_count = 0
        unhealthy_count = 0
        issues_found = []

        # Configure DNS resolver with production settings
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5  # Faster timeout for health checks
        resolver.lifetime = 15
        resolver.nameservers = ['8.8.8.8', '1.1.1.1', '9.9.9.9']

        for domain in active_domains:
            domain_issues = []

            try:
                # 1. Check CNAME record points to our platform
                try:
                    cname_answers = resolver.resolve(domain.domain, 'CNAME')
                    cname_target = str(cname_answers[0].target).rstrip('.')

                    if 'huzilerz.com' not in cname_target:
                        domain_issues.append(
                            f"CNAME record points to '{cname_target}' instead of 'huzilerz.com'"
                        )
                        logger.warning(f"CNAME misconfigured for {domain.domain}: {cname_target}")

                except dns.resolver.NoAnswer:
                    # No CNAME, check A record as fallback
                    try:
                        a_answers = resolver.resolve(domain.domain, 'A')
                        # If A record exists, that's acceptable (could be proxied via Cloudflare)
                        logger.info(f"Domain {domain.domain} uses A record instead of CNAME")
                    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                        domain_issues.append("No CNAME or A record found - domain not pointing to platform")
                        logger.warning(f"No DNS records found for {domain.domain}")

                except dns.resolver.NXDOMAIN:
                    domain_issues.append("Domain does not exist (NXDOMAIN)")
                    logger.warning(f"Domain {domain.domain} does not exist")

                # 2. Check SSL certificate expiration (if enabled)
                if domain.ssl_enabled and domain.ssl_provisioned_at:
                    # SSL certs typically last 90 days (Let's Encrypt)
                    cert_age = timezone.now() - domain.ssl_provisioned_at
                    if cert_age > timedelta(days=80):
                        domain_issues.append(
                            f"SSL certificate may be expiring soon (provisioned {cert_age.days} days ago)"
                        )
                        logger.warning(f"SSL renewal needed for {domain.domain}")

                # 3. Check if verification TXT record is still present (optional check)
                # Users should be able to remove it after verification, so just log if missing
                try:
                    txt_record_name = f"_huzilerz-verify.{domain.domain}"
                    txt_answers = resolver.resolve(txt_record_name, 'TXT')
                    logger.debug(f"Verification TXT record still present for {domain.domain}")
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    # This is normal - users can remove verification record after domain is verified
                    pass

                # Determine health status
                if domain_issues:
                    unhealthy_count += 1
                    issues_found.append({
                        'domain': domain.domain,
                        'issues': domain_issues
                    })

                    # TODO: Send notification to workspace owner about domain issues
                    logger.warning(
                        f"Domain {domain.domain} has {len(domain_issues)} issue(s): "
                        f"{', '.join(domain_issues)}"
                    )
                else:
                    healthy_count += 1

            except dns.resolver.Timeout:
                logger.warning(f"Health check timeout for {domain.domain}")
                unhealthy_count += 1
                issues_found.append({
                    'domain': domain.domain,
                    'issues': ['DNS query timeout']
                })

            except Exception as e:
                logger.error(f"Health check error for {domain.domain}: {str(e)}", exc_info=True)
                unhealthy_count += 1
                issues_found.append({
                    'domain': domain.domain,
                    'issues': [f'Health check error: {str(e)}']
                })

        result = {
            'total_checked': active_domains.count(),
            'healthy': healthy_count,
            'unhealthy': unhealthy_count,
            'issues': issues_found[:10]  # Limit to first 10 for logging
        }

        logger.info(
            f"Health checks complete: {result['healthy']} healthy, "
            f"{result['unhealthy']} unhealthy"
        )

        # Log critical issues
        if unhealthy_count > 0:
            logger.warning(f"Found {unhealthy_count} domains with health issues")

        return result

    except Exception as e:
        logger.error(f"Health check task failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    name='workspace_hosting.cleanup_failed_domains',
    bind=True
)
def cleanup_failed_domains(self):
    """
    Cleanup domains stuck in pending status for too long

    Runs daily via Celery Beat
    Marks domains as 'failed' if pending > 7 days

    Returns:
        dict: Cleanup statistics
    """
    from workspace.hosting.models import CustomDomain
    from datetime import timedelta

    try:
        logger.info("Starting cleanup of failed domains")

        # Find domains pending for more than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        stale_domains = CustomDomain.objects.filter(
            status='pending',
            created_at__lt=cutoff_date
        )

        cleanup_count = stale_domains.count()

        # Mark as failed
        stale_domains.update(status='failed')

        logger.info(f"Cleanup complete: {cleanup_count} domains marked as failed")

        # TODO: Send notification to users about failed domains

        return {
            'cleaned_up': cleanup_count
        }

    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


# ==================== DOMAIN PURCHASE & RENEWAL TASKS ====================


@shared_task(
    name='workspace_hosting.process_domain_purchase',
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def process_domain_purchase(self, purchase_id: str):
    """
    Process domain purchase after payment confirmation

    Triggered by mobile money payment webhook
    Performs actual purchase from registrar (Namecheap/GoDaddy)

    Args:
        purchase_id: DomainPurchase UUID

    Returns:
        dict: Purchase result
    """
    from workspace.hosting.services.domain_purchase_service import DomainPurchaseService

    try:
        logger.info(f"Processing domain purchase: {purchase_id}")

        result = DomainPurchaseService.complete_purchase(purchase_id)

        if result.get('success'):
            logger.info(
                f"Domain purchase completed: {result.get('domain_name')} "
                f"(Order: {result.get('order_id')})"
            )
        else:
            logger.error(
                f"Domain purchase failed: {purchase_id} - {result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Domain purchase task failed: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e)


@shared_task(
    name='workspace_hosting.process_domain_renewal',
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def process_domain_renewal(self, renewal_id: str):
    """
    Process domain renewal after payment confirmation

    Triggered by mobile money payment webhook
    Performs actual renewal with registrar

    Args:
        renewal_id: DomainRenewal UUID

    Returns:
        dict: Renewal result
    """
    from workspace.hosting.services.domain_renewal_service import DomainRenewalService

    try:
        logger.info(f"Processing domain renewal: {renewal_id}")

        result = DomainRenewalService.complete_renewal(renewal_id)

        if result.get('success'):
            logger.info(
                f"Domain renewal completed: {result.get('domain_name')} "
                f"(New expiry: {result.get('new_expiry_date')})"
            )
        else:
            logger.error(
                f"Domain renewal failed: {renewal_id} - {result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Domain renewal task failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    name='workspace_hosting.send_renewal_warnings',
    bind=True
)
def send_renewal_warnings(self):
    """
    Send renewal warnings for expiring domains

    Runs daily via Celery Beat
    Cameroon market: Manual renewal only (no auto-renewal)
    Progressive warning system: 30, 15, 7, 3, 1 days before expiry

    Returns:
        dict: Warning statistics
    """
    from workspace.hosting.services.domain_renewal_service import DomainRenewalService

    try:
        logger.info("Starting renewal warning process")

        # Get domains needing warnings
        domains_needing_warning = DomainRenewalService.get_domains_needing_renewal_warning()

        sent_count = 0
        failed_count = 0
        warnings_by_urgency = {
            'critical': 0,  # 1-3 days
            'high': 0,      # 7 days
            'normal': 0     # 15-30 days
        }

        for domain in domains_needing_warning:
            try:
                result = DomainRenewalService.send_renewal_warning(domain)

                if result.get('success'):
                    sent_count += 1
                    urgency = result.get('urgency', 'normal')
                    warnings_by_urgency[urgency] = warnings_by_urgency.get(urgency, 0) + 1

                    logger.info(
                        f"Renewal warning sent: {domain.domain} "
                        f"(expires in {result.get('days_until_expiry')} days)"
                    )
                else:
                    failed_count += 1
                    logger.error(f"Failed to send warning for {domain.domain}: {result.get('error')}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Warning failed for {domain.domain}: {str(e)}", exc_info=True)

        result = {
            'total_checked': len(domains_needing_warning),
            'warnings_sent': sent_count,
            'failed': failed_count,
            'by_urgency': warnings_by_urgency
        }

        logger.info(
            f"Renewal warnings complete: {sent_count} sent, {failed_count} failed "
            f"(Critical: {warnings_by_urgency['critical']}, "
            f"High: {warnings_by_urgency['high']}, "
            f"Normal: {warnings_by_urgency['normal']})"
        )

        return result

    except Exception as e:
        logger.error(f"Renewal warning task failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    name='workspace_hosting.handle_expired_domains',
    bind=True
)
def handle_expired_domains(self):
    """
    Handle domains that have expired (user didn't renew)

    Runs daily via Celery Beat
    Suspends expired domains and sends final notifications

    Returns:
        dict: Expiration handling statistics
    """
    from workspace.hosting.services.domain_renewal_service import DomainRenewalService

    try:
        logger.info("Starting expired domains handling")

        result = DomainRenewalService.handle_expired_domains()

        logger.info(
            f"Expired domains handled: {result['suspended']} suspended "
            f"out of {result['total_expired']} expired"
        )

        if result.get('errors'):
            logger.warning(f"Errors during expiration handling: {len(result['errors'])} errors")

        return result

    except Exception as e:
        logger.error(f"Expired domains task failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)
