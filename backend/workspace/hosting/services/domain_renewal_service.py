"""
Domain Renewal Service
Handle domain renewal warnings and manual renewal flow (Cameroon market)
NO auto-renewal - All renewals require manual mobile money payment
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

from workspace.hosting.models import CustomDomain, DomainRenewal
from workspace.hosting.services.domain_registrar_service import DomainRegistrarService
from workspace.hosting.services.domain_purchase_service import DomainPurchaseService

logger = logging.getLogger(__name__)


class DomainRenewalService:
    """
    Domain renewal management for Cameroon market
    Manual payment flow with progressive warning system
    """

    # Renewal warning intervals (days before expiration)
    WARNING_INTERVALS = [30, 15, 7, 3, 1]  # Escalating urgency

    @classmethod
    def get_domains_needing_renewal_warning(cls) -> List[CustomDomain]:
        """
        Get domains that need renewal warnings

        Returns:
            List of CustomDomain objects that need warnings
        """
        now = timezone.now()
        domains = []

        for days_before in cls.WARNING_INTERVALS:
            # Calculate target expiry date range
            target_date = now + timedelta(days=days_before)
            # Give 1-day window for each warning
            date_range_start = target_date - timedelta(hours=12)
            date_range_end = target_date + timedelta(hours=12)

            # Find domains expiring in this window
            expiring_domains = CustomDomain.objects.filter(
                purchased_via_platform=True,
                status__in=['verified', 'active'],
                expires_at__gte=date_range_start,
                expires_at__lte=date_range_end,
                auto_renew_enabled=False  # Only manual renewal domains
            ).exclude(
                # Exclude if already warned for this interval
                renewal_warning_count__gte=days_before
            ).select_related('workspace', 'created_by')

            domains.extend(expiring_domains)

        return domains

    @classmethod
    def send_renewal_warning(cls, domain: CustomDomain) -> Dict[str, Any]:
        """
        Send renewal warning to domain owner

        Args:
            domain: CustomDomain to warn about

        Returns:
            dict: Warning result
        """
        try:
            days_until_expiry = (domain.expires_at - timezone.now()).days

            # Determine warning urgency
            if days_until_expiry <= 1:
                urgency = 'critical'
                subject = f' URGENT: {domain.domain} expires in {days_until_expiry} day(s)!'
            elif days_until_expiry <= 7:
                urgency = 'high'
                subject = f' Important: {domain.domain} expires soon'
            else:
                urgency = 'normal'
                subject = f'Reminder: {domain.domain} renewal needed'

            # Calculate renewal price
            renewal_price_fcfa = domain.renewal_price_fcfa or DomainPurchaseService.calculate_price_fcfa(
                domain.renewal_price_usd or Decimal('12.00')
            )

            # TODO: Send email/SMS notification via notification service
            # notification_service.send_renewal_warning(
            #     user=domain.created_by,
            #     domain=domain.domain,
            #     days_until_expiry=days_until_expiry,
            #     renewal_price_fcfa=renewal_price_fcfa,
            #     urgency=urgency
            # )

            # Update warning tracking
            domain.renewal_reminder_sent = True
            domain.last_renewal_warning_sent_at = timezone.now()
            domain.renewal_warning_count += 1
            domain.save(update_fields=[
                'renewal_reminder_sent',
                'last_renewal_warning_sent_at',
                'renewal_warning_count',
                'updated_at'
            ])

            logger.info(
                f"Renewal warning sent for {domain.domain}: "
                f"{days_until_expiry} days until expiry (urgency: {urgency})"
            )

            return {
                'success': True,
                'domain': domain.domain,
                'days_until_expiry': days_until_expiry,
                'urgency': urgency,
                'renewal_price_fcfa': float(renewal_price_fcfa)
            }

        except Exception as e:
            logger.error(f"Failed to send renewal warning for {domain.domain}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    @transaction.atomic
    def initiate_renewal(cls, domain_id: str, user, phone_number: str,
                        renewal_years: int = 1, preferred_provider: str = 'fapshi',
                        idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate domain renewal (Step 1: Before payment)

        Creates DomainRenewal record in 'pending_payment' status
        User will then pay via mobile money via PaymentService

        Args:
            domain_id: CustomDomain UUID
            user: User initiating renewal
            phone_number: User's mobile money phone number
            renewal_years: Renewal period (default 1 year)
            preferred_provider: Payment provider (fapshi, mtn, orange)
            idempotency_key: Optional UUID for preventing duplicate requests

        Returns:
            dict: Renewal initiation result
        """
        try:
            # Get domain
            domain = CustomDomain.objects.select_related('workspace', 'created_by').get(id=domain_id)

            # Validate ownership
            if domain.created_by != user and domain.workspace.owner != user:
                return {
                    'success': False,
                    'errors': ['You can only renew domains you own']
                }

            # Validate domain was purchased via platform
            if not domain.purchased_via_platform:
                return {
                    'success': False,
                    'errors': ['Only domains purchased through Huzilerz can be renewed here']
                }

            # Check if domain is expired
            if domain.expires_at < timezone.now():
                days_expired = (timezone.now() - domain.expires_at).days
                if days_expired > 30:
                    return {
                        'success': False,
                        'errors': [
                            f'Domain expired {days_expired} days ago. '
                            f'Domains expired for more than 30 days cannot be renewed. '
                            f'Please purchase a new domain.'
                        ]
                    }

            # Get renewal pricing
            renewal_price_usd = domain.renewal_price_usd or Decimal('12.00')
            renewal_price_fcfa = DomainPurchaseService.calculate_price_fcfa(renewal_price_usd)
            exchange_rate = DomainPurchaseService.get_exchange_rate()

            # Create DomainRenewal record
            domain_renewal = DomainRenewal.objects.create(
                custom_domain=domain,
                user=user,
                domain_name=domain.domain,
                registrar=domain.registrar_name or 'namecheap',
                renewal_price_usd=renewal_price_usd,
                renewal_price_fcfa=renewal_price_fcfa,
                exchange_rate=exchange_rate,
                payment_method='mobile_money',
                renewal_status='pending_payment',
                renewal_period_years=renewal_years,
                previous_expiry_date=domain.expires_at
            )

            # Create PaymentIntent via PaymentService
            from payments.services.payment_service import PaymentService

            payment_metadata = {
                'phone_number': phone_number,
                'domain_name': domain.domain,
                'renewal_id': str(domain_renewal.id),
                'domain_id': str(domain.id),
                'registrar': domain.registrar_name or 'namecheap',
                'years': renewal_years
            }

            payment_result = PaymentService.create_payment(
                workspace_id=domain.workspace.id,
                user=user,
                amount=int(renewal_price_fcfa),
                currency='XAF',
                purpose='domain_renewal',
                preferred_provider=preferred_provider,
                idempotency_key=idempotency_key,
                metadata=payment_metadata
            )

            if not payment_result['success']:
                raise ValidationError(f"Payment initiation failed: {payment_result.get('error')}")

            # Link PaymentIntent to DomainRenewal
            from payments.models import PaymentIntent
            payment_intent = PaymentIntent.objects.get(id=payment_result['payment_intent_id'])
            domain_renewal.payment_intent = payment_intent
            domain_renewal.save(update_fields=['payment_intent', 'updated_at'])

            logger.info(
                f"Domain renewal initiated: {domain.domain} for user {user.id} "
                f"(Renewal ID: {domain_renewal.id}, PaymentIntent: {payment_intent.id})"
            )

            return {
                'success': True,
                'renewal_id': str(domain_renewal.id),
                'payment_intent_id': str(payment_intent.id),
                'domain_name': domain.domain,
                'current_expiry': domain.expires_at.isoformat(),
                'renewal_price_usd': float(renewal_price_usd),
                'renewal_price_fcfa': float(renewal_price_fcfa),
                'exchange_rate': float(exchange_rate),
                'payment_instructions': payment_result.get('instructions'),
                'redirect_url': payment_result.get('redirect_url'),
                'next_step': 'payment'
            }

        except CustomDomain.DoesNotExist:
            return {
                'success': False,
                'errors': ['Domain not found']
            }

        except Exception as e:
            logger.error(f"Failed to initiate domain renewal: {str(e)}", exc_info=True)
            return {
                'success': False,
                'errors': [f"Failed to initiate renewal: {str(e)}"]
            }

  

    @classmethod
    @transaction.atomic
    def complete_renewal(cls, renewal_id: str) -> Dict[str, Any]:
        """
        Complete domain renewal with registrar (Step 3: Renew with registrar)

        Called by Celery task after payment confirmation

        Args:
            renewal_id: DomainRenewal UUID

        Returns:
            dict: Renewal result
        """
        try:
            domain_renewal = DomainRenewal.objects.select_related(
                'custom_domain'
            ).get(id=renewal_id)

            if domain_renewal.renewal_status != 'processing':
                return {
                    'success': False,
                    'error': f"Invalid renewal status: {domain_renewal.renewal_status}"
                }

            # Initialize registrar service
            registrar_service = DomainRegistrarService(registrar=domain_renewal.registrar)

            # Renew domain with registrar
            renewal_result = registrar_service.renew_domain(
                domain_name=domain_renewal.domain_name,
                renewal_years=domain_renewal.renewal_period_years
            )

            if not renewal_result.get('success'):
                # Renewal failed
                error_msg = renewal_result.get('error', 'Unknown error')
                domain_renewal.mark_failed(error_msg)

                logger.error(
                    f"Domain renewal with registrar failed: {domain_renewal.domain_name} - {error_msg}"
                )

                return {
                    'success': False,
                    'error': error_msg
                }

            # Renewal successful
            new_expiry_date = renewal_result['new_expiry_date']

            domain_renewal.mark_completed(
                registrar_renewal_id=renewal_result['renewal_id'],
                new_expiry_date=new_expiry_date
            )
            domain_renewal.registrar_response = renewal_result.get('registrar_response', {})
            domain_renewal.save(update_fields=['registrar_response', 'updated_at'])

            # Update CustomDomain
            custom_domain = domain_renewal.custom_domain
            custom_domain.expires_at = new_expiry_date
            custom_domain.next_renewal_date = custom_domain.calculate_next_renewal_date()
            custom_domain.renewal_reminder_sent = False  # Reset for next cycle
            custom_domain.renewal_warning_count = 0
            custom_domain.save(update_fields=[
                'expires_at',
                'next_renewal_date',
                'renewal_reminder_sent',
                'renewal_warning_count',
                'updated_at'
            ])

            logger.info(
                f"Domain renewal completed: {domain_renewal.domain_name} "
                f"(New expiry: {new_expiry_date})"
            )

            return {
                'success': True,
                'renewal_id': str(renewal_id),
                'domain_name': domain_renewal.domain_name,
                'new_expiry_date': new_expiry_date.isoformat(),
                'renewal_id_registrar': renewal_result['renewal_id']
            }

        except DomainRenewal.DoesNotExist:
            logger.error(f"Domain renewal not found: {renewal_id}")
            return {
                'success': False,
                'error': 'Renewal not found'
            }

        except Exception as e:
            logger.error(f"Domain renewal completion failed: {str(e)}", exc_info=True)

            # Mark as failed
            try:
                domain_renewal.mark_failed(str(e))
            except:
                pass

            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def handle_expired_domains(cls) -> Dict[str, Any]:
        """
        Handle domains that have expired (user didn't renew)

        Called by daily Celery task
        Suspends domains and marks them as expired

        Returns:
            dict: Processing statistics
        """
        now = timezone.now()

        # Find domains that expired and weren't renewed
        expired_domains = CustomDomain.objects.filter(
            purchased_via_platform=True,
            status__in=['verified', 'active'],
            expires_at__lt=now
        ).select_related('workspace')

        suspended_count = 0
        errors = []

        for domain in expired_domains:
            try:
                # Suspend domain
                domain.status = 'suspended'
                domain.save(update_fields=['status', 'updated_at'])

                # Create expired renewal record (for history)
                DomainRenewal.objects.create(
                    custom_domain=domain,
                    user=domain.created_by,
                    domain_name=domain.domain,
                    registrar=domain.registrar_name or 'namecheap',
                    renewal_price_usd=domain.renewal_price_usd or Decimal('12.00'),
                    renewal_price_fcfa=domain.renewal_price_fcfa or Decimal('7200.00'),
                    exchange_rate=domain.exchange_rate_at_purchase or Decimal('600.00'),
                    renewal_status='expired',
                    previous_expiry_date=domain.expires_at,
                    warning_sent_at=domain.last_renewal_warning_sent_at,
                    days_before_expiry_warned=domain.renewal_warning_count
                )

                suspended_count += 1

                logger.warning(f"Domain expired and suspended: {domain.domain}")

                # TODO: Send final expiration notification
                # notification_service.send_domain_expired_notification(
                #     user=domain.created_by,
                #     domain=domain.domain
                # )

            except Exception as e:
                logger.error(f"Failed to handle expired domain {domain.domain}: {str(e)}", exc_info=True)
                errors.append({'domain': domain.domain, 'error': str(e)})

        logger.info(f"Expired domains handled: {suspended_count} suspended")

        return {
            'total_expired': expired_domains.count(),
            'suspended': suspended_count,
            'errors': errors
        }

    @classmethod
    def get_renewal_status(cls, renewal_id: str) -> Dict[str, Any]:
        """
        Get status of domain renewal

        Args:
            renewal_id: DomainRenewal UUID

        Returns:
            dict: Renewal status and details
        """
        try:
            domain_renewal = DomainRenewal.objects.select_related(
                'custom_domain'
            ).get(id=renewal_id)

            return {
                'success': True,
                'renewal_id': str(domain_renewal.id),
                'domain_name': domain_renewal.domain_name,
                'status': domain_renewal.renewal_status,
                'renewal_price_fcfa': float(domain_renewal.renewal_price_fcfa),
                'previous_expiry': domain_renewal.previous_expiry_date.isoformat(),
                'new_expiry': domain_renewal.new_expiry_date.isoformat() if domain_renewal.new_expiry_date else None,
                'payment_reference': domain_renewal.payment_reference,
                'created_at': domain_renewal.created_at.isoformat(),
                'renewed_at': domain_renewal.renewed_at.isoformat() if domain_renewal.renewed_at else None,
                'error_message': domain_renewal.error_message if domain_renewal.error_message else None
            }

        except DomainRenewal.DoesNotExist:
            return {
                'success': False,
                'error': 'Renewal not found'
            }
